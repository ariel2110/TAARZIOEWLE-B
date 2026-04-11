
from sqlalchemy import String, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class SecurityAlert(Base, TimestampMixin):
    __tablename__ = 'security_alerts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alert_type: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True, default='medium')
    customer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    summary: Mapped[str] = mapped_column(String(255))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(20), index=True, default='open')
    escalation_level: Mapped[str] = mapped_column(String(20), default='watch')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
