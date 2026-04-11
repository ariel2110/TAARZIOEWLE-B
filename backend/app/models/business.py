
from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column
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
    lead_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    campaign_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    targeting_profile_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
