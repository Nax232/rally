"""F4 acceptance tests against the approved synthetic fixture and invariants."""

import json
import math
from pathlib import Path

import pytest
from app.prioritization.core import (
    CRITERIA,
    DEMO_WEIGHTS,
    Criterion,
    ModelError,
    deprivation,
    rank,
    score,
    uncertainty,
    weights_from_ahp,
)

FIXTURE = json.loads(
    (Path(__file__).resolve().parents[3] / "SIPRE_PRIORIZACION_EJEMPLO.json").read_text()
)


def vector(values):
    return {
        code: Criterion(value, "observed", value, value, "synthetic-fixture")
        for code, value in zip(CRITERIA, values, strict=True)
    }


def test_p4_t01_t02_t03_ahp_gates():
    matrix = [[a / b for b in DEMO_WEIGHTS] for a in DEMO_WEIGHTS]
    weights, cr = weights_from_ahp(matrix, demo=True)
    assert weights == pytest.approx(DEMO_WEIGHTS)
    assert cr == pytest.approx(0, abs=1e-12)
    wrong = [[1.0] * 8 for _ in range(8)]
    for i, j in ((0, 1), (1, 2), (2, 0)):
        wrong[i][j], wrong[j][i] = 9.0, 1 / 9
    with pytest.raises(ModelError, match="CONSISTENCY"):
        weights_from_ahp(wrong)
    for bad in (matrix[:7], [[0] * 8 for _ in range(8)], [[-1] * 8 for _ in range(8)]):
        with pytest.raises(ModelError):
            weights_from_ahp(bad)
    with pytest.raises(ModelError, match="reciprocal"):
        weights_from_ahp(
            [
                [3 if (i, j) == (0, 1) else v for j, v in enumerate(row)]
                for i, row in enumerate(matrix)
            ]
        )


def test_p4_t04_t05_extremes_and_fixture():
    assert score(vector([0] * 8), DEMO_WEIGHTS)["priority_score"] == 0
    assert score(vector([1] * 8), DEMO_WEIGHTS)["priority_score"] == 1
    rows = []
    for zone in FIXTURE["zones"]:
        result = score(vector(list(zone["criteria"].values())), DEMO_WEIGHTS)
        for key in ("priority_score", "dplus", "dminus"):
            fixture_key = {"dplus": "d_plus", "dminus": "d_minus"}.get(key, key)
            assert result[key] == pytest.approx(zone["expected"][fixture_key], abs=1e-5)
        rows.append((zone["zone_id"], result))
    assert [key for key, _ in rank(rows)] == FIXTURE["expected_ranking"]


def test_p4_t06_t07_t14_anchored_monotonic_and_deterministic():
    base = score(vector([0.4] * 8), DEMO_WEIGHTS)
    other = score(vector([0.8] * 8), DEMO_WEIGHTS)
    assert score(vector([0.4] * 8), DEMO_WEIGHTS) == base
    assert rank([("A", base), ("B", other)])[1][1]["priority_score"] == base["priority_score"]
    raised = score(vector([0.5] + [0.4] * 7), DEMO_WEIGHTS)
    assert raised["priority_score"] >= base["priority_score"]


def test_p4_t08_t09_t12_missing_distinct_from_zero_and_fixed_u():
    known = vector([0] * 8)
    missing = known | {"C1": Criterion(None, "missing", source="no-report")}
    result = score(missing, DEMO_WEIGHTS)
    assert result["exploratory"] and result["needs_verification"]
    assert result["score_lower"] == pytest.approx(0)
    assert result["score_lower"] <= result["priority_score"] <= result["score_upper"]
    assert result["priority_score"] > score(known, DEMO_WEIGHTS)["priority_score"]
    all_missing = {code: Criterion(None, "missing") for code in CRITERIA[:7]}
    all_missing["C8"] = Criterion(0.9, "observed", 0.9, 0.9)
    result = score(all_missing, DEMO_WEIGHTS)
    assert result["insufficient_evidence"] and result["needs_verification"]
    assert result["priority_score"] > 0


def test_p4_t10_t11_uncertainty_and_elapsed_facts():
    assert uncertainty(0.25, 0.8, 0.5) > uncertainty(0.75, 0.1, 0)
    assert deprivation([(6, 12, 1)]) == 0.5
    assert deprivation([(6, 12, 0.25)]) == 0.125
    assert deprivation([]) == 0
    assert deprivation([], unknown=True) is None


def test_p4_t13_t16_t17_explanation_profiles_no_dispatch():
    result = score(vector([0.4] * 8), DEMO_WEIGHTS)
    assert math.sqrt(sum(f["dplus_contribution"] for f in result["factors"])) == pytest.approx(
        result["dplus"]
    )
    assert math.sqrt(sum(f["dminus_contribution"] for f in result["factors"])) == pytest.approx(
        result["dminus"]
    )
    assert "decision" not in result and "dispatch" not in result and "quantity" not in result
    with pytest.raises(ModelError):
        score(vector([0.4] * 8), [1 / 8] * 7)
    with pytest.raises(ModelError, match="MODEL_NOT_CONFIGURED"):
        score(vector([0.4] * 8), None)
    with pytest.raises(ModelError, match="DEMO_C8"):
        high_c8 = [0.20, 0.12, 0.16, 0.12, 0.10, 0.10, 0.10, 0.10]
        weights_from_ahp([[a / b for b in high_c8] for a in high_c8], demo=True)


def test_p4_t14_tie_group_is_deterministic_and_nontransitive_safe():
    base = score(vector([0.5] * 8), DEMO_WEIGHTS)
    rows = [
        ("Z", {**base, "priority_score": 0.5 + 1.6e-9}),
        ("B", {**base, "priority_score": 0.5 + 0.8e-9}),
        ("A", {**base, "priority_score": 0.5}),
    ]
    assert [key for key, _ in rank(rows)] == ["B", "Z", "A"]
    assert rank(list(reversed(rows))) == rank(rows)
