"""H7 scenario road network: nodes, edges, versioned routes and invalidation."""

from pathlib import Path

from alembic import op

revision = "0005_gis_network"
down_revision = "0004_snapshot_lock"
branch_labels = None
depends_on = None


def upgrade():
    sql_path = Path(__file__).parent.parent / "sql" / "0005_gis_network.sql"
    sql = sql_path.read_text(encoding="utf-8")
    op.execute(sql)
    op.execute(
        "CREATE TRIGGER road_nodes_immutable BEFORE UPDATE OR DELETE ON geo.road_nodes "
        "FOR EACH ROW EXECUTE FUNCTION core.immutable()"
    )
    op.execute(
        "CREATE TRIGGER road_edges_immutable BEFORE DELETE ON geo.road_edges "
        "FOR EACH ROW EXECUTE FUNCTION core.immutable()"
    )
    op.execute(
        "CREATE TRIGGER route_candidates_immutable BEFORE UPDATE ON geo.route_candidates "
        "FOR EACH ROW EXECUTE FUNCTION core.immutable()"
    )
    op.execute(
        "CREATE TRIGGER route_candidate_edges_immutable BEFORE UPDATE OR DELETE "
        "ON geo.route_candidate_edges FOR EACH ROW EXECUTE FUNCTION core.immutable()"
    )


def downgrade():
    raise RuntimeError("Use a forward migration or separate restore.")
