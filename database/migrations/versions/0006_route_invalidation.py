"""Allow route invalidation to cascade while preventing direct edge deletion."""

from alembic import op

revision = "0006_route_invalidation"
down_revision = "0005_gis_network"
branch_labels = None
depends_on = None


def upgrade():
    # Blocking an edge deletes affected ephemeral candidates. The FK cascade
    # must be able to remove their sequence rows in the same transaction.
    op.execute(
        "DROP TRIGGER IF EXISTS route_candidate_edges_immutable ON geo.route_candidate_edges"
    )
    op.execute(
        "CREATE TRIGGER route_candidate_edges_immutable BEFORE UPDATE "
        "ON geo.route_candidate_edges FOR EACH ROW EXECUTE FUNCTION core.immutable()"
    )
    op.execute("REVOKE DELETE ON geo.route_candidate_edges FROM sipre_app")


def downgrade():
    raise RuntimeError("Use a forward migration or separate restore.")
