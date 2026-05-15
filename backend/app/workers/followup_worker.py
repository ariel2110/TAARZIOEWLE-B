"""
followup_worker.py — Processes pending follow-up outreach tasks.

Scans OutreachMessage records that are in 'sent' status and have passed
their follow-up window, then queues them for follow-up or marks as stale.

Schedule:
    0 9 * * * cd /home/tazo-web-platform/backend && .venv/bin/python -m app.workers.followup_worker

Usage:
    python -m app.workers.followup_worker
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('followup_worker')

# Messages sent more than N days ago without a reply are candidates for follow-up
FOLLOWUP_AFTER_DAYS = 3
STALE_AFTER_DAYS = 14


def run() -> None:
    logger.info('[followup_worker] Starting at %s', datetime.now(timezone.utc).isoformat())
    try:
        from app.db.session import SessionLocal
        from app.models.outreach_message import OutreachMessage
        from app.models.activity_log import ActivityLog

        db = SessionLocal()
        now = datetime.now(timezone.utc)
        try:
            # Find messages sent but not replied within follow-up window
            followup_cutoff = now - timedelta(days=FOLLOWUP_AFTER_DAYS)
            stale_cutoff = now - timedelta(days=STALE_AFTER_DAYS)

            pending = (
                db.query(OutreachMessage)
                .filter(OutreachMessage.status.in_(['sent', 'delivered']))
                .filter(OutreachMessage.updated_at < followup_cutoff)  # type: ignore[attr-defined]
                .all()
            )

            followup_count = 0
            stale_count = 0
            for msg in pending:
                updated = getattr(msg, 'updated_at', None) or getattr(msg, 'created_at', None)
                if updated and updated.replace(tzinfo=timezone.utc) < stale_cutoff:
                    msg.status = 'stale'
                    db.add(ActivityLog(
                        actor_type='system', entity_type='outreach_message', entity_id=msg.id,
                        action_type='outreach_stale', summary=f'No reply after {STALE_AFTER_DAYS} days',
                    ))
                    stale_count += 1
                else:
                    msg.status = 'followup_due'
                    db.add(ActivityLog(
                        actor_type='system', entity_type='outreach_message', entity_id=msg.id,
                        action_type='outreach_followup_due', summary=f'Follow-up due after {FOLLOWUP_AFTER_DAYS} days',
                    ))
                    followup_count += 1

            if pending:
                db.commit()

            logger.info('[followup_worker] Processed %d: %d follow-up due, %d stale', len(pending), followup_count, stale_count)
        finally:
            db.close()
    except Exception as exc:
        logger.error('[followup_worker] Failed: %s', exc, exc_info=True)
        sys.exit(1)

    logger.info('[followup_worker] Done.')


if __name__ == '__main__':
    run()

