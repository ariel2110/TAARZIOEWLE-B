
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.targeting import TargetingProfileCreate, TargetingProfileRead, CampaignCreate, CampaignRead
from app.schemas.lead import LeadRead, LeadAssignCampaign
from app.schemas.business import BusinessRead
from app.services.targeting.targeting_service import TargetingService
from app.models.user import User

router = APIRouter(prefix='/admin/targeting', tags=['admin-targeting'])
service = TargetingService()


@router.get('/profiles', response_model=list[TargetingProfileRead])
def list_profiles(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.list_profiles(db)


@router.post('/profiles', response_model=TargetingProfileRead)
def create_profile(payload: TargetingProfileCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.create_profile(db, payload)


@router.get('/campaigns', response_model=list[CampaignRead])
def list_campaigns(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.list_campaigns(db)


@router.post('/campaigns', response_model=CampaignRead)
def create_campaign(payload: CampaignCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.create_campaign(db, payload)


@router.post('/campaigns/{campaign_id}/assign-lead/{lead_id}', response_model=LeadRead)
def assign_lead(campaign_id: int, lead_id: int, payload: LeadAssignCampaign, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.assign_lead_to_campaign(db, lead_id, campaign_id, payload.targeting_profile_id)
    if not item:
        raise HTTPException(status_code=404, detail='Lead not found')
    return item


@router.post('/campaigns/{campaign_id}/assign-business/{business_id}', response_model=BusinessRead)
def assign_business(campaign_id: int, business_id: int, payload: LeadAssignCampaign, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.assign_business_to_campaign(db, business_id, campaign_id, payload.targeting_profile_id)
    if not item:
        raise HTTPException(status_code=404, detail='Business not found')
    return item


@router.get('/campaigns/{campaign_id}/results')
def campaign_results(campaign_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.campaign_results(db, campaign_id)


@router.get('/search', response_model=list[LeadRead])
def search_leads(city: str | None = None, category: str | None = None, min_score: int = 0, no_website_only: bool = False, not_contacted_only: bool = False, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.search_leads(db, city=city, category=category, min_score=min_score, no_website_only=no_website_only, not_contacted_only=not_contacted_only)
