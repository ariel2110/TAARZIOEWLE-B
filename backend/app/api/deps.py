from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.config import settings
from app.core.security import decode_access_token
from app.core.odin_auth import _decode_odin_token
from app.services.auth.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def verify_portal_request(
    x_odin_origin: Optional[str] = Header(default=None),
    x_internal_key: Optional[str] = Header(default=None),
) -> None:
    """Verify the request arrived through the Odin/Traefik portal gateway.

    When INTERNAL_KEY is set in env, both X-Odin-Origin and X-Internal-Key
    must match. In development (key not set) the check is skipped.
    """
    if not settings.internal_key:
        return  # dev mode — skip
    if x_odin_origin != "true" or x_internal_key != settings.internal_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request must originate from the portal gateway",
        )


# Role hierarchy: higher index = more permissions
_ROLE_RANK: dict[str, int] = {
    'viewer': 0,
    'analyst': 1,
    'admin': 2,
    'superadmin': 3,
}


def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    x_admin_token: Optional[str] = Header(default=None),
    x_admin_email: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    # Preferred: bearer token auth skeleton
    if credentials and credentials.credentials:
        try:
            # Check Odin SSO first
            is_odin = False
            try:
                payload = _decode_odin_token(credentials.credentials)
                email = str(payload.get('sub', '')) + '@odin.local'
                role = 'admin' if str(payload.get('role', '')) in ('admin', 'merchant') else 'viewer'
                is_odin = True
            except Exception:
                pass
                
            if not is_odin:
                payload = decode_access_token(credentials.credentials)
                email = str(payload.get('sub', '')).strip()
                role = str(payload.get('role', '')).strip()

            if not email or role not in _ROLE_RANK:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid bearer token')
            user = AuthService().get_or_create_admin(db=db, email=email, full_name='Admin User')
            # Sync role from token
            if user.role != role:
                user.role = role
                db.commit()
            return user
        except JWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid bearer token') from exc

    if settings.environment.lower() == 'production':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing bearer token')

    # Legacy dev-header fallback
    if x_admin_token != settings.admin_dev_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing or invalid admin token')

    email = x_admin_email or settings.admin_seed_email
    if settings.allowed_admin_email_domain and not email.endswith(f"@{settings.allowed_admin_email_domain}"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin email domain not allowed')

    return AuthService().get_or_create_admin(db=db, email=email, full_name=settings.admin_seed_name)


def require_role(min_role: str):
    """Dependency factory: ensures the current admin has at least `min_role`."""
    min_rank = _ROLE_RANK.get(min_role, 0)

    def _dep(user: User = Depends(get_current_admin)) -> User:
        user_rank = _ROLE_RANK.get(user.role, 0)
        if user_rank < min_rank:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f'Requires role: {min_role}',
            )
        return user

    return _dep


from app.models.customer_account import CustomerAccount
from app.services.auth.customer_auth_service import CustomerAuthService

# Alias for routes that use require_admin instead of get_current_admin
require_admin = get_current_admin


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
