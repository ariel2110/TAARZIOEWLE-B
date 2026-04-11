from __future__ import annotations
from dataclasses import dataclass

@dataclass
class DeliveryProviderResult:
    provider: str
    delivery_channel: str
    status: str
    detail: str | None = None
    external_reference: str | None = None
