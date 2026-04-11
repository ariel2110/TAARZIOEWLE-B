
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import require_admin
from app.schemas.public_portal import DemoRequestStatusResponse, PublicStatusSummaryResponse, DemoCompareResponse, PackagePlanResponse
from app.services.public.public_portal_service import PublicPortalService
from app.models.provisioning_decision_log import ProvisioningDecisionLog
from app.models.onboarding_session import OnboardingSession
from app.models.login_challenge import LoginChallenge
from app.models.login_delivery_attempt import LoginDeliveryAttempt
from app.models.rate_limit_event import RateLimitEvent

router = APIRouter(prefix="/admin/public-flow", tags=["admin-public-flow"])
service = PublicPortalService()

@router.get('/demo-requests', response_model=DemoRequestStatusResponse)
def list_demo_requests(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_admin)):
    return service.demo_request_status(db, customer_phone)

@router.get('/demo-status-summary', response_model=PublicStatusSummaryResponse)
def public_flow_summary(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_admin)):
    return service.demo_status_summary(db, customer_phone)

@router.get('/demo-compare', response_model=DemoCompareResponse)
def public_flow_compare(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_admin)):
    return service.demo_compare(db, customer_phone)

@router.get('/packages', response_model=list[PackagePlanResponse])
def package_plans(db: Session = Depends(get_db), _=Depends(require_admin)):
    return service.package_plans(db)

@router.get('/provisioning-decisions')
def provisioning_decisions(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_admin)):
    q = db.query(ProvisioningDecisionLog)
    if customer_phone:
        q = q.filter(ProvisioningDecisionLog.customer_phone == customer_phone)
    rows = q.order_by(ProvisioningDecisionLog.id.desc()).limit(100).all()
    return {
        'items': [
            {
                'id': r.id,
                'customer_phone': r.customer_phone,
                'decision_type': r.decision_type,
                'onboarding_state': r.onboarding_state,
                'package_name': r.package_name,
                'lead_id': r.lead_id,
                'business_id': r.business_id,
                'customer_account_id': r.customer_account_id,
                'decision_reason': r.decision_reason,
                'previous_state': r.previous_state,
                'next_action': r.next_action,
                'notes': r.notes,
                'created_at': r.created_at,
            } for r in rows
        ],
        'total': len(rows),
    }

@router.get('/onboarding-sessions')
def onboarding_sessions(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_admin)):
    q = db.query(OnboardingSession)
    if customer_phone:
        q = q.filter(OnboardingSession.customer_phone == customer_phone)
    rows = q.order_by(OnboardingSession.id.desc()).limit(100).all()
    return {
        'items': [
            {
                'id': s.id,
                'customer_phone': s.customer_phone,
                'business_name': s.business_name,
                'current_state': s.current_state,
                'previous_state': s.previous_state,
                'package_name': s.package_name,
                'lead_id': s.lead_id,
                'business_id': s.business_id,
                'customer_account_id': s.customer_account_id,
                'last_preview_score': s.last_preview_score,
                'next_action': s.next_action,
                'magic_token_active': bool(s.magic_login_token),
                'magic_token_expires_at': s.magic_token_expires_at,
                'created_at': s.created_at,
                'updated_at': s.updated_at,
            } for s in rows
        ],
        'total': len(rows),
    }


@router.get('/login-challenges')
def login_challenges(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_admin)):
    q = db.query(LoginChallenge)
    if customer_phone:
        q = q.filter(LoginChallenge.customer_phone == customer_phone)
    rows = q.order_by(LoginChallenge.id.desc()).limit(100).all()
    return {
        'items': [
            {
                'id': r.id,
                'customer_phone': r.customer_phone,
                'challenge_type': r.challenge_type,
                'expires_at': r.expires_at,
                'consumed_at': r.consumed_at,
                'is_active': r.is_active,
                'customer_account_id': r.customer_account_id,
                'onboarding_session_id': r.onboarding_session_id,
                'created_at': r.created_at,
            } for r in rows
        ],
        'total': len(rows),
    }


@router.get('/login-deliveries')
def login_deliveries(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_admin)):
    q = db.query(LoginDeliveryAttempt)
    if customer_phone:
        q = q.filter(LoginDeliveryAttempt.customer_phone == customer_phone)
    rows = q.order_by(LoginDeliveryAttempt.id.desc()).limit(100).all()
    return {
        'items': [
            {
                'id': r.id,
                'customer_phone': r.customer_phone,
                'challenge_type': r.challenge_type,
                'provider': r.provider,
                'delivery_channel': r.delivery_channel,
                'status': r.status,
                'challenge_id': r.challenge_id,
                'detail': r.detail,
                'was_rate_limited': r.was_rate_limited,
                'created_at': r.created_at,
            } for r in rows
        ],
        'total': len(rows),
    }


@router.get('/rate-limit-events')
def rate_limit_events(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_admin)):
    q = db.query(RateLimitEvent)
    if customer_phone:
        q = q.filter(RateLimitEvent.key.contains(customer_phone))
    rows = q.order_by(RateLimitEvent.id.desc()).limit(100).all()
    return {
        'items': [
            {
                'id': r.id,
                'scope': r.scope,
                'key': r.key,
                'action': r.action,
                'success': r.success,
                'detail': r.detail,
                'created_at': r.created_at,
            } for r in rows
        ],
        'total': len(rows),
    }


@router.get('/login-monitoring-summary')
def login_monitoring_summary(customer_phone: str | None = Query(default=None), db: Session = Depends(get_db), _=Depends(require_admin)):
    return service.login_security_monitoring_summary(db, customer_phone)
