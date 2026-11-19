"""Pure helpers for the frozen Stage 3B.3-R primary protocol."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from visual_reasoning.stage3b3.windows import fine_two_layer_windows


def balanced_primary_shards(
    rows: list[dict[str, Any]], *, shard_count: int
) -> list[list[dict[str, Any]]]:
    """Greedily balance numeric and cheaper structural primary items."""
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    shards: list[list[dict[str, Any]]] = [[] for _ in range(shard_count)]
    loads = [0.0 for _ in range(shard_count)]
    for row in rows:
        weight = 0.55 if "structural" in str(row["edit_tier"]) else 1.0
        destination = min(range(shard_count), key=lambda index: (loads[index], index))
        shards[destination].append(row)
        loads[destination] += weight
    return shards


def apply_redesign_fine_rule(coarse_statistics: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply the original frozen fine gate to BWS and redesigned restoration BSRC."""
    by_key = {(row["coordinate"], row["name"]): row for row in coarse_statistics}
    expected = {(coordinate, f"W{index}") for coordinate in ("Ed_minus_1", "Ed") for index in range(6)}
    if set(by_key) != expected:
        raise ValueError("Fine gate requires exactly six coarse windows at both primary coordinates")

    qualified: dict[str, list[str]] = defaultdict(list)
    audit = []
    for coordinate in ("Ed_minus_1", "Ed"):
        for index in range(6):
            name = f"W{index}"
            statistics = by_key[(coordinate, name)]["statistics"]
            threshold = {
                metric: float(statistics[metric]["median"]) >= 0.20
                for metric in ("BWS_normalized", "BSRC_normalized")
            }
            separated: dict[str, list[str]] = {}
            for metric in ("BWS_normalized", "BSRC_normalized"):
                candidate_low = float(statistics[metric]["median_bootstrap_95_ci"][0])
                separated[metric] = [
                    f"W{other}"
                    for other in range(6)
                    if abs(other - index) >= 2
                    and candidate_low
                    > float(
                        by_key[(coordinate, f"W{other}")]["statistics"][metric][
                            "median_bootstrap_95_ci"
                        ][1]
                    )
                ]
            ci_pass = any(len(comparators) >= 2 for comparators in separated.values())
            passed = any(threshold.values()) or ci_pass
            if passed:
                qualified[coordinate].append(name)
            audit.append({
                "coordinate": coordinate,
                "coarse_window": name,
                "median_normalized_BWS": statistics["BWS_normalized"]["median"],
                "median_normalized_BSRC": statistics["BSRC_normalized"]["median"],
                "threshold_pass": threshold,
                "CI_separated_nonadjacent_windows": separated,
                "CI_separation_pass": ci_pass,
                "qualifies": passed,
            })
    nonempty = {coordinate: names for coordinate, names in qualified.items() if names}
    union = sorted({name for names in nonempty.values() for name in names})
    return {
        "qualified_by_coordinate": nonempty,
        "qualifying_union": union,
        "fine_windows": fine_two_layer_windows(union),
        "restoration_metric_replacing_original_BWN": "BSRC_normalized",
        "reason": "The redesigned paired-semantic restoration estimand replaces the invalid original BWN sham estimand while retaining the prospectively frozen threshold and CI-separation rule.",
        "validation_results_used_for_layer_selection": False,
        "attention_used": False,
        "audit": audit,
    }


def evaluate_localization_decision(
    coarse_rows: list[dict[str, Any]],
    fine_rows: list[dict[str, Any]],
    activation_rows: list[dict[str, Any]],
    *,
    controls_pass: bool,
) -> dict[str, Any]:
    """Apply the frozen Stage 3B.3 decision thresholds with BSRC restoration."""
    if not controls_pass:
        return {
            "recommendation": "REDESIGN",
            "rationale": "One or more intervention-integrity controls failed.",
            "narrow_candidates": [],
            "distributed_coordinates": [],
            "current_state_redirect_candidates": [],
        }

    fine_by_parent: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in fine_rows:
        fine_by_parent[(row["coordinate"], row["parent_window"])].append(row)
    narrow = []
    for row in coarse_rows:
        fine_retains = any(
            max(float(value["BWS_median"]), float(value.get("BSRC_median", float("-inf")))) >= 0.15
            for value in fine_by_parent.get((row["coordinate"], row["name"]), [])
        )
        passes = bool(
            float(row["BWS_median"]) >= 0.20
            and float(row["BSRC_median"]) >= 0.20
            and float(row["BWS_ci_low"]) > 0.0
            and float(row["BSRC_ci_low"]) > 0.0
            and float(row["sufficiency_bidirectional_fraction"]) >= 0.70
            and float(row["restoration_bidirectional_fraction"]) >= 0.70
            and float(row["selective_sham_to_target_ratio"]) < 0.25
            and float(row["restoration_render_to_semantic_ratio"]) < 0.25
            and fine_retains
        )
        if passes:
            narrow.append({
                "coordinate": row["coordinate"],
                "window": row["name"],
                "fine_retains": fine_retains,
            })

    distributed = []
    for coordinate in ("Ed_minus_1", "Ed"):
        count = sum(
            max(float(row["BWS_median"]), float(row["BSRC_median"])) >= 0.10
            for row in coarse_rows
            if row["coordinate"] == coordinate
        )
        if count >= 3:
            distributed.append({"coordinate": coordinate, "qualifying_window_count": count})

    ordered_activation = sorted(activation_rows, key=lambda row: int(row["after_layer"]))
    redirects = []
    for before, after in zip(ordered_activation, ordered_activation[1:]):
        increase = float(after["BAP_median"]) - float(before["BAP_median"])
        if increase >= 0.30 and float(after["BAP_median"]) >= 0.50 and float(after["BAP_ci_low"]) > 0.0:
            redirects.append({
                "after_layer": int(after["after_layer"]),
                "increase": increase,
                "post_median": float(after["BAP_median"]),
            })

    if narrow:
        recommendation = "GO — Module/path localization"
        rationale = "At least one coarse window passes the frozen paired sufficiency/restoration rule and retains a two-layer effect."
    elif distributed:
        recommendation = "GO — Distributed layer mechanism analysis"
        rationale = "No narrow hotspot passes the full rule, but at least three coarse windows meet the frozen distributed-transfer threshold."
    elif redirects:
        recommendation = "REDIRECT — Current-state representation analysis"
        rationale = "Layer-source effects miss the hotspot/distributed rules while current-position residual transfer shows a frozen-threshold transition."
    else:
        recommendation = "REDESIGN"
        rationale = "Controls pass, but none of the prospectively frozen localization or redirect rules is met."
    return {
        "recommendation": recommendation,
        "rationale": rationale,
        "narrow_candidates": narrow,
        "distributed_coordinates": distributed,
        "current_state_redirect_candidates": redirects,
    }
