
from sqlalchemy.orm import Session
from sqlalchemy import func
import sqlalchemy as sa
from app.models.approval_item import ApprovalItem
from app.models.payment_record import PaymentRecord
from app.models.draft_site import DraftSite
from app.models.business import Business
from app.models.lead_record import LeadRecord
from app.models.activity_log import ActivityLog
from app.models.security_alert import SecurityAlert
from app.models.outreach_message import OutreachMessage


class CEOReportService:
    def daily_digest(self, db: Session) -> dict:
        approvals_pending = db.query(ApprovalItem).filter(ApprovalItem.status.in_(['proposed','under_review'])).count()
        payments_pending = db.query(PaymentRecord).filter(PaymentRecord.internal_status.in_(['pending','awaiting_confirmation'])).count()
        expiring_drafts = db.query(DraftSite).filter(DraftSite.status.in_(['published_preview','pending_payment'])).count()
        outreach_ready = db.query(Business).filter(Business.status == 'outreach_ready').count()
        qualified_leads = db.query(LeadRecord).filter(LeadRecord.status == 'qualified').count()
        open_security_alerts = db.query(SecurityAlert).filter(SecurityAlert.status == 'open').count()
        high_security_alerts = db.query(SecurityAlert).filter(SecurityAlert.status == 'open', SecurityAlert.severity.in_(['high','critical'])).count()

        # ── A/B campaign performance (last active campaign) ────────────────
        ab_rows = (
            db.query(
                OutreachMessage.ab_variant,
                OutreachMessage.ab_campaign_id,
                func.count(OutreachMessage.id).label('total'),
                func.sum(OutreachMessage.has_replied.cast(sa.Integer)).label('replied'),
            )
            .filter(OutreachMessage.ab_variant.is_not(None))
            .group_by(OutreachMessage.ab_variant, OutreachMessage.ab_campaign_id)
            .order_by(OutreachMessage.ab_campaign_id.desc())
            .limit(10)
            .all()
        )
        ab_stats: list[dict] = []
        for row in ab_rows:
            total = row.total or 1
            ab_stats.append({
                'variant': row.ab_variant or 'control',
                'campaign': row.ab_campaign_id or 'default',
                'total': row.total,
                'replied': row.replied or 0,
                'reply_rate_pct': round((row.replied or 0) / total * 100, 1),
            })

        static_summary = 'חדר הבקרה התפעולי יציב. יש לתעדף עסקים מוכנים לפנייה, פריטי אישור, אישורי תשלום ובדיקת התראות אבטחה פתוחות.'
        static_actions = [
            'פתח את תור הפנייה המוכנה ושלח את האצווה הבאה של הודעות וואטסאפ.',
            'טפל בפריטי אישור בעלי ביטחון גבוה כדי לשחרר שיפורי קמפיין ותבנית.',
            'אשר תשלומים ממתינים והעבר עסקים מוכנים להפעלה.',
            'עיין ברשימת החשד ובהתראות הפתוחות לפני הרחבת נפח הכניסה הציבורית.',
        ]

        summary = self._llm_executive_summary(
            approvals_pending=approvals_pending,
            payments_pending=payments_pending,
            expiring_drafts=expiring_drafts,
            outreach_ready=outreach_ready,
            qualified_leads=qualified_leads,
            open_security_alerts=open_security_alerts,
            high_security_alerts=high_security_alerts,
            ab_stats=ab_stats,
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
            'ab_stats': ab_stats,
            'pressure_notes': [
                f'{approvals_pending} אישורים ממתינים',
                f'{payments_pending} תשלומים ממתינים',
                f'{outreach_ready} עסקים מוכנים לפנייה',
                f'{open_security_alerts} התראות אבטחה פתוחות',
            ],
        }

    def _llm_executive_summary(self, **metrics) -> str | None:
        """Generate a dynamic CEO executive summary using LLM if a key is configured."""
        from app.core.config import settings
        if not settings.openai_api_key:
            return None
        try:
            from app.services.llm.router_service import LLMRouterService
            ab_stats: list[dict] = metrics.pop('ab_stats', [])
            ab_section = ''
            if ab_stats:
                lines = ['\nA/B Campaign Performance (latest):']
                for row in ab_stats:
                    lines.append(
                        f"  Campaign '{row['campaign']}' variant '{row['variant']}': "
                        f"{row['replied']}/{row['total']} replies ({row['reply_rate_pct']}%)"
                    )
                ab_section = '\n'.join(lines)
            prompt = (
                "אתה עוזר בכיר לבינה עסקית בפלטפורמת SaaS לעסקים מקומיים.\n"
                "כתוב תקציר מנהלים תמציתי (3-5 משפטים, בעברית) המבוסס על המדדים התפעוליים של היום:\n"
                f"- Approvals pending: {metrics.get('approvals_pending', 0)}\n"
                f"- Payments pending: {metrics.get('payments_pending', 0)}\n"
                f"- Expiring draft sites: {metrics.get('expiring_drafts', 0)}\n"
                f"- Businesses outreach-ready: {metrics.get('outreach_ready', 0)}\n"
                f"- Qualified leads: {metrics.get('qualified_leads', 0)}\n"
                f"- Open security alerts: {metrics.get('open_security_alerts', 0)}\n"
                f"- High/critical security alerts: {metrics.get('high_security_alerts', 0)}\n"
                f"{ab_section}\n\n"
                "בנוסף לתקציר, אם יש נתוני A/B — נתח אילו גרסאות מביאות יותר תגובות. "
                "המלץ בשורה אחת אם כדאי לשנות את הקמפיין הנוכחי (Pivot) או להמשיך לאחוז בו. "
                "התמקד בסיכונים, הזדמנויות והפעולה החשובה ביותר. ללא נקודות תבליט."
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

