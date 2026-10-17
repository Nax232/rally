"""Real PostgreSQL/PostGIS tests using explicit isolated database URLs."""

import os
import secrets
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from app.api import canonical
from app.main import create_app
from app.security import hasher
from app.settings import Settings
from app.worker import run_once
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

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


@pytest.fixture
def setup(env):
    password = secrets.token_urlsafe(24)
    users = {}
    with env["owner"].begin() as db:
        for role in ("ADMIN", "OPERATOR", "ANALYST", "VIEWER", "DECISION_MAKER"):
            uid, login = uuid4(), "test-" + uuid4().hex
            db.execute(
                text("INSERT INTO core.users(user_id,login,password_hash) VALUES(:u,:l,:p)"),
                {"u": uid, "l": login, "p": hasher.hash(password)},
            )
            db.execute(text("INSERT INTO core.user_roles VALUES(:u,:r)"), {"u": uid, "r": role})
            users[role] = (uid, login)
    clients = {}
    for role, (_uid, login) in users.items():
        client = TestClient(create_app(Settings(database_url=os.environ["SIPRE_TEST_APP_URL"])))
        client.__enter__()
        response = client.post("/api/v1/auth/login", json={"login": login, "password": password})
        assert response.status_code == 200, response.text
        client.headers["x-csrf-token"] = response.json()["csrf_token"]
        clients[role] = client
    now = (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
    operator = clients["OPERATOR"]

    def post(client, path, payload, expected=201, key=None):
        r = client.post(
            "/api/v1" + path, json=payload, headers={"Idempotency-Key": key or uuid4().hex}
        )
        assert r.status_code == expected, r.text
        return r.json()

    eid = post(
        operator,
        "/emergencies",
        {
            "name": "Test",
            "hazard_type": "SIMULATED",
            "territory": "Demo",
            "description": "Not operational",
            "start_at": now,
        },
    )["emergency_id"]
    for role in ("ANALYST", "VIEWER", "DECISION_MAKER"):
        post(clients["ADMIN"], f"/emergencies/{eid}/members", {"user_id": str(users[role][0])})
    sid = post(
        operator,
        "/sources",
        {"organization": "Demo", "kind": "SYNTHETIC", "description": "Test fixture"},
    )["source_id"]
    rid = post(
        operator,
        "/resource-types",
        {
            "code": uuid4().hex,
            "unit": "unit",
            "discrete": True,
            "kg_per_unit": "1",
            "m3_per_unit": "0.01",
        },
    )["resource_type_id"]
    zid = post(
        operator,
        f"/emergencies/{eid}/zones",
        {
            "external_id": uuid4().hex,
            "name": "Zona",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [[[-71, -33], [-70.99, -33], [-70.99, -32.99], [-71, -32.99], [-71, -33]]]
                ],
            },
            "baseline_population": 10,
            "source_id": sid,
            "baseline_at": now,
            "quality": "DEMO",
        },
    )["zone_id"]
    did = post(
        operator, "/depots", {"name": "Demo", "longitude": -71, "latitude": -33, "source_id": sid}
    )["depot_id"]
    yield {
        "clients": clients,
        "users": users,
        "post": post,
        "emergency": eid,
        "zone": zid,
        "source": sid,
        "resource": rid,
        "depot": did,
        "now": now,
        "password": password,
    }
    for client in clients.values():
        client.__exit__(None, None, None)


def need_body(s, quantity=None, status="UNKNOWN"):
    return {
        "zone_id": s["zone"],
        "resource_type_id": s["resource"],
        "quantity": quantity,
        "unit": "unit",
        "status": status,
        "urgency": "DEMO",
        "source_id": s["source"],
        "reported_at": s["now"],
    }


def test_unknown_zero_and_cross_emergency(setup):
    s = setup
    op = s["clients"]["OPERATOR"]
    path = f"/emergencies/{s['emergency']}/needs"
    s["post"](op, path, need_body(s))
    s["post"](op, path, need_body(s, "0", "CONFIRMED"))
    s["post"](op, path, need_body(s, "0"), 422)
    s["post"](op, path, need_body(s, "0.5", "CONFIRMED"), 422)
    s["post"](op, path, {**need_body(s), "unit": "kg"}, 422)
    s["post"](op, path, {**need_body(s), "zone_id": str(uuid4())}, 422)
    rows = op.get(f"/api/v1/emergencies/{s['emergency']}/data/needs").json()
    assert len(rows) == 2
    assert {r["status"] for r in rows} == {"UNKNOWN", "CONFIRMED"}


