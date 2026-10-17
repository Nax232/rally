"""F4 AHP and anchored TOPSIS; independent of persistence and zone count."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

CRITERIA = tuple(f"C{i}" for i in range(1, 9))
RI_8 = 1.41
DEMO_WEIGHTS = (0.24, 0.12, 0.16, 0.12, 0.10, 0.10, 0.10, 0.06)


class ModelError(ValueError):
    """A validated model input cannot be calculated or published."""


def _unit(value: float, name: str) -> float:
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise ModelError(f"{name} must be finite and in [0,1]")
    return number


def weights_from_ahp(
    matrix: list[list[float]], *, demo: bool = False
) -> tuple[tuple[float, ...], float]:
    """Geometric row means, Saaty RI8, and the F4 CR publication gate."""
    if matrix is None:
        raise ModelError("MODEL_NOT_CONFIGURED")
    if len(matrix) != 8 or any(len(row) != 8 for row in matrix):
        raise ModelError("AHP matrix must be 8x8")
    a = [[float(value) for value in row] for row in matrix]
    for i in range(8):
        for j in range(8):
            if not math.isfinite(a[i][j]) or a[i][j] <= 0:
                raise ModelError("AHP entries must be finite and positive")
            if i == j and not math.isclose(a[i][j], 1, abs_tol=1e-9):
                raise ModelError("AHP diagonal must equal 1")
            if not math.isclose(a[i][j] * a[j][i], 1, rel_tol=1e-9, abs_tol=1e-9):
                raise ModelError("AHP matrix must be reciprocal")
    means = [math.exp(sum(math.log(v) for v in row) / 8) for row in a]
    total = sum(means)
    weights = tuple(value / total for value in means)
    lam = sum(sum(a[i][j] * weights[j] for j in range(8)) / weights[i] for i in range(8)) / 8
    cr = max(0.0, (lam - 8) / 7 / RI_8)
    if cr > 0.10 + 1e-12:
        raise ModelError("AHP_CONSISTENCY_RATIO_EXCEEDED")
    if demo and weights[7] > 0.08 + 1e-12:
        raise ModelError("DEMO_C8_WEIGHT_EXCEEDED")
    return weights, cr


def validate_weights(
    weights: list[float] | tuple[float, ...], *, demo: bool = False
) -> tuple[float, ...]:
    if weights is None:
        raise ModelError("MODEL_NOT_CONFIGURED")
    if len(weights) != 8:
        raise ModelError("Eight weights required")
    values = tuple(float(weight) for weight in weights)
    if any(not math.isfinite(weight) or weight <= 0 for weight in values):
        raise ModelError("Weights must be finite and positive")
    if abs(sum(values) - 1) > 1e-9:
        raise ModelError("Weights must sum to 1")
    if demo and values[7] > 0.08 + 1e-12:
        raise ModelError("DEMO_C8_WEIGHT_EXCEEDED")
    return values


@dataclass(frozen=True)
class Criterion:
    value: float | None
    status: Literal["observed", "estimated", "missing"]
    lower: float = 0.0
    upper: float = 1.0
    source: str | None = None

    def __post_init__(self):
        _unit(self.lower, "lower")
        _unit(self.upper, "upper")
        if self.lower > self.upper:
            raise ModelError("Criterion interval inverted")
        if self.status == "missing":
            if self.value is not None:
                raise ModelError("Missing criterion must have null value")
        elif self.status in ("observed", "estimated"):
            if self.value is None:
                raise ModelError("Known criterion must have value")
            value = _unit(self.value, "criterion")
            if not self.lower <= value <= self.upper:
                raise ModelError("Criterion value outside interval")
        else:
            raise ModelError("Unknown criterion status")

    @property
    def estimate(self) -> float:
        return (self.lower + self.upper) / 2 if self.value is None else self.value


def distances(
    values: list[float] | tuple[float, ...], weights: tuple[float, ...]
) -> tuple[float, float, float]:
    if len(values) != 8:
        raise ModelError("Eight criteria required")
    clean = [_unit(value, code) for code, value in zip(CRITERIA, values, strict=True)]
    dplus = math.sqrt(
        sum((weight * (1 - value)) ** 2 for weight, value in zip(weights, clean, strict=True))
    )
    dminus = math.sqrt(
        sum((weight * value) ** 2 for weight, value in zip(weights, clean, strict=True))
    )
    return dplus, dminus, dminus / (dplus + dminus)


def score(criteria: dict[str, Criterion], weights: list[float] | tuple[float, ...]) -> dict:
    """Exploratory estimate, fixed-U bounds, and nonadditive factor explanation."""
    if set(criteria) != set(CRITERIA):
        raise ModelError("Exactly C1..C8 required")
    w = validate_weights(weights)
    if criteria["C8"].value is None:
        raise ModelError("C8 uncertainty must be computed, not imputed")
    values = [criteria[code].estimate for code in CRITERIA]
    dplus, dminus, estimate = distances(values, w)
    lower = [criteria[code].lower for code in CRITERIA[:7]] + [values[7]]
    upper = [criteria[code].upper for code in CRITERIA[:7]] + [values[7]]
    score_lower = distances(lower, w)[2]
    score_upper = distances(upper, w)[2]
    if not score_lower - 1e-12 <= estimate <= score_upper + 1e-12:
        raise ModelError("SCORE_INTERVAL_INCONSISTENT")
    factors = []
    for index, code in enumerate(CRITERIA):
        without = values.copy()
        without[index] = 0
        factors.append(
            {
                "criterion_code": code,
                "normalized_value": values[index],
                "status": criteria[code].status,
                "source": criteria[code].source,
                "weight": w[index],
                "dplus_contribution": (w[index] * (1 - values[index])) ** 2,
                "dminus_contribution": (w[index] * values[index]) ** 2,
                "delta_counterfactual": estimate - distances(without, w)[2],
            }
        )
    missing = [code for code in CRITERIA[:7] if criteria[code].status == "missing"]
    uncertainty = values[7]
    return {
        "priority_score": estimate,
        "score_lower": score_lower,
        "score_upper": score_upper,
        "priority_level": "BAJA"
        if estimate < 0.25
        else "MEDIA"
        if estimate < 0.5
        else "ALTA"
        if estimate < 0.75
        else "CRITICA",
        "uncertainty_index": uncertainty,
        "high_uncertainty": uncertainty >= 0.65,
        "needs_verification": bool({"C1", "C5"} & set(missing))
        or len(missing) >= 3
        or uncertainty >= 0.65,
        "insufficient_evidence": len(missing) == 7,
        "missing_criteria": missing,
        "dplus": dplus,
        "dminus": dminus,
        "factors": factors,
        "exploratory": bool(missing),
    }


def rank(rows: list[tuple[str, dict]]) -> list[tuple[str, dict]]:
    """Sort deterministically; D17 tie groups anchored at the first score."""
    ordered = sorted(rows, key=lambda row: (-row[1]["priority_score"], row[0]))
    # Within each group use a stable ID. Anchoring avoids a non-transitive
    # comparator when three scores differ pairwise by ~1e-9.
    groups: list[list[tuple[str, dict]]] = []
    for row in ordered:
        if not groups or groups[-1][0][1]["priority_score"] - row[1]["priority_score"] > 1e-9:
            groups.append([row])
        else:
            groups[-1].append(row)
    result = []
    for group in groups:
        for row in sorted(group, key=lambda item: item[0]):
            result.append((row[0], {**row[1], "priority_rank": len(result) + 1}))
    return result


def uncertainty(coverage: float, staleness: float, conflict: float) -> float:
    return (
        0.50 * (1 - _unit(coverage, "coverage"))
        + 0.30 * _unit(staleness, "staleness")
        + 0.20 * _unit(conflict, "conflict")
    )


def deprivation(
    active_needs: list[tuple[float, float, float]], *, unknown: bool = False
) -> float | None:
    """(hours since effective assistance, H_ref, unserved fraction) per need."""
    if not active_needs:
        return None if unknown else 0.0
    values = []
    for hours, reference, fraction in active_needs:
        if not math.isfinite(hours) or hours < 0 or not math.isfinite(reference) or reference <= 0:
            raise ModelError("Invalid deprivation hours/reference")
        values.append(min(1, hours / reference) * _unit(fraction, "unserved fraction"))
    return max(values)
