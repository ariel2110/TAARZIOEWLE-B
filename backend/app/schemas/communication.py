
from pydantic import BaseModel


class WhatsAppLaunchRequest(BaseModel):
    phone: str
    message: str


class WhatsAppBusinessLaunchRequest(BaseModel):
    business_id: int
    draft_site_id: int | None = None
    message_template_key: str = 'initial_outreach_v1'
    ab_campaign_id: str | None = None
    ab_variant: str | None = None


class MarkOutreachSentRequest(BaseModel):
    status: str = 'sent'


class RescheduleFollowupRequest(BaseModel):
    note: str | None = None


class WhatsAppLaunchResponse(BaseModel):
    normalized_phone: str
    whatsapp_url: str
    message: str
    outreach_id: int | None = None
