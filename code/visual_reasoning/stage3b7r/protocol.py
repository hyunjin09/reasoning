"""Pure prospective statistics and split checks for Stage 3B.7-R."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np


def aggregate_numeric_fields_by_base(
    rows: list[dict[str, Any]],
    *,
    fields: list[str],
) -> list[dict[str, Any]]:
    """Average repeated target rows so each base contributes one observation."""

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["base_problem_id"]), []).append(row)
    aggregated = []
    for base_id, base_rows in sorted(grouped.items(), key=lambda item: int(item[0])):
        item: dict[str, Any] = {"base_problem_id": base_id, "target_row_count": len(base_rows)}
        for field in fields:
            values = [float(row[field]) for row in base_rows if row.get(field) is not None]
            if values and not np.isfinite(np.asarray(values, dtype=np.float64)).all():
                raise ValueError(f"non-finite {field} for base {base_id}")
            item[field] = float(np.mean(values)) if values else None
        aggregated.append(item)
    return aggregated


def paired_margins(
    target_effects: np.ndarray,
    sham_effects: np.ndarray,
    irrelevant_effects: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return the frozen semantic-minus-absolute-control paired margins."""

    target = np.asarray(target_effects, dtype=np.float64)
    sham = np.asarray(sham_effects, dtype=np.float64)
    irrelevant = np.asarray(irrelevant_effects, dtype=np.float64)
    if target.shape != sham.shape or target.shape != irrelevant.shape:
        raise ValueError("target, sham, and irrelevant effects must have identical shapes")
    if target.ndim != 1 or not target.size:
        raise ValueError("paired effects must be non-empty one-dimensional arrays")
    if not all(np.isfinite(values).all() for values in (target, sham, irrelevant)):
        raise ValueError("paired effects must be finite")
    return target - np.abs(sham), target - np.abs(irrelevant)


def bootstrap_median_ci(
    values: np.ndarray,
    *,
    iterations: int,
    seed: int,
) -> tuple[float, float]:
    """Compute the frozen percentile bootstrap interval over independent bases."""

    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or not array.size or not np.isfinite(array).all():
        raise ValueError("bootstrap values must be a finite non-empty vector")
    if iterations < 1:
        raise ValueError("bootstrap iterations must be positive")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, array.size, size=(iterations, array.size))
    medians = np.median(array[indices], axis=1)
    low, high = np.quantile(medians, [0.025, 0.975])
    return float(low), float(high)


def target_validation_gate(
    *,
    target_effects: np.ndarray,
    sham_effects: np.ndarray,
    irrelevant_effects: np.ndarray,
    source_consistent: np.ndarray,
    bootstrap_iterations: int,
    seed: int,
) -> dict[str, Any]:
    """Evaluate exactly the seven prospectively frozen semantic conditions."""

    target = np.asarray(target_effects, dtype=np.float64)
    sham = np.asarray(sham_effects, dtype=np.float64)
    irrelevant = np.asarray(irrelevant_effects, dtype=np.float64)
    consistency = np.asarray(source_consistent, dtype=bool)
    sham_margin, irrelevant_margin = paired_margins(target, sham, irrelevant)
    if consistency.shape != target.shape:
        raise ValueError("source-consistency flags must align one-to-one with effects")

    target_ci = bootstrap_median_ci(target, iterations=bootstrap_iterations, seed=seed)
    sham_ci = bootstrap_median_ci(sham_margin, iterations=bootstrap_iterations, seed=seed + 1)
    irrelevant_ci = bootstrap_median_ci(irrelevant_margin, iterations=bootstrap_iterations, seed=seed + 2)
    target_median = float(np.median(target))
    sham_median = float(np.median(sham_margin))
    irrelevant_median = float(np.median(irrelevant_margin))
    bidirectional_fraction = float(np.mean(consistency))
    conditions = {
        "target_median_positive": target_median > 0,
        "target_median_ci_low_positive": target_ci[0] > 0,
        "bidirectional_fraction_at_least_0_75": bidirectional_fraction >= 0.75,
        "sham_margin_median_positive": sham_median > 0,
        "sham_margin_median_ci_low_positive": sham_ci[0] > 0,
        "irrelevant_margin_median_positive": irrelevant_median > 0,
        "irrelevant_margin_median_ci_low_positive": irrelevant_ci[0] > 0,
    }
    return {
        "n": int(target.size),
        "target_median": target_median,
        "target_median_ci": list(target_ci),
        "bidirectional_fraction": bidirectional_fraction,
        "sham_margin_median": sham_median,
        "sham_margin_median_ci": list(sham_ci),
        "irrelevant_margin_median": irrelevant_median,
        "irrelevant_margin_median_ci": list(irrelevant_ci),
        "conditions": conditions,
        "failed_conditions": [name for name, passed in conditions.items() if not passed],
        "semantic_pass": bool(all(conditions.values())),
    }


