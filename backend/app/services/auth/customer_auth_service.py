import secrets
from sqlalchemy.orm import Session
from app.models.customer_account import CustomerAccount
from app.models.customer_login_event import CustomerLoginEvent
from app.core.security import create_access_token, hash_password, verify_password, needs_rehash
from app.core.config import settings
from app.services.common.rate_limit_service import RateLimitService


class CustomerAuthService:
    def __init__(self) -> None:
        self.rate_limit_service = RateLimitService()

    def create_customer_account(self, db: Session, *, business_id: int, phone: str, email: str | None = None,
                                contact_name: str | None = None, draft_site_id: int | None = None,
                                active_site_id: int | None = None, package_name: str | None = None) -> tuple[CustomerAccount, str]:
        temp_password = secrets.token_hex(3)
        account = CustomerAccount(
            business_id=business_id,
            phone=phone,
            email=email,
            contact_name=contact_name,
            draft_site_id=draft_site_id,
            active_site_id=active_site_id,
            package_name=package_name,
            password_hash=hash_password(temp_password),
            must_change_password=True,
            is_active=True,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account, temp_password

    def authenticate_customer(self, db: Session, *, phone: str, password: str, ip_address: str | None = None,
                              user_agent: str | None = None) -> CustomerAccount | None:
        # ── Hard lockout check (30-min block after too many failures) ─────────
        hard_locked = self.rate_limit_service.count_recent(
            db,
            scope='customer_login',
            key=phone,
            action='hard_lockout',
            window_minutes=30,
        )
        if hard_locked:
            event = CustomerLoginEvent(customer_account_id=None, phone=phone, event_type='login_blocked',
                                       ip_address=ip_address, user_agent=user_agent,
                                       notes='hard_lockout_active')
            db.add(event)
            db.commit()
            return None

        failures = self.rate_limit_service.count_recent(
            db,
            scope='customer_login',
            key=phone,
            action='password_login',
            window_minutes=settings.customer_login_window_minutes,
            success_only=False,
        )
        if failures >= settings.customer_login_max_failures:
            # Escalate to hard lockout — blocks all login attempts for 30 min
            self.rate_limit_service.record(db, scope='customer_login', key=phone, action='hard_lockout', success=False, detail='escalated_from_failures')
            self.rate_limit_service.record(db, scope='customer_login', key=phone, action='blocked_login', success=False, detail='too_many_failures')
            event = CustomerLoginEvent(customer_account_id=None, phone=phone, event_type='login_blocked', ip_address=ip_address, user_agent=user_agent, notes='hard_lockout_triggered')
            db.add(event)
            db.commit()
            return None

        account = db.query(CustomerAccount).filter(CustomerAccount.phone == phone, CustomerAccount.is_active == True).first()
        ok = bool(account and verify_password(password, account.password_hash))

        # Silent bcrypt upgrade: if login succeeded and password is still SHA-256, re-hash now
        if ok and account and needs_rehash(account.password_hash):
            account.password_hash = hash_password(password)
            db.add(account)

        event = CustomerLoginEvent(customer_account_id=getattr(account, 'id', None), phone=phone,
                                   event_type='login_success' if ok else 'login_failure',
                                   ip_address=ip_address, user_agent=user_agent)
        db.add(event)
        db.commit()
        self.rate_limit_service.record(
            db,
            scope='customer_login',
            key=phone,
            action='password_login',
            success=ok,
            detail='password_check',
        )
        return account if ok else None

    def create_customer_access_token(self, account: CustomerAccount) -> str:
        return create_access_token(subject=f'customer:{account.id}', role='customer')

    def get_customer_by_id(self, db: Session, customer_id: int) -> CustomerAccount | None:
        return db.query(CustomerAccount).filter(CustomerAccount.id == customer_id).first()

    def change_password(self, db: Session, account: CustomerAccount, current_password: str, new_password: str) -> CustomerAccount:
        if not verify_password(current_password, account.password_hash):
            raise ValueError('Current password is invalid')
        account.password_hash = hash_password(new_password)
        account.must_change_password = False
        db.add(account)
        db.commit()
        db.refresh(account)
        db.add(CustomerLoginEvent(customer_account_id=account.id, phone=account.phone, event_type='password_changed'))
        db.commit()
        return account
