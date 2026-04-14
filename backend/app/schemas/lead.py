
from pydantic import BaseModel


class LeadCreate(BaseModel):
    imported_name: str
    city: str | None = None
    category: str | None = None
    phone: str | None = None
    address: str | None = None
    website_url: str | None = None
    score: int = 0
    rating: float | None = None
    reviews_count: int | None = None
    status: str = 'imported'
    campaign_id: int | None = None
    targeting_profile_id: int | None = None


class LeadRead(LeadCreate):
    id: int
    cross_ref_score: int = 0
    cross_ref_status: str = 'pending'
    cross_ref_agents: str | None = None

    class Config:
        from_attributes = True


class LeadAssignCampaign(BaseModel):
    campaign_id: int | None = None
    targeting_profile_id: int | None = None
