from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_admin
from app.schemas.insight import InsightRead
from app.services.insights.insight_generation_service import InsightGenerationService

router = APIRouter(prefix='/admin/insights', tags=['admin-insights'], dependencies=[Depends(get_current_admin)])
service = InsightGenerationService()


@router.get('', response_model=list[InsightRead])
def list_insights(db: Session = Depends(get_db)):
    service.seed_default_insight(db)
    return service.list_insights(db)
