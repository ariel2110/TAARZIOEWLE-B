
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin


class Business(Base, TimestampMixin):
    __tablename__ = 'businesses'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default='new', index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey('lead_records.id', ondelete='SET NULL'), nullable=True, index=True)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True, index=True)
    targeting_profile_id: Mapped[int | None] = mapped_column(ForeignKey('targeting_profiles.id', ondelete='SET NULL'), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships (lazy loaded — use explicitly when needed)
    draft_sites: Mapped[list['DraftSite']] = relationship('DraftSite', foreign_keys='DraftSite.business_id', back_populates='business', lazy='select')
    customer_accounts: Mapped[list['CustomerAccount']] = relationship('CustomerAccount', foreign_keys='CustomerAccount.business_id', back_populates='business', lazy='select')
    payment_records: Mapped[list['PaymentRecord']] = relationship('PaymentRecord', foreign_keys='PaymentRecord.business_id', back_populates='business', lazy='select')
