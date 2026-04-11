
from sqlalchemy.orm import Session
from app.models.approval_item import ApprovalItem
from app.models.activity_log import ActivityLog

class ApprovalService:
    def list_items(self, db: Session, status: str | None = None) -> list[ApprovalItem]:
        q = db.query(ApprovalItem)
        if status:
            q = q.filter(ApprovalItem.status == status)
        return q.order_by(ApprovalItem.id.desc()).all()

    def get_item(self, db: Session, item_id: int) -> ApprovalItem | None:
        return db.query(ApprovalItem).filter(ApprovalItem.id == item_id).first()

    def approve(self, db: Session, item_id: int) -> ApprovalItem | None:
        item = self.get_item(db, item_id)
        if not item:
            return None
        old = item.status
        item.status = 'approved'
        db.add(ActivityLog(actor_type='admin', entity_type='approval_item', entity_id=item.id, action_type='approval_approved', summary=f'{old} -> approved'))
        db.commit(); db.refresh(item)
        return item

    def reject(self, db: Session, item_id: int) -> ApprovalItem | None:
        item = self.get_item(db, item_id)
        if not item:
            return None
        old = item.status
        item.status = 'rejected'
        db.add(ActivityLog(actor_type='admin', entity_type='approval_item', entity_id=item.id, action_type='approval_rejected', summary=f'{old} -> rejected'))
        db.commit(); db.refresh(item)
        return item