def test_permissions_csrf_scope_and_logout(setup):
    s = setup
    viewer = s["clients"]["VIEWER"]
    s["post"](viewer, f"/emergencies/{s['emergency']}/needs", need_body(s), 403)
    assert viewer.get(f"/api/v1/emergencies/{uuid4()}").status_code == 403
    admin = s["clients"]["ADMIN"]
    s["post"](
        admin,
        "/emergencies",
        {
            "name": "Forbidden",
            "hazard_type": "DEMO",
            "territory": "Demo",
            "description": "Test",
            "start_at": s["now"],
        },
        403,
    )
    op = s["clients"]["OPERATOR"]
    csrf = op.headers.pop("x-csrf-token")
    s["post"](op, f"/emergencies/{s['emergency']}/needs", need_body(s), 403)
    op.headers["x-csrf-token"] = csrf
    assert op.post("/api/v1/auth/logout").status_code == 204
    assert op.get("/api/v1/auth/me").status_code == 401


def test_idempotency_stock_and_asset_identity(setup, env):
    s = setup
    op = s["clients"]["OPERATOR"]
    body = {
        "depot_id": s["depot"],
        "resource_type_id": s["resource"],
        "change_quantity": "10",
        "source_id": s["source"],
        "reason": "DEMO initial",
    }
    key = uuid4().hex
    first = s["post"](op, "/inventory/movements", body, key=key)
    assert s["post"](op, "/inventory/movements", body, key=key) == first
    s["post"](op, "/inventory/movements", {**body, "change_quantity": "20"}, 409, key)
    s["post"](op, "/inventory/movements", {**body, "change_quantity": "-11"}, 422)
    with env["owner"].connect() as db:
        assert (
            db.execute(
                text("""SELECT quantity FROM ops.inventory_balances
            WHERE depot_id=:d AND resource_type_id=:r"""),
                {"d": s["depot"], "r": s["resource"]},
            ).scalar()
            == 10
        )
    asset = {
        "asset_tag": uuid4().hex,
        "type": "TRUCK",
        "state": "AVAILABLE",
        "base_id": s["depot"],
        "source_id": s["source"],
        "max_kg": "100",
        "max_m3": "2",
    }
    aid = s["post"](op, "/assets", asset)["asset_id"]
    s["post"](op, "/assets", asset, 409)
    s["post"](op, "/assets", {**asset, "asset_tag": uuid4().hex, "max_kg": "0"}, 422)
    r = op.patch(
        f"/api/v1/assets/{aid}",
        json={"expected_revision": 1, "state": "MAINTENANCE", "reason": "Inspection"},
        headers={"Idempotency-Key": uuid4().hex},
    )
    assert r.status_code == 200, r.text


def test_reports_history_estimates_and_dates(setup, env):
    s = setup
    op = s["clients"]["OPERATOR"]
    body = {
        "zone_id": s["zone"],
        "source_id": s["source"],
        "observed_at": s["now"],
        "comments": "Demo",
        "observations": [
            {
                "metric_code": "demo",
                "value_numeric": None,
                "unit": "unit",
                "evidence_status": "UNKNOWN",
            }
        ],
    }
    path = f"/emergencies/{s['emergency']}/reports"
    first = s["post"](op, path, body)["report_id"]
    s["post"](op, path, {**body, "supersedes_id": first})
    s["post"](op, path, {**body, "observed_at": "2020-01-01T00:00:00"}, 422)
    s["post"](
        op,
        path,
        {**body, "observed_at": (datetime.now(UTC) + timedelta(days=1)).isoformat()},
        422,
    )
    estimated = {
        **body,
        "observations": [
            {
                "metric_code": "demo",
                "value_numeric": "5",
                "unit": "unit",
                "evidence_status": "ESTIMATED_APPROVED",
            }
        ],
    }
    s["post"](op, path, estimated, 403)
    with env["owner"].begin() as db:
        db.execute(
            text("INSERT INTO core.user_roles VALUES(:u,'DECISION_MAKER')"),
            {"u": s["users"]["OPERATOR"][0]},
        )
    s["post"](op, path, estimated)
    rows = op.get(f"/api/v1/emergencies/{s['emergency']}/data/reports").json()
    assert len(rows) == 3 and all(r["data_age_hours"] >= 0 for r in rows)
    with env["owner"].begin() as db:
        with pytest.raises(DBAPIError), db.begin_nested():
            db.execute(
                text("UPDATE ops.reports SET comments='overwrite' WHERE report_id=:r"), {"r": first}
            )


