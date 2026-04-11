
from pydantic import BaseModel


class BusinessCreate(BaseModel):
    name: str
    city: str | None = None
    category: str | None = None
    status: str = 'new'
    phone: str | None = None
    address: str | None = None
    lead_id: int | None = None
    campaign_id: int | None = None
    targeting_profile_id: int | None = None


class BusinessRead(BusinessCreate):
    id: int

    class Config:
        from_attributes = True
