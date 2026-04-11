
from sqlalchemy.orm import Session
from app.models.business import Business
from app.models.activity_log import ActivityLog
from app.schemas.business import BusinessCreate


class BusinessService:
    def list_businesses(self, db: Session, skip: int = 0, limit: int = 100) -> list[Business]:
        return db.query(Business).order_by(Business.id.desc()).offset(skip).limit(limit).all()

    def create_business(self, db: Session, payload: BusinessCreate) -> Business:
        item = Business(**payload.model_dump())
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def get_business(self, db: Session, business_id: int) -> Business | None:
        return db.query(Business).filter(Business.id == business_id).first()

    def assign_campaign(self, db: Session, business_id: int, campaign_id: int | None, targeting_profile_id: int | None) -> Business | None:
        item = self.get_business(db, business_id)
        if not item:
            return None
        item.campaign_id = campaign_id
        if targeting_profile_id is not None:
            item.targeting_profile_id = targeting_profile_id
        db.add(ActivityLog(actor_type='admin', entity_type='business', entity_id=item.id, action_type='business_campaign_assigned', summary=f'campaign={campaign_id} profile={targeting_profile_id}'))
        db.commit(); db.refresh(item)
        return item

    def mark_outreach_ready(self, db: Session, business_id: int) -> Business | None:
        item = self.get_business(db, business_id)
        if not item:
            return None
        item.status = 'outreach_ready'
        db.add(ActivityLog(actor_type='admin', entity_type='business', entity_id=item.id, action_type='business_outreach_ready', summary='Marked outreach_ready'))
        db.commit(); db.refresh(item)
        return item

    def move_to_activation(self, db: Session, business_id: int) -> Business | None:
        item = self.get_business(db, business_id)
        if not item:
            return None
        item.status = 'paid'
        db.add(ActivityLog(actor_type='admin', entity_type='business', entity_id=item.id, action_type='business_move_to_activation', summary='Moved to activation/pending active'))
        db.commit(); db.refresh(item)
        return item
