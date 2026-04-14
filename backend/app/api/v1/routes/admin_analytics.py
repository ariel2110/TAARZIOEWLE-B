from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import sqlalchemy as sa
import datetime
from app.api.deps import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.models.outreach_message import OutreachMessage
from app.services.analytics.kpi_service import KPIService

router = APIRouter(prefix='/admin/analytics', tags=['admin-analytics'])
service = KPIService()


@router.get('/snapshot')
def snapshot(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return service.snapshot(db)


@router.get('/ab-results')
def ab_results(
    campaign_id: str | None = Query(default=None, description='Filter by ab_campaign_id'),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    A/B test results — reply and delivery rates per variant.

    Groups by ab_variant + ab_campaign_id and counts:
    - total sends, sent, delivered, read
    - has_replied (authoritative conversion event from webhook)
    - reply_rate and read_rate as percentages

    Optional ?campaign_id=xxx to narrow to one experiment.
    """
    q = db.query(
        OutreachMessage.ab_variant,
        OutreachMessage.ab_campaign_id,
        func.count(OutreachMessage.id).label('total'),
        func.sum((OutreachMessage.status.in_(['sent', 'delivered', 'read', 'replied'])).cast(sa.Integer)).label('sent'),
        func.sum((OutreachMessage.status.in_(['delivered', 'read', 'replied'])).cast(sa.Integer)).label('delivered'),
        func.sum((OutreachMessage.status.in_(['read', 'replied'])).cast(sa.Integer)).label('read'),
        func.sum(OutreachMessage.has_replied.cast(sa.Integer)).label('replied'),
    )

    if campaign_id:
        q = q.filter(OutreachMessage.ab_campaign_id == campaign_id)

    rows = q.group_by(OutreachMessage.ab_variant, OutreachMessage.ab_campaign_id).all()

    results = []
    for row in rows:
        total = row.total or 1
        results.append({
            'variant': row.ab_variant or 'control',
            'campaign_id': row.ab_campaign_id or 'default',
            'total': row.total,
            'sent': row.sent or 0,
            'delivered': row.delivered or 0,
            'read': row.read or 0,
            'replied': row.replied or 0,
            'reply_rate': round((row.replied or 0) / total * 100, 1),
            'read_rate': round((row.read or 0) / total * 100, 1),
        })
    return results


# ─── CEO Agent Analytics ───────────────────────────────────────────────────────

@router.get('/agent-global-stats')
def agent_global_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    Returns this calendar month's aggregated platform economics:
    - Total revenue (ILS) from paid subscriptions
    - Total API cost (ILS), broken down per agent
    - Net profit (ILS) and margin %
    - Pie-chart data for frontend visualisation
    - Total sites built this month
    """
    from app.models.agent_usage_log import AgentUsageLog
    from app.models.system_daily_analytics import SystemDailyAnalytics
    from app.models.public_intake import PublicIntake
    from app.core.pricing_config import PLAN_REVENUE_ILS, AGENT_DISPLAY

    today = datetime.date.today()
    month_start = today.replace(day=1)

    # ── Monthly API cost per agent (sum from AgentUsageLog) ──────────────
    cost_rows = (
        db.query(
            AgentUsageLog.agent_name,
            func.sum(AgentUsageLog.cost_ils).label('total_cost'),
            func.sum(AgentUsageLog.input_tokens).label('total_in'),
            func.sum(AgentUsageLog.output_tokens).label('total_out'),
            func.count(AgentUsageLog.id).label('calls'),
        )
        .filter(AgentUsageLog.created_at >= month_start)
        .group_by(AgentUsageLog.agent_name)
        .all()
    )

    total_api_cost_ils = 0.0
    agent_breakdown = []
    for row in cost_rows:
        cost = round(row.total_cost or 0.0, 4)
        total_api_cost_ils += cost
        info = AGENT_DISPLAY.get(row.agent_name, {'label': row.agent_name, 'color': '#9ca3af', 'emoji': '🤖'})
        agent_breakdown.append({
            'agent':        row.agent_name,
            'label':        info['label'],
            'emoji':        info['emoji'],
            'color':        info['color'],
            'cost_ils':     cost,
            'tokens_in':    row.total_in or 0,
            'tokens_out':   row.total_out or 0,
            'calls':        row.calls or 0,
        })

    # ── Monthly revenue: count paid intakes activated this month ─────────
    paid_intakes = (
        db.query(PublicIntake.plan_tier, func.count(PublicIntake.id).label('n'))
        .filter(
            PublicIntake.payment_status == 'paid',
            PublicIntake.created_at >= month_start,
        )
        .group_by(PublicIntake.plan_tier)
        .all()
    )
    total_revenue_ils = 0.0
    sites_built = 0
    for row in paid_intakes:
        revenue = PLAN_REVENUE_ILS.get(row.plan_tier or 'auto', 39.0) * (row.n or 0)
        total_revenue_ils += revenue
        sites_built += row.n or 0

    net_profit = round(total_revenue_ils - total_api_cost_ils, 2)
    margin_pct = round((net_profit / total_revenue_ils * 100) if total_revenue_ils > 0 else 0.0, 1)

    return {
        'period':             f"{month_start.isoformat()} / {today.isoformat()}",
        'total_revenue_ils':  round(total_revenue_ils, 2),
        'total_api_cost_ils': round(total_api_cost_ils, 4),
        'net_profit_ils':     net_profit,
        'margin_pct':         margin_pct,
        'sites_built':        sites_built,
        'agent_breakdown':    sorted(agent_breakdown, key=lambda x: x['cost_ils'], reverse=True),
    }


@router.get('/agent-status')
def agent_status(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    Per-agent configuration status, pricing, and total spend all-time + this month.
    Includes projected cost per site-generation run.
    """
    from app.core.config import settings
    from app.core.pricing_config import TOKEN_PRICING, AGENT_DISPLAY, USD_TO_ILS, PLAN_REVENUE_ILS
    from app.models.agent_usage_log import AgentUsageLog

    today = datetime.date.today()
    month_start = today.replace(day=1)

    # ── Summarise usage per agent ─────────────────────────────────────────
    all_time = {
        r.agent_name: {'cost_ils': round(r.cost_ils or 0, 4), 'calls': r.calls}
        for r in db.query(
            AgentUsageLog.agent_name,
            func.sum(AgentUsageLog.cost_ils).label('cost_ils'),
            func.count(AgentUsageLog.id).label('calls'),
        ).group_by(AgentUsageLog.agent_name).all()
    }
    this_month = {
        r.agent_name: {'cost_ils': round(r.cost_ils or 0, 4), 'calls': r.calls}
        for r in db.query(
            AgentUsageLog.agent_name,
            func.sum(AgentUsageLog.cost_ils).label('cost_ils'),
            func.count(AgentUsageLog.id).label('calls'),
        )
        .filter(AgentUsageLog.created_at >= month_start)
        .group_by(AgentUsageLog.agent_name).all()
    }

    # ── Avg tokens per call for cost projection ───────────────────────────
    avg_tokens = {
        r.agent_name: {
            'avg_in':  round((r.avg_in or 0)),
            'avg_out': round((r.avg_out or 0)),
        }
        for r in db.query(
            AgentUsageLog.agent_name,
            func.avg(AgentUsageLog.input_tokens).label('avg_in'),
            func.avg(AgentUsageLog.output_tokens).label('avg_out'),
        ).group_by(AgentUsageLog.agent_name).all()
    }

    configured = {
        'claude':  bool(getattr(settings, 'anthropic_api_key', None)),
        'gpt':     bool(getattr(settings, 'openai_api_key', None)),
        'gemini':  bool(getattr(settings, 'gemini_api_key', None)),
        'grok':    bool(getattr(settings, 'xai_api_key', None)),
        'serper':  bool(getattr(settings, 'serper_api_key', None)),
        'apify':   bool(getattr(settings, 'apify_api_key', None)),
    }

    agents = []
    for agent_key, info in AGENT_DISPLAY.items():
        pricing = TOKEN_PRICING.get(agent_key, {})
        at = all_time.get(agent_key, {'cost_ils': 0.0, 'calls': 0})
        mt = this_month.get(agent_key, {'cost_ils': 0.0, 'calls': 0})
        avg = avg_tokens.get(agent_key, {'avg_in': 0, 'avg_out': 0})

        # Project cost for one typical site-gen call (based on historic avg)
        proj_usd = 0.0
        if pricing and avg['avg_in']:
            proj_usd = (avg['avg_in'] / 1_000_000) * pricing.get('input', 0) \
                     + (avg['avg_out'] / 1_000_000) * pricing.get('output', 0)
        proj_ils = round(proj_usd * USD_TO_ILS, 4)

        agents.append({
            'agent':                  agent_key,
            'label':                  info['label'],
            'emoji':                  info['emoji'],
            'color':                  info['color'],
            'configured':             configured.get(agent_key, False),
            'model':                  pricing.get('model', '—'),
            'pricing_input_per_1m':   pricing.get('input', '—'),
            'pricing_output_per_1m':  pricing.get('output', '—'),
            'cost_ils_all_time':      at['cost_ils'],
            'calls_all_time':         at['calls'],
            'cost_ils_this_month':    mt['cost_ils'],
            'calls_this_month':       mt['calls'],
            'avg_input_tokens':       avg['avg_in'],
            'avg_output_tokens':      avg['avg_out'],
            'projected_cost_per_call_ils': proj_ils,
        })

    return {'agents': agents, 'usd_to_ils': USD_TO_ILS}


@router.get('/agent-recent-runs')
def agent_recent_runs(
    limit: int = Query(default=30, le=100),
    agent_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """Latest LLM call log rows — for the per-site economics table."""
    from app.models.agent_usage_log import AgentUsageLog

    q = db.query(AgentUsageLog).order_by(AgentUsageLog.created_at.desc())
    if agent_name:
        q = q.filter(AgentUsageLog.agent_name == agent_name)
    rows = q.limit(limit).all()

    return [
        {
            'id':             r.id,
            'created_at':     r.created_at.isoformat() if r.created_at else None,
            'agent_name':     r.agent_name,
            'model_name':     r.model_name,
            'task_type':      r.task_type,
            'stage':          r.stage,
            'business_id':    r.business_id,
            'draft_site_id':  r.draft_site_id,
            'input_tokens':   r.input_tokens,
            'output_tokens':  r.output_tokens,
            'cost_ils':       round(r.cost_ils or 0, 6),
            'cost_usd':       round(r.cost_usd or 0, 8),
        }
        for r in rows
    ]