def test_snapshot_job_and_closed_history(setup, env):
    s = setup
    analyst = s["clients"]["ANALYST"]
    e = s["emergency"]
    cutoff = datetime.now(UTC).isoformat()
    snap = s["post"](analyst, f"/emergencies/{e}/snapshots", {"cutoff_at": cutoff})
    job = s["post"](analyst, f"/emergencies/{e}/jobs", {"snapshot_id": snap["snapshot_id"]}, 202)
    assert run_once(env["worker"])
    result = analyst.get("/api/v1/jobs/" + job["job_id"]).json()
    assert result["state"] == "SUCCESS", result
    before = analyst.get("/api/v1/snapshots/" + snap["snapshot_id"]).json()
    assert before["payload"]["mode"] == "SIMULATED"
    assert before["payload"]["network_revision"] == before["network_revision"]
    assert before["fingerprint"] == snap["fingerprint"]
    s["post"](analyst, f"/emergencies/{e}/optimization-runs", {}, 501)
    op = s["clients"]["OPERATOR"]
    revision = op.get(f"/api/v1/emergencies/{e}").json()["input_revision"]
    payload = {
        "expected_revision": revision,
        "state": "CLOSED",
        "name": "Test",
        "description": "Preserved",
        "reason": "Test done",
    }
    key = uuid4().hex
    r = op.patch(f"/api/v1/emergencies/{e}", json=payload, headers={"Idempotency-Key": key})
    assert r.status_code == 200, r.text
    assert (
        op.patch(
            f"/api/v1/emergencies/{e}", json=payload, headers={"Idempotency-Key": key}
        ).status_code
        == 200
    )
    s["post"](op, f"/emergencies/{e}/needs", need_body(s), 409)
    assert analyst.get("/api/v1/snapshots/" + snap["snapshot_id"]).json() == before


def test_sql_permissions_real_reader_and_immutable(setup, env):
    s = setup
    with env["reader"].begin() as db:
        assert db.execute(text("SELECT count(*) FROM analytics.v_foundation_status")).scalar() >= 1
        for command in (
            "SELECT * FROM ops.emergencies",
            "INSERT INTO analytics.v_foundation_status VALUES('SIMULATED','DRAFT',1)",
            "UPDATE analytics.v_foundation_status SET emergency_count=0",
            "DELETE FROM analytics.v_foundation_status",
            "CREATE TABLE analytics.illegal(id int)",
        ):
            with pytest.raises(DBAPIError), db.begin_nested():
                db.execute(text(command))
    with env["app"].begin() as db:
        for command in (
            "DELETE FROM audit.events",
            "UPDATE audit.events SET action='bad'",
            "UPDATE ops.inventory_balances SET quantity=999",
            "DELETE FROM ops.needs",
        ):
            with pytest.raises(DBAPIError), db.begin_nested():
                db.execute(text(command))
    with env["owner"].begin() as db:
        with pytest.raises(DBAPIError), db.begin_nested():
            db.execute(
                text("UPDATE geo.zones SET baseline_population=0 WHERE zone_id=:z"),
                {"z": s["zone"]},
            )


