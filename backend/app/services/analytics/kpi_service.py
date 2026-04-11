from sqlalchemy.orm import Session
from app.models.lead_record import LeadRecord
from app.models.business import Business
from app.models.draft_site import DraftSite
from app.models.payment_record import PaymentRecord
from app.models.approval_item import ApprovalItem


class KPIService:
    def snapshot(self, db: Session) -> dict:
        return {
            'leads': db.query(LeadRecord).count(),
            'qualified_leads': db.query(LeadRecord).filter(LeadRecord.status == 'qualified').count(),
            'businesses': db.query(Business).count(),
            'draft_sites': db.query(DraftSite).count(),
            'payments_confirmed': db.query(PaymentRecord).filter(PaymentRecord.internal_status == 'confirmed').count(),
            'approvals_pending': db.query(ApprovalItem).filter(ApprovalItem.status.in_(['proposed', 'under_review'])).count(),
        }
