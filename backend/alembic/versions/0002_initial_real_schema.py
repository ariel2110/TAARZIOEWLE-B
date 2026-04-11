"""initial real schema

Revision ID: 0002_initial_real_schema
Revises: 0001_initial_placeholder
Create Date: 2026-04-10
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_initial_real_schema'
down_revision = '0001_initial_placeholder'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='admin'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])

    op.create_table(
        'businesses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=120), nullable=True),
        sa.Column('category', sa.String(length=120), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='new'),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_businesses_name', 'businesses', ['name'])
    op.create_index('ix_businesses_city', 'businesses', ['city'])
    op.create_index('ix_businesses_category', 'businesses', ['category'])
    op.create_index('ix_businesses_status', 'businesses', ['status'])

    op.create_table(
        'lead_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('imported_name', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=120), nullable=True),
        sa.Column('category', sa.String(length=120), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('website_url', sa.String(length=255), nullable=True),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='imported'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_lead_records_imported_name', 'lead_records', ['imported_name'])
    op.create_index('ix_lead_records_city', 'lead_records', ['city'])
    op.create_index('ix_lead_records_category', 'lead_records', ['category'])
    op.create_index('ix_lead_records_score', 'lead_records', ['score'])
    op.create_index('ix_lead_records_status', 'lead_records', ['status'])

    op.create_table(
        'targeting_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('city', sa.String(length=120), nullable=False),
        sa.Column('radius_km', sa.Integer(), nullable=False, server_default='8'),
        sa.Column('category_list', sa.JSON(), nullable=True),
        sa.Column('min_reviews', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('min_rating', sa.Float(), nullable=False, server_default='0'),
        sa.Column('requires_no_website', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('requires_phone', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('score_threshold', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_targeting_profiles_name', 'targeting_profiles', ['name'])
    op.create_index('ix_targeting_profiles_city', 'targeting_profiles', ['city'])

    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('targeting_profile_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('goals_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_campaigns_name', 'campaigns', ['name'])
    op.create_index('ix_campaigns_status', 'campaigns', ['status'])
    op.create_index('ix_campaigns_targeting_profile_id', 'campaigns', ['targeting_profile_id'])

    op.create_table(
        'draft_sites',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('site_title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('preview_url', sa.String(length=255), nullable=True),
        sa.Column('primary_color', sa.String(length=40), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('noindex', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('hero_title', sa.String(length=255), nullable=True),
        sa.Column('about_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_draft_sites_business_id', 'draft_sites', ['business_id'])
    op.create_index('ix_draft_sites_status', 'draft_sites', ['status'])

    op.create_table(
        'payment_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('business_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='manual'),
        sa.Column('internal_status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('external_reference', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_payment_records_business_id', 'payment_records', ['business_id'])
    op.create_index('ix_payment_records_internal_status', 'payment_records', ['internal_status'])

    op.create_table(
        'generated_insights',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('insight_type', sa.String(length=80), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('evidence_json', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='proposed'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_generated_insights_insight_type', 'generated_insights', ['insight_type'])
    op.create_index('ix_generated_insights_status', 'generated_insights', ['status'])

    op.create_table(
        'activity_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('actor_type', sa.String(length=50), nullable=False, server_default='system'),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('entity_type', sa.String(length=80), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('action_type', sa.String(length=120), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_activity_logs_actor_type', 'activity_logs', ['actor_type'])
    op.create_index('ix_activity_logs_entity_type', 'activity_logs', ['entity_type'])
    op.create_index('ix_activity_logs_entity_id', 'activity_logs', ['entity_id'])
    op.create_index('ix_activity_logs_action_type', 'activity_logs', ['action_type'])

    op.create_table(
        'approval_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('approval_type', sa.String(length=80), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False, server_default='proposed'),
        sa.Column('approval_required', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_approval_items_approval_type', 'approval_items', ['approval_type'])
    op.create_index('ix_approval_items_status', 'approval_items', ['status'])

    op.create_table(
        'outreach_messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('business_id', sa.Integer(), nullable=True),
        sa.Column('draft_site_id', sa.Integer(), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=False, server_default='whatsapp'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='draft'),
        sa.Column('message_template_key', sa.String(length=120), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('outbound_target', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_outreach_messages_business_id', 'outreach_messages', ['business_id'])
    op.create_index('ix_outreach_messages_draft_site_id', 'outreach_messages', ['draft_site_id'])
    op.create_index('ix_outreach_messages_channel', 'outreach_messages', ['channel'])
    op.create_index('ix_outreach_messages_status', 'outreach_messages', ['status'])


def downgrade() -> None:
    op.drop_table('outreach_messages')
    op.drop_table('approval_items')
    op.drop_table('activity_logs')
    op.drop_table('generated_insights')
    op.drop_table('payment_records')
    op.drop_table('draft_sites')
    op.drop_table('campaigns')
    op.drop_table('targeting_profiles')
    op.drop_table('lead_records')
    op.drop_table('businesses')
    op.drop_table('users')
