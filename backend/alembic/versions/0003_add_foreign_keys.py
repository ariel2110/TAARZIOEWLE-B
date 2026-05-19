"""add_foreign_keys

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-11
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002_initial_real_schema'
branch_labels = None
depends_on = None


def _try(conn, sql: str) -> None:
    """Run SQL in its own savepoint so failures don't abort the transaction."""
    try:
        conn.execute(sa.text("SAVEPOINT mig003"))
        conn.execute(sa.text(sql))
        conn.execute(sa.text("RELEASE SAVEPOINT mig003"))
    except Exception:
        conn.execute(sa.text("ROLLBACK TO SAVEPOINT mig003"))


def upgrade() -> None:
    conn = op.get_bind()

    # Add missing FK columns to businesses
    _try(conn, "ALTER TABLE businesses ADD COLUMN lead_id INTEGER")
    _try(conn, "ALTER TABLE businesses ADD COLUMN campaign_id INTEGER")
    _try(conn, "ALTER TABLE businesses ADD COLUMN targeting_profile_id INTEGER")

    # FK constraints — best-effort via savepoints
    _try(conn, "ALTER TABLE businesses ADD CONSTRAINT fk_businesses_lead_id FOREIGN KEY(lead_id) REFERENCES lead_records (id) ON DELETE SET NULL")
    _try(conn, "ALTER TABLE businesses ADD CONSTRAINT fk_businesses_campaign_id FOREIGN KEY(campaign_id) REFERENCES campaigns (id) ON DELETE SET NULL")
    _try(conn, "ALTER TABLE businesses ADD CONSTRAINT fk_businesses_targeting_profile_id FOREIGN KEY(targeting_profile_id) REFERENCES targeting_profiles (id) ON DELETE SET NULL")
    _try(conn, "ALTER TABLE draft_sites ADD CONSTRAINT fk_draft_sites_business_id FOREIGN KEY(business_id) REFERENCES businesses (id) ON DELETE CASCADE")
    _try(conn, "ALTER TABLE payment_records ADD CONSTRAINT fk_payment_records_business_id FOREIGN KEY(business_id) REFERENCES businesses (id) ON DELETE SET NULL")
    _try(conn, "ALTER TABLE lead_records ADD CONSTRAINT fk_lead_records_campaign_id FOREIGN KEY(campaign_id) REFERENCES campaigns (id) ON DELETE SET NULL")
    _try(conn, "ALTER TABLE lead_records ADD CONSTRAINT fk_lead_records_targeting_profile_id FOREIGN KEY(targeting_profile_id) REFERENCES targeting_profiles (id) ON DELETE SET NULL")


def downgrade() -> None:
    conn = op.get_bind()
    _try(conn, "ALTER TABLE lead_records DROP CONSTRAINT IF EXISTS fk_lead_records_targeting_profile_id")
    _try(conn, "ALTER TABLE lead_records DROP CONSTRAINT IF EXISTS fk_lead_records_campaign_id")
    _try(conn, "ALTER TABLE payment_records DROP CONSTRAINT IF EXISTS fk_payment_records_business_id")
    _try(conn, "ALTER TABLE draft_sites DROP CONSTRAINT IF EXISTS fk_draft_sites_business_id")
    _try(conn, "ALTER TABLE businesses DROP CONSTRAINT IF EXISTS fk_businesses_targeting_profile_id")
    _try(conn, "ALTER TABLE businesses DROP CONSTRAINT IF EXISTS fk_businesses_campaign_id")
    _try(conn, "ALTER TABLE businesses DROP CONSTRAINT IF EXISTS fk_businesses_lead_id")
    _try(conn, "ALTER TABLE businesses DROP COLUMN IF EXISTS targeting_profile_id")
    _try(conn, "ALTER TABLE businesses DROP COLUMN IF EXISTS campaign_id")
    _try(conn, "ALTER TABLE businesses DROP COLUMN IF EXISTS lead_id")
