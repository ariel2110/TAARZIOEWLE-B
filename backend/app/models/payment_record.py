from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class PaymentRecord(Base, TimestampMixin):
    __tablename__ = 'payment_records'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str] = mapped_column(String(50), default='manual')
    internal_status: Mapped[str] = mapped_column(String(50), default='pending', index=True)
    external_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
