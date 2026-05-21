"""
Twilio voice-call webhook — receives callbacks from Twilio and returns TwiML.

Endpoint: POST /webhooks/twilio/voice
Query param `s` carries the flow state (e.g. ?s=greeting, ?s=ask_interest …).

Security: Twilio signs every request with X-Twilio-Signature.
Validation is enabled when TWILIO_AUTH_TOKEN is set.
"""
from __future__ import annotations

import hashlib
import hmac
import base64
import logging
from urllib.parse import urlencode, parse_qsl

from xml.sax.saxutils import escape as _xml_escape

from fastapi import APIRouter, Form, Header, HTTPException, Query, Request
from fastapi.responses import Response

from app.core.config import settings
from app.services.twilio_voice_flow_service import voice_flow_service
from app.services import twilio_ai_voice_service as ai_bot

_DTMF_TO_LANG = {"1": "he", "2": "en", "3": "ar", "4": "ru"}


def _stream_twiml(ws_url: str, lang: str, from_phone: str, ctx) -> str:
    """Build <Connect><Stream> TwiML with caller context + selected language."""
    params = (
        f'<Parameter name="caller_phone"   value="{_xml_escape(from_phone)}"/>'
        f'<Parameter name="caller_name"    value="{_xml_escape(ctx.contact_name or "")}"/>'
        f'<Parameter name="is_customer"    value="{str(ctx.is_customer).lower()}"/>'
        f'<Parameter name="business_name"  value="{_xml_escape(ctx.business_name or "")}"/>'
        f'<Parameter name="lang"           value="{_xml_escape(lang)}"/>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        '<Connect>'
        f'<Stream url="{_xml_escape(ws_url)}">'
        f'{params}'
        '</Stream>'
        '</Connect>'
        '</Response>'
    )

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/twilio", tags=["webhooks-twilio"])

# Hebrew digit words
_HE_DIGITS = {
    '0': 'אפס', '1': 'אחת', '2': 'שתיים', '3': 'שלוש', '4': 'ארבע',
    '5': 'חמש',  '6': 'שש',  '7': 'שבע',   '8': 'שמונה', '9': 'תשע',
}


_HE_DIGITS = {
    '0': 'אפס', '1': 'אחת', '2': 'שתיים', '3': 'שלוש', '4': 'ארבע',
    '5': 'חמש',  '6': 'שש',  '7': 'שבע',   '8': 'שמונה', '9': 'תשע',
}


@router.get("/otp-twiml")
async def otp_twiml(code: str = Query(default=""), ext: str = Query(default="")):
    """Serve OTP TwiML with Google Hebrew TTS.

    If `ext` is provided (e.g. ext=2), a 4-second pause is inserted before the
    Say verb so that IVR extension routing (triggered via Twilio SendDigits) has
    time to complete before the OTP is spoken.
    """
    digits = ''.join(c for c in code if c.isdigit())
    if not digits:
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response><Hangup/></Response>'
        return Response(content=twiml, media_type="application/xml; charset=utf-8")

    spoken = ', '.join(_HE_DIGITS.get(d, d) for d in digits)
    text = f'שלום, קוד האימות שלך הוא: {spoken}. חוזר: {spoken}. להתראות.'

    # When an extension is being dialled (SendDigits), allow extra time for routing
    pause_xml = '<Pause length="4"/>' if ext.strip() else ''

    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        f'{pause_xml}'
        f'<Say language="he-IL">{text}</Say>'
        '</Response>'
    )
    return Response(content=twiml, media_type="application/xml; charset=utf-8")


# ── Twilio signature validation ───────────────────────────────────────────────

def _verify_twilio_signature(
    request_url: str,
    post_params: dict,
    signature: str,
    auth_token: str,
) -> bool:
    """
    Validate X-Twilio-Signature per Twilio docs:
    https://www.twilio.com/docs/usage/security#validating-signatures-from-twilio
    """
    # Build sorted param string appended to URL
    if post_params:
        sorted_params = "".join(
            f"{k}{v}" for k, v in sorted(post_params.items())
        )
        s = request_url + sorted_params
    else:
        s = request_url

    mac = hmac.new(auth_token.encode(), s.encode(), hashlib.sha1)
    expected = base64.b64encode(mac.digest()).decode()
    return hmac.compare_digest(expected, signature)


# ── main webhook handler ──────────────────────────────────────────────────────