def test_sql_negative_nan_and_wrong_crs(setup, env):
    s = setup
    with env["app"].begin() as db:
        db.execute(
            text("SELECT set_config('sipre.actor_id',:u,true)"),
            {"u": str(s["users"]["OPERATOR"][0])},
        )
        for value in ("NaN", "Infinity", "-1"):
            with pytest.raises(DBAPIError), db.begin_nested():
                db.execute(
                    text("""INSERT INTO ops.resource_types
                    VALUES(:id,:code,'unit',true,CAST(:v AS numeric),1)"""),
                    {"id": uuid4(), "code": uuid4().hex, "v": value},
                )
        with pytest.raises(DBAPIError), db.begin_nested():
            db.execute(
                text("""INSERT INTO ops.depots(depot_id,name,geom,source_id)
                VALUES(:id,'bad',ST_SetSRID(ST_Point(1,1),3857),:s)"""),
                {"id": uuid4(), "s": s["source"]},
            )


def test_worker_reclaims_expired_job_once(setup, env):
    s = setup
    a = s["clients"]["ANALYST"]
    snap = s["post"](
        a,
        f"/emergencies/{s['emergency']}/snapshots",
        {"cutoff_at": datetime.now(UTC).isoformat()},
    )
    job = s["post"](
        a, f"/emergencies/{s['emergency']}/jobs", {"snapshot_id": snap["snapshot_id"]}, 202
    )
    with env["owner"].begin() as db:
        db.execute(
            text("""UPDATE core.job_runs SET state='RUNNING',owner_token=:t,attempts=1,
            lease_until=now()-interval '1 second' WHERE job_id=:j"""),
            {"t": uuid4(), "j": job["job_id"]},
        )
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: run_once(env["worker"]), range(2)))
    row = a.get("/api/v1/jobs/" + job["job_id"]).json()
    assert row["state"] == "SUCCESS" and row["attempts"] == 2
    with env["owner"].connect() as db:
        count = db.execute(
            text("""SELECT count(*) FROM audit.events
            WHERE action='JOB_SUCCESS' AND object_id=:j"""),
            {"j": job["job_id"]},
        ).scalar()
        assert count == 1


def test_user_revocation_and_passwords_not_leaked(setup):
    s = setup
    admin = s["clients"]["ADMIN"]
    uid = str(s["users"]["VIEWER"][0])
    r = admin.patch(
        "/api/v1/users/" + uid,
        json={"active": False, "roles": ["VIEWER"]},
        headers={"Idempotency-Key": uuid4().hex},
    )
    assert r.status_code == 200, r.text
    assert s["clients"]["VIEWER"].get("/api/v1/auth/me").status_code == 401
    r = admin.post("/api/v1/auth/login", json={"login": "bad", "password": "tiny-X9"})
    assert r.status_code == 422 and "tiny-X9" not in r.text
    events = admin.get("/api/v1/audit/events").text
    assert s["password"] not in events and "$argon2" not in events


def test_concurrent_stock_cannot_overdraw(setup, env):
    s = setup
    op = s["clients"]["OPERATOR"]
    s["post"](
        op,
        "/inventory/movements",
        {
            "depot_id": s["depot"],
            "resource_type_id": s["resource"],
            "change_quantity": "10",
            "source_id": s["source"],
            "reason": "Concurrency test",
        },
    )

    def debit(_):
        try:
            with env["app"].begin() as db:
                db.execute(
                    text("SELECT set_config('sipre.actor_id',:u,true)"),
                    {"u": str(s["users"]["OPERATOR"][0])},
                )
                db.execute(
                    text("""INSERT INTO ops.inventory_ledger
                    (entry_id,depot_id,resource_type_id,change_quantity,reason,source_id,created_by)
                    VALUES(:id,:d,:r,-7,'concurrent debit',:s,:u)"""),
                    {
                        "id": uuid4(),
                        "d": s["depot"],
                        "r": s["resource"],
                        "s": s["source"],
                        "u": s["users"]["OPERATOR"][0],
                    },
                )
            return "committed"
        except DBAPIError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(debit, range(2))) == ["committed", "rejected"]
    with env["owner"].connect() as db:
        assert (
            db.execute(
                text("""SELECT quantity FROM ops.inventory_balances
            WHERE depot_id=:d AND resource_type_id=:r"""),
                {"d": s["depot"], "r": s["resource"]},
            ).scalar()
            == 3
        )


