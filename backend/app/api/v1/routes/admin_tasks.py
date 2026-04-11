"""
admin_tasks.py — FastAPI routes for Celery background task management.

Endpoints:
  POST /admin/tasks/generate-site/{business_id}  — Trigger AI site generation (async)
  POST /admin/tasks/batch-generate               — Trigger batch site generation
  GET  /admin/tasks/{task_id}/status             — Poll task progress / result
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.celery_app import celery_app
from app.api.deps import get_current_admin
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/admin/tasks', tags=['admin-tasks'])


# ── Request / Response schemas ────────────────────────────────────────────────

class BatchGenerateRequest(BaseModel):
    business_ids: list[int]


class RegenerateWithNoteRequest(BaseModel):
    note: str


class TaskTriggeredResponse(BaseModel):
    task_id: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str                        # PENDING | PROGRESS | SUCCESS | FAILURE | REVOKED
    step: str | None = None           # human-readable progress step
    result: dict[str, Any] | None = None
    error: str | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_status(task_id: str) -> TaskStatusResponse:
    """Read task state from Celery result backend."""
    result = celery_app.AsyncResult(task_id)
    state = result.state          # e.g. 'PENDING', 'PROGRESS', 'SUCCESS', 'FAILURE'
    step: str | None = None
    task_result: dict | None = None
    error: str | None = None

    if state == 'PROGRESS':
        meta = result.info or {}
        step = meta.get('step')
    elif state == 'SUCCESS':
        task_result = result.result if isinstance(result.result, dict) else {}
    elif state == 'FAILURE':
        exc = result.result
        error = str(exc) if exc else 'Unknown error'

    return TaskStatusResponse(
        task_id=task_id,
        state=state,
        step=step,
        result=task_result,
        error=error,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post('/generate-site/{business_id}', response_model=TaskTriggeredResponse)
def trigger_generate_site(
    business_id: int,
    _: User = Depends(get_current_admin),
) -> TaskTriggeredResponse:
    """Trigger async AI site generation for a single business."""
    from app.tasks import generate_site_task  # late import to avoid circular dep
    task = generate_site_task.delay(business_id)
    logger.info('[admin_tasks] triggered generate_site_task id=%s for business_id=%d', task.id, business_id)
    return TaskTriggeredResponse(
        task_id=task.id,
        message=f'Site generation started for business {business_id}',
    )


@router.post('/regenerate-with-note/{business_id}', response_model=TaskTriggeredResponse)
def trigger_regenerate_with_note(
    business_id: int,
    body: RegenerateWithNoteRequest,
    _: User = Depends(get_current_admin),
) -> TaskTriggeredResponse:
    """Trigger async AI regeneration with specific owner change instructions."""
    if not body.note or not body.note.strip():
        raise HTTPException(status_code=400, detail='note must not be empty')
    note = body.note.strip()[:2000]  # cap at 2000 chars
    from app.tasks import regenerate_with_note_task  # late import to avoid circular dep
    task = regenerate_with_note_task.delay(business_id, note)
    logger.info(
        '[admin_tasks] triggered regenerate_with_note_task id=%s for business_id=%d',
        task.id, business_id,
    )
    return TaskTriggeredResponse(
        task_id=task.id,
        message=f'Regeneration with note started for business {business_id}',
    )


@router.post('/batch-generate', response_model=TaskTriggeredResponse)
def trigger_batch_generate(
    body: BatchGenerateRequest,
    _: User = Depends(get_current_admin),
) -> TaskTriggeredResponse:
    """Trigger async AI site generation for multiple businesses."""
    if not body.business_ids:
        raise HTTPException(status_code=400, detail='business_ids must not be empty')
    if len(body.business_ids) > 100:
        raise HTTPException(status_code=400, detail='Maximum 100 businesses per batch')

    from app.tasks import batch_generate_task  # late import to avoid circular dep
    task = batch_generate_task.delay(body.business_ids)
    logger.info('[admin_tasks] triggered batch_generate_task id=%s count=%d', task.id, len(body.business_ids))
    return TaskTriggeredResponse(
        task_id=task.id,
        message=f'Batch generation started for {len(body.business_ids)} businesses',
    )


@router.get('/{task_id}/status', response_model=TaskStatusResponse)
def get_task_status(
    task_id: str,
    _: User = Depends(get_current_admin),
) -> TaskStatusResponse:
    """Poll task progress and retrieve result once complete."""
    return _parse_status(task_id)
