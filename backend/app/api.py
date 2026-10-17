"""F9 operational data API. All writes are transactional and idempotent."""

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app import schemas
from app.security import database, event, hasher, principal, require, scoped

router = APIRouter(prefix="/api/v1", tags=["foundation"])


def encode(value):
    return jsonable_encoder(value, custom_encoder={set: list, Decimal: str})


def canonical(value):
    return json.dumps(encode(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def mutation(db, user, request, payload, action, status=201):
    key = request.headers.get("idempotency-key", "")
    if not 8 <= len(key) <= 128:
        raise HTTPException(422, "IDEMPOTENCY_KEY_REQUIRED_8_TO_128")
    fingerprint = hashlib.sha256(
        (request.method + request.url.path + canonical(payload)).encode()
    ).hexdigest()
    # Serialize the same actor/key; uniqueness also protects retries across processes.
    lock = int.from_bytes(
        hashlib.sha256((str(user["user_id"]) + key).encode()).digest()[:8], "big", signed=True
    )
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock})
    params = {"u": user["user_id"], "k": key}
    previous = (
        db.execute(text("SELECT * FROM core.idempotency WHERE user_id=:u AND key=:k"), params)
        .mappings()
        .first()
    )
    if previous:
        if previous["request_hash"] != fingerprint:
            raise HTTPException(409, "IDEMPOTENCY_KEY_REUSED")
        return JSONResponse(status_code=previous["status_code"], content=previous["response"])
    result = encode(action())
    db.execute(
        text("""INSERT INTO core.idempotency(user_id,key,request_hash,status_code,response)
        VALUES(:u,:k,:h,:s,CAST(:r AS jsonb))"""),
        {**params, "h": fingerprint, "s": status, "r": canonical(result)},
    )
    return JSONResponse(status_code=status, content=result)


def insert(db, table, data, json_fields=()):
    # Only internal constant table/column names reach this helper.
    expressions = [f"CAST(:{k} AS jsonb)" if k in json_fields else f":{k}" for k in data]
    params = {k: canonical(v) if k in json_fields else v for k, v in data.items()}
    db.execute(
        text(f"INSERT INTO {table} ({','.join(data)}) VALUES ({','.join(expressions)})"), params
    )


@router.post("/users")
def add_user(
    body: schemas.UserCreate,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "users")

    def action():
        uid = uuid4()
        insert(
            db,
            "core.users",
            {
                "user_id": uid,
                "login": body.login.casefold(),
                "password_hash": hasher.hash(body.password.get_secret_value()),
            },
        )
        for role in set(body.roles):
            insert(db, "core.user_roles", {"user_id": uid, "role_code": role})
        event(db, user["user_id"], "USER_CREATED", "users", uid)
        return {"user_id": uid}

    # Include a one-way password fingerprint in the request fingerprint, never its plaintext.
    payload = body.model_dump(mode="json")
    payload["password"] = hashlib.sha256(body.password.get_secret_value().encode()).hexdigest()
    return mutation(db, user, request, payload, action)


@router.get("/users")
def list_users(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "users")
    return [
        dict(x)
        for x in db.execute(
            text("""SELECT u.user_id,u.login,u.active,u.created_at,
        coalesce(array_agg(r.role_code) FILTER (WHERE r.role_code IS NOT NULL),'{}') AS roles
        FROM core.users u LEFT JOIN core.user_roles r USING(user_id)
        GROUP BY u.user_id ORDER BY u.login,u.user_id LIMIT :l OFFSET :o"""),
            {"l": limit, "o": offset},
        ).mappings()
    ]


@router.patch("/users/{user_id}")
def update_user(
    user_id: UUID,
    body: schemas.UserUpdate,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "users")
    if user_id == user["user_id"]:
        raise HTTPException(409, "SELF_PERMISSION_CHANGE_FORBIDDEN")

    def action():
        if not db.execute(
            text("UPDATE core.users SET active=:a WHERE user_id=:u RETURNING user_id"),
            {"a": body.active, "u": user_id},
        ).scalar():
            raise HTTPException(404, "USER_NOT_FOUND")
        db.execute(text("DELETE FROM core.user_roles WHERE user_id=:u"), {"u": user_id})
        for role in set(body.roles):
            insert(db, "core.user_roles", {"user_id": user_id, "role_code": role})
        db.execute(text("DELETE FROM core.sessions WHERE user_id=:u"), {"u": user_id})
        event(db, user["user_id"], "PERMISSIONS_CHANGED", "users", user_id)
        return {"user_id": user_id, "active": body.active}

    return mutation(db, user, request, body.model_dump(mode="json"), action, 200)


