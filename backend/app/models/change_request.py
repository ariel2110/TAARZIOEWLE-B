from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class ChangeRequest(Base, TimestampMixin):
    __tablename__ = 'change_requests'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_account_id: Mapped[int] = mapped_column(Integer, index=True)
    business_id: Mapped[int] = mapped_column(Integer, index=True)
    request_type: Mapped[str] = mapped_column(String(80), default='general', index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default='submitted', index=True)
    estimated_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
