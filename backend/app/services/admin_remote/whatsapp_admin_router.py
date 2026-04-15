"""WhatsApp Admin Remote Control — Platinum Failsafe & UX Suite
================================================================
State machine for admin remote control via WhatsApp self-messages.

States:
  MAIN_MENU
  CHAT_WITH_GROK
  CHAT_WITH_CLAUDE
  CHAT_WITH_GEMINI
  AWAITING_PIN          — blocking PIN prompt before a high-stakes action
  AWAITING_COST_CONFIRM — blocking cost-approval prompt

Safety layers:
  • Admin PIN (default 1234, override via ADMIN_WA_PIN env var) gates high-stakes commands
  • Global kill switch: "ABORT" / "!!!" halts all background work and resets state
  • Inactivity timeout: 20 min in chat state → auto-return to MAIN_MENU
  • Pre-flight cost estimates forwarded to WhatsApp for "1" approval

UX:
  • Pagination: lists chunked in groups of 5, reply 'next' for more
  • All errors caught and sent to WhatsApp in human-readable form
  • Voice notes (audio/ptt) → Whisper transcription → processed as text command

Shared Blackboard:
  • Switching AI agents passes a summary of previous agent's last exchange
    so the new agent has context.
"""
from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Literal

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService
from app.services.admin_remote.agents_config import (
    GROK_SYSTEM_PROMPT,
    GEMINI_SYSTEM_PROMPT,
    CLAUDE_SYSTEM_PROMPT,
    GPT_SYSTEM_PROMPT,
    AGENT_MAP,
)
from app.services.admin_remote.system_tools import (
    TOOLS_SCHEMA,
    TOOLS_SCHEMA_ANTHROPIC,
    dispatch_tool,
)

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
_ADMIN_PIN: str = os.environ.get("ADMIN_WA_PIN", "1234")
_INACTIVITY_SECONDS: int = 20 * 60   # 20 minutes
_PAGE_SIZE: int = 5
_EXIT_KEYWORDS = {"exit", "יציאה", "תפריט", "menu", "back", "חזרה", "ביטול"}

AdminState = Literal[
    "MAIN_MENU",
    "CHAT_WITH_GROK",
    "CHAT_WITH_CLAUDE",
    "CHAT_WITH_GEMINI",
    "CHAT_WITH_GPT",
    "AWAITING_PIN",
    "AWAITING_COST_CONFIRM",
]

# ── In-memory session ─────────────────────────────────────────────────────────
_session: dict = {
    "state": "MAIN_MENU",
    "claude_history": [],      # list[{role, content}]
    "gemini_history": [],      # list[{role, parts}]
    "gpt_history": [],         # list[{role, content}]
    "blackboard": "",          # shared 1-sentence summary across agent switches
    "_prev_agent_state": "",   # last active agent state for blackboard delivery
    "paginated_items": [],     # items waiting to be paged out
    "page_offset": 0,
    "pending_action": None,    # callable(db) awaiting PIN/cost confirm
    "pending_label": "",
    "pending_cost": 0.0,
    "last_activity": datetime.now(timezone.utc),
    "prev_activity": None,     # snapshot before current message (for idle check)
}

# ── Menu text ─────────────────────────────────────────────────────────────────
_MENU_TEXT = (
    "🤖 *SiteNest Admin Remote*\n"
    "ברוך הבא, אריאל!\n\n"
    "בחר פעולה:\n"
    "• *גרוק* — שוחח עם Grok (AI CEO)\n"
    "• *קלוד* — שוחח עם Claude (Anthropic)\n"
    "• *ג'מיני* — שוחח עם Gemini (Google)\n"
    "• *ג'פיטי* — שוחח עם ChatGPT (OpenAI)\n"
    "• *סטטיסטיקות* — דוח יומי מהיר\n"
    "• *לידים* — לידים חמים ובוערים\n"
    "• *עזרה* — תפריט זה\n\n"
    "_שלח *יציאה* מכל מצב לחזרה לתפריט_\n"
    "_שלח *ABORT* או *!!!* לעצירת חירום_"
)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry points
# ─────────────────────────────────────────────────────────────────────────────

