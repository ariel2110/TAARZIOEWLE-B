from sqlalchemy.orm import Session
from app.models.feedback_item import FeedbackItem
from app.models.activity_log import ActivityLog
from app.models.approval_item import ApprovalItem


class FeedbackService:
    def list_items(self, db: Session, target_type: str | None = None, status: str | None = None) -> list[FeedbackItem]:
        q = db.query(FeedbackItem)
        if target_type:
            q = q.filter(FeedbackItem.target_type == target_type)
        if status:
            q = q.filter(FeedbackItem.feedback_status == status)
        return q.order_by(FeedbackItem.id.desc()).all()

    def create(self, db: Session, **kwargs) -> FeedbackItem:
        item = FeedbackItem(**kwargs)
        db.add(item)
        db.flush()
        db.add(ActivityLog(actor_type='admin', entity_type='feedback_item', entity_id=item.id, action_type='feedback_created', summary=f'{item.target_type}:{item.target_id}'))
        db.commit()
        db.refresh(item)
        return item

    def analyze(self, db: Session, feedback_id: int) -> FeedbackItem | None:
        item = db.query(FeedbackItem).filter(FeedbackItem.id == feedback_id).first()
        if not item:
            return None
        text = (item.open_feedback or '').lower()
        category = 'general_quality'
        scope = 'item_only'
        action = 'review_item'
        preference_candidate = False
        if item.target_type == 'draft_site':
            category = 'site_quality'
            action = 'improve_draft'
        if 'הודעה' in text or 'message' in text or item.target_type == 'outreach_message':
            category = 'outreach_message'
            action = 'revise_outreach_message'
        if 'תבנית' in text or 'template' in text:
            scope = 'template_level'
            action = 'create_template_improvement_candidate'
        if 'פעם הבאה' in text or 'מעתה' in text or 'always' in text:
            preference_candidate = True
            if scope == 'item_only':
                scope = 'system_level'
        if 'קטגור' in text:
            scope = 'category_level'
        if 'קמפיין' in text:
            scope = 'campaign_level'
        if item.quick_rating == 'not_a_fit' and scope == 'item_only':
            action = 'rebuild_or_major_change'
        understanding = f"Understood feedback for {item.target_type}. Classified as {category}."
        response = f"I understand this as a {category} issue. Suggested next action: {action}. Suggested scope: {scope}."
        item.analysis_category = category
        item.suggested_scope = scope
        item.action_hint = action
        item.preference_candidate = preference_candidate
        item.ceo_understanding = understanding
        item.ceo_response = response
        item.feedback_status = 'analyzed'
        db.add(ActivityLog(actor_type='system', entity_type='feedback_item', entity_id=item.id, action_type='feedback_analyzed', summary=f'{category} / {scope} / {action}'))
        if item.quick_rating in ('needs_improvement', 'not_a_fit'):
            approval = ApprovalItem(
                approval_type='feedback_followup',
                title=f'Feedback follow-up for {item.target_type} #{item.target_id or item.id}',
                summary=response,
                status='proposed',
                approval_required=True,
                payload_json={'feedback_id': item.id, 'action_hint': action, 'scope': scope, 'category': category},
            )
            db.add(approval)
        db.commit()
        db.refresh(item)
        return item
