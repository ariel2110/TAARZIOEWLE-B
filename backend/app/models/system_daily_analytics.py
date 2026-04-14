"""SystemDailyAnalytics — one row per calendar day.

Aggregated platform metrics rebuilt (or updated) daily by a background task.
Used by the CEO Analytics dashboard global-stats endpoint.
"""
from __future__ import annotations

import datetime

from sqlalchemy import Date, Float, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class SystemDailyAnalytics(Base, TimestampMixin):
    __tablename__ = 'system_daily_analytics'

    id:   Mapped[int]            = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date]  = mapped_column(Date, unique=True, index=True)

    # ── Revenue ───────────────────────────────────────────────────────────
    total_revenue_ils:   Mapped[float] = mapped_column(Float, default=0.0)
    total_sites_built:   Mapped[int]   = mapped_column(Integer, default=0)

    # ── API Costs (ILS) ───────────────────────────────────────────────────
    total_api_cost_ils:  Mapped[float] = mapped_column(Float, default=0.0)
    claude_cost_ils:     Mapped[float] = mapped_column(Float, default=0.0)
    gpt_cost_ils:        Mapped[float] = mapped_column(Float, default=0.0)
    gemini_cost_ils:     Mapped[float] = mapped_column(Float, default=0.0)
    grok_cost_ils:       Mapped[float] = mapped_column(Float, default=0.0)
    serper_cost_ils:     Mapped[float] = mapped_column(Float, default=0.0)
    apify_cost_ils:      Mapped[float] = mapped_column(Float, default=0.0)

    # ── Token totals ──────────────────────────────────────────────────────
    claude_tokens_in:    Mapped[int] = mapped_column(Integer, default=0)
    claude_tokens_out:   Mapped[int] = mapped_column(Integer, default=0)
    gpt_tokens_in:       Mapped[int] = mapped_column(Integer, default=0)
    gpt_tokens_out:      Mapped[int] = mapped_column(Integer, default=0)
    gemini_tokens_in:    Mapped[int] = mapped_column(Integer, default=0)
    gemini_tokens_out:   Mapped[int] = mapped_column(Integer, default=0)
    grok_tokens_in:      Mapped[int] = mapped_column(Integer, default=0)
    grok_tokens_out:     Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint('date', name='uq_sda_date'),
    )

