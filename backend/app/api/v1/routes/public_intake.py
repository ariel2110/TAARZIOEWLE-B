"""
Public intake form endpoint — serves sitenest.site landing page form.
Allows potential customers to submit their business info, social links, and images.

VIP flow: POST /public/google-vip  →  exchange Google ID token for a short-lived VIP JWT
          The VIP JWT is then sent as vip_token= in the intake form to bypass rate limiting.
"""
import json
import logging
import os
import re
import secrets
import uuid
from pathlib import Path

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_vip_token, verify_vip_token
from app.db.session import get_db
from app.models.public_intake import PublicIntake
from app.services.common.rate_limit_service import RateLimitService

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/public', tags=['public-intake'])
_rate_svc = RateLimitService()

# Where uploaded images are stored (relative to backend root)
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'static_sites' / 'uploads' / 'intake'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Where AI-generated intake previews are saved
PREVIEW_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'static_sites' / 'intake_previews'
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_CORRECTIONS = 3

# ── Demo submission rate limits ─────────────────────────────────────────────
# Prevents token burning and abuse from sitenest.site public intake form.
_DEMO_IP_MAX       = 3    # max 3 submissions per IP per 24 h
_DEMO_IP_WINDOW    = 1440 # 24 hours in minutes
_DEMO_PHONE_MAX    = 2    # same phone can only submit 2 demos total (all-time: use very long window)
_DEMO_PHONE_WINDOW = 43200  # 30 days in minutes


# ── Response schemas ────────────────────────────────────────────────────────
class IntakeSubmitResponse(BaseModel):
    token: str
    status: str
    message: str


class VipTokenResponse(BaseModel):
    vip_token: str
    expires_in_minutes: int


class IntakeStatusResponse(BaseModel):
    token: str
    business_name: str
    phone: str
    facebook_url: str | None
    tiktok_url: str | None
    instagram_url: str | None
    website_url: str | None
    description: str | None
    image_urls: list[str]
    status: str
    correction_count: int
    corrections_remaining: int
    admin_note: str | None
    created_at: str | None
    ai_status: str | None
    generated_preview_url: str | None
    # Payment & domain activation
    desired_domain: str | None
    payment_status: str
    payment_link: str | None
    site_live_url: str | None


# ── Helper ──────────────────────────────────────────────────────────────────
def _safe_url(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    # Block dangerous URI schemes (javascript:, data:, vbscript:, etc.)
    if re.match(r'^(javascript|data|vbscript|blob)\s*:', url, re.IGNORECASE):
        return None
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url[:500] if url else None


def _build_status_response(intake: PublicIntake) -> IntakeStatusResponse:
    images = json.loads(intake.image_filenames or '[]')
    image_urls = [f'/static/uploads/intake/{fn}' for fn in images]
    return IntakeStatusResponse(
        token=intake.token,
        business_name=intake.business_name,
        phone=intake.phone,
        facebook_url=intake.facebook_url,
        tiktok_url=intake.tiktok_url,
        instagram_url=intake.instagram_url,
        website_url=intake.website_url,
        description=intake.description,
        image_urls=image_urls,
        status=intake.status,
        correction_count=intake.correction_count,
        corrections_remaining=max(0, MAX_CORRECTIONS - intake.correction_count),
        admin_note=intake.admin_note,
        created_at=intake.created_at.isoformat() if intake.created_at else None,
        ai_status=intake.ai_status,
        generated_preview_url=intake.generated_preview_url,
        desired_domain=intake.desired_domain,
        payment_status=intake.payment_status or 'unpaid',
        payment_link=intake.payment_link,
        site_live_url=intake.site_live_url,
    )


# ── POST /public/google-vip ─────────────────────────────────────────────────
class GoogleVipRequest(BaseModel):
    id_token: str  # Google ID token from Sign-In button


@router.post('/google-vip', response_model=VipTokenResponse)
async def google_vip_login(payload: GoogleVipRequest) -> VipTokenResponse:
    """Exchange a Google ID token for a short-lived VIP intake token.
    VIP users bypass per-IP and per-phone rate limiting on the intake form.
    """
    if not settings.google_client_id:
        raise HTTPException(status_code=503, detail='Google Sign-In is not configured on this server.')

    # Verify the Google ID token with Google's tokeninfo endpoint
    try:
        resp = httpx.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': payload.id_token},
            timeout=8,
        )
        resp.raise_for_status()
        token_info = resp.json()
    except Exception:
        raise HTTPException(status_code=401, detail='Failed to verify Google token. Please try again.')

    # Validate audience matches our client ID
    if token_info.get('aud') != settings.google_client_id:
        raise HTTPException(status_code=401, detail='Google token audience mismatch.')

    google_sub = token_info.get('sub', '')
    email = token_info.get('email', '')

    if not google_sub:
        raise HTTPException(status_code=401, detail='Invalid Google token — no subject claim.')

    vip_token = create_vip_token(google_sub=google_sub, email=email)
    return VipTokenResponse(
        vip_token=vip_token,
        expires_in_minutes=settings.google_vip_token_expire_minutes,
    )


