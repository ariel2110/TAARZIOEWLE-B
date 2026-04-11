from __future__ import annotations
from .base import DeliveryProviderResult

class ConsoleDeliveryProvider:
    provider_name = 'console'
    delivery_channel = 'console'

    def send(self, *, challenge_type: str, customer_phone: str, payload_preview: str) -> DeliveryProviderResult:
        print(f"[ConsoleDeliveryProvider] {challenge_type} -> {customer_phone}: {payload_preview}")
        return DeliveryProviderResult(
            provider=self.provider_name,
            delivery_channel=self.delivery_channel,
            status='prepared',
            detail=f'Console delivery prepared for {challenge_type} to {customer_phone}',
        )
