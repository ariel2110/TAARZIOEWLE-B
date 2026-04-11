from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.services.analytics.kpi_service import KPIService

router = APIRouter(prefix='/admin/analytics', tags=['admin-analytics'])
service = KPIService()


@router.get('/snapshot')
def snapshot(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.snapshot(db)
