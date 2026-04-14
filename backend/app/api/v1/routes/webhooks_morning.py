"""Morning payment webhook listener
=====================================
Receives POST events from Morning (Israeli payment processor),
verifies the HMAC-SHA256 signature, and triggers site activation.

Webhook event flow:
  Morning → POST /webhooks/morning
    → verify signature
    → parse body → find intake by externalId
    → on SUCCESS: purchase domain + deploy site + send WhatsApp

This endpoint is intentionally unauthenticated (public) because
Morning needs to reach it without a JWT. Security is provided exclusively
by the HMAC signature verification.
"""
from __future__ import annotations

import logging
import threading

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.morning_service import MorningService

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/webhooks', tags=['webhooks'])
_morning = MorningService()


@router.post('/morning')
async def morning_webhook(request: Request):
    """Receive and process a Morning payment webhook."""
    body_bytes = await request.body()

    # ── 1. Signature verification ─────────────────────────────────────────────
    signature = (
        request.headers.get('X-Morning-Signature')
        or request.headers.get('X-Morning-Signature-V2')
        or request.headers.get('X-Signature')
        or ''
    )
    if signature and not _morning.verify_webhook_signature(body_bytes, signature):
        logger.warning('[MorningWebhook] Invalid signature')
        raise HTTPException(status_code=403, detail='Invalid signature')

    # ── 2. Parse body ─────────────────────────────────────────────────────────
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid JSON body')

    parsed = _morning.parse_webhook(body)
    if not parsed:
        return JSONResponse({'ok': False, 'detail': 'unrecognised payload'})

    logger.info(
        '[MorningWebhook] type=%s status=%s external_id=%s txn=%s',
        parsed['type'], parsed['status'], parsed.get('external_id', '')[:8], parsed['transaction_id'][:12],
    )

    if parsed['status'] != 'SUCCESS':
        return JSONResponse({'ok': True, 'detail': 'non-success event ignored'})

    external_id = parsed.get('external_id')
    if not external_id:
        logger.warning('[MorningWebhook] No externalId in webhook — cannot link to intake')
        return JSONResponse({'ok': True, 'detail': 'no external_id'})

    # ── 3. Find intake + mark paid ────────────────────────────────────────────
    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake

    db = SessionLocal()
    try:
        intake = db.query(PublicIntake).filter(PublicIntake.token == external_id).first()
        if not intake:
            logger.warning('[MorningWebhook] Intake not found for token=%s', external_id[:8])
            return JSONResponse({'ok': True, 'detail': 'intake not found'})

        if intake.payment_status == 'paid':
            return JSONResponse({'ok': True, 'detail': 'already processed'})

        intake.payment_status = 'paid'
        intake.payment_reference = parsed['transaction_id']
        db.commit()
        logger.info('[MorningWebhook] Intake %s marked as paid', external_id[:8])

        # Capture values needed for background task before closing session
        domain = intake.desired_domain or ''
        html_content = intake.generated_html or ''
        phone = intake.phone or ''
        business_name = intake.business_name or ''
        token = intake.token
    finally:
        db.close()

    # ── 4. Trigger activation in background ──────────────────────────────────
    threading.Thread(
        target=_activate_site_and_notify,
        args=(token, domain, html_content, phone, business_name),
        daemon=True,
    ).start()

    return JSONResponse({'ok': True})


# ── Background activation ─────────────────────────────────────────────────────

def _activate_site_and_notify(
    token: str,
    domain: str,
    html_content: str,
    phone: str,
    business_name: str,
) -> None:
    """
    Background task:
      1. Validate domain + re-check availability
      2. Purchase domain
      3. Set DNS, deploy HTML, nginx vhost, SSL
      4. Update DB with live URL
      5. Send WhatsApp congratulations
    """
    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake
    from app.services.hostinger_service import HostingerService
    from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService

    db = SessionLocal()
    try:
        if not domain or not html_content:
            logger.warning('[Activation] Missing domain or HTML for token=%s', token[:8])
            return

        logger.info('[Activation] Starting for domain=%s token=%s', domain, token[:8])
        ok, live_url = HostingerService().activate_site(domain, html_content)

        # Update intake
        intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
        if intake:
            intake.site_live_url = live_url if ok else ''
            intake.status = 'done'
            db.commit()

        if ok:
            _send_congrats(phone, business_name, live_url)
        else:
            _notify_admin_activation_failed(token, domain, live_url)
    except Exception:
        logger.exception('[Activation] Unhandled error for token=%s', token[:8])
    finally:
        db.close()


def _send_congrats(phone: str, business_name: str, live_url: str) -> None:
    """Send a WhatsApp congratulations message to the lead."""
    from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService
    message = (
        f"🎉 מזל טוב {business_name}!\n\n"
        f"האתר שלך כבר באוויר!\n\n"
        f"🌐 הכתובת שלך:\n{live_url}\n\n"
        f"💳 נזכיר שהמנוי שלך הוא 39 ₪/חודש — כולל אחסון, תחזוקה, ועדכונים.\n\n"
        f"שנצליח ביחד 🚀\n_צוות SiteNest_"
    )
    EvolutionWhatsAppService().send_text(phone, message)
    logger.info('[Activation] Congrats WhatsApp sent to %s***', phone[:6])


def _notify_admin_activation_failed(token: str, domain: str, error: str) -> None:
    """Notify admin if site activation failed."""
    owner = settings.whatsapp_owner_phone
    if not owner:
        return
    from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService
    msg = (
        f"⚠️ *SiteNest — הפעלת אתר נכשלה*\n\n"
        f"Token: {token[:12]}...\n"
        f"Domain: {domain}\n"
        f"Error: {error}\n\n"
        f"נדרשת פעולה ידנית."
    )
    EvolutionWhatsAppService().send_text(owner, msg)
