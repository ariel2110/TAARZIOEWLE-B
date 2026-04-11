"""initial placeholder

Revision ID: 0001_initial_placeholder
Revises:
Create Date: 2026-04-10
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial_placeholder'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables are currently auto-created from SQLAlchemy metadata in init_db.
    # Replace this placeholder with real migrations as the next step.
    pass


def downgrade() -> None:
    pass
