"""
Public intake form endpoint — serves sitenest.site landing page form.
Allows potential customers to submit their business info, social links, and images.
"""
import json
import os
import secrets
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.public_intake import PublicIntake

router = APIRouter(prefix='/public', tags=['public-intake'])

# Where uploaded images are stored (relative to backend root)
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'static_sites' / 'uploads' / 'intake'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
MAX_CORRECTIONS = 3


# ── Response schemas ────────────────────────────────────────────────────────
class IntakeSubmitResponse(BaseModel):
    token: str
    status: str
    message: str


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


# ── Helper ──────────────────────────────────────────────────────────────────
def _safe_url(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    if url and not url.startswith(('http://', 'https://')):
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
    )


# ── POST /public/intake ─────────────────────────────────────────────────────
@router.post('/intake', response_model=IntakeSubmitResponse)
async def submit_intake(
    business_name: str = Form(..., max_length=255),
    phone: str = Form(..., max_length=32),
    facebook_url: str | None = Form(default=None),
    tiktok_url: str | None = Form(default=None),
    instagram_url: str | None = Form(default=None),
    website_url: str | None = Form(default=None),
    description: str | None = Form(default=None, max_length=1000),
    images: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
) -> IntakeSubmitResponse:
    # Basic validation
    if not phone.strip():
        raise HTTPException(status_code=400, detail='Phone number is required')
    if not business_name.strip():
        raise HTTPException(status_code=400, detail='Business name is required')

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
