from pydantic import BaseModel


class DraftSiteCreate(BaseModel):
    business_id: int
    site_title: str
    status: str = 'draft'
    primary_color: str | None = None
    hero_title: str | None = None
    about_text: str | None = None


class DraftSiteRead(DraftSiteCreate):
    id: int
    preview_url: str | None = None
    is_demo: bool
    noindex: bool

    class Config:
        from_attributes = True
