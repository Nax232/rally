
CREATE DOMAIN core.nonnegative AS numeric CHECK (VALUE >= 0 AND VALUE < 'Infinity'::numeric);
CREATE DOMAIN core.positive AS numeric CHECK (VALUE > 0 AND VALUE < 'Infinity'::numeric);
CREATE TABLE core.users (
 user_id uuid PRIMARY KEY, login text NOT NULL UNIQUE CHECK(length(login) BETWEEN 3 AND 100),
 password_hash text NOT NULL CHECK(password_hash LIKE '$argon2id$%'), active boolean NOT NULL DEFAULT true,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE core.roles(role_code text PRIMARY KEY);
INSERT INTO core.roles VALUES ('ADMIN'),('OPERATOR'),('ANALYST'),('DECISION_MAKER'),('VIEWER');
CREATE TABLE core.user_roles(user_id uuid REFERENCES core.users, role_code text REFERENCES core.roles, PRIMARY KEY(user_id,role_code));
CREATE TABLE core.sessions (
 token_hash text PRIMARY KEY, user_id uuid NOT NULL REFERENCES core.users, csrf_hash text NOT NULL,
 expires_at timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ON core.sessions(user_id);
CREATE TABLE core.login_attempts (
 login_key text PRIMARY KEY, failures integer NOT NULL DEFAULT 0, window_start timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE ops.emergencies (
 emergency_id uuid PRIMARY KEY, name text NOT NULL CHECK(length(trim(name))>0), hazard_type text NOT NULL,
 territory text NOT NULL, description text NOT NULL, start_at timestamptz NOT NULL,
 mode text NOT NULL DEFAULT 'SIMULATED' CHECK(mode='SIMULATED'),
 state text NOT NULL DEFAULT 'DRAFT' CHECK(state IN ('DRAFT','ACTIVE','CLOSED','CANCELLED')),
 input_revision bigint NOT NULL DEFAULT 1, created_by uuid NOT NULL REFERENCES core.users,
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE core.emergency_members (
 emergency_id uuid REFERENCES ops.emergencies, user_id uuid REFERENCES core.users,
 PRIMARY KEY(emergency_id,user_id)
);
CREATE TABLE audit.events (
 audit_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), actor_id uuid REFERENCES core.users,
 action text NOT NULL, object_type text NOT NULL, object_id text NOT NULL,
 emergency_id uuid REFERENCES ops.emergencies, event_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 metadata jsonb NOT NULL DEFAULT '{}'
);
CREATE INDEX ON audit.events(emergency_id,event_at);
CREATE TABLE ops.sources (
 source_id uuid PRIMARY KEY, organization text NOT NULL CHECK(length(trim(organization))>0),
 kind text NOT NULL, description text NOT NULL, created_by uuid NOT NULL REFERENCES core.users,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE geo.zones (
 zone_id uuid PRIMARY KEY, emergency_id uuid NOT NULL REFERENCES ops.emergencies,
 external_id text NOT NULL, name text NOT NULL, geom geometry(MultiPolygon,4326) NOT NULL,
 centroid_geom geometry(Point,4326) GENERATED ALWAYS AS (ST_PointOnSurface(geom)) STORED,
 baseline_population bigint NOT NULL CHECK(baseline_population>=0),
 source_id uuid NOT NULL REFERENCES ops.sources, baseline_at timestamptz NOT NULL,
 quality text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(emergency_id,zone_id), UNIQUE(emergency_id,external_id),
 CHECK(ST_IsValid(geom) AND NOT ST_IsEmpty(geom)),
 CHECK(ST_XMin(Box3D(geom))>=-180 AND ST_XMax(Box3D(geom))<=180 AND ST_YMin(Box3D(geom))>=-90 AND ST_YMax(Box3D(geom))<=90),
 CHECK(baseline_at<=created_at)
);
CREATE INDEX ON geo.zones USING gist(geom);
CREATE TABLE ops.reports (
 report_id uuid PRIMARY KEY, emergency_id uuid NOT NULL, zone_id uuid NOT NULL,
 source_id uuid NOT NULL REFERENCES ops.sources, observed_at timestamptz NOT NULL,
 recorded_at timestamptz NOT NULL DEFAULT now(), status text NOT NULL,
 comments text NOT NULL, raw_payload jsonb NOT NULL DEFAULT '{}',
 supersedes_id uuid UNIQUE, created_by uuid NOT NULL REFERENCES core.users,
 UNIQUE(emergency_id,zone_id,report_id),
 FOREIGN KEY(emergency_id,zone_id) REFERENCES geo.zones(emergency_id,zone_id),
 FOREIGN KEY(emergency_id,zone_id,supersedes_id) REFERENCES ops.reports(emergency_id,zone_id,report_id),
 CHECK(observed_at<=recorded_at), CHECK(supersedes_id IS NULL OR supersedes_id<>report_id)
);
CREATE TABLE ops.observations (
 observation_id uuid PRIMARY KEY, report_id uuid NOT NULL REFERENCES ops.reports,
 metric_code text NOT NULL, value_numeric core.nonnegative, unit text NOT NULL,
 evidence_status text NOT NULL CHECK(evidence_status IN ('OBSERVED','ESTIMATED_APPROVED','UNKNOWN')),
 quality_flags jsonb NOT NULL DEFAULT '[]', approved_by uuid REFERENCES core.users,
 UNIQUE(report_id,metric_code),
 CHECK((evidence_status='UNKNOWN')=(value_numeric IS NULL)),
 CHECK(evidence_status<>'ESTIMATED_APPROVED' OR approved_by IS NOT NULL)
);
CREATE TABLE ops.resource_types (
 resource_type_id uuid PRIMARY KEY, code text NOT NULL UNIQUE, unit text NOT NULL,
 discrete boolean NOT NULL, kg_per_unit core.nonnegative NOT NULL, m3_per_unit core.nonnegative NOT NULL,
 UNIQUE(resource_type_id,unit)
);
CREATE TABLE ops.specialty_types (
 specialty_type_id uuid PRIMARY KEY, code text NOT NULL UNIQUE, unit text NOT NULL DEFAULT 'unit' CHECK(unit='unit'),
 UNIQUE(specialty_type_id,unit)
);
CREATE TABLE ops.needs (
 need_id uuid PRIMARY KEY, emergency_id uuid NOT NULL, zone_id uuid NOT NULL,
 resource_type_id uuid, specialty_type_id uuid, quantity core.nonnegative, unit text NOT NULL,
 status text NOT NULL CHECK(status IN ('CONFIRMED','ESTIMATED_APPROVED','UNKNOWN')),
 urgency text NOT NULL, source_id uuid NOT NULL REFERENCES ops.sources,
 reported_at timestamptz NOT NULL, recorded_at timestamptz NOT NULL DEFAULT now(),
 approved_by uuid REFERENCES core.users, created_by uuid NOT NULL REFERENCES core.users, supersedes_id uuid UNIQUE,
 UNIQUE(emergency_id,zone_id,need_id),
 FOREIGN KEY(emergency_id,zone_id) REFERENCES geo.zones(emergency_id,zone_id),
 FOREIGN KEY(resource_type_id,unit) REFERENCES ops.resource_types(resource_type_id,unit),
 FOREIGN KEY(specialty_type_id,unit) REFERENCES ops.specialty_types(specialty_type_id,unit),
 FOREIGN KEY(emergency_id,zone_id,supersedes_id) REFERENCES ops.needs(emergency_id,zone_id,need_id),
 CHECK(num_nonnulls(resource_type_id,specialty_type_id)=1),
 CHECK((status='UNKNOWN')=(quantity IS NULL)),
 CHECK(status<>'ESTIMATED_APPROVED' OR approved_by IS NOT NULL),
 CHECK(reported_at<=recorded_at), CHECK(supersedes_id IS NULL OR supersedes_id<>need_id)
);
CREATE TABLE ops.depots (
 depot_id uuid PRIMARY KEY, name text NOT NULL, geom geometry(Point,4326) NOT NULL,
 active boolean NOT NULL DEFAULT true, source_id uuid NOT NULL REFERENCES ops.sources,
 CHECK(NOT ST_IsEmpty(geom) AND ST_IsValid(geom) AND ST_X(geom) BETWEEN -180 AND 180 AND ST_Y(geom) BETWEEN -90 AND 90)
);
CREATE INDEX ON ops.depots USING gist(geom);
CREATE TABLE core.inventory_revision(singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton), revision bigint NOT NULL);
INSERT INTO core.inventory_revision VALUES(true,0);
CREATE TABLE ops.inventory_balances (
 depot_id uuid REFERENCES ops.depots, resource_type_id uuid REFERENCES ops.resource_types,
 quantity core.nonnegative NOT NULL DEFAULT 0, reserved core.nonnegative NOT NULL DEFAULT 0,
 revision bigint NOT NULL DEFAULT 0, updated_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(depot_id,resource_type_id), CHECK(reserved<=quantity), CHECK(reserved=0)
);
-- No reservations until H8: F9 cannot fabricate a human decision or reserve stock.
CREATE TABLE ops.inventory_ledger (
 entry_id uuid PRIMARY KEY, depot_id uuid NOT NULL REFERENCES ops.depots,
 resource_type_id uuid NOT NULL REFERENCES ops.resource_types,
 change_quantity numeric NOT NULL CHECK(change_quantity NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric) AND change_quantity<>0),
 reason text NOT NULL CHECK(length(trim(reason))>0), source_id uuid NOT NULL REFERENCES ops.sources,
 created_by uuid NOT NULL REFERENCES core.users, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE ops.physical_assets (
 asset_id uuid PRIMARY KEY, asset_tag text NOT NULL UNIQUE, type text NOT NULL,
 state text NOT NULL CHECK(state IN ('AVAILABLE','UNAVAILABLE','MAINTENANCE')),
 base_id uuid NOT NULL REFERENCES ops.depots, source_id uuid NOT NULL REFERENCES ops.sources,
 row_version bigint NOT NULL DEFAULT 1, updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE ops.vehicles (
 asset_id uuid PRIMARY KEY REFERENCES ops.physical_assets, max_kg core.positive NOT NULL,
 max_m3 core.positive NOT NULL, base_depot_id uuid NOT NULL REFERENCES ops.depots
);
CREATE TABLE ops.specialized_units (
 asset_id uuid PRIMARY KEY REFERENCES ops.physical_assets,
 specialty_type_id uuid NOT NULL REFERENCES ops.specialty_types,
 qualification_status text NOT NULL CHECK(qualification_status IN ('QUALIFIED','UNVERIFIED','EXPIRED')),
 base_depot_id uuid NOT NULL REFERENCES ops.depots
);
CREATE TABLE model.input_snapshots (
 snapshot_id uuid PRIMARY KEY, emergency_id uuid NOT NULL REFERENCES ops.emergencies,
 cutoff_at timestamptz NOT NULL, input_revision bigint NOT NULL, inventory_revision bigint NOT NULL,
 network_revision bigint NOT NULL DEFAULT 0, fingerprint text NOT NULL CHECK(length(fingerprint)=64),
 payload jsonb NOT NULL, created_by uuid NOT NULL REFERENCES core.users,
 created_at timestamptz NOT NULL DEFAULT now(), CHECK(cutoff_at<=created_at)
);
CREATE TABLE core.job_runs (
 job_id uuid PRIMARY KEY, emergency_id uuid NOT NULL REFERENCES ops.emergencies,
 snapshot_id uuid NOT NULL REFERENCES model.input_snapshots, kind text NOT NULL CHECK(kind='SNAPSHOT_VERIFY'),
 state text NOT NULL DEFAULT 'QUEUED' CHECK(state IN ('QUEUED','RUNNING','SUCCESS','FAILED')),
 created_by uuid NOT NULL REFERENCES core.users, created_at timestamptz NOT NULL DEFAULT now(),
 attempts integer NOT NULL DEFAULT 0, owner_token uuid, lease_until timestamptz,
 result jsonb, error_code text, ended_at timestamptz
);
CREATE INDEX ON core.job_runs(state,lease_until);
CREATE TABLE core.idempotency (
 user_id uuid REFERENCES core.users, key text NOT NULL, request_hash text NOT NULL,
 status_code integer NOT NULL, response jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(user_id,key)
);
CREATE FUNCTION core.immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'IMMUTABLE_RECORD' USING ERRCODE='23514'; END $$;
CREATE FUNCTION core.audit_change() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
 SET search_path=pg_catalog,public AS $$
DECLARE actor uuid; item jsonb; eid uuid;
BEGIN
 actor := nullif(current_setting('sipre.actor_id',true),'')::uuid;
 IF actor IS NULL THEN RAISE EXCEPTION 'ACTOR_REQUIRED' USING ERRCODE='23514'; END IF;
 item := to_jsonb(NEW);
 eid := (item->>'emergency_id')::uuid;
 INSERT INTO audit.events(actor_id,action,object_type,object_id,emergency_id,metadata)
 VALUES(actor,TG_OP,TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,
 coalesce(item->>'emergency_id',item->>'asset_id',item->>'entry_id',item->>'source_id',item->>'zone_id',item->>'report_id',item->>'need_id','catalog'),
 eid,jsonb_build_object('row',item - 'password_hash' - 'raw_payload'));
 RETURN NEW;
END $$;
CREATE FUNCTION core.guard_emergency() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
 SET search_path=pg_catalog,public AS $$
DECLARE s text;
BEGIN
 SELECT state INTO s FROM ops.emergencies WHERE emergency_id=NEW.emergency_id FOR UPDATE;
 IF s IN ('CLOSED','CANCELLED') THEN RAISE EXCEPTION 'EMERGENCY_CLOSED' USING ERRCODE='23514'; END IF;
 UPDATE ops.emergencies SET input_revision=input_revision+1,updated_at=now() WHERE emergency_id=NEW.emergency_id;
 RETURN NEW;
END $$;
CREATE FUNCTION core.guard_state() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF OLD.state IN ('CLOSED','CANCELLED') THEN RAISE EXCEPTION 'EMERGENCY_CLOSED' USING ERRCODE='23514'; END IF;
 IF NEW.state NOT IN (OLD.state,'CLOSED','CANCELLED') AND NOT (OLD.state='DRAFT' AND NEW.state='ACTIVE')
 THEN RAISE EXCEPTION 'INVALID_STATE_TRANSITION' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER emergency_state BEFORE UPDATE ON ops.emergencies FOR EACH ROW EXECUTE FUNCTION core.guard_state();
CREATE FUNCTION core.check_need() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.quantity IS NOT NULL AND NEW.quantity<>trunc(NEW.quantity) AND
 (NEW.specialty_type_id IS NOT NULL OR EXISTS(SELECT 1 FROM ops.resource_types WHERE resource_type_id=NEW.resource_type_id AND discrete))
 THEN RAISE EXCEPTION 'INDIVISIBLE_RESOURCE' USING ERRCODE='23514'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER need_units BEFORE INSERT ON ops.needs FOR EACH ROW EXECUTE FUNCTION core.check_need();
CREATE FUNCTION core.apply_stock() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
 SET search_path=pg_catalog,public AS $$
BEGIN
 PERFORM 1 FROM core.inventory_revision WHERE singleton FOR UPDATE;
 IF NEW.change_quantity<>trunc(NEW.change_quantity) AND
 EXISTS(SELECT 1 FROM ops.resource_types WHERE resource_type_id=NEW.resource_type_id AND discrete)
 THEN RAISE EXCEPTION 'INDIVISIBLE_RESOURCE' USING ERRCODE='23514'; END IF;
 INSERT INTO ops.inventory_balances(depot_id,resource_type_id) VALUES(NEW.depot_id,NEW.resource_type_id)
 ON CONFLICT DO NOTHING;
 UPDATE ops.inventory_balances SET quantity=quantity+NEW.change_quantity,revision=revision+1,updated_at=now()
 WHERE depot_id=NEW.depot_id AND resource_type_id=NEW.resource_type_id;
 UPDATE core.inventory_revision SET revision=revision+1 WHERE singleton;
 RETURN NEW;
END $$;
CREATE TRIGGER stock_insert BEFORE INSERT ON ops.inventory_ledger FOR EACH ROW EXECUTE FUNCTION core.apply_stock();
CREATE FUNCTION core.asset_revision() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
 SET search_path=pg_catalog,public AS $$
BEGIN
 UPDATE core.inventory_revision SET revision=revision+1 WHERE singleton;
 IF TG_OP='UPDATE' THEN NEW.row_version:=OLD.row_version+1; NEW.updated_at:=now(); END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER asset_revision BEFORE INSERT OR UPDATE ON ops.physical_assets FOR EACH ROW EXECUTE FUNCTION core.asset_revision();
CREATE VIEW analytics.v_foundation_status AS
 SELECT mode,state,count(*) AS emergency_count FROM ops.emergencies GROUP BY mode,state;
GRANT USAGE ON SCHEMA core,ops,geo,model,audit TO sipre_app;
GRANT USAGE ON SCHEMA core,model,ops,audit TO sipre_worker;
GRANT SELECT ON ALL TABLES IN SCHEMA core,ops,geo,model,audit TO sipre_app;
GRANT INSERT,UPDATE ON core.users TO sipre_app;
GRANT INSERT,DELETE ON core.user_roles,core.emergency_members TO sipre_app;
GRANT INSERT,UPDATE,DELETE ON core.sessions,core.login_attempts TO sipre_app;
GRANT INSERT ON core.idempotency,core.job_runs,audit.events,model.input_snapshots TO sipre_app;
GRANT INSERT,UPDATE ON ops.emergencies,ops.physical_assets TO sipre_app;
GRANT INSERT ON ops.sources,geo.zones,ops.reports,ops.observations,ops.needs,
 ops.resource_types,ops.specialty_types,ops.depots,ops.inventory_ledger,ops.vehicles,ops.specialized_units TO sipre_app;
GRANT SELECT,UPDATE ON core.job_runs TO sipre_worker;
GRANT SELECT ON model.input_snapshots TO sipre_worker;
GRANT INSERT ON audit.events TO sipre_worker;
GRANT SELECT ON analytics.v_foundation_status TO sipre_metabase_reader;

