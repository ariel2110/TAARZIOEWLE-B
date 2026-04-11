
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class OnboardingSession(Base, TimestampMixin):
    __tablename__ = 'onboarding_sessions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_phone: Mapped[str] = mapped_column(String(32), index=True)
    business_name: Mapped[str] = mapped_column(String(255), index=True)
    current_state: Mapped[str] = mapped_column(String(80), default='intake_preview', index=True)
    previous_state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    package_name: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey('lead_records.id'), nullable=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey('businesses.id'), nullable=True)
    customer_account_id: Mapped[int | None] = mapped_column(ForeignKey('customer_accounts.id'), nullable=True)
    last_preview_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    magic_login_token: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    magic_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    next_action: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
