"""Synthetic F4 profile for academic SIMULATED runs; review pending.

None of these reference values, metric mappings or conflict tolerances is an
operational threshold. They are proposed solely to exercise the raw-data path.
"""

import math
from copy import deepcopy

from app.prioritization.core import DEMO_WEIGHTS, ModelError, weights_from_ahp

VERSION = "F4-DEMO-SYNTHETIC-1-REVIEW-PENDING"

PROFILE = {
    "version": VERSION,
    "mode": "SIMULATED",
    "validation": "SYNTHETIC_REVIEW_PENDING",
    "algorithm": "anchored-topsis-v1",
    "ahp_method": "geometric-row-mean",
    "weights": list(DEMO_WEIGHTS),
    "ahp_matrix": [[a / b for b in DEMO_WEIGHTS] for a in DEMO_WEIGHTS],
    "references": {
        "R1_severe_per_1000": 50.0,
        "R2_trapped_per_1000": 25.0,
        "P_ref_people": 10000.0,
        "R5_relative_delay": 2.0,
        "H_ref_hours": {"WATER": 24.0, "FOOD": 24.0, "MEDICAL": 12.0, "SHELTER": 24.0},
        "tau_hours": 24.0,
    },
    "critical_facility_weights": {
        "health_damage": 0.5,
        "response_damage": 0.3,
        "coordination_damage": 0.2,
    },
    "basic_service_weights": {
        "water_interruption": 0.4,
        "electricity_interruption": 0.25,
        "sanitation_interruption": 0.2,
        "telecom_interruption": 0.15,
    },
    "missing_interval": [0.0, 1.0],
    "uncertainty_weights": {"incomplete": 0.5, "stale": 0.3, "conflict": 0.2},
    "conflict_rule": "max pairwise absolute difference / max(max pair,1), clipped to [0,1]",
    "tie_rule": "descending score; first-score anchored groups <=1e-9; stable zone_id within group",
    "metric_contract": {
        "severely_injured": "persons",
        "trapped": "persons",
        "affected_people": "persons",
        "vulnerable_affected_unique": "persons",
        "health_damage": "fraction",
        "response_damage": "fraction",
        "coordination_damage": "fraction",
        "no_route_confirmed": "boolean_0_1",
        "actual_travel_sec": "seconds",
        "baseline_travel_sec": "seconds",
        "no_active_essential_need_confirmed": "boolean_0_1",
        "water_interruption": "fraction",
        "electricity_interruption": "fraction",
        "sanitation_interruption": "fraction",
        "telecom_interruption": "fraction",
    },
}


def profile():
    candidate = deepcopy(PROFILE)
    weights, cr = weights_from_ahp(candidate["ahp_matrix"], demo=True)
    if any(abs(a - b) > 1e-9 for a, b in zip(weights, candidate["weights"], strict=True)):
        raise ModelError("PROFILE_WEIGHT_MATRIX_MISMATCH")
    for key in ("critical_facility_weights", "basic_service_weights", "uncertainty_weights"):
        values = candidate[key].values()
        if any(not math.isfinite(value) or value <= 0 for value in values):
            raise ModelError("PROFILE_INVALID_SUBWEIGHTS")
        if abs(sum(values) - 1) > 1e-9:
            raise ModelError("PROFILE_INVALID_SUBWEIGHTS")
    references = candidate["references"]
    scalar_refs = [value for key, value in references.items() if key != "H_ref_hours"]
    if any(not math.isfinite(value) or value <= 0 for value in scalar_refs):
        raise ModelError("PROFILE_INVALID_REFERENCE")
    if any(not math.isfinite(value) or value <= 0 for value in references["H_ref_hours"].values()):
        raise ModelError("PROFILE_INVALID_REFERENCE")
    candidate["ahp_cr"] = cr
    return candidate
