"""Persist reproducible F4 SIMULATED priority runs and read-only BI projections."""

from alembic import op

revision = "0007_prioritization"
down_revision = "0006_route_invalidation"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE core.job_runs DROP CONSTRAINT job_runs_kind_check")
    op.execute(
        "ALTER TABLE core.job_runs ADD CONSTRAINT job_runs_kind_check "
        "CHECK(kind IN ('SNAPSHOT_VERIFY','PRIORITY'))"
    )
    op.execute(
        """CREATE TABLE model.priority_runs (
          run_id uuid PRIMARY KEY,
          emergency_id uuid NOT NULL REFERENCES ops.emergencies,
          snapshot_id uuid NOT NULL,
          job_id uuid NOT NULL UNIQUE REFERENCES core.job_runs,
          profile_version text NOT NULL,
          profile_hash text NOT NULL CHECK(length(profile_hash)=64),
          profile jsonb NOT NULL,
          created_by uuid NOT NULL REFERENCES core.users,
          created_at timestamptz NOT NULL DEFAULT now(),
          UNIQUE(run_id,emergency_id),
          FOREIGN KEY(emergency_id,snapshot_id)
            REFERENCES model.input_snapshots(emergency_id,snapshot_id)
        )"""
    )
    op.execute(
        """CREATE TABLE model.priority_results (
          run_id uuid NOT NULL,
          emergency_id uuid NOT NULL,
          zone_id uuid NOT NULL,
          priority_rank integer NOT NULL CHECK(priority_rank>0),
          priority_score double precision NOT NULL CHECK(priority_score BETWEEN 0 AND 1),
          score_lower double precision NOT NULL CHECK(score_lower BETWEEN 0 AND 1),
          score_upper double precision NOT NULL CHECK(score_upper BETWEEN 0 AND 1),
          priority_level text NOT NULL CHECK(priority_level IN ('BAJA','MEDIA','ALTA','CRITICA')),
          uncertainty_index double precision NOT NULL CHECK(uncertainty_index BETWEEN 0 AND 1),
          needs_verification boolean NOT NULL,
          insufficient_evidence boolean NOT NULL,
          details jsonb NOT NULL,
          PRIMARY KEY(run_id,zone_id),
          UNIQUE(run_id,priority_rank),
          FOREIGN KEY(run_id,emergency_id) REFERENCES model.priority_runs(run_id,emergency_id),
          FOREIGN KEY(emergency_id,zone_id) REFERENCES geo.zones(emergency_id,zone_id),
          CHECK(score_lower<=priority_score AND priority_score<=score_upper)
        )"""
    )
    op.execute(
        """CREATE TABLE model.priority_factors (
          run_id uuid NOT NULL,
          zone_id uuid NOT NULL,
          criterion_code text NOT NULL CHECK(criterion_code IN
            ('C1','C2','C3','C4','C5','C6','C7','C8')),
          normalized_value double precision NOT NULL CHECK(normalized_value BETWEEN 0 AND 1),
          weight double precision NOT NULL CHECK(weight>0 AND weight<=1),
          evidence_status text NOT NULL CHECK(evidence_status IN
            ('observed','estimated','missing')),
          source text,
          dplus_contribution double precision NOT NULL CHECK(dplus_contribution>=0),
          dminus_contribution double precision NOT NULL CHECK(dminus_contribution>=0),
          delta_counterfactual double precision NOT NULL,
          PRIMARY KEY(run_id,zone_id,criterion_code),
          FOREIGN KEY(run_id,zone_id) REFERENCES model.priority_results(run_id,zone_id)
        )"""
    )
    for table in ("priority_runs", "priority_results", "priority_factors"):
        op.execute(
            f"CREATE TRIGGER {table}_immutable BEFORE UPDATE OR DELETE "
            f"ON model.{table} FOR EACH ROW EXECUTE FUNCTION core.immutable()"
        )
    op.execute("GRANT SELECT,INSERT ON model.priority_runs TO sipre_app")
    op.execute("GRANT SELECT ON model.priority_runs TO sipre_worker")
    op.execute("GRANT SELECT ON model.priority_results,model.priority_factors TO sipre_app")
    op.execute(
        "GRANT SELECT,INSERT ON model.priority_results,model.priority_factors TO sipre_worker"
    )
    op.execute(
        """CREATE VIEW analytics.v_priority_results AS
          SELECT r.emergency_id,r.zone_id,z.name AS zone_name,r.run_id,
            s.cutoff_at AS evaluated_at,r.priority_rank,r.priority_score,
            r.score_lower,r.score_upper,r.priority_level,r.uncertainty_index,
            r.needs_verification,r.insufficient_evidence,
            p.profile_version,p.profile->>'validation' AS profile_validation,
            (r.details->>'observation_age_hours')::double precision AS observation_age_hours,
            (r.details->>'missing_criteria_count')::integer AS missing_criteria_count,
            p.profile_hash
          FROM model.priority_results r
          JOIN model.priority_runs p USING(run_id)
          JOIN model.input_snapshots s ON s.snapshot_id=p.snapshot_id
          JOIN geo.zones z ON z.zone_id=r.zone_id
          JOIN core.job_runs j ON j.job_id=p.job_id
          WHERE j.state='SUCCESS'"""
    )
    op.execute(
        """CREATE VIEW analytics.v_priority_factors AS
          SELECT r.emergency_id,f.run_id,f.zone_id,f.criterion_code,
            f.normalized_value,f.weight,f.evidence_status,f.source,
            f.dplus_contribution,f.dminus_contribution,f.delta_counterfactual
          FROM model.priority_factors f
          JOIN model.priority_results r USING(run_id,zone_id)
          JOIN model.priority_runs p USING(run_id)
          JOIN core.job_runs j ON j.job_id=p.job_id
          WHERE j.state='SUCCESS'"""
    )
    op.execute(
        "GRANT SELECT ON analytics.v_priority_results,analytics.v_priority_factors "
        "TO sipre_metabase_reader"
    )


def downgrade():
    raise RuntimeError("Use a forward migration or separate restore.")
