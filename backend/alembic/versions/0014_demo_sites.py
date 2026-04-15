"""Create demo_sites table."""
from alembic import op
import sqlalchemy as sa

revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'demo_sites',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(80), nullable=False),
        sa.Column('place_id', sa.String(120), nullable=True),
        sa.Column('business_name', sa.String(255), nullable=False),
        sa.Column('tagline', sa.String(512), nullable=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('address', sa.String(512), nullable=True),
        sa.Column('city', sa.String(120), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('reviews_count', sa.Integer(), nullable=True),
        sa.Column('google_maps_url', sa.String(1024), nullable=True),
        sa.Column('top_review', sa.Text(), nullable=True),
        sa.Column('business_types', sa.String(512), nullable=True),
        sa.Column('category', sa.String(120), nullable=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='draft'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('first_viewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('whatsapp_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_demo_sites_slug', 'demo_sites', ['slug'], unique=True)
    op.create_index('ix_demo_sites_place_id', 'demo_sites', ['place_id'])


def downgrade() -> None:
    op.drop_index('ix_demo_sites_place_id', 'demo_sites')
    op.drop_index('ix_demo_sites_slug', 'demo_sites')
    op.drop_table('demo_sites')
