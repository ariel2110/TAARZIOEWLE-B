
from pydantic import BaseModel

class QueueSummaryItem(BaseModel):
    queue_type: str
    count: int
    label: str

class QueueEntityItem(BaseModel):
    id: int
    title: str
    subtitle: str | None = None
    priority: str = 'medium'
    queue_type: str
    linked_entity_type: str
    linked_entity_id: int
    available_actions: list[str] = []

class QueueActionRequest(BaseModel):
    action: str
    campaign_id: int | None = None
    targeting_profile_id: int | None = None
    note: str | None = None
