
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class PackagePlan(Base, TimestampMixin):
    __tablename__ = 'package_plans'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    monthly_demo_limit: Mapped[int] = mapped_column(Integer, default=2)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    customer_portal_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_contact_verification: Mapped[bool] = mapped_column(Boolean, default=False)
    billing_mode: Mapped[str] = mapped_column(String(40), default='demo', index=True)
