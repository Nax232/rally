"""H7 GIS: network revision, invalidation, eligibility and metric geometry."""

import os
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.main import create_app
from app.security import hasher
from app.settings import Settings
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def env():
    required = [
        "SIPRE_TEST_DATABASE_URL",
        "SIPRE_TEST_APP_URL",
        "SIPRE_TEST_WORKER_URL",
        "SIPRE_TEST_READER_URL",
    ]
    if not all(os.environ.get(k) for k in required):
        pytest.skip("Explicit isolated database role URLs required")
    engines = [create_engine(os.environ[k]) for k in required]
    yield dict(zip(("owner", "app", "worker", "reader"), engines, strict=True))
    for engine in engines:
        engine.dispose()


def login_client(login, password, app_url):
    client = TestClient(create_app(Settings(database_url=app_url)))
    client.__enter__()
    response = client.post("/api/v1/auth/login", json={"login": login, "password": password})
    assert response.status_code == 200, response.text
    client.headers["x-csrf-token"] = response.json()["csrf_token"]
    return client


@pytest.fixture
def setup(env):
    password = secrets.token_urlsafe(24)
    with env["owner"].begin() as db:
        uid, login = uuid4(), "gis-" + uuid4().hex
        db.execute(
            text("INSERT INTO core.users(user_id,login,password_hash) VALUES(:u,:l,:p)"),
            {"u": uid, "l": login, "p": hasher.hash(password)},
        )
        db.execute(text("INSERT INTO core.user_roles VALUES(:u,'OPERATOR')"), {"u": uid})
    operator = login_client(login, password, os.environ["SIPRE_TEST_APP_URL"])
    now = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    source = operator.post(
        "/api/v1/sources",
        json={"organization": "GIS", "kind": "SIMULATED", "description": "H7"},
        headers={"Idempotency-Key": "src-" + uuid4().hex},
    )
    assert source.status_code == 201, source.text
    source_id = source.json()["source_id"]
    emergency = operator.post(
        "/api/v1/emergencies",
        json={
            "name": "GIS " + uuid4().hex[:8],
            "hazard_type": "earthquake",
            "territory": "test",
            "description": "H7 network",
            "start_at": now,
        },
        headers={"Idempotency-Key": "em-" + uuid4().hex},
    )
    assert emergency.status_code == 201, emergency.text
    eid = emergency.json()["emergency_id"]
    depot = operator.post(
        "/api/v1/depots",
        json={"name": "Base", "longitude": -71.0, "latitude": -33.0, "source_id": source_id},
        headers={"Idempotency-Key": "depot-" + uuid4().hex},
    )
    assert depot.status_code == 201, depot.text
    zone = operator.post(
        f"/api/v1/emergencies/{eid}/zones",
        json={
            "external_id": "Z1",
            "name": "Zona",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-70.99, -33.01],
                            [-70.97, -33.01],
                            [-70.97, -32.99],
                            [-70.99, -32.99],
                            [-70.99, -33.01],
                        ]
                    ]
                ],
            },
            "baseline_population": 100,
            "source_id": source_id,
            "baseline_at": now,
            "quality": "SIMULATED",
        },
        headers={"Idempotency-Key": "zone-" + uuid4().hex},
    )
    assert zone.status_code == 201, zone.text
    yield {
        "operator": operator,
        "emergency": eid,
        "source": source_id,
        "depot": depot.json()["depot_id"],
        "zone": zone.json()["zone_id"],
    }
    operator.__exit__(None, None, None)


def post_node(setup, external_id, lon, lat):
    response = setup["operator"].post(
        f"/api/v1/emergencies/{setup['emergency']}/road-nodes",
        json={"external_id": external_id, "longitude": lon, "latitude": lat},
        headers={"Idempotency-Key": "node-" + uuid4().hex},
    )
    assert response.status_code == 201, response.text
    return response.json()["node_id"]


def post_edge(
    setup, external_id, from_node, to_node, from_ll, to_ll, length_m, travel_sec, status, allowed=()
):
    payload = {
        "external_id": external_id,
        "from_node": from_node,
        "to_node": to_node,
        "from_longitude": from_ll[0],
        "from_latitude": from_ll[1],
        "to_longitude": to_ll[0],
        "to_latitude": to_ll[1],
        "length_m": length_m,
        "travel_sec": travel_sec,
        "status": status,
        "allowed_vehicle_types": list(allowed),
    }
    response = setup["operator"].post(
        f"/api/v1/emergencies/{setup['emergency']}/road-edges",
        json=payload,
        headers={"Idempotency-Key": "edge-" + uuid4().hex},
    )
    assert response.status_code == 201, response.text
    return response.json()


def plan_route(setup, vehicle_type="TRUCK", unload_sec=300, require_return=True, horizon_hours=6):
    response = setup["operator"].post(
        f"/api/v1/emergencies/{setup['emergency']}/routes",
        json={
            "external_id": "R" + uuid4().hex[:8],
            "depot_id": setup["depot"],
            "zone_id": setup["zone"],
            "vehicle_type": vehicle_type,
            "unload_sec": unload_sec,
            "require_return": require_return,
            "horizon_hours": horizon_hours,
            "expires_in_hours": 2,
        },
        headers={"Idempotency-Key": "route-" + uuid4().hex},
    )
    return response


