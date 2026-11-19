#!/usr/bin/env python3
"""Freeze the Stage 3C.6 residual-mechanism classification and recommendation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main() -> None:
    crossings = read_json(OUT / "phase_a_hpre_scan/threshold_crossings.json")
    regions = read_json(OUT / "phase_a_hpre_scan/candidate_region_freeze.json")
    boundary = read_json(OUT / "phase_b_boundary/boundary_statistics.json")
    controls = read_json(OUT / "controls/control_statistics.json")
    dose = read_json(OUT / "phase_c_optional_dose/dose_statistics.json")
    target_profiles: dict[str, Any] = {}
    for target in ("target_a", "target_b"):
        layer_stats = read_json(OUT / f"phase_a_hpre_scan/{target}_layer_statistics.json")["sign_aligned_layers"]
        crossing = crossings[target]
        strong = crossing["first_50"] is not None and crossing["broad_outcome"] != "R4_transient_rescue_decay"
        broad_count = sum(bool(row["robust_positive"]) and float(row["median_RR"]) >= 0.50 for row in layer_stats)
        phase_b = boundary["targets"].get(target)
        control = controls["targets"].get(target)
        target_profiles[target] = {
            "broad_scan_outcome": crossing["broad_outcome"],
            "threshold_crossings": {key: crossing[key] for key in ("first_20", "first_50", "first_80")},
            "peak_RR": crossing["peak_RR"], "peak_RR_layer": crossing["peak_RR_layer"],
            "peak_median_gain": crossing["peak_median_gain"], "peak_gain_layer": crossing["peak_gain_layer"],
            "strong_residual_rescue": strong,
            "robust_RR50_layer_count": broad_count,
            "broad_residual_rescue": strong and broad_count >= 8,
            "candidate_region": regions["targets"][target]["candidate_region"],
            "boundary_outcome": None if phase_b is None else phase_b["boundary_outcome"],
            "strongest_boundary": None if phase_b is None else phase_b["strongest_confirmed_boundary"],
            "dose_linear_slope": None if target not in dose["targets"] else dose["targets"][target]["linear_slope"],
            "control_statistics": control,
        }
    strong_targets = [target for target, row in target_profiles.items() if row["strong_residual_rescue"]]
    broad_targets = [target for target, row in target_profiles.items() if row["broad_residual_rescue"]]
    supported = []
    if strong_targets:
        supported.append("O1_current_residual_mediation")
    if any(row["threshold_crossings"]["first_20"] is not None and row["threshold_crossings"]["first_50"] is not None and row["threshold_crossings"]["first_50"] > row["threshold_crossings"]["first_20"] for row in target_profiles.values()):
        supported.append("O2_progressive_residual_integration")
    if any(row["boundary_outcome"] in {"B_Attention_integration", "B_MLP_integration"} for row in target_profiles.values()):
        supported.append("O3_boundary_specific_integration")
    if not strong_targets:
        supported.append("O4_residual_insufficiency")
    if target_profiles["target_a"]["strong_residual_rescue"] != target_profiles["target_b"]["strong_residual_rescue"] or abs(float(target_profiles["target_a"]["peak_RR"]) - float(target_profiles["target_b"]["peak_RR"])) >= 0.30:
        supported.append("O5_target_heterogeneous_mechanism")
    if "O5_target_heterogeneous_mechanism" in supported:
        primary_outcome = "O5 — Target-Heterogeneous Mechanism"
    elif "O4_residual_insufficiency" in supported:
        primary_outcome = "O4 — Residual Insufficiency"
    elif "O3_boundary_specific_integration" in supported:
        primary_outcome = "O3 — Boundary-Specific Integration"
    elif "O2_progressive_residual_integration" in supported:
        primary_outcome = "O2 — Progressive Residual Integration"
    else:
        primary_outcome = "O1 — Current-Residual Mediation"
    if not strong_targets:
        recommendation = "GO — Prior-Cache / Two-Query Interaction"
    elif broad_targets:
        recommendation = "GO — Residual Feature / Subspace Mechanism"
    else:
        recommendation = "GO — Token-Type Carrier Atlas"
    target_heterogeneity = {
        "primary_unit": "base_problem_id", "N_unique_bases": 24,
        "targets": target_profiles,
        "peak_RR_difference_A_minus_B": float(target_profiles["target_a"]["peak_RR"]) - float(target_profiles["target_b"]["peak_RR"]),
        "targets_not_pooled_into_one_mechanism": True,
    }
    write_json(OUT / "analysis/target_heterogeneity.json", target_heterogeneity)
    classification = {
        "primary_unit": "base_problem_id", "N_unique_bases": 24,
        "primary_scientific_outcome": primary_outcome, "supported_outcomes": supported,
        "target_profiles": target_profiles,
        "strong_targets": strong_targets, "broad_targets": broad_targets,
        "recommendation": recommendation, "recommendation_is_review_only": True,
        "recommendation_rule_was_prospectively_frozen": True,
        "interpretation_boundary": "RR is unclipped and is not a unique causal information fraction; O and C were reported separately before sign-aligned within-base aggregation.",
        "past_token_kv_donor_patched": False, "visual_kv_donor_patched": False,
        "token_type_scan_started": False, "sink_manipulated": False, "stage4_started": False,
    }
    write_json(OUT / "analysis/current_residual_classification.json", classification)
    print(json.dumps(classification, indent=2))


if __name__ == "__main__":
    main()
