from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class DemoSite(Base, TimestampMixin):
    """
    Demo website generated for a lead (a business without a website).
    A unique public URL is generated (slug) and shared via WhatsApp.
    """
    __tablename__ = 'demo_sites'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    place_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)

    business_name: Mapped[str] = mapped_column(String(255))
    tagline: Mapped[str | None] = mapped_column(String(512), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    google_maps_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    top_review: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_types: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Lifecycle
    photo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default='draft')  # draft/sent/viewed/converted
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    first_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    whatsapp_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
