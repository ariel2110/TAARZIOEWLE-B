"""add rating and reviews_count to lead_records

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('lead_records') as batch_op:
        batch_op.add_column(sa.Column('rating', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('reviews_count', sa.Integer(), nullable=True))
        batch_op.create_index('ix_lead_records_rating', ['rating'])
        batch_op.create_index('ix_lead_records_reviews_count', ['reviews_count'])


def downgrade() -> None:
    with op.batch_alter_table('lead_records') as batch_op:
        batch_op.drop_index('ix_lead_records_reviews_count')
        batch_op.drop_index('ix_lead_records_rating')
        batch_op.drop_column('reviews_count')
        batch_op.drop_column('rating')