# ── Admin approval notification helper ─────────────────────────────────────
def _notify_admin_approval(token: str, business_name: str, phone: str, message: str) -> None:
    """Send the admin a WhatsApp notification with a link to approve/edit/reject the message."""
    from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService
    owner_phone = getattr(settings, 'whatsapp_owner_phone', '') or ''
    if not owner_phone:
        return
    approve_url = f"{settings.api_base_url}/static/approve.html?key={settings.admin_dev_token}"
    notification = (
        f"📋 *SiteNest - הודעה ממתינה לאישורך*\n\n"
        f"👤 לקוח: *{business_name}*\n"
        f"📞 טלפון: {phone}\n\n"
        f"✉️ *ההודעה המוצעת:*\n"
        f"─────────────────\n"
        f"{message}\n"
        f"─────────────────\n\n"
        f"🔗 לאישור / עריכה / דחייה:\n{approve_url}"
    )
    EvolutionWhatsAppService().send_text(owner_phone, notification)


# ── Background task: run AI pipeline for public intake ──────────────────────
def _run_intake_pipeline(token: str) -> None:
    """Background task that runs the full 5-stage AutoSite pipeline on a public intake.
    Saves the generated HTML as a preview, auto-sends WhatsApp outreach if Evolution API
    is configured, and updates intake status to 'in_review' when done.
    """
    from app.services.generator.autosite_pipeline_service import AutoSitePipelineService
    from app.services.communications.evolution_whatsapp_service import EvolutionWhatsAppService

    db = None
    try:
        db = __import__('app.db.session', fromlist=['SessionLocal']).SessionLocal()
        intake: PublicIntake | None = db.query(PublicIntake).filter(PublicIntake.token == token).first()
        if not intake:
            return

        intake.ai_status = 'generating'
        db.commit()

        # Build a pseudo-Google Maps input from intake form data
        lines = [
            f"Name: {intake.business_name}",
            f"Phone: {intake.phone}",
        ]
        if intake.facebook_url:
            lines.append(f"Facebook: {intake.facebook_url}")
        if intake.instagram_url:
            lines.append(f"Instagram: {intake.instagram_url}")
        if intake.tiktok_url:
            lines.append(f"TikTok: {intake.tiktok_url}")
        if intake.website_url:
            lines.append(f"Website: {intake.website_url}")
        if intake.description:
            lines.append(f"Description: {intake.description}")

        enrichment = {
            'name': intake.business_name,
            'phone': intake.phone,
            'website_url': intake.website_url or '',
            'facebook_url': intake.facebook_url or '',
            'instagram_url': intake.instagram_url or '',
            'tiktok_url': intake.tiktok_url or '',
        }

        result = AutoSitePipelineService().run('\n'.join(lines), enrichment=enrichment)
        if not result or not result.html or len(result.html) < 500:
            intake.ai_status = 'failed'
            db.commit()
            logger.warning("[IntakePipeline] Pipeline returned no HTML for token=%s", token[:8])
            return

        # Save HTML preview to filesystem
        safe_slug = token[:16]
        html_file = PREVIEW_DIR / f'intake_{safe_slug}.html'
        html_file.write_text(result.html, encoding='utf-8')

        intake.generated_preview_url = f'/static/intake_previews/intake_{safe_slug}.html'
        intake.generated_html = result.html
        intake.ai_status = 'done'
        intake.status = 'in_review'
        db.commit()

        logger.info(
            "[IntakePipeline] Done for token=%s — preview=%s",
            token[:8], intake.generated_preview_url,
        )

        # Queue WhatsApp message for admin approval before sending to lead
        if result.outreach_message and intake.phone:
            demo_link = f"{settings.api_base_url}{intake.generated_preview_url}"
            message = result.outreach_message.replace('[DEMO_LINK]', demo_link)
            intake.whatsapp_pending_message = message
            intake.whatsapp_status = 'pending'
            db.commit()
            _notify_admin_approval(intake.token, intake.business_name, intake.phone, message)

    except Exception:
        logger.exception("[IntakePipeline] Unhandled error for token=%s", token[:8] if token else '?')
        if db:
            try:
                intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
                if intake:
                    intake.ai_status = 'failed'
                    db.commit()
            except Exception:
                pass
    finally:
        if db:
            db.close()


