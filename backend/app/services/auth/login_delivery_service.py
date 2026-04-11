from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.login_delivery_attempt import LoginDeliveryAttempt
from app.services.auth.delivery_router_service import DeliveryRouterService


class LoginDeliveryService:
    """Abstraction for future SMS/email magic-link delivery.
    V23 adds a router and richer metadata, while still staying in preview/dev mode.
    """

    def __init__(self) -> None:
        self.router = DeliveryRouterService()

    def prepare_delivery(self, db: Session, *, customer_phone: str, challenge_type: str, challenge_id: int | None, provider: str = 'preview', delivery_channel: str = 'preview', detail: str | None = None, was_rate_limited: bool = False, external_reference: str | None = None) -> LoginDeliveryAttempt:
        row = LoginDeliveryAttempt(
            customer_phone=customer_phone,
            challenge_type=challenge_type,
            provider=provider,
            delivery_channel=delivery_channel,
            status='rate_limited' if was_rate_limited else 'prepared',
            challenge_id=challenge_id,
            detail=detail,
            was_rate_limited=was_rate_limited,
            external_reference=external_reference,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def dispatch_preview(self, db: Session, *, challenge_type: str, customer_phone: str, challenge_id: int | None, payload_preview: str, channel_hint: str | None = None) -> LoginDeliveryAttempt:
        provider = self.router.choose_provider(channel_hint=channel_hint)
        result = provider.send(challenge_type=challenge_type, customer_phone=customer_phone, payload_preview=payload_preview)
        return self.prepare_delivery(
            db,
            customer_phone=customer_phone,
            challenge_type=challenge_type,
            challenge_id=challenge_id,
            provider=result.provider,
            delivery_channel=result.delivery_channel,
            detail=result.detail,
            external_reference=result.external_reference,
        )
