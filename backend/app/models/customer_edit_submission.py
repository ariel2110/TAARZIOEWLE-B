from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class CustomerEditSubmission(Base, TimestampMixin):
    __tablename__ = 'customer_edit_submissions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_account_id: Mapped[int] = mapped_column(Integer, index=True)
    business_id: Mapped[int] = mapped_column(Integer, index=True)
    field_key: Mapped[str] = mapped_column(String(120), index=True)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default='pending_review', index=True)
