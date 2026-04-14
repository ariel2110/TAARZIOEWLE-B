"""add_foreign_keys

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-11
"""
from alembic import op

revision = '0003'
down_revision = '0002_initial_real_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('businesses') as batch_op:
        batch_op.create_foreign_key('fk_businesses_lead_id', 'lead_records', ['lead_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_businesses_campaign_id', 'campaigns', ['campaign_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_businesses_targeting_profile_id', 'targeting_profiles', ['targeting_profile_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('draft_sites') as batch_op:
        batch_op.create_foreign_key('fk_draft_sites_business_id', 'businesses', ['business_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('customer_accounts') as batch_op:
        batch_op.create_foreign_key('fk_customer_accounts_business_id', 'businesses', ['business_id'], ['id'], ondelete='CASCADE')
        batch_op.create_foreign_key('fk_customer_accounts_draft_site_id', 'draft_sites', ['draft_site_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_customer_accounts_active_site_id', 'draft_sites', ['active_site_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('payment_records') as batch_op:
        batch_op.create_foreign_key('fk_payment_records_business_id', 'businesses', ['business_id'], ['id'], ondelete='SET NULL')

    with op.batch_alter_table('lead_records') as batch_op:
        batch_op.create_foreign_key('fk_lead_records_campaign_id', 'campaigns', ['campaign_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_lead_records_targeting_profile_id', 'targeting_profiles', ['targeting_profile_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    with op.batch_alter_table('lead_records') as batch_op:
        batch_op.drop_constraint('fk_lead_records_targeting_profile_id', type_='foreignkey')
        batch_op.drop_constraint('fk_lead_records_campaign_id', type_='foreignkey')

    with op.batch_alter_table('payment_records') as batch_op:
        batch_op.drop_constraint('fk_payment_records_business_id', type_='foreignkey')

    with op.batch_alter_table('customer_accounts') as batch_op:
        batch_op.drop_constraint('fk_customer_accounts_active_site_id', type_='foreignkey')
        batch_op.drop_constraint('fk_customer_accounts_draft_site_id', type_='foreignkey')
        batch_op.drop_constraint('fk_customer_accounts_business_id', type_='foreignkey')

    with op.batch_alter_table('draft_sites') as batch_op:
        batch_op.drop_constraint('fk_draft_sites_business_id', type_='foreignkey')

    with op.batch_alter_table('businesses') as batch_op:
        batch_op.drop_constraint('fk_businesses_targeting_profile_id', type_='foreignkey')
        batch_op.drop_constraint('fk_businesses_campaign_id', type_='foreignkey')
        batch_op.drop_constraint('fk_businesses_lead_id', type_='foreignkey')
