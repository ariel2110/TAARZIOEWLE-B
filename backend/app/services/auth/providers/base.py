from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class DeliveryProviderResult:
    provider: str
    delivery_channel: str
    ok: bool = True
    status: str = "sent"
    detail: str | None = None
    external_reference: str | None = None
    error: str | None = None
