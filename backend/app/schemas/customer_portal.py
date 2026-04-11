from pydantic import BaseModel


class CustomerLoginRequest(BaseModel):
    phone: str
    password: str


class CustomerLoginResponse(BaseModel):
    access_token: str
    customer_account_id: int
    business_id: int
    must_change_password: bool


class CustomerMeResponse(BaseModel):
    customer_account_id: int
    business_id: int
    active_site_id: int | None = None
    draft_site_id: int | None = None
    phone: str
    email: str | None = None
    contact_name: str | None = None
    must_change_password: bool
    package_name: str | None = None


class CustomerChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class CustomerCreateRequest(BaseModel):
    business_id: int
    phone: str
    email: str | None = None
    contact_name: str | None = None
    draft_site_id: int | None = None
    active_site_id: int | None = None
    package_name: str | None = None


class CustomerCreateResponse(BaseModel):
    customer_account_id: int
    business_id: int
    phone: str
    temporary_password: str
    must_change_password: bool
