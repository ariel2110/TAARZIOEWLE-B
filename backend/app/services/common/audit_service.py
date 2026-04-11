from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog


class AuditService:
    def log(self, db: Session, *, actor_type: str, actor_id: int | None, entity_type: str, entity_id: int | None, action_type: str, summary: str | None = None):
        entry = ActivityLog(
            actor_type=actor_type,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action_type=action_type,
            summary=summary,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
