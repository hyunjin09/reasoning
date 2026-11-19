"""Pure metrics and acceptance checks for A6000 platform calibration."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

from scipy.stats import spearmanr


CANDIDATES = ("original_candidate", "counterfactual_candidate")

CRITERION_NAMES = {
    1: "deterministic replay",
    2: "full versus memory-bounded scoring parity",
    3: "cached versus full recomputation parity",
    4: "self patches reproduce recipients",
    5: "intervention selectivity",
    6: "GQA and RoPE layouts",
    7: "all outputs finite",
    8: "at least two A6000 devices pass",
    9: "no device-specific intervention failure",
    10: "no frozen-pool long-prefix OOM",
    11: "strong prior effects preserve direction on at least 90 percent",
    12: "no systematic strong-effect sign reversal",
    13: "target-versus-control ordering remains intact",
    14: "threshold-adjacent disagreements documented without retuning",
    15: "long-prefix stress test",
    16: "W8 and W16 mechanics",
    17: "event-span rescue mechanics",
    18: "matched-neighbor mechanics",
    19: "local and final readout scoring",
    20: "route-intervention dry run when mechanically eligible",
}


def _token_log_probabilities(score: Mapping[str, Any], candidate: str) -> list[float]:
    try:
        values = score[candidate]["token_log_probabilities"]
    except (KeyError, TypeError) as error:
        raise ValueError(f"Missing {candidate} token log probabilities") from error
    return [float(value) for value in values]


def compare_scores(
    reference: Mapping[str, Any], observed: Mapping[str, Any], *, tolerance: float,
) -> dict[str, Any]:
    """Compare candidate-level teacher scores without hiding shape mismatch."""

    if tolerance < 0:
        raise ValueError("Tolerance must be nonnegative")
    token_deltas: list[float] = []
    candidate_rows = {}
    for candidate in CANDIDATES:
        left = _token_log_probabilities(reference, candidate)
        right = _token_log_probabilities(observed, candidate)
        if len(left) != len(right):
            raise ValueError("Compared candidate token lengths differ")
        deltas = [abs(a - b) for a, b in zip(left, right)]
        token_deltas.extend(deltas)
        candidate_rows[candidate] = {
            "token_count": len(left),
            "max_abs_delta": max(deltas, default=0.0),
            "deltas": deltas,
        }
    aggregate_delta = abs(float(reference["D"]) - float(observed["D"]))
    token_delta = max(token_deltas, default=0.0)
    finite = all(isfinite(value) for value in [aggregate_delta, token_delta, *token_deltas])
    return {
        "tolerance": float(tolerance),
        "aggregate_D_max_abs_delta": aggregate_delta,
        "token_log_probability_max_abs_delta": token_delta,
        "candidates": candidate_rows,
        "finite": finite,
        "passed": bool(finite and aggregate_delta <= tolerance and token_delta <= tolerance),
    }


def validate_calibration_cohort(payload: Mapping[str, Any]) -> dict[str, Any]:
    cells = list(payload.get("cells", []))
    bases = [str(cell["base_problem_id"]) for cell in cells]
    strata = Counter(str(cell["effect_stratum"]) for cell in cells)
    expected = {"strong": 4, "medium": 4, "threshold_adjacent_or_small": 4}
    long_count = sum(bool(cell.get("long_prefix_stress")) for cell in cells)
    checks = {
        "base_count_12": len(cells) == 12,
        "unique_base_count_12": len(set(bases)) == 12,
        "strata_exact": dict(strata) == expected,
        "at_least_three_long_prefix": long_count >= 3,
    }
    return {
        "base_count": len(cells),
        "unique_base_count": len(set(bases)),
        "stratum_counts": dict(strata),
        "long_prefix_count": long_count,
        "checks": checks,
        "passed": all(checks.values()),
    }


def _direction(value: float) -> int:
    return 1 if value > 0 else -1 if value < 0 else 0


def continuity_statistics(
    rows: Sequence[Mapping[str, Any]], *, hardware_sensitive_band: float,
) -> dict[str, Any]:
    if not rows:
        raise ValueError("Continuity rows must be nonempty")
    values_5000 = [float(row["a5000"]) for row in rows]
    values_6000 = [float(row["a6000"]) for row in rows]
    deltas = [abs(left - right) for left, right in zip(values_5000, values_6000)]
    strong_medium = [
        row for row in rows if str(row["stratum"]) in {"strong", "medium"}
    ]
    adjacent = [
        row for row in rows if str(row["stratum"]) == "threshold_adjacent_or_small"
    ]

    def agreement(selected: Sequence[Mapping[str, Any]]) -> float | None:
        if not selected:
            return None
        return sum(
            _direction(float(row["a5000"])) == _direction(float(row["a6000"]))
            for row in selected
        ) / len(selected)

    correlation = spearmanr(values_5000, values_6000).statistic if len(rows) >= 2 else None
    ordered = sorted(deltas)
    middle = len(ordered) // 2
    median = (
        ordered[middle]
        if len(ordered) % 2
        else (ordered[middle - 1] + ordered[middle]) / 2
    )
    return {
        "row_count": len(rows),
        "median_absolute_difference": median,
        "maximum_absolute_difference": max(deltas),
        "spearman_rank_correlation": None if correlation is None else float(correlation),
        "overall_direction_agreement": agreement(rows),
        "strong_medium_direction_agreement": agreement(strong_medium),
        "threshold_adjacent_direction_agreement": agreement(adjacent),
        "hardware_sensitive_band": float(hardware_sensitive_band),
        "hardware_sensitive_count": sum(
            abs(float(row["a5000"])) <= hardware_sensitive_band for row in rows
        ),
        "absolute_differences": deltas,
    }


def acceptance_checklist(evidence: Mapping[str, Any]) -> dict[str, Any]:
    expected = {str(index) for index in CRITERION_NAMES}
    if set(evidence) != expected:
        raise ValueError("Acceptance evidence must contain exactly criteria 1 through 20")
    rows = [
        {
            "criterion_id": index,
            "criterion": CRITERION_NAMES[index],
            "passed": bool(evidence[str(index)]),
        }
        for index in sorted(CRITERION_NAMES)
    ]
    return {
        "criterion_count": len(rows),
        "passed_count": sum(row["passed"] for row in rows),
        "failed_count": sum(not row["passed"] for row in rows),
        "overall_passed": all(row["passed"] for row in rows),
        "criteria": rows,
    }


__all__ = [
    "CRITERION_NAMES",
    "acceptance_checklist",
    "compare_scores",
    "continuity_statistics",
    "validate_calibration_cohort",
]
