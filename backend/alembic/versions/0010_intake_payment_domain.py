"""add payment and domain fields to public_intakes

Revision ID: 0010
Revises: 0009
Create Date: 2026-04-14
"""
from alembic import op
import sqlalchemy as sa

revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('public_intakes') as batch_op:
        batch_op.add_column(sa.Column('desired_domain', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('payment_status', sa.String(20), nullable=False, server_default='unpaid'))
        batch_op.add_column(sa.Column('payment_reference', sa.String(120), nullable=True))
        batch_op.add_column(sa.Column('payment_link', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('site_live_url', sa.String(255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('public_intakes') as batch_op:
        batch_op.drop_column('desired_domain')
        batch_op.drop_column('payment_status')
        batch_op.drop_column('payment_reference')
        batch_op.drop_column('payment_link')
        batch_op.drop_column('site_live_url')
