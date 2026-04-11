
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

        static_summary = 'Operational control room is stable. Prioritize outreach-ready businesses, approval items, payment confirmations, and review open security alerts.'
        static_actions = [
            'Open the outreach-ready queue and send the next batch of WhatsApp messages.',
            'Clear high-confidence approval items to unblock campaign and template improvements.',
            'Confirm pending payments and move ready businesses into activation.',
            'Review the security watchlist and open alerts before enabling more public login volume.',
        ]

        summary = self._llm_executive_summary(
            approvals_pending=approvals_pending,
            payments_pending=payments_pending,
            expiring_drafts=expiring_drafts,
            outreach_ready=outreach_ready,
            qualified_leads=qualified_leads,
            open_security_alerts=open_security_alerts,
            high_security_alerts=high_security_alerts,
        ) or static_summary

        return {
            'executive_summary': summary,
            'recommended_actions': static_actions,
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

    def _llm_executive_summary(self, **metrics: int) -> str | None:
        """Generate a dynamic CEO executive summary using LLM if a key is configured."""
        from app.core.config import settings
        if not settings.openai_api_key:
            return None
        try:
            from app.services.llm.router_service import LLMRouterService
            prompt = (
                "You are a senior business intelligence assistant for a local-business SaaS platform.\n"
                "Write a concise CEO executive summary (3-5 sentences, English) based on today's operational metrics:\n"
                f"- Approvals pending: {metrics.get('approvals_pending', 0)}\n"
                f"- Payments pending: {metrics.get('payments_pending', 0)}\n"
                f"- Expiring draft sites: {metrics.get('expiring_drafts', 0)}\n"
                f"- Businesses outreach-ready: {metrics.get('outreach_ready', 0)}\n"
                f"- Qualified leads: {metrics.get('qualified_leads', 0)}\n"
                f"- Open security alerts: {metrics.get('open_security_alerts', 0)}\n"
                f"- High/critical security alerts: {metrics.get('high_security_alerts', 0)}\n\n"
                "Focus on risks, opportunities, and the single most important action. No bullet points."
            )
            return LLMRouterService().call("generate_site_copy", prompt)
        except Exception:
            return None

    def add_note(self, db: Session, note: str) -> dict:
        db.add(ActivityLog(actor_type='admin', entity_type='ceo_console', entity_id=0, action_type='ceo_note_added', summary=note))
        db.commit()
        return {'status': 'ok', 'note': note}

    def create_task(self, db: Session, source: str, title: str, note: str | None = None) -> dict:
        summary = f'{source}: {title}' + (f' · {note}' if note else '')
        db.add(ActivityLog(actor_type='admin', entity_type='ceo_console', entity_id=0, action_type='ceo_task_created', summary=summary))
        db.commit()
        return {'status': 'ok', 'task_title': title, 'source': source}

