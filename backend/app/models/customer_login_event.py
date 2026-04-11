from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class CustomerLoginEvent(Base, TimestampMixin):
    __tablename__ = 'customer_login_events'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_account_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(120), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
