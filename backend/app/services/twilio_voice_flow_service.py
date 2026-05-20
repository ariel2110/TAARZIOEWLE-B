"""
TAZO Voice Bot — Hebrew business-onboarding conversation over Twilio voice calls.

Flow:
  greeting  → ask_interest → ask_name → ask_type → confirm → done
                           ↘ bye (if not interested / timeout)

State is held in-process (module dict) keyed by CallSid.
Calls are short-lived so no Redis is needed.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── session store ─────────────────────────────────────────────────────────────
@dataclass
class CallSession:
    call_sid: str
    caller_phone: str
    state: str = "greeting"
    business_name: str = ""
    business_type: str = ""
    created_at: float = field(default_factory=time.time)


_sessions: dict[str, CallSession] = {}
_lock = threading.Lock()

_BUSINESS_TYPES = {
    "1": "אוכל ומסעדות 🍽️",
    "2": "חנויות וקמעונאות 🛍️",
    "3": "שירותים מקצועיים 💼",
    "4": "תחום אחר 🏢",
}

# ── TwiML helpers ─────────────────────────────────────────────────────────────

def _webhook_url(state: str) -> str:
    base = settings.api_base_url.rstrip("/")
    return f"{base}/api/v1/webhooks/twilio/voice?s={state}"


def _say(text: str, loop: int = 1) -> str:
    safe = escape(text)
    return f'<Say language="he-IL" loop="{loop}">{safe}</Say>'


def _gather_speech(action_state: str, prompt: str, timeout: int = 6) -> str:
    url = escape(_webhook_url(action_state))
    return (
        f'<Gather input="speech dtmf" numDigits="1" '
        f'timeout="{timeout}" speechTimeout="3" action="{url}">'
        f'{_say(prompt)}'
        f'</Gather>'
        f'<Redirect>{escape(_webhook_url("timeout"))}</Redirect>'
    )


def _gather_dtmf(action_state: str, prompt: str, num_digits: int = 1, timeout: int = 10) -> str:
    url = escape(_webhook_url(action_state))
    return (
        f'<Gather input="dtmf" numDigits="{num_digits}" timeout="{timeout}" action="{url}">'
        f'{_say(prompt)}'
        f'</Gather>'
        f'<Redirect>{escape(_webhook_url("timeout"))}</Redirect>'
    )


def _twiml(body: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>'


# ── main service ──────────────────────────────────────────────────────────────

class TwilioVoiceFlowService:

    # ── session management ────────────────────────────────────────────────────

    def _get_or_create(self, call_sid: str, caller_phone: str) -> CallSession:
        with _lock:
            if call_sid not in _sessions:
                _sessions[call_sid] = CallSession(
                    call_sid=call_sid, caller_phone=caller_phone
                )
                # clean sessions older than 30 min
                cutoff = time.time() - 1800
                stale = [k for k, v in _sessions.items() if v.created_at < cutoff]
                for k in stale:
                    del _sessions[k]
            return _sessions[call_sid]

    def _update(self, call_sid: str, **kwargs) -> None:
        with _lock:
            if call_sid in _sessions:
                for k, v in kwargs.items():
                    setattr(_sessions[call_sid], k, v)

    # ── public entry point ────────────────────────────────────────────────────

    def handle(
        self,
        *,
        call_sid: str,
        caller_phone: str,
        state: str,
        speech_result: str | None = None,
        digits: str | None = None,
    ) -> str:
        """Return a TwiML string for the current state."""
        session = self._get_or_create(call_sid, caller_phone)

        logger.info(
            "[VoiceFlow] call=%s state=%s speech=%r digits=%r",
            call_sid[:8], state, speech_result, digits,
        )

        # ── state machine ─────────────────────────────────────────────────────
        if state == "greeting":
            return self._greeting()

        if state == "ask_interest":
            return self._ask_interest(session, speech_result, digits)

        if state == "ask_name":
            return self._ask_name()

        if state == "got_name":
            return self._got_name(session, speech_result)

        if state == "ask_type":
            return self._ask_type()

        if state == "got_type":
            return self._got_type(session, digits)

        if state == "timeout":
            return self._timeout(session)

        if state == "bye":
            return self._bye()

        # fallback
        return self._greeting()

    # ── states ────────────────────────────────────────────────────────────────

    def _greeting(self) -> str:
        prompt = (
            "שלום! כאן TAZO — הפלטפורמה שבונה אתרים מקצועיים לעסקים ישראלים, "
            "תוך עשרים וארבע שעות בלבד. "
            "אנחנו מציעים לך חודש ראשון חינם לגמרי, ללא התחייבות. "
            "האם תרצה לשמוע עוד? אמור כן, או לחץ 1. "
            "לסיום לחץ 2."
        )
        return _twiml(_gather_speech("ask_interest", prompt, timeout=7))

    def _ask_interest(
        self, session: CallSession, speech: str | None, digits: str | None
    ) -> str:
        interested = False
        if digits == "1":
            interested = True
        elif digits == "2":
            interested = False
        elif speech:
            speech_lower = speech.lower()
            interested = any(
                w in speech_lower
                for w in ["כן", "yes", "בטח", "אוקיי", "בסדר", "רוצה", "מעוניין", "ok"]
            )

        if interested:
            return _twiml(_gather_speech(
                "got_name",
                "מצוין! שמחים לשמוע. ספר לי — מה שם העסק שלך? אמור את שם העסק בבקשה.",
                timeout=8,
            ))
        else:
            return _twiml(
                _say(
                    "מובן לגמרי. אם תחשוב עלינו בעתיד, "
                    "אנחנו תמיד כאן בכתובת tazo-web.com. "
                    "שיהיה לך יום נהדר!"
                )
                + "<Hangup/>"
            )

    def _ask_name(self) -> str:
        return _twiml(_gather_speech(
            "got_name",
            "ספר לי — מה שם העסק שלך?",
            timeout=8,
        ))

    def _got_name(self, session: CallSession, speech: str | None) -> str:
        name = (speech or "").strip()
        if not name or len(name) < 2:
            # re-ask
            return _twiml(_gather_speech(
                "got_name",
                "לא שמעתי היטב. אמור שוב בבקשה — מה שם העסק שלך?",
                timeout=8,
            ))
        self._update(session.call_sid, business_name=name, state="ask_type")
        return _twiml(_gather_dtmf(
            "got_type",
            f"תודה! {escape(name)}. "
            "עכשיו בחר את סוג העסק שלך. "
            "לחץ 1 לאוכל ומסעדות. "
            "לחץ 2 לחנויות וקמעונאות. "
            "לחץ 3 לשירותים מקצועיים. "
            "לחץ 4 לאחר.",
            timeout=12,
        ))

    def _ask_type(self) -> str:
        return _twiml(_gather_dtmf(
            "got_type",
            "בחר את סוג העסק שלך. "
            "1 לאוכל ומסעדות, 2 לחנויות, 3 לשירותים, 4 לאחר.",
        ))

    def _got_type(self, session: CallSession, digits: str | None) -> str:
        btype = _BUSINESS_TYPES.get(digits or "", "עסק כללי 🏢")
        self._update(session.call_sid, business_type=btype, state="confirm")

        # fire-and-forget WhatsApp
        self._send_whatsapp(session.caller_phone, session.business_name, btype)

        name = escape(session.business_name or "העסק שלך")
        return _twiml(
            _say(
                f"מעולה! {name}, {btype}. "
                "שלחתי לך עכשיו הודעה בוואטסאפ עם כל הפרטים. "
                "נציג מטעם TAZO יצור איתך קשר תוך שעה אחת. "
                "תודה רבה על הזמן, ושיהיה לך יום מדהים!"
            )
            + "<Hangup/>"
        )

    def _timeout(self, session: CallSession) -> str:
        if session.state in ("greeting",):
            # re-try greeting once
            self._update(session.call_sid, state="bye")
            return _twiml(_gather_speech(
                "ask_interest",
                "לא שמעתי תשובה. האם תרצה לשמוע על בניית אתר לעסק שלך? אמור כן או לחץ 1.",
                timeout=6,
            ))
        return self._bye()

    def _bye(self) -> str:
        return _twiml(
            _say("תודה על השיחה. ניתן למצוא אותנו תמיד בכתובת tazo-web.com. שיהיה לך יום טוב!")
            + "<Hangup/>"
        )

    # ── side effects ──────────────────────────────────────────────────────────

    def _send_whatsapp(self, phone: str, business_name: str, business_type: str) -> None:
        """Send a WhatsApp follow-up to the caller (best-effort, non-blocking)."""
        import threading
        threading.Thread(
            target=self._do_send_whatsapp,
            args=(phone, business_name, business_type),
            daemon=True,
        ).start()

    def _do_send_whatsapp(
        self, phone: str, business_name: str, business_type: str
    ) -> None:
        try:
            from app.services.communications.meta_whatsapp_service import (
                MetaWhatsAppService,
            )
            svc = MetaWhatsAppService()
            name = business_name or "העסק שלך"
            btype = business_type or "עסק כללי"
            msg = (
                f"✨ *ברוכים הבאים ל-TAZO!*\n\n"
                f"תודה על שיחתנו 🙏\n\n"
                f"🏢 *שם העסק:* {name}\n"
                f"📂 *סוג עסק:* {btype}\n\n"
                f"נציג שלנו יצור איתך קשר תוך שעה אחת.\n\n"
                f"🌐 *בנה את האתר שלך עכשיו:*\n"
                f"https://tazo-web.com\n\n"
                f"_מערכת TAZO — אתרים מקצועיים ב-24 שעות_"
            )
            ok = svc.send_text(phone, msg)
            logger.info("[VoiceFlow] WhatsApp to %s → %s", phone, "sent" if ok else "failed")
        except Exception as exc:  # noqa: BLE001
            logger.error("[VoiceFlow] WhatsApp error: %s", exc)


voice_flow_service = TwilioVoiceFlowService()
