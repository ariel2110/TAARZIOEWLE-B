"""AgentUsageLog — one row per LLM / tool call.

Tracks every AI API invocation with token counts and calculated cost
so CEO Analytics can show per-site and global economics.
"""
from __future__ import annotations

from sqlalchemy import Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class AgentUsageLog(Base, TimestampMixin):
    __tablename__ = 'agent_usage_logs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Call context ──────────────────────────────────────────────────────
    # Any of these may be NULL — e.g. abandonment-recovery has no business_id
    business_id:    Mapped[int | None]  = mapped_column(Integer, nullable=True, index=True)
    draft_site_id:  Mapped[int | None]  = mapped_column(Integer, nullable=True, index=True)
    intake_token:   Mapped[str | None]  = mapped_column(String(128), nullable=True, index=True)
    stage:          Mapped[str | None]  = mapped_column(String(80), nullable=True)
    # e.g. 'site_generation' | 'abandonment_recovery' | 'ceo_digest' | 'enrichment'
    task_type:      Mapped[str | None]  = mapped_column(String(80), nullable=True, index=True)

    # ── Agent identity ────────────────────────────────────────────────────
    # 'claude' | 'gpt' | 'gemini' | 'grok' | 'serper' | 'apify'
    agent_name:  Mapped[str] = mapped_column(String(40), index=True)
    model_name:  Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ── Usage ─────────────────────────────────────────────────────────────
    input_tokens:      Mapped[int] = mapped_column(Integer, default=0)
    output_tokens:     Mapped[int] = mapped_column(Integer, default=0)
    additional_units:  Mapped[int] = mapped_column(Integer, default=0)  # e.g. # of queries (serper)

    # ── Cost (pre-calculated at write time) ───────────────────────────────
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    cost_ils: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (
        Index('ix_aul_agent_created', 'agent_name', 'created_at'),
        Index('ix_aul_business_created', 'business_id', 'created_at'),
    )
