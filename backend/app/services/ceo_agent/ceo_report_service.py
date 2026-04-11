
from sqlalchemy.orm import Session
from app.models.approval_item import ApprovalItem
from app.models.payment_record import PaymentRecord
from app.models.draft_site import DraftSite
from app.models.business import Business
from app.models.lead_record import LeadRecord
from app.models.activity_log import ActivityLog
from app.models.security_alert import SecurityAlert


class CEOReportService:
    def daily_digest(self, db: Session) -> dict:
        approvals_pending = db.query(ApprovalItem).filter(ApprovalItem.status.in_(['proposed','under_review'])).count()
        payments_pending = db.query(PaymentRecord).filter(PaymentRecord.internal_status.in_(['pending','awaiting_confirmation'])).count()
        expiring_drafts = db.query(DraftSite).filter(DraftSite.status.in_(['published_preview','pending_payment'])).count()
        outreach_ready = db.query(Business).filter(Business.status == 'outreach_ready').count()
        qualified_leads = db.query(LeadRecord).filter(LeadRecord.status == 'qualified').count()
        open_security_alerts = db.query(SecurityAlert).filter(SecurityAlert.status == 'open').count()
        high_security_alerts = db.query(SecurityAlert).filter(SecurityAlert.status == 'open', SecurityAlert.severity.in_(['high','critical'])).count()
        summary = 'Operational control room is stable. Prioritize outreach-ready businesses, approval items, payment confirmations, and review open security alerts.'
        actions = [
            'Open the outreach-ready queue and send the next batch of WhatsApp messages.',
            'Clear high-confidence approval items to unblock campaign and template improvements.',
            'Confirm pending payments and move ready businesses into activation.',
            'Review the security watchlist and open alerts before enabling more public login volume.',
        ]
        return {
            'executive_summary': summary,
            'recommended_actions': actions,
            'approval_queue_count': approvals_pending,
            'payments_pending': payments_pending,
            'expiring_drafts': expiring_drafts,
            'outreach_ready_count': outreach_ready,
            'qualified_leads': qualified_leads,
            'open_security_alerts': open_security_alerts,
            'high_security_alerts': high_security_alerts,
            'pressure_notes': [
                f'{approvals_pending} approvals pending',
                f'{payments_pending} payments pending',
                f'{outreach_ready} businesses ready for outreach',
                f'{open_security_alerts} open security alerts',
            ],
        }

    def add_note(self, db: Session, note: str) -> dict:
        db.add(ActivityLog(actor_type='admin', entity_type='ceo_console', entity_id=0, action_type='ceo_note_added', summary=note))
        db.commit()
        return {'status': 'ok', 'note': note}

    def create_task(self, db: Session, source: str, title: str, note: str | None = None) -> dict:
        summary = f'{source}: {title}' + (f' · {note}' if note else '')
        db.add(ActivityLog(actor_type='admin', entity_type='ceo_console', entity_id=0, action_type='ceo_task_created', summary=summary))
        db.commit()
        return {'status': 'ok', 'task_title': title, 'source': source}
