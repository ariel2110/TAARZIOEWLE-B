from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class DemoRequestLog(TimestampMixin, Base):
    __tablename__ = "demo_request_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_phone: Mapped[str] = mapped_column(String(32), index=True)
    business_name: Mapped[str] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="demo_requested", index=True)
    onboarding_state: Mapped[str] = mapped_column(String(80), default="demo_requested", index=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("lead_records.id"), nullable=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id"), nullable=True)
    customer_account_id: Mapped[int | None] = mapped_column(ForeignKey("customer_accounts.id"), nullable=True)
    dedup_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    package_name_snapshot: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    previous_state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    next_action: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
