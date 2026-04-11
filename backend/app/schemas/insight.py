from datetime import datetime
from pydantic import BaseModel


class InsightRead(BaseModel):
    id: int
    insight_type: str
    title: str
    summary: str
    confidence_score: float | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
