"""Meta Cloud API WhatsApp Service
====================================
Sends WhatsApp messages via Meta's official Cloud API (no self-hosted server needed).
Drop-in replacement for EvolutionWhatsAppService.

Meta Cloud API docs: https://developers.facebook.com/docs/whatsapp/cloud-api

Setup (.env):
    META_WA_PHONE_NUMBER_ID=your_phone_number_id   # from Meta Business Manager
    META_WA_ACCESS_TOKEN=your_permanent_token       # System User permanent token
    WHATSAPP_VERIFY_TOKEN=tazo-web-verify           # for webhook verification

Phone Number ID:
    Meta Business Manager → WhatsApp → API Setup → Phone number ID

Access Token:
    Meta Business Manager → System Users → Create System User (Admin) →
    Generate token → Select whatsapp_business_messaging permission → Generate

The service auto-normalises Israeli phone numbers:
  052-123-4567 → 972521234567
"""
from __future__ import annotations

import logging
import re

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 15  # seconds
_META_API_BASE = "https://graph.facebook.com/v19.0"


class MetaWhatsAppService:
    """Send WhatsApp messages through Meta Cloud API (official)."""

    # ── Public API ─────────────────────────────────────────────────────────

    def send_text(self, phone: str, message: str) -> bool:
        """Send a plain-text WhatsApp message.

        Returns True on success, False when Meta API is not configured
        or the request fails (failure is always logged, never raised).
        """
        if not self._is_configured():
            logger.info("[MetaWA] Not configured — skipping send")
            return False

        e164 = self._normalize(phone)
        if not e164:
            logger.warning("[MetaWA] Invalid phone number: %r", phone)
            return False

        url = f"{_META_API_BASE}/{settings.meta_wa_phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": e164,
            "type": "text",
            "text": {"body": message, "preview_url": False},
        }
        headers = {
            "Authorization": f"Bearer {settings.meta_wa_access_token}",
            "Content-Type": "application/json",
        }

        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=_TIMEOUT)
            resp.raise_for_status()
            logger.info("[MetaWA] Sent to %s*** — status %d", e164[:8], resp.status_code)
            return True
        except httpx.HTTPStatusError as e:
            logger.warning(
                "[MetaWA] HTTP %d sending to %s***: %s",
                e.response.status_code, e164[:8], e.response.text[:300],
            )
        except Exception as e:
            logger.warning("[MetaWA] Failed to send: %s", e)

        return False

    def send_with_link_preview(self, phone: str, message: str, url: str, title: str = "") -> bool:
        """Send a message with link preview enabled."""
        if not self._is_configured():
            return False

        e164 = self._normalize(phone)
        if not e164:
            return False

        endpoint = f"{_META_API_BASE}/{settings.meta_wa_phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": e164,
            "type": "text",
            "text": {"body": f"{message}\n\n{url}", "preview_url": True},
        }
        headers = {
            "Authorization": f"Bearer {settings.meta_wa_access_token}",
            "Content-Type": "application/json",
        }

        try:
            resp = httpx.post(endpoint, json=payload, headers=headers, timeout=_TIMEOUT)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.warning("[MetaWA] link-preview send failed: %s", e)
            return False

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _is_configured(self) -> bool:
        return bool(
            getattr(settings, "meta_wa_phone_number_id", None)
            and getattr(settings, "meta_wa_access_token", None)
        )

    def _normalize(self, phone: str) -> str | None:
        """Convert any Israeli phone format → E.164 digits (no + prefix).
        972521234567  ← Meta expects this format (no @, no +)
        """
        digits = re.sub(r"\D", "", phone or "")
        if not digits:
            return None
        digits = digits.lstrip("+")
        # Israeli local: starts with 0 and 10 digits
        if digits.startswith("0") and len(digits) == 10:
            digits = "972" + digits[1:]
        # Already international with country code
        if len(digits) >= 11:
            return digits
        logger.warning("[MetaWA] Cannot normalise phone: %r → %r", phone, digits)
        return None
