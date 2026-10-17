"""Create F6 schema namespaces; business tables await F2/F3.

Revision ID: 0001_namespaces
Revises: none
"""

from alembic import op

revision = "0001_namespaces"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # core is provisioned with its owner before Alembic creates its version table.
    for schema in ("ops", "geo", "model", "planning", "audit", "experiments", "analytics"):
        op.execute(f"CREATE SCHEMA {schema} AUTHORIZATION sipre_migrator")
    for schema in ("core", "ops", "geo", "model", "planning", "audit", "experiments", "analytics"):
        op.execute(f"REVOKE ALL ON SCHEMA {schema} FROM PUBLIC")
        op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA {schema} REVOKE ALL ON TABLES FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA analytics TO sipre_metabase_reader")
    # No broad/default SELECT: a later migration grants only specific curated views.
    # No app writes until business tables and capability boundaries are approved.


def downgrade():
    raise RuntimeError(
        "Destructive schema rollback is intentionally disabled. "
        "Use a reviewed forward migration or restore into a separate database."
    )
