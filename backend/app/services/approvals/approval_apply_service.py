
from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog
from app.models.approval_item import ApprovalItem
from app.services.common.status_transition_guard_service import StatusTransitionGuardService


class ApprovalApplyService:
    def __init__(self) -> None:
        self.guard = StatusTransitionGuardService()

    def apply(self, db: Session, item: ApprovalItem) -> dict:
        ok, reason = self.guard.can_transition('approval', item.status, 'applied')
        if not ok:
            raise ValueError(reason)

        execution = self._dispatch(db, item)

        item.status = 'applied'
        db.add(ActivityLog(
            actor_type='admin',
            entity_type='approval_item',
            entity_id=item.id,
            action_type='approval_applied',
            summary=item.title,
        ))
        db.commit()
        db.refresh(item)
        return {'id': item.id, 'status': item.status, 'applied': True, 'execution': execution}

    # ── Dispatcher ────────────────────────────────────────────────────────────

    def _dispatch(self, db: Session, item: ApprovalItem) -> dict:
        """Route to the correct executor based on payload_json.action_type."""
        payload: dict = item.payload_json or {}
        action_type = (payload.get('action_type') or '').strip().upper()

        if not action_type or action_type == 'NONE':
            return {'status': 'acknowledged', 'message': 'אין פעולה לביצוע — הפריט מסומן כבוצע.'}

        from app.services.ceo_agent.ceo_grok_service import CEOGrokService
        grok = CEOGrokService()

        if action_type == 'UPDATE_CLAUDE_PROMPT':
            return grok._execute_update_claude_prompt(payload.get('new_value', ''))

        if action_type == 'UPDATE_PIPELINE_CONFIG':
            return self._apply_pipeline_config(db, item, payload)

        if action_type == 'A_B_TEST_WHATSAPP_MSG':
            return self._apply_ab_test(db, item, payload)

        # Unknown / manual action — log and acknowledge
        db.add(ActivityLog(
            actor_type='admin',
            entity_type='approval_item',
            entity_id=item.id,
            action_type='approval_manual_required',
            summary=f'יישום ידני נדרש: {action_type} — {item.title}',
        ))
        return {
            'status': 'acknowledged',
            'message': f'✅ הפעולה "{action_type}" אושרה. יש לבצע יישום ידני בקוד לפי ההצעה.',
        }

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _apply_pipeline_config(self, db: Session, item: ApprovalItem, payload: dict) -> dict:
        target = payload.get('target_component') or 'general'
        new_value = payload.get('new_value') or ''
        db.add(ActivityLog(
            actor_type='admin',
            entity_type='approval_item',
            entity_id=item.id,
            action_type='pipeline_config_applied',
            summary=f'[CONFIG] {target}: {new_value[:300]}',
        ))
        return {
            'status': 'success',
            'message': (
                f'✅ הגדרת "{target}" נרשמה ואושרה. '
                'הצעת Grok תועדה ביומן הפעולות. '
                'יישום טכני יידרש על ידי מפתח במידת הצורך.'
            ),
        }

    def _apply_ab_test(self, db: Session, item: ApprovalItem, payload: dict) -> dict:
        new_value = payload.get('new_value') or ''
        db.add(ActivityLog(
            actor_type='admin',
            entity_type='approval_item',
            entity_id=item.id,
            action_type='ab_test_launched',
            summary=f'[A/B] {new_value[:300]}',
        ))
        return {
            'status': 'success',
            'message': '✅ A/B טסט אושר ונרשם ביומן. הפעל קמפיין חדש דרך מסך הקמפיינים.',
        }
