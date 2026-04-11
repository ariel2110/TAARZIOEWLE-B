
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class ProvisioningDecisionLog(TimestampMixin, Base):
    __tablename__ = "provisioning_decision_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_phone: Mapped[str] = mapped_column(String(32), index=True)
    decision_type: Mapped[str] = mapped_column(String(80), index=True)
    onboarding_state: Mapped[str] = mapped_column(String(80), index=True)
    package_name: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("lead_records.id"), nullable=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id"), nullable=True)
    customer_account_id: Mapped[int | None] = mapped_column(ForeignKey("customer_accounts.id"), nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    previous_state: Mapped[str | None] = mapped_column(String(80), nullable=True)
    next_action: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
