from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class FeedbackItem(Base, TimestampMixin):
    __tablename__ = 'feedback_items'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    target_type: Mapped[str] = mapped_column(String(80), index=True)
    target_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    context_type: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    quick_rating: Mapped[str] = mapped_column(String(40), default='needs_improvement', index=True)
    open_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback_status: Mapped[str] = mapped_column(String(40), default='new', index=True)
    analysis_category: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    suggested_scope: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    ceo_understanding: Mapped[str | None] = mapped_column(Text, nullable=True)
    ceo_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_hint: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    preference_candidate: Mapped[bool] = mapped_column(default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
