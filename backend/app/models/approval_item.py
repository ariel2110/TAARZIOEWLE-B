
from sqlalchemy import String, Text, Boolean, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class ApprovalItem(Base, TimestampMixin):
    __tablename__ = 'approval_items'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    approval_type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default='proposed', index=True)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    before_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
