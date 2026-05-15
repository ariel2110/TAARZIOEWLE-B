"""Morning.co.il payment service
================================
Creates subscription payment links and verifies incoming webhooks.

Morning API docs: https://developers.morning.co.il/

Flow:
1. `create_payment_link(token, business_name, phone, domain)` →
   returns URL the user redirects to (dynamic Morning page or fixed fallback)
2. Morning fires POST webhook on payment success
3. `verify_webhook_signature(body_bytes, signature)` → bool
4. Parse webhook body → extract `externalId` (= intake token) + status
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_BASE_URL = 'https://api.morning.co.il/v1'
_TIMEOUT = 15
_PRICE_NIS = 39

# ── Plan tier definitions ─────────────────────────────────────────────────────

# Maps payment amount (NIS) → internal tier label.
# 'auto'    = 39 NIS  → full automation (Hostinger domain + SSL + deploy)
# 'starter' = 299 NIS → manual onboarding, sub-domain only
# 'growth'  = 699 NIS → manual onboarding, independent domain
# 'pro'     = 1299 NIS → premium manual onboarding, personal account manager
PLAN_AMOUNTS: dict[str, int] = {
    'auto':    39,
    'starter': 299,
    'growth':  699,
    'pro':     1299,
}

# Reverse lookup: amount → tier
_AMOUNT_TO_TIER: dict[int, str] = {v: k for k, v in PLAN_AMOUNTS.items()}

# Fixed Morning payment links (created in Morning dashboard, not generated dynamically)
PLAN_URLS: dict[str, str] = {
    'auto':    'https://mrng.to/Afe6Dg21q0',   # 39 NIS — automated pipeline
    'starter': 'https://mrng.to/sHDNNsGZwX',  # 299 NIS — Starter
    'growth':  'https://mrng.to/nTNb7uWesR',   # 699 NIS — Growth
    'pro':     'https://mrng.to/SDxruL9Hg0',   # 1299 NIS — Pro
}

PLAN_LABELS: dict[str, str] = {
    'auto':    'Auto — 39 ₪/חודש',
    'starter': 'Starter — 299 ₪/חודש',
    'growth':  'Growth — 699 ₪/חודש',
    'pro':     'Pro — 1,299 ₪/חודש',
}


class MorningService:

    # ── Public API ────────────────────────────────────────────────────────────

    def detect_tier(self, amount: int) -> str:
        """
        Map a payment amount (NIS) to a tier label.
        Returns 'auto', 'starter', 'growth', 'pro', or 'unknown'.
        """
        return _AMOUNT_TO_TIER.get(amount, 'unknown')

    def create_checkout_session(
        self,
        lead_id: str,
        plan: str = 'auto',
        business_name: str = '',
        phone: str = '',
        domain: str | None = None,
    ) -> str:
        """
        Return the Morning checkout URL for a given lead and plan.

        - plan='auto'   : creates a dynamic per-lead link with externalId=lead_id
                          so the webhook can correlate payment → intake record.
        - plan=anything : returns the fixed Morning URL for that plan tier.
                          The customer pays directly; admin handles onboarding.
        """
        if plan == 'auto':
            return self.create_payment_link(
                intake_token=lead_id,
                business_name=business_name,
                phone=phone,
                domain=domain,
            )
        url = PLAN_URLS.get(plan)
        if not url:
            logger.warning('[Morning] Unknown plan %r — falling back to starter URL', plan)
            url = PLAN_URLS['starter']
        logger.info('[Morning] Returning fixed plan URL for plan=%s lead_id=%s', plan, (lead_id or '')[:8])
        return url

    def create_payment_link(
        self,
        intake_token: str,
        business_name: str,
        phone: str,
        domain: str | None = None,
    ) -> str:
        """
        Create a Morning payment checkout URL for a 39 NIS/month subscription.

        Returns the checkout URL. Falls back to the fixed Morning link if
        dynamic creation is not configured or fails.
        """
        if not self._is_configured():
            logger.info('[Morning] API not configured — using fixed payment URL')
            return settings.morning_fixed_payment_url

        description = f'TAZO-WEB — אתר חודשי · {business_name}'
        if domain:
            description += f' · {domain}'

        payload: dict = {
            'description': description,
            'price': _PRICE_NIS,
            'currency': 'ILS',
            # externalId — Morning's primary correlation field (returned in webhook)
            'externalId': intake_token,
            # custom — secondary free-text field mapped to the internal LeadID/token
            # so Morning dashboard and webhook both carry the reference
            'custom': intake_token,
            'successUrl': f'{settings.morning_success_url}?token={intake_token}',
            'cancelUrl': settings.morning_cancel_url,
            'client': {'name': business_name, 'phone': phone},
        }
        if settings.morning_plan_id:
            payload['planId'] = settings.morning_plan_id

        try:
            resp = httpx.post(
                f'{_BASE_URL}/paymentlinks',
                json=payload,
                headers=self._headers(),
                timeout=_TIMEOUT,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                url = data.get('url') or data.get('link') or data.get('paymentUrl') or data.get('checkout_url')
                if url:
                    logger.info('[Morning] Payment link created for token=%s', intake_token[:8])
                    return url
            logger.warning('[Morning] Unexpected response %d: %s', resp.status_code, resp.text[:200])
        except Exception as exc:
            logger.warning('[Morning] Failed to create payment link: %s', exc)

        # Fallback to the fixed 39 NIS link
        return settings.morning_fixed_payment_url

    def verify_webhook_signature(self, body_bytes: bytes, signature: str) -> bool:
        """
        Verify Morning webhook HMAC-SHA256 signature.
        The signature is computed over the raw request body using the webhook secret.
        """
        secret = settings.morning_webhook_secret or settings.morning_api_secret or ''
        if not secret:
            logger.warning('[Morning] Webhook secret not configured — skipping verification')
            return True  # fail-open in dev; production should always have a secret
        expected = hmac.new(
            key=secret.encode('utf-8'),
            msg=body_bytes,
            digestmod=hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature.lower().strip())

    def parse_webhook(self, body: dict) -> dict | None:
        """
        Parse a Morning webhook body and return a normalised dict:
        {
          'type': 'payment.success' | 'payment.failed' | ...,
          'external_id': str | None,
          'transaction_id': str,
          'amount': int,
          'status': 'SUCCESS' | 'FAILED' | ...,
        }
        Returns None if the body is unrecognisable.
        """
        # Morning may use different field names depending on version / event type
        event_type = (
            body.get('eventType')
            or body.get('event_type')
            or body.get('type')
            or 'unknown'
        )

        # Dig for the transaction / document block
        txn = body.get('transaction') or body.get('document') or body

        external_id = (
            body.get('externalId')
            or body.get('external_id')
            or body.get('custom')          # fallback to custom field (also carries token)
            or txn.get('externalId')
            or txn.get('external_id')
            or txn.get('custom')
        )
        transaction_id = (
            body.get('transactionId')
            or body.get('id')
            or txn.get('id')
            or txn.get('documentId')
        )
        status = (
            body.get('status')
            or txn.get('status')
            or 'UNKNOWN'
        )
        amount = int(body.get('amount') or txn.get('amount') or txn.get('price') or 0)

        # Extract client info (present in pro-tier fixed-link webhooks
        # where externalId is not set)
        client_block = body.get('client') or txn.get('client') or {}
        client_name = (
            client_block.get('name')
            or body.get('clientName')
            or body.get('client_name')
            or txn.get('clientName')
            or ''
        )
        client_phone = (
            client_block.get('phone')
            or client_block.get('mobile')
            or body.get('clientPhone')
            or body.get('client_phone')
            or ''
        )
        email = (
            client_block.get('email')
            or body.get('clientEmail')
            or body.get('email')
            or txn.get('email')
            or ''
        )
        product_name = (
            body.get('productName')
            or body.get('product_name')
            or txn.get('productName')
            or txn.get('name')
            or txn.get('description')
            or ''
        )

        return {
            'type': event_type,
            'external_id': external_id,
            'transaction_id': str(transaction_id or ''),
            'amount': amount,
            'status': str(status).upper(),
            'client_name': client_name,
            'client_phone': client_phone,
            'email': email,
            'product_name': product_name,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _is_configured(self) -> bool:
        return bool(settings.morning_api_key and settings.morning_api_secret)

    def _headers(self) -> dict:
        import base64
        credentials = base64.b64encode(
            f'{settings.morning_api_key}:{settings.morning_api_secret}'.encode()
        ).decode()
        return {
            'Authorization': f'Basic {credentials}',
            'Content-Type': 'application/json',
        }
