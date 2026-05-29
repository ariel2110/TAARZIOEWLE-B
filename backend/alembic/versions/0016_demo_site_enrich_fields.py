"""Add opening_hours and reviews_json to demo_sites."""
from alembic import op
import sqlalchemy as sa

revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('demo_sites', sa.Column('opening_hours', sa.Text(), nullable=True))
    op.add_column('demo_sites', sa.Column('reviews_json', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('demo_sites', 'reviews_json')
    op.drop_column('demo_sites', 'opening_hours')
