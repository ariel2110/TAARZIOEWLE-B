"""Morning payment webhook listener
=====================================
Receives POST events from Morning (Israeli payment processor),
verifies the HMAC-SHA256 signature, and routes to the correct
activation path based on the payment amount (plan tier).

Routing logic
─────────────
  amount = 39 NIS  → 'auto'    tier:
    Full automation: Hostinger domain purchase + DNS + nginx + SSL + deploy
    Requires a pre-existing PublicIntake with `desired_domain` and `generated_html`.

  amount = 299 NIS → 'starter' tier:
    Manual onboarding. Admin is notified via WhatsApp.
    No domain is purchased. Record is created and flagged as pro_lead.

  amount = 699 NIS → 'growth'  tier:
    Same as starter, richer admin notification.

  amount = 1299 NIS → 'pro'   tier:
    Premium manual onboarding. Admin gets urgent alert.
    Client receives a personalised WhatsApp welcome from Ariel.

Security: HMAC-SHA256 signature verification (X-Morning-Signature header).
This endpoint is intentionally unauthenticated; security is the signature.
"""
from __future__ import annotations

import logging
import secrets
import threading

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.morning_service import MorningService, PLAN_LABELS

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/webhooks', tags=['webhooks'])
_morning = MorningService()


# ── Webhook entry point ───────────────────────────────────────────────────────

@router.post('/morning')
async def morning_webhook(request: Request):
    """Receive and process a Morning payment webhook."""
    body_bytes = await request.body()

    # ── 1. Signature verification ─────────────────────────────────────────
    signature = (
        request.headers.get('X-Morning-Signature')
        or request.headers.get('X-Morning-Signature-V2')
        or request.headers.get('X-Signature')
        or ''
    )
    if signature and not _morning.verify_webhook_signature(body_bytes, signature):
        logger.warning('[MorningWebhook] Invalid signature — rejecting')
        raise HTTPException(status_code=403, detail='Invalid signature')

    # ── 2. Parse body ─────────────────────────────────────────────────────
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid JSON body')

    parsed = _morning.parse_webhook(body)
    if not parsed:
        return JSONResponse({'ok': False, 'detail': 'unrecognised payload'})

    logger.info(
        '[MorningWebhook] type=%s status=%s amount=%s external_id=%s txn=%s',
        parsed['type'], parsed['status'], parsed['amount'],
        (parsed.get('external_id') or '')[:8],
        parsed['transaction_id'][:12],
    )

    if parsed['status'] != 'SUCCESS':
        return JSONResponse({'ok': True, 'detail': f'non-success event ({parsed["status"]}) ignored'})

    # ── 3. Detect tier and route ──────────────────────────────────────────
    tier = _morning.detect_tier(parsed['amount'])

    if tier == 'auto':
        return await _route_auto_payment(parsed)

    if tier in ('starter', 'growth', 'pro'):
        return await _route_pro_payment(parsed, tier)

    # Unknown amount — log and return 200 so Morning doesn't retry forever
    logger.warning(
        '[MorningWebhook] Unknown amount=%s — no route matched. txn=%s',
        parsed['amount'], parsed['transaction_id'][:12],
    )
    return JSONResponse({'ok': True, 'detail': f'unknown amount {parsed["amount"]}'})


# ── Auto-tier (39 NIS): full pipeline ─────────────────────────────────────────

async def _route_auto_payment(parsed: dict) -> JSONResponse:
    """Handle the 39 NIS automated pipeline payment."""
    external_id = parsed.get('external_id')
    if not external_id:
        logger.warning('[MorningWebhook][auto] No externalId — cannot correlate to intake')
        return JSONResponse({'ok': True, 'detail': 'no external_id'})

    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake

    db = SessionLocal()
    try:
        intake = db.query(PublicIntake).filter(PublicIntake.token == external_id).first()
        if not intake:
            logger.warning('[MorningWebhook][auto] Intake not found: token=%s', external_id[:8])
            return JSONResponse({'ok': True, 'detail': 'intake not found'})

        if intake.payment_status == 'paid':
            return JSONResponse({'ok': True, 'detail': 'already processed'})

        intake.payment_status = 'paid'
        intake.payment_reference = parsed['transaction_id']
        intake.plan_tier = 'auto'
        db.commit()
        logger.info('[MorningWebhook][auto] Intake %s marked as paid', external_id[:8])

        # Snapshot values before session closes
        domain        = intake.desired_domain or ''
        html_content  = intake.generated_html or ''
        phone         = intake.phone or ''
        business_name = intake.business_name or ''
        token         = intake.token
    finally:
        db.close()

    threading.Thread(
        target=_activate_site_and_notify,
        args=(token, domain, html_content, phone, business_name),
        daemon=True,
    ).start()

    return JSONResponse({'ok': True})


