
from pydantic import BaseModel


class ApprovalItemRead(BaseModel):
    id: int
    approval_type: str
    title: str
    summary: str | None = None
    status: str
    approval_required: bool

    class Config:
        from_attributes = True


class ApprovalItemDetail(ApprovalItemRead):
    rationale: str | None = None
    evidence_json: dict | None = None
    before_json: dict | None = None
    after_json: dict | None = None
    confidence_score: float | None = None
    payload_json: dict | None = None