def test_network_revision_and_invalidation(setup, env):
    operator = setup["operator"]
    post_node(setup, "N1", -71.0, -33.0)
    post_node(setup, "N2", -70.98, -33.0)
    first = post_edge(
        setup, "E1", "N1", "N2", (-71.0, -33.0), (-70.98, -33.0), 1800, 120, "VERIFIED_OPEN"
    )
    assert first["network_revision"] >= 1
    second = post_edge(
        setup, "E2", "N2", "N1", (-70.98, -33.0), (-71.0, -33.0), 1800, 120, "VERIFIED_OPEN"
    )
    assert second["network_revision"] > first["network_revision"]
    planned = plan_route(setup)
    assert planned.status_code == 201, planned.text
    body = planned.json()
    assert body["route_status"] == "VERIFIED_OPEN"
    assert body["total_time_hr"] == pytest.approx((120 + 120 + 300) / 3600.0)
    assert [row[2] for row in body["edge_sequence"]] == ["forward", "backward"]
    route_id = body["route_id"]
    edge_id = body["edge_sequence"][0][0]
    with env["owner"].connect() as db:
        row_rev = db.execute(
            text(
                "SELECT network_revision FROM geo.road_edges WHERE edge_id=:id AND emergency_id=:e"
            ),
            {"id": edge_id, "e": setup["emergency"]},
        ).scalar_one()
    blocked = operator.patch(
        f"/api/v1/emergencies/{setup['emergency']}/road-edges/{edge_id}",
        json={
            "expected_revision": row_rev,
            "status": "BLOCKED",
            "allowed_vehicle_types": [],
            "reason": "cierre vial",
        },
        headers={"Idempotency-Key": "block-" + uuid4().hex},
    )
    assert blocked.status_code == 200, blocked.text
    assert blocked.json()["invalidated_routes"] >= 1
    assert blocked.json()["network_revision"] > row_rev
    fetched = operator.get(f"/api/v1/emergencies/{setup['emergency']}/routes/{route_id}")
    assert fetched.status_code == 404


def test_route_rejected_when_blocked(setup):
    post_node(setup, "A", -71.0, -33.0)
    post_node(setup, "B", -70.98, -33.0)
    post_edge(setup, "AB", "A", "B", (-71.0, -33.0), (-70.98, -33.0), 1800, 600, "BLOCKED")
    response = plan_route(setup, require_return=False)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ROUTE_NOT_FOUND"


def test_restricted_edge_excludes_other_vehicle_class(setup):
    post_node(setup, "A", -71.0, -33.0)
    post_node(setup, "B", -70.98, -33.0)
    post_node(setup, "C", -70.98, -32.99)
    post_edge(setup, "AB", "A", "B", (-71.0, -33.0), (-70.98, -33.0), 9000, 1500, "VERIFIED_OPEN")
    post_edge(
        setup,
        "AC",
        "A",
        "C",
        (-71.0, -33.0),
        (-70.98, -32.99),
        4000,
        600,
        "VERIFIED_RESTRICTED",
        allowed=("AMBULANCE",),
    )
    post_edge(setup, "CB", "C", "B", (-70.98, -32.99), (-70.98, -33.0), 1600, 300, "VERIFIED_OPEN")
    denied = plan_route(setup, vehicle_type="TRUCK", require_return=False)
    assert denied.status_code == 201, denied.text
    assert denied.json()["route_status"] == "VERIFIED_OPEN"
    allowed = plan_route(setup, vehicle_type="AMBULANCE", require_return=False)
    assert allowed.status_code == 201, allowed.text
    assert allowed.json()["route_status"] == "VERIFIED_RESTRICTED"


def test_metric_lengths_and_horizon_errors(setup, env):
    post_node(setup, "A", -71.0, -33.0)
    post_node(setup, "B", -70.98, -33.0)
    post_edge(setup, "AB", "A", "B", (-71.0, -33.0), (-70.98, -33.0), 2000, 100, "VERIFIED_OPEN")
    post_edge(setup, "BA", "B", "A", (-70.98, -33.0), (-71.0, -33.0), 2000, 100, "VERIFIED_OPEN")
    with env["owner"].connect() as db:
        length_m = db.execute(
            text(
                """SELECT ST_Length(geom::geography) FROM geo.road_edges
                WHERE emergency_id=:e LIMIT 1"""
            ),
            {"e": setup["emergency"]},
        ).scalar()
    assert length_m > 1000
    too_short = plan_route(setup, unload_sec=60, require_return=True, horizon_hours=0.05)
    assert too_short.status_code == 422
    assert too_short.json()["error"]["code"] == "HORIZON_EXCEEDED"


def test_duplicate_edge_and_revision_conflict(setup):
    post_node(setup, "A", -71.0, -33.0)
    post_node(setup, "B", -70.98, -33.0)
    first = post_edge(
        setup, "AB", "A", "B", (-71.0, -33.0), (-70.98, -33.0), 1800, 120, "VERIFIED_OPEN"
    )
    duplicate = setup["operator"].post(
        f"/api/v1/emergencies/{setup['emergency']}/road-edges",
        json={
            "external_id": "AB2",
            "from_node": "A",
            "to_node": "B",
            "from_longitude": -71.0,
            "from_latitude": -33.0,
            "to_longitude": -70.98,
            "to_latitude": -33.0,
            "length_m": 1800,
            "travel_sec": 120,
            "status": "VERIFIED_OPEN",
            "allowed_vehicle_types": [],
        },
        headers={"Idempotency-Key": "dup-" + uuid4().hex},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_ROAD_EDGE"
    conflict = setup["operator"].patch(
        f"/api/v1/emergencies/{setup['emergency']}/road-edges/{first['edge_id']}",
        json={
            "expected_revision": 9999,
            "status": "BLOCKED",
            "allowed_vehicle_types": [],
            "reason": "conflicto",
        },
        headers={"Idempotency-Key": "conf-" + uuid4().hex},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "REVISION_CONFLICT"
