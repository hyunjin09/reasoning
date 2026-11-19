"""Paired-semantic restoration metrics and prospectively frozen validation gates."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any


SEMANTIC_VARIANTS = ("O", "O_sham", "C", "C_sham")


def semantic_restoration_metrics(
    *,
    original_history: Mapping[str, float],
    counterfactual_history: Mapping[str, float],
    all_layer_bri: float,
) -> dict[str, Any]:
    """Contrast O/C semantic classes while measuring within-class render variation."""

    for name, values in (
        ("original_history", original_history),
        ("counterfactual_history", counterfactual_history),
    ):
        missing = set(SEMANTIC_VARIANTS) - set(values)
        if missing:
            raise ValueError(f"{name} is missing variants: {sorted(missing)}")
    oh_o = statistics.fmean([float(original_history["O"]), float(original_history["O_sham"])])
    oh_c = statistics.fmean([float(original_history["C"]), float(original_history["C_sham"])])
    ch_o = statistics.fmean([
        float(counterfactual_history["O"]), float(counterfactual_history["O_sham"])
    ])
    ch_c = statistics.fmean([
        float(counterfactual_history["C"]), float(counterfactual_history["C_sham"])
    ])
    src_o = oh_o - oh_c
    src_c = ch_o - ch_c
    bsrc = statistics.fmean([src_o, src_c])
    artifact_terms = {
        "A_O_original_history": abs(float(original_history["O"]) - float(original_history["O_sham"])),
        "A_C_original_history": abs(float(original_history["C"]) - float(original_history["C_sham"])),
        "A_O_counterfactual_history": abs(
            float(counterfactual_history["O"]) - float(counterfactual_history["O_sham"])
        ),
        "A_C_counterfactual_history": abs(
            float(counterfactual_history["C"]) - float(counterfactual_history["C_sham"])
        ),
    }
    a_render = statistics.fmean(artifact_terms.values())
    bri = abs(float(all_layer_bri))
    active = abs(bsrc) >= 0.10 * bri
    return {
        "R_O": oh_o,
        "R_C": oh_c,
        "SRC_O": src_o,
        "SRC_C": src_c,
        "BSRC": bsrc,
        "BSRC_normalized": None if bri == 0.0 else bsrc / bri,
        **artifact_terms,
        "A_render": a_render,
        "all_layer_BRI": float(all_layer_bri),
        "activity_floor": 0.10 * bri,
        "active": active,
        "render_to_semantic_ratio": None if bsrc == 0.0 else a_render / abs(bsrc),
        "render_to_all_layer_ratio": None if bri == 0.0 else a_render / bri,
        "O_restoration_source_consistent": src_o > 0.0,
        "C_restoration_source_consistent": src_c > 0.0,
        "bidirectionally_source_consistent": src_o > 0.0 and src_c > 0.0,
    }


def _one_sided_binomial_p(successes: int, trials: int) -> float:
    return sum(math.comb(trials, value) for value in range(successes, trials + 1)) / (2**trials)


def evaluate_restoration_gates(
    rows: Sequence[Mapping[str, Any]], *, expected_base_count: int = 8
) -> dict[str, Any]:
    """Apply the predeclared base-aggregated Gates A--D."""

    by_base: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_base[str(row["base_problem_id"])].append(row)
    if len(by_base) != expected_base_count:
        raise ValueError(
            f"Expected {expected_base_count} independent bases, observed {len(by_base)}"
        )

    base_rows = []
    for base, base_values in sorted(by_base.items()):
        active = [value for value in base_values if bool(value["active"])]
        if active:
            summary = {
                "base_problem_id": base,
                "active_window_coordinate_count": len(active),
                "median_BSRC": statistics.median(float(value["BSRC"]) for value in active),
                "median_SRC_O": statistics.median(float(value["SRC_O"]) for value in active),
                "median_SRC_C": statistics.median(float(value["SRC_C"]) for value in active),
                "median_render_to_semantic_ratio": statistics.median(
                    float(value["render_to_semantic_ratio"]) for value in active
                ),
                "median_render_to_all_layer_ratio": statistics.median(
                    float(value["render_to_all_layer_ratio"]) for value in active
                ),
                "median_A_render": statistics.median(float(value["A_render"]) for value in active),
            }
            summary["bidirectionally_source_consistent"] = bool(
                summary["median_SRC_O"] > 0.0 and summary["median_SRC_C"] > 0.0
            )
        else:
            summary = {
                "base_problem_id": base,
                "active_window_coordinate_count": 0,
                "median_BSRC": None,
                "median_SRC_O": None,
                "median_SRC_C": None,
                "median_render_to_semantic_ratio": None,
                "median_render_to_all_layer_ratio": None,
                "median_A_render": None,
                "bidirectionally_source_consistent": False,
            }
        base_rows.append(summary)

    active_bases = [value for value in base_rows if value["active_window_coordinate_count"] > 0]
    consistent_count = sum(bool(value["bidirectionally_source_consistent"]) for value in base_rows)
    binomial_p = _one_sided_binomial_p(consistent_count, expected_base_count)
    cohort_median_bsrc = (
        statistics.median(float(value["median_BSRC"]) for value in active_bases)
        if active_bases else None
    )
    median_render_semantic = (
        statistics.median(float(value["median_render_to_semantic_ratio"]) for value in active_bases)
        if active_bases else None
    )
    median_render_all = (
        statistics.median(float(value["median_render_to_all_layer_ratio"]) for value in active_bases)
        if active_bases else None
    )
    gate_a = bool(
        consistent_count >= 7
        and binomial_p < 0.05
        and cohort_median_bsrc is not None
        and cohort_median_bsrc > 0.0
    )
    gate_b = len(active_bases) >= 7
    gate_c = median_render_semantic is not None and median_render_semantic <= 0.25
    gate_d = median_render_all is not None and median_render_all <= 0.05
    return {
        "independent_unit": "base_problem_id",
        "expected_base_count": expected_base_count,
        "observed_base_count": len(base_rows),
        "active_base_count": len(active_bases),
        "base_summaries": base_rows,
        "gate_A": {
            "passed": gate_a,
            "bidirectionally_consistent_base_count": consistent_count,
            "required_count": 7,
            "one_sided_exact_binomial_p": binomial_p,
            "cohort_median_active_base_BSRC": cohort_median_bsrc,
        },
        "gate_B": {"passed": gate_b, "active_base_count": len(active_bases), "required_count": 7},
        "gate_C": {
            "passed": gate_c,
            "median_base_render_to_semantic_ratio": median_render_semantic,
            "maximum": 0.25,
        },
        "gate_D": {
            "passed": gate_d,
            "median_base_render_to_all_layer_ratio": median_render_all,
            "maximum": 0.05,
        },
        "all_gates_passed": bool(gate_a and gate_b and gate_c and gate_d),
    }