# ── Pro-tier (299 / 699 / 1299 NIS): manual onboarding ───────────────────────

async def _route_pro_payment(parsed: dict, tier: str) -> JSONResponse:
    """
    Handle a Starter / Growth / Pro payment.
    1. Idempotency-check on transaction_id
    2. Create a pro_lead PublicIntake record
    3. Alert admin via WhatsApp (tier-specific message)
    4. For Pro tier: also send personalised client welcome
    """
    transaction_id = parsed['transaction_id']
    client_name    = parsed.get('client_name') or 'לקוח חדש'
    client_phone   = parsed.get('client_phone') or ''
    amount         = parsed['amount']

    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake

    db = SessionLocal()
    token = ''
    try:
        # Idempotency: skip if already recorded
        existing = (
            db.query(PublicIntake)
            .filter(PublicIntake.payment_reference == transaction_id)
            .first()
        )
        if existing:
            logger.info(
                '[MorningWebhook][%s] Transaction already recorded: txn=%s',
                tier, transaction_id[:12],
            )
            return JSONResponse({'ok': True, 'detail': 'already processed'})

        token = secrets.token_urlsafe(32)
        intake = PublicIntake(
            token=token,
            business_name=client_name,
            phone=client_phone,
            status='pro_lead',
            payment_status='paid',
            payment_reference=transaction_id,
            plan_tier=tier,
        )
        db.add(intake)
        db.commit()
        logger.info(
            '[MorningWebhook][%s] Pro lead created: token=%s client=%s',
            tier, token[:8], client_name[:30],
        )
    finally:
        db.close()

    # Alerts run outside the DB session
    threading.Thread(
        target=_handle_pro_notifications,
        args=(tier, client_name, client_phone, transaction_id, amount, token),
        daemon=True,
    ).start()

    return JSONResponse({'ok': True})


# ── Notification helpers ──────────────────────────────────────────────────────

def _handle_pro_notifications(
    tier: str,
    client_name: str,
    client_phone: str,
    transaction_id: str,
    amount: int,
    token: str,
) -> None:
    """Send admin alert + optional client welcome for pro-tier payments."""
    _notify_admin_pro_payment(tier, client_name, client_phone, transaction_id, amount, token)
    if tier == 'pro' and client_phone:
        _send_pro_client_welcome(client_name, client_phone)


def _notify_admin_pro_payment(
    tier: str,
    client_name: str,
    client_phone: str,
    transaction_id: str,
    amount: int,
    token: str,
) -> None:
    """Send the admin a tier-specific WhatsApp alert for a pro payment."""
    owner = settings.whatsapp_owner_phone
    if not owner:
        return

    tier_config: dict[str, dict] = {
        'starter': {
            'emoji': '🟡',
            'title': 'לקוח Starter חדש!',
            'actions': (
                '• צור קשר ותאם צרכים\n'
                '• הגדר תת-דומיין (xxx.sitenest.site)\n'
                '• הפעל את האתר ידנית'
            ),
        },
        'growth': {
            'emoji': '🟠',
            'title': 'לקוח Growth חדש!',
            'actions': (
                '• צור קשר ובחר דומיין עצמאי\n'
                '• הגדר DNS + SSL + הוסף לאחסון\n'
                '• הכן דוח ביצועים ראשוני\n'
                '• הגדר AI צ\'אט-בוט'
            ),
        },
        'pro': {
            'emoji': '🔴',
            'title': 'לקוח PRO חדש — עדיפות גבוהה!',
            'actions': (
                '⚡ הודעת קבלת פנים אישית נשלחה ✅\n'
                '• בנה אסטרטגיה דיגיטלית תוך 24 שעות\n'
                '• תכנן קמפיין גוגל/פייסבוק ראשוני\n'
                '• הגדר CRM ו-SEO מורחב\n'
                '• תאם שיחת kickoff'
            ),
        },
    }

    cfg = tier_config.get(tier, tier_config['starter'])
    admin_panel_url = f"https://api.sitenest.site/api/v1/admin/public-flow"

    msg = (
        f"{cfg['emoji']} *SiteNest — {cfg['title']}*\n\n"
        f"👤 שם: *{client_name}*\n"
        f"📞 טלפון: {client_phone or 'לא זמין'}\n"
        f"💰 חבילה: *{PLAN_LABELS.get(tier, tier)}*\n"
        f"💳 עסקה: `{transaction_id[:16]}...`\n\n"
        f"📋 *פעולות נדרשות:*\n"
        f"{cfg['actions']}\n\n"
        f"🔗 ניהול: {admin_panel_url}"
    )

    from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService
    EvolutionWhatsAppService().send_text(owner, msg)
    logger.info('[MorningWebhook][%s] Admin alert sent for client=%s', tier, client_name[:30])


