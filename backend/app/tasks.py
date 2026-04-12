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


# ── Task 5: Inbound Magic Portal — customer-initiated full build ─────────────

@celery_app.task(
    base=_BaseTask,
    bind=True,
    name='app.tasks.inbound_build_task',
    max_retries=1,
    default_retry_delay=30,
    time_limit=480,
    soft_time_limit=450,
)
def inbound_build_task(self: Task, business_id: int) -> dict:
    """
    Full AI pipeline triggered by a public inbound request (Magic Portal).

    Progress states emitted for frontend polling:
      scouting   → fetching Maps + social data
      scouted    → data ready; frontend shows phone-capture wall
      building   → Claude HTML generation in progress
      done       → draft ready

    Returns:
        {"status": "success"|"error", "preview_url": str, "draft_site_id": int}
    """
    logger.info('[inbound_build_task] starting for business_id=%d', business_id)
    try:
        import json as _json
        from app.db.session import SessionLocal
        from app.models.business import Business
        from app.models.draft_site import DraftSite
        from app.services.draft_sites.draft_site_service import DraftSiteService

        db = SessionLocal()
        try:
            business = db.query(Business).filter(Business.id == business_id).first()
            if not business:
                return {'status': 'error', 'business_id': business_id, 'message': f'Business {business_id} not found'}

            svc = DraftSiteService()

            # ── Stage 0 prep: get or create draft ────────────────────────────
            self.update_state(state='PROGRESS', meta={
                'step': 'scouting', 'percent': 8,
                'label': 'שואב דירוגים וביקורות מגוגל מפות...',
            })
            existing = db.query(DraftSite).filter(DraftSite.business_id == business_id).first()
            draft = existing or svc.create_for_business(db, business_id)
            if not draft:
                return {'status': 'error', 'business_id': business_id, 'message': 'Could not create draft'}

            # ── Stage 0 enrichment context (reads cache — fast) ───────────────
            enrichment = svc._build_enriched_context(db, draft)

            self.update_state(state='PROGRESS', meta={
                'step': 'social', 'percent': 22,
                'label': 'מאתר חשבון אינסטגרם וטיקטוק שלך...',
            })

            # ── Run social discovery ──────────────────────────────────────────
            from app.services.generator.autosite_pipeline_service import AutoSitePipelineService
            pipeline = AutoSitePipelineService()
            social = pipeline._stage0_social_discovery(enrichment)
            enrichment = {**enrichment, '_social': social}

            self.update_state(state='PROGRESS', meta={
                'step': 'scouted', 'percent': 40,
                'label': 'מצאנו הכל! מנתח שירותים מובילים מתוך איזי...',
            })

            # ── Stage 1a: GPT content generation ─────────────────────────────
            self.update_state(state='PROGRESS', meta={
                'step': 'content', 'percent': 55,
                'label': 'ה-AI מנתח ומבין את העסק שלך...',
            })
            raw_str = _json.dumps({
                'name': enrichment.get('name', business.name),
                'city': enrichment.get('city', business.city or ''),
                'category': enrichment.get('category', business.category or ''),
                'phone': enrichment.get('phone', business.phone or ''),
                'address': enrichment.get('address', business.address or ''),
                'rating': enrichment.get('rating'),
                'reviews_count': enrichment.get('reviews_count', 0),
                'website': enrichment.get('website', ''),
                'top_review': enrichment.get('top_review', ''),
                'opening_hours': enrichment.get('opening_hours', []),
            }, ensure_ascii=False)

            content = pipeline._stage1a_content(raw_str, social=social)

            # ── Stage 1b: Gemini design ───────────────────────────────────────
            self.update_state(state='PROGRESS', meta={
                'step': 'designing', 'percent': 68,
                'label': 'מעצב לפי צבעי המותג שלך...',
            })
            design = pipeline._stage1b_design(raw_str)

            # ── Stage 2: Claude HTML ──────────────────────────────────────────
            self.update_state(state='PROGRESS', meta={
                'step': 'building', 'percent': 80,
                'label': 'ה-AI בונה כעת את האתר שלך...',
            })
            html = pipeline._stage2_build(content, design, enrichment) if content else None

            if not html:
                # Fallback to standard DraftSiteService if custom pipeline failed
                result_draft = svc.generate_preview(db, draft.id)
            else:
                # Save HTML to draft
                from app.services.draft_sites.draft_site_service import DraftSiteService as _DSS
                import os
                draft.html_content = html
                draft.status = 'preview_ready'
                static_dir = os.path.join(os.path.dirname(__file__), 'static_sites', 'drafts')
                os.makedirs(static_dir, exist_ok=True)
                html_path = os.path.join(static_dir, f'draft_{draft.id}.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                draft.preview_url = f'/static/drafts/draft_{draft.id}.html'
                db.commit()
                result_draft = draft

            if not result_draft:
                return {'status': 'error', 'business_id': business_id, 'message': 'Pipeline returned no result'}

            self.update_state(state='PROGRESS', meta={
                'step': 'done', 'percent': 100,
                'label': '🎉 האתר מוכן!',
            })

            from app.services.public.site_domain_service import build_draft_public_url
            public_url = build_draft_public_url(result_draft.id, business.name)

            logger.info('[inbound_build_task] done — business_id=%d draft_id=%d', business_id, result_draft.id)
            return {
                'status': 'success',
                'business_id': business_id,
                'draft_site_id': result_draft.id,
                'preview_url': result_draft.preview_url,
                'public_url': public_url,
                'message': 'Demo site ready!',
            }
        finally:
            db.close()

    except Exception as exc:
        logger.error('[inbound_build_task] exception for business_id=%d: %s', business_id, exc, exc_info=True)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {'status': 'error', 'business_id': business_id, 'message': f'Pipeline failed: {exc}'}


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
