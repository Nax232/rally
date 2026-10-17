"""Strengthen evidence, physical identity and snapshot isolation."""

from alembic import op

revision = "0003_integrity"
down_revision = "0002_foundation"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    ALTER TABLE model.input_snapshots ADD UNIQUE(emergency_id,snapshot_id);
    ALTER TABLE core.job_runs ADD FOREIGN KEY(emergency_id,snapshot_id)
        REFERENCES model.input_snapshots(emergency_id,snapshot_id);
    ALTER TABLE ops.physical_assets ADD UNIQUE(asset_id,base_id);
    ALTER TABLE ops.vehicles ADD FOREIGN KEY(asset_id,base_depot_id)
        REFERENCES ops.physical_assets(asset_id,base_id);
    ALTER TABLE ops.specialized_units ADD FOREIGN KEY(asset_id,base_depot_id)
        REFERENCES ops.physical_assets(asset_id,base_id);
    ALTER TABLE ops.reports ADD CHECK(status='RECORDED');
    CREATE FUNCTION core.global_revision() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
    SET search_path=pg_catalog,public AS $$
    BEGIN
        UPDATE core.inventory_revision SET revision=revision+1 WHERE singleton;
        RETURN NEW;
    END $$;
    CREATE FUNCTION core.validate_evidence() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
    SET search_path=pg_catalog,public AS $$
    DECLARE actor uuid; report_time timestamptz; state text;
    BEGIN
        actor := nullif(current_setting('sipre.actor_id',true),'')::uuid;
        IF NEW.approved_by IS NOT NULL AND (
            NEW.approved_by IS DISTINCT FROM actor OR NOT EXISTS(
                SELECT 1 FROM core.user_roles WHERE user_id=actor AND role_code='DECISION_MAKER'
            )
        ) THEN RAISE EXCEPTION 'ESTIMATE_APPROVAL_REQUIRED' USING ERRCODE='23514'; END IF;
        IF TG_TABLE_NAME='observations' THEN
            SELECT recorded_at INTO report_time FROM ops.reports WHERE report_id=NEW.report_id;
            IF report_time IS DISTINCT FROM transaction_timestamp() THEN
                RAISE EXCEPTION 'REPORT_ALREADY_FINALIZED' USING ERRCODE='23514';
            END IF;
        END IF;
        RETURN NEW;
    END $$;
    REVOKE ALL ON FUNCTION core.global_revision(),core.validate_evidence() FROM PUBLIC;
    """)
    for table in (
        "ops.sources",
        "ops.resource_types",
        "ops.specialty_types",
        "ops.depots",
        "ops.vehicles",
        "ops.specialized_units",
    ):
        op.execute(
            f"CREATE TRIGGER global_revision BEFORE INSERT ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION core.global_revision()"
        )
    for table in ("ops.observations", "ops.needs"):
        op.execute(
            f"CREATE TRIGGER evidence BEFORE INSERT ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION core.validate_evidence()"
        )


def downgrade():
    raise RuntimeError("Forward migration or separate restore required.")
