from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class ActivityLog(TimestampMixin, Base):
    __tablename__ = 'activity_logs'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    actor_type: Mapped[str] = mapped_column(String(50), default='system', index=True)
    actor_id: Mapped[int | None] = mapped_column(Integer, default=None)
    entity_type: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, default=None, index=True)
    action_type: Mapped[str] = mapped_column(String(120), index=True)
    summary: Mapped[str | None] = mapped_column(Text, default=None)
