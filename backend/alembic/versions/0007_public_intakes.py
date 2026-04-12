"""create public_intakes table

Revision ID: 0007
Revises: 0006_lead_rating_reviews
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'public_intakes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('token', sa.String(64), nullable=False),
        sa.Column('business_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(32), nullable=False),
        sa.Column('facebook_url', sa.String(500), nullable=True),
        sa.Column('tiktok_url', sa.String(500), nullable=True),
        sa.Column('instagram_url', sa.String(500), nullable=True),
        sa.Column('website_url', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('image_filenames', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='submitted'),
        sa.Column('correction_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('admin_note', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )
    op.create_index('ix_public_intakes_token', 'public_intakes', ['token'], unique=True)
    op.create_index('ix_public_intakes_status', 'public_intakes', ['status'])


def downgrade() -> None:
    op.drop_index('ix_public_intakes_status', table_name='public_intakes')
    op.drop_index('ix_public_intakes_token', table_name='public_intakes')
    op.drop_table('public_intakes')
