"""
ceo_digest_worker.py — Generates and caches the daily CEO digest.

This worker is designed to be run periodically (e.g., every 6 hours)
via a cron job or systemd timer:

    # /etc/systemd/system/sitenest-ceo-digest.timer
    [Timer]
    OnCalendar=*-*-* 06:00:00
    Persistent=true

    # /etc/systemd/system/sitenest-ceo-digest.service
    [Service]
    Type=oneshot
    WorkingDirectory=/home/site-nest-platform/backend
    ExecStart=.venv/bin/python -m app.workers.ceo_digest_worker

Or via cron:
    0 6,12,18,0 * * * cd /home/site-nest-platform/backend && .venv/bin/python -m app.workers.ceo_digest_worker

Usage:
    python -m app.workers.ceo_digest_worker
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger('ceo_digest_worker')


def run() -> None:
    logger.info('[ceo_digest_worker] Starting at %s', datetime.now(timezone.utc).isoformat())
    try:
        from app.db.session import SessionLocal
        from app.services.ceo_agent.ceo_brain_service import CEOBrainService

        db = SessionLocal()
        try:
            svc = CEOBrainService()
            digest = svc.get_daily_digest(db)
            logger.info('[ceo_digest_worker] Digest generated: %s...', str(digest)[:120])
        finally:
            db.close()
    except Exception as exc:
        logger.error('[ceo_digest_worker] Failed: %s', exc, exc_info=True)
        sys.exit(1)

    logger.info('[ceo_digest_worker] Done.')


if __name__ == '__main__':
    run()

