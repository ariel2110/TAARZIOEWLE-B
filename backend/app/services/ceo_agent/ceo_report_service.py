
from datetime import datetime, timezone
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
from app.models.customer_account import CustomerAccount


class CEOReportService:
    def daily_digest(self, db: Session) -> dict:
        now_he = datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M')

        approvals_pending = db.query(ApprovalItem).filter(ApprovalItem.status.in_(['proposed','under_review'])).count()
        payments_pending = db.query(PaymentRecord).filter(PaymentRecord.internal_status.in_(['pending','awaiting_confirmation'])).count()
        payments_confirmed = db.query(PaymentRecord).filter(PaymentRecord.internal_status == 'confirmed').count()
        expiring_drafts = db.query(DraftSite).filter(DraftSite.status.in_(['published_preview','pending_payment'])).count()
        total_drafts = db.query(DraftSite).count()
        outreach_ready = db.query(Business).filter(Business.status == 'outreach_ready').count()
        qualified_leads = db.query(LeadRecord).filter(LeadRecord.status == 'qualified').count()
        total_leads = db.query(LeadRecord).count()
        total_businesses = db.query(Business).count()
        draft_created = db.query(Business).filter(Business.status == 'draft_created').count()
        open_security_alerts = db.query(SecurityAlert).filter(SecurityAlert.status == 'open').count()
        high_security_alerts = db.query(SecurityAlert).filter(SecurityAlert.status == 'open', SecurityAlert.severity.in_(['high','critical'])).count()
        total_customers = db.query(CustomerAccount).count()
        active_customers = db.query(CustomerAccount).filter(CustomerAccount.is_active == True).count()

        # ── A/B campaign performance ────────────────
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

        # ── Recent activity log with timestamps ──────
        recent_activity = (
            db.query(ActivityLog)
            .filter(ActivityLog.action_type.in_([
                'approval_applied', 'pipeline_config_applied', 'ab_test_launched',
                'lead_boiling_hot', 'payment_confirmed', 'ceo_task_created',
                'approval_approved', 'draft_site_created', 'draft_site_regenerated',
                'customer_created', 'site_generated',
            ]))
            .order_by(ActivityLog.id.desc())
            .limit(8)
            .all()
        )
        _action_labels = {
            'approval_applied': 'אושר ובוצע',
            'pipeline_config_applied': 'הגדרה הופעלה',
            'ab_test_launched': 'A/B הושק',
            'lead_boiling_hot': 'ליד חם זוהה',
            'payment_confirmed': 'תשלום אושר',
            'ceo_task_created': 'משימה נוצרה',
            'approval_approved': 'אושר',
            'draft_site_created': 'אתר טיוטה נוצר',
            'draft_site_regenerated': 'אתר נוצר מחדש',
            'customer_created': 'לקוח נרשם',
            'site_generated': 'אתר נוצר',
        }
        recent_fixes = [
            {
                'label': _action_labels.get(a.action_type, a.action_type),
                'summary': (a.summary or '')[:80],
                'timestamp': a.created_at.strftime('%d/%m %H:%M') if hasattr(a, 'created_at') and a.created_at else '',
            }
            for a in recent_activity
        ]

        # ── What's missing / needed ──────────────────
        what_needed = []
        if outreach_ready > 0:
            what_needed.append(f'📤 {outreach_ready} עסקים מוכנים לפנייה — יש לשלוח WhatsApp')
        if approvals_pending > 0:
            what_needed.append(f'⏳ {approvals_pending} אישורים ממתינים לאישורך')
        if payments_pending > 0:
            what_needed.append(f'💳 {payments_pending} תשלומים ממתינים לאימות')
        if open_security_alerts > 0:
            what_needed.append(f'🚨 {open_security_alerts} התראות אבטחה פתוחות{" (כולל HIGH/CRITICAL)" if high_security_alerts > 0 else ""}')
        if total_customers == 0 and total_businesses > 0:
            what_needed.append(f'👥 אין לקוחות רשומים — לחץ "סנכרן לקוחות מדמו" בדף לקוחות')

        static_summary = (
            f'📊 דו"ח מנהלים — {now_he}\n\n'
            f'המערכת פעילה. יש {total_businesses} עסקים ({draft_created} עם דמו), '
            f'{total_leads} לידים ({qualified_leads} מוסמכים), '
            f'{total_customers} לקוחות רשומים ({active_customers} פעילים). '
            f'{expiring_drafts} אתרי דמו ממתינים להמרה. '
        )
        if what_needed:
            static_summary += 'פעולות נדרשות: ' + '; '.join(what_needed[:3])

        static_actions = [
            'פתח את תור הפנייה המוכנה ושלח את האצווה הבאה של הודעות וואטסאפ.',
            'טפל בפריטי אישור בעלי ביטחון גבוה כדי לשחרר שיפורי קמפיין ותבנית.',
            'אשר תשלומים ממתינים והעבר עסקים מוכנים להפעלה.',
            'עיין ברשימת החשד ובהתראות הפתוחות לפני הרחבת נפח הכניסה הציבורית.',
            'לחץ "סנכרן לקוחות מדמו" כדי לרשום אוטומטית עסקים עם אתרי דמו.',
        ]

        summary = self._llm_executive_summary(
            approvals_pending=approvals_pending,
            payments_pending=payments_pending,
            expiring_drafts=expiring_drafts,
            outreach_ready=outreach_ready,
            qualified_leads=qualified_leads,
            open_security_alerts=open_security_alerts,
            high_security_alerts=high_security_alerts,
            total_businesses=total_businesses,
            total_customers=total_customers,
            payments_confirmed=payments_confirmed,
            ab_stats=ab_stats,
        ) or static_summary

        return {
            'executive_summary': summary,
            'recommended_actions': static_actions,
            'what_needed': what_needed,
            'approval_queue_count': approvals_pending,
            'payments_pending': payments_pending,
            'payments_confirmed': payments_confirmed,
            'expiring_drafts': expiring_drafts,
            'total_drafts': total_drafts,
            'outreach_ready_count': outreach_ready,
            'qualified_leads': qualified_leads,
            'total_leads': total_leads,
            'total_businesses': total_businesses,
            'draft_created_businesses': draft_created,
            'total_customers': total_customers,
            'active_customers': active_customers,
            'open_security_alerts': open_security_alerts,
            'high_security_alerts': high_security_alerts,
            'ab_stats': ab_stats,
            'recent_fixes': recent_fixes,
            'generated_at': now_he,
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
                f"- Payments confirmed: {metrics.get('payments_confirmed', 0)}\n"
                f"- Expiring draft sites: {metrics.get('expiring_drafts', 0)}\n"
                f"- Businesses outreach-ready: {metrics.get('outreach_ready', 0)}\n"
                f"- Total businesses: {metrics.get('total_businesses', 0)}\n"
                f"- Total customers: {metrics.get('total_customers', 0)}\n"
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
