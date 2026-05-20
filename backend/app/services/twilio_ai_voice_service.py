"""TAZO AI Voice Bot — Whisper STT + GPT-4o-mini + Google TTS (Hebrew).

Flow:
  1. Bot speaks <Say language="he-IL"> then opens mic with <Record>
  2. Twilio POSTs RecordingUrl to /ai-voice-record
  3. We download the MP3 and send to OpenAI Whisper (language=he)
  4. Hebrew transcript -> GPT-4o-mini -> Hebrew reply
  5. Return TwiML: <Say> reply + <Record> for the next turn
"""
from __future__ import annotations

import asyncio
import io
import logging
import threading
import time
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

import httpx
from openai import AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

_SYSTEM = (
    "אתה נציג שירות לקוחות של חברת TAZO"
    " — פלטפורמה המסייעת לעסקים מקומיים לנהל את הנוכחות הדיגיטלית שלהם.\n"
    "שמך הוא טאזו.\n\n"
    "כללים חשובים:\n"
    "1. ענה אך ורק בעברית תקינה.\n"
    "2. תשובות קצרות ותמציתיות — עד 2 משפטים בלבד (שיחת טלפון!).\n"
    "3. היה ידידותי, חם ומקצועי.\n"
    "4. אם הלקוח אומר להתראות / ביי / תודה / לא מעניין / לא רוצה — \n"
    "   סיים בנימוס עם 'תודה שפנית, יום נעים. להתראות!' ואל תוסיף שאלות.\n"
    "5. TAZO מאפשרת לעסקים: קבלת הזמנות דרך WhatsApp, דף עסקי מקצועי, \n"
    "   ניהול לקוחות ונאמנות, שיווק אוטומטי וסטטיסטיקות.\n"
    "6. אם הלקוח מתעניין — שאל שם ומספר טלפון לחזרה.\n"
    "7. אל תחשוף מידע פנימי: מחירים ספציפיים, API, קוד, שמות לקוחות, \n"
    "   פרטי שרת או כל מידע טכני. אם שואלים — אמור שהצוות יחזור עם פרטים.\n"
    "8. אל תדון בנושאים שאינם קשורים לשירות (פוליטיקה, בריאות, כספים אישיים וכו\').\n"
    "9. אם אינך יודע תשובה — אמור שהצוות יחזור ללקוח בהקדם.\n"
)

_FAREWELL_WORDS = ("להתראות", "ביי", "bye", "תודה ביי")


@dataclass
class _Session:
    call_sid: str
    caller_phone: str
    messages: list = field(default_factory=list)
    empty_turns: int = 0
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


def _record_url() -> str:
    return settings.api_base_url.rstrip("/") + "/api/v1/webhooks/twilio/ai-voice-record"


def _say(text: str) -> str:
    return f'<Say language="he-IL">{escape(text)}</Say>'


def _record(timeout: int = 3) -> str:
    url = escape(_record_url())
    return (
        f'<Record action="{url}" method="POST" '
        f'maxLength="30" timeout="{timeout}" '
        f'playBeep="false" trim="trim-silence"/>' +
        f'<Redirect method="POST">{url}</Redirect>'
    )


def _wrap(body: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>'


def _speak_and_listen(text: str) -> str:
    return _wrap(_say(text) + _record())


async def _transcribe(recording_url: str) -> str:
    """Download Twilio recording MP3 and send to Whisper for Hebrew STT."""
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


async def _gpt_reply(session: _Session) -> str:
    try:
        oai = AsyncOpenAI(api_key=settings.openai_api_key)
        result = await oai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": _SYSTEM}] + session.messages[-20:],
            max_tokens=130,
            temperature=0.7,
        )
        return result.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("[AIVoiceBot] GPT error: %s", exc)
        return "סליחה, יש תקלה טכנית רגעית."


def greeting_twiml(call_sid: str, caller_phone: str) -> str:
    session = _get_or_create(call_sid, caller_phone)
    opening = "שלום! הגעת לשירות הלקוחות של TAZO. אני טאזו, כאן כדי לעזור. כיצד אוכל לסייע לך היום?"
    # Store greeting in history so GPT has context on subsequent turns
    if not session.messages:
        session.messages.append({"role": "assistant", "content": opening})
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
            return _wrap(_say("לא שמעתי תגובה. יום טוב!") + "<Hangup/>")
        return _speak_and_listen("לא שמעתי אותך. תוכל לדבר שוב?")

    session.empty_turns = 0

    speech = await _transcribe(recording_url)
    if not speech:
        return _speak_and_listen("לא הצלחתי להבין. תוכל לנסות שוב?")

    logger.info("[AIVoiceBot] call=%s user: %r", call_sid[:8], speech)
    session.messages.append({"role": "user", "content": speech})

    lower = speech.lower()
    if any(w in lower for w in _FAREWELL_WORDS) and len(speech) < 25:
        bye = "תודה שפנית לטאזו! יום נעים ומוצלח. להתראות!"
        session.messages.append({"role": "assistant", "content": bye})
        return _wrap(_say(bye) + "<Hangup/>")

    reply = await _gpt_reply(session)
    session.messages.append({"role": "assistant", "content": reply})
    logger.info("[AIVoiceBot] call=%s bot: %r", call_sid[:8], reply)

    if any(w in reply for w in ("להתראות", "יום נעים", "יום טוב", "שיהיה לך")):
        return _wrap(_say(reply) + "<Hangup/>")

    return _speak_and_listen(reply)
