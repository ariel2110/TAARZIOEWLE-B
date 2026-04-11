from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import sqlalchemy as sa
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.models.outreach_message import OutreachMessage
from app.services.analytics.kpi_service import KPIService

router = APIRouter(prefix='/admin/analytics', tags=['admin-analytics'])
service = KPIService()


@router.get('/snapshot')
def snapshot(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.snapshot(db)


@router.get('/ab-results')
def ab_results(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    """A/B test results — reply and delivery rates per variant."""
    rows = (
        db.query(
            OutreachMessage.ab_variant,
            func.count(OutreachMessage.id).label('total'),
            func.sum((OutreachMessage.status == 'sent').cast(sa.Integer)).label('sent'),
            func.sum((OutreachMessage.status == 'delivered').cast(sa.Integer)).label('delivered'),
            func.sum((OutreachMessage.status == 'read').cast(sa.Integer)).label('read'),
            func.sum((OutreachMessage.status == 'replied').cast(sa.Integer)).label('replied'),
        )
        .group_by(OutreachMessage.ab_variant)
        .all()
    )
    results = []
    for row in rows:
        total = row.total or 1
        results.append({
            'variant': row.ab_variant or 'control',
            'total': row.total,
            'sent': row.sent or 0,
            'delivered': row.delivered or 0,
            'read': row.read or 0,
            'replied': row.replied or 0,
            'reply_rate': round((row.replied or 0) / total * 100, 1),
            'read_rate': round((row.read or 0) / total * 100, 1),
        })
    return results

