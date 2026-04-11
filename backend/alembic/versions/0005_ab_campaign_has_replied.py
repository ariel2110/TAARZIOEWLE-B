"""add ab_campaign_id and has_replied to outreach_messages

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('outreach_messages') as batch_op:
        batch_op.add_column(sa.Column('ab_campaign_id', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('has_replied', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.create_index('ix_outreach_messages_ab_campaign_id', ['ab_campaign_id'])
        batch_op.create_index('ix_outreach_messages_has_replied', ['has_replied'])


def downgrade() -> None:
    with op.batch_alter_table('outreach_messages') as batch_op:
        batch_op.drop_index('ix_outreach_messages_has_replied')
        batch_op.drop_index('ix_outreach_messages_ab_campaign_id')
        batch_op.drop_column('has_replied')
        batch_op.drop_column('ab_campaign_id')
