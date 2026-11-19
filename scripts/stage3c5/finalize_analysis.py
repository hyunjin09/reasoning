#!/usr/bin/env python3
"""Freeze Stage 3C.5 joint classification and target heterogeneity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c5"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def target_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = {}
    for target_id in ("target_a", "target_b"):
        selected = [row for row in rows if row["target_id"] == target_id]
        result[target_id] = {
            "N": len(selected),
            "BCR_median": float(np.median([row["BCR"] for row in selected])),
            "BCR_mean": float(np.mean([row["BCR"] for row in selected])),
            "positive_count": sum(float(row["BCR"]) > 0 for row in selected),
            "CRR_median": float(np.median([row["CRR"] for row in selected])),
            "sham_absolute_shift_median": float(np.median([row["mean_sham_absolute_shift"] for row in selected])),
        }
    return result


def main() -> None:
    phase_a = read_json(OUT / "phase_a_tpre_layer/tpre_layer_statistics.json")
    necessary = read_json(OUT / "analysis/necessary_window_analysis.json")
    handoff = read_json(OUT / "phase_b_handoff/handoff_statistics.json")
    gated = read_json(OUT / "phase_b_handoff/gated_r_statistics.json")
    controls = read_json(OUT / "controls/target_specificity_statistics.json")
    carrier_files = {
        "R_last1": "r_last1_results.jsonl", "R_last2": "r_last2_results.jsonl",
        "R_last4": "r_last4_results.jsonl", "Q": "q_results.jsonl", "h_pre": "hpre_results.jsonl",
    }
    target_profiles = {
        carrier: target_summary(read_jsonl(OUT / "phase_b_handoff" / filename))
        for carrier, filename in carrier_files.items()
    }
    target_heterogeneity = {
        "primary_unit": "base_problem_id", "N_unique_bases": 24,
        "phase_a": {
            target_id: {
                label: {
                    "median_loss": float(phase_a["targets"][target_id][label]["loss_summary"]["median"]),
                    "median_retention": float(phase_a["targets"][target_id][label]["retained_median"]),
                    "positive_count": int(phase_a["targets"][target_id][label]["loss_summary"]["positive_count"]),
                }
                for label in phase_a["scopes"]
            }
            for target_id in ("target_a", "target_b")
        },
        "carrier_profiles": target_profiles,
        "interpretation": "Target A has substantially stronger immediate current-residual and R carriage; Target B remains more robust and weakly transferred. Results are not pooled away.",
    }
    write_json(OUT / "analysis/target_heterogeneity.json", target_heterogeneity)
    per_problem = read_jsonl(OUT / "phase_b_handoff/per_problem_handoff.jsonl")
    carrier_comparison = {
        "primary_unit": "base_problem_id", "N_unique_bases": len(per_problem),
        "initial": {
            carrier: {
                "BCR_median": float(handoff["carriers"][carrier]["BCR"]["median"]),
                "positive_count": int(handoff["carriers"][carrier]["BCR"]["positive_count"]),
                "CRR_median": float(handoff["carriers"][carrier]["CRR_median"]),
                "sham_absolute_shift_median": float(handoff["carriers"][carrier]["sham_absolute_shift_median"]),
                "semantic_to_sham_ratio_median": float(handoff["carriers"][carrier]["semantic_to_sham_ratio_median"]),
                "robust_under_frozen_rule": bool(handoff["robustness"][carrier]["robust"]),
            }
            for carrier in ("R_last1", "Q", "h_pre")
        },
        "gated_recent_R": {
            carrier: {
                "BCR_median": float(gated["carriers"][carrier]["BCR"]["median"]),
                "positive_count": int(gated["carriers"][carrier]["BCR"]["positive_count"]),
                "CRR_median": float(gated["carriers"][carrier]["CRR_median"]),
                "sham_absolute_shift_median": float(gated["carriers"][carrier]["sham_absolute_shift_median"]),
                "expands_under_frozen_rule": bool(gated["expansion_cells"][carrier]["expands"]),
            }
            for carrier in ("R_last2", "R_last4")
        },
        "primary_15_test_family": handoff["primary_15_test_family"],
        "carrier_contrasts": handoff["carrier_contrasts"],
        "per_problem": per_problem,
    }
    write_json(OUT / "analysis/carrier_comparison.json", carrier_comparison)
    classification = {
        "phase_a_outcome": necessary["outcome"],
        "phase_b_gate_passed": bool(necessary["phase_b_gate_pass"]),
        "necessary_scope": necessary["selected_scope"],
        "carrier_robustness": handoff["robustness"],
        "recent_R_expansion": gated["expansion_cells"],
        "target_specificity": {
            "T_greater_M_count": controls["T_greater_M_count"],
            "T_greater_I_count": controls["T_greater_I_count"],
            "N": controls["N_unique_bases"],
        },
        "scientific_outcome": "O5 — No Clean Carrier",
        "reason": "P4/P5 establish isolated t_pre necessity, but no base-aggregated R_last1, Q, or h_pre carrier reaches the frozen median CRR>=0.20 criterion; R_last2/R_last4 add only 0.003/0.009 median CRR.",
        "strongest_descriptive_candidate": {
            "carrier": "h_pre",
            "base_aggregated_BCR_median": float(handoff["carriers"]["h_pre"]["BCR"]["median"]),
            "base_aggregated_CRR_median": float(handoff["carriers"]["h_pre"]["CRR_median"]),
            "positive_count": int(handoff["carriers"]["h_pre"]["BCR"]["positive_count"]),
            "target_a_CRR_median": float(handoff["targets"]["h_pre"]["target_a"]["CRR_median"]),
            "target_b_CRR_median": float(handoff["targets"]["h_pre"]["target_b"]["CRR_median"]),
            "does_not_override_frozen_robustness_rule": True,
        },
        "recommendation": "GO — Current-Residual Mechanism",
        "recommendation_is_review_only": True,
        "boundary": "This recommendation prioritizes the strongest target-heterogeneous candidate for a new reviewed design; it is not a claim that Stage 3C.5 cleanly identified h_pre as the carrier.",
        "sink_manipulated": False,
    }
    write_json(OUT / "analysis/handoff_classification.json", classification)
    print(json.dumps(classification, indent=2))


if __name__ == "__main__":
    main()