@router.post("/emergencies")
def add_emergency(
    body: schemas.Emergency,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "create_emergency")

    def action():
        eid = uuid4()
        insert(
            db,
            "ops.emergencies",
            {"emergency_id": eid, **body.model_dump(), "created_by": user["user_id"]},
        )
        insert(db, "core.emergency_members", {"emergency_id": eid, "user_id": user["user_id"]})
        return {"emergency_id": eid, "input_revision": 1, "mode": "SIMULATED"}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.get("/emergencies")
def emergencies(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "read")
    return [
        dict(x)
        for x in db.execute(
            text("""SELECT e.* FROM ops.emergencies e
        JOIN core.emergency_members m USING(emergency_id) WHERE m.user_id=:u
        ORDER BY e.created_at,e.emergency_id LIMIT :l OFFSET :o"""),
            {"u": user["user_id"], "l": limit, "o": offset},
        ).mappings()
    ]


@router.get("/emergencies/{emergency_id}")
def emergency(emergency_id: UUID, db=Depends(database, scope="function"), user=Depends(principal)):
    return dict(scoped(db, user, emergency_id))


@router.patch("/emergencies/{emergency_id}")
def edit_emergency(
    emergency_id: UUID,
    body: schemas.EmergencyUpdate,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    scoped(db, user, emergency_id, "write")  # replay is allowed even if first request closed it

    def action():
        row = scoped(db, user, emergency_id, "write", mutable=True)
        if row["input_revision"] != body.expected_revision:
            raise HTTPException(409, "REVISION_CONFLICT")
        db.execute(
            text("""UPDATE ops.emergencies SET name=:n,description=:d,state=:s,
            input_revision=input_revision+1,updated_at=now() WHERE emergency_id=:e"""),
            {"n": body.name, "d": body.description, "s": body.state, "e": emergency_id},
        )
        event(
            db,
            user["user_id"],
            "EMERGENCY_CHANGE:" + body.reason,
            "emergencies",
            emergency_id,
            emergency_id,
        )
        return {"emergency_id": emergency_id, "input_revision": row["input_revision"] + 1}

    return mutation(db, user, request, body.model_dump(mode="json"), action, 200)


@router.post("/emergencies/{emergency_id}/members")
def add_member(
    emergency_id: UUID,
    body: schemas.Member,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "users")

    def action():
        insert(
            db, "core.emergency_members", {"emergency_id": emergency_id, "user_id": body.user_id}
        )
        event(db, user["user_id"], "MEMBER_ADDED", "members", body.user_id, emergency_id)
        return {"user_id": body.user_id, "emergency_id": emergency_id}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.post("/sources")
def source(
    body: schemas.Source,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "catalog")

    def action():
        sid = uuid4()
        insert(
            db,
            "ops.sources",
            {"source_id": sid, **body.model_dump(), "created_by": user["user_id"]},
        )
        return {"source_id": sid}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.post("/resource-types")
def resource(
    body: schemas.Resource,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "catalog")

    def action():
        rid = uuid4()
        insert(db, "ops.resource_types", {"resource_type_id": rid, **body.model_dump()})
        return {"resource_type_id": rid}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.post("/specialty-types")
def specialty(
    body: schemas.Specialty,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "catalog")

    def action():
        sid = uuid4()
        insert(db, "ops.specialty_types", {"specialty_type_id": sid, **body.model_dump()})
        return {"specialty_type_id": sid}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.post("/depots")
def depot(
    body: schemas.Depot,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "catalog")

    def action():
        did = uuid4()
        db.execute(
            text("""INSERT INTO ops.depots(depot_id,name,geom,source_id) VALUES
            (:id,:name,ST_SetSRID(ST_MakePoint(:longitude,:latitude),4326),:source_id)"""),
            {"id": did, **body.model_dump()},
        )
        return {"depot_id": did}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.post("/inventory/movements")
def stock(
    body: schemas.Stock,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "catalog")

    def action():
        eid = uuid4()
        insert(
            db,
            "ops.inventory_ledger",
            {"entry_id": eid, **body.model_dump(), "created_by": user["user_id"]},
        )
        return {"entry_id": eid}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.post("/assets")
def asset(
    body: schemas.Asset,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "catalog")

    def action():
        aid = uuid4()
        insert(
            db,
            "ops.physical_assets",
            {
                "asset_id": aid,
                **body.model_dump(include={"asset_tag", "type", "state", "base_id", "source_id"}),
            },
        )
        if body.max_kg is not None:
            insert(
                db,
                "ops.vehicles",
                {
                    "asset_id": aid,
                    "max_kg": body.max_kg,
                    "max_m3": body.max_m3,
                    "base_depot_id": body.base_id,
                },
            )
        if body.specialty_type_id:
            insert(
                db,
                "ops.specialized_units",
                {
                    "asset_id": aid,
                    "specialty_type_id": body.specialty_type_id,
                    "qualification_status": body.qualification_status,
                    "base_depot_id": body.base_id,
                },
            )
        return {"asset_id": aid}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.patch("/assets/{asset_id}")
def edit_asset(
    asset_id: UUID,
    body: schemas.AssetUpdate,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "catalog")

    def action():
        row = db.execute(
            text("""UPDATE ops.physical_assets SET state=:s
            WHERE asset_id=:a AND row_version=:v RETURNING row_version"""),
            {"a": asset_id, "v": body.expected_revision, "s": body.state},
        ).scalar()
        if row is None:
            raise HTTPException(409, "REVISION_CONFLICT")
        event(db, user["user_id"], "ASSET_CHANGE:" + body.reason, "assets", asset_id)
        return {"asset_id": asset_id, "row_version": row}

    return mutation(db, user, request, body.model_dump(mode="json"), action, 200)


@router.post("/emergencies/{emergency_id}/zones")
def zone(
    emergency_id: UUID,
    body: schemas.Zone,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    scoped(db, user, emergency_id, "write")

    def action():
        scoped(db, user, emergency_id, "write", mutable=True)
        zid = uuid4()
        db.execute(
            text("""INSERT INTO geo.zones(zone_id,emergency_id,external_id,name,geom,
            baseline_population,source_id,baseline_at,quality)
            VALUES(:id,:e,:external_id,:name,ST_GeomFromGeoJSON(:geometry),
            :baseline_population,:source_id,:baseline_at,:quality)"""),
            {
                "id": zid,
                "e": emergency_id,
                **body.model_dump(),
                "geometry": canonical(body.geometry),
            },
        )
        return {"zone_id": zid, "crs": "EPSG:4326"}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.post("/emergencies/{emergency_id}/reports")
def report(
    emergency_id: UUID,
    body: schemas.Report,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    scoped(db, user, emergency_id, "write")
    if any(o.evidence_status == "ESTIMATED_APPROVED" for o in body.observations):
        require(user, "approve_estimate")

    def action():
        scoped(db, user, emergency_id, "write", mutable=True)
        rid = uuid4()
        insert(
            db,
            "ops.reports",
            {
                "report_id": rid,
                "emergency_id": emergency_id,
                **body.model_dump(exclude={"observations"}),
                "status": "RECORDED",
                "created_by": user["user_id"],
            },
        )
        for obs in body.observations:
            insert(
                db,
                "ops.observations",
                {
                    "observation_id": uuid4(),
                    "report_id": rid,
                    **obs.model_dump(),
                    "approved_by": user["user_id"]
                    if obs.evidence_status == "ESTIMATED_APPROVED"
                    else None,
                },
                ("quality_flags",),
            )
        return {"report_id": rid}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.post("/emergencies/{emergency_id}/needs")
def need(
    emergency_id: UUID,
    body: schemas.Need,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    scoped(db, user, emergency_id, "write")
    if body.status == "ESTIMATED_APPROVED":
        require(user, "approve_estimate")

    def action():
        scoped(db, user, emergency_id, "write", mutable=True)
        nid = uuid4()
        insert(
            db,
            "ops.needs",
            {
                "need_id": nid,
                "emergency_id": emergency_id,
                **body.model_dump(),
                "created_by": user["user_id"],
                "approved_by": user["user_id"] if body.status == "ESTIMATED_APPROVED" else None,
            },
        )
        return {"need_id": nid}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


GLOBAL_READ = {
    "sources": "SELECT * FROM ops.sources",
    "resource-types": "SELECT * FROM ops.resource_types",
    "specialty-types": "SELECT * FROM ops.specialty_types",
    "depots": "SELECT depot_id,name,active,source_id,ST_AsGeoJSON(geom)::jsonb "
    "AS geometry FROM ops.depots",
    "assets": "SELECT a.*,v.max_kg,v.max_m3,s.specialty_type_id,s.qualification_status FROM "
    "ops.physical_assets a LEFT JOIN ops.vehicles v USING(asset_id) "
    "LEFT JOIN ops.specialized_units s USING(asset_id)",
    "inventory": "SELECT *,quantity-reserved AS available FROM ops.inventory_balances",
}
SCOPED_READ = {
    "zones": "SELECT zone_id,emergency_id,external_id,name,baseline_population,"
    "source_id,baseline_at,"
    "quality,ST_AsGeoJSON(geom)::jsonb AS geometry FROM geo.zones WHERE emergency_id=:e",
    "reports": "SELECT *,extract(epoch FROM (:cutoff-observed_at))/3600 AS data_age_hours "
    "FROM ops.reports WHERE emergency_id=:e AND observed_at<=:cutoff",
    "needs": "SELECT * FROM ops.needs WHERE emergency_id=:e AND reported_at<=:cutoff",
    "observations": "SELECT o.*,r.emergency_id,r.source_id,r.observed_at,r.recorded_at FROM "
    "ops.observations o JOIN ops.reports r USING(report_id) "
    "WHERE r.emergency_id=:e AND r.observed_at<=:cutoff",
    "road-nodes": "SELECT node_id,emergency_id,external_id,"
    "ST_AsGeoJSON(geom)::jsonb AS geometry FROM geo.road_nodes WHERE emergency_id=:e",
    "road-edges": "SELECT edge_id,emergency_id,external_id,from_node,to_node,length_m,travel_sec,"
    "status,allowed_vehicle_types,network_revision,ST_AsGeoJSON(geom)::jsonb AS geometry "
    "FROM geo.road_edges WHERE emergency_id=:e",
}


@router.get("/catalog/{collection}")
def catalog(
    collection: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    if not ({"read", "catalog"} & user["capabilities"]):
        raise HTTPException(403, "CAPABILITY_REQUIRED")
    if collection not in GLOBAL_READ:
        raise HTTPException(404, "COLLECTION_NOT_FOUND")
    return [
        dict(x)
        for x in db.execute(
            text(GLOBAL_READ[collection] + " ORDER BY 1 LIMIT :l OFFSET :o"),
            {"l": limit, "o": offset},
        ).mappings()
    ]


@router.get("/emergencies/{emergency_id}/data/{collection}")
def data(
    emergency_id: UUID,
    collection: str,
    as_of_time: schemas.AwareDatetime | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    scoped(db, user, emergency_id)
    if collection not in SCOPED_READ:
        raise HTTPException(404, "COLLECTION_NOT_FOUND")
    cutoff = as_of_time or datetime.now(UTC)
    if cutoff > datetime.now(UTC):
        raise HTTPException(422, "FUTURE_CUTOFF")
    return [
        dict(x)
        for x in db.execute(
            text(SCOPED_READ[collection] + " ORDER BY 1 LIMIT :l OFFSET :o"),
            {"e": emergency_id, "cutoff": cutoff, "l": limit, "o": offset},
        ).mappings()
    ]


@router.post("/emergencies/{emergency_id}/snapshots")
def snapshot(
    emergency_id: UUID,
    body: schemas.Snapshot,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    scoped(db, user, emergency_id, "snapshot")

    def action():
        # Lock emergency then stock revision; every stock writer takes the latter.
        e = scoped(db, user, emergency_id, "snapshot", mutable=True)
        revision = db.execute(text("SELECT core.lock_inventory_revision()")).scalar_one()
        payload = {"emergency": dict(e), "cutoff_at": body.cutoff_at, "mode": "SIMULATED"}
        for name, query in SCOPED_READ.items():
            payload[name] = [
                dict(x)
                for x in db.execute(
                    text(query + " ORDER BY 1"), {"e": emergency_id, "cutoff": body.cutoff_at}
                ).mappings()
            ]
        for name, query in GLOBAL_READ.items():
            payload[name] = [dict(x) for x in db.execute(text(query + " ORDER BY 1")).mappings()]
        sid = uuid4()
        serialized = canonical(payload)
        fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
        insert(
            db,
            "model.input_snapshots",
            {
                "snapshot_id": sid,
                "emergency_id": emergency_id,
                "cutoff_at": body.cutoff_at,
                "input_revision": e["input_revision"],
                "inventory_revision": revision,
                "fingerprint": fingerprint,
                "payload": payload,
                "created_by": user["user_id"],
            },
            ("payload",),
        )
        return {"snapshot_id": sid, "fingerprint": fingerprint}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.get("/snapshots/{snapshot_id}")
def get_snapshot(
    snapshot_id: UUID, db=Depends(database, scope="function"), user=Depends(principal)
):
    row = (
        db.execute(
            text("SELECT * FROM model.input_snapshots WHERE snapshot_id=:id"), {"id": snapshot_id}
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(404, "SNAPSHOT_NOT_FOUND")
    scoped(db, user, row["emergency_id"])
    return dict(row)


@router.post("/emergencies/{emergency_id}/jobs")
def job(
    emergency_id: UUID,
    body: schemas.Job,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    scoped(db, user, emergency_id, "jobs")

    def action():
        scoped(db, user, emergency_id, "jobs", mutable=True)
        if not db.execute(
            text("""SELECT 1 FROM model.input_snapshots
            WHERE snapshot_id=:s AND emergency_id=:e"""),
            {"s": body.snapshot_id, "e": emergency_id},
        ).scalar():
            raise HTTPException(422, "SNAPSHOT_EMERGENCY_MISMATCH")
        jid = uuid4()
        insert(
            db,
            "core.job_runs",
            {
                "job_id": jid,
                "emergency_id": emergency_id,
                **body.model_dump(),
                "created_by": user["user_id"],
            },
        )
        event(db, user["user_id"], "JOB_QUEUED", "jobs", jid, emergency_id)
        return {"job_id": jid, "state": "QUEUED"}

    return mutation(db, user, request, body.model_dump(mode="json"), action, 202)


@router.get("/jobs/{job_id}")
def get_job(job_id: UUID, db=Depends(database, scope="function"), user=Depends(principal)):
    row = (
        db.execute(
            text("""SELECT job_id,emergency_id,kind,state,attempts,result,error_code,
        created_at,ended_at FROM core.job_runs WHERE job_id=:j"""),
            {"j": job_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(404, "JOB_NOT_FOUND")
    scoped(db, user, row["emergency_id"])
    return dict(row)


@router.post("/emergencies/{emergency_id}/priority-runs")
@router.post("/emergencies/{emergency_id}/optimization-runs")
def unavailable_engine(
    emergency_id: UUID, db=Depends(database, scope="function"), user=Depends(principal)
):
    scoped(db, user, emergency_id, "jobs")
    raise HTTPException(501, "ENGINE_NOT_IMPLEMENTED_IN_PHASE9")


@router.get("/audit/events")
def audit(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    require(user, "audit")
    return [
        dict(x)
        for x in db.execute(
            text("""SELECT * FROM audit.events
        ORDER BY event_at,audit_id LIMIT :l OFFSET :o"""),
            {"l": limit, "o": offset},
        ).mappings()
    ]


@router.post("/emergencies/{emergency_id}/road-nodes")
def road_node(
    emergency_id: UUID,
    body: schemas.RoadNode,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    scoped(db, user, emergency_id, "write")

    def action():
        scoped(db, user, emergency_id, "write", mutable=True)
        nid = uuid4()
        db.execute(
            text(
                """INSERT INTO geo.road_nodes(node_id,emergency_id,external_id,geom)
                VALUES(:id,:e,:external_id,ST_SetSRID(ST_MakePoint(:longitude,:latitude),4326))"""
            ),
            {"id": nid, "e": emergency_id, **body.model_dump()},
        )
        return {"node_id": nid, "external_id": body.external_id}

    return mutation(db, user, request, body.model_dump(mode="json"), action)


@router.post("/emergencies/{emergency_id}/road-edges")
def road_edge(
    emergency_id: UUID,
    body: schemas.RoadEdge,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    scoped(db, user, emergency_id, "write")

    def action():
        scoped(db, user, emergency_id, "write", mutable=True)
        from_node = db.execute(
            text(
                """SELECT node_id FROM geo.road_nodes
                WHERE emergency_id=:e AND external_id=:id"""
            ),
            {"e": emergency_id, "id": body.from_node},
        ).scalar()
        to_node = db.execute(
            text(
                """SELECT node_id FROM geo.road_nodes
                WHERE emergency_id=:e AND external_id=:id"""
            ),
            {"e": emergency_id, "id": body.to_node},
        ).scalar()
        if from_node is None or to_node is None:
            raise HTTPException(422, "ROAD_NODE_NOT_FOUND")
        if from_node == to_node:
            raise HTTPException(422, "SELF_LOOP_EDGE")
        edge_id = uuid4()
        revision = db.execute(text("SELECT core.lock_network_revision()")).scalar_one()
        try:
            db.execute(
                text(
                    """INSERT INTO geo.road_edges(
                    edge_id,emergency_id,external_id,from_node,to_node,geom,length_m,travel_sec,
                    status,allowed_vehicle_types,network_revision)
                    VALUES(:id,:e,:external_id,:from_node,:to_node,
                    ST_MakeLine(ST_SetSRID(ST_MakePoint(:from_lon,:from_lat),4326),
                    ST_SetSRID(ST_MakePoint(:to_lon,:to_lat),4326)),
                    :length_m,:travel_sec,:status,:allowed,:revision)"""
                ),
                {
                    "id": edge_id,
                    "e": emergency_id,
                    "external_id": body.external_id,
                    "from_node": from_node,
                    "to_node": to_node,
                    "from_lon": body.from_longitude,
                    "from_lat": body.from_latitude,
                    "to_lon": body.to_longitude,
                    "to_lat": body.to_latitude,
                    "length_m": body.length_m,
                    "travel_sec": body.travel_sec,
                    "status": body.status,
                    "allowed": body.allowed_vehicle_types,
                    "revision": revision,
                },
            )
        except DBAPIError as error:
            sqlstate = getattr(error.orig, "sqlstate", "") or ""
            if sqlstate == "23505":
                raise HTTPException(409, "DUPLICATE_ROAD_EDGE") from None
            raise
        event(db, user["user_id"], "ROAD_EDGE_CREATED", "road_edges", edge_id, emergency_id)
        return {"edge_id": edge_id, "network_revision": revision}

    payload = body.model_dump(mode="json")
    return mutation(db, user, request, payload, action)


@router.patch("/emergencies/{emergency_id}/road-edges/{edge_id}")
def road_edge_update(
    emergency_id: UUID,
    edge_id: UUID,
    body: schemas.RoadEdgeUpdate,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    scoped(db, user, emergency_id, "write")

    def action():
        scoped(db, user, emergency_id, "write", mutable=True)
        current = db.execute(
            text(
                "SELECT network_revision FROM geo.road_edges WHERE edge_id=:id AND emergency_id=:e"
            ),
            {"id": edge_id, "e": emergency_id},
        ).scalar()
        if current is None:
            raise HTTPException(404, "ROAD_EDGE_NOT_FOUND")
        if current != body.expected_revision:
            raise HTTPException(409, "REVISION_CONFLICT")
        revision = db.execute(text("SELECT core.lock_network_revision()")).scalar_one()
        candidates = db.execute(
            text(
                """SELECT count(*) FROM geo.route_candidate_edges rce
                JOIN geo.route_candidates rc USING(route_id)
                WHERE rce.edge_id=:id AND rc.emergency_id=:e"""
            ),
            {"id": edge_id, "e": emergency_id},
        ).scalar_one()
        updated = db.execute(
            text(
                """UPDATE geo.road_edges SET status=:s,allowed_vehicle_types=:a,
                network_revision=:r,updated_at=now()
                WHERE edge_id=:id AND emergency_id=:e AND network_revision=:v
                RETURNING network_revision"""
            ),
            {
                "s": body.status,
                "a": body.allowed_vehicle_types,
                "r": revision,
                "id": edge_id,
                "e": emergency_id,
                "v": body.expected_revision,
            },
        ).scalar()
        if updated is None:
            raise HTTPException(409, "REVISION_CONFLICT")
        event(
            db,
            user["user_id"],
            "ROAD_EDGE_UPDATE:" + body.reason,
            "road_edges",
            edge_id,
            emergency_id,
        )
        return {
            "edge_id": edge_id,
            "network_revision": int(updated),
            "invalidated_routes": int(candidates),
        }

    return mutation(db, user, request, body.model_dump(mode="json"), action, 200)


@router.post("/emergencies/{emergency_id}/routes")
def route_plan(
    emergency_id: UUID,
    body: schemas.RoutePlanRequest,
    request: Request,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    from datetime import UTC, datetime, timedelta

    from app.gis.provider import plan_and_persist
    from app.gis.routes import RouteError

    scoped(db, user, emergency_id, "write")

    def action():
        scoped(db, user, emergency_id, "write", mutable=True)
        expires_at = datetime.now(UTC) + timedelta(hours=float(body.expires_in_hours))
        try:
            plan = plan_and_persist(
                db,
                emergency_id,
                body.external_id,
                body.depot_id,
                body.zone_id,
                body.vehicle_type,
                body.unload_sec,
                body.horizon_hours,
                require_return=body.require_return,
                expires_at=expires_at,
            )
        except RouteError as error:
            raise HTTPException(422, error.code) from None
        event(db, user["user_id"], "ROUTE_PLANNED", "route_candidates", plan.route_id, emergency_id)
        return {
            "route_id": plan.route_id,
            "route_status": plan.route_status,
            "network_revision": plan.network_revision,
            "length_m": plan.length_m,
            "travel_sec": plan.travel_sec,
            "return_length_m": plan.return_length_m,
            "return_travel_sec": plan.return_travel_sec,
            "total_time_hr": plan.total_time_hr,
            "edge_sequence": plan.edge_sequence,
            "expires_at": expires_at,
        }

    return mutation(db, user, request, body.model_dump(mode="json"), action, 201)


@router.get("/emergencies/{emergency_id}/routes/{route_id}")
def route_get(
    emergency_id: UUID,
    route_id: UUID,
    db=Depends(database, scope="function"),
    user=Depends(principal),
):
    from app.gis.provider import eligibility_for_planning

    scoped(db, user, emergency_id)
    row = (
        db.execute(
            text(
                """SELECT route_id,depot_id,zone_id,vehicle_type,route_status,network_revision,
            length_m,travel_sec,unload_sec,return_length_m,return_travel_sec,expires_at,
            (travel_sec+return_travel_sec+unload_sec)/3600.0 AS total_time_hr,
            ST_AsGeoJSON(path_geom)::jsonb AS path_geometry
            FROM geo.route_candidates WHERE route_id=:r AND emergency_id=:e"""
            ),
            {"r": route_id, "e": emergency_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        raise HTTPException(404, "ROUTE_NOT_FOUND")
    edges = [
        dict(x)
        for x in db.execute(
            text(
                """SELECT edge_id,sequence_no,direction FROM geo.route_candidate_edges
                WHERE route_id=:r ORDER BY sequence_no"""
            ),
            {"r": route_id},
        ).mappings()
    ]
    return {
        **dict(row),
        "edges": edges,
        "eligible_for_planning": eligibility_for_planning(db, emergency_id, route_id),
    }
