from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.services.feedback.feedback_service import FeedbackService
from app.models.user import User

router = APIRouter(prefix='/admin/feedback', tags=['admin-feedback'])
service = FeedbackService()


@router.get('', response_model=list[FeedbackRead])
def list_feedback(target_type: str | None = None, status: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.list_items(db, target_type=target_type, status=status)


@router.post('', response_model=FeedbackRead)
def create_feedback(payload: FeedbackCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.create(db, **payload.model_dump())


@router.post('/{feedback_id}/analyze', response_model=FeedbackRead)
def analyze_feedback(feedback_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    item = service.analyze(db, feedback_id)
    if not item:
        raise HTTPException(status_code=404, detail='Feedback item not found')
    return item
