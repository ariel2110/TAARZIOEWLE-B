"""add whatsapp approval fields to public_intakes

Adds two columns so AI-generated WhatsApp messages are held for admin
approval before being sent to leads:

  - whatsapp_pending_message:  the proposed message text waiting for approval
  - whatsapp_status:           'none' | 'pending' | 'sent' | 'rejected'

Revision ID: 0009
Revises: 0008
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa

revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('public_intakes') as batch_op:
        batch_op.add_column(sa.Column('whatsapp_pending_message', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('whatsapp_status', sa.String(20), nullable=False,
                                      server_default='none'))


def downgrade() -> None:
    with op.batch_alter_table('public_intakes') as batch_op:
        batch_op.drop_column('whatsapp_pending_message')
        batch_op.drop_column('whatsapp_status')
