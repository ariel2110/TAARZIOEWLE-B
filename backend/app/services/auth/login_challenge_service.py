
from __future__ import annotations
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.login_challenge import LoginChallenge
from app.models.customer_account import CustomerAccount
from app.core.security import create_access_token


class LoginChallengeService:
    MAGIC_MINUTES = 20
    OTP_MINUTES = 10

    def _deactivate_previous(self, db: Session, customer_phone: str, challenge_type: str):
        rows = db.query(LoginChallenge).filter(
            LoginChallenge.customer_phone == customer_phone,
            LoginChallenge.challenge_type == challenge_type,
            LoginChallenge.is_active == True,
            LoginChallenge.consumed_at.is_(None),
        ).all()
        for row in rows:
            row.is_active = False
            db.add(row)
        db.commit()

    def create_magic_link(self, db: Session, *, customer_phone: str, customer_account_id: int | None = None, onboarding_session_id: int | None = None) -> LoginChallenge:
        self._deactivate_previous(db, customer_phone, 'magic_link')
        token = secrets.token_urlsafe(24)
        row = LoginChallenge(
            customer_phone=customer_phone,
            challenge_type='magic_link',
            token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=self.MAGIC_MINUTES),
            customer_account_id=customer_account_id,
            onboarding_session_id=onboarding_session_id,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def create_otp(self, db: Session, *, customer_phone: str, customer_account_id: int | None = None, onboarding_session_id: int | None = None) -> LoginChallenge:
        self._deactivate_previous(db, customer_phone, 'otp')
        code = ''.join(secrets.choice('0123456789') for _ in range(6))
        row = LoginChallenge(
            customer_phone=customer_phone,
            challenge_type='otp',
            token=secrets.token_urlsafe(16),
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=self.OTP_MINUTES),
            customer_account_id=customer_account_id,
            onboarding_session_id=onboarding_session_id,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def consume_magic_link(self, db: Session, token: str) -> dict:
        row = db.query(LoginChallenge).filter(LoginChallenge.token == token, LoginChallenge.challenge_type == 'magic_link').first()
        if not row or not row.is_active or row.consumed_at is not None:
            raise ValueError('Magic link is invalid')
        if row.expires_at < datetime.utcnow():
            raise ValueError('Magic link has expired')
        row.consumed_at = datetime.utcnow()
        row.is_active = False
        db.add(row)
        db.commit()
        account = None
        if row.customer_account_id:
            account = db.query(CustomerAccount).filter(CustomerAccount.id == row.customer_account_id, CustomerAccount.is_active == True).first()
        access_token = create_access_token(subject=f'customer:{account.id}', role='customer') if account else None
        return {'ok': True, 'customer_phone': row.customer_phone, 'customer_account_id': getattr(account, 'id', None), 'access_token': access_token}

    def verify_otp(self, db: Session, *, customer_phone: str, code: str) -> dict:
        row = db.query(LoginChallenge).filter(
            LoginChallenge.customer_phone == customer_phone,
            LoginChallenge.challenge_type == 'otp',
            LoginChallenge.is_active == True,
            LoginChallenge.consumed_at.is_(None),
        ).order_by(LoginChallenge.id.desc()).first()
        if not row:
            raise ValueError('OTP request not found')
        if row.expires_at < datetime.utcnow():
            raise ValueError('OTP has expired')
        if row.code != code:
            raise ValueError('OTP code is invalid')
        row.consumed_at = datetime.utcnow()
        row.is_active = False
        db.add(row)
        db.commit()
        account = None
        if row.customer_account_id:
            account = db.query(CustomerAccount).filter(CustomerAccount.id == row.customer_account_id, CustomerAccount.is_active == True).first()
        access_token = create_access_token(subject=f'customer:{account.id}', role='customer') if account else None
        return {'ok': True, 'customer_phone': row.customer_phone, 'customer_account_id': getattr(account, 'id', None), 'access_token': access_token}
