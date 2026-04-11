from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin


class PaymentRecord(Base, TimestampMixin):
    __tablename__ = 'payment_records'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey('businesses.id', ondelete='SET NULL'), nullable=True, index=True)

    # Relationship
    business: Mapped['Business | None'] = relationship('Business', foreign_keys=[business_id], back_populates='payment_records', lazy='select')
    amount: Mapped[int] = mapped_column(Integer, default=0)
    provider: Mapped[str] = mapped_column(String(50), default='manual')
    internal_status: Mapped[str] = mapped_column(String(50), default='pending', index=True)
    external_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