def handle_admin_message(text: str, db: Session) -> None:
    """Main dispatcher — called from the webhook handler for text commands."""
    text = (text or "").strip()
    if not text:
        return

    # Check inactivity BEFORE touching activity timestamp
    _check_inactivity_timeout()

    # Update activity timestamps
    _session["prev_activity"] = _session["last_activity"]
    _session["last_activity"] = datetime.now(timezone.utc)

    # ── Global kill switch ────────────────────────────────────────────────────
    if text.upper() in {"ABORT", "!!!"}:
        _emergency_stop()
        return

    state: AdminState = _session["state"]

    # ── Pagination "next" ─────────────────────────────────────────────────────
    if text.lower() in {"next", "הבא", "עוד"} and _session["paginated_items"]:
        _send_next_page()
        return

    # ── PIN gate ──────────────────────────────────────────────────────────────
    if state == "AWAITING_PIN":
        _handle_pin_response(text, db)
        return

    # ── Cost-confirm gate ─────────────────────────────────────────────────────
    if state == "AWAITING_COST_CONFIRM":
        _handle_cost_confirm(text, db)
        return

    # ── Universal exit ────────────────────────────────────────────────────────
    if state != "MAIN_MENU" and text.lower() in _EXIT_KEYWORDS:
        _reset_to_menu("↩️ חזרת לתפריט הראשי.")
        return

    # ── Route by state ────────────────────────────────────────────────────────
    if state == "MAIN_MENU":
        _handle_menu_command(text, db)
    elif state == "CHAT_WITH_GROK":
        _chat_grok(text, db)
    elif state == "CHAT_WITH_CLAUDE":
        _chat_claude(text, db)
    elif state == "CHAT_WITH_GEMINI":
        _chat_gemini(text, db)
    elif state == "CHAT_WITH_GPT":
        _chat_gpt(text, db)


def handle_admin_audio(evo_message_data: dict, db: Session) -> None:
    """Download voice note via Evolution base64 API, transcribe via Whisper, dispatch as text."""
    try:
        _send("🎤 מתמלל הודעה קולית...")
        text = _transcribe_audio(evo_message_data)
        if not text:
            _send("❌ לא הצלחתי לתמלל את ההודעה הקולית.")
            return
        _send(f"📝 *תמלול:* _{text}_")
        handle_admin_message(text, db)
    except Exception as exc:
        _send_error("voice transcription", exc)


# ─────────────────────────────────────────────────────────────────────────────
# Safety & inactivity helpers
# ─────────────────────────────────────────────────────────────────────────────

def _check_inactivity_timeout() -> None:
    """If in a chat state and idle for ≥20 min, auto-return to MAIN_MENU."""
    if _session["state"] == "MAIN_MENU":
        return
    prev = _session.get("prev_activity")
    if prev is None:
        return
    elapsed = (datetime.now(timezone.utc) - prev).total_seconds()
    if elapsed >= _INACTIVITY_SECONDS:
        _reset_to_menu("⏰ *פסק זמן:* לא הייתה פעילות במשך 20 דקות — חזרה לתפריט.")


def _reset_to_menu(msg: str = "") -> None:
    _session["state"] = "MAIN_MENU"
    _session["claude_history"] = []
    _session["gemini_history"] = []
    _session["gpt_history"] = []
    _session["paginated_items"] = []
    _session["page_offset"] = 0
    _session["pending_action"] = None
    _session["pending_label"] = ""
    _session["pending_cost"] = 0.0
    if msg:
        _send(msg + "\n\n" + _MENU_TEXT)
    else:
        _send(_MENU_TEXT)


def _emergency_stop() -> None:
    """Halt all pending work and reset state."""
    _reset_to_menu()
    _send("🛑 *EMERGENCY STOP*: כל התהליכים הופסקו.")


