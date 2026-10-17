"""F4 DEMO raw observations -> eight normalized criteria at a snapshot cutoff."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime

from app.prioritization.core import Criterion, ModelError, deprivation, uncertainty


def _number(value, *, unit=None, expected=None, maximum=None):
    if value is None:
        return None
    number = float(value)
    if not math.isfinite(number) or number < 0 or (maximum is not None and number > maximum):
        raise ModelError("RAW_VALUE_OUT_OF_DOMAIN")
    if expected is not None and unit != expected:
        raise ModelError("RAW_UNIT_MISMATCH")
    return number


def _clip(value):
    if not math.isfinite(value):
        raise ModelError("RAW_VALUE_OUT_OF_DOMAIN")
    return min(1.0, max(0.0, value))


def derive_zone(zone, snapshot, profile):
    """Read only the frozen input snapshot; no live joins or fabricated observations."""
    zid = str(zone["zone_id"])
    cutoff = datetime.fromisoformat(str(snapshot["cutoff_at"]).replace("Z", "+00:00"))
    reports = {
        str(r["report_id"]): r
        for r in snapshot.get("reports", [])
        if str(r["zone_id"]) == zid
        and datetime.fromisoformat(str(r["recorded_at"]).replace("Z", "+00:00")) <= cutoff
    }
    superseded = {str(r["supersedes_id"]) for r in reports.values() if r.get("supersedes_id")}
    reports = {key: row for key, row in reports.items() if key not in superseded}
    observations = defaultdict(list)
    for row in snapshot.get("observations", []):
        rid = str(row["report_id"])
        if rid in reports:
            observations[row["metric_code"]].append((row, reports[rid]))
    selected = {}
    conflict_values = []
    comparisons = 0
    for code, rows in observations.items():
        if code not in profile["metric_contract"]:
            continue
        rows.sort(
            key=lambda item: (
                str(item[1]["observed_at"]),
                str(item[1]["recorded_at"]),
                str(item[0]["observation_id"]),
            )
        )
        selected[code] = rows[-1]
        comparable = [
            float(obs["value_numeric"]) for obs, _ in rows if obs["value_numeric"] is not None
        ]
        if len(comparable) > 1:
            comparisons += 1
            conflict_values.append(
                _clip((max(comparable) - min(comparable)) / max(max(comparable), 1))
            )

    def metric(code):
        if code not in selected:
            return None, "missing", None, None
        obs, report = selected[code]
        status = obs["evidence_status"]
        if status == "UNKNOWN":
            return None, "missing", None, None
        value = _number(
            obs["value_numeric"],
            unit=obs["unit"],
            expected=profile["metric_contract"][code],
            maximum=1 if obs["unit"] in ("fraction", "boolean_0_1") else None,
        )
        observed_at = datetime.fromisoformat(str(report["observed_at"]).replace("Z", "+00:00"))
        if observed_at > cutoff:
            raise ModelError("FUTURE_OBSERVATION")
        return (
            value,
            "observed" if status == "OBSERVED" else "estimated",
            str(report.get("source_id", "unknown-source")) + ":" + str(obs["observation_id"]),
            (cutoff - observed_at).total_seconds() / 3600,
        )

    def criterion(code, calculator, inputs):
        facts = [metric(key) for key in inputs]
        if any(fact[0] is None for fact in facts):
            return Criterion(
                None,
                "missing",
                source="missing:"
                + ",".join(key for key, fact in zip(inputs, facts, strict=True) if fact[0] is None),
            )
        value = _clip(calculator(*[fact[0] for fact in facts]))
        status = "estimated" if any(fact[1] == "estimated" for fact in facts) else "observed"
        return Criterion(value, status, value, value, ",".join(fact[2] for fact in facts))

    ref = profile["references"]
    population = _number(zone["baseline_population"], maximum=None)
    if population is not None and population > 0:
        c1 = criterion(
            "C1",
            lambda severe, trapped: (
                0.65 * _clip(1000 * severe / population / ref["R1_severe_per_1000"])
                + 0.35 * _clip(1000 * trapped / population / ref["R2_trapped_per_1000"])
            ),
            ["severely_injured", "trapped"],
        )
    else:
        c1 = Criterion(None, "missing", source="baseline_population_missing")
    c2 = criterion(
        "C2",
        lambda affected: math.log1p(affected) / math.log1p(ref["P_ref_people"]),
        ["affected_people"],
    )
    c3 = criterion(
        "C3",
        lambda vulnerable, affected: vulnerable / max(affected, 1),
        ["vulnerable_affected_unique", "affected_people"],
    )
    if c3.value is not None:
        v = metric("vulnerable_affected_unique")[0]
        n = metric("affected_people")[0]
        if v > n:
            raise ModelError("VULNERABLE_COUNT_EXCEEDS_AFFECTED")
    facility = profile["critical_facility_weights"]
    c4 = criterion(
        "C4",
        lambda *values: (
            sum(v * w for v, w in zip(values, facility.values(), strict=True))
            / sum(facility.values())
        ),
        list(facility),
    )
    no_route = metric("no_route_confirmed")
    verified_candidates = [
        row for row in snapshot.get("route-candidates", [])
        if str(row["zone_id"]) == zid
        and row["network_revision"] == snapshot.get("network_revision")
        and row["route_status"] in ("VERIFIED_OPEN", "VERIFIED_RESTRICTED")
    ]
    access_route_conflict = no_route[0] == 1 and bool(verified_candidates)
    if no_route[0] is None or no_route[1] != "observed":
        c5 = Criterion(None, "missing", source="route_unknown")
    elif access_route_conflict:
        c5 = Criterion(None, "missing", source="contradicted_by_verified_route_candidate")
    elif no_route[0] == 1:
        c5 = Criterion(1.0, no_route[1], 1.0, 1.0, no_route[2])
    elif no_route[0] == 0:
        c5 = criterion(
            "C5",
            lambda actual, baseline: (
                (actual / baseline - 1) / ref["R5_relative_delay"] if baseline > 0 else math.nan
            ),
            ["actual_travel_sec", "baseline_travel_sec"],
        )
    else:
        raise ModelError("ROUTE_BOOLEAN_INVALID")
    services = profile["basic_service_weights"]
    c6 = criterion(
        "C6",
        lambda *values: sum(v * w for v, w in zip(values, services.values(), strict=True)),
        list(services),
    )

    resource_codes = {
        str(r["resource_type_id"]): r["code"] for r in snapshot.get("resource-types", [])
    }
    specialty_codes = {
        str(r["specialty_type_id"]): r["code"] for r in snapshot.get("specialty-types", [])
    }
    needs = [n for n in snapshot.get("needs", []) if str(n["zone_id"]) == zid]
    superseded_needs = {str(n["supersedes_id"]) for n in needs if n.get("supersedes_id")}
    assistance = defaultdict(list)
    for delivery in snapshot.get("assistance-events", []):
        if str(delivery["zone_id"]) != zid:
            continue
        effective_at = datetime.fromisoformat(str(delivery["effective_at"]).replace("Z", "+00:00"))
        recorded_at = datetime.fromisoformat(str(delivery["recorded_at"]).replace("Z", "+00:00"))
        if effective_at <= cutoff and recorded_at <= cutoff:
            assistance[str(delivery["need_id"])].append(delivery)
    unresolved_supersession = any(assistance[need_id] for need_id in superseded_needs)
    needs = [n for n in needs if str(n["need_id"]) not in superseded_needs]
    active = []
    active_statuses = []
    active_sources = []
    covered_any = False
    unknown = False
    for need in needs:
        code = (
            resource_codes.get(str(need["resource_type_id"]))
            if need.get("resource_type_id")
            else specialty_codes.get(str(need["specialty_type_id"]))
        )
        if code not in ref["H_ref_hours"]:
            continue
        if need["status"] == "UNKNOWN":
            unknown = True
            continue
        quantity = _number(need["quantity"])
        if quantity == 0:
            continue
        deliveries = assistance[str(need["need_id"])]
        delivered = sum(_number(event["quantity"]) for event in deliveries)
        if delivered > quantity + 1e-9:
            raise ModelError("ASSISTANCE_EXCEEDS_NEED")
        fraction_unserved = max(0.0, (quantity - delivered) / quantity)
        if fraction_unserved == 0:
            covered_any = True
            continue
        # A partial delivery never resets the clock of the still-unserved
        # fraction. All events are facts, never stock reservations or orders.
        started = datetime.fromisoformat(
            str(snapshot["emergency"]["start_at"]).replace("Z", "+00:00")
        )
        active.append(
            (
                max(0.0, (cutoff - started).total_seconds() / 3600),
                ref["H_ref_hours"][code],
                fraction_unserved,
            )
        )
        active_statuses.append(need["status"])
        active_sources.append(str(need["need_id"]))
    absence_fact = metric("no_active_essential_need_confirmed")
    confirmed_absence = absence_fact[0] == 1 and absence_fact[1] == "observed"
    if not active and not covered_any and not confirmed_absence:
        unknown = True
    c7value = deprivation(active, unknown=unknown)
    if unresolved_supersession:
        c7value = None
    c7 = (
        Criterion(
            None,
            "missing",
            source="assistance_supersession_unresolved"
            if unresolved_supersession
            else "unknown_essential_need",
        )
        if c7value is None
        else Criterion(
            c7value,
            "observed"
            if (active and all(status == "CONFIRMED" for status in active_statuses))
            or (not active and (covered_any or absence_fact[1] == "observed"))
            else "estimated",
            c7value,
            c7value,
            "needs:" + ",".join(active_sources)
            if active else "assistance:fully-covered" if covered_any else absence_fact[2],
        )
    )
    substantive = [c1, c2, c3, c4, c5, c6, c7]
    coverage = sum(item.status == "observed" for item in substantive) / 7
    ages = [fact[3] for code in selected if (fact := metric(code))[3] is not None]
    staleness = sum(_clip(age / ref["tau_hours"]) for age in ages) / len(ages) if ages else 1.0
    conflict = 1.0 if access_route_conflict else max(conflict_values, default=0.0)
    u = uncertainty(coverage, staleness, conflict)
    c8 = Criterion(u, "observed", u, u, "coverage-age-conflict")
    return {f"C{j}": item for j, item in enumerate([*substantive, c8], 1)}, {
        "coverage": coverage,
        "staleness": staleness,
        "conflict": conflict,
        "conflict_comparisons": comparisons,
        "no_conflict_comparison": comparisons == 0,
        "access_route_conflict": access_route_conflict,
        "verified_route_candidate_ids": [str(row["route_id"]) for row in verified_candidates],
        "observation_age_hours": max(ages, default=None),
        "raw_metric_ids": {
            key: [str(row[0]["observation_id"]) for row in rows]
            for key, rows in observations.items()
        },
        "assistance_event_ids": [
            str(event["event_id"]) for events in assistance.values() for event in events
        ],
        "assistance_supersession_unresolved": unresolved_supersession,
    }
