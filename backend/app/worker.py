"""Durable SQL worker for foundation snapshot verification, not mathematical engines."""

import argparse
import hashlib
import time
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.api import canonical
from app.settings import Settings


def run_once(engine):
    token = uuid4()
    with engine.begin() as db:
        job = (
            db.execute(
                text("""WITH candidate AS (
            SELECT job_id FROM core.job_runs WHERE state='QUEUED' OR
            (state='RUNNING' AND lease_until<now()) ORDER BY created_at
            FOR UPDATE SKIP LOCKED LIMIT 1)
            UPDATE core.job_runs j SET state='RUNNING',attempts=attempts+1,owner_token=:token,
                lease_until=now()+interval '60 seconds'
            FROM candidate c WHERE j.job_id=c.job_id RETURNING j.*"""),
                {"token": token},
            )
            .mappings()
            .first()
        )
    if not job:
        return False
    with engine.begin() as db:
        snapshot = (
            db.execute(
                text("SELECT * FROM model.input_snapshots WHERE snapshot_id=:s"),
                {"s": job["snapshot_id"]},
            )
            .mappings()
            .one()
        )
        valid = (
            hashlib.sha256(canonical(snapshot["payload"]).encode()).hexdigest()
            == snapshot["fingerprint"]
        )
        failed = not valid or job["attempts"] > 3
        state = "FAILED" if failed else "SUCCESS"
        code = (
            "MAX_ATTEMPTS"
            if job["attempts"] > 3
            else ("SNAPSHOT_HASH_MISMATCH" if not valid else None)
        )
        updated = db.execute(
            text("""UPDATE core.job_runs SET state=:state,result=CAST(:result AS jsonb),
            error_code=:error,ended_at=now(),lease_until=NULL
            WHERE job_id=:j AND owner_token=:t AND state='RUNNING' AND lease_until>now()
            RETURNING job_id"""),
            {
                "state": state,
                "result": canonical({"verified": valid}),
                "error": code,
                "j": job["job_id"],
                "t": token,
            },
        ).scalar()
        if updated:
            db.execute(
                text("""INSERT INTO audit.events(actor_id,action,object_type,object_id,emergency_id)
                VALUES(:u,:action,'jobs',:j,:e)"""),
                {
                    "u": job["created_by"],
                    "action": "JOB_" + state,
                    "j": str(job["job_id"]),
                    "e": job["emergency_id"],
                },
            )
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    if settings.database_url is None:
        raise SystemExit("SIPRE_DATABASE_URL required")
    engine = create_engine(settings.database_url.get_secret_value(), pool_pre_ping=True)
    try:
        while True:
            worked = run_once(engine)
            if args.once:
                break
            if not worked:
                time.sleep(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
