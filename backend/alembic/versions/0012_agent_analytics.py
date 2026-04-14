"""Create agent_usage_logs and system_daily_analytics tables

Revision ID: 0012
Revises: 0011
Create Date: 2026-04-14

Adds CEO Analytics infrastructure:
  - agent_usage_logs          — one row per LLM / tool API call
  - system_daily_analytics    — one row per calendar day (aggregated)
"""
from alembic import op
import sqlalchemy as sa

revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── agent_usage_logs ──────────────────────────────────────────────────
    op.create_table(
        'agent_usage_logs',
        sa.Column('id',               sa.Integer,     primary_key=True, autoincrement=True),
        sa.Column('created_at',       sa.DateTime,    nullable=True),
        sa.Column('updated_at',       sa.DateTime,    nullable=True),
        sa.Column('business_id',      sa.Integer,     nullable=True),
        sa.Column('draft_site_id',    sa.Integer,     nullable=True),
        sa.Column('intake_token',     sa.String(128), nullable=True),
        sa.Column('stage',            sa.String(80),  nullable=True),
        sa.Column('task_type',        sa.String(80),  nullable=True),
        sa.Column('agent_name',       sa.String(40),  nullable=False),
        sa.Column('model_name',       sa.String(100), nullable=True),
        sa.Column('input_tokens',     sa.Integer,     nullable=False, server_default='0'),
        sa.Column('output_tokens',    sa.Integer,     nullable=False, server_default='0'),
        sa.Column('additional_units', sa.Integer,     nullable=False, server_default='0'),
        sa.Column('cost_usd',         sa.Float,       nullable=False, server_default='0'),
        sa.Column('cost_ils',         sa.Float,       nullable=False, server_default='0'),
    )
    op.create_index('ix_aul_agent_name',     'agent_usage_logs', ['agent_name'])
    op.create_index('ix_aul_business_id',    'agent_usage_logs', ['business_id'])
    op.create_index('ix_aul_draft_site_id',  'agent_usage_logs', ['draft_site_id'])
    op.create_index('ix_aul_intake_token',   'agent_usage_logs', ['intake_token'])
    op.create_index('ix_aul_task_type',      'agent_usage_logs', ['task_type'])
    op.create_index('ix_aul_agent_created',  'agent_usage_logs', ['agent_name', 'created_at'])
    op.create_index('ix_aul_biz_created',    'agent_usage_logs', ['business_id', 'created_at'])

    # ── system_daily_analytics ────────────────────────────────────────────
    op.create_table(
        'system_daily_analytics',
        sa.Column('id',                 sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('created_at',         sa.DateTime, nullable=True),
        sa.Column('updated_at',         sa.DateTime, nullable=True),
        sa.Column('date',               sa.Date,    nullable=False, unique=True),
        sa.Column('total_revenue_ils',  sa.Float,   nullable=False, server_default='0'),
        sa.Column('total_sites_built',  sa.Integer, nullable=False, server_default='0'),
        sa.Column('total_api_cost_ils', sa.Float,   nullable=False, server_default='0'),
        sa.Column('claude_cost_ils',    sa.Float,   nullable=False, server_default='0'),
        sa.Column('gpt_cost_ils',       sa.Float,   nullable=False, server_default='0'),
        sa.Column('gemini_cost_ils',    sa.Float,   nullable=False, server_default='0'),
        sa.Column('grok_cost_ils',      sa.Float,   nullable=False, server_default='0'),
        sa.Column('serper_cost_ils',    sa.Float,   nullable=False, server_default='0'),
        sa.Column('apify_cost_ils',     sa.Float,   nullable=False, server_default='0'),
        sa.Column('claude_tokens_in',   sa.Integer, nullable=False, server_default='0'),
        sa.Column('claude_tokens_out',  sa.Integer, nullable=False, server_default='0'),
        sa.Column('gpt_tokens_in',      sa.Integer, nullable=False, server_default='0'),
        sa.Column('gpt_tokens_out',     sa.Integer, nullable=False, server_default='0'),
        sa.Column('gemini_tokens_in',   sa.Integer, nullable=False, server_default='0'),
        sa.Column('gemini_tokens_out',  sa.Integer, nullable=False, server_default='0'),
        sa.Column('grok_tokens_in',     sa.Integer, nullable=False, server_default='0'),
        sa.Column('grok_tokens_out',    sa.Integer, nullable=False, server_default='0'),
    )
    op.create_index('ix_sda_date', 'system_daily_analytics', ['date'])


def downgrade() -> None:
    op.drop_table('system_daily_analytics')
    op.drop_table('agent_usage_logs')
