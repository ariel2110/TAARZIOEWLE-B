"""Internal voice bot endpoints — used by the voice-stream microservice.

GET  /api/v1/internal/voice/caller-memory?phone=  → past calls + orders summary
POST /api/v1/internal/voice/save-call-log         → persist transcript + summary
"""
from __future__ import annotations

import json
import logging
import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.customer_account import CustomerAccount
from app.models.voice_call_log import VoiceCallLog

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/internal/voice", tags=["internal-voice"])


def _clean_phone(raw: str) -> str:
    p = re.sub(r"\D", "", raw or "")
    if p.startswith("0") and len(p) == 10:
        p = "972" + p[1:]
    return p


@router.get("/caller-memory")
def get_caller_memory(phone: str, db: Session = Depends(get_db)):
    """Return past call summaries and recent order activity for a caller phone."""
    clean = _clean_phone(phone)

    # Last 5 calls — most recent first
    logs = (
        db.query(VoiceCallLog)
        .filter(VoiceCallLog.caller_phone.in_([phone, clean, "0" + clean[3:] if clean.startswith("972") else ""]))
        .order_by(VoiceCallLog.created_at.desc())
        .limit(5)
        .all()
    )

    past_parts = []
    for log in logs:
        if log.summary:
            ts = log.created_at.strftime("%d/%m/%Y") if log.created_at else "?"
            past_parts.append(f"[{ts}] {log.summary}")
    past_calls_summary = "\n".join(past_parts) if past_parts else ""

    # Recent orders from tazo-web (CustomerAccount → orders if available)
    orders_summary = ""
    try:
        acct = (
            db.query(CustomerAccount)
            .filter(CustomerAccount.phone.in_([phone, clean]))
            .first()
        )
        if acct:
            # Could expand to query actual order table here
            orders_summary = f"לקוח: {acct.full_name or ''}, עסק: {acct.business_name or ''}"
    except Exception:
        pass

    return {
        "past_calls_summary": past_calls_summary,
        "orders_summary": orders_summary,
        "call_count": len(logs),
    }


class SaveCallLogIn(BaseModel):
    call_sid: str
    caller_phone: str
    caller_name: str | None = None
    business_name: str | None = None
    user_role: str | None = None
    language: str = "he"
    transcript: str | None = None
    summary: str | None = None
    duration_turns: int = 0
    link_sent: bool = False
    escalated: bool = False
    call_outcome: str | None = None


@router.post("/save-call-log")
def save_call_log(body: SaveCallLogIn, db: Session = Depends(get_db)):
    """Persist a completed voice call transcript and summary."""
    clean = _clean_phone(body.caller_phone)

    existing = db.query(VoiceCallLog).filter(VoiceCallLog.call_sid == body.call_sid).first()
    if existing:
        return {"ok": True, "updated": True}

    log = VoiceCallLog(
        call_sid=body.call_sid,
        caller_phone=clean or body.caller_phone,
        caller_name=body.caller_name,
        business_name=body.business_name,
        user_role=body.user_role,
        language=body.language,
        transcript=body.transcript,
        summary=body.summary,
        duration_turns=body.duration_turns,
        link_sent=body.link_sent,
        escalated=body.escalated,
        call_outcome=body.call_outcome,
    )
    db.add(log)
    db.commit()
    logger.info("[voice-memory] saved call %s (%d turns)", body.call_sid[:8], body.duration_turns)
    return {"ok": True, "updated": False}
