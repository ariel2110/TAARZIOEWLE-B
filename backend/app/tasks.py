"""
tasks.py — Celery background tasks for SiteNest.

All heavy AI operations and scheduled maintenance that would block the API
server (or should run periodically) live here:

  - generate_site_task   → 4-agent AI pipeline for one business
  - batch_generate_task  → fan-out site generation for N businesses
  - followup_task        → scan sent outreach, mark followup_due / stale
  - ceo_digest_task      → regenerate the CEO brain daily digest
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


# ── Task 5: Regenerate draft site with owner change instructions ─────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.regenerate_with_note_task',
    max_retries=2,
    default_retry_delay=30,
)
def regenerate_with_note_task(self: Task, business_id: int, regeneration_note: str) -> dict:
    """
    Re-run the AI pipeline for a business, injecting the owner's change note
    into Stage 1a so GPT-4o knows exactly what to update.

    Triggered from: POST /admin/tasks/regenerate-with-note/{business_id}
    """
    logger.info(
        '[regenerate_with_note_task] business_id=%d note_len=%d',
        business_id, len(regeneration_note or ''),
    )
    try:
        from app.db.session import SessionLocal
        from app.models.business import Business
        from app.services.draft_sites.draft_site_service import DraftSiteService

        db = SessionLocal()
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                return {
                    'status': 'error', 'business_id': business_id,
                    'draft_site_id': None,
                    'message': f'Business {business_id} not found',
                }

            self.update_state(state='PROGRESS', meta={'step': 'running_ai_pipeline', 'business_id': business_id})
            draft = DraftSiteService().create_and_preview(
                db, business_id, regeneration_note=regeneration_note
            )

            if not draft:
                return {
                    'status': 'error', 'business_id': business_id,
                    'draft_site_id': None,
                    'message': 'Pipeline returned no result',
                }

            logger.info(
                '[regenerate_with_note_task] done — business_id=%d draft_id=%d',
                business_id, draft.id,
            )
            return {
                'status': 'success',
                'business_id': business_id,
                'draft_site_id': draft.id,
                'preview_url': draft.preview_url,
                'message': f'Draft regenerated for {business.name} with custom note',
            }
        finally:
            db.close()

    except Exception as exc:
        logger.error(
            '[regenerate_with_note_task] exception for business_id=%d: %s',
            business_id, exc, exc_info=True,
        )
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'business_id': business_id,
                'draft_site_id': None,
                'message': f'Pipeline failed after retries: {exc}',
            }


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


# ── Task 3: Follow-up worker ─────────────────────────────────────────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.followup_task',
    max_retries=1,
    default_retry_delay=60,
)
def followup_task(self: Task) -> dict:
    """
    Scan sent outreach messages and mark them as followup_due or stale.

    Runs from Celery Beat every day at 09:00.
    Delegates to the existing followup_worker.run() logic (single source of truth).
    """
    logger.info('[followup_task] starting')
    try:
        from app.workers.followup_worker import run as _run_followup
        _run_followup()
        return {'status': 'ok'}
    except Exception as exc:
        logger.error('[followup_task] failed: %s', exc, exc_info=True)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {'status': 'error', 'message': str(exc)}


# ── Task 4: CEO digest worker ────────────────────────────────────────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.ceo_digest_task',
    max_retries=1,
    default_retry_delay=120,
    time_limit=600,
    soft_time_limit=540,
)
def ceo_digest_task(self: Task) -> dict:
    """
    Regenerate the CEO daily digest (AI-powered summary of platform KPIs).

    Runs from Celery Beat every 6 hours.
    Delegates to ceo_digest_worker.run() — heavy LLM call, hence off-thread.
    """
    logger.info('[ceo_digest_task] starting')
    try:
        from app.workers.ceo_digest_worker import run as _run_digest
        _run_digest()
        return {'status': 'ok'}
    except Exception as exc:
        logger.error('[ceo_digest_task] failed: %s', exc, exc_info=True)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {'status': 'error', 'message': str(exc)}
