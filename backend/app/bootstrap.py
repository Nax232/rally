"""Explicit administrative bootstrap and a tiny demo seed, never confirmatory scenarios."""

import argparse
import os
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5

from sqlalchemy import create_engine, text

from app.api import insert
from app.security import event, hasher
from app.settings import Settings


def identifier(name):
    return uuid5(NAMESPACE_URL, "sipre:phase9:demo:" + name)


def create_user(db, login, password, roles):
    current = db.execute(
        text("SELECT user_id FROM core.users WHERE login=:l"), {"l": login}
    ).scalar()
    if current:
        return current  # Never reset credentials/permissions during a repeated seed.
    if not password or len(password) < 12:
        raise ValueError("Bootstrap password environment variable requires at least 12 characters")
    uid = uuid4()
    insert(
        db, "core.users", {"user_id": uid, "login": login, "password_hash": hasher.hash(password)}
    )
    for role in roles:
        insert(db, "core.user_roles", {"user_id": uid, "role_code": role})
    event(db, uid, "BOOTSTRAP_USER", "users", uid)
    return uid


def seed(db, admin):
    operator = create_user(
        db,
        "demo.operator",
        os.environ.get("SIPRE_DEMO_PASSWORD"),
        ["OPERATOR", "ANALYST", "VIEWER"],
    )
    eid = identifier("emergency")
    if db.execute(text("SELECT 1 FROM ops.emergencies WHERE emergency_id=:e"), {"e": eid}).scalar():
        return
    db.execute(text("SELECT set_config('sipre.actor_id',:u,true)"), {"u": str(admin)})
    sid, rid, did, zid = [identifier(x) for x in ("source", "resource", "depot", "zone")]
    cutoff = datetime(2026, 1, 1, tzinfo=UTC)
    insert(
        db,
        "ops.sources",
        {
            "source_id": sid,
            "organization": "SIPRE DEMO",
            "kind": "SYNTHETIC",
            "description": "F9 smoke seed; not a confirmatory instance",
            "created_by": admin,
        },
    )
    insert(
        db,
        "ops.resource_types",
        {
            "resource_type_id": rid,
            "code": "F9_DEMO_KIT",
            "unit": "unit",
            "discrete": True,
            "kg_per_unit": 1,
            "m3_per_unit": "0.01",
        },
    )
    insert(
        db,
        "ops.emergencies",
        {
            "emergency_id": eid,
            "name": "F9 DEMO",
            "hazard_type": "SYNTHETIC",
            "territory": "Synthetic test polygon",
            "description": "Infrastructure demonstration only",
            "start_at": cutoff,
            "created_by": admin,
        },
    )
    insert(db, "core.emergency_members", {"emergency_id": eid, "user_id": operator})
    db.execute(
        text("""INSERT INTO geo.zones(zone_id,emergency_id,external_id,name,geom,
        baseline_population,source_id,baseline_at,quality) VALUES(:z,:e,'F9-Z01','DEMO',
        ST_GeomFromText(
        'MULTIPOLYGON(((-71 -33,-70.99 -33,-70.99 -32.99,-71 -32.99,-71 -33)))',4326),
        100,:s,:t,'SYNTHETIC')"""),
        {"z": zid, "e": eid, "s": sid, "t": cutoff},
    )
    db.execute(
        text("""INSERT INTO ops.depots(depot_id,name,geom,source_id)
        VALUES(:d,'F9 DEMO depot',ST_SetSRID(ST_Point(-71,-33),4326),:s)"""),
        {"d": did, "s": sid},
    )
    insert(
        db,
        "ops.inventory_ledger",
        {
            "entry_id": identifier("movement"),
            "depot_id": did,
            "resource_type_id": rid,
            "change_quantity": 10,
            "reason": "F9 synthetic stock",
            "source_id": sid,
            "created_by": admin,
        },
    )
    insert(
        db,
        "ops.needs",
        {
            "need_id": identifier("need"),
            "emergency_id": eid,
            "zone_id": zid,
            "resource_type_id": rid,
            "quantity": None,
            "unit": "unit",
            "status": "UNKNOWN",
            "urgency": "DEMO",
            "source_id": sid,
            "reported_at": cutoff,
            "created_by": admin,
        },
    )
    aid = identifier("asset")
    insert(
        db,
        "ops.physical_assets",
        {
            "asset_id": aid,
            "asset_tag": "F9-DEMO-TRUCK",
            "type": "TRUCK",
            "state": "AVAILABLE",
            "base_id": did,
            "source_id": sid,
        },
    )
    insert(db, "ops.vehicles", {"asset_id": aid, "max_kg": 100, "max_m3": 2, "base_depot_id": did})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", default="admin")
    parser.add_argument("--seed", action="store_true")
    args = parser.parse_args()
    config = Settings()
    if config.database_url is None:
        raise SystemExit("SIPRE_DATABASE_URL for migration role required")
    engine = create_engine(config.database_url.get_secret_value())
    try:
        with engine.begin() as db:
            admin = create_user(
                db, args.login.casefold(), os.environ.get("SIPRE_BOOTSTRAP_PASSWORD"), ["ADMIN"]
            )
            if args.seed:
                seed(db, admin)
        print("Bootstrap complete. Existing users and demo records preserved.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
