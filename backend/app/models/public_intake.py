from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class PublicIntake(Base, TimestampMixin):
    """Stores intake form submissions from potential customers on sitenest.site."""
    __tablename__ = 'public_intakes'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    business_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(32))
    facebook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tiktok_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    instagram_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_filenames: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    status: Mapped[str] = mapped_column(String(50), default='submitted', index=True)
    # 'submitted' | 'in_review' | 'revision_requested' | 'done' | 'cancelled'
    correction_count: Mapped[int] = mapped_column(Integer, default=0)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    # AI generation tracking
    ai_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # 'pending' | 'generating' | 'done' | 'failed'
    generated_preview_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    generated_html: Mapped[str | None] = mapped_column(Text, nullable=True)

    # WhatsApp approval queue
    whatsapp_pending_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    whatsapp_status: Mapped[str] = mapped_column(String(20), default='none')
    # 'none' | 'pending' | 'sent' | 'rejected'

    # Payment & domain activation
    desired_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_status: Mapped[str] = mapped_column(String(20), default='unpaid')
    # 'unpaid' | 'pending' | 'paid' | 'failed'
    payment_reference: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    payment_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    site_live_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Which Morning plan was paid: 'auto' | 'starter' | 'growth' | 'pro'
    # 'auto' = 39 NIS (full automation); others = manual onboarding
    plan_tier: Mapped[str] = mapped_column(String(20), default='auto')
