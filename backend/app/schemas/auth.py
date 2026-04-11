from pydantic import BaseModel, EmailStr


class CurrentAdminResponse(BaseModel):
    email: EmailStr
    full_name: str
    role: str
    auth_mode: str


class GoogleAuthStartResponse(BaseModel):
    auth_url: str
    enabled: bool


class DevLoginRequest(BaseModel):
    email: EmailStr
    full_name: str | None = 'Admin User'
    admin_token: str


class DevLoginResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    email: EmailStr
    role: str
