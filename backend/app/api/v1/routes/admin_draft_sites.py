
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.draft_site import DraftSiteCreate, DraftSiteRead
from app.services.draft_sites.draft_site_service import DraftSiteService
from app.models.user import User

router = APIRouter(prefix='/admin/draft-sites', tags=['admin-draft-sites'])
service = DraftSiteService()


@router.get('', response_model=list[DraftSiteRead])
def list_drafts(skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.list_drafts(db, skip=skip, limit=limit)


@router.post('', response_model=DraftSiteRead)
def create_draft(payload: DraftSiteCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.create_draft(db, payload)


@router.post('/{draft_id}/generate-preview', response_model=DraftSiteRead)
def generate_preview(draft_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.generate_preview(db, draft_id)
    if not item:
        raise HTTPException(status_code=404, detail='Draft not found')
    return item


@router.post('/create-and-preview/{business_id}', response_model=DraftSiteRead)
def create_and_preview(business_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.create_and_preview(db, business_id)
    if not item:
        raise HTTPException(status_code=404, detail='Business not found')
    return item
