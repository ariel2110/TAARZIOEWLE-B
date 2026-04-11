
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.ceo import (
    CEOReport, CEOHealth, CEONoteCreate, CEOTaskCreate,
    GrokThinkRequest, GrokExecuteRequest, GrokExecuteResponse,
)
from app.services.ceo_agent.ceo_report_service import CEOReportService
from app.services.ceo_agent.ceo_grok_service import CEOGrokService
from app.models.user import User

router = APIRouter(prefix='/admin/ceo', tags=['admin-ceo'])
service = CEOReportService()
grok_service = CEOGrokService()


@router.get('/daily-digest', response_model=CEOReport)
def daily_digest(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.daily_digest(db)


@router.get('/health', response_model=CEOHealth)
def health(_: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    from sqlalchemy import text
    db_ok = False
    try:
        db.execute(text('SELECT 1'))
        db_ok = True
    except Exception:
        db_ok = False

    from app.models.outreach_message import OutreachMessage
    from app.models.lead_record import LeadRecord
    total_messages = db.query(OutreachMessage).count()
    total_leads = db.query(LeadRecord).count()

    drivers = [
        f'בסיס נתונים {"מחובר" if db_ok else "לא זמין"}',
        f'{total_leads} לידים נטענו',
        f'{total_messages} הודעות בתור',
        'AI Pipeline — מוכן',
        'WhatsApp Gateway — מוגדר',
    ]
    return {
        'overall_status': 'פעיל' if db_ok else 'מושבת',
        'database_ok': db_ok,
        'drivers': drivers,
    }


@router.post('/task-from-recommendation')
def task_from_recommendation(payload: CEOTaskCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.create_task(db, payload.source, payload.title, payload.note)


@router.post('/decision-note')
def decision_note(payload: CEONoteCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.add_note(db, payload.note)


# ── Grok CEO endpoints ────────────────────────────────────────────────────────

@router.post('/grok-think')
def grok_think(
    payload: GrokThinkRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Invoke Grok as the AI CEO. Returns a structured Hebrew proposal."""
    return grok_service.think(db, payload.message)


@router.post('/grok-execute', response_model=GrokExecuteResponse)
def grok_execute(
    payload: GrokExecuteRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Execute an approved Grok action (or route to approval queue)."""
    return grok_service.execute(
        db,
        action_type=payload.action_type,
        target_component=payload.target_component,
        new_value=payload.new_value,
    )
