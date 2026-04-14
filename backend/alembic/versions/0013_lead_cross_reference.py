"""Add cross-reference validation columns to lead_records."""
from alembic import op
import sqlalchemy as sa

revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('lead_records', sa.Column('lat', sa.Float(), nullable=True))
    op.add_column('lead_records', sa.Column('lng', sa.Float(), nullable=True))
    op.add_column('lead_records', sa.Column('cross_ref_score', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('lead_records', sa.Column('cross_ref_status', sa.String(20), nullable=False, server_default='pending'))
    op.add_column('lead_records', sa.Column('cross_ref_agents', sa.Text(), nullable=True))
    op.create_index('ix_lead_records_cross_ref_score', 'lead_records', ['cross_ref_score'])
    op.create_index('ix_lead_records_cross_ref_status', 'lead_records', ['cross_ref_status'])


def downgrade() -> None:
    op.drop_index('ix_lead_records_cross_ref_status', 'lead_records')
    op.drop_index('ix_lead_records_cross_ref_score', 'lead_records')
    op.drop_column('lead_records', 'cross_ref_agents')
    op.drop_column('lead_records', 'cross_ref_status')
    op.drop_column('lead_records', 'cross_ref_score')
    op.drop_column('lead_records', 'lng')
    op.drop_column('lead_records', 'lat')
