from __future__ import annotations
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.rate_limit_event import RateLimitEvent


class RateLimitService:
    def count_recent(self, db: Session, *, scope: str, key: str, action: str, window_minutes: int, success_only: bool | None = None) -> int:
        since = datetime.utcnow() - timedelta(minutes=window_minutes)
        q = db.query(RateLimitEvent).filter(
            RateLimitEvent.scope == scope,
            RateLimitEvent.key == key,
            RateLimitEvent.action == action,
            RateLimitEvent.created_at >= since,
        )
        if success_only is not None:
            q = q.filter(RateLimitEvent.success == success_only)
        return q.count()

    def record(self, db: Session, *, scope: str, key: str, action: str, success: bool, detail: str | None = None) -> RateLimitEvent:
        row = RateLimitEvent(scope=scope, key=key, action=action, success=success, detail=detail)
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def check_and_record(self, db: Session, *, scope: str, key: str, action: str, window_minutes: int, max_per_window: int, detail: str | None = None) -> tuple[bool, int, int]:
        current = self.count_recent(db, scope=scope, key=key, action=action, window_minutes=window_minutes)
        allowed = current < max_per_window
        self.record(db, scope=scope, key=key, action=action, success=allowed, detail=detail or ('allowed' if allowed else 'rate_limited'))
        return allowed, current, max_per_window


    def composite_key(self, *, phone: str | None = None, source_ip: str | None = None, session_key: str | None = None) -> str:
        return '|'.join([f for f in [phone or '-', source_ip or '-', session_key or '-'] if f is not None])

    def check_public_login_rate(self, db: Session, *, phone: str, source_ip: str | None = None, session_key: str | None = None, action: str = 'request', window_minutes: int = 30, max_per_window: int = 5):
        key = self.composite_key(phone=phone, source_ip=source_ip, session_key=session_key)
        return self.check_and_record(
            db, scope='public_login', key=key, action=action,
            window_minutes=window_minutes, max_per_window=max_per_window,
            detail=f'public_login:{action}',
        )
