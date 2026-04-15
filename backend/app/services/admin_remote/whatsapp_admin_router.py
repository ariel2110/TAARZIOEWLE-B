"""WhatsApp Admin Remote Control
================================
Turns the admin's personal WhatsApp into a remote control panel for SiteNest.

State machine:
  MAIN_MENU       — default state, shows command menu
  CHAT_WITH_GROK  — forwards to Grok (xAI)
  CHAT_WITH_CLAUDE — forwards to Claude (Anthropic)
  CHAT_WITH_GEMINI — forwards to Gemini (Google)

Security: Only messages from WHATSAPP_OWNER_PHONE are processed.
All others are silently ignored at the webhook layer.

Usage (from webhook handler):
    from app.services.admin_remote.whatsapp_admin_router import handle_admin_message
    handle_admin_message(text, db)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService

logger = logging.getLogger(__name__)

# ── Session state (in-memory, intentionally simple) ──────────────────────────
AdminState = Literal["MAIN_MENU", "CHAT_WITH_GROK", "CHAT_WITH_CLAUDE", "CHAT_WITH_GEMINI"]

_session: dict = {
    "state": "MAIN_MENU",
    # Claude/Gemini keep rolling history for multi-turn conversation
    "claude_history": [],   # list[{"role": "user"|"assistant", "content": str}]
    "gemini_history": [],   # list[{"role": "user"|"model", "parts": [str]}]
}

_EXIT_KEYWORDS = {"exit", "יציאה", "תפריט", "menu", "back", "חזרה", "ביטול"}

# ── Menu text ─────────────────────────────────────────────────────────────────
_MENU_TEXT = (
    "🤖 *SiteNest Admin Remote*\n"
    "ברוך הבא, אריאל!\n\n"
    "בחר פעולה:\n"
    "• *גרוק* — שוחח עם Grok (AI CEO)\n"
    "• *קלוד* — שוחח עם Claude (Anthropic)\n"
    "• *ג'מיני* — שוחח עם Gemini (Google)\n"
    "• *סטטיסטיקות* — דוח יומי מהיר\n"
    "• *לידים* — לידים חמים ובוערים\n"
    "• *עזרה* — תפריט זה\n\n"
    "_שלח *יציאה* מכל מצב שיחה כדי לחזור לתפריט_"
)


# ── Public entry point ────────────────────────────────────────────────────────

def handle_admin_message(text: str, db: Session) -> None:
    """Dispatch an inbound message from the admin WhatsApp to the state machine."""
    text = (text or "").strip()
    if not text:
        return

    state: AdminState = _session["state"]

    # Exit from any chat state back to main menu
    if state != "MAIN_MENU" and text.lower() in _EXIT_KEYWORDS:
        _session["state"] = "MAIN_MENU"
        _session["claude_history"] = []
        _session["gemini_history"] = []
        _send("↩️ חזרת לתפריט הראשי.\n\n" + _MENU_TEXT)
        return

    if state == "MAIN_MENU":
        _handle_menu_command(text, db)
    elif state == "CHAT_WITH_GROK":
        _chat_grok(text, db)
    elif state == "CHAT_WITH_CLAUDE":
        _chat_claude(text)
    elif state == "CHAT_WITH_GEMINI":
        _chat_gemini(text)


# ── Menu command dispatcher ───────────────────────────────────────────────────

def _handle_menu_command(text: str, db: Session) -> None:
    lower = text.lower().strip()

    if lower in {"גרוק", "grok", "groc"}:
        _session["state"] = "CHAT_WITH_GROK"
        _session["claude_history"] = []
        _session["gemini_history"] = []
        _send("🧠 *מצב שיחה: Grok (AI CEO)*\nשלח הודעה לגרוק. שלח *יציאה* לחזרה לתפריט.")

    elif lower in {"קלוד", "claude", "אנתרופיק", "anthropic"}:
        _session["state"] = "CHAT_WITH_CLAUDE"
        _session["claude_history"] = []
        _send("🤖 *מצב שיחה: Claude (Anthropic)*\nשלח הודעה לקלוד. שלח *יציאה* לחזרה לתפריט.")

    elif lower in {"ג'מיני", "ג׳מיני", "gemini", "google", "גוגל"}:
        _session["state"] = "CHAT_WITH_GEMINI"
        _session["gemini_history"] = []
        _send("💎 *מצב שיחה: Gemini (Google)*\nשלח הודעה לג'מיני. שלח *יציאה* לחזרה לתפריט.")

    elif lower in {"סטטיסטיקות", "stats", "דוח", "report", "statistics", "נתונים"}:
        _send(_get_stats(db))

    elif lower in {"לידים", "leads", "חם", "hot", "חמים", "בוערים"}:
        _send(_get_hot_leads(db))

    elif lower in {"עזרה", "help", "תפריט", "menu", "?", "היי", "שלום", "hello", "hi", "הי"}:
        _send(_MENU_TEXT)

    else:
        _send(f"❓ לא הבנתי את הפקודה: *{text}*\n\n" + _MENU_TEXT)


# ── AI chat handlers ──────────────────────────────────────────────────────────

def _chat_grok(text: str, db: Session) -> None:
    """Forward message to Grok CEO service and reply with the structured response."""
    try:
        from app.services.ceo_agent.ceo_grok_service import CEOGrokService
        _send("⏳ שואל את גרוק...")
        result = CEOGrokService().think(db, ariel_message=text)

        parts: list[str] = []
        if result.get("understanding_and_analysis"):
            parts.append(f"📊 *ניתוח:*\n{result['understanding_and_analysis']}")
        if result.get("strategic_insight"):
            parts.append(f"💡 *תובנה:*\n{result['strategic_insight']}")
        if result.get("proposed_action_plan"):
            parts.append(f"📋 *תוכנית:*\n{result['proposed_action_plan']}")
        if result.get("message_to_ariel"):
            parts.append(f"💬 *גרוק אומר:*\n{result['message_to_ariel']}")

        _send("\n\n".join(parts) if parts else str(result))
    except Exception:
        logger.exception("[admin_wa] Grok error")
        _send("❌ שגיאה בחיבור לגרוק. בדוק את ה-XAI_API_KEY.")


def _chat_claude(text: str) -> None:
    """Forward message to Claude (Anthropic) and reply. Maintains conversation history."""
    try:
        import anthropic

        _session["claude_history"].append({"role": "user", "content": text})
        _send("⏳ שואל את קלוד...")

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            system=(
                "You are Claude, an AI assistant helping Ariel, the founder of SiteNest — "
                "an automated platform that automatically builds and sells AI-powered websites "
                "for local businesses in Israel. Answer concisely and helpfully. "
                "Respond in the same language the user writes in (Hebrew or English)."
            ),
            messages=_session["claude_history"],
        )
        reply = response.content[0].text
        _session["claude_history"].append({"role": "assistant", "content": reply})
        _send(f"🤖 *Claude:*\n{reply}")
    except Exception:
        logger.exception("[admin_wa] Claude error")
        _send("❌ שגיאה בחיבור לקלוד. בדוק את ה-ANTHROPIC_API_KEY.")


def _chat_gemini(text: str) -> None:
    """Forward message to Gemini (Google) and reply. Maintains conversation history."""
    try:
        import google.generativeai as genai

        _send("⏳ שואל את ג'מיני...")
        genai.configure(api_key=settings.gemini_api_key)

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=(
                "You are Gemini, an AI assistant helping Ariel, the founder of SiteNest — "
                "an automated platform that automatically builds and sells AI-powered websites "
                "for local businesses in Israel. Answer concisely and helpfully. "
                "Respond in the same language the user writes in (Hebrew or English)."
            ),
        )

        # Build Gemini-format history (all messages except the current one)
        gemini_history = []
        for entry in _session["gemini_history"]:
            gemini_history.append({
                "role": entry["role"],
                "parts": entry["parts"],
            })

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(text)
        reply = response.text

        # Store both user and assistant turns
        _session["gemini_history"].append({"role": "user", "parts": [text]})
        _session["gemini_history"].append({"role": "model", "parts": [reply]})

        _send(f"💎 *Gemini:*\n{reply}")
    except Exception:
        logger.exception("[admin_wa] Gemini error")
        _send("❌ שגיאה בחיבור לג'מיני. בדוק את ה-GEMINI_API_KEY.")


# ── Stats helpers ─────────────────────────────────────────────────────────────

def _get_stats(db: Session) -> str:
    """Fetch quick daily stats from DB and format as a WhatsApp message."""
    try:
        import datetime as dt
        from sqlalchemy import cast, func
        from sqlalchemy.types import Date
        from app.models.lead_record import LeadRecord
        from app.models.business import Business
        from app.models.outreach_message import OutreachMessage

        today = dt.date.today()

        total_leads = db.query(func.count(LeadRecord.id)).scalar() or 0
        hot_leads = (
            db.query(func.count(LeadRecord.id))
            .filter(LeadRecord.status.in_(["hot", "super_hot", "boiling_hot"]))
            .scalar() or 0
        )
        boiling = (
            db.query(func.count(LeadRecord.id))
            .filter(LeadRecord.status == "boiling_hot")
            .scalar() or 0
        )
        total_businesses = db.query(func.count(Business.id)).scalar() or 0

        sent_today = (
            db.query(func.count(OutreachMessage.id))
            .filter(cast(OutreachMessage.created_at, Date) == today)
            .filter(OutreachMessage.channel == "whatsapp")
            .scalar() or 0
        )
        replied_today = (
            db.query(func.count(OutreachMessage.id))
            .filter(cast(OutreachMessage.created_at, Date) == today)
            .filter(OutreachMessage.status.in_(["replied", "read"]))
            .scalar() or 0
        )

        now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
        return (
            f"📊 *SiteNest — דוח מהיר*\n"
            f"🗓 {now_str}\n\n"
            f"👥 *לידים:*\n"
            f"  סה\"כ: {total_leads}\n"
            f"  🔥 חמים: {hot_leads}\n"
            f"  🌡 בוערים: {boiling}\n\n"
            f"🏢 *עסקים במערכת:* {total_businesses}\n\n"
            f"📱 *WhatsApp היום:*\n"
            f"  נשלחו: {sent_today}\n"
            f"  ענו: {replied_today}"
        )
    except Exception:
        logger.exception("[admin_wa] _get_stats error")
        return "❌ שגיאה בטעינת הסטטיסטיקות."


def _get_hot_leads(db: Session) -> str:
    """Return the top 10 hot/boiling leads formatted for WhatsApp."""
    try:
        from sqlalchemy import func
        from app.models.lead_record import LeadRecord

        leads = (
            db.query(LeadRecord)
            .filter(LeadRecord.status.in_(["boiling_hot", "super_hot", "hot"]))
            .order_by(LeadRecord.score.desc())
            .limit(10)
            .all()
        )

        if not leads:
            return "✅ אין לידים חמים כרגע."

        _STATUS_EMOJI = {"boiling_hot": "🌡", "super_hot": "⚡️", "hot": "🔥"}
        lines = ["🔥 *לידים חמים (Top 10):*\n"]
        for i, lead in enumerate(leads, 1):
            emoji = _STATUS_EMOJI.get(lead.status, "📌")
            name = getattr(lead, "imported_name", None) or getattr(lead, "name", None) or "—"
            phone = getattr(lead, "phone", "") or ""
            score = getattr(lead, "score", 0) or 0
            lines.append(f"{i}. {emoji} {name} | {phone} | ציון: {score}")

        return "\n".join(lines)
    except Exception:
        logger.exception("[admin_wa] _get_hot_leads error")
        return "❌ שגיאה בטעינת הלידים."


# ── Send helper ───────────────────────────────────────────────────────────────

def _send(text: str) -> None:
    """Send a reply to the admin's WhatsApp phone."""
    owner = (settings.whatsapp_owner_phone or "").strip()
    if not owner:
        logger.warning("[admin_wa] whatsapp_owner_phone not configured — cannot send reply")
        return
    EvolutionWhatsAppService().send_text(owner, text)
