from pydantic import BaseModel


class TargetingProfileCreate(BaseModel):
    name: str
    city: str
    radius_km: int = 8
    category_list: list[str] = []
    min_reviews: int = 0
    min_rating: float = 0.0
    requires_no_website: bool = True
    requires_phone: bool = True
    score_threshold: int = 0


class TargetingProfileRead(TargetingProfileCreate):
    id: int
    active: bool = True

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    name: str
    targeting_profile_id: int | None = None
    status: str = 'draft'
    goals_json: dict = {}


class CampaignRead(CampaignCreate):
    id: int

    class Config:
        from_attributes = True


class TargetingSearchParams(BaseModel):
    city: str | None = None
    category: str | None = None
    min_score: int = 0
    no_website_only: bool = False
    not_contacted_only: bool = False
