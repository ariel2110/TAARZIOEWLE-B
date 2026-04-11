
from sqlalchemy.orm import Session
from app.models.lead_record import LeadRecord
from app.models.business import Business
from app.models.approval_item import ApprovalItem
from app.models.payment_record import PaymentRecord
from app.models.draft_site import DraftSite
from app.models.feedback_item import FeedbackItem

class QueueService:
    def summary(self, db: Session) -> list[dict]:
        return [
            {'queue_type': 'feedback_review', 'label': 'Feedback Review', 'count': db.query(FeedbackItem).filter(FeedbackItem.feedback_status.in_(['new','analyzed'])).count()},
            {'queue_type': 'lead_review', 'label': 'Lead Review', 'count': db.query(LeadRecord).filter(LeadRecord.status.in_(['imported','needs_review'])).count()},
            {'queue_type': 'outreach_ready', 'label': 'Outreach Ready', 'count': db.query(Business).filter(Business.status == 'outreach_ready').count()},
            {'queue_type': 'approvals', 'label': 'Approvals', 'count': db.query(ApprovalItem).filter(ApprovalItem.status.in_(['proposed','under_review'])).count()},
            {'queue_type': 'payments', 'label': 'Payments Pending', 'count': db.query(PaymentRecord).filter(PaymentRecord.internal_status.in_(['pending','awaiting_confirmation'])).count()},
            {'queue_type': 'expiring_drafts', 'label': 'Expiring Drafts', 'count': db.query(DraftSite).filter(DraftSite.status.in_(['published_preview','pending_payment'])).count()},
        ]

    def queue_items(self, db: Session, queue_type: str) -> list[dict]:
        if queue_type == 'lead_review':
            leads = db.query(LeadRecord).filter(LeadRecord.status.in_(['imported','needs_review'])).order_by(LeadRecord.score.desc(), LeadRecord.id.desc()).all()
            return [
                {'id': x.id, 'title': x.imported_name, 'subtitle': f"{x.city or '—'} · {x.category or '—'} · score {x.score}", 'priority': 'high' if x.score >= 70 else 'medium', 'queue_type': queue_type, 'linked_entity_type': 'lead', 'linked_entity_id': x.id, 'available_actions': ['qualify_lead','assign_campaign','convert_to_business']}
                for x in leads
            ]
        if queue_type == 'outreach_ready':
            items = db.query(Business).filter(Business.status == 'outreach_ready').order_by(Business.id.desc()).all()
            return [
                {'id': x.id, 'title': x.name, 'subtitle': f"{x.city or '—'} · {x.category or '—'}", 'priority': 'high', 'queue_type': queue_type, 'linked_entity_type': 'business', 'linked_entity_id': x.id, 'available_actions': ['build_whatsapp_message','mark_outreach_sent','assign_campaign']}
                for x in items
            ]
        if queue_type == 'approvals':
            items = db.query(ApprovalItem).filter(ApprovalItem.status.in_(['proposed','under_review'])).order_by(ApprovalItem.id.desc()).all()
            return [
                {'id': x.id, 'title': x.title, 'subtitle': f"{x.approval_type} · {x.status}", 'priority': 'high' if x.status == 'under_review' else 'medium', 'queue_type': queue_type, 'linked_entity_type': 'approval', 'linked_entity_id': x.id, 'available_actions': ['open_detail','approve','reject']}
                for x in items
            ]
        if queue_type == 'payments':
            items = db.query(PaymentRecord).filter(PaymentRecord.internal_status.in_(['pending','awaiting_confirmation'])).order_by(PaymentRecord.id.desc()).all()
            return [
                {'id': x.id, 'title': f"Payment #{x.id}", 'subtitle': f"{x.provider} · {x.internal_status} · amount {x.amount}", 'priority': 'high', 'queue_type': queue_type, 'linked_entity_type': 'payment', 'linked_entity_id': x.id, 'available_actions': ['confirm_payment','move_to_activation']}
                for x in items
            ]
        if queue_type == 'feedback_review':
            items = db.query(FeedbackItem).filter(FeedbackItem.feedback_status.in_(['new','analyzed'])).order_by(FeedbackItem.id.desc()).all()
            return [
                {'id': x.id, 'title': f"{x.target_type} feedback #{x.id}", 'subtitle': f"{x.quick_rating} · {x.analysis_category or 'new'}", 'priority': 'high' if x.quick_rating == 'not_a_fit' else 'medium', 'queue_type': queue_type, 'linked_entity_type': 'feedback_item', 'linked_entity_id': x.id, 'available_actions': ['analyze_feedback','create_approval_candidate']}
                for x in items
            ]
        if queue_type == 'expiring_drafts':
            items = db.query(DraftSite).filter(DraftSite.status.in_(['published_preview','pending_payment'])).order_by(DraftSite.id.desc()).all()
            return [
                {'id': x.id, 'title': x.site_title, 'subtitle': f"status {x.status} · business {x.business_id}", 'priority': 'medium', 'queue_type': queue_type, 'linked_entity_type': 'draft_site', 'linked_entity_id': x.id, 'available_actions': ['extend_review','mark_outreach_ready']}
                for x in items
            ]
        return []