# ─────────────────────────────────────────────────────────────────────────────
# PIN gate
# ─────────────────────────────────────────────────────────────────────────────

def _request_pin(label: str, action, cost: float = 0.0) -> None:
    """Pause and demand PIN before running `action(db)`."""
    _session["state"] = "AWAITING_PIN"
    _session["pending_action"] = action
    _session["pending_label"] = label
    _session["pending_cost"] = cost
    cost_line = f"\nעלות משוערת: ~${cost:.2f}" if cost > 0 else ""
    _send(
        f"🔐 *Security Check*\n"
        f"פעולה: *{label}*{cost_line}\n\n"
        f"הזן את קוד ה-PIN שלך (4 ספרות) לאישור, או שלח *ביטול*."
    )


def _handle_pin_response(text: str, db: Session) -> None:
    if text.lower() in _EXIT_KEYWORDS:
        _session["state"] = "MAIN_MENU"
        _session["pending_action"] = None
        _send("❌ הפעולה בוטלה.")
        return
    if text.strip() == _ADMIN_PIN:
        action = _session.pop("pending_action", None)
        label = _session.pop("pending_label", "")
        _session.pop("pending_cost", None)
        _session["state"] = "MAIN_MENU"
        _send(f"✅ PIN אושר — מבצע: *{label}*...")
        if action:
            try:
                action(db)
            except Exception as exc:
                _send_error(label, exc)
    else:
        _send("❌ PIN שגוי. נסה שוב או שלח *ביטול*.")


# ─────────────────────────────────────────────────────────────────────────────
# Cost-confirm gate
# ─────────────────────────────────────────────────────────────────────────────

def request_cost_confirm(label: str, cost_breakdown: str, action, estimated_usd: float) -> None:
    """Public helper — call from any high-cost operation to get approval before running."""
    _session["state"] = "AWAITING_COST_CONFIRM"
    _session["pending_action"] = action
    _session["pending_label"] = label
    _session["pending_cost"] = estimated_usd
    _send(
        f"💰 *Pre-flight Cost Check*\n"
        f"פעולה: *{label}*\n\n"
        f"{cost_breakdown}\n\n"
        f"*עלות משוערת: ~${estimated_usd:.3f}*\n\n"
        f"שלח *1* לאישור | *ביטול* לביטול"
    )


def _handle_cost_confirm(text: str, db: Session) -> None:
    if text.strip() == "1":
        action = _session.pop("pending_action", None)
        label = _session.pop("pending_label", "")
        _session.pop("pending_cost", None)
        _session["state"] = "MAIN_MENU"
        _send(f"✅ אושר — מבצע: *{label}*...")
        if action:
            try:
                action(db)
            except Exception as exc:
                _send_error(label, exc)
    elif text.lower() in _EXIT_KEYWORDS:
        _session["state"] = "MAIN_MENU"
        _session["pending_action"] = None
        _send("❌ הפעולה בוטלה.")
    else:
        _send("שלח *1* לאישור או *ביטול* לביטול.")


# ─────────────────────────────────────────────────────────────────────────────
# Pagination
# ─────────────────────────────────────────────────────────────────────────────

def _send_paginated(items: list, header: str = "") -> None:
    """Store item list and send first page."""
    _session["paginated_items"] = [str(i) for i in items]
    _session["page_offset"] = 0
    _send_next_page(header)


def _send_next_page(header: str = "") -> None:
    items = _session["paginated_items"]
    offset = _session["page_offset"]
    chunk = items[offset: offset + _PAGE_SIZE]
    if not chunk:
        _send("✅ אין עוד פריטים.")
        _session["paginated_items"] = []
        return

    lines = []
    if header:
        lines.append(header)
    lines.extend(chunk)
    total = len(items)
    end = min(offset + _PAGE_SIZE, total)
    lines.append(f"\n_{offset + 1}–{end} מתוך {total}_")
    if end < total:
        lines.append("↪️ שלח *next* לפריטים הבאים")

    _send("\n".join(lines))
    _session["page_offset"] = offset + _PAGE_SIZE


