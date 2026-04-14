"""add plan_tier column to public_intakes

Revision ID: 0011
Revises: 0010
Create Date: 2026-04-14

Adds `plan_tier` to track which Morning subscription plan was purchased:
  'auto'    = 39 NIS  (full automated pipeline)
  'starter' = 299 NIS (manual onboarding)
  'growth'  = 699 NIS (manual onboarding + independent domain)
  'pro'     = 1299 NIS (premium manual onboarding)
"""
from alembic import op
import sqlalchemy as sa

revision = '0011'
down_revision = '0010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('public_intakes') as batch_op:
        batch_op.add_column(
            sa.Column('plan_tier', sa.String(20), nullable=False, server_default='auto')
        )


def downgrade() -> None:
    with op.batch_alter_table('public_intakes') as batch_op:
        batch_op.drop_column('plan_tier')
