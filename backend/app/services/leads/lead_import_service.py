
import csv
import io
from sqlalchemy.orm import Session
from app.models.lead_record import LeadRecord
from app.models.business import Business
from app.models.activity_log import ActivityLog
from app.schemas.lead import LeadCreate


class LeadImportService:
    def list_leads(self, db: Session, skip: int = 0, limit: int = 100) -> list[LeadRecord]:
        return db.query(LeadRecord).order_by(LeadRecord.score.desc(), LeadRecord.id.desc()).offset(skip).limit(limit).all()

    def create_lead(self, db: Session, payload: LeadCreate) -> LeadRecord:
        lead = LeadRecord(**payload.model_dump())
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    def import_csv_text(self, db: Session, content: str) -> dict:
        reader = csv.DictReader(io.StringIO(content))
        created = 0
        for row in reader:
            rating_raw = row.get('rating') or row.get('Rating')
            reviews_raw = row.get('reviews_count') or row.get('reviews') or row.get('reviews_count')
            lead = LeadRecord(
                imported_name=row.get('imported_name') or row.get('name') or 'Unnamed lead',
                city=row.get('city'),
                category=row.get('category'),
                phone=row.get('phone'),
                address=row.get('address'),
                website_url=row.get('website_url'),
                score=int(row.get('score') or 0),
                rating=float(rating_raw) if rating_raw else None,
                reviews_count=int(reviews_raw) if reviews_raw else None,
                status=row.get('status') or 'imported',
            )
            db.add(lead)
            created += 1
        db.commit()
        return {'created': created, 'status': 'ok'}

    def qualify(self, db: Session, lead_id: int) -> LeadRecord | None:
        lead = db.query(LeadRecord).filter(LeadRecord.id == lead_id).first()
        if not lead:
            return None
        lead.status = 'qualified'
        db.add(ActivityLog(actor_type='admin', entity_type='lead_record', entity_id=lead.id, action_type='lead_qualified', summary=f'Lead {lead.imported_name} qualified'))
        db.commit(); db.refresh(lead)
        return lead

    def assign_campaign(self, db: Session, lead_id: int, campaign_id: int | None, targeting_profile_id: int | None) -> LeadRecord | None:
        lead = db.query(LeadRecord).filter(LeadRecord.id == lead_id).first()
        if not lead:
            return None
        lead.campaign_id = campaign_id
        if targeting_profile_id is not None:
            lead.targeting_profile_id = targeting_profile_id
        db.add(ActivityLog(actor_type='admin', entity_type='lead_record', entity_id=lead.id, action_type='lead_campaign_assigned', summary=f'campaign={campaign_id} profile={targeting_profile_id}'))
        db.commit(); db.refresh(lead)
        return lead

    def convert_to_business(self, db: Session, lead_id: int) -> Business | None:
        lead = db.query(LeadRecord).filter(LeadRecord.id == lead_id).first()
        if not lead:
            return None
        business = Business(
            name=lead.imported_name,
            city=lead.city,
            category=lead.category,
            phone=lead.phone,
            address=lead.address,
            status='reviewed',
            lead_id=lead.id,
            campaign_id=lead.campaign_id,
            targeting_profile_id=lead.targeting_profile_id,
        )
        lead.status = 'converted_to_business'
        db.add(business)
        db.flush()
        db.add(ActivityLog(actor_type='admin', entity_type='lead_record', entity_id=lead.id, action_type='lead_converted_to_business', summary=f'business_id={business.id}'))
        db.commit(); db.refresh(business)
        return business
