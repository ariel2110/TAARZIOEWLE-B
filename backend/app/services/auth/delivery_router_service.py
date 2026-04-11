from __future__ import annotations
from app.services.auth.providers.preview_provider import PreviewDeliveryProvider
from app.services.auth.providers.console_provider import ConsoleDeliveryProvider

class DeliveryRouterService:
    def __init__(self) -> None:
        self.preview_provider = PreviewDeliveryProvider()
        self.console_provider = ConsoleDeliveryProvider()

    def choose_provider(self, *, channel_hint: str | None = None):
        if channel_hint == 'console':
            return self.console_provider
        return self.preview_provider
