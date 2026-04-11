from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class GeneratedInsight(TimestampMixin, Base):
    __tablename__ = 'generated_insights'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    insight_type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    evidence_json: Mapped[str | None] = mapped_column(Text, default=None)
    confidence_score: Mapped[float | None] = mapped_column(Float, default=None)
    status: Mapped[str] = mapped_column(String(50), default='proposed', index=True)
