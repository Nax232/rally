"""Immutable, bounded effective-assistance facts for F4 C7 in SIMULATED mode."""

from alembic import op

revision = "0008_simulated_assistance"
down_revision = "0007_prioritization"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """CREATE TABLE ops.assistance_events (
          event_id uuid PRIMARY KEY,
          emergency_id uuid NOT NULL,
          zone_id uuid NOT NULL,
          need_id uuid NOT NULL,
          quantity core.positive NOT NULL,
          effective_at timestamptz NOT NULL,
          recorded_at timestamptz NOT NULL DEFAULT now(),
          source_id uuid NOT NULL REFERENCES ops.sources,
          note text NOT NULL CHECK(length(trim(note))>0),
          created_by uuid NOT NULL REFERENCES core.users,
          FOREIGN KEY(emergency_id,zone_id,need_id)
            REFERENCES ops.needs(emergency_id,zone_id,need_id),
          CHECK(effective_at<=recorded_at)
        )"""
    )
    op.execute("CREATE INDEX ON ops.assistance_events(need_id,effective_at)")
    op.execute(
        """CREATE FUNCTION core.check_simulated_assistance() RETURNS trigger
          LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
          DECLARE n record; delivered numeric; emergency_mode text;
          BEGIN
            SELECT mode INTO emergency_mode FROM ops.emergencies
              WHERE emergency_id=NEW.emergency_id;
            IF emergency_mode IS DISTINCT FROM 'SIMULATED' THEN
              RAISE EXCEPTION 'SIMULATED_ONLY' USING ERRCODE='23514';
            END IF;
            SELECT * INTO n FROM ops.needs WHERE need_id=NEW.need_id FOR UPDATE;
            IF n.need_id IS NULL OR n.status='UNKNOWN' OR n.quantity IS NULL OR n.quantity=0
              OR n.emergency_id<>NEW.emergency_id OR n.zone_id<>NEW.zone_id THEN
              RAISE EXCEPTION 'ASSISTANCE_NEED_INVALID' USING ERRCODE='23514';
            END IF;
            IF EXISTS(SELECT 1 FROM ops.needs WHERE supersedes_id=NEW.need_id) THEN
              RAISE EXCEPTION 'ASSISTANCE_NEED_SUPERSEDED' USING ERRCODE='23514';
            END IF;
            IF NEW.effective_at<n.reported_at THEN
              RAISE EXCEPTION 'ASSISTANCE_BEFORE_NEED' USING ERRCODE='23514';
            END IF;
            SELECT coalesce(sum(quantity),0) INTO delivered FROM ops.assistance_events
              WHERE need_id=NEW.need_id;
            IF delivered+NEW.quantity>n.quantity THEN
              RAISE EXCEPTION 'ASSISTANCE_EXCEEDS_NEED' USING ERRCODE='23514';
            END IF;
            IF n.specialty_type_id IS NOT NULL OR EXISTS(
              SELECT 1 FROM ops.resource_types
              WHERE resource_type_id=n.resource_type_id AND discrete
            ) THEN
              IF NEW.quantity<>trunc(NEW.quantity) THEN
                RAISE EXCEPTION 'INDIVISIBLE_RESOURCE' USING ERRCODE='23514';
              END IF;
            END IF;
            RETURN NEW;
          END $$"""
    )
    op.execute(
        "CREATE TRIGGER a_guard_emergency BEFORE INSERT ON ops.assistance_events "
        "FOR EACH ROW EXECUTE FUNCTION core.guard_emergency()"
    )
    op.execute(
        "CREATE TRIGGER b_check_assistance BEFORE INSERT ON ops.assistance_events "
        "FOR EACH ROW EXECUTE FUNCTION core.check_simulated_assistance()"
    )
    op.execute(
        "CREATE TRIGGER assistance_immutable BEFORE UPDATE OR DELETE ON ops.assistance_events "
        "FOR EACH ROW EXECUTE FUNCTION core.immutable()"
    )
    op.execute(
        "CREATE TRIGGER assistance_audit AFTER INSERT ON ops.assistance_events "
        "FOR EACH ROW EXECUTE FUNCTION core.audit_change()"
    )
    op.execute("REVOKE ALL ON FUNCTION core.check_simulated_assistance() FROM PUBLIC")
    op.execute("GRANT SELECT,INSERT ON ops.assistance_events TO sipre_app")
    op.execute("GRANT SELECT ON ops.assistance_events TO sipre_worker")


def downgrade():
    raise RuntimeError("Use a forward migration or separate restore.")
