
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
        item.status = 'applied'
        db.add(ActivityLog(actor_type='admin', entity_type='approval_item', entity_id=item.id, action_type='approval_applied', summary=item.title))
        db.commit(); db.refresh(item)
        return {'id': item.id, 'status': item.status, 'applied': True}
