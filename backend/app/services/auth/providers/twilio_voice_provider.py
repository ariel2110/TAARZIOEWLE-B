"""
Twilio Voice OTP delivery provider.

Makes a phone call to the business/customer and speaks the OTP code
digit-by-digit in Hebrew using Amazon Polly (he-IL) via Twilio.

Uses Twilio REST API directly (no SDK) via httpx — already a project dependency.
Auth: API Key SID + Secret (preferred) or Account SID + Auth Token.
"""
from __future__ import annotations

import logging
from xml.sax.saxutils import escape

import httpx

from .base import DeliveryProviderResult

logger = logging.getLogger(__name__)

# Hebrew digit words for clear TTS pronunciation
_HE_DIGITS = {
    '0': 'אפס', '1': 'אחת', '2': 'שתיים', '3': 'שלוש', '4': 'ארבע',
    '5': 'חמש',  '6': 'שש',  '7': 'שבע',   '8': 'שמונה', '9': 'תשע',
}


def _build_twiml(code: str) -> str:
    """Build TwiML that speaks each digit in Hebrew, repeated twice."""
    spoken = ', '.join(_HE_DIGITS.get(d, d) for d in code)
    text = (
        f'שלום, קוד האימות שלך הוא: {escape(spoken)}. '
        f'חוזר: {escape(spoken)}. '
        f'להתראות.'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        f'<Say language="he-IL">{text}</Say>'
        '</Response>'
    )


class TwilioVoiceDeliveryProvider:
    provider_name = 'twilio_voice'
    delivery_channel = 'voice_call'

    def send(
        self,
        *,
        challenge_type: str,
        customer_phone: str,
        payload_preview: str,
    ) -> DeliveryProviderResult:
        from app.core.config import settings

        account_sid = settings.twilio_account_sid
        if not account_sid:
            return DeliveryProviderResult(
                provider=self.provider_name,
                delivery_channel=self.delivery_channel,
                status='error',
                detail='TWILIO_ACCOUNT_SID not configured',
            )

        # Prefer API Key auth over Auth Token
        if settings.twilio_api_key_sid and settings.twilio_api_key_secret:
            auth = (settings.twilio_api_key_sid, settings.twilio_api_key_secret)
        elif settings.twilio_auth_token:
            auth = (account_sid, settings.twilio_auth_token)
        else:
            return DeliveryProviderResult(
                provider=self.provider_name,
                delivery_channel=self.delivery_channel,
                status='error',
                detail='No Twilio auth credentials configured',
            )

        from_number = settings.twilio_from_number
        if not from_number:
            return DeliveryProviderResult(
                provider=self.provider_name,
                delivery_channel=self.delivery_channel,
                status='error',
                detail='TWILIO_FROM_NUMBER not configured — purchase a number first',
            )

        # payload_preview may be "OTP:1234;ext=2", "OTP:1234", or "1234"
        # Parse optional extension before extracting digits
        ext_digits = ""
        pp = payload_preview
        if ';ext=' in pp:
            pp, ext_part = pp.split(';ext=', 1)
            ext_raw = ext_part.strip()
            # Normalise: "002" → "2", keep multi-digit extensions
            try:
                ext_digits = str(int(ext_raw))
            except ValueError:
                ext_digits = ''.join(c for c in ext_raw if c.isdigit())

        code = ''.join(c for c in pp if c.isdigit())
        if not code:
            logger.error('[TwilioVoice] No digits found in payload_preview=%r', payload_preview)
            return DeliveryProviderResult(
                provider=self.provider_name,
                delivery_channel=self.delivery_channel,
                status='error',
                detail='No digits in payload_preview',
            )
        # Build URL to our TwiML endpoint — avoids encoding issues with inline Twiml
        from urllib.parse import urlencode
        qs_params: dict[str, str] = {'code': code}
        if ext_digits:
            qs_params['ext'] = ext_digits
        twiml_url = (
            settings.api_base_url.rstrip('/') +
            '/api/v1/webhooks/twilio/otp-twiml?' +
            urlencode(qs_params)
        )

        try:
            call_data: dict = {
                'To': customer_phone,
                'From': from_number,
                'Url': twiml_url,
                'Method': 'GET',
                'Timeout': '30',
            }
            if ext_digits:
                # Navigate IVR to extension: 4 s pause (8 × 0.5 s 'w') then dial digit(s)
                call_data['SendDigits'] = 'wwwwwwww' + ext_digits
                logger.info('[TwilioVoice] Extension routing: sendDigits=%r', call_data['SendDigits'])

            resp = httpx.post(
                f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Calls.json',
                auth=auth,
                data=call_data,
                timeout=15,
            )
            resp.raise_for_status()
            call_sid = resp.json().get('sid', '')
            logger.info(
                '[TwilioVoice] Call initiated to %s ext=%r — sid=%s', customer_phone, ext_digits or None, call_sid
            )
            return DeliveryProviderResult(
                provider=self.provider_name,
                delivery_channel=self.delivery_channel,
                status='sent',
                detail=f'Voice call initiated to {customer_phone}' + (f' (ext {ext_digits})' if ext_digits else ''),
                external_reference=call_sid,
            )

        except httpx.HTTPStatusError as exc:
            logger.error(
                '[TwilioVoice] HTTP %s — %s', exc.response.status_code, exc.response.text
            )
            return DeliveryProviderResult(
                provider=self.provider_name,
                delivery_channel=self.delivery_channel,
                status='error',
                detail=f'Twilio API error {exc.response.status_code}: {exc.response.text[:200]}',
            )
        except Exception as exc:  # noqa: BLE001
            logger.error('[TwilioVoice] Unexpected error: %s', exc)
            return DeliveryProviderResult(
                provider=self.provider_name,
                delivery_channel=self.delivery_channel,
                status='error',
                detail=str(exc),
            )
