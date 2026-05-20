"""TAZO AI Voice Bot — Whisper STT + GPT-4o-mini + Google TTS (Hebrew).

Flow:
  1. Caller phone looked up in DB → CallerContext built (existing customer / lead / new)
  2. Bot speaks personalised <Say language="he-IL"> greeting + <Record>
  3. Twilio POSTs RecordingUrl → /ai-voice-record
  4. Download MP3 → OpenAI Whisper (language=he) → Hebrew transcript
  5. Transcript → GPT-4o-mini (with context) → Hebrew reply
  6. If reply / speech contains link request → send SMS/WhatsApp link
  7. If farewell detected → Hangup + save lead to DemoRequestLog
  8. Otherwise → return TwiML: <Say> reply + <Record> for next turn

v2 upgrades:
  - Caller identification via DB (CustomerAccount / LeadRecord)
  - Personalised greeting and system prompt per caller type
  - SMS/WhatsApp link sending when user requests registration
  - Lead auto-saved to DemoRequestLog on call end
"""
from __future__ import annotations

import asyncio
import datetime
import io
import logging
import re
import threading
import time
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

import httpx
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Caller context ────────────────────────────────────────────────────────────

@dataclass
class CallerContext:
    is_customer: bool = False
    is_lead: bool = False
    contact_name: str = ""
    business_name: str = ""
    package_name: str = ""
    business_category: str = ""
    business_city: str = ""


def _normalize_phone_variants(phone: str) -> list[str]:
    digits = re.sub(r"\D", "", phone or "")
    variants: set[str] = {phone}
    if digits.startswith("972") and len(digits) >= 12:
        local = "0" + digits[3:]
        variants |= {"+" + digits, digits, local}
    elif digits.startswith("0") and len(digits) == 10:
        intl = "972" + digits[1:]
        variants |= {"+" + intl, intl, digits}
    return list(variants)


def _lookup_caller_sync(phone: str) -> CallerContext:
    from app.db.session import SessionLocal
    from app.models.customer_account import CustomerAccount
    from app.models.lead_record import LeadRecord

    ctx = CallerContext()
    variants = _normalize_phone_variants(phone)
    db = SessionLocal()
    try:
        ca = (
            db.query(CustomerAccount)
            .filter(CustomerAccount.phone.in_(variants))
            .first()
        )
        if ca:
            ctx.is_customer = True
            ctx.contact_name = ca.contact_name or ""
            ctx.package_name = ca.package_name or ""
            biz = ca.business  # eager/lazy loaded
            if biz:
                ctx.business_name = biz.name or ""
                ctx.business_category = biz.category or ""
                ctx.business_city = biz.city or ""
            return ctx

        lead = (
            db.query(LeadRecord)
            .filter(LeadRecord.phone.in_(variants))
            .first()
        )
        if lead:
            ctx.is_lead = True
            ctx.contact_name = lead.imported_name or ""
            ctx.business_category = lead.category or ""
            ctx.business_city = lead.city or ""
    except Exception as exc:
        logger.warning("[AIVoiceBot] DB lookup error: %s", exc)
    finally:
        db.close()
    return ctx


async def _lookup_caller(phone: str) -> CallerContext:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _lookup_caller_sync, phone)


# ── Dynamic system prompt ─────────────────────────────────────────────────────

