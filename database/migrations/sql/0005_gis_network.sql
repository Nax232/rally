-- H7 GIS: scenario road network, versioned route candidates and invalidation.
-- Distances are stored in metres (geography), never degrees. UNKNOWN is not transit by default.

CREATE TABLE core.network_revision (
 singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
 revision bigint NOT NULL DEFAULT 0,
 updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO core.network_revision VALUES(true,0,now());
CREATE FUNCTION core.lock_network_revision() RETURNS bigint
 LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE rev bigint;
BEGIN
 SELECT revision INTO rev FROM core.network_revision WHERE singleton FOR UPDATE;
 RETURN rev;
END $$;
REVOKE ALL ON FUNCTION core.lock_network_revision() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION core.lock_network_revision() TO sipre_app;

CREATE TABLE geo.road_nodes (
 node_id uuid PRIMARY KEY,
 emergency_id uuid NOT NULL REFERENCES ops.emergencies,
 external_id text NOT NULL,
 geom geometry(Point,4326) NOT NULL,
 UNIQUE(emergency_id,node_id),
 UNIQUE(emergency_id,external_id),
 CHECK(NOT ST_IsEmpty(geom) AND ST_IsValid(geom)),
 CHECK(ST_X(geom) BETWEEN -180 AND 180 AND ST_Y(geom) BETWEEN -90 AND 90)
);
CREATE INDEX ON geo.road_nodes USING gist(geom);

CREATE TABLE geo.road_edges (
 edge_id uuid PRIMARY KEY,
 emergency_id uuid NOT NULL REFERENCES ops.emergencies,
 external_id text NOT NULL,
 from_node uuid NOT NULL,
 to_node uuid NOT NULL,
 geom geometry(LineString,4326) NOT NULL,
 length_m core.positive NOT NULL,
 travel_sec core.positive NOT NULL,
 status text NOT NULL CHECK(status IN ('VERIFIED_OPEN','VERIFIED_RESTRICTED','BLOCKED','UNKNOWN')),
 allowed_vehicle_types text[] NOT NULL DEFAULT '{}' CHECK(cardinality(allowed_vehicle_types)<=50),
 network_revision bigint NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 row_version bigint NOT NULL DEFAULT 1,
 UNIQUE(emergency_id,edge_id),
 UNIQUE(emergency_id,external_id),
 UNIQUE(emergency_id,from_node,to_node),
 FOREIGN KEY(emergency_id,from_node) REFERENCES geo.road_nodes(emergency_id,node_id),
 FOREIGN KEY(emergency_id,to_node) REFERENCES geo.road_nodes(emergency_id,node_id),
 CHECK(from_node<>to_node),
 CHECK(NOT ST_IsEmpty(geom) AND ST_IsValid(geom) AND ST_GeometryType(geom)='ST_LineString' AND ST_SRID(geom)=4326),
 CHECK(ST_NPoints(geom)>=2),
 CHECK(network_revision>=0),
 CHECK(NOT (status='VERIFIED_OPEN' AND cardinality(allowed_vehicle_types)>0)),
 CHECK(NOT ('' = ANY(allowed_vehicle_types)))
);
CREATE INDEX ON geo.road_edges USING gist(geom);
CREATE INDEX ON geo.road_edges(emergency_id,status);

CREATE TABLE geo.route_candidates (
 route_id uuid PRIMARY KEY,
 emergency_id uuid NOT NULL REFERENCES ops.emergencies,
 external_id text NOT NULL,
 depot_id uuid NOT NULL REFERENCES ops.depots,
 zone_id uuid NOT NULL,
 vehicle_type text NOT NULL CHECK(length(vehicle_type) BETWEEN 1 AND 50),
 path_geom geometry(LineString,4326) NOT NULL,
 length_m core.positive NOT NULL,
 travel_sec core.positive NOT NULL,
 unload_sec core.positive NOT NULL,
 return_length_m double precision NOT NULL CHECK(return_length_m>=0),
 return_travel_sec double precision NOT NULL CHECK(return_travel_sec>=0),
 require_return boolean NOT NULL,
 route_status text NOT NULL CHECK(route_status IN ('VERIFIED_OPEN','VERIFIED_RESTRICTED')),
 network_revision bigint NOT NULL,
 expires_at timestamptz NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(emergency_id,route_id),
 UNIQUE(emergency_id,external_id),
 FOREIGN KEY(emergency_id,zone_id) REFERENCES geo.zones(emergency_id,zone_id),
 CHECK(NOT ST_IsEmpty(path_geom) AND ST_IsValid(path_geom) AND ST_GeometryType(path_geom)='ST_LineString' AND ST_SRID(path_geom)=4326),
 CHECK(unload_sec>0 AND network_revision>=0 AND expires_at>created_at)
);
CREATE INDEX ON geo.route_candidates(emergency_id,route_status);
CREATE INDEX ON geo.route_candidates(emergency_id,depot_id,vehicle_type,zone_id);
CREATE INDEX ON geo.route_candidates(expires_at);

CREATE TABLE geo.route_candidate_edges (
 route_id uuid NOT NULL REFERENCES geo.route_candidates(route_id) ON DELETE CASCADE,
 edge_id uuid NOT NULL,
 sequence_no integer NOT NULL CHECK(sequence_no>=0),
 direction text NOT NULL CHECK(direction IN ('forward','backward')),
 PRIMARY KEY(route_id,sequence_no),
 UNIQUE(route_id,edge_id)
);
CREATE INDEX ON geo.route_candidate_edges(edge_id);

-- Every network mutation is a new revision. Audit uses the pre-update row so
-- the invalidation that follows still sees the correct network_revision.
CREATE FUNCTION core.touch_network_revision() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
 SET search_path=pg_catalog,public AS $$
BEGIN
 UPDATE core.network_revision SET revision=revision+1,updated_at=now() WHERE singleton;
 RETURN NEW;
END $$;
CREATE FUNCTION core.network_revision_column() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
 SET search_path=pg_catalog,public AS $$
DECLARE rev bigint;
BEGIN
 SELECT revision INTO rev FROM core.network_revision WHERE singleton FOR UPDATE;
 NEW.network_revision:=rev;
 RETURN NEW;
END $$;
CREATE FUNCTION core.audit_network_edge() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
 SET search_path=pg_catalog,public AS $$
DECLARE actor uuid; item jsonb;
BEGIN
 actor := nullif(current_setting('sipre.actor_id',true),'')::uuid;
 IF actor IS NULL THEN RAISE EXCEPTION 'ACTOR_REQUIRED' USING ERRCODE='23514'; END IF;
 IF TG_OP='INSERT' THEN
  INSERT INTO audit.events(actor_id,action,object_type,object_id,emergency_id,metadata)
  VALUES(actor,'INSERT',TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,
  NEW.edge_id,NEW.emergency_id,jsonb_build_object('after',to_jsonb(NEW)));
  RETURN NEW;
 END IF;
 item := to_jsonb(OLD);
 INSERT INTO audit.events(actor_id,action,object_type,object_id,emergency_id,metadata)
 VALUES(actor,TG_OP,TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,
 coalesce(NEW.edge_id,OLD.edge_id),coalesce(NEW.emergency_id,OLD.emergency_id),
 jsonb_build_object('before',item,'after',to_jsonb(NEW)));
 RETURN OLD;
END $$;
CREATE FUNCTION core.audit_network_node() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
 SET search_path=pg_catalog,public AS $$
DECLARE actor uuid; item jsonb;
BEGIN
 actor := nullif(current_setting('sipre.actor_id',true),'')::uuid;
 IF actor IS NULL THEN RAISE EXCEPTION 'ACTOR_REQUIRED' USING ERRCODE='23514'; END IF;
 IF TG_OP='INSERT' THEN
  INSERT INTO audit.events(actor_id,action,object_type,object_id,emergency_id,metadata)
  VALUES(actor,'INSERT',TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,
  NEW.node_id,NEW.emergency_id,jsonb_build_object('after',to_jsonb(NEW)));
  RETURN NEW;
 END IF;
 item := to_jsonb(OLD);
 INSERT INTO audit.events(actor_id,action,object_type,object_id,emergency_id,metadata)
 VALUES(actor,TG_OP,TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,
 coalesce(NEW.node_id,OLD.node_id),coalesce(NEW.emergency_id,OLD.emergency_id),
 jsonb_build_object('before',item,'after',to_jsonb(NEW)));
 RETURN OLD;
END $$;
CREATE FUNCTION core.invalidate_routes_on_edge() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
 SET search_path=pg_catalog,public AS $$
BEGIN
 DELETE FROM geo.route_candidates WHERE route_id IN
 (SELECT route_id FROM geo.route_candidate_edges WHERE edge_id=NEW.edge_id);
 RETURN NEW;
END $$;
CREATE FUNCTION core.guard_edge_transition() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF NEW.status='VERIFIED_OPEN' AND OLD.status IN ('BLOCKED','UNKNOWN') THEN
  RAISE EXCEPTION 'REVERIFICATION_REQUIRED' USING ERRCODE='23514';
 END IF;
 IF OLD.status='VERIFIED_OPEN' AND NEW.status='VERIFIED_RESTRICTED'
  AND cardinality(NEW.allowed_vehicle_types)=0 THEN
  RAISE EXCEPTION 'RESTRICTED_REQUIRES_ALLOWED_TYPES' USING ERRCODE='23514';
 END IF;
 IF NEW.status IN ('BLOCKED','UNKNOWN') THEN NEW.allowed_vehicle_types:='{}'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER edge_insert BEFORE INSERT ON geo.road_edges
 FOR EACH ROW EXECUTE FUNCTION core.network_revision_column();
CREATE TRIGGER edge_update BEFORE UPDATE ON geo.road_edges
 FOR EACH ROW EXECUTE FUNCTION core.network_revision_column();
CREATE TRIGGER edge_guard BEFORE UPDATE ON geo.road_edges
 FOR EACH ROW EXECUTE FUNCTION core.guard_edge_transition();
CREATE TRIGGER edge_audit BEFORE UPDATE ON geo.road_edges
 FOR EACH ROW EXECUTE FUNCTION core.audit_network_edge();
CREATE TRIGGER edge_audit_insert BEFORE INSERT ON geo.road_edges
 FOR EACH ROW EXECUTE FUNCTION core.audit_network_edge();
CREATE TRIGGER node_audit_insert BEFORE INSERT ON geo.road_nodes
 FOR EACH ROW EXECUTE FUNCTION core.audit_network_node();
CREATE TRIGGER node_audit BEFORE UPDATE ON geo.road_nodes
 FOR EACH ROW EXECUTE FUNCTION core.audit_network_node();
CREATE TRIGGER edge_revision AFTER UPDATE ON geo.road_edges
 FOR EACH ROW EXECUTE FUNCTION core.touch_network_revision();
CREATE TRIGGER edge_revision_insert AFTER INSERT ON geo.road_edges
 FOR EACH ROW EXECUTE FUNCTION core.touch_network_revision();
CREATE TRIGGER edge_invalidate AFTER UPDATE ON geo.road_edges
 FOR EACH ROW EXECUTE FUNCTION core.invalidate_routes_on_edge();
CREATE TRIGGER node_revision AFTER INSERT ON geo.road_nodes
 FOR EACH ROW EXECUTE FUNCTION core.touch_network_revision();

-- H7 tables are versioned and revisable; foundation immutability does not apply.
DROP TRIGGER IF EXISTS road_nodes_immutable ON geo.road_nodes;
DROP TRIGGER IF EXISTS road_edges_immutable ON geo.road_edges;
DROP TRIGGER IF EXISTS route_candidates_immutable ON geo.route_candidates;
DROP TRIGGER IF EXISTS route_candidate_edges_immutable ON geo.route_candidate_edges;

CREATE VIEW analytics.v_route_conditions AS
 SELECT r.route_id AS route_id, r.zone_id AS zone_id, r.depot_id AS depot_id,
  r.vehicle_type AS vehicle_type, r.route_status AS status,
  round((r.length_m+r.return_length_m)::numeric/1000.0,6) AS distance_km,
  round((r.travel_sec+r.return_travel_sec+r.unload_sec)::numeric/3600.0,6) AS total_time_hr,
  r.network_revision AS network_revision, r.created_at AS last_verified_at,
  r.expires_at AS expires_at, e.mode='SIMULATED' AS simulated
 FROM geo.route_candidates r JOIN ops.emergencies e USING(emergency_id);

GRANT USAGE ON SCHEMA analytics TO sipre_metabase_reader;
GRANT SELECT ON geo.road_nodes,geo.road_edges,geo.route_candidates,geo.route_candidate_edges TO sipre_app;
GRANT INSERT,UPDATE ON geo.road_nodes,geo.road_edges TO sipre_app;
GRANT INSERT,DELETE ON geo.route_candidates,geo.route_candidate_edges TO sipre_app;
GRANT SELECT ON core.network_revision TO sipre_app;
GRANT SELECT ON analytics.v_route_conditions TO sipre_metabase_reader;
