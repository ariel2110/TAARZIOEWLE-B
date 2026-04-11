from pydantic import BaseModel


class PaymentCreate(BaseModel):
    business_id: int | None = None
    amount: int
    provider: str = 'manual'
    internal_status: str = 'pending'
    external_reference: str | None = None


class PaymentRead(PaymentCreate):
    id: int

    class Config:
        from_attributes = True
