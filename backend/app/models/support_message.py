from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class SupportMessage(Base, TimestampMixin):
    __tablename__ = 'support_messages'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_account_id: Mapped[int] = mapped_column(Integer, index=True)
    business_id: Mapped[int] = mapped_column(Integer, index=True)
    subject: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default='open', index=True)