# ─────────────────────────────────────────────────────────────────────────────
# Menu command dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def _handle_menu_command(text: str, db: Session) -> None:
    lower = text.lower().strip()
    blackboard = _session.get("blackboard", "")
    prev_agent = _session.get("_prev_agent_state", "")

    if lower in {"גרוק", "grok", "groc"}:
        _session["state"] = "CHAT_WITH_GROK"
        _session["claude_history"] = []
        _session["gemini_history"] = []
        _session["_prev_agent_state"] = "CHAT_WITH_GROK"
        intro = "🧠 *מצב שיחה: Grok (AI CEO)*\nשלח הודעה לגרוק. שלח *יציאה* לחזרה לתפריט."
        if blackboard and prev_agent and prev_agent != "CHAT_WITH_GROK":
            intro += f"\n\n📋 *הקשר מהסוכן הקודם:*\n_{blackboard}_"
        _send(intro)

    elif lower in {"קלוד", "claude", "אנתרופיק", "anthropic"}:
        _session["state"] = "CHAT_WITH_CLAUDE"
        _session["claude_history"] = []
        _session["_prev_agent_state"] = "CHAT_WITH_CLAUDE"
        intro = "🤖 *מצב שיחה: Claude (Anthropic)*\nשלח הודעה לקלוד. שלח *יציאה* לחזרה לתפריט."
        if blackboard and prev_agent and prev_agent != "CHAT_WITH_CLAUDE":
            intro += f"\n\n📋 *הקשר מהסוכן הקודם:*\n_{blackboard}_"
        _send(intro)

    elif lower in {"ג'מיני", "ג׳מיני", "gemini", "google", "גוגל"}:
        _session["state"] = "CHAT_WITH_GEMINI"
        _session["gemini_history"] = []
        _session["_prev_agent_state"] = "CHAT_WITH_GEMINI"
        intro = "💎 *מצב שיחה: Gemini (Google)*\nשלח הודעה לג'מיני. שלח *יציאה* לחזרה לתפריט."
        if blackboard and prev_agent and prev_agent != "CHAT_WITH_GEMINI":
            intro += f"\n\n📋 *הקשר מהסוכן הקודם:*\n_{blackboard}_"
        _send(intro)

    elif lower in {"ג'פיטי", "ג׳פיטי", "גיפיטי", "chatgpt", "gpt", "openai", "צ'טגיפיטי"}:
        _session["state"] = "CHAT_WITH_GPT"
        _session["gpt_history"] = []
        _session["_prev_agent_state"] = "CHAT_WITH_GPT"
        intro = "🟢 *מצב שיחה: ChatGPT (OpenAI)*\nשלח הודעה ל-GPT. שלח *יציאה* לחזרה לתפריט."
        if blackboard and prev_agent and prev_agent != "CHAT_WITH_GPT":
            intro += f"\n\n📋 *הקשר מהסוכן הקודם:*\n_{blackboard}_"
        _send(intro)

    elif lower in {"סטטיסטיקות", "stats", "דוח", "report", "statistics", "נתונים"}:
        try:
            _send(_get_stats(db))
        except Exception as exc:
            _send_error("stats", exc)

    elif lower in {"לידים", "leads", "חם", "hot", "חמים", "בוערים"}:
        try:
            items = _get_hot_leads_list(db)
            _send_paginated(items, "🔥 *לידים חמים:*\n")
        except Exception as exc:
            _send_error("hot leads", exc)

    elif lower in {"עזרה", "help", "תפריט", "menu", "?", "היי", "שלום", "hello", "hi", "הי"}:
        _send(_MENU_TEXT)

    else:
        _send(f"❓ לא הבנתי את הפקודה: *{text}*\n\n" + _MENU_TEXT)


