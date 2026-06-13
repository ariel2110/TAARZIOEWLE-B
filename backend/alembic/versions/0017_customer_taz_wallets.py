"""add customer_taz_wallets table

Revision ID: 0017_customer_taz_wallets
Revises: 0016_demo_site_enrich_fields
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa

revision = '0017_customer_taz_wallets'
down_revision = '0016'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'customer_taz_wallets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('phone', sa.String(50), nullable=False),
        sa.Column('wallet_id', sa.String(50), nullable=False),
        sa.Column('pending_order_ref', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone'),
        sa.UniqueConstraint('wallet_id'),
    )
    op.create_index('ix_customer_taz_wallets_phone', 'customer_taz_wallets', ['phone'])
    op.create_index('ix_customer_taz_wallets_wallet_id', 'customer_taz_wallets', ['wallet_id'])


def downgrade() -> None:
    op.drop_table('customer_taz_wallets')
