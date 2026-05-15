"""Evolution API WhatsApp Service
=================================
Sends WhatsApp messages via a self-hosted Evolution API instance.
Falls back gracefully when not configured — no exceptions propagate.

Evolution API docs: https://doc.evolution-api.com/

Setup (in .env):
    EVOLUTION_API_URL=http://localhost:8080
    EVOLUTION_API_KEY=your-api-key
    EVOLUTION_INSTANCE=TAZO-WEB          # the instance name you created

The service auto-normalises Israeli phone numbers:
  052-123-4567 → 972521234567@s.whatsapp.net
"""
from __future__ import annotations

import logging
import re

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 15  # seconds


class EvolutionWhatsAppService:
    """Send WhatsApp messages through a self-hosted Evolution API."""

    # ── Public API ────────────────────────────────────────────────────────────

    def send_text(self, phone: str, message: str) -> bool:
        """Send a plain-text WhatsApp message.

        Returns True on success, False when Evolution API is not configured
        or the request fails (failure is always logged, never raised).
        """
        if not self._is_configured():
            logger.info("[EvolutionWA] Not configured — skipping send")
            return False

        phone_jid = self._normalize(phone)
        if not phone_jid:
            logger.warning("[EvolutionWA] Invalid phone number: %r", phone)
            return False

        url = (
            f"{settings.evolution_api_url.rstrip('/')}"
            f"/message/sendText/{settings.evolution_instance}"
        )
        payload = {"number": phone_jid, "textMessage": {"text": message}}
        headers = {"apikey": settings.evolution_api_key, "Content-Type": "application/json"}

        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=_TIMEOUT)
            resp.raise_for_status()
            logger.info(
                "[EvolutionWA] Sent to %s*** — status %d",
                phone_jid[:10], resp.status_code,
            )
            return True
        except httpx.HTTPStatusError as e:
            logger.warning(
                "[EvolutionWA] HTTP %d sending to %s***: %s",
                e.response.status_code, phone_jid[:10], e.response.text[:200],
            )
        except Exception as e:
            logger.warning("[EvolutionWA] Failed to send: %s", e)

        return False

    def send_with_link_preview(self, phone: str, message: str, url: str, title: str = "") -> bool:
        """Send a message with a link preview card (Evolution API linkPreview endpoint)."""
        if not self._is_configured():
            return False

        phone_jid = self._normalize(phone)
        if not phone_jid:
            return False

        endpoint = (
            f"{settings.evolution_api_url.rstrip('/')}"
            f"/message/sendText/{settings.evolution_instance}"
        )
        payload = {
            "number": phone_jid,
            "textMessage": {"text": f"{message}\n\n{url}"},
            "linkPreview": True,
        }
        headers = {"apikey": settings.evolution_api_key, "Content-Type": "application/json"}

        try:
            resp = httpx.post(endpoint, json=payload, headers=headers, timeout=_TIMEOUT)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.warning("[EvolutionWA] link-preview send failed: %s", e)
            return False

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _is_configured(self) -> bool:
        return bool(
            settings.evolution_api_url
            and settings.evolution_api_key
            and settings.evolution_instance
        )

    def _normalize(self, phone: str) -> str | None:
        """Convert any Israeli phone format → E.164 JID (972XXXXXXXXX@s.whatsapp.net)."""
        digits = re.sub(r"\D", "", phone or "")
        if not digits:
            return None
        # Strip leading +
        digits = digits.lstrip("+")
        # Israeli local: starts with 0 and 10 digits
        if digits.startswith("0") and len(digits) == 10:
            digits = "972" + digits[1:]
        # Already international with 972
        if not digits.startswith("972") or len(digits) < 11:
            logger.debug("[EvolutionWA] Phone %r not normalized cleanly — using as-is", phone)
        return f"{digits}@s.whatsapp.net"
