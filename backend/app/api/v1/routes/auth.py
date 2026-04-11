from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.auth import CurrentAdminResponse, GoogleAuthStartResponse, DevLoginRequest, DevLoginResponse, GoogleVerifyRequest, GoogleVerifyResponse
from app.services.auth.google_oauth_service import GoogleOAuthService
from app.services.auth.auth_service import AuthService
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix='/auth', tags=['auth'])
auth_service = AuthService()


@router.get('/me', response_model=CurrentAdminResponse)
def me(current_admin: User = Depends(get_current_admin)) -> CurrentAdminResponse:
    return CurrentAdminResponse(
        email=current_admin.email,
        full_name=current_admin.full_name,
        role=current_admin.role,
        auth_mode='bearer-jwt',
    )


@router.post('/dev-login', response_model=DevLoginResponse)
def dev_login(payload: DevLoginRequest, db: Session = Depends(get_db)) -> DevLoginResponse:
    if settings.environment.lower() == 'production':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Not found')
    if payload.admin_token != settings.admin_dev_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid admin token')
    user = auth_service.get_or_create_admin(db=db, email=payload.email, full_name=payload.full_name or 'Admin User')
    token = auth_service.create_admin_access_token(user.email)
    return DevLoginResponse(access_token=token, email=user.email, role=user.role)


@router.get('/google/start', response_model=GoogleAuthStartResponse)
def google_start() -> GoogleAuthStartResponse:
    data = GoogleOAuthService().build_auth_url()
    return GoogleAuthStartResponse(**data)


@router.post('/google/verify', response_model=GoogleVerifyResponse)
def google_verify(payload: GoogleVerifyRequest, db: Session = Depends(get_db)) -> GoogleVerifyResponse:
    """Verify a Google ID token from the frontend and return a JWT."""
    if not settings.google_client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Google login is not configured on this server')
    try:
        info = GoogleOAuthService().verify_id_token(payload.id_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid Google token')

    email: str = info['email']
    allowed = [e.strip().lower() for e in settings.allowed_admin_emails.split(',') if e.strip()]
    if allowed and email.lower() not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Email not authorized for admin access')

    user = auth_service.get_or_create_admin(db=db, email=email, full_name=info['full_name'])
    token = auth_service.create_admin_access_token(user.email)
    return GoogleVerifyResponse(access_token=token, email=user.email, full_name=user.full_name, role=user.role)
