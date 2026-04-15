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
        understanding = f"הובן פידבק עבור {item.target_type}. סווג כ״{category}."
        response = f"פעולה מומלצת: {action}. היקף: {scope}."

        # Optional LLM enhancement for open feedback text
        if item.open_feedback and len(item.open_feedback.strip()) > 10:
            llm_result = self._llm_analyze_open_feedback(
                open_feedback=item.open_feedback,
                target_type=item.target_type,
                quick_rating=item.quick_rating,
                category=category,
                scope=scope,
                action=action,
            )
            if llm_result:
                understanding, response = llm_result
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
                title=f'מעקב פידבק עבור {item.target_type} #{item.target_id or item.id}',
                summary=response,
                status='proposed',
                approval_required=True,
                payload_json={'feedback_id': item.id, 'action_hint': action, 'scope': scope, 'category': category},
            )
            db.add(approval)
        db.commit()
        db.refresh(item)
        return item

    # ------------------------------------------------------------------

    def _llm_analyze_open_feedback(
        self,
        *,
        open_feedback: str,
        target_type: str,
        quick_rating: str,
        category: str,
        scope: str,
        action: str,
    ) -> tuple[str, str] | None:
        """Return (understanding, response) enriched by LLM, or None if unavailable."""
        from app.core.config import settings
        if not settings.openai_api_key:
            return None
        try:
            from app.services.llm.router_service import LLMRouterService
            prompt = (
                "אתה מנהל מוצר בכיר המנתח פידבק עבור פלטפורמת SaaS לעסקים מקומיים.\n"
                f"סוג פידבק: {target_type} | דירוג: {quick_rating}\n"
                f"ניתוח באזיסת כללים: קטגוריה={category}, היקף={scope}, פעולה={action}\n\n"
                f"הקונה כתב:\n\"\"\"\n{open_feedback}\n\"\"\"\n\n"
                "ענה בשני פסקאות קצרות מופרדות ב-|||:\n"
                "1. הבנה תמציתית — מה הקונה מתכוון (1-2 משפטים בעברית)\n"
                "2. תגובה מומלצת / תכנית פעולה (1-2 משפטים בעברית)\n\n"
                "ללא טקסט נוסף, רק שני הפסקאות מופרדות ב-|||."
            )
            raw = LLMRouterService().call_tracked("review_generated_copy", prompt, stage="feedback_analysis")
            if not raw or "|||" not in raw:
                return None
            parts = raw.split("|||", 1)
            return parts[0].strip(), parts[1].strip()
        except Exception:
            return None
