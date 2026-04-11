"""Admin user management — view and assign roles."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin, require_role
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix='/admin/users', tags=['admin-users'])

VALID_ROLES = ('viewer', 'analyst', 'admin', 'superadmin')


class SetRoleRequest(BaseModel):
    role: str


@router.get('')
def list_admin_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_role('admin')),
):
    """List all admin users with their roles."""
    users = db.query(User).order_by(User.id).all()
    return [{'id': u.id, 'email': u.email, 'full_name': u.full_name, 'role': u.role, 'is_active': u.is_active} for u in users]


@router.get('/me')
def current_user(user: User = Depends(get_current_admin)):
    """Return current admin user info including role."""
    return {'id': user.id, 'email': user.email, 'full_name': user.full_name, 'role': user.role, 'is_active': user.is_active}


@router.post('/{user_id}/set-role')
def set_user_role(
    user_id: int,
    payload: SetRoleRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_role('superadmin')),
):
    """Change a user's role. Only superadmins can do this."""
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f'Invalid role. Must be one of: {", ".join(VALID_ROLES)}')
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    user.role = payload.role
    db.commit()
    return {'id': user.id, 'email': user.email, 'role': user.role}