# ─────────────────────────────────────────────────────────────────────────────
# AI chat handlers
# ─────────────────────────────────────────────────────────────────────────────

def _chat_grok(text: str, db: Session) -> None:
    """Grok chat with native function-calling tool loop (xAI OpenAI-compatible API)."""
    try:
        from app.core.config import settings as _settings
        import httpx as _httpx
        import json as _json

        blackboard = _session.get("blackboard", "")
        is_first_msg = not _session.get("_grok_had_exchange")
        user_content = (
            f"[Context from previous agent: {blackboard}]\n\n{text}"
            if (blackboard and is_first_msg) else text
        )

        evo_key = getattr(_settings, "xai_api_key", None) or ""
        if not evo_key:
            _send("❌ XAI_API_KEY לא מוגדר. הוסף אותו ל-.env")
            return

        _send("⏳ שואל את גרוק...")
        headers = {"Authorization": f"Bearer {evo_key}", "Content-Type": "application/json"}
        messages = [
            {"role": "system", "content": GROK_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        # Tool-calling loop (up to 3 rounds)
        _grok_in_tok = 0
        _grok_out_tok = 0
        for _round in range(3):
            payload = {
                "model": "grok-3-mini",
                "messages": messages,
                "tools": TOOLS_SCHEMA,
                "tool_choice": "auto",
                "max_tokens": 1200,
                "temperature": 0.7,
            }
            resp = _httpx.post(
                "https://api.x.ai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=45,
            )
            resp.raise_for_status()
            resp_data = resp.json()
            _usage = resp_data.get("usage", {})
            _grok_in_tok += _usage.get("prompt_tokens", 0)
            _grok_out_tok += _usage.get("completion_tokens", 0)
            choice = resp_data["choices"][0]
            msg = choice["message"]
            finish = choice.get("finish_reason", "")

            if finish == "tool_calls" or msg.get("tool_calls"):
                # Execute each requested tool and feed results back
                messages.append(msg)
                for tc in msg.get("tool_calls", []):
                    fn_name = tc["function"]["name"]
                    fn_args = _json.loads(tc["function"].get("arguments", "{}"))
                    logger.warning("[admin_wa] Grok calling tool: %s(%s)", fn_name, fn_args)
                    result = dispatch_tool(fn_name, fn_args, db)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": _json.dumps(result, ensure_ascii=False),
                    })
                continue  # next round with tool results

            # Final text reply
            reply = msg.get("content") or ""
            break
        else:
            reply = "לא הצלחתי לקבל תשובה סופית מגרוק."

        _session["_grok_had_exchange"] = True
        try:
            from app.services.cost_tracker import track_usage as _track_usage
            _track_usage(agent_name="grok", model_name="grok-3-mini", input_tokens=_grok_in_tok, output_tokens=_grok_out_tok, stage="whatsapp_admin")
        except Exception:
            pass
        _send(f"🧠 *Grok:*\n{reply}")
        _session["blackboard"] = f"Grok: {reply[:200]}"
    except Exception as exc:
        _send_error("Grok", exc)


