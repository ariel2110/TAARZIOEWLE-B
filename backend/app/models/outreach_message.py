
from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class OutreachMessage(TimestampMixin, Base):
    __tablename__ = 'outreach_messages'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey('businesses.id'), default=None, index=True)
    draft_site_id: Mapped[int | None] = mapped_column(ForeignKey('draft_sites.id'), default=None, index=True)
    channel: Mapped[str] = mapped_column(String(50), default='whatsapp', index=True)
    status: Mapped[str] = mapped_column(String(50), default='draft', index=True)
    message_template_key: Mapped[str | None] = mapped_column(String(120), default=None)
    content: Mapped[str] = mapped_column(Text)
    outbound_target: Mapped[str | None] = mapped_column(String(50), default=None)
    city_context: Mapped[str | None] = mapped_column(String(120), default=None)
    category_context: Mapped[str | None] = mapped_column(String(120), default=None)
    # A/B testing support
    ab_variant: Mapped[str | None] = mapped_column(String(50), default=None, index=True)
    ab_campaign_id: Mapped[str | None] = mapped_column(String(100), default=None, index=True)
    has_replied: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
