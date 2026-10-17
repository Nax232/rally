"""Durable SQL worker for snapshot verification and F4 SIMULATED prioritization."""

import argparse
import hashlib
import time
from uuid import uuid4

from sqlalchemy import create_engine, text

from app.api import canonical
from app.prioritization.core import ModelError, rank, score, weights_from_ahp
from app.prioritization.criteria import derive_zone
from app.settings import Settings


def _priority(db, job, snapshot):
    run = db.execute(
        text("SELECT * FROM model.priority_runs WHERE job_id=:j"), {"j": job["job_id"]}
    ).mappings().one()
    profile = run["profile"]
    if hashlib.sha256(canonical(profile).encode()).hexdigest() != run["profile_hash"]:
        raise ModelError("PROFILE_HASH_MISMATCH")
    if profile.get("mode") != "SIMULATED":
        raise ModelError("SIMULATED_ONLY")
    weights, cr = weights_from_ahp(profile["ahp_matrix"], demo=True)
    if any(abs(a - b) > 1e-9 for a, b in zip(weights, profile["weights"], strict=True)):
        raise ModelError("PROFILE_WEIGHT_MATRIX_MISMATCH")
    payload = snapshot["payload"]
    if str(payload["emergency"]["emergency_id"]) != str(job["emergency_id"]):
        raise ModelError("SNAPSHOT_EMERGENCY_MISMATCH")
    zones = payload.get("zones", [])
    if not zones:
        raise ModelError("NO_ZONES")
    calculations = []
    for zone in zones:
        if str(zone["emergency_id"]) != str(job["emergency_id"]):
            raise ModelError("SNAPSHOT_EMERGENCY_MISMATCH")
        criteria, quality = derive_zone(zone, payload, profile)
        result = score(criteria, weights)
        result["quality"] = quality
        result["criteria"] = {
            code: {
                "value": criterion.value,
                "status": criterion.status,
                "lower": criterion.lower,
                "upper": criterion.upper,
                "source": criterion.source,
            }
            for code, criterion in criteria.items()
        }
        result["ahp_cr"] = cr
        result["profile_version"] = run["profile_version"]
        result["observation_age_hours"] = quality["observation_age_hours"]
        result["missing_criteria_count"] = len(result["missing_criteria"])
        calculations.append((str(zone["zone_id"]), result))
    for zone_id, result in rank(calculations):
        db.execute(
            text("""INSERT INTO model.priority_results(
            run_id,emergency_id,zone_id,priority_rank,priority_score,score_lower,
            score_upper,priority_level,uncertainty_index,needs_verification,
            insufficient_evidence,details)
            VALUES(:run,:emergency,:zone,:rank,:score,:lower,:upper,:level,:u,:verify,
            :insufficient,CAST(:details AS jsonb))"""),
            {
                "run": run["run_id"],
                "emergency": job["emergency_id"],
                "zone": zone_id,
                "rank": result["priority_rank"],
                "score": result["priority_score"],
                "lower": result["score_lower"],
                "upper": result["score_upper"],
                "level": result["priority_level"],
                "u": result["uncertainty_index"],
                "verify": result["needs_verification"],
                "insufficient": result["insufficient_evidence"],
                "details": canonical(result),
            },
        )
        for factor in result["factors"]:
            db.execute(
                text("""INSERT INTO model.priority_factors(
                run_id,zone_id,criterion_code,normalized_value,weight,evidence_status,
                source,dplus_contribution,dminus_contribution,delta_counterfactual)
                VALUES(:run,:zone,:criterion,:value,:weight,:status,:source,:dplus,:dminus,:delta)"""),
                {
                    "run": run["run_id"],
                    "zone": zone_id,
                    "criterion": factor["criterion_code"],
                    "value": factor["normalized_value"],
                    "weight": factor["weight"],
                    "status": factor["status"],
                    "source": factor["source"],
                    "dplus": factor["dplus_contribution"],
                    "dminus": factor["dminus_contribution"],
                    "delta": factor["delta_counterfactual"],
                },
            )
    return {"run_id": str(run["run_id"]), "zone_count": len(calculations)}


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
        result = {"verified": valid}
        if not failed and job["kind"] == "PRIORITY":
            try:
                result = _priority(db, job, snapshot)
            except ModelError as exc:
                state = "FAILED"
                code = str(exc)
                result = {"verified": True}
        updated = db.execute(
            text("""UPDATE core.job_runs SET state=:state,result=CAST(:result AS jsonb),
            error_code=:error,ended_at=now(),lease_until=NULL
            WHERE job_id=:j AND owner_token=:t AND state='RUNNING' AND lease_until>now()
            RETURNING job_id"""),
            {
                "state": state,
                "result": canonical(result),
                "error": code,
                "j": job["job_id"],
                "t": token,
            },
        ).scalar()
        if not updated:
            raise RuntimeError("JOB_LEASE_LOST")
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
