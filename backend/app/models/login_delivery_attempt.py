from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class LoginDeliveryAttempt(Base, TimestampMixin):
    __tablename__ = 'login_delivery_attempts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_phone: Mapped[str] = mapped_column(String(32), index=True)
    challenge_type: Mapped[str] = mapped_column(String(32), index=True)
    provider: Mapped[str] = mapped_column(String(32), default='preview', index=True)
    delivery_channel: Mapped[str] = mapped_column(String(32), default='preview', index=True)
    status: Mapped[str] = mapped_column(String(32), default='prepared', index=True)
    external_reference: Mapped[str | None] = mapped_column(String(160), nullable=True)
    challenge_id: Mapped[int | None] = mapped_column(ForeignKey('login_challenges.id'), nullable=True)
    detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    was_rate_limited: Mapped[bool] = mapped_column(Boolean, default=False)