def test_cross_emergency_fk_and_login_limit(setup):
    s = setup
    op = s["clients"]["OPERATOR"]
    other = s["post"](
        op,
        "/emergencies",
        {
            "name": "Other",
            "hazard_type": "DEMO",
            "territory": "Demo",
            "description": "Test",
            "start_at": s["now"],
        },
    )["emergency_id"]
    s["post"](op, f"/emergencies/{other}/needs", need_body(s), 422)
    login = "unknown-" + uuid4().hex
    for _ in range(10):
        assert (
            op.post(
                "/api/v1/auth/login", json={"login": login, "password": "wrong-password-long"}
            ).status_code
            == 401
        )
    assert (
        op.post(
            "/api/v1/auth/login", json={"login": login, "password": "wrong-password-long"}
        ).status_code
        == 429
    )


def test_error_envelope_and_users_listing(setup):
    s = setup
    anonymous = TestClient(create_app(Settings(database_url=os.environ["SIPRE_TEST_APP_URL"])))
    with anonymous:
        r = anonymous.get("/api/v1/auth/me")
    assert r.status_code == 401
    assert r.json() == {
        "error": {
            "code": "AUTHENTICATION_REQUIRED",
            "correlation_id": r.json()["error"]["correlation_id"],
        }
    }
    assert UUID(r.json()["error"]["correlation_id"]).version == 4
    viewer = s["clients"]["VIEWER"]
    r = viewer.get("/api/v1/users")
    assert r.status_code == 403 and r.json()["error"]["code"] == "CAPABILITY_REQUIRED"
    admin = s["clients"]["ADMIN"]
    logins, page = set(), 0
    while True:
        rows = admin.get(f"/api/v1/users?limit=200&offset={page * 200}").json()
        if not rows:
            break
        logins.update(row["login"] for row in rows)
        assert all("password_hash" not in row for row in rows)
        assert all(row["roles"] for row in rows)
        page += 1
    assert logins >= {login for _uid, login in s["users"].values()}
    assert admin.get("/api/v1/users?limit=0").status_code == 422
    assert admin.get("/api/v1/users?offset=-1").status_code == 422


def test_login_response_has_no_password_material(setup):
    s = setup
    body = (
        s["clients"]["OPERATOR"]
        .post(
            "/api/v1/auth/login",
            json={"login": s["users"]["OPERATOR"][1], "password": s["password"]},
        )
        .json()
    )
    assert set(body) == {"user_id", "csrf_token"}


def test_stale_revision_conflict_and_snapshot_scope(setup, env):
    s = setup
    op = s["clients"]["OPERATOR"]
    analyst = s["clients"]["ANALYST"]
    e = s["emergency"]
    revision = op.get(f"/api/v1/emergencies/{e}").json()["input_revision"]
    payload = {
        "expected_revision": revision,
        "state": "ACTIVE",
        "name": "Test",
        "description": "Conflict",
        "reason": "Optimistic lock",
    }
    key = uuid4().hex
    assert (
        op.patch(
            f"/api/v1/emergencies/{e}", json=payload, headers={"Idempotency-Key": key}
        ).status_code
        == 200
    )
    stale = op.patch(
        f"/api/v1/emergencies/{e}", json=payload, headers={"Idempotency-Key": uuid4().hex}
    )
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "REVISION_CONFLICT"
    snap = s["post"](
        analyst, f"/emergencies/{e}/snapshots", {"cutoff_at": datetime.now(UTC).isoformat()}
    )
    other = s["post"](
        op,
        "/emergencies",
        {
            "name": "Other",
            "hazard_type": "DEMO",
            "territory": "Demo",
            "description": "Isolation",
            "start_at": s["now"],
        },
    )["emergency_id"]
    s["post"](
        s["clients"]["ADMIN"],
        f"/emergencies/{other}/members",
        {"user_id": str(s["users"]["ANALYST"][0])},
    )
    mismatch = s["post"](
        analyst,
        f"/emergencies/{other}/jobs",
        {"snapshot_id": snap["snapshot_id"]},
        422,
    )
    assert mismatch["error"]["code"] == "SNAPSHOT_EMERGENCY_MISMATCH"
    with env["owner"].begin() as db:
        with pytest.raises(DBAPIError), db.begin_nested():
            db.execute(
                text("UPDATE model.input_snapshots SET payload='{}' WHERE snapshot_id=:s"),
                {"s": snap["snapshot_id"]},
            )


