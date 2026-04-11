from pydantic import BaseModel


class CustomerOverviewResponse(BaseModel):
    account: dict
    business: dict
    sites: list[dict]
    recent_payments: list[dict]


class CustomerBasicEditCreate(BaseModel):
    field_key: str
    new_value: str


class CustomerChangeRequestCreate(BaseModel):
    request_type: str = 'general'
    title: str
    description: str


class CustomerSupportCreate(BaseModel):
    subject: str
    message: str
