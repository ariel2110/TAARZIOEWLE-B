"""
celery_app.py — Celery application instance for TAZO-WEB.

Workers run heavy AI tasks (site generation, batch outreach) asynchronously
so the FastAPI server can return immediately and stay responsive.

Queue: 'TAZO-WEB' — all tasks use this single queue.
Broker/Backend: Redis (configured via env vars CELERY_BROKER_URL / CELERY_RESULT_BACKEND).

Fallback when Redis is unavailable:
  CELERY_ALWAYS_EAGER=true  → tasks run synchronously in-process (for tests/dev).
"""
from __future__ import annotations

import os

from celery.schedules import crontab
from celery import Celery

_BROKER = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery(
    'TAZO_WEB_tasks',
    broker=_BROKER,
    backend=_BACKEND,
    include=['app.tasks'],          # auto-discover tasks module
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Jerusalem',
    enable_utc=True,
    task_default_queue='TAZO-WEB',
    task_routes={'app.tasks.*': {'queue': 'TAZO-WEB'}},
    # Keep results for 24 hours so the frontend can poll
    result_expires=86_400,
    # Retry tasks on connection error (Redis temporarily unavailable)
    broker_connection_retry_on_startup=True,
    # Dev/test: run tasks inline when CELERY_ALWAYS_EAGER=true
    task_always_eager=os.getenv('CELERY_ALWAYS_EAGER', 'false').lower() == 'true',
    task_eager_propagates=True,
    # Hard time limit per task: 5 minutes
    task_time_limit=300,
    task_soft_time_limit=270,
    # Worker settings
    worker_prefetch_multiplier=1,   # one task at a time per worker process
    task_acks_late=True,            # ack only after task completes
    # ── Celery Beat periodic schedule ────────────────────────────────────────
    # Requires running: celery -A app.core.celery_app beat --loglevel=info
    beat_schedule={
        'followup-daily-9am': {
            'task': 'app.tasks.followup_task',
            'schedule': 60 * 60 * 24,   # every 24 hours
            'options': {'queue': 'TAZO-WEB'},
        },
        'ceo-digest-every-6h': {
            'task': 'app.tasks.ceo_digest_task',
            'schedule': 60 * 60 * 6,    # every 6 hours
            'options': {'queue': 'TAZO-WEB'},
        },
        'facebook-token-refresh-every-50-days': {
            # Runs at 09:00 every 50 days — safely before the 60-day token expiry.
            # day_of_week='*', day_of_month='*/50' is not directly expressible in
            # crontab, so we use a timedelta of 50 days (4_320_000 seconds).
            'task': 'app.tasks.facebook_token_refresh_task',
            'schedule': 60 * 60 * 24 * 50,   # every 50 days in seconds
            'options': {'queue': 'TAZO-WEB'},
        },
    },
)
