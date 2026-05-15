"""
notification_service.py — Admin notification service.

Persists admin notifications (demo viewed, payment confirmed, etc.) in the
ActivityLog table and optionally delivers them via email when delivery_mode
is set to something other than 'console'.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog
from app.core.config import settings

logger = logging.getLogger(__name__)

_NOTIFICATION_ACTIONS = {
    'demo_viewed',
    'payment_confirmed',
    'lead_auto_qualified',
    'customer_support_opened',
    'change_request_created',
    'cross_ref_manual_review',
    'cross_ref_bulk_manual_review',
}


class NotificationService:
    """Creates admin notifications backed by ActivityLog rows."""

    def notify(
        self,
        db: Session,
        *,
        event: str,
        entity_type: str,
        entity_id: int | None = None,
        summary: str,
        extra: dict | None = None,
    ) -> ActivityLog:
        """Persist the notification and deliver it based on delivery_mode."""
        entry = ActivityLog(
            actor_type='system',
            actor_id=None,
            entity_type=entity_type,
            entity_id=entity_id,
            action_type=event,
            summary=summary,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

        if settings.delivery_mode == 'console':
            logger.info('[notification] %s | %s', event, summary)
        else:
            self._try_email(event=event, summary=summary, extra=extra or {})

        return entry

    # ── helpers ───────────────────────────────────────────────────
    def _try_email(self, *, event: str, summary: str, extra: dict) -> None:
        """Send email notification; silently ignore delivery errors."""
        try:
            import smtplib
            from email.message import EmailMessage
            if not hasattr(settings, 'notification_email') or not settings.notification_email:
                return
            msg = EmailMessage()
            msg['Subject'] = f'[TAZO-WEB] {event}'
            msg['From'] = 'noreply@TAZO-WEB.site'
            msg['To'] = settings.notification_email  # type: ignore[attr-defined]
            body_lines = [f'Event: {event}', f'Details: {summary}']
            for k, v in extra.items():
                body_lines.append(f'{k}: {v}')
            body_lines.append(f'Time: {datetime.now(timezone.utc).isoformat()}')
            msg.set_content('\n'.join(body_lines))
            with smtplib.SMTP('localhost', 25, timeout=5) as smtp:
                smtp.send_message(msg)
        except Exception as exc:  # noqa: BLE001
            logger.warning('[notification] email delivery failed: %s', exc)

    def list_recent(self, db: Session, limit: int = 50) -> list[ActivityLog]:
        """Return most recent admin notifications."""
        return (
            db.query(ActivityLog)
            .filter(ActivityLog.action_type.in_(_NOTIFICATION_ACTIONS))
            .order_by(ActivityLog.id.desc())
            .limit(limit)
            .all()
        )


_notification_service = NotificationService()
