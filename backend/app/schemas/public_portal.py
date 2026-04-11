
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class HomeContentResponse(BaseModel):
    title: str
    subtitle: str
    admin_email: EmailStr
    admin_name: str
    monthly_demo_limit: int
    features: list[str]
    steps: list[str]
    faq: list[dict]

class IntakePreviewRequest(BaseModel):
    business_name: str = Field(min_length=2)
    city: Optional[str] = None
    category: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website_url: Optional[str] = None
    facebook_url: Optional[str] = None
    instagram_url: Optional[str] = None
    contact_name: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    customer_phone: Optional[str] = None

class IntakePreviewResponse(BaseModel):
    business_name: str
    normalized_city: str | None
    normalized_category: str | None
    pulled_fields: dict
    missing_fields: list[str]
    readiness_score: int
    monthly_demo_limit: int
    current_month_count: int
    can_request_demo_site: bool
    next_step: str
    suggested_improvements: list[str]
    strengths: list[str]

class PublicLoginOptionsResponse(BaseModel):
    admin_email: EmailStr
    customer_login_methods: list[str]
    customer_default_onboarding: str

class DemoRequestAvailabilityResponse(BaseModel):
    customer_phone: str | None
    package_name: str | None = None
    monthly_demo_limit: int
    current_month_count: int
    remaining_demo_requests: int
    can_request_demo_site: bool
    policy_note: str | None = None

class PublicRequestDemoRequest(IntakePreviewRequest):
    create_customer_account: bool = True
    package_name: str | None = 'Demo'

class PublicRequestDemoResponse(BaseModel):
    ok: bool
    message: str
    lead_id: int
    business_id: int
    customer_account_id: int | None
    temp_password: str | None
    demo_limit_remaining: int
    next_step: str
    created_new_lead: bool = True
    created_new_business: bool = True
    reused_existing_customer: bool = False
    dedup_reason: str | None = None
    onboarding_state: str = "demo_requested"
    package_name: str | None = None
    provisioning_decision_summary: str | None = None


class DemoRequestStatusItem(BaseModel):
    id: int
    customer_phone: str
    business_name: str
    city: str | None
    category: str | None
    status: str
    onboarding_state: str
    lead_id: int | None
    business_id: int | None
    customer_account_id: int | None
    dedup_reason: str | None
    package_name_snapshot: str | None = None
    previous_state: str | None = None
    next_action: str | None = None

class DemoRequestStatusResponse(BaseModel):
    items: list[DemoRequestStatusItem]
    total: int


class PublicStatusSummaryResponse(BaseModel):
    customer_phone: str | None
    package_name: str | None = None
    current_state: str | None = None
    last_business_id: int | None = None
    last_customer_account_id: int | None = None
    monthly_demo_limit: int
    current_month_count: int
    remaining_demo_requests: int
    latest_next_action: str | None = None
    history_count: int


class PackagePlanResponse(BaseModel):
    name: str
    monthly_demo_limit: int
    description: str | None = None
    is_default: bool = False
    is_active: bool = True
    customer_portal_enabled: bool = True
    requires_contact_verification: bool = False
    billing_mode: str = 'demo'


class PublicRequestMagicLinkRequest(BaseModel):
    customer_phone: str
    business_name: str | None = None


class PublicRequestMagicLinkResponse(BaseModel):
    ok: bool
    customer_phone: str
    onboarding_state: str | None = None
    token_preview: str
    expires_in_minutes: int
    next_step: str
    challenge_id: int | None = None
    delivery_status: str | None = None
    rate_limit_remaining_hint: int | None = None


class DemoCompareResponse(BaseModel):
    customer_phone: str | None
    availability: DemoRequestAvailabilityResponse
    summary: PublicStatusSummaryResponse
    recent_items: list[DemoRequestStatusItem]


class PublicRequestOtpRequest(BaseModel):
    customer_phone: str
    business_name: str | None = None


class PublicRequestOtpResponse(BaseModel):
    ok: bool
    customer_phone: str
    onboarding_state: str | None = None
    otp_preview: str
    expires_in_minutes: int
    next_step: str
    challenge_id: int | None = None
    delivery_status: str | None = None
    rate_limit_remaining_hint: int | None = None


class PublicVerifyOtpRequest(BaseModel):
    customer_phone: str
    code: str


class PublicVerifyOtpResponse(BaseModel):
    ok: bool
    customer_phone: str
    customer_account_id: int | None = None
    access_token: str | None = None


class PublicConsumeMagicLinkResponse(BaseModel):
    ok: bool
    customer_phone: str
    customer_account_id: int | None = None
    access_token: str | None = None
