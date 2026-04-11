from __future__ import annotations
from .base import DeliveryProviderResult

class PreviewDeliveryProvider:
    provider_name = 'preview'
    delivery_channel = 'preview'

    def send(self, *, challenge_type: str, customer_phone: str, payload_preview: str) -> DeliveryProviderResult:
        return DeliveryProviderResult(
            provider=self.provider_name,
            delivery_channel=self.delivery_channel,
            status='prepared',
            detail=f'Preview delivery prepared for {challenge_type} to {customer_phone}: {payload_preview}',
        )