def _build_system(ctx: CallerContext) -> str:
    lines = [
        "אתה נציג שירות לקוחות של חברת TAZO"
        " — פלטפורמה המסייעת לעסקים מקומיים לנהל את הנוכחות הדיגיטלית שלהם.",
        "שמך הוא טאזו.",
        "",
    ]
    if ctx.is_customer:
        lines.append("=== מידע על המתקשר (לקוח קיים) ===")
        if ctx.contact_name:
            lines.append(f"שם: {ctx.contact_name}")
        if ctx.business_name:
            lines.append(f"עסק: {ctx.business_name}")
        if ctx.business_category:
            lines.append(f"קטגוריה: {ctx.business_category}")
        if ctx.business_city:
            lines.append(f"עיר: {ctx.business_city}")
        if ctx.package_name:
            lines.append(f"חבילה פעילה: {ctx.package_name}")
        lines.append("המתקשר הוא לקוח קיים של TAZO — ברך אותו בשמו ועזור בחום.")
        lines.append("")
    elif ctx.is_lead:
        lines.append("=== מידע על המתקשר (ליד ידוע) ===")
        if ctx.contact_name:
            lines.append(f"שם: {ctx.contact_name}")
        if ctx.business_category:
            lines.append(f"קטגוריה: {ctx.business_category}")
        if ctx.business_city:
            lines.append(f"עיר: {ctx.business_city}")
        lines.append("המתקשר פנה אלינו בעבר — עודד אותו להצטרף ל-TAZO.")
        lines.append("")
    lines += [
        "כללים חשובים:",
        "1. ענה אך ורק בעברית תקינה.",
        "2. תשובות קצרות ותמציתיות — עד 2 משפטים בלבד (שיחת טלפון!).",
        "3. היה ידידותי, חם ומקצועי.",
        "4. אם הלקוח אומר להתראות / ביי / תודה / לא מעניין / לא רוצה —",
        "   ענה בדיוק: 'תודה שפנית, יום נעים. להתראות!' ואל תוסיף שאלות.",
        "5. TAZO מאפשרת לעסקים: קבלת הזמנות דרך WhatsApp, דף עסקי מקצועי,",
        "   ניהול לקוחות ונאמנות, שיווק אוטומטי וסטטיסטיקות.",
        "6. אם הלקוח מבקש קישור / הרשמה / רישום / להצטרף / לתבוע עסק —",
        "   כלול [SEND_LINK] בתחילת תגובתך ואחר כך המשך.",
        "7. אם הלקוח מתעניין — שאל שם ומספר טלפון לחזרה.",
        "8. אל תחשוף מידע פנימי: מחירים מדויקים, API, קוד, שמות לקוחות,",
        "   פרטי שרת. אם שואלים — אמור שהצוות יחזור.",
        "9. אל תדון בנושאים שאינם קשורים לשירות.",
        "10. אם אינך יודע — אמור שהצוות יחזור בהקדם.",
    ]
    return "\n".join(lines)


# ── Session ───────────────────────────────────────────────────────────────────

_FAREWELL_WORDS = ("להתראות", "ביי", "bye", "תודה ביי")


@dataclass
class _Session:
    call_sid: str
    caller_phone: str
    context: CallerContext = field(default_factory=CallerContext)
    messages: list = field(default_factory=list)
    empty_turns: int = 0
    link_sent: bool = False
    collected_name: str = ""
    created_at: float = field(default_factory=time.time)


_sessions: dict[str, _Session] = {}
_lock = threading.Lock()


def _get_or_create(call_sid: str, caller_phone: str) -> _Session:
    with _lock:
        if call_sid not in _sessions:
            _sessions[call_sid] = _Session(call_sid, caller_phone)
        return _sessions[call_sid]


def _cleanup() -> None:
    cutoff = time.time() - 900
    with _lock:
        stale = [k for k, v in _sessions.items() if v.created_at < cutoff]
        for k in stale:
            del _sessions[k]


# ── TwiML helpers ─────────────────────────────────────────────────────────────

def _record_url() -> str:
    return settings.api_base_url.rstrip("/") + "/api/v1/webhooks/twilio/ai-voice-record"


def _say(text: str) -> str:
    return f'<Say language="he-IL">{escape(text)}</Say>'


def _record(timeout: int = 3) -> str:
    url = escape(_record_url())
    return (
        f'<Record action="{url}" method="POST" '
        f'maxLength="30" timeout="{timeout}" '
        f'playBeep="false" trim="trim-silence"/>'
        f'<Redirect method="POST">{url}</Redirect>'
    )


def _wrap(body: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>'


def _speak_and_listen(text: str) -> str:
    return _wrap(_say(text) + _record())


# ── Whisper STT ───────────────────────────────────────────────────────────────

async def _transcribe(recording_url: str) -> str:
    await asyncio.sleep(0.3)
    auth = (
        settings.twilio_api_key_sid or settings.twilio_account_sid,
        settings.twilio_api_key_secret or settings.twilio_auth_token,
    )
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(recording_url + ".mp3", auth=auth)
            resp.raise_for_status()
            audio_bytes = resp.content
    except Exception as exc:
        logger.error("[AIVoiceBot] Download failed: %s", exc)
        return ""
    try:
        oai = AsyncOpenAI(api_key=settings.openai_api_key)
        transcript = await oai.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.mp3", io.BytesIO(audio_bytes), "audio/mpeg"),
            language="he",
        )
        text = transcript.text.strip()
        logger.info("[AIVoiceBot] Whisper: %r", text)
        return text
    except Exception as exc:
        logger.error("[AIVoiceBot] Whisper error: %s", exc)
        return ""


