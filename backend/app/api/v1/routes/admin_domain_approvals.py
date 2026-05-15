from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.models.public_intake import PublicIntake

router = APIRouter(prefix='/admin/domain-approvals', tags=['admin-domain-approvals'])


class DomainApprovalItem(BaseModel):
    intake_id: int
    business_name: str
    phone: str
    domain: str
    price_usd: Optional[float] = None
    approval_status: Optional[str] = None
    payment_status: str
    token_prefix: str

    class Config:
        from_attributes = True


def _to_item(intake: PublicIntake) -> DomainApprovalItem:
    # Derive approval_status from payment_status + domain
    if intake.desired_domain and intake.payment_status == 'paid':
        approval_status = 'pending_admin'
    elif intake.desired_domain and intake.payment_status in ('pending', 'unpaid'):
        approval_status = 'awaiting_payment'
    else:
        approval_status = None
    return DomainApprovalItem(
        intake_id=intake.id,
        business_name=intake.business_name,
        phone=intake.phone,
        domain=intake.desired_domain or '',
        price_usd=None,
        approval_status=approval_status,
        payment_status=intake.payment_status,
        token_prefix=intake.token[:8] if intake.token else '',
    )


@router.get('', response_model=list[DomainApprovalItem])
def list_domain_approvals(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    intakes = (
        db.query(PublicIntake)
        .filter(PublicIntake.desired_domain.isnot(None), PublicIntake.desired_domain != '')
        .order_by(PublicIntake.created_at.desc())
        .limit(200)
        .all()
    )
    return [_to_item(i) for i in intakes]


@router.post('/{intake_id}/approve')
def approve_domain(intake_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    intake = db.query(PublicIntake).filter(PublicIntake.id == intake_id).first()
    if not intake:
        raise HTTPException(status_code=404, detail='Intake not found')
    intake.payment_status = 'paid'
    intake.admin_note = (intake.admin_note or '') + '\n[domain approved]'
    db.commit()
    return {'status': 'approved', 'message': f'Domain {intake.desired_domain} approved'}


@router.post('/{intake_id}/reject')
def reject_domain(intake_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    intake = db.query(PublicIntake).filter(PublicIntake.id == intake_id).first()
    if not intake:
        raise HTTPException(status_code=404, detail='Intake not found')
    intake.payment_status = 'failed'
    intake.admin_note = (intake.admin_note or '') + '\n[domain rejected]'
    db.commit()
    return {'status': 'rejected', 'message': f'Domain {intake.desired_domain} rejected'}
