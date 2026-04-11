
from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.customer_login_event import CustomerLoginEvent
from app.models.login_challenge import LoginChallenge
from app.models.login_delivery_attempt import LoginDeliveryAttempt
from app.models.rate_limit_event import RateLimitEvent
from app.models.onboarding_session import OnboardingSession
from app.models.demo_request_log import DemoRequestLog
from app.models.security_alert import SecurityAlert

class SecurityMonitoringService:
    def summary(self, db: Session):
        login_failures = db.query(CustomerLoginEvent).filter(CustomerLoginEvent.event_type == 'login_failure').count()
        blocked = db.query(CustomerLoginEvent).filter(CustomerLoginEvent.event_type == 'login_blocked').count()
        active_challenges = db.query(LoginChallenge).filter(LoginChallenge.is_active == True).count()
        rate_limited = db.query(RateLimitEvent).filter(RateLimitEvent.success == False).count()
        deliveries = db.query(LoginDeliveryAttempt).count()
        onboarding = db.query(OnboardingSession).count()
        demo_requests = db.query(DemoRequestLog).count()
        open_alerts = db.query(SecurityAlert).filter(SecurityAlert.status == 'open').count()
        high_alerts = db.query(SecurityAlert).filter(SecurityAlert.status == 'open', SecurityAlert.severity.in_(['high','critical'])).count()
        return {
            'login_failures': login_failures,
            'blocked_logins': blocked,
            'active_challenges': active_challenges,
            'rate_limited_events': rate_limited,
            'delivery_attempts': deliveries,
            'onboarding_sessions': onboarding,
            'demo_requests': demo_requests,
            'open_security_alerts': open_alerts,
            'high_security_alerts': high_alerts,
            'overall_status': 'warning' if blocked or rate_limited or high_alerts else 'healthy',
        }

    def timeline(self, db: Session, customer_phone: str | None = None, limit: int = 100):
        items = []
        q1 = db.query(CustomerLoginEvent)
        q2 = db.query(LoginChallenge)
        q3 = db.query(LoginDeliveryAttempt)
        q4 = db.query(RateLimitEvent)
        q5 = db.query(OnboardingSession)
        q6 = db.query(DemoRequestLog)
        q7 = db.query(SecurityAlert)
        if customer_phone:
            q1 = q1.filter(CustomerLoginEvent.phone == customer_phone)
            q2 = q2.filter(LoginChallenge.customer_phone == customer_phone)
            q3 = q3.filter(LoginDeliveryAttempt.customer_phone == customer_phone)
            q4 = q4.filter(RateLimitEvent.key.contains(customer_phone))
            q5 = q5.filter(OnboardingSession.customer_phone == customer_phone)
            q6 = q6.filter(DemoRequestLog.customer_phone == customer_phone)
            q7 = q7.filter(SecurityAlert.customer_phone == customer_phone)
        for row in q1.order_by(CustomerLoginEvent.id.desc()).limit(limit).all():
            items.append({'type':'login_event','at':row.created_at,'phone':row.phone,'label':row.event_type,'detail':row.notes})
        for row in q2.order_by(LoginChallenge.id.desc()).limit(limit).all():
            items.append({'type':'challenge','at':row.created_at,'phone':row.customer_phone,'label':row.challenge_type,'detail':'active' if row.is_active else 'inactive'})
        for row in q3.order_by(LoginDeliveryAttempt.id.desc()).limit(limit).all():
            items.append({'type':'delivery_attempt','at':row.created_at,'phone':row.customer_phone,'label':row.status,'detail':f"{row.provider}/{row.delivery_channel}"})
        for row in q4.order_by(RateLimitEvent.id.desc()).limit(limit).all():
            items.append({'type':'rate_limit','at':row.created_at,'phone':customer_phone,'label':row.action,'detail':f"{row.scope}:{row.key}:{row.success}"})
        for row in q5.order_by(OnboardingSession.id.desc()).limit(limit).all():
            items.append({'type':'onboarding','at':row.created_at,'phone':row.customer_phone,'label':row.current_state,'detail':row.next_action})
        for row in q6.order_by(DemoRequestLog.id.desc()).limit(limit).all():
            items.append({'type':'demo_request','at':row.created_at,'phone':row.customer_phone,'label':row.onboarding_state,'detail':row.next_action})
        for row in q7.order_by(SecurityAlert.id.desc()).limit(limit).all():
            items.append({'type':'security_alert','at':row.created_at,'phone':row.customer_phone,'label':row.alert_type,'detail':f"{row.severity} · {row.summary}"})
        items.sort(key=lambda x: x['at'] or 0, reverse=True)
        return items[:limit]

    def suspicion_report(self, db: Session, customer_phone: str | None = None):
        phones = []
        if customer_phone:
            phones = [customer_phone]
        else:
            phones = [p for (p,) in db.query(CustomerLoginEvent.phone).filter(CustomerLoginEvent.phone.isnot(None)).distinct().all()]
        items=[]
        for phone in phones:
            failures = db.query(CustomerLoginEvent).filter(CustomerLoginEvent.phone == phone, CustomerLoginEvent.event_type == 'login_failure').count()
            blocked = db.query(CustomerLoginEvent).filter(CustomerLoginEvent.phone == phone, CustomerLoginEvent.event_type == 'login_blocked').count()
            rate_hits = db.query(RateLimitEvent).filter(RateLimitEvent.key.contains(phone), RateLimitEvent.success == False).count()
            delivery_fails = db.query(LoginDeliveryAttempt).filter(LoginDeliveryAttempt.customer_phone == phone, LoginDeliveryAttempt.status.in_(['failed','rate_limited'])).count()
            alerts = db.query(SecurityAlert).filter(SecurityAlert.customer_phone == phone, SecurityAlert.status == 'open').count()
            score = failures + blocked*3 + rate_hits*2 + delivery_fails*2 + alerts*2
            tier = 'low'
            if score >= 12: tier='high'
            elif score >= 5: tier='medium'
            items.append({'customer_phone':phone,'suspicion_score':score,'suspicion_tier':tier,'login_failures':failures,'blocked_logins':blocked,'rate_limit_hits':rate_hits,'delivery_failures':delivery_fails,'open_alerts':alerts})
        items.sort(key=lambda x: x['suspicion_score'], reverse=True)
        return {'items': items[:100], 'total': len(items)}

    def ensure_alerts(self, db: Session):
        report = self.suspicion_report(db)
        created = 0
        for item in report['items']:
            if item['suspicion_tier'] not in {'medium', 'high'}:
                continue
            existing = db.query(SecurityAlert).filter(SecurityAlert.customer_phone == item['customer_phone'], SecurityAlert.status == 'open').first()
            if existing:
                continue
            alert = SecurityAlert(
                alert_type='suspicion_watch',
                severity='high' if item['suspicion_tier'] == 'high' else 'medium',
                customer_phone=item['customer_phone'],
                summary=f"Suspicion score {item['suspicion_score']} for {item['customer_phone']}",
                detail=f"Failures={item['login_failures']} blocked={item['blocked_logins']} rate_limit={item['rate_limit_hits']} delivery_failures={item['delivery_failures']}",
                source='security_monitoring',
                escalation_level='review' if item['suspicion_tier'] == 'high' else 'watch',
            )
            db.add(alert); created += 1
        if created:
            db.commit()
        return {'created': created, 'total_considered': report['total']}

    def alerts(self, db: Session, status: str | None = None):
        q = db.query(SecurityAlert)
        if status:
            q = q.filter(SecurityAlert.status == status)
        return q.order_by(SecurityAlert.id.desc()).all()
