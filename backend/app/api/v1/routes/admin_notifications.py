"""Admin notifications endpoint — returns recent system events for in-app alerts."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.services.common.notification_service import NotificationService

router = APIRouter(prefix='/admin/notifications', tags=['admin-notifications'])
_svc = NotificationService()


@router.get('')
def list_notifications(
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Recent admin notifications (demo viewed, payment confirmed, etc.)."""
    items = _svc.list_recent(db, limit=limit)
    return [
        {
            'id': n.id,
            'event': n.action_type,
            'entity_type': n.entity_type,
            'entity_id': n.entity_id,
            'summary': n.summary,
            'created_at': n.created_at.isoformat() if n.created_at else None,
        }
        for n in items
    ]
