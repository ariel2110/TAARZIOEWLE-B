from sqlalchemy import String, Integer, Boolean, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class TargetingProfile(Base, TimestampMixin):
    __tablename__ = 'targeting_profiles'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    city: Mapped[str] = mapped_column(String(120), index=True)
    radius_km: Mapped[int] = mapped_column(Integer, default=8)
    category_list: Mapped[list | None] = mapped_column(JSON, nullable=True)
    min_reviews: Mapped[int] = mapped_column(Integer, default=0)
    min_rating: Mapped[float] = mapped_column(Float, default=0.0)
    requires_no_website: Mapped[bool] = mapped_column(Boolean, default=True)
    requires_phone: Mapped[bool] = mapped_column(Boolean, default=True)
    score_threshold: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
