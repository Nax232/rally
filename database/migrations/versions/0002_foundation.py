"""F9 data, identity, immutable evidence and durable jobs."""

from pathlib import Path

from alembic import op

revision = "0002_foundation"
down_revision = "0001_namespaces"
branch_labels = None
depends_on = None


def upgrade():
    sql = (Path(__file__).parent.parent / "sql" / "0002_foundation.sql").read_text(encoding="utf-8")
    op.execute(sql)
    for table in (
        "geo.zones",
        "ops.reports",
        "ops.observations",
        "ops.needs",
        "ops.sources",
        "ops.resource_types",
        "ops.specialty_types",
        "ops.depots",
        "ops.inventory_ledger",
        "model.input_snapshots",
        "audit.events",
    ):
        op.execute(
            f"CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION core.immutable()"
        )
    for table in ("geo.zones", "ops.reports", "ops.needs"):
        op.execute(
            f"CREATE TRIGGER guard_emergency BEFORE INSERT ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION core.guard_emergency()"
        )
    for table in (
        "ops.emergencies",
        "geo.zones",
        "ops.reports",
        "ops.needs",
        "ops.sources",
        "ops.resource_types",
        "ops.specialty_types",
        "ops.depots",
        "ops.inventory_ledger",
        "ops.physical_assets",
        "ops.vehicles",
        "ops.specialized_units",
        "model.input_snapshots",
    ):
        op.execute(
            f"CREATE TRIGGER audit_change AFTER INSERT OR UPDATE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION core.audit_change()"
        )
    op.execute("REVOKE ALL ON ALL FUNCTIONS IN SCHEMA core FROM PUBLIC")


def downgrade():
    raise RuntimeError("Use a forward migration or restore to a separate database.")
