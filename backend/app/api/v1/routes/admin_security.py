
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import require_admin
from app.services.security.security_monitoring_service import SecurityMonitoringService
from app.services.security.lockout_policy_service import LockoutPolicyService

router = APIRouter(prefix="/admin/security", tags=["admin-security"])
service = SecurityMonitoringService()
policy_service = LockoutPolicyService()

@router.get('/summary')
def summary(db: Session = Depends(get_db), _=Depends(require_admin)):
    return service.summary(db)

@router.post('/refresh-alerts')
def refresh_alerts(db: Session = Depends(get_db), _=Depends(require_admin)):
    return service.ensure_alerts(db)

@router.get('/timeline')
def timeline(customer_phone: str | None = Query(default=None), limit: int = Query(default=100, le=300), db: Session = Depends(get_db), _=Depends(require_admin)):
    return {"items": service.timeline(db, customer_phone=customer_phone, limit=limit)}

@router.get('/suspicion')
def suspicion(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_admin)):
    return service.suspicion_report(db, customer_phone=customer_phone)

@router.get('/alerts')
def alerts(status: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_admin)):
    rows = service.alerts(db, status=status)
    return [
        {
            'id': r.id,
            'alert_type': r.alert_type,
            'severity': r.severity,
            'customer_phone': r.customer_phone,
            'summary': r.summary,
            'detail': r.detail,
            'status': r.status,
            'escalation_level': r.escalation_level,
            'created_at': r.created_at,
        } for r in rows
    ]

@router.get('/lockout-policy')
def lockout_policy(_=Depends(require_admin)):
    return policy_service.policy_summary()
