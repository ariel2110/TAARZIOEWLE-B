from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class RateLimitEvent(Base, TimestampMixin):
    __tablename__ = 'rate_limit_events'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(64), index=True)
    key: Mapped[str] = mapped_column(String(128), index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    success: Mapped[bool] = mapped_column(default=True, index=True)
    detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