def validate_disjoint_split(
    *,
    fresh: Iterable[int],
    primary: Iterable[int],
    historical: Iterable[int],
    diagnostic: Iterable[int],
) -> None:
    """Reject overlap between fresh validation and any protected cohort."""

    fresh_set = set(fresh)
    for name, values in (
        ("primary", set(primary)),
        ("historical", set(historical)),
        ("diagnostic", set(diagnostic)),
    ):
        overlap = sorted(fresh_set & values)
        if overlap:
            raise ValueError(f"fresh validation overlaps {name}: {overlap}")


def flatten_scoring_results(
    rows: list[dict[str, Any]],
    *,
    evidence_types: dict[str, str],
) -> list[dict[str, Any]]:
    """Flatten scorer output while restoring frozen annotation metadata.

    Stage 3B.7-R result bundles intentionally keep intervention results compact;
    evidence type remains in the immutable annotation manifests.  Aggregation
    joins that descriptive field by base problem rather than requiring the
    scorer to duplicate it into every result bundle.
    """

    flattened: list[dict[str, Any]] = []
    for base in rows:
        base_id = str(base["base_problem_id"])
        evidence_type = base.get("evidence_type") or evidence_types.get(base_id)
        if not evidence_type:
            raise ValueError(f"missing frozen evidence type for base {base_id}")
        for target in base["targets"]:
            for arm in target["arm_results"]:
                flattened.append(
                    {
                        "base_problem_id": base_id,
                        "example_id": str(base["example_id"]),
                        "evidence_type": str(evidence_type),
                        **arm,
                    }
                )
    return flattened


def select_historical_visual_row(
    result: dict[str, Any],
    *,
    cell_id: str,
    unit_id: str,
    heads: list[int],
) -> dict[str, Any] | None:
    """Select an exact historical V-source row without unit fallback."""

    matches = [
        unit
        for cell in result["cells"]
        for unit in cell["unit_results"]
        if str(cell["cell_id"]) == str(cell_id)
        and str(unit["unit_id"]) == str(unit_id)
        and unit["source_group"] == "V"
        and [int(head) for head in unit["heads"]] == [int(head) for head in heads]
    ]
    if len(matches) > 1:
        raise ValueError(f"duplicate historical V rows for {cell_id}/{unit_id}/{heads}")
    return matches[0] if matches else None


def primary_roi_gate(
    *,
    target_robust: bool,
    target_bidirectional_fraction: float,
    sham_margin_ci_low: float,
    irrelevant_margin_ci_low: float,
    target_greater_irrelevant_fraction: float,
    target_prr: float,
    ring_prr: float,
    mechanical_pass: bool,
) -> bool:
    """Apply the frozen Stage 3B.7-R gate from primary ROI scoring to Phase B."""

    return bool(
        target_robust
        and target_bidirectional_fraction >= 0.75
        and sham_margin_ci_low > 0.0
        and irrelevant_margin_ci_low > 0.0
        and target_greater_irrelevant_fraction >= 0.75
        and max(target_prr, ring_prr) >= 0.50
        and mechanical_pass
    )


def spatial_category(
    *,
    gate_pass: bool,
    target_robust: bool,
    all_visual_robust: bool,
    target_prr: float,
    ring_prr: float,
    complement_prr: float,
    irrelevant_prr: float,
) -> str:
    """Classify spatial recovery using only prospectively frozen thresholds."""

    if not gate_pass:
        return "ROI-Inconclusive"
    if (
        target_robust
        and target_prr >= 0.75
        and complement_prr < 0.50
        and irrelevant_prr < 0.25
    ):
        return "ROI-Local"
    if (
        target_robust
        and target_prr >= 0.25
        and ring_prr >= 0.75
        and ring_prr - target_prr >= 0.20
    ):
        return "ROI-Local-Plus-Context"
    if all_visual_robust and (
        complement_prr >= 0.50 or max(target_prr, ring_prr) < 0.50
    ):
        return "Visual-Distributed"
    return "ROI-Inconclusive"


__all__ = [
    "aggregate_numeric_fields_by_base",
    "bootstrap_median_ci",
    "flatten_scoring_results",
    "paired_margins",
    "primary_roi_gate",
    "select_historical_visual_row",
    "spatial_category",
    "target_validation_gate",
    "validate_disjoint_split",
]
