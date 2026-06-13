
from fastapi import APIRouter, Body, Depends, Query, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.public_portal import (
    HomeContentResponse,
    IntakePreviewRequest,
    IntakePreviewResponse,
    PublicLoginOptionsResponse,
    DemoRequestAvailabilityResponse,
    PublicRequestDemoRequest,
    PublicRequestDemoResponse,
    DemoRequestStatusResponse,
    PublicStatusSummaryResponse,
    PackagePlanResponse,
    PublicRequestMagicLinkRequest,
    PublicRequestMagicLinkResponse,
    PublicRequestOtpRequest,
    PublicRequestOtpResponse,
    PublicVerifyOtpRequest,
    PublicVerifyOtpResponse,
    PublicConsumeMagicLinkResponse,
    DemoCompareResponse,
)
from app.services.public.public_portal_service import PublicPortalService

router = APIRouter(prefix='/public', tags=['public'])
service = PublicPortalService()

@router.get('/home-content', response_model=HomeContentResponse)
def home_content(db: Session = Depends(get_db)):
    return service.home_content(db)

@router.get('/login-options', response_model=PublicLoginOptionsResponse)
def login_options():
    return service.login_options()

@router.get('/packages', response_model=list[PackagePlanResponse])
def packages(db: Session = Depends(get_db)):
    return service.package_plans(db)

@router.get('/demo-availability', response_model=DemoRequestAvailabilityResponse)
def demo_availability(customer_phone: str | None = Query(default=None), package_name: str | None = Query(default=None), db: Session = Depends(get_db)):
    return service.demo_request_availability(db, customer_phone, package_name)

@router.post('/intake-preview', response_model=IntakePreviewResponse)
def intake_preview(payload: IntakePreviewRequest, db: Session = Depends(get_db)):
    return service.intake_preview(db, payload)

@router.post('/request-demo', response_model=PublicRequestDemoResponse)
def request_demo(payload: PublicRequestDemoRequest, db: Session = Depends(get_db)):
    try:
        return service.request_demo(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post('/request-magic-link', response_model=PublicRequestMagicLinkResponse)
def request_magic_link(payload: PublicRequestMagicLinkRequest, db: Session = Depends(get_db), x_forwarded_for: str | None = Header(default=None), x_session_key: str | None = Header(default=None)):
    try:
        return service.request_magic_link(db, payload.customer_phone, payload.business_name, x_forwarded_for, x_session_key)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get('/demo-status', response_model=DemoRequestStatusResponse)
def demo_status(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db)):
    return service.demo_request_status(db, customer_phone)

@router.get('/demo-status-summary', response_model=PublicStatusSummaryResponse)
def demo_status_summary(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db)):
    return service.demo_status_summary(db, customer_phone)

@router.get('/demo-compare', response_model=DemoCompareResponse)
def demo_compare(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db)):
    return service.demo_compare(db, customer_phone)


@router.post('/request-otp', response_model=PublicRequestOtpResponse)
def request_otp(payload: PublicRequestOtpRequest, db: Session = Depends(get_db), x_forwarded_for: str | None = Header(default=None), x_session_key: str | None = Header(default=None)):
    try:
        return service.request_otp(db, payload.customer_phone, payload.business_name, x_forwarded_for, x_session_key, payload.extension)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post('/verify-otp', response_model=PublicVerifyOtpResponse)
def verify_otp(payload: PublicVerifyOtpRequest, db: Session = Depends(get_db)):
    try:
        return service.verify_otp(db, payload.customer_phone, payload.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.post('/consume-magic-link', response_model=PublicConsumeMagicLinkResponse)
def consume_magic_link(token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    try:
        return service.consume_magic_link(db, token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# ── SMS OTP endpoints ─────────────────────────────────────────────────────────

class SmsOtpRequest(BaseModel):
    phone: str
    lang: str = "he"   # he / en / ar / ru

class SmsOtpVerifyRequest(BaseModel):
    phone: str
    code: str

@router.post('/sms-otp/send')
def send_sms_otp(payload: SmsOtpRequest, db: Session = Depends(get_db)):
    """Send a 4-digit OTP via SMS to the given phone number.
    The SMS body follows Web OTP API format for Android auto-fill.
    """
    import re as _re
    from app.services.auth.login_challenge_service import LoginChallengeService
    from app.services.auth.providers.twilio_sms_provider import TwilioSmsDeliveryProvider

    # Basic phone validation
    digits = _re.sub(r"\D", "", payload.phone)
    if len(digits) < 8:
        raise HTTPException(status_code=400, detail="מספר טלפון לא תקין")

    svc = LoginChallengeService()
    challenge = svc.create_otp(db, customer_phone=digits)

    result = TwilioSmsDeliveryProvider().deliver(
        to_phone=digits,
        code=challenge.code,
        lang=payload.lang,
    )

    if not result.ok:
        raise HTTPException(status_code=502, detail=f"שליחת SMS נכשלה: {result.error}")

    return {"ok": True, "phone": digits, "sid": result.external_reference}


@router.post('/sms-otp/verify')
def verify_sms_otp(payload: SmsOtpVerifyRequest, db: Session = Depends(get_db)):
    """Verify the 4-digit SMS OTP code."""
    import re as _re
    from app.services.auth.login_challenge_service import LoginChallengeService

    digits = _re.sub(r"\D", "", payload.phone)
    svc = LoginChallengeService()
    try:
        result = svc.verify_otp(db, customer_phone=digits, code=payload.code.strip())
        return {"ok": True, **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
