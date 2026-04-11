from fastapi import APIRouter, Depends, Query
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
def ab_results(
    campaign_id: str | None = Query(default=None, description='Filter by ab_campaign_id'),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    A/B test results — reply and delivery rates per variant.

    Groups by ab_variant + ab_campaign_id and counts:
    - total sends, sent, delivered, read
    - has_replied (authoritative conversion event from webhook)
    - reply_rate and read_rate as percentages

    Optional ?campaign_id=xxx to narrow to one experiment.
    """
    q = db.query(
        OutreachMessage.ab_variant,
        OutreachMessage.ab_campaign_id,
        func.count(OutreachMessage.id).label('total'),
        func.sum((OutreachMessage.status.in_(['sent', 'delivered', 'read', 'replied'])).cast(sa.Integer)).label('sent'),
        func.sum((OutreachMessage.status.in_(['delivered', 'read', 'replied'])).cast(sa.Integer)).label('delivered'),
        func.sum((OutreachMessage.status.in_(['read', 'replied'])).cast(sa.Integer)).label('read'),
        func.sum(OutreachMessage.has_replied.cast(sa.Integer)).label('replied'),
    )

    if campaign_id:
        q = q.filter(OutreachMessage.ab_campaign_id == campaign_id)

    rows = q.group_by(OutreachMessage.ab_variant, OutreachMessage.ab_campaign_id).all()

    results = []
    for row in rows:
        total = row.total or 1
        results.append({
            'variant': row.ab_variant or 'control',
            'campaign_id': row.ab_campaign_id or 'default',
            'total': row.total,
            'sent': row.sent or 0,
            'delivered': row.delivered or 0,
            'read': row.read or 0,
            'replied': row.replied or 0,
            'reply_rate': round((row.replied or 0) / total * 100, 1),
            'read_rate': round((row.read or 0) / total * 100, 1),
        })
    return results