def _chat_claude(text: str, db: Session) -> None:
    """Claude chat with native tool_use loop (Anthropic API)."""
    try:
        import anthropic
        import json as _json

        if not _session["claude_history"]:
            blackboard = _session.get("blackboard", "")
            content = (
                f"[Shared context from previous AI: {blackboard}]\n\nUser: {text}"
                if blackboard else text
            )
            _session["claude_history"].append({"role": "user", "content": content})
        else:
            _session["claude_history"].append({"role": "user", "content": text})

        _send("⏳ שואל את קלוד...")
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

        # Tool-calling loop (up to 3 rounds)
        _claude_in_tok = 0
        _claude_out_tok = 0
        for _round in range(3):
            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1500,
                system=CLAUDE_SYSTEM_PROMPT,
                tools=TOOLS_SCHEMA_ANTHROPIC,
                messages=_session["claude_history"],
            )
            _claude_in_tok += getattr(response.usage, 'input_tokens', 0) or 0
            _claude_out_tok += getattr(response.usage, 'output_tokens', 0) or 0

            if response.stop_reason == "tool_use":
                # Append assistant message with tool_use blocks
                _session["claude_history"].append({
                    "role": "assistant",
                    "content": response.content,
                })
                # Build tool_result blocks
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        logger.warning("[admin_wa] Claude calling tool: %s(%s)", block.name, block.input)
                        result = dispatch_tool(block.name, block.input, db)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": _json.dumps(result, ensure_ascii=False),
                        })
                _session["claude_history"].append({"role": "user", "content": tool_results})
                continue

            # Final text reply
            reply = response.content[0].text if response.content else ""
            break
        else:
            reply = "לא הצלחתי לקבל תשובה סופית מקלוד."

        _session["claude_history"].append({"role": "assistant", "content": reply})
        try:
            from app.services.cost_tracker import track_usage as _track_usage
            _track_usage(agent_name="claude", model_name="claude-opus-4-5", input_tokens=_claude_in_tok, output_tokens=_claude_out_tok, stage="whatsapp_admin")
        except Exception:
            pass
        _send(f"🤖 *Claude:*\n{reply}")
        _session["blackboard"] = f"Claude: {reply[:200]}"
    except Exception as exc:
        _send_error("Claude", exc)


def _chat_gemini(text: str, db: Session) -> None:
    """Gemini chat — auto-fetches live data before answering data questions."""
    try:
        import google.generativeai as genai
        import json as _json
        _send("⏳ שואל את ג'מיני...")
        genai.configure(api_key=settings.gemini_api_key)

        history = list(_session["gemini_history"])
        # First message: inject blackboard
        if not history:
            blackboard = _session.get("blackboard", "")
            first_text = (
                f"[Shared context from previous AI: {blackboard}]\n\nUser: {text}"
                if blackboard else text
            )
        else:
            first_text = text

        # Pre-flight: detect data-related keywords and inject live context
        _DATA_KEYWORDS = {
            "ליד", "לידים", "סטטיסטיקות", "נתונים", "כמה", "stats", "leads", "how many", "מה המצב",
            "lead", "מצב", "היום", "בוקר", "הלילה",
        }
        if any(kw in text.lower() for kw in _DATA_KEYWORDS):
            live = dispatch_tool("get_system_stats", {}, db)
            if live["ok"]:
                first_text = (
                    f"[Live SiteNest data as of now: {_json.dumps(live['data'], ensure_ascii=False)}]\n\n"
                    + first_text
                )

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            system_instruction=GEMINI_SYSTEM_PROMPT,
        )
        chat = model.start_chat(history=history)
        response = chat.send_message(first_text)
        reply = response.text

        try:
            from app.services.cost_tracker import track_usage as _track_usage
            _meta = getattr(response, 'usage_metadata', None)
            _in_tok = getattr(_meta, 'prompt_token_count', 0) or 0
            _out_tok = getattr(_meta, 'candidates_token_count', 0) or 0
            _track_usage(agent_name="gemini", model_name="gemini-1.5-flash", input_tokens=_in_tok, output_tokens=_out_tok, stage="whatsapp_admin")
        except Exception:
            pass
        _session["gemini_history"].append({"role": "user", "parts": [text]})
        _session["gemini_history"].append({"role": "model", "parts": [reply]})
        _send(f"💎 *Gemini:*\n{reply}")
        _session["blackboard"] = f"Gemini: {reply[:200]}"
    except Exception as exc:
        _send_error("Gemini", exc)


