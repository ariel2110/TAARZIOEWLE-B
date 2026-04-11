
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.lead import LeadCreate, LeadRead, LeadAssignCampaign
from app.schemas.business import BusinessRead
from app.services.leads.lead_import_service import LeadImportService
from app.models.user import User
from app.models.lead_record import LeadRecord
from app.models.activity_log import ActivityLog

router = APIRouter(prefix='/admin/leads', tags=['admin-leads'])
service = LeadImportService()


@router.get('', response_model=list[LeadRead])
def list_leads(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.list_leads(db, skip=skip, limit=limit)


@router.post('', response_model=LeadRead)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.create_lead(db, payload)


@router.post('/import-csv')
def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    content = file.file.read().decode('utf-8')
    return service.import_csv_text(db, content)


@router.post('/auto-qualify')
def auto_qualify_leads(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    """
    Auto-qualify leads with score >= 70 that have no website.
    Returns a list of newly qualified leads.
    """
    candidates = (
        db.query(LeadRecord)
        .filter(LeadRecord.status == 'imported')
        .filter(LeadRecord.score >= 70)
        .filter((LeadRecord.website_url == None) | (LeadRecord.website_url == ''))  # noqa: E711
        .all()
    )
    qualified = []
    for lead in candidates:
        lead.status = 'qualified'
        db.add(ActivityLog(
            actor_type='system',
            entity_type='lead_record',
            entity_id=lead.id,
            action_type='lead_auto_qualified',
            summary=f'Auto-qualified: {lead.imported_name} (score={lead.score}, no website)',
        ))
        qualified.append({'id': lead.id, 'name': lead.imported_name, 'score': lead.score})

    if qualified:
        db.commit()
        # Fire admin notification
        try:
            from app.services.common.notification_service import NotificationService
            NotificationService().notify(
                db,
                event='lead_auto_qualified',
                entity_type='lead_record',
                summary=f'Auto-qualified {len(qualified)} leads with score ≥70 and no website',
                extra={'count': str(len(qualified))},
            )
        except Exception:  # noqa: BLE001
            pass

    return {'qualified': len(qualified), 'leads': qualified}


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