# ── GPT reply ─────────────────────────────────────────────────────────────────

async def _gpt_reply(session: _Session) -> str:
    try:
        oai = AsyncOpenAI(api_key=settings.openai_api_key)
        result = await oai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": _build_system(session.context)}]
            + session.messages[-20:],
            max_tokens=150,
            temperature=0.7,
        )
        return result.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("[AIVoiceBot] GPT error: %s", exc)
        return "סליחה, יש תקלה טכנית רגעית."


# ── SMS / WhatsApp link sender ────────────────────────────────────────────────

_REGISTRATION_LINK = "https://tazo-web.com"
_LINK_MESSAGE = (
    "שלום מ-TAZO!\n"
    "הנה הקישור שלך להצטרפות ולתביעת העסק שלך:\n"
    "{link}\n\n"
    "שאלות? אנחנו כאן בשבילך!"
)


def _send_link_sync(phone: str) -> bool:
    message = _LINK_MESSAGE.format(link=_REGISTRATION_LINK)

    # 1. Try Meta WhatsApp
    try:
        from app.services.communications.meta_whatsapp_service import MetaWhatsAppService
        wa = MetaWhatsAppService()
        if wa._is_configured():
            ok = wa.send_text(phone, message)
            if ok:
                logger.info("[AIVoiceBot] WhatsApp link sent to %s***", (phone or "")[:7])
                return True
    except Exception:
        pass

    # 2. Twilio SMS fallback
    try:
        from twilio.rest import Client as TwilioClient  # type: ignore[import]
        client = TwilioClient(
            settings.twilio_account_sid,
            settings.twilio_auth_token,
        )
        client.messages.create(
            body=message,
            from_=settings.twilio_from_number,
            to=phone,
        )
        logger.info("[AIVoiceBot] SMS link sent to %s***", (phone or "")[:7])
        return True
    except Exception as exc:
        logger.warning("[AIVoiceBot] Failed to send link: %s", exc)
        return False


async def _send_link(phone: str) -> bool:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _send_link_sync, phone)


# ── Lead saving ───────────────────────────────────────────────────────────────

def _save_lead_sync(session: _Session) -> None:
    if session.context.is_customer:
        return
    if not session.caller_phone:
        return

    business_name = session.context.business_name or session.collected_name or "לא ידוע"
    try:
        from app.db.session import SessionLocal
        from app.models.demo_request_log import DemoRequestLog

        db = SessionLocal()
        try:
            existing = (
                db.query(DemoRequestLog)
                .filter(DemoRequestLog.customer_phone == session.caller_phone)
                .order_by(DemoRequestLog.created_at.desc())
                .first()
            )
            if existing:
                age = (datetime.datetime.utcnow() - existing.created_at).total_seconds()
                if age < 3600:
                    return

            log = DemoRequestLog(
                customer_phone=session.caller_phone,
                business_name=business_name,
                city=session.context.business_city or None,
                category=session.context.business_category or None,
                status="voice_call_lead",
                onboarding_state="ai_bot_contacted",
                notes=(
                    f"AI voice bot — {len(session.messages)} turns"
                    + (" — link sent" if session.link_sent else "")
                ),
            )
            db.add(log)
            db.commit()
            logger.info(
                "[AIVoiceBot] Lead saved: %s*** (%d turns)",
                session.caller_phone[:7], len(session.messages),
            )
        finally:
            db.close()
    except Exception as exc:
        logger.warning("[AIVoiceBot] Failed to save lead: %s", exc)


async def _save_lead(session: _Session) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _save_lead_sync, session)


# ── Link request detection ────────────────────────────────────────────────────

_LINK_TRIGGER_WORDS = (
    "קישור", "לינק", "link", "הרשמה", "רישום", "להצטרף", "להירשם",
    "לתבוע", "תביעה", "להכנס למערכת", "להיכנס למערכת",
    "שלח לי", "תשלח לי", "sms", "אסמס", "וואטסאפ", "whatsapp",
)


def _wants_link(text: str) -> bool:
    lower = text.lower()
    return any(w in lower for w in _LINK_TRIGGER_WORDS)


