"""End-to-end HTTP flow against the running Docker API; no test doubles."""

import json
import os
import time
import urllib.error
import urllib.request
from uuid import uuid4

API = os.environ.get("SIPRE_API", "http://127.0.0.1:8001")


def call(method, path, body=None, token=None, csrf=None, key=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(API + path, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Cookie", "sipre_session=" + token)
    if csrf:
        request.add_header("x-csrf-token", csrf)
    if key:
        request.add_header("Idempotency-Key", key)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = response.read().decode()
            return response.status, json.loads(payload) if payload else None, response.headers
    except urllib.error.HTTPError as error:
        payload = error.read().decode()
        return error.code, json.loads(payload) if payload else None, error.headers


def extract(headers, name):
    raw = headers.get("Set-Cookie", "")
    for part in raw.split(","):
        if part.strip().startswith(name + "="):
            return part.strip().split("=", 1)[1].split(";", 1)[0]
    return None


results = []


def check(label, condition, detail=""):
    results.append((bool(condition), label, detail))
    print(
        ("PASS: " if condition else "FAIL: ")
        + label
        + (" :: " + str(detail) if detail and not condition else "")
    )


admin_password = os.environ["SIPRE_BOOTSTRAP_PASSWORD"]
demo_password = os.environ["SIPRE_DEMO_PASSWORD"]

status, body, headers = call(
    "POST", "/api/v1/auth/login", {"login": "admin", "password": admin_password}
)
check("login admin 200", status == 200, (status, body))
admin_token = extract(headers, "sipre_session")
admin_csrf = body["csrf_token"]

status, me, _ = call("GET", "/api/v1/auth/me", token=admin_token)
check("me con roles/capacidades", status == 200 and "ADMIN" in me["roles"], (status, me))

# Create a viewer-only account through the real API.
viewer_login = "viewer-" + uuid4().hex[:10]
viewer_password = "Viewer-Pass-2026!" + uuid4().hex[:6]
status, created, _ = call(
    "POST",
    "/api/v1/users",
    {"login": viewer_login, "password": viewer_password, "roles": ["VIEWER"]},
    token=admin_token,
    csrf=admin_csrf,
    key=uuid4().hex,
)
check("ADMIN crea usuario VIEWER", status == 201, (status, created))

status, body, headers = call(
    "POST", "/api/v1/auth/login", {"login": viewer_login, "password": viewer_password}
)
check("login VIEWER 200", status == 200, (status, body))
viewer_token = extract(headers, "sipre_session")
viewer_csrf = body["csrf_token"]

status, _, _ = call(
    "POST",
    "/api/v1/emergencies",
    {
        "name": "denied",
        "hazard_type": "DEMO",
        "territory": "x",
        "description": "x",
        "start_at": "2026-01-01T00:00:00+00:00",
    },
    token=viewer_token,
    csrf=viewer_csrf,
    key=uuid4().hex,
)
check("VIEWER denegado para crear emergencia (403)", status == 403, status)

# CSRF missing entirely
status2, _, _ = call(
    "POST",
    "/api/v1/emergencies",
    {
        "name": "denied",
        "hazard_type": "DEMO",
        "territory": "x",
        "description": "x",
        "start_at": "2026-01-01T00:00:00+00:00",
    },
    token=admin_token,
    csrf=None,
    key=uuid4().hex,
)
check("sin CSRF rechazado (403)", status2 == 403, status2)

status, body, _ = call("GET", "/api/v1/auth/me")
check("sin sesión rechazado (401)", status == 401, status)

# Full operator flow: emergency -> zone -> need -> snapshot -> job -> worker result.
status, body, headers = call(
    "POST", "/api/v1/auth/login", {"login": "demo.operator", "password": demo_password}
)
check("login demo.operator 200", status == 200, (status, body))
op_token = extract(headers, "sipre_session")
op_csrf = body["csrf_token"]

status, emergency, _ = call(
    "POST",
    "/api/v1/emergencies",
    {
        "name": "F9 E2E",
        "hazard_type": "SYNTHETIC",
        "territory": "Demo",
        "description": "Docker end to end",
        "start_at": "2026-01-01T00:00:00+00:00",
    },
    token=op_token,
    csrf=op_csrf,
    key=uuid4().hex,
)
check("OPERATOR crea emergencia", status == 201, (status, emergency))
eid = emergency["emergency_id"]

status, source, _ = call(
    "POST",
    "/api/v1/sources",
    {"organization": "E2E", "kind": "SYNTHETIC", "description": "Docker"},
    token=op_token,
    csrf=op_csrf,
    key=uuid4().hex,
)
check("crea fuente", status == 201, (status, source))
sid = source["source_id"]

status, zone, _ = call(
    "POST",
    f"/api/v1/emergencies/{eid}/zones",
    {
        "external_id": uuid4().hex,
        "name": "Z1",
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
                [[[-71, -33], [-70.99, -33], [-70.99, -32.99], [-71, -32.99], [-71, -33]]]
            ],
        },
        "baseline_population": 100,
        "source_id": sid,
        "baseline_at": "2026-01-01T00:00:00+00:00",
        "quality": "DEMO",
    },
    token=op_token,
    csrf=op_csrf,
    key=uuid4().hex,
)
check("crea zona MultiPolygon EPSG:4326", status == 201, (status, zone))

