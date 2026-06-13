from __future__ import annotations
from app.core.config import settings
from app.services.auth.providers.preview_provider import PreviewDeliveryProvider
from app.services.auth.providers.console_provider import ConsoleDeliveryProvider
from app.services.auth.providers.twilio_voice_provider import TwilioVoiceDeliveryProvider
from app.services.auth.providers.twilio_sms_provider import TwilioSmsDeliveryProvider

class DeliveryRouterService:
    def __init__(self) -> None:
        self.preview_provider = PreviewDeliveryProvider()
        self.console_provider = ConsoleDeliveryProvider()
        self.voice_provider = TwilioVoiceDeliveryProvider()
        self.sms_provider = TwilioSmsDeliveryProvider()

    def choose_provider(self, *, channel_hint: str | None = None):
        if channel_hint == 'preview':
            return self.preview_provider
        if channel_hint == 'console' or settings.delivery_mode == 'console':
            return self.console_provider
        if channel_hint == 'sms':
            return self.sms_provider
        # production: route by configured delivery mode
        if settings.delivery_mode == 'voice':
            return self.voice_provider
        if settings.delivery_mode == 'sms':
            return self.sms_provider
        if settings.delivery_mode == 'whatsapp':
            return self.console_provider  # placeholder until WhatsApp provider is wired
        return self.console_provider  # safe default — always log, never silently drop

