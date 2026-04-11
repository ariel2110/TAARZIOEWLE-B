
from sqlalchemy import String, Integer, Float, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.models.mixins import TimestampMixin


class LeadRecord(Base, TimestampMixin):
    __tablename__ = 'lead_records'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    imported_name: Mapped[str] = mapped_column(String(255), index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    # Google Maps signals — the source of truth for hot-lead scoring
    rating: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default='imported', index=True)
    campaign_id: Mapped[int | None] = mapped_column(ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True, index=True)
    targeting_profile_id: Mapped[int | None] = mapped_column(ForeignKey('targeting_profiles.id', ondelete='SET NULL'), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Social & Digital Asset Discovery ───────────────────────────────────
    facebook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tiktok_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    easy_url: Mapped[str | None] = mapped_column(String(500), nullable=True)       # Easy (איזי) directory page
    b144_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    legacy_site_url: Mapped[str | None] = mapped_column(String(500), nullable=True) # old non-mobile-friendly site
    social_verified: Mapped[bool] = mapped_column(default=False, index=True)
    social_confidence: Mapped[int] = mapped_column(Integer, default=0)              # 0–100
    digital_gap_label: Mapped[str | None] = mapped_column(String(50), nullable=True) # 'super_hot' | 'hot' | None

    # Relationships
    businesses: Mapped[list['Business']] = relationship('Business', foreign_keys='Business.lead_id', back_populates=None, lazy='select', viewonly=True)
