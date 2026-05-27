
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class LoginChallenge(Base, TimestampMixin):
    __tablename__ = 'login_challenges'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_phone: Mapped[str] = mapped_column(String(32), index=True)
    challenge_type: Mapped[str] = mapped_column(String(32), index=True, default='magic_link')
    token: Mapped[str] = mapped_column(String(160), index=True)
    code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    customer_account_id: Mapped[int | None] = mapped_column(ForeignKey('customer_accounts.id'), nullable=True)
    onboarding_session_id: Mapped[int | None] = mapped_column(ForeignKey('onboarding_sessions.id'), nullable=True)
