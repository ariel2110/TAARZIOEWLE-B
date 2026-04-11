from sqlalchemy.orm import Session
from app.models.business import Business
from app.models.customer_account import CustomerAccount
from app.models.customer_edit_submission import CustomerEditSubmission
from app.models.change_request import ChangeRequest
from app.models.support_message import SupportMessage
from app.models.activity_log import ActivityLog
from app.models.payment_record import PaymentRecord
from app.models.draft_site import DraftSite


class CustomerPortalService:
    SAFE_FIELDS = {'phone', 'email', 'contact_name'}

    def overview(self, db: Session, account: CustomerAccount):
        business = db.query(Business).filter(Business.id == account.business_id).first()
        payments = db.query(PaymentRecord).filter(PaymentRecord.business_id == account.business_id).order_by(PaymentRecord.id.desc()).limit(5).all()
        drafts = db.query(DraftSite).filter(DraftSite.business_id == account.business_id).order_by(DraftSite.id.desc()).limit(3).all()
        return {
            'account': {
                'customer_account_id': account.id,
                'phone': account.phone,
                'email': account.email,
                'contact_name': account.contact_name,
                'package_name': account.package_name,
                'must_change_password': account.must_change_password,
            },
            'business': {
                'id': business.id if business else None,
                'name': business.name if business else None,
                'status': business.status if business else None,
                'city': business.city if business else None,
                'category': business.category if business else None,
            },
            'sites': [{'id': d.id, 'title': d.site_title, 'status': d.status, 'preview_url': d.preview_url} for d in drafts],
            'recent_payments': [{'id': p.id, 'amount': p.amount, 'currency': p.currency, 'status': p.internal_status, 'payment_type': p.payment_type} for p in payments]
        }

    def submit_basic_edit(self, db: Session, account: CustomerAccount, field_key: str, new_value: str):
        if field_key not in self.SAFE_FIELDS:
            raise ValueError('Field not allowed for customer edit')
        old_value = getattr(account, field_key, None)
        submission = CustomerEditSubmission(customer_account_id=account.id, business_id=account.business_id, field_key=field_key, old_value=str(old_value) if old_value is not None else None, new_value=new_value)
        db.add(submission)
        db.add(ActivityLog(actor_type='customer', actor_id=account.id, business_id=account.business_id, action_type='customer_edit_submitted', action_payload_json={'field_key': field_key}))
        db.commit(); db.refresh(submission)
        return submission

    def list_edit_submissions(self, db: Session, account: CustomerAccount):
        return db.query(CustomerEditSubmission).filter(CustomerEditSubmission.customer_account_id == account.id).order_by(CustomerEditSubmission.id.desc()).all()

    def create_change_request(self, db: Session, account: CustomerAccount, request_type: str, title: str, description: str):
        item = ChangeRequest(customer_account_id=account.id, business_id=account.business_id, request_type=request_type, title=title, description=description)
        db.add(item)
        db.add(ActivityLog(actor_type='customer', actor_id=account.id, business_id=account.business_id, action_type='customer_change_request_created', action_payload_json={'title': title, 'request_type': request_type}))
        db.commit(); db.refresh(item)
        return item

    def list_change_requests(self, db: Session, account: CustomerAccount):
        return db.query(ChangeRequest).filter(ChangeRequest.customer_account_id == account.id).order_by(ChangeRequest.id.desc()).all()

    def create_support_message(self, db: Session, account: CustomerAccount, subject: str, message: str):
        item = SupportMessage(customer_account_id=account.id, business_id=account.business_id, subject=subject, message=message)
        db.add(item)
        db.add(ActivityLog(actor_type='customer', actor_id=account.id, business_id=account.business_id, action_type='customer_support_message_created', action_payload_json={'subject': subject}))
        db.commit(); db.refresh(item)
        return item

    def list_support_messages(self, db: Session, account: CustomerAccount):
        return db.query(SupportMessage).filter(SupportMessage.customer_account_id == account.id).order_by(SupportMessage.id.desc()).all()

    def timeline(self, db: Session, account: CustomerAccount):
        events = db.query(ActivityLog).filter(ActivityLog.business_id == account.business_id).order_by(ActivityLog.id.desc()).limit(50).all()
        return [{'id': e.id, 'action_type': e.action_type, 'actor_type': e.actor_type, 'created_at': str(getattr(e, 'created_at', '')), 'payload': e.action_payload_json} for e in events]
