from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.models.customer_edit_submission import CustomerEditSubmission
from app.models.change_request import ChangeRequest
from app.models.support_message import SupportMessage

router = APIRouter(prefix='/admin/customer-ops', tags=['admin-customer-ops'])

@router.get('/edit-submissions')
def list_edit_submissions(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    rows = db.query(CustomerEditSubmission).order_by(CustomerEditSubmission.id.desc()).all()
    return [{'id': r.id, 'customer_account_id': r.customer_account_id, 'business_id': r.business_id, 'field_key': r.field_key, 'status': r.status, 'new_value': r.new_value} for r in rows]

@router.get('/change-requests')
def list_change_requests(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    rows = db.query(ChangeRequest).order_by(ChangeRequest.id.desc()).all()
    return [{'id': r.id, 'customer_account_id': r.customer_account_id, 'business_id': r.business_id, 'request_type': r.request_type, 'title': r.title, 'status': r.status, 'estimated_price': r.estimated_price} for r in rows]

@router.get('/support-messages')
def list_support_messages(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    rows = db.query(SupportMessage).order_by(SupportMessage.id.desc()).all()
    return [{'id': r.id, 'customer_account_id': r.customer_account_id, 'business_id': r.business_id, 'subject': r.subject, 'status': r.status} for r in rows]
