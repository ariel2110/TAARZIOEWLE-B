
from sqlalchemy import String, Text, Integer, Float, ForeignKey
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
    # Google Places / geo enrichment
    google_place_id: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # ── Social & Digital Asset Discovery ───────────────────────────────────
    facebook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tiktok_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    easy_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    legacy_site_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    social_verified: Mapped[bool] = mapped_column(default=False)
    social_confidence: Mapped[int] = mapped_column(Integer, default=0)
    digital_gap_label: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships (lazy loaded — use explicitly when needed)
    draft_sites: Mapped[list['DraftSite']] = relationship('DraftSite', foreign_keys='DraftSite.business_id', back_populates='business', lazy='select')
    customer_accounts: Mapped[list['CustomerAccount']] = relationship('CustomerAccount', foreign_keys='CustomerAccount.business_id', back_populates='business', lazy='select')
    payment_records: Mapped[list['PaymentRecord']] = relationship('PaymentRecord', foreign_keys='PaymentRecord.business_id', back_populates='business', lazy='select')