@router.post("/voice")
async def twilio_voice_webhook(
    request: Request,
    s: str = Query(default="greeting"),
    x_twilio_signature: str | None = Header(default=None),
    # Twilio form fields
    CallSid: str = Form(default=""),
    From: str = Form(default=""),
    SpeechResult: str | None = Form(default=None),
    Digits: str | None = Form(default=None),
    CallStatus: str | None = Form(default=None),
):
    # ── optional signature check ──────────────────────────────────────────────
    if settings.twilio_auth_token and x_twilio_signature:
        form_data = dict(await request.form())
        str_params = {k: str(v) for k, v in form_data.items()}
        # Reconstruct the public-facing URL (behind reverse proxy the internal
        # URL differs from what Twilio signed, so use api_base_url)
        query = str(request.url.query)
        path = str(request.url.path)
        full_url = settings.api_base_url.rstrip("/") + path
        if query:
            full_url += "?" + query
        if not _verify_twilio_signature(
            full_url, str_params, x_twilio_signature, settings.twilio_auth_token
        ):
            logger.warning("[TwilioWebhook] Invalid signature from %s", request.client)
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    if not CallSid:
        raise HTTPException(status_code=400, detail="Missing CallSid")

    logger.info(
        "[TwilioWebhook] call=%s state=%s from=%s speech=%r digits=%r status=%s",
        CallSid[:8], s, From, SpeechResult, Digits, CallStatus,
    )

    twiml = voice_flow_service.handle(
        call_sid=CallSid,
        caller_phone=From,
        state=s,
        speech_result=SpeechResult,
        digits=Digits,
    )

    return Response(content=twiml, media_type="application/xml")


# ── outbound call initiator (admin helper) ────────────────────────────────────

@router.post("/call")
async def initiate_voice_call(
    to: str = Form(...),
    x_internal_key: str | None = Header(default=None),
):
    """Kick off a TAZO onboarding call to the given phone number."""
    # Simple key check — full admin auth handled by Traefik in production
    if settings.internal_key and x_internal_key != settings.internal_key:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not settings.twilio_account_sid or not settings.twilio_from_number:
        raise HTTPException(status_code=503, detail="Twilio not configured")

    import httpx
    from xml.sax.saxutils import escape as xml_escape

    webhook_url = f"{settings.api_base_url}/api/v1/webhooks/twilio/voice?s=greeting"
    auth = (
        (settings.twilio_api_key_sid, settings.twilio_api_key_secret)
        if settings.twilio_api_key_sid
        else (settings.twilio_account_sid, settings.twilio_auth_token)
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.twilio.com/2010-04-01/Accounts/"
            f"{settings.twilio_account_sid}/Calls.json",
            auth=auth,
            data={
                "To": to,
                "From": settings.twilio_from_number,
                "Url": webhook_url,
                "Method": "POST",
                "Timeout": "30",
            },
            timeout=15,
        )

    if not resp.is_success:
        logger.error("[TwilioWebhook] Call failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail=resp.text[:300])

    data = resp.json()
    return {"ok": True, "call_sid": data.get("sid"), "status": data.get("status")}


# ── AI Voice Bot (Whisper STT) ───────────────────────────────────────────────

@router.post("/ai-voice")
async def ai_voice_webhook(
    request: Request,
    CallSid: str = Form(default=""),
    From: str = Form(default=""),
    CallStatus: str | None = Form(default=None),
    Direction: str | None = Form(default=None),
):
    """
    Entry point — inbound calls and outbound call connect.

    Mode A (ElevenLabs streaming — VOICE_STREAM_URL is set):
      Returns <Connect><Stream> TwiML so Twilio opens a WebSocket to the
      voice-stream microservice. Caller context is passed as <Parameter> tags.

    Mode B (fallback — Whisper + <Record> loop):
      Returns <Say> greeting + <Record> TwiML (original approach).
    """
    if not CallSid:
        raise HTTPException(status_code=400, detail="Missing CallSid")

    # Ignore terminal status callbacks — Twilio sends these after the call ends
    if CallStatus in ("completed", "busy", "failed", "no-answer", "canceled"):
        logger.info("[AIVoice] call=%s status=%s — ignoring terminal callback", CallSid[:8], CallStatus)
        return Response(content="<Response/>", media_type="application/xml")

    logger.info(
        "[AIVoice] call=%s from=%s status=%s dir=%s",
        CallSid[:8], From, CallStatus, Direction,
    )

    # ── Mode A: ElevenLabs real-time streaming ────────────────────────────────
    stream_url = getattr(settings, "voice_stream_url", None)
    if stream_url:
        # Look up caller context from DB (reuse existing function)
        ctx = await ai_bot._lookup_caller(From)

        ws_url = stream_url.rstrip("/") + "/ws"
        action_url = settings.api_base_url.rstrip("/") + "/api/v1/webhooks/twilio/ai-voice-lang"

        # Build fallback stream (timeout = no digit pressed → default to Hebrew)
        fallback_params = (
            f'<Parameter name="caller_phone"   value="{_xml_escape(From)}"/>'
            f'<Parameter name="caller_name"    value="{_xml_escape(ctx.contact_name or "")}"/>'
            f'<Parameter name="is_customer"    value="{str(ctx.is_customer).lower()}"/>'
            f'<Parameter name="business_name"  value="{_xml_escape(ctx.business_name or "")}"/>'
            f'<Parameter name="lang"           value="he"/>'
        )

        # Play multilingual menu via Twilio <Say> (supports Hebrew natively),
        # gather a single DTMF digit, then redirect to /ai-voice-lang.
        # Fallback: if no digit pressed within 10 s → connect stream in Hebrew.
        twiml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Response>'
            f'<Gather action="{_xml_escape(action_url)}" method="POST" numDigits="1" timeout="10">'
            '<Say language="he-IL">ברוכים הבאים לטאזו! לעברית לחצו 1.</Say>'
            '<Say language="en-US">For English press 2.</Say>'
            '<Say voice="Polly.Zeina">للعربية اضغط 3.</Say>'
            '<Say language="ru-RU">На русском нажмите 4.</Say>'
            '</Gather>'
            '<Connect>'
            f'<Stream url="{_xml_escape(ws_url)}">'
            f'{fallback_params}'
            '</Stream>'
            '</Connect>'
            '</Response>'
        )
        logger.info("[AIVoice] call=%s → menu+streaming mode (ws=%s)", CallSid[:8], ws_url)
        return Response(content=twiml, media_type="application/xml")

    # ── Mode B: Record + Whisper fallback ────────────────────────────────────
    twiml = await ai_bot.greeting_twiml(CallSid, From)
    return Response(content=twiml, media_type="application/xml")


