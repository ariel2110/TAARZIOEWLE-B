
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.business import Business
from app.models.approval_item import ApprovalItem
from app.services.common.status_transition_guard_service import StatusTransitionGuardService
from app.services.approvals.approval_apply_service import ApprovalApplyService

router = APIRouter(prefix='/admin/workflows', tags=['admin-workflows'])
guard = StatusTransitionGuardService()
apply_service = ApprovalApplyService()

@router.get('/business-transition-check')
def business_transition_check(current: str, target: str, _=Depends(get_current_admin)):
    ok, reason = guard.can_transition('business', current, target)
    return {'allowed': ok, 'reason': reason, 'current': current, 'target': target}

@router.post('/business/{business_id}/transition/{target}')
def business_transition(business_id: int, target: str, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail='Business not found')
    ok, reason = guard.can_transition('business', business.status, target)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)
    business.status = target
    db.commit(); db.refresh(business)
    return {'id': business.id, 'status': business.status}

@router.post('/approval/{item_id}/apply')
def approval_apply(item_id: int, db: Session = Depends(get_db), _=Depends(get_current_admin)):
    item = db.query(ApprovalItem).filter(ApprovalItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail='Approval item not found')
    try:
        return apply_service.apply(db, item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
