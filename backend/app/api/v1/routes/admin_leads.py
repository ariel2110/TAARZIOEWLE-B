
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadRead, LeadAssignCampaign
from app.schemas.business import BusinessRead
from app.services.leads.lead_import_service import LeadImportService
from app.models.user import User

router = APIRouter(prefix='/admin/leads', tags=['admin-leads'])
service = LeadImportService()


@router.get('', response_model=list[LeadRead])
def list_leads(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.list_leads(db)


@router.post('', response_model=LeadRead)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.create_lead(db, payload)


@router.post('/import-csv')
def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    content = file.file.read().decode('utf-8')
    return service.import_csv_text(db, content)


@router.post('/{lead_id}/qualify', response_model=LeadRead)
def qualify_lead(lead_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.qualify(db, lead_id)
    if not item:
        raise HTTPException(status_code=404, detail='Lead not found')
    return item


@router.post('/{lead_id}/assign', response_model=LeadRead)
def assign_campaign(lead_id: int, payload: LeadAssignCampaign, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.assign_campaign(db, lead_id, payload.campaign_id, payload.targeting_profile_id)
    if not item:
        raise HTTPException(status_code=404, detail='Lead not found')
    return item


@router.post('/{lead_id}/convert-to-business', response_model=BusinessRead)
def convert_to_business(lead_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.convert_to_business(db, lead_id)
    if not item:
        raise HTTPException(status_code=404, detail='Lead not found')
    return item
