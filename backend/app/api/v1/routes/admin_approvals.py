
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.approval import ApprovalItemRead, ApprovalItemDetail
from app.services.approvals.approval_service import ApprovalService
from app.models.user import User

router = APIRouter(prefix='/admin/approvals', tags=['admin-approvals'])
service = ApprovalService()


@router.get('', response_model=list[ApprovalItemRead])
def list_approvals(status: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.list_items(db, status=status)


@router.get('/{item_id}', response_model=ApprovalItemDetail)
def approval_detail(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail='Approval item not found')
    return item


@router.post('/{item_id}/approve', response_model=ApprovalItemRead)
def approve_item(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.approve(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail='Approval item not found')
    return item


@router.post('/{item_id}/reject', response_model=ApprovalItemRead)
def reject_item(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.reject(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail='Approval item not found')
    return item


@router.post('/{item_id}/apply')
def apply_item(item_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail='Approval item not found')
    from app.services.approvals.approval_apply_service import ApprovalApplyService
    try:
        return ApprovalApplyService().apply(db, item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