def test_worker_failure_paths_hash_mismatch_and_max_attempts(setup, env):
    s = setup
    while run_once(env["worker"]):
        pass  # Drain any job left queued by earlier tests.
    analyst = s["clients"]["ANALYST"]
    e = s["emergency"]
    snapshot_id, cutoff = uuid4(), datetime.now(UTC).isoformat()
    with env["owner"].begin() as db:
        db.execute(
            text("SELECT set_config('sipre.actor_id',:u,true)"),
            {"u": str(s["users"]["ANALYST"][0])},
        )
        db.execute(
            text("""INSERT INTO model.input_snapshots(snapshot_id,emergency_id,cutoff_at,
            input_revision,inventory_revision,fingerprint,payload,created_by)
            VALUES(:s,:e,:c,1,0,:f,CAST(:p AS jsonb),:u)"""),
            {
                "s": snapshot_id,
                "e": e,
                "c": cutoff,
                "f": "0" * 64,
                "p": canonical({"tampered": True}),
                "u": s["users"]["ANALYST"][0],
            },
        )
    mismatch = s["post"](analyst, f"/emergencies/{e}/jobs", {"snapshot_id": str(snapshot_id)}, 202)
    assert run_once(env["worker"])
    row = analyst.get("/api/v1/jobs/" + mismatch["job_id"]).json()
    assert row["state"] == "FAILED" and row["error_code"] == "SNAPSHOT_HASH_MISMATCH", row

    healthy = s["post"](
        analyst, f"/emergencies/{e}/snapshots", {"cutoff_at": datetime.now(UTC).isoformat()}
    )
    exhausted = s["post"](
        analyst, f"/emergencies/{e}/jobs", {"snapshot_id": healthy["snapshot_id"]}, 202
    )
    with env["owner"].begin() as db:
        db.execute(
            text("UPDATE core.job_runs SET attempts=3 WHERE job_id=:j"),
            {"j": exhausted["job_id"]},
        )
    assert run_once(env["worker"])
    row = analyst.get("/api/v1/jobs/" + exhausted["job_id"]).json()
    assert row["state"] == "FAILED" and row["error_code"] == "MAX_ATTEMPTS", row
    assert analyst.get("/api/v1/jobs/" + uuid4().hex).status_code == 404


def test_expired_sessions_are_pruned_at_next_login(setup, env):
    s = setup
    op_login = s["users"]["OPERATOR"][1]
    with env["owner"].begin() as db:
        db.execute(
            text("""INSERT INTO core.sessions(token_hash,user_id,csrf_hash,expires_at)
            VALUES(:t,:u,:c,now()-interval '1 hour')"""),
            {"t": uuid4().hex, "u": s["users"]["OPERATOR"][0], "c": uuid4().hex},
        )
        count_expired = text("SELECT count(*) FROM core.sessions WHERE expires_at<now()")
        assert db.execute(count_expired).scalar() == 1
    assert (
        s["clients"]["OPERATOR"]
        .post("/api/v1/auth/login", json={"login": op_login, "password": s["password"]})
        .status_code
        == 200
    )
    with env["owner"].connect() as db:
        assert db.execute(count_expired).scalar() == 0


