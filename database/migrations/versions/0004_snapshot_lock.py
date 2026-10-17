"""Expose only a lock operation, never inventory revision writes, to the API."""

from alembic import op

revision = "0004_snapshot_lock"
down_revision = "0003_integrity"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE FUNCTION core.lock_inventory_revision() RETURNS bigint
    LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
    DECLARE rev bigint;
    BEGIN
        SELECT revision INTO rev FROM core.inventory_revision WHERE singleton FOR UPDATE;
        RETURN rev;
    END $$;
    REVOKE ALL ON FUNCTION core.lock_inventory_revision() FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION core.lock_inventory_revision() TO sipre_app;
    """)


def downgrade():
    raise RuntimeError("Use a forward migration or separate restore.")
