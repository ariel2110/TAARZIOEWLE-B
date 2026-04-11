
import random

from sqlalchemy.orm import Session
from app.models.business import Business
from app.models.draft_site import DraftSite
from app.models.outreach_message import OutreachMessage
from app.models.activity_log import ActivityLog


class OutreachService:

    @staticmethod
    def pick_variant(
        control_message: str,
        test_message: str,
        *,
        campaign_id: str | None = None,
        split_pct: int = 20,
    ) -> tuple[str, str, str]:
        """
        Traffic-split helper.  Returns (variant_name, message_to_send, campaign_id).

        split_pct % of calls receive the test variant ('variant_b');
        the rest receive the control variant ('control').

        Example:
            variant, msg, cid = OutreachService.pick_variant(
                control_message='שלום הכנו עבורך...',
                test_message='רגע, תראה מה הכנו לך!...',
                campaign_id='apr_2026_aggressive',
                split_pct=20,
            )
        """
        campaign_id = campaign_id or 'default'
        if random.randint(1, 100) <= split_pct:
            return 'variant_b', test_message, campaign_id
        return 'control', control_message, campaign_id

    def build_business_message(
        self,
        db: Session,
        business_id: int,
        draft_site_id: int | None = None,
        message_template_key: str = 'initial_outreach_v1',
        *,
        ab_variant: str | None = None,
        ab_campaign_id: str | None = None,
    ) -> OutreachMessage | None:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return None
        draft = None
        if draft_site_id:
            draft = db.query(DraftSite).filter(DraftSite.id == draft_site_id).first()
        elif business_id:
            draft = db.query(DraftSite).filter(DraftSite.business_id == business_id).order_by(DraftSite.id.desc()).first()
        preview = draft.preview_url if draft and draft.preview_url else 'preview link pending'
        city = business.city or 'your city'
        category = business.category or 'local business'
        message = (
            f"שלום, הכנו עבורך עמוד הדגמה זמני לעסק שלך בתחום {category} באזור {city}. "
            f"אפשר לצפות כאן: {preview}. אם זה מעניין אותך, אפשר להפעיל את האתר ולעשות התאמות. "
            f"אם לא רלוונטי, אפשר לבקש מחיקה מיידית."
        )
        item = OutreachMessage(
            business_id=business.id,
            draft_site_id=draft.id if draft else None,
            channel='whatsapp',
            status='draft',
            message_template_key=message_template_key,
            content=message,
            outbound_target=business.phone,
            city_context=business.city,
            category_context=business.category,
            ab_variant=ab_variant,
            ab_campaign_id=ab_campaign_id,
        )
        db.add(item)
        db.flush()
        db.add(ActivityLog(actor_type='system', entity_type='outreach_message', entity_id=item.id, action_type='outreach_message_created', summary=f'business_id={business.id}'))
        db.commit(); db.refresh(item)
        return item

    def mark_sent(self, db: Session, outreach_id: int, status: str = 'sent') -> OutreachMessage | None:
        item = db.query(OutreachMessage).filter(OutreachMessage.id == outreach_id).first()
        if not item:
            return None
        item.status = status
        if item.business_id:
            business = db.query(Business).filter(Business.id == item.business_id).first()
            if business:
                business.status = 'contacted'
        db.add(ActivityLog(actor_type='admin', entity_type='outreach_message', entity_id=item.id, action_type='outreach_marked_sent', summary=status))
        db.commit(); db.refresh(item)
        return item

    def reschedule_followup(self, db: Session, outreach_id: int, note: str | None = None) -> OutreachMessage | None:
        item = db.query(OutreachMessage).filter(OutreachMessage.id == outreach_id).first()
        if not item:
            return None
        item.status = 'followup_due'
        db.add(ActivityLog(actor_type='admin', entity_type='outreach_message', entity_id=item.id, action_type='outreach_followup_rescheduled', summary=note or 'followup_due'))
        db.commit(); db.refresh(item)
        return item
