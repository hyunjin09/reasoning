#!/usr/bin/env python3
"""Assemble cross-phase Stage 3C.8 analyses after all primary scoring freezes."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage3c8.analysis import inferential_summary


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def per_base_class(rows: list[dict[str, Any]], *, class_field: str, gain_field: str = "gain") -> dict[str, dict[str, float]]:
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[str(row[class_field])][str(row["base_problem_id"])].append(float(row[gain_field]))
    return {
        token_class: {base: float(np.mean(values)) for base, values in bases.items()}
        for token_class, bases in grouped.items()
    }


def fit_base_fixed_effect_model(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Fit a transparent grouped descriptive OLS with a fixed intercept per base."""

    if not rows:
        return {"status": "not_fit", "reason": "no fresh Phase-B positions"}
    bases = sorted({str(row["base_problem_id"]) for row in rows}, key=int)
    lexical = sorted({str(row["token_class"]) for row in rows})
    visual = sorted({str(row["visual_alignment"]) for row in rows})
    reasoning = sorted({str(row["reasoning_role"]) for row in rows})
    columns = ["intercept", "distance_to_t_star"]
    columns += [f"base:{value}" for value in bases[1:]]
    columns += [f"lexical:{value}" for value in lexical[1:]]
    columns += [f"visual:{value}" for value in visual[1:]]
    columns += [f"reasoning:{value}" for value in reasoning[1:]]
    columns += ["boundary"]
    matrix, outcome = [], []
    for row in rows:
        values = [1.0, float(row["distance"])]
        values += [float(str(row["base_problem_id"]) == value) for value in bases[1:]]
        values += [float(str(row["token_class"]) == value) for value in lexical[1:]]
        values += [float(str(row["visual_alignment"]) == value) for value in visual[1:]]
        values += [float(str(row["reasoning_role"]) == value) for value in reasoning[1:]]
        values += [float(row["structural_role"] != "NONE")]
        matrix.append(values)
        outcome.append(float(row["gain"]))
    x = np.asarray(matrix, dtype=np.float64)
    y = np.asarray(outcome, dtype=np.float64)
    beta, _, rank, _ = np.linalg.lstsq(x, y, rcond=None)
    residual = y - x @ beta
    degrees = max(1, len(y) - int(rank))
    variance = float(np.dot(residual, residual) / degrees)
    covariance = variance * np.linalg.pinv(x.T @ x)
    errors = np.sqrt(np.maximum(0.0, np.diag(covariance)))
    scientific = [index for index, name in enumerate(columns) if not name.startswith("base:")]
    return {
        "status": "fit",
        "model": "ordinary least squares with base_problem_id fixed intercepts",
        "grouping": "base_problem_id",
        "random_intercept_requested_by_plan": True,
        "implementation": "base fixed effects used as a transparent grouped alternative because statsmodels is unavailable",
        "N_position_rows": len(rows),
        "N_unique_bases": len(bases),
        "matrix_rank": int(rank),
        "reference_levels": {"base": bases[0], "lexical": lexical[0], "visual_alignment": visual[0], "reasoning_role": reasoning[0]},
        "coefficients": {
            columns[index]: {"estimate": float(beta[index]), "standard_error": float(errors[index])}
            for index in scientific
        },
        "descriptive_only": True,
    }


def main() -> None:
    phase_a_stats = read_json(OUT / "phase_a_tpre/token_type_statistics.json")
    phase_b_stats = read_json(OUT / "analysis/position_vs_type_analysis.json")
    phase_c_stats = read_json(OUT / "phase_c_prompt/token_type_statistics.json")
    phase_a = [row for row in read_jsonl(OUT / "phase_a_tpre/per_base_tpre_rescue.jsonl") if row["cohort_role"] == "fresh"]
    phase_b_positions = [row for row in read_jsonl(OUT / "phase_b_recent/per_position_rescue.jsonl") if row["cohort_role"] == "fresh"]
    phase_b_groups = [row for row in read_jsonl(OUT / "phase_b_recent/type_group_rescue.jsonl") if row["cohort_role"] == "fresh" and row["group"].startswith("lexical:")]
    phase_c_groups = [row for row in read_jsonl(OUT / "phase_c_prompt/prompt_type_group_rescue.jsonl") if row["cohort_role"] == "fresh" and row["group"].startswith("lexical:")]
    write_json(OUT / "analysis/token_type_atlas.json", {
        "phase_a_tpre": phase_a_stats,
        "phase_b_recent": phase_b_stats,
        "phase_c_prompt": phase_c_stats,
        "primary_unit": "base_problem_id",
        "phases_have_distinct_references_and_CRR_is_not_compared_as_a_common_fraction": True,
    })

    phase_a_classes = per_base_class([
        {**row, "gain": row["KV_gain"], "class": row["lexical_semantic_class"]} for row in phase_a
    ], class_field="class")
    phase_b_classes = per_base_class([
        {**row, "class": row["group"].removeprefix("lexical:")} for row in phase_b_groups
    ], class_field="class")
    phase_c_classes = per_base_class([
        {**row, "class": row["group"].removeprefix("lexical:")} for row in phase_c_groups
    ], class_field="class")
    phase_specific = {}
    for token_class in sorted(set(phase_a_classes) | set(phase_b_classes) | set(phase_c_classes)):
        phase_specific[token_class] = {}
        for phase, values in (
            ("phase_a_tpre_KV", phase_a_classes.get(token_class, {})),
            ("phase_b_recent_group_KV", phase_b_classes.get(token_class, {})),
            ("phase_c_prompt_group_KV", phase_c_classes.get(token_class, {})),
        ):
            phase_specific[token_class][phase] = inferential_summary(values)
    write_json(OUT / "analysis/phase_specificity_analysis.json", {
        "classes": phase_specific,
        "warning": "Raw gains use phase-specific deficits/readouts; CRR and magnitude are not directly exchangeable across phases.",
    })
    write_json(OUT / "analysis/hierarchical_descriptive_model.json", fit_base_fixed_effect_model(phase_b_positions))

    matched = read_jsonl(OUT / "phase_b_recent/recency_matched_controls.jsonl")
    boundary = [row for row in matched if row.get("comparison_family") == "lexical_semantic_class" and row["focal_class"] == "PUNCTUATION"]
    by_base: dict[str, list[float]] = defaultdict(list)
    for row in boundary:
        by_base[row["base_problem_id"]].append(float(row["gain_difference"]))
    boundary_summary = inferential_summary({base: float(np.mean(values)) for base, values in by_base.items()})
    write_json(OUT / "analysis/boundary_analysis.json", {
        "punctuation_vs_nearest_other_class_within_base": boundary_summary,
        "matched_rows": len(boundary),
        "descriptive_grouped_analysis": True,
    })
    visual = [row for row in matched if row.get("comparison_family") == "visual_alignment" and row["focal_class"] in {"TARGET_ALIGNED", "MENTION_ALIGNED"}]
    by_base = defaultdict(list)
    for row in visual:
        by_base[row["base_problem_id"]].append(float(row["gain_difference"]))
    write_json(OUT / "analysis/visual_alignment_analysis.json", {
        "recent_reasoning_aligned_vs_nearest_other_alignment": inferential_summary({base: float(np.mean(values)) for base, values in by_base.items()}),
        "prompt_structural_controls_path": "outputs/stage3c8/phase_c_prompt/structural_controls.jsonl",
        "attention_used": False,
    })
    print(json.dumps({"phase_specific_classes": len(phase_specific), "hierarchical_rows": len(phase_b_positions)}, indent=2))


if __name__ == "__main__":
    main()
