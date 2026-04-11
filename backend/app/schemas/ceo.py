
from pydantic import BaseModel


class CEOReport(BaseModel):
    executive_summary: str
    recommended_actions: list[str]
    approval_queue_count: int = 0
    payments_pending: int = 0
    expiring_drafts: int = 0
    outreach_ready_count: int = 0
    qualified_leads: int = 0
    open_security_alerts: int = 0
    high_security_alerts: int = 0
    pressure_notes: list[str] = []


class CEOHealth(BaseModel):
    overall_status: str
    database_ok: bool = True
    drivers: list[str] = []


class CEONoteCreate(BaseModel):
    note: str


class CEOTaskCreate(BaseModel):
    source: str
    title: str
    note: str | None = None


class GrokThinkRequest(BaseModel):
    message: str | None = None  # Optional message from Ariel; if None, Grok does an autonomous analysis


class GrokExecuteRequest(BaseModel):
    action_type: str
    target_component: str = ""
    new_value: str = ""


class GrokExecuteResponse(BaseModel):
    status: str           # "success" | "error" | "acknowledged" | "pending_approval"
    message: str
