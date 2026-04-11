from pydantic import BaseModel
from typing import Any
from datetime import datetime


class FeedbackCreate(BaseModel):
    target_type: str
    target_id: int | None = None
    context_type: str | None = None
    quick_rating: str = 'needs_improvement'
    open_feedback: str | None = None
    metadata_json: dict[str, Any] | None = None


class FeedbackRead(BaseModel):
    id: int
    target_type: str
    target_id: int | None = None
    context_type: str | None = None
    quick_rating: str
    open_feedback: str | None = None
    feedback_status: str
    analysis_category: str | None = None
    suggested_scope: str | None = None
    ceo_understanding: str | None = None
    ceo_response: str | None = None
    action_hint: str | None = None
    preference_candidate: bool
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