def test_priority_job_persists_exploratory_results_without_decisions(setup, env, monkeypatch):
    s = setup
    eid = s["emergency"]
    analyst = s["clients"]["ANALYST"]
    viewer = s["clients"]["VIEWER"]
    snapshot = s["post"](
        analyst, f"/emergencies/{eid}/snapshots", {"cutoff_at": datetime.now(UTC).isoformat()}
    )
    path = f"/emergencies/{eid}/priority-runs"
    assert s["post"](viewer, path, {"snapshot_id": snapshot["snapshot_id"]}, 403)
    other = s["post"](
        s["clients"]["OPERATOR"],
        "/emergencies",
        {
            "name": "Other priority incident",
            "hazard_type": "SIMULATED",
            "territory": "Demo",
            "description": "Scope check",
            "start_at": (datetime.now(UTC) - timedelta(seconds=1)).isoformat(),
        },
    )["emergency_id"]
    s["post"](
        s["clients"]["ADMIN"],
        f"/emergencies/{other}/members",
        {"user_id": str(s["users"]["ANALYST"][0])},
    )
    s["post"](
        analyst,
        f"/emergencies/{other}/priority-runs",
        {"snapshot_id": snapshot["snapshot_id"]},
        422,
    )
    key = uuid4().hex
    queued = s["post"](analyst, path, {"snapshot_id": snapshot["snapshot_id"]}, 202, key)
    assert s["post"](analyst, path, {"snapshot_id": snapshot["snapshot_id"]}, 202, key) == queued
    assert queued["profile_validation"] == "SYNTHETIC_REVIEW_PENDING"
    from app.prioritization.core import ModelError

    def missing_profile():
        raise ModelError("PROFILE_MISSING")

    monkeypatch.setattr("app.api.demo_priority_profile", missing_profile)
    s["post"](analyst, path, {"snapshot_id": snapshot["snapshot_id"]}, 409)
    monkeypatch.undo()
    assert run_once(env["worker"])
    job = analyst.get("/api/v1/jobs/" + queued["job_id"]).json()
    assert job["state"] == "SUCCESS", job
    response = viewer.get("/api/v1/priority-runs/" + queued["run_id"] + "/results")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["state"] == "SUCCESS" and len(payload["results"]) == 1
    result = payload["results"][0]
    assert result["zone_id"] == s["zone"]
    assert result["needs_verification"]
    assert result["insufficient_evidence"]
    assert result["details"]["exploratory"]
    assert result["details"]["missing_criteria_count"] >= 3
    assert result["score_lower"] <= result["priority_score"] <= result["score_upper"]
    assert len(result["details"]["factors"]) == 8
    with env["owner"].begin() as db:
        assert (
            db.execute(
                text("SELECT count(*) FROM model.priority_factors WHERE run_id=:r"),
                {"r": queued["run_id"]},
            ).scalar()
            == 8
        )
        assert (
            db.execute(
                text(
                    "SELECT count(*) FROM audit.events "
                    "WHERE action='PRIORITY_QUEUED' AND emergency_id=:e"
                ),
                {"e": eid},
            ).scalar()
            == 1
        )
        with pytest.raises(DBAPIError), db.begin_nested():
            db.execute(
                text("UPDATE model.priority_results SET priority_score=0 WHERE run_id=:r"),
                {"r": queued["run_id"]},
            )
        assert db.execute(text("SELECT to_regclass('planning.decisions')")).scalar() is None
        assert not db.execute(
            text(
                "SELECT has_table_privilege('sipre_metabase_reader',"
                "'model.priority_results','SELECT')"
            )
        ).scalar()
    with env["reader"].connect() as db:
        assert db.execute(text("SELECT count(*) FROM analytics.v_priority_results")).scalar() >= 1


def test_priority_job_derives_observed_criteria_from_frozen_reports(setup, env):
    s = setup
    eid, zid = s["emergency"], s["zone"]
    operator, analyst = s["clients"]["OPERATOR"], s["clients"]["ANALYST"]
    metrics = {
        "severely_injured": (1, "persons"),
        "trapped": (0, "persons"),
        "affected_people": (10, "persons"),
        "vulnerable_affected_unique": (2, "persons"),
        "health_damage": (0.2, "fraction"),
        "response_damage": (0.4, "fraction"),
        "coordination_damage": (0.1, "fraction"),
        "no_route_confirmed": (0, "boolean_0_1"),
        "actual_travel_sec": (1800, "seconds"),
        "baseline_travel_sec": (900, "seconds"),
        "no_active_essential_need_confirmed": (1, "boolean_0_1"),
        "water_interruption": (0.6, "fraction"),
        "electricity_interruption": (0.4, "fraction"),
        "sanitation_interruption": (0.2, "fraction"),
        "telecom_interruption": (0.1, "fraction"),
    }
    s["post"](
        operator,
        f"/emergencies/{eid}/reports",
        {
            "zone_id": zid,
            "source_id": s["source"],
            "observed_at": (datetime.now(UTC) - timedelta(seconds=2)).isoformat(),
            "comments": "F4 synthetic observations",
            "observations": [
                {
                    "metric_code": code,
                    "value_numeric": value,
                    "unit": unit,
                    "evidence_status": "OBSERVED",
                }
                for code, (value, unit) in metrics.items()
            ],
        },
    )
    snapshot = s["post"](
        analyst, f"/emergencies/{eid}/snapshots", {"cutoff_at": datetime.now(UTC).isoformat()}
    )
    queued = s["post"](
        analyst, f"/emergencies/{eid}/priority-runs", {"snapshot_id": snapshot["snapshot_id"]}, 202
    )
    assert run_once(env["worker"])
    result = analyst.get("/api/v1/priority-runs/" + queued["run_id"] + "/results").json()
    assert result["state"] == "SUCCESS", result
    row = result["results"][0]
    criteria = row["details"]["criteria"]
    assert criteria["C1"]["value"] == pytest.approx(0.65)
    assert criteria["C3"]["value"] == pytest.approx(0.2)
    assert criteria["C5"]["value"] == pytest.approx(0.5)
    assert criteria["C7"]["value"] == 0
    assert row["details"]["missing_criteria"] == []
    assert not row["details"]["exploratory"]
    assert row["score_lower"] == pytest.approx(row["priority_score"])
    assert row["score_upper"] == pytest.approx(row["priority_score"])


