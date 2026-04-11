from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class CustomerAccount(Base, TimestampMixin):
    __tablename__ = 'customer_accounts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, index=True)
    draft_site_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    active_site_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    package_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
