"""add ai generation fields to public_intakes

Adds three new columns to support the background AI pipeline that runs
after a public intake form submission:

  - ai_status:              'pending' | 'generating' | 'done' | 'failed'
  - generated_preview_url:  relative path to the generated HTML preview
  - generated_html:         full HTML (kept so admin can re-render without re-running AI)

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('public_intakes') as batch_op:
        batch_op.add_column(sa.Column('ai_status', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('generated_preview_url', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('generated_html', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('public_intakes') as batch_op:
        batch_op.drop_column('generated_html')
        batch_op.drop_column('generated_preview_url')
        batch_op.drop_column('ai_status')
