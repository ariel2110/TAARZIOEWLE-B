"""intake dual preview + google places enrichment

Revision ID: 0015
Revises: 0014
Create Date: 2026-04-15

Adds four columns to public_intakes:
  - google_place_id        VARCHAR(120) nullable
  - google_enrichment_json TEXT nullable
  - generated_preview_url_v2 VARCHAR(255) nullable
  - generated_html_v2      TEXT nullable
"""
from alembic import op
import sqlalchemy as sa

revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('public_intakes', sa.Column('google_place_id', sa.String(120), nullable=True))
    op.add_column('public_intakes', sa.Column('google_enrichment_json', sa.Text, nullable=True))
    op.add_column('public_intakes', sa.Column('generated_preview_url_v2', sa.String(255), nullable=True))
    op.add_column('public_intakes', sa.Column('generated_html_v2', sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column('public_intakes', 'google_place_id')
    op.drop_column('public_intakes', 'google_enrichment_json')
    op.drop_column('public_intakes', 'generated_preview_url_v2')
    op.drop_column('public_intakes', 'generated_html_v2')