@router.post("/ai-voice-lang")
async def ai_voice_lang_select(
    CallSid: str = Form(default=""),
    From: str = Form(default=""),
    Digits: str = Form(default=""),
):
    """
    Called by Twilio <Gather> action after the user presses a language digit.
    Returns <Connect><Stream> TwiML with the chosen language as a parameter.
    """
    lang = _DTMF_TO_LANG.get(Digits, "he")

    stream_url = getattr(settings, "voice_stream_url", None)
    if not stream_url:
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><Hangup/></Response>',
            media_type="application/xml",
        )

    ctx = await ai_bot._lookup_caller(From)
    ws_url = stream_url.rstrip("/") + "/ws"

    logger.info("[AIVoice] call=%s digit=%s → lang=%s → stream", CallSid[:8], Digits, lang)
    return Response(
        content=_stream_twiml(ws_url, lang, From, ctx),
        media_type="application/xml",
    )


@router.post("/ai-voice-record")
async def ai_voice_record(
    request: Request,
    x_twilio_signature: str | None = Header(default=None),
    CallSid: str = Form(default=""),
    From: str = Form(default=""),
    RecordingUrl: str | None = Form(default=None),
    RecordingDuration: int = Form(default=0),
    CallStatus: str | None = Form(default=None),
):
    """Called by Twilio when a <Record> finishes. Downloads audio, Whisper STT, GPT reply."""
    if settings.twilio_auth_token and x_twilio_signature:
        form_data = dict(await request.form())
        str_params = {k: str(v) for k, v in form_data.items()}
        query = str(request.url.query)
        path = str(request.url.path)
        full_url = settings.api_base_url.rstrip("/") + path
        if query:
            full_url += "?" + query
        if not _verify_twilio_signature(
            full_url, str_params, x_twilio_signature, settings.twilio_auth_token
        ):
            logger.warning("[AIVoiceBot] Invalid signature from %s", request.client)
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    if not CallSid:
        raise HTTPException(status_code=400, detail="Missing CallSid")

    logger.info(
        "[AIVoiceBot] record: call=%s from=%s url=%s dur=%s status=%s",
        CallSid[:8], From, RecordingUrl, RecordingDuration, CallStatus,
    )

    twiml = await ai_bot.respond_from_recording(
        CallSid, From, RecordingUrl, RecordingDuration
    )
    return Response(content=twiml, media_type="application/xml")


@router.post("/ai-call")
async def initiate_ai_call(
    to: str = Form(...),
    x_internal_key: str | None = Header(default=None),
):
    """Kick off an AI-powered outbound call to the given phone number."""
    if settings.internal_key and x_internal_key != settings.internal_key:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not settings.twilio_account_sid or not settings.twilio_from_number:
        raise HTTPException(status_code=503, detail="Twilio not configured")

    import httpx

    webhook_url = (
        settings.api_base_url.rstrip("/") + "/api/v1/webhooks/twilio/ai-voice"
    )
    auth = (
        (settings.twilio_api_key_sid, settings.twilio_api_key_secret)
        if settings.twilio_api_key_sid
        else (settings.twilio_account_sid, settings.twilio_auth_token)
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.twilio.com/2010-04-01/Accounts/"
            f"{settings.twilio_account_sid}/Calls.json",
            auth=auth,
            data={
                "To": to,
                "From": settings.twilio_from_number,
                "Url": webhook_url,
                "Method": "POST",
                "Timeout": "30",
                "StatusCallback": webhook_url,
            },
            timeout=15,
        )

    if not resp.is_success:
        logger.error("[AIVoiceBot] Call initiation failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail=resp.text[:300])

    data = resp.json()
    logger.info("[AIVoiceBot] Outbound call started: %s → %s", data.get("sid"), to)
    return {"ok": True, "call_sid": data.get("sid"), "status": data.get("status")}
