from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class Campaign(Base, TimestampMixin):
    __tablename__ = 'campaigns'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    targeting_profile_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default='draft', index=True)
    goals_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
