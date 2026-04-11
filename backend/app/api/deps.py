from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.config import settings
from app.core.security import decode_access_token
from app.services.auth.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_admin_token: Optional[str] = Header(default=None),
    x_admin_email: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    # Preferred: bearer token auth skeleton
    if credentials and credentials.credentials:
        try:
            payload = decode_access_token(credentials.credentials)
            email = str(payload.get('sub', '')).strip()
            role = str(payload.get('role', '')).strip()
            if not email or role != 'admin':
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid bearer token')
            return AuthService().get_or_create_admin(db=db, email=email, full_name='Admin User')
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid bearer token') from exc

    # Legacy dev-header fallback
    if x_admin_token != settings.admin_dev_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing or invalid admin token')

    email = x_admin_email or settings.admin_seed_email
    if settings.allowed_admin_email_domain and not email.endswith(f"@{settings.allowed_admin_email_domain}"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin email domain not allowed')

    return AuthService().get_or_create_admin(db=db, email=email, full_name=settings.admin_seed_name)


from app.models.customer_account import CustomerAccount
from app.services.auth.customer_auth_service import CustomerAuthService


def get_current_customer(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> CustomerAccount:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing customer bearer token')
    try:
        payload = decode_access_token(credentials.credentials)
        sub = str(payload.get('sub', '')).strip()
        role = str(payload.get('role', '')).strip()
        if role != 'customer' or not sub.startswith('customer:'):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid customer token')
        customer_id = int(sub.split(':', 1)[1])
        account = CustomerAuthService().get_customer_by_id(db=db, customer_id=customer_id)
        if not account or not account.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Customer not found or inactive')
        return account
    except (JWTError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid customer token') from exc
