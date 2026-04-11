
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.models.targeting_profile import TargetingProfile
from app.models.campaign import Campaign
from app.models.lead_record import LeadRecord
from app.models.business import Business
from app.models.activity_log import ActivityLog
from app.schemas.targeting import TargetingProfileCreate, CampaignCreate


class TargetingService:
    def create_profile(self, db: Session, payload: TargetingProfileCreate) -> TargetingProfile:
        obj = TargetingProfile(**payload.model_dump(), active=True)
        db.add(obj)
        db.commit(); db.refresh(obj)
        return obj

    def list_profiles(self, db: Session) -> list[TargetingProfile]:
        return db.query(TargetingProfile).order_by(TargetingProfile.id.desc()).all()

    def create_campaign(self, db: Session, payload: CampaignCreate) -> Campaign:
        obj = Campaign(**payload.model_dump())
        db.add(obj)
        db.commit(); db.refresh(obj)
        return obj

    def list_campaigns(self, db: Session) -> list[Campaign]:
        return db.query(Campaign).order_by(Campaign.id.desc()).all()

    def assign_lead_to_campaign(self, db: Session, lead_id: int, campaign_id: int | None, targeting_profile_id: int | None = None) -> LeadRecord | None:
        item = db.query(LeadRecord).filter(LeadRecord.id == lead_id).first()
        if not item:
            return None
        item.campaign_id = campaign_id
        if targeting_profile_id is not None:
            item.targeting_profile_id = targeting_profile_id
        db.add(ActivityLog(actor_type='admin', entity_type='lead_record', entity_id=item.id, action_type='lead_campaign_assigned', summary=f'campaign={campaign_id} profile={targeting_profile_id}'))
        db.commit(); db.refresh(item)
        return item

    def assign_business_to_campaign(self, db: Session, business_id: int, campaign_id: int | None, targeting_profile_id: int | None = None) -> Business | None:
        item = db.query(Business).filter(Business.id == business_id).first()
        if not item:
            return None
        item.campaign_id = campaign_id
        if targeting_profile_id is not None:
            item.targeting_profile_id = targeting_profile_id
        db.add(ActivityLog(actor_type='admin', entity_type='business', entity_id=item.id, action_type='business_campaign_assigned', summary=f'campaign={campaign_id} profile={targeting_profile_id}'))
        db.commit(); db.refresh(item)
        return item

    def campaign_results(self, db: Session, campaign_id: int) -> dict:
        leads = db.query(LeadRecord).filter(LeadRecord.campaign_id == campaign_id).count()
        businesses = db.query(Business).filter(Business.campaign_id == campaign_id).count()
        return {'campaign_id': campaign_id, 'lead_count': leads, 'business_count': businesses}

    def search_leads(self, db: Session, city: str | None = None, category: str | None = None, min_score: int = 0, no_website_only: bool = False, not_contacted_only: bool = False) -> list[LeadRecord]:
        query = db.query(LeadRecord)
        filters = [LeadRecord.score >= min_score]
        if city:
            filters.append(LeadRecord.city == city)
        if category:
            filters.append(LeadRecord.category == category)
        if no_website_only:
            filters.append(LeadRecord.website_url.is_(None))
        if not_contacted_only:
            filters.append(LeadRecord.status != 'contacted')
        return query.filter(and_(*filters)).order_by(LeadRecord.score.desc(), LeadRecord.id.desc()).all()
