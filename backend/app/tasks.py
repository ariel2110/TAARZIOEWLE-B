"""
tasks.py — Celery background tasks for SiteNest.

All heavy AI operations that would block the API server run here:
  - generate_site_task  → runs the 4-agent pipeline for a business
  - batch_outreach_task → queues outreach messages for a list of business IDs

Tasks write progress updates to their own Celery result backend so the
frontend can poll /admin/tasks/{task_id}/status.
"""
from __future__ import annotations

import logging
from typing import Any

from celery import Task

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


# ── Base task with common error handling ─────────────────────────────────────

class _BaseTask(Task):
    abstract = True

    def on_failure(self, exc: Exception, task_id: str, args: Any, kwargs: Any, einfo: Any) -> None:
        logger.error('[task:%s] failed — %s', task_id, exc, exc_info=True)


# ── Task 1: Generate draft site for a business ───────────────────────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.generate_site_task',
    max_retries=2,
    default_retry_delay=30,
)
def generate_site_task(self: Task, business_id: int) -> dict:
    """
    Run the 4-agent AI pipeline to generate a draft site for a business.

    Triggered from: POST /admin/tasks/generate-site/{business_id}
    Poll status at: GET  /admin/tasks/{task_id}/status

    Returns:
        {
            "status": "success" | "error",
            "business_id": int,
            "draft_site_id": int | None,
            "message": str,
        }
    """
    logger.info('[generate_site_task] starting for business_id=%d', business_id)

    try:
        from app.db.session import SessionLocal
        from app.models.business import Business
        from app.services.draft_sites.draft_site_service import DraftSiteService

        db = SessionLocal()
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                return {'status': 'error', 'business_id': business_id, 'draft_site_id': None, 'message': f'Business {business_id} not found'}

            # Run the full pipeline via DraftSiteService (creates/reuses draft, runs AI, writes HTML file)
            self.update_state(state='PROGRESS', meta={'step': 'running_ai_pipeline', 'business_id': business_id})
            draft = DraftSiteService().create_and_preview(db, business_id)

            if not draft:
                return {'status': 'error', 'business_id': business_id, 'draft_site_id': None, 'message': 'Pipeline returned no result'}

            logger.info('[generate_site_task] done — business_id=%d draft_id=%d', business_id, draft.id)
            return {
                'status': 'success',
                'business_id': business_id,
                'draft_site_id': draft.id,
                'preview_url': draft.preview_url,
                'message': f'Draft site generated successfully for {business.name}',
            }

        finally:
            db.close()

    except Exception as exc:
        logger.error('[generate_site_task] exception for business_id=%d: %s', business_id, exc, exc_info=True)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'business_id': business_id,
                'draft_site_id': None,
                'message': f'Pipeline failed after retries: {exc}',
            }


# ── Task 2: Batch site generation for multiple businesses ────────────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.batch_generate_task',
    max_retries=0,
)
def batch_generate_task(self: Task, business_ids: list[int]) -> dict:
    """
    Spawn individual generate_site_task for each business_id in the list.
    Returns immediately with sub-task IDs for tracking.
    """
    sub_tasks = []
    for bid in business_ids:
        task = generate_site_task.delay(bid)
        sub_tasks.append({'business_id': bid, 'task_id': task.id})
    return {'status': 'dispatched', 'count': len(sub_tasks), 'tasks': sub_tasks}