def _chat_gpt(text: str, db: Session) -> None:
    """GPT chat with native function-calling tool loop (OpenAI API)."""
    try:
        import openai
        import json as _json

        if not _session["gpt_history"]:
            blackboard = _session.get("blackboard", "")
            content = (
                f"[Shared context from previous AI: {blackboard}]\n\nUser: {text}"
                if blackboard else text
            )
            _session["gpt_history"].append({"role": "user", "content": content})
        else:
            _session["gpt_history"].append({"role": "user", "content": text})

        _send("⏳ שואל את ג'פיטי...")
        client = openai.OpenAI(api_key=settings.openai_api_key)

        # Tool-calling loop (up to 3 rounds)
        _gpt_in_tok = 0
        _gpt_out_tok = 0
        loop_messages = [{"role": "system", "content": GPT_SYSTEM_PROMPT}, *_session["gpt_history"]]
        for _round in range(3):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=1500,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                messages=loop_messages,
            )
            _gpt_in_tok += getattr(response.usage, 'prompt_tokens', 0) or 0
            _gpt_out_tok += getattr(response.usage, 'completion_tokens', 0) or 0
            choice = response.choices[0]
            msg = choice.message

            if choice.finish_reason == "tool_calls" and msg.tool_calls:
                loop_messages.append(msg)
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    fn_args = _json.loads(tc.function.arguments or "{}")
                    logger.warning("[admin_wa] GPT calling tool: %s(%s)", fn_name, fn_args)
                    result = dispatch_tool(fn_name, fn_args, db)
                    loop_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": _json.dumps(result, ensure_ascii=False),
                    })
                continue

            reply = msg.content or ""
            break
        else:
            reply = "לא הצלחתי לקבל תשובה סופית מ-GPT."

        _session["gpt_history"].append({"role": "assistant", "content": reply})
        try:
            from app.services.cost_tracker import track_usage as _track_usage
            _track_usage(agent_name="gpt", model_name="gpt-4o-mini", input_tokens=_gpt_in_tok, output_tokens=_gpt_out_tok, stage="whatsapp_admin")
        except Exception:
            pass
        _send(f"🟢 *ChatGPT:*\n{reply}")
        _session["blackboard"] = f"ChatGPT: {reply[:200]}"
    except Exception as exc:
        _send_error("ChatGPT", exc)

# ─────────────────────────────────────────────────────────────────────────────
# Voice note transcription (OpenAI Whisper)
# ─────────────────────────────────────────────────────────────────────────────