# ── Public API ────────────────────────────────────────────────────────────────

async def greeting_twiml(call_sid: str, caller_phone: str) -> str:
    session = _get_or_create(call_sid, caller_phone)

    if not session.messages:
        ctx = await _lookup_caller(caller_phone)
        session.context = ctx
        logger.info(
            "[AIVoiceBot] call=%s phone=%s*** customer=%s lead=%s name=%r",
            call_sid[:8], caller_phone[:7],
            ctx.is_customer, ctx.is_lead, ctx.contact_name,
        )

        if ctx.is_customer and ctx.contact_name:
            first = ctx.contact_name.split()[0]
            biz_part = f" בנושא {ctx.business_name}" if ctx.business_name else ""
            opening = f"שלום {first}! שמחים שהתקשרת. כיצד אוכל לעזור לך היום{biz_part}?"
        elif ctx.is_customer:
            opening = "שלום! שמחים שהתקשרת לשירות הלקוחות של TAZO. כיצד אוכל לעזור?"
        elif ctx.is_lead and ctx.contact_name:
            first = ctx.contact_name.split()[0]
            opening = f"שלום {first}! אני טאזו מ-TAZO. שמחה לדבר איתך! כיצד אוכל לעזור?"
        else:
            opening = (
                "שלום! הגעת לשירות הלקוחות של TAZO. "
                "אני טאזו, כאן כדי לעזור. "
                "כיצד אוכל לסייע לך היום?"
            )

        session.messages.append({"role": "assistant", "content": opening})
    else:
        opening = session.messages[0]["content"]

    return _speak_and_listen(opening)


async def respond_from_recording(
    call_sid: str,
    caller_phone: str,
    recording_url: str | None,
    recording_duration: int,
) -> str:
    _cleanup()
    session = _get_or_create(call_sid, caller_phone)

    if not recording_url or recording_duration < 1:
        session.empty_turns += 1
        if session.empty_turns >= 3:
            asyncio.create_task(_save_lead(session))
            return _wrap(_say("לא שמעתי תגובה. יום טוב!") + "<Hangup/>")
        return _speak_and_listen("לא שמעתי אותך. תוכל לדבר שוב?")

    session.empty_turns = 0
    speech = await _transcribe(recording_url)
    if not speech:
        return _speak_and_listen("לא הצלחתי להבין. תוכל לנסות שוב?")

    logger.info("[AIVoiceBot] call=%s user: %r", call_sid[:8], speech)
    session.messages.append({"role": "user", "content": speech})

    # Collect name from conversation
    if not session.collected_name:
        name_match = re.search(r"(?:שמי|קוראים לי|אני)\s+([א-ת]{2,15})", speech)
        if name_match:
            session.collected_name = name_match.group(1)

    # Farewell detection
    lower = speech.lower()
    if any(w in lower for w in _FAREWELL_WORDS) and len(speech) < 30:
        bye = "תודה שפנית לטאזו! יום נעים ומוצלח. להתראות!"
        session.messages.append({"role": "assistant", "content": bye})
        asyncio.create_task(_save_lead(session))
        return _wrap(_say(bye) + "<Hangup/>")

    # User explicitly asks for a link
    if _wants_link(speech) and not session.link_sent:
        session.link_sent = True
        asyncio.create_task(_send_link(caller_phone))
        reply = "שלחתי לך הודעה עם הקישור ישירות לטלפון שלך. האם יש עוד משהו שאוכל לעזור?"
        session.messages.append({"role": "assistant", "content": reply})
        return _speak_and_listen(reply)

    # GPT reply
    reply = await _gpt_reply(session)
    session.messages.append({"role": "assistant", "content": reply})
    logger.info("[AIVoiceBot] call=%s bot: %r", call_sid[:8], reply)

    # GPT decided to send a link
    if "[SEND_LINK]" in reply and not session.link_sent:
        session.link_sent = True
        asyncio.create_task(_send_link(caller_phone))
        reply = reply.replace("[SEND_LINK]", "").strip()
        if not reply:
            reply = "שלחתי לך קישור לטלפון! האם יש עוד שאלה?"

    # GPT decided to end the call
    if any(w in reply for w in ("להתראות", "יום נעים", "יום טוב", "שיהיה לך")):
        asyncio.create_task(_save_lead(session))
        return _wrap(_say(reply) + "<Hangup/>")

    return _speak_and_listen(reply)
