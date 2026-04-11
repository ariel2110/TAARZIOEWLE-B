"""add_ab_variant_to_outreach_messages

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa

revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('outreach_messages') as batch_op:
        batch_op.add_column(sa.Column('ab_variant', sa.String(50), nullable=True, index=True))


def downgrade() -> None:
    with op.batch_alter_table('outreach_messages') as batch_op:
        batch_op.drop_column('ab_variant')