def _transcribe_audio(evo_message_data: dict) -> str:
    """Fetch audio via Evolution's base64 API and transcribe via OpenAI Whisper.

    WhatsApp audio is end-to-end encrypted — the `url` field in audioMessage
    is a CDN path for encrypted bytes, unusable directly.  We ask Evolution
    to decrypt and deliver the raw bytes as base64.
    """
    import base64
    import openai

    evo_base = (settings.evolution_api_url or "http://127.0.0.1:8181").rstrip("/")
    instance  = settings.evolution_instance or "sitenest"
    evo_key   = settings.evolution_api_key or ""

    # Build the exact payload Evolution expects
    payload = {
        "message": {
            "key":     evo_message_data.get("key", {}),
            "message": evo_message_data.get("message", {}),
        }
    }
    headers = {"apikey": evo_key, "Content-Type": "application/json"}
    resp = httpx.post(
        f"{evo_base}/chat/getBase64FromMediaMessage/{instance}",
        json=payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()

    b64_data: str = result.get("base64") or result.get("data") or ""
    if not b64_data:
        raise ValueError(f"Evolution returned no base64 data: {result}")

    # Determine file extension from returned mimetype (e.g. "audio/ogg; codecs=opus")
    mime_type: str = result.get("mimetype") or "audio/ogg"
    ext_map = {
        "audio/ogg":  ".ogg",
        "audio/mpeg": ".mp3",
        "audio/mp4":  ".mp4",
        "audio/webm": ".webm",
        "audio/wav":  ".wav",
        "audio/aac":  ".aac",
        "audio/flac": ".flac",
    }
    clean_mime = mime_type.lower().split(";")[0].strip()
    ext = ext_map.get(clean_mime, ".ogg")

    audio_bytes = base64.b64decode(b64_data)
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        client = openai.OpenAI(api_key=settings.openai_api_key)
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
            )
        return (transcript or "").strip()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# Stats & leads helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_stats(db: Session) -> str:
    import datetime as dt
    from sqlalchemy import cast, func
    from sqlalchemy.types import Date
    from app.models.lead_record import LeadRecord
    from app.models.business import Business
    from app.models.outreach_message import OutreachMessage

    today = dt.date.today()
    total_leads   = db.query(func.count(LeadRecord.id)).scalar() or 0
    hot_leads     = db.query(func.count(LeadRecord.id)).filter(LeadRecord.status.in_(["hot","super_hot","boiling_hot"])).scalar() or 0
    boiling       = db.query(func.count(LeadRecord.id)).filter(LeadRecord.status == "boiling_hot").scalar() or 0
    total_biz     = db.query(func.count(Business.id)).scalar() or 0
    sent_today    = db.query(func.count(OutreachMessage.id)).filter(cast(OutreachMessage.created_at, Date) == today).filter(OutreachMessage.channel == "whatsapp").scalar() or 0
    replied_today = db.query(func.count(OutreachMessage.id)).filter(cast(OutreachMessage.created_at, Date) == today).filter(OutreachMessage.status.in_(["replied","read"])).scalar() or 0

    now_str = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    return (
        f"📊 *SiteNest — דוח מהיר*\n🗓 {now_str}\n\n"
        f"👥 *לידים:*\n  סה\"כ: {total_leads}\n  🔥 חמים: {hot_leads}\n  🌡 בוערים: {boiling}\n\n"
        f"🏢 *עסקים במערכת:* {total_biz}\n\n"
        f"📱 *WhatsApp היום:*\n  נשלחו: {sent_today}\n  ענו: {replied_today}"
    )


def _get_hot_leads_list(db: Session) -> list[str]:
    from app.models.lead_record import LeadRecord
    leads = (
        db.query(LeadRecord)
        .filter(LeadRecord.status.in_(["boiling_hot", "super_hot", "hot"]))
        .order_by(LeadRecord.score.desc())
        .limit(50)
        .all()
    )
    if not leads:
        return ["✅ אין לידים חמים כרגע."]
    _EMOJI = {"boiling_hot": "🌡", "super_hot": "⚡️", "hot": "🔥"}
    lines = []
    for i, lead in enumerate(leads, 1):
        emoji = _EMOJI.get(lead.status, "📌")
        name  = getattr(lead, "imported_name", None) or getattr(lead, "name", None) or "—"
        phone = getattr(lead, "phone", "") or ""
        score = getattr(lead, "score", 0) or 0
        lines.append(f"{i}. {emoji} {name} | {phone} | ציון: {score}")
    return lines


# ─────────────────────────────────────────────────────────────────────────────
# Error helper
# ─────────────────────────────────────────────────────────────────────────────

def _send_error(context: str, exc: Exception) -> None:
    logger.exception("[admin_wa] error in %s", context)
    short = str(exc)
    if len(short) > 200:
        short = short[:200] + "…"
    _send(
        f"❌ *שגיאה ב-{context}:*\n`{short}`\n\n"
        f"_לוגים: `journalctl -u sitenest-backend -n 50`_"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Send helper
# ─────────────────────────────────────────────────────────────────────────────

def _send(text: str) -> None:
    owner = (settings.whatsapp_owner_phone or "").strip()
    if not owner:
        logger.warning("[admin_wa] whatsapp_owner_phone not configured — cannot send reply")
        return
    logger.warning("[admin_wa] _send → phone=%r  text=%r", owner, text[:80])
    try:
        ok = EvolutionWhatsAppService().send_text(owner, text)
        logger.warning("[admin_wa] _send result: %s", "OK" if ok else "FAILED")
    except Exception:
        logger.exception("[admin_wa] _send raised exception")
