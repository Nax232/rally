"""Synthetic raw-data contract tests for F4 C1..C8 and provenance."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.prioritization.core import ModelError, score
from app.prioritization.criteria import derive_zone
from app.prioritization.demo_profile import profile


def synthetic(now, *, age_hours=1):
    zone_id, emergency_id, report_id = str(uuid4()), str(uuid4()), str(uuid4())
    observed = now - timedelta(hours=age_hours)
    values = {
        "severely_injured": 5,
        "trapped": 3,
        "affected_people": 200,
        "vulnerable_affected_unique": 50,
        "health_damage": 0.5,
        "response_damage": 0.2,
        "coordination_damage": 0.1,
        "no_route_confirmed": 0,
        "actual_travel_sec": 1800,
        "baseline_travel_sec": 900,
        "water_interruption": 0.6,
        "electricity_interruption": 0.4,
        "sanitation_interruption": 0.2,
        "telecom_interruption": 0.1,
    }
    units = profile()["metric_contract"]
    snapshot = {
        "cutoff_at": now.isoformat(),
        "emergency": {
            "emergency_id": emergency_id,
            "start_at": (now - timedelta(hours=24)).isoformat(),
        },
        "reports": [
            {
                "report_id": report_id,
                "zone_id": zone_id,
                "observed_at": observed.isoformat(),
                "recorded_at": observed.isoformat(),
                "supersedes_id": None,
            }
        ],
        "observations": [
            {
                "report_id": report_id,
                "observation_id": str(uuid4()),
                "metric_code": key,
                "value_numeric": value,
                "unit": units[key],
                "evidence_status": "OBSERVED",
            }
            for key, value in values.items()
        ],
        "needs": [],
        "resource-types": [],
        "specialty-types": [],
    }
    return {"zone_id": zone_id, "baseline_population": 1000}, snapshot


def test_f4_raw_normalization_and_explanation():
    now = datetime.now(UTC)
    zone, snapshot = synthetic(now)
    criteria, quality = derive_zone(zone, snapshot, profile())
    assert criteria["C1"].value == pytest.approx(0.65 * 0.1 + 0.35 * 0.12)
    assert criteria["C3"].value == 0.25
    assert criteria["C4"].value == pytest.approx(0.5 * 0.5 + 0.2 * 0.3 + 0.1 * 0.2)
    assert criteria["C5"].value == 0.5
    assert criteria["C6"].value == pytest.approx(0.6 * 0.4 + 0.4 * 0.25 + 0.2 * 0.2 + 0.1 * 0.15)
    assert criteria["C7"].value is None
    assert quality["coverage"] == pytest.approx(6 / 7)
    assert quality["no_conflict_comparison"]
    result = score(criteria, profile()["weights"])
    assert 0 <= result["score_lower"] <= result["priority_score"] <= result["score_upper"] <= 1


def test_f4_confirmed_absence_of_active_essential_need_is_zero():
    now = datetime.now(UTC)
    zone, snapshot = synthetic(now)
    snapshot["observations"].append({
        "report_id": snapshot["reports"][0]["report_id"],
        "observation_id": str(uuid4()),
        "metric_code": "no_active_essential_need_confirmed",
        "value_numeric": 1,
        "unit": "boolean_0_1",
        "evidence_status": "OBSERVED",
    })
    criteria, quality = derive_zone(zone, snapshot, profile())
    assert criteria["C7"].value == 0
    assert quality["coverage"] == 1


def test_f4_null_age_conflict_and_time_since_emergency():
    now = datetime.now(UTC)
    zone, snapshot = synthetic(now, age_hours=1)
    initial, quality_initial = derive_zone(zone, snapshot, profile())
    observed_at = now - timedelta(hours=20)
    snapshot["reports"][0]["observed_at"] = observed_at.isoformat()
    snapshot["reports"][0]["recorded_at"] = observed_at.isoformat()
    old, quality_old = derive_zone(zone, snapshot, profile())
    assert old["C8"].value > initial["C8"].value
    assert quality_old["staleness"] > quality_initial["staleness"]
    snapshot["observations"][0]["value_numeric"] = None
    snapshot["observations"][0]["evidence_status"] = "UNKNOWN"
    missing, _ = derive_zone(zone, snapshot, profile())
    assert missing["C1"].value is None and missing["C1"].status == "missing"
    assert missing["C8"].value > old["C8"].value
    need_id, type_id = str(uuid4()), str(uuid4())
    snapshot["resource-types"] = [{"resource_type_id": type_id, "code": "WATER"}]
    snapshot["needs"] = [
        {
            "need_id": need_id,
            "zone_id": zone["zone_id"],
            "resource_type_id": type_id,
            "specialty_type_id": None,
            "quantity": 10,
            "status": "CONFIRMED",
            "supersedes_id": None,
        }
    ]
    with_need, _ = derive_zone(zone, snapshot, profile())
    assert with_need["C7"].value == 1
    snapshot["cutoff_at"] = (now - timedelta(hours=12)).isoformat()
    earlier, _ = derive_zone(zone, snapshot, profile())
    assert earlier["C7"].value == 0.5


def test_f4_rejects_out_of_domain_raw_values():
    zone, snapshot = synthetic(datetime.now(UTC))
    for observation in snapshot["observations"]:
        if observation["metric_code"] == "water_interruption":
            observation["value_numeric"] = 1.5
    with pytest.raises(ModelError, match="RAW_VALUE_OUT_OF_DOMAIN"):
        derive_zone(zone, snapshot, profile())


def test_f4_estimated_route_cannot_be_called_confirmed():
    zone, snapshot = synthetic(datetime.now(UTC))
    for observation in snapshot["observations"]:
        if observation["metric_code"] == "no_route_confirmed":
            observation["evidence_status"] = "ESTIMATED_APPROVED"
    criteria, _ = derive_zone(zone, snapshot, profile())
    assert criteria["C5"].status == "missing"
    assert score(criteria, profile()["weights"])["needs_verification"]


def test_f4_verified_route_conflicts_with_claim_of_no_route():
    zone, snapshot = synthetic(datetime.now(UTC))
    snapshot["network_revision"] = 3
    snapshot["route-candidates"] = [{
        "route_id": str(uuid4()),
        "zone_id": zone["zone_id"],
        "network_revision": 3,
        "route_status": "VERIFIED_OPEN",
    }]
    for observation in snapshot["observations"]:
        if observation["metric_code"] == "no_route_confirmed":
            observation["value_numeric"] = 1
    criteria, quality = derive_zone(zone, snapshot, profile())
    assert criteria["C5"].status == "missing"
    assert quality["access_route_conflict"]
    assert quality["conflict"] == 1
    assert score(criteria, profile()["weights"])["needs_verification"]


def test_f4_partial_assistance_preserves_clock_and_full_cover_zero():
    now = datetime.now(UTC)
    zone, snapshot = synthetic(now)
    need_id, type_id = str(uuid4()), str(uuid4())
    snapshot["resource-types"] = [{"resource_type_id": type_id, "code": "WATER"}]
    snapshot["needs"] = [
        {
            "need_id": need_id,
            "zone_id": zone["zone_id"],
            "resource_type_id": type_id,
            "specialty_type_id": None,
            "quantity": 10,
            "status": "CONFIRMED",
            "supersedes_id": None,
        }
    ]
    before, _ = derive_zone(zone, snapshot, profile())
    assert before["C7"].value == 1
    event = {
        "event_id": str(uuid4()),
        "need_id": need_id,
        "zone_id": zone["zone_id"],
        "quantity": 4,
        "effective_at": (now - timedelta(hours=1)).isoformat(),
        "recorded_at": (now - timedelta(minutes=1)).isoformat(),
    }
    snapshot["assistance-events"] = [event]
    partial, quality = derive_zone(zone, snapshot, profile())
    assert partial["C7"].value == pytest.approx(0.6)
    assert quality["assistance_event_ids"] == [event["event_id"]]
    snapshot["assistance-events"].append({**event, "event_id": str(uuid4()), "quantity": 6})
    complete, _ = derive_zone(zone, snapshot, profile())
    assert complete["C7"].value == 0


def test_f4_superseded_need_with_assistance_requires_reconciliation():
    now = datetime.now(UTC)
    zone, snapshot = synthetic(now)
    old_id, new_id, type_id = str(uuid4()), str(uuid4()), str(uuid4())
    snapshot["resource-types"] = [{"resource_type_id": type_id, "code": "WATER"}]
    base = {
        "zone_id": zone["zone_id"],
        "resource_type_id": type_id,
        "specialty_type_id": None,
        "quantity": 10,
        "status": "CONFIRMED",
    }
    snapshot["needs"] = [
        {**base, "need_id": old_id, "supersedes_id": None},
        {**base, "need_id": new_id, "supersedes_id": old_id},
    ]
    snapshot["assistance-events"] = [
        {
            "event_id": str(uuid4()),
            "need_id": old_id,
            "zone_id": zone["zone_id"],
            "quantity": 4,
            "effective_at": (now - timedelta(hours=1)).isoformat(),
            "recorded_at": (now - timedelta(minutes=1)).isoformat(),
        }
    ]
    criteria, quality = derive_zone(zone, snapshot, profile())
    assert criteria["C7"].status == "missing"
    assert quality["assistance_supersession_unresolved"]