status, resource, _ = call(
    "POST",
    "/api/v1/resource-types",
    {
        "code": uuid4().hex,
        "unit": "unit",
        "discrete": True,
        "kg_per_unit": "1",
        "m3_per_unit": "0.01",
    },
    token=op_token,
    csrf=op_csrf,
    key=uuid4().hex,
)
check("crea tipo de recurso", status == 201, (status, resource))
rid = resource["resource_type_id"]

status, need, _ = call(
    "POST",
    f"/api/v1/emergencies/{eid}/needs",
    {
        "zone_id": zone["zone_id"],
        "resource_type_id": rid,
        "quantity": None,
        "unit": "unit",
        "status": "UNKNOWN",
        "urgency": "DEMO",
        "source_id": sid,
        "reported_at": "2026-01-01T00:00:00+00:00",
    },
    token=op_token,
    csrf=op_csrf,
    key=uuid4().hex,
)
check("necesidad UNKNOWN con quantity NULL", status == 201, (status, need))

key2 = uuid4().hex
status, replay, _ = call(
    "POST",
    f"/api/v1/emergencies/{eid}/needs",
    {
        "zone_id": zone["zone_id"],
        "resource_type_id": rid,
        "quantity": None,
        "unit": "unit",
        "status": "UNKNOWN",
        "urgency": "DEMO",
        "source_id": sid,
        "reported_at": "2026-01-01T00:00:00+00:00",
    },
    token=op_token,
    csrf=op_csrf,
    key=key2,
)
status_b, replay_b, _ = call(
    "POST",
    f"/api/v1/emergencies/{eid}/needs",
    {
        "zone_id": zone["zone_id"],
        "resource_type_id": rid,
        "quantity": None,
        "unit": "unit",
        "status": "UNKNOWN",
        "urgency": "DEMO",
        "source_id": sid,
        "reported_at": "2026-01-01T00:00:00+00:00",
    },
    token=op_token,
    csrf=op_csrf,
    key=key2,
)
check(
    "idempotencia devuelve la misma respuesta",
    status_b == status and replay_b == replay,
    (status, status_b),
)
check(
    "idempotencia no duplica filas",
    len({replay.get("need_id"), replay_b.get("need_id")}) == 1,
    (replay, replay_b),
)

status, rows, _ = call("GET", f"/api/v1/emergencies/{eid}/data/needs", token=op_token)
check("data/needs devuelve la necesidad", status == 200 and len(rows) >= 1, (status, rows))

# Snapshot + job as analyst capability (demo.operator also holds ANALYST).
status, snapshot, _ = call(
    "POST",
    f"/api/v1/emergencies/{eid}/snapshots",
    {"cutoff_at": "2026-10-16T12:00:00+00:00"},
    token=op_token,
    csrf=op_csrf,
    key=uuid4().hex,
)
check(
    "snapshot inmutable con fingerprint",
    status == 201 and len(snapshot.get("fingerprint", "")) == 64,
    (status, snapshot),
)

status, job, _ = call(
    "POST",
    f"/api/v1/emergencies/{eid}/jobs",
    {"snapshot_id": snapshot["snapshot_id"]},
    token=op_token,
    csrf=op_csrf,
    key=uuid4().hex,
)
check("job en cola 202", status == 202 and job["state"] == "QUEUED", (status, job))

status, _, _ = call(
    "POST",
    f"/api/v1/emergencies/{eid}/optimization-runs",
    {},
    token=op_token,
    csrf=op_csrf,
    key=uuid4().hex,
)
check("motor F5 aún no implementado (501 explícito)", status == 501, status)

status, queued, _ = call(
    "POST",
    f"/api/v1/emergencies/{eid}/priority-runs",
    {"snapshot_id": snapshot["snapshot_id"]},
    token=op_token,
    csrf=op_csrf,
    key=uuid4().hex,
)
check(
    "F4 encola corrida SIMULATED con perfil DEMO",
    status == 202 and queued.get("profile_validation") == "SYNTHETIC_REVIEW_PENDING",
    (status, queued),
)
if status == 202:
    outcome = None
    for _ in range(30):
        status, outcome, _ = call(
            "GET", f"/api/v1/priority-runs/{queued['run_id']}/results", token=op_token
        )
        if outcome and outcome.get("state") in ("SUCCESS", "FAILED"):
            break
        time.sleep(0.5)
    check(
        "F4 persiste resultado explicable sin despacho",
        status == 200
        and outcome.get("state") == "SUCCESS"
        and len(outcome.get("results", [])) == 1
        and len(outcome["results"][0]["details"]["factors"]) == 8
        and outcome["results"][0]["details"]["exploratory"],
        (status, outcome),
    )

print(
    json.dumps(
        {
            "passed": sum(1 for c, _, _ in results if c),
            "failed": sum(1 for c, _, _ in results if not c),
            "job_id": job.get("job_id"),
            "emergency_id": eid,
        },
        indent=2,
    )
)
raise SystemExit(0 if all(c for c, _, _ in results) else 1)