# ── POST /public/intake ─────────────────────────────────────────────────────
@router.post('/intake', response_model=IntakeSubmitResponse)
async def submit_intake(
    request: Request,
    background_tasks: BackgroundTasks,
    business_name: str = Form(..., max_length=255),
    phone: str = Form(..., max_length=32),
    facebook_url: str | None = Form(default=None),
    tiktok_url: str | None = Form(default=None),
    instagram_url: str | None = Form(default=None),
    website_url: str | None = Form(default=None),
    description: str | None = Form(default=None, max_length=1000),
    images: list[UploadFile] = File(default=[]),
    vip_token: str | None = Form(default=None),   # Google VIP token bypasses rate limits
    db: Session = Depends(get_db),
) -> IntakeSubmitResponse:
    # Basic validation
    if not phone.strip():
        raise HTTPException(status_code=400, detail='Phone number is required')
    if not business_name.strip():
        raise HTTPException(status_code=400, detail='Business name is required')

    # ── VIP bypass: Google-authenticated users skip rate limiting ────────────
    is_vip = False
    if vip_token:
        vip_payload = verify_vip_token(vip_token)
        if vip_payload:
            is_vip = True
            logger.info("[Intake] VIP submission from %s", vip_payload.get('email', 'unknown')[:30])

    if not is_vip:
        # ── Rate limiting: IP-based (3 per 24h) ────────────────────────────
        client_ip = (request.headers.get('X-Forwarded-For') or '').split(',')[0].strip() \
                    or (request.client.host if request.client else 'unknown')
        ip_allowed, ip_count, ip_max = _rate_svc.check_and_record(
            db,
            scope='public_intake',
            key=client_ip,
            action='submit',
            window_minutes=_DEMO_IP_WINDOW,
            max_per_window=_DEMO_IP_MAX,
            detail=f'ip={client_ip}',
        )
        if not ip_allowed:
            raise HTTPException(
                status_code=429,
                detail=f'הגעת למגבלת ההגשות ({ip_max} פניות ב-24 שעות). נסה שוב מחר.',
            )

        # ── Rate limiting: phone-based (2 per 30 days) ────────────────────
        phone_clean = re.sub(r'\D', '', phone.strip())
        phone_allowed, phone_count, phone_max = _rate_svc.check_and_record(
            db,
            scope='public_intake_phone',
            key=phone_clean,
            action='submit',
            window_minutes=_DEMO_PHONE_WINDOW,
            max_per_window=_DEMO_PHONE_MAX,
            detail=f'phone={phone_clean}',
        )
        if not phone_allowed:
            raise HTTPException(
                status_code=429,
                detail='מספר הטלפון הזה כבר הגיש בקשה. צור קשר ישירות אם יש בעיה.',
            )

    # Save uploaded images
    saved_filenames: list[str] = []
    for img in images[:5]:  # max 5 images
        if not img.filename:
            continue
        ext = Path(img.filename).suffix.lower()
        if ext not in ALLOWED_EXTS:
            continue
        content = await img.read()
        if len(content) > MAX_IMAGE_SIZE:
            continue
        safe_name = f'{uuid.uuid4().hex}{ext}'
        (UPLOAD_DIR / safe_name).write_bytes(content)
        saved_filenames.append(safe_name)

    token = secrets.token_urlsafe(32)
    intake = PublicIntake(
        token=token,
        business_name=business_name.strip(),
        phone=phone.strip(),
        facebook_url=_safe_url(facebook_url),
        tiktok_url=_safe_url(tiktok_url),
        instagram_url=_safe_url(instagram_url),
        website_url=_safe_url(website_url),
        description=(description or '').strip() or None,
        image_filenames=json.dumps(saved_filenames),
        status='submitted',
        correction_count=0,
    )
    db.add(intake)
    db.commit()
    db.refresh(intake)

    # ── Trigger AI pipeline in background ────────────────────────────────────
    # Runs the full 5-stage AutoSite pipeline asynchronously.
    # Result is saved to intake.generated_preview_url when done.
    intake.ai_status = 'pending'
    db.commit()
    background_tasks.add_task(_run_intake_pipeline, intake.token)

    return IntakeSubmitResponse(
        token=token,
        status='submitted',
        message='הבקשה שלך התקבלה! ניצור איתך קשר בקרוב.',
    )


