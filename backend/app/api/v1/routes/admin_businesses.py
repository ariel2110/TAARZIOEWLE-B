
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.business import BusinessCreate, BusinessRead
from app.schemas.lead import LeadAssignCampaign
from app.schemas.draft_site import DraftSiteRead
from app.services.businesses.business_service import BusinessService
from app.services.draft_sites.draft_site_service import DraftSiteService
from app.models.user import User

router = APIRouter(prefix='/admin/businesses', tags=['admin-businesses'])
service = BusinessService()
draft_service = DraftSiteService()


@router.get('', response_model=list[BusinessRead])
def list_businesses(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.list_businesses(db, skip=skip, limit=limit)


@router.post('', response_model=BusinessRead)
def create_business(payload: BusinessCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.create_business(db, payload)


@router.post('/{business_id}/assign', response_model=BusinessRead)
def assign_campaign(business_id: int, payload: LeadAssignCampaign, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.assign_campaign(db, business_id, payload.campaign_id, payload.targeting_profile_id)
    if not item:
        raise HTTPException(status_code=404, detail='Business not found')
    return item


@router.post('/{business_id}/move-to-draft', response_model=DraftSiteRead)
def move_to_draft(business_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = draft_service.create_for_business(db, business_id)
    if not item:
        raise HTTPException(status_code=404, detail='Business not found')
    return item


@router.post('/{business_id}/outreach-ready', response_model=BusinessRead)
def mark_outreach_ready(business_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.mark_outreach_ready(db, business_id)
    if not item:
        raise HTTPException(status_code=404, detail='Business not found')
    return item
