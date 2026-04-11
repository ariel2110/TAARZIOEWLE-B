"""
celery_app.py — Celery application instance for SiteNest.

Workers run heavy AI tasks (site generation, batch outreach) asynchronously
so the FastAPI server can return immediately and stay responsive.

Queue: 'sitenest' — all tasks use this single queue.
Broker/Backend: Redis (configured via env vars CELERY_BROKER_URL / CELERY_RESULT_BACKEND).

Fallback when Redis is unavailable:
  CELERY_ALWAYS_EAGER=true  → tasks run synchronously in-process (for tests/dev).
"""
from __future__ import annotations

import os

from celery import Celery

_BROKER = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery(
    'sitenest_tasks',
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
    task_default_queue='sitenest',
    task_routes={'app.tasks.*': {'queue': 'sitenest'}},
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
)
