from sqlalchemy import String, Integer, Float, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class EnrichedBizCache(Base, TimestampMixin):
    """
    Cache table for enriched businesses pulled from Google Places.
    Prevents re-fetching the same business on subsequent searches.
    """
    __tablename__ = 'enriched_biz_cache'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    place_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    business_types: Mapped[str | None] = mapped_column(String(512), nullable=True)
    search_query: Mapped[str | None] = mapped_column(String(255), nullable=True)
    completeness_score: Mapped[int] = mapped_column(Integer, default=0)
    imported_as_lead: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)