# ── GET /public/intake/{token} ──────────────────────────────────────────────
@router.get('/intake/{token}', response_model=IntakeStatusResponse)
def intake_status(token: str, db: Session = Depends(get_db)) -> IntakeStatusResponse:
    intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
    if not intake:
        raise HTTPException(status_code=404, detail='Submission not found')
    return _build_status_response(intake)


# ── POST /public/intake/{token}/correction ──────────────────────────────────
@router.post('/intake/{token}/correction', response_model=IntakeStatusResponse)
def request_correction(
    token: str,
    note: str | None = None,
    db: Session = Depends(get_db),
) -> IntakeStatusResponse:
    intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
    if not intake:
        raise HTTPException(status_code=404, detail='Submission not found')
    if intake.status == 'cancelled':
        raise HTTPException(status_code=400, detail='Submission has been cancelled')
    if intake.correction_count >= MAX_CORRECTIONS:
        raise HTTPException(
            status_code=400,
            detail=f'Maximum {MAX_CORRECTIONS} correction requests allowed',
        )
    intake.correction_count += 1
    intake.status = 'revision_requested'
    if note:
        intake.admin_note = note[:500]
    db.commit()
    db.refresh(intake)
    return _build_status_response(intake)


# ── POST /public/intake/{token}/set-domain ────────────────────────────────
class SetDomainRequest(BaseModel):
    domain: str


@router.post('/intake/{token}/set-domain', response_model=IntakeStatusResponse)
def set_intake_domain(
    token: str,
    body: SetDomainRequest,
    db: Session = Depends(get_db),
) -> IntakeStatusResponse:
    """Store the desired domain the lead wants to register.

    Validates that the domain uses only .co.il or .com TLD and has
    reasonable syntax BEFORE the user pays — so they know immediately
    if their choice is invalid.
    """
    from app.services.hostinger_service import HostingerService

    intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
    if not intake:
        raise HTTPException(status_code=404, detail='Submission not found')
    if intake.payment_status == 'paid':
        raise HTTPException(status_code=400, detail='Payment already completed — cannot change domain')

    valid, error = HostingerService().validate_domain(body.domain.strip().lower())
    if not valid:
        raise HTTPException(status_code=422, detail=error)

    intake.desired_domain = body.domain.strip().lower()
    db.commit()
    db.refresh(intake)
    return _build_status_response(intake)


# ── POST /public/intake/{token}/checkout ────────────────────────────────────
@router.post('/intake/{token}/checkout')
def create_checkout(
    token: str,
    db: Session = Depends(get_db),
) -> dict:
    """Create a Morning payment link for 39 NIS/month subscription.

    Requires that the lead has already set their desired_domain via
    POST /set-domain.  Returns {payment_url: "..."}.
    """
    from app.services.morning_service import MorningService

    intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
    if not intake:
        raise HTTPException(status_code=404, detail='Submission not found')
    if intake.payment_status == 'paid':
        return {'payment_url': intake.site_live_url or settings.morning_success_url}
    if not intake.desired_domain:
        raise HTTPException(status_code=400, detail='יש לבחור שם דומיין לפני שממשיכים לתשלום')

    payment_url = MorningService().create_payment_link(
        intake_token=intake.token,
        business_name=intake.business_name,
        phone=intake.phone,
        domain=intake.desired_domain,
    )
    intake.payment_link = payment_url
    intake.payment_status = 'pending'
    db.commit()
    return {'payment_url': payment_url}


# ── DELETE /public/intake/{token} ───────────────────────────────────────────
@router.delete('/intake/{token}')
def cancel_intake(token: str, db: Session = Depends(get_db)) -> dict:
    intake = db.query(PublicIntake).filter(PublicIntake.token == token).first()
    if not intake:
        raise HTTPException(status_code=404, detail='Submission not found')
    if intake.status == 'cancelled':
        return {'ok': True, 'message': 'Already cancelled'}
    # Remove uploaded images
    try:
        images = json.loads(intake.image_filenames or '[]')
        for fn in images:
            p = UPLOAD_DIR / fn
            if p.exists():
                p.unlink()
    except Exception:
        pass
    intake.status = 'cancelled'
    db.commit()
    return {'ok': True, 'message': 'Submission cancelled'}
