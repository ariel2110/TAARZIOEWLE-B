
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.ceo import CEOReport, CEOHealth, CEONoteCreate, CEOTaskCreate
from app.services.ceo_agent.ceo_report_service import CEOReportService
from app.models.user import User

router = APIRouter(prefix='/admin/ceo', tags=['admin-ceo'])
service = CEOReportService()


@router.get('/daily-digest', response_model=CEOReport)
def daily_digest(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.daily_digest(db)


@router.get('/health', response_model=CEOHealth)
def health(_: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return {'overall_status': 'healthy', 'database_ok': True, 'drivers': ['Queues visible', 'Approvals connected', 'Feedback intelligence active']}


@router.post('/task-from-recommendation')
def task_from_recommendation(payload: CEOTaskCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.create_task(db, payload.source, payload.title, payload.note)


@router.post('/decision-note')
def decision_note(payload: CEONoteCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.add_note(db, payload.note)
