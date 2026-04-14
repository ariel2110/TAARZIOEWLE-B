"""Cost Tracker — lightweight async LLM usage logging
======================================================
Public API:

    from app.services.cost_tracker import track_usage

    track_usage(
        agent_name   = 'claude',          # 'claude'|'gpt'|'gemini'|'grok'|'serper'|'apify'
        model_name   = 'claude-sonnet-4-6',
        input_tokens = 1200,
        output_tokens= 800,
        business_id  = 42,                # optional
        draft_site_id= 7,                 # optional
        intake_token = None,              # optional
        stage        = 'build_site_html', # optional label
        task_type    = 'site_generation', # optional category
    )

``track_usage`` is fire-and-forget — it queues a Celery task and returns
immediately.  The main request thread is never blocked.

When Celery is unavailable (dev / test), the write runs in a daemon thread
so the call is still non-blocking.
"""
from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)


# ── Public fire-and-forget helper ────────────────────────────────────────────

def track_usage(
    *,
    agent_name:      str,
    model_name:      str | None     = None,
    input_tokens:    int            = 0,
    output_tokens:   int            = 0,
    additional_units: int           = 0,
    business_id:     int | None     = None,
    draft_site_id:   int | None     = None,
    intake_token:    str | None     = None,
    stage:           str | None     = None,
    task_type:       str | None     = None,
) -> None:
    """Queue an async DB write.  Never raises, never blocks."""
    kwargs = dict(
        agent_name=agent_name,
        model_name=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        additional_units=additional_units,
        business_id=business_id,
        draft_site_id=draft_site_id,
        intake_token=intake_token,
        stage=stage,
        task_type=task_type,
    )
    try:
        from app.tasks import log_usage_task
        log_usage_task.delay(**kwargs)
    except Exception as exc:
        logger.debug('[CostTracker] Celery unavailable (%s) — falling back to thread', exc)
        threading.Thread(
            target=_write_usage_sync,
            kwargs=kwargs,
            daemon=True,
        ).start()


# ── Synchronous DB write (used by Celery task + thread fallback) ──────────────

def _write_usage_sync(
    *,
    agent_name:       str,
    model_name:       str | None     = None,
    input_tokens:     int            = 0,
    output_tokens:    int            = 0,
    additional_units: int            = 0,
    business_id:      int | None     = None,
    draft_site_id:    int | None     = None,
    intake_token:     str | None     = None,
    stage:            str | None     = None,
    task_type:        str | None     = None,
) -> None:
    """Write one AgentUsageLog row + update today's SystemDailyAnalytics."""
    try:
        from app.core.pricing_config import (
            calc_token_cost_usd, usd_to_ils,
            SERPER_COST_PER_QUERY_USD, APIFY_COST_PER_RUN_USD,
        )
        from app.db.session import SessionLocal
        from app.models.agent_usage_log import AgentUsageLog
        from app.models.system_daily_analytics import SystemDailyAnalytics
        import datetime

        # ── Cost calculation ──────────────────────────────────────────────
        if agent_name == 'serper':
            cost_usd = SERPER_COST_PER_QUERY_USD * max(additional_units, 1)
        elif agent_name == 'apify':
            cost_usd = APIFY_COST_PER_RUN_USD * max(additional_units, 1)
        else:
            cost_usd = calc_token_cost_usd(agent_name, input_tokens, output_tokens)

        cost_ils = usd_to_ils(cost_usd)

        db = SessionLocal()
        try:
            # ── Insert usage log row ──────────────────────────────────────
            log = AgentUsageLog(
                agent_name=agent_name,
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                additional_units=additional_units,
                business_id=business_id,
                draft_site_id=draft_site_id,
                intake_token=intake_token,
                stage=stage,
                task_type=task_type,
                cost_usd=cost_usd,
                cost_ils=cost_ils,
            )
            db.add(log)

            # ── Upsert today's aggregated row ─────────────────────────────
            today = datetime.date.today()
            row = (
                db.query(SystemDailyAnalytics)
                .filter(SystemDailyAnalytics.date == today)
                .first()
            )
            if not row:
                row = SystemDailyAnalytics(date=today)
                db.add(row)

            row.total_api_cost_ils = (row.total_api_cost_ils or 0.0) + cost_ils

            # Per-agent aggregation
            _bump_agent(row, agent_name, cost_ils, input_tokens, output_tokens)

            db.commit()
            logger.debug(
                '[CostTracker] Logged %s cost=%.6f ILS in=%.0f out=%.0f',
                agent_name, cost_ils, input_tokens, output_tokens,
            )
        finally:
            db.close()

    except Exception:
        logger.exception('[CostTracker] Failed to write usage log')


def _bump_agent(
    row: 'SystemDailyAnalytics',
    agent_name: str,
    cost_ils: float,
    input_tokens: int,
    output_tokens: int,
) -> None:
    """Increment the per-agent columns on a SystemDailyAnalytics row."""
    if agent_name == 'claude':
        row.claude_cost_ils    = (row.claude_cost_ils   or 0.0) + cost_ils
        row.claude_tokens_in   = (row.claude_tokens_in  or 0) + input_tokens
        row.claude_tokens_out  = (row.claude_tokens_out or 0) + output_tokens
    elif agent_name == 'gpt':
        row.gpt_cost_ils       = (row.gpt_cost_ils   or 0.0) + cost_ils
        row.gpt_tokens_in      = (row.gpt_tokens_in  or 0) + input_tokens
        row.gpt_tokens_out     = (row.gpt_tokens_out or 0) + output_tokens
    elif agent_name == 'gemini':
        row.gemini_cost_ils    = (row.gemini_cost_ils   or 0.0) + cost_ils
        row.gemini_tokens_in   = (row.gemini_tokens_in  or 0) + input_tokens
        row.gemini_tokens_out  = (row.gemini_tokens_out or 0) + output_tokens
    elif agent_name == 'grok':
        row.grok_cost_ils      = (row.grok_cost_ils   or 0.0) + cost_ils
        row.grok_tokens_in     = (row.grok_tokens_in  or 0) + input_tokens
        row.grok_tokens_out    = (row.grok_tokens_out or 0) + output_tokens
    elif agent_name == 'serper':
        row.serper_cost_ils    = (row.serper_cost_ils or 0.0) + cost_ils
    elif agent_name == 'apify':
        row.apify_cost_ils     = (row.apify_cost_ils  or 0.0) + cost_ils
