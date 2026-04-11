from sqlalchemy import String, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class DraftSite(Base, TimestampMixin):
    __tablename__ = 'draft_sites'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, index=True)
    site_title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default='draft', index=True)
    preview_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(40), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True)
    noindex: Mapped[bool] = mapped_column(Boolean, default=True)
    hero_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    about_text: Mapped[str | None] = mapped_column(Text, nullable=True)