def test_simulated_assistance_is_bounded_and_c7_preserves_unserved_time(setup, env):
    s = setup
    eid, zid = s["emergency"], s["zone"]
    operator, analyst = s["clients"]["OPERATOR"], s["clients"]["ANALYST"]
    with env["owner"].connect() as db:
        water_id = db.execute(
            text("SELECT resource_type_id FROM ops.resource_types WHERE code='WATER'")
        ).scalar()
    if water_id is None:
        water_id = s["post"](
            operator,
            "/resource-types",
            {
                "code": "WATER",
                "unit": "unit",
                "discrete": True,
                "kg_per_unit": "1",
                "m3_per_unit": "0.01",
            },
        )["resource_type_id"]
    reported = datetime.now(UTC) - timedelta(seconds=2)
    need_id = s["post"](
        operator,
        f"/emergencies/{eid}/needs",
        {
            "zone_id": zid,
            "resource_type_id": str(water_id),
            "quantity": "10",
            "unit": "unit",
            "status": "CONFIRMED",
            "urgency": "DEMO",
            "source_id": s["source"],
            "reported_at": reported.isoformat(),
        },
    )["need_id"]
    route = f"/emergencies/{eid}/needs/{need_id}/assistance-events"
    first = {
        "quantity": "4",
        "effective_at": datetime.now(UTC).isoformat(),
        "source_id": s["source"],
        "note": "Synthetic partial assistance",
    }
    assert s["post"](analyst, route, first, 403)
    s["post"](operator, route, first)
    assert s["post"](operator, route, {**first, "quantity": "7"}, 422)

    def calculate():
        snapshot = s["post"](
            analyst,
            f"/emergencies/{eid}/snapshots",
            {"cutoff_at": datetime.now(UTC).isoformat()},
        )
        queued = s["post"](
            analyst,
            f"/emergencies/{eid}/priority-runs",
            {"snapshot_id": snapshot["snapshot_id"]},
            202,
        )
        assert run_once(env["worker"])
        result = analyst.get("/api/v1/priority-runs/" + queued["run_id"] + "/results").json()
        assert result["state"] == "SUCCESS", result
        return result["results"][0]["details"]["criteria"]["C7"]["value"]

    partial = calculate()
    assert 0 < partial < 1
    s["post"](
        operator, route, {**first, "quantity": "6", "effective_at": datetime.now(UTC).isoformat()}
    )
    assert calculate() == 0
    with env["owner"].connect() as db:
        assert (
            db.execute(
                text("SELECT sum(quantity) FROM ops.assistance_events WHERE need_id=:n"),
                {"n": need_id},
            ).scalar()
            == 10
        )
        assert (
            db.execute(
                text(
                    "SELECT count(*) FROM ops.inventory_ledger "
                    "WHERE reason='Synthetic partial assistance'"
                )
            ).scalar()
            == 0
        )