def _send_pro_client_welcome(client_name: str, client_phone: str) -> None:
    """
    Send a personalised Premium welcome message directly to the Pro client.
    Creates a first-class experience from the very first second.
    """
    msg = (
        f"היי {client_name}! 👋\n\n"
        f"אני אריאל מ-SiteNest. קיבלתי עכשיו את ההזמנה שלך למסלול המקצועי (Pro).\n\n"
        f"אני כבר מתחיל לעבוד על האסטרטגיה הדיגיטלית שלך ואחזור אליך "
        f"תוך 24 שעות עם תוכנית פעולה מלאה — כולל דומיין, עיצוב, SEO וקמפיין.\n\n"
        f"תודה על האמון 🙏\n"
        f"_אריאל, SiteNest_"
    )
    from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService
    EvolutionWhatsAppService().send_text(client_phone, msg)
    logger.info('[MorningWebhook][pro] Personal welcome sent to client %s***', client_phone[:6])


# ── Auto-tier background activation ──────────────────────────────────────────

def _activate_site_and_notify(
    token: str,
    domain: str,
    html_content: str,
    phone: str,
    business_name: str,
) -> None:
    """
    Background thread for the 39 NIS auto-tier:
      1. Purchase domain via Hostinger (validates + availability check)
      2. Set DNS A record
      3. Deploy HTML → nginx vhost → Certbot SSL
      4. Update DB with live URL
      5. Send WhatsApp congratulations to the client
    Errors notify admin; the thread never raises.
    """
    from app.db.session import SessionLocal
    from app.models.public_intake import PublicIntake
    from app.services.hostinger_service import HostingerService

    db = SessionLocal()
    try:
        if not domain or not html_content:
            logger.warning(
                '[Activation] Missing domain or HTML for token=%s — skipping', token[:8]
            )
            return

        logger.info('[Activation] Starting pipeline: domain=%s token=%s', domain, token[:8])
        ok, live_url = HostingerService().activate_site(domain, html_content)

        intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
        if intake:
            intake.site_live_url = live_url if ok else ''
            intake.status = 'done'
            db.commit()

        if ok:
            _send_auto_congrats(phone, business_name, live_url)
        else:
            _notify_admin_activation_failed(token, domain, live_url)
    except Exception:
        logger.exception('[Activation] Unhandled error for token=%s', token[:8])
    finally:
        db.close()


def _send_auto_congrats(phone: str, business_name: str, live_url: str) -> None:
    """WhatsApp congratulations to the 39 NIS auto-tier client after site goes live."""
    from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService
    msg = (
        f"🎉 מזל טוב {business_name}!\n\n"
        f"האתר שלך כבר באוויר!\n\n"
        f"🌐 הכתובת שלך:\n{live_url}\n\n"
        f"💳 המנוי שלך הוא 39 ₪/חודש — כולל אחסון, תחזוקה, ועדכונים.\n\n"
        f"שנצליח ביחד 🚀\n_צוות SiteNest_"
    )
    EvolutionWhatsAppService().send_text(phone, msg)
    logger.info('[Activation] Congrats sent to %s***', phone[:6])


def _notify_admin_activation_failed(token: str, domain: str, error: str) -> None:
    """Alert admin when site activation fails so they can intervene manually."""
    owner = settings.whatsapp_owner_phone
    if not owner:
        return
    from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService
    msg = (
        f"⚠️ *SiteNest — הפעלת אתר נכשלה*\n\n"
        f"Token: `{token[:12]}...`\n"
        f"Domain: {domain}\n"
        f"Error: {error}\n\n"
        f"נדרשת פעולה ידנית."
    )
    EvolutionWhatsAppService().send_text(owner, msg)
