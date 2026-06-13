"""Persistent log of AI voice call conversations.

Stores per-call transcripts so the bot can recall past interactions
and greet returning callers by name with relevant context.
"""
from sqlalchemy import String, Text, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.models.mixins import TimestampMixin


class VoiceCallLog(Base, TimestampMixin):
    __tablename__ = 'voice_call_logs'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    call_sid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    caller_phone: Mapped[str] = mapped_column(String(50), index=True)
    language: Mapped[str] = mapped_column(String(8), default='he')

    # Caller identity at time of call
    caller_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    business_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Conversation transcript (JSON list of {role, content})
    transcript: Mapped[str | None] = mapped_column(Text(), nullable=True)
    # Summary generated at call end for quick context on next call
    summary: Mapped[str | None] = mapped_column(Text(), nullable=True)

    # Call metadata
    duration_turns: Mapped[int] = mapped_column(Integer, default=0)
    link_sent: Mapped[bool] = mapped_column(default=False)
    escalated: Mapped[bool] = mapped_column(default=False)
    call_outcome: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # e.g. 'completed', 'hung_up', 'escalated', 'link_sent'
