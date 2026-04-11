"""
WhatsApp webhook endpoint.

Receives delivery status updates and inbound messages from the WhatsApp
Business API (e.g., 360dialog, Twilio, or Meta Cloud API) and updates
OutreachMessage records accordingly.

We use HMAC-SHA256 signature verification when WHATSAPP_WEBHOOK_SECRET is set.
"""
from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.outreach_message import OutreachMessage
from app.models.activity_log import ActivityLog

router = APIRouter(prefix='/webhooks/whatsapp', tags=['webhooks'])
logger = logging.getLogger(__name__)

# Map provider delivery statuses → our internal status
_DELIVERY_MAP: dict[str, str] = {
    'sent': 'sent',
    'delivered': 'delivered',
    'read': 'read',
    'failed': 'failed',
    'undelivered': 'failed',
}


def _verify_signature(request_body: bytes, signature_header: str | None) -> bool:
    """Verify HMAC-SHA256 signature from WhatsApp webhook (optional)."""
    secret = getattr(settings, 'whatsapp_webhook_secret', None)
    if not secret:
        return True  # No secret configured — accept all (dev mode)
    if not signature_header:
        return False
    expected = hmac.new(secret.encode(), request_body, hashlib.sha256).hexdigest()
    provided = signature_header.removeprefix('sha256=')
    return hmac.compare_digest(expected, provided)


@router.get('')
def webhook_verify(request: Request):
    """
    Meta Cloud API / 360dialog webhook verification (GET challenge).
    Handles: hub.mode=subscribe, hub.verify_token, hub.challenge
    """
    params = request.query_params
    token = getattr(settings, 'whatsapp_verify_token', None) or 'sitenest-verify'
    if params.get('hub.mode') == 'subscribe' and params.get('hub.verify_token') == token:
        return int(params.get('hub.challenge', '0'))
    raise HTTPException(status_code=403, detail='Forbidden')


@router.post('')
async def webhook_receive(request: Request, db: Session = Depends(get_db)):
    """
    Receive WhatsApp delivery status or inbound message events.

    Supports both Meta Cloud API format and 360dialog format.
    """
    body = await request.body()
    sig = request.headers.get('x-hub-signature-256') or request.headers.get('x-webhook-signature')
    if not _verify_signature(body, sig):
        raise HTTPException(status_code=401, detail='Invalid signature')

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail='Invalid JSON')

    processed = 0

    # ── Meta Cloud API format ────────────────────────────────────
    for entry in payload.get('entry', []):
        for change in entry.get('changes', []):
            value = change.get('value', {})
            # Delivery statuses
            for status_evt in value.get('statuses', []):
                _handle_status(db, status_evt)
                processed += 1
            # Inbound messages
            for msg in value.get('messages', []):
                _handle_inbound(db, msg, value.get('metadata', {}))
                processed += 1

    # ── 360dialog format ────────────────────────────────────────
    for status_evt in payload.get('statuses', []):
        _handle_status(db, status_evt)
        processed += 1
    for msg in payload.get('messages', []):
        _handle_inbound(db, msg, {})
        processed += 1

    logger.info('[whatsapp_webhook] processed %d events', processed)
    return {'ok': True, 'processed': processed}


# ── Internal handlers ────────────────────────────────────────────────

def _handle_status(db: Session, status_evt: dict) -> None:
    """Update OutreachMessage status based on delivery status event."""
    wa_msg_id: str = status_evt.get('id', '')
    raw_status: str = status_evt.get('status', '')
    internal_status = _DELIVERY_MAP.get(raw_status, raw_status)

    # Try to find matching outreach message by WA message id stored in notes
    msg = (
        db.query(OutreachMessage)
        .filter(OutreachMessage.status.notin_(['read', 'replied']))
        .filter(OutreachMessage.channel == 'whatsapp')
        .order_by(OutreachMessage.id.desc())
        .filter(OutreachMessage.outbound_target.is_not(None))
        .first()
    )

    recipient_phone: str = status_evt.get('recipient_id', '')
    if recipient_phone:
        msg = (
            db.query(OutreachMessage)
            .filter(OutreachMessage.outbound_target == recipient_phone)
            .filter(OutreachMessage.channel == 'whatsapp')
            .order_by(OutreachMessage.id.desc())
            .first()
        )

    if msg and internal_status in _DELIVERY_MAP.values():
        msg.status = internal_status
        db.add(ActivityLog(
            actor_type='webhook',
            entity_type='outreach_message',
            entity_id=msg.id,
            action_type=f'whatsapp_{internal_status}',
            summary=f'WA delivery: {raw_status} → {internal_status} (wa_id={wa_msg_id})',
        ))
        db.commit()


def _handle_inbound(db: Session, msg: dict, metadata: dict) -> None:
    """Handle an inbound WhatsApp reply message."""
    from_phone: str = msg.get('from', '')
    text = ''
    if msg.get('type') == 'text':
        text = msg.get('text', {}).get('body', '')
    elif msg.get('type') == 'button':
        text = msg.get('button', {}).get('text', '')

    # Mark matching outreach as replied
    if from_phone:
        outreach = (
            db.query(OutreachMessage)
            .filter(OutreachMessage.outbound_target == from_phone)
            .filter(OutreachMessage.channel == 'whatsapp')
            .order_by(OutreachMessage.id.desc())
            .first()
        )
        if outreach:
            outreach.status = 'replied'
            db.add(ActivityLog(
                actor_type='webhook',
                entity_type='outreach_message',
                entity_id=outreach.id,
                action_type='whatsapp_replied',
                summary=f'Inbound reply from {from_phone}: {text[:120]}',
            ))
            db.commit()

        # Also fire admin notification
        try:
            from app.services.common.notification_service import NotificationService
            NotificationService().notify(
                db,
                event='whatsapp_reply_received',
                entity_type='outreach_message',
                entity_id=outreach.id if outreach else None,
                summary=f'WhatsApp reply from {from_phone}: {text[:120]}',
                extra={'from': from_phone, 'text': text[:120]},
            )
        except Exception:  # noqa: BLE001
            pass
