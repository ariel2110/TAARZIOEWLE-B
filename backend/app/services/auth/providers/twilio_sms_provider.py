"""Twilio SMS OTP delivery provider.

Sends a 4-digit OTP via SMS from +972533889859.
The SMS body follows the Web OTP API format so Android/Chrome auto-fills the code.

Web OTP format (last two lines MUST be exact):
  Your TAZO code is: 1234

  @tazo-web.com #1234

Requirements:
  - SMS body must end with a line in the format: @<domain> #<otp>
  - The domain must match the page where the OTP input is displayed
  - Android Chrome & Samsung Internet auto-fill via navigator.credentials.get()
"""
from __future__ import annotations

import logging

import httpx

from .base import DeliveryProviderResult

logger = logging.getLogger(__name__)

# Domains where OTP input can appear — all must be listed for Web OTP
_OTP_DOMAINS = ["tazo-web.com", "tazo-sync.com", "tazo-go.com"]


def _sms_body(code: str, lang: str = "he") -> str:
    """Build SMS body with Web OTP API auto-fill format."""
    if lang == "he":
        body = f"קוד האימות שלך ב-TAZO: {code}\nהקוד תקף ל-10 דקות."
    elif lang == "ar":
        body = f"رمز التحقق الخاص بك في TAZO: {code}\nصالح لمدة 10 دقائق."
    else:
        body = f"Your TAZO verification code: {code}\nValid for 10 minutes."

    # Web OTP API auto-fill line — must be the last line, format: @domain #code
    body += f"\n\n@tazo-web.com #{code}"
    return body


class TwilioSmsDeliveryProvider:
    """Send OTP via Twilio SMS from the registered AI support number."""

    def deliver(self, *, to_phone: str, code: str, lang: str = "he") -> DeliveryProviderResult:
        from app.core.config import settings

        account_sid = settings.twilio_account_sid
        auth_token  = settings.twilio_auth_token
        api_key_sid = settings.twilio_api_key_sid
        api_key_sec = settings.twilio_api_key_secret
        from_number = settings.twilio_from_number or "+972533889859"

        if not account_sid:
            logger.warning("[SMS-OTP] Twilio credentials not configured")
            return DeliveryProviderResult(ok=False, provider="twilio_sms",
                                          delivery_channel="sms", error="not_configured")

        # Normalise phone
        import re
        clean = re.sub(r"\D", "", to_phone)
        if clean.startswith("0") and len(clean) == 10:
            clean = "972" + clean[1:]
        to_e164 = f"+{clean}"

        body = _sms_body(code, lang)

        # Auth: prefer API Key over Account Auth Token
        auth = (api_key_sid, api_key_sec) if (api_key_sid and api_key_sec) else (account_sid, auth_token)

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        try:
            resp = httpx.post(url, data={"From": from_number, "To": to_e164, "Body": body},
                              auth=auth, timeout=15)
            data = resp.json()
            if resp.status_code in (200, 201):
                sid = data.get("sid", "")
                logger.info("[SMS-OTP] sent to %s*** sid=%s", clean[:7], sid[:8])
                return DeliveryProviderResult(ok=True, provider="twilio_sms",
                                              delivery_channel="sms", external_reference=sid)
            logger.warning("[SMS-OTP] Twilio error %s: %s", resp.status_code, data.get("message"))
            return DeliveryProviderResult(ok=False, provider="twilio_sms",
                                          delivery_channel="sms", error=data.get("message", "twilio_error"))
        except Exception as exc:
            logger.error("[SMS-OTP] request failed: %s", exc)
            return DeliveryProviderResult(ok=False, provider="twilio_sms",
                                          delivery_channel="sms", error=str(exc))
