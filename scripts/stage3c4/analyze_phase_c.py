#!/usr/bin/env python3
"""Aggregate Stage 3C.4 interactions, controls, family, and outcome."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage3c4.analysis import holm_adjust, retention_summary, signed_summary
from visual_reasoning.stage3c4.protocol import classify_spatiotemporal_outcome


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c4"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def result_map(root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["base_problem_id"]): row
        for path in sorted(root.glob("shard_*/examples/*/result.json"))
        for row in [read_json(path)]
    }


def correlation(x: list[float], y: list[float]) -> dict[str, Any]:
    result = spearmanr(np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64))
    return {"N": len(x), "spearman_rho": float(result.statistic), "two_sided_p": float(result.pvalue)}


def main() -> None:
    config = read_json(OUT / "config/stage3c4_config.json")
    decision_rule = read_json(OUT / "config/decision_rule.json")
    rows = result_map(OUT / "raw/phase_c")
    expected = config["primary_base_problem_ids"]
    if set(rows) != set(expected):
        raise RuntimeError(f"Phase C cohort mismatch: observed={sorted(rows)}")
    phase_a = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "phase_a_layer/per_problem_layer_scope_results.jsonl")}
    phase_b = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "phase_b_time/per_problem_temporal_results.jsonl")}
    cells = list(read_json(OUT / "config/interaction_cells.json")["cells"])

    per_problem = []
    mention_rows = []
    irrelevant_rows = []
    for base in expected:
        raw = rows[base]
        targets = {}
        for target_id in ("target_a", "target_b"):
            target = raw["target_results"][target_id]
            native = float(target["native"]["D"])
            cell_d = {label: float(target["arms"][label]["score"]["D"]) for label in cells}
            targets[target_id] = {
                "D_native": native,
                "D_by_cell": cell_d,
                "loss_by_cell": {label: native - value for label, value in cell_d.items()},
                "retention_by_cell": {label: value / native for label, value in cell_d.items()},
            }
        aggregated_d = {
            label: float(np.mean([targets[target]["D_by_cell"][label] for target in targets]))
            for label in cells
        }
        aggregated_retention = {
            label: float(np.mean([targets[target]["retention_by_cell"][label] for target in targets]))
            for label in cells
        }
        per_problem.append({
            "base_problem_id": base,
            "targets": targets,
            "base_aggregated_D_native": float(np.mean([targets[target]["D_native"] for target in targets])),
            "base_aggregated_D_by_cell": aggregated_d,
            "base_aggregated_retention_by_cell": aggregated_retention,
        })
        for source, destination in (("M", mention_rows), ("I", irrelevant_rows)):
            target_rows = {}
            for target_id in ("target_a", "target_b"):
                native = float(raw["target_results"][target_id]["native"]["D"])
                target_rows[target_id] = {}
                for window in ("T0", "T4"):
                    target_d = float(phase_b[base]["targets"][target_id]["D_by_window"][window])
                    control_d = float(raw["target_results"][target_id]["arms"][f"{source}_{window}"]["score"]["D"])
                    target_rows[target_id][window] = {
                        "D_native": native,
                        "D_target_suppressed": target_d,
                        "D_control_suppressed": control_d,
                        "target_loss": native - target_d,
                        "control_loss": native - control_d,
                        "target_minus_control_loss": control_d - target_d,
                    }
            destination.append({"base_problem_id": base, "source_control": source, "targets": target_rows})
    write_jsonl(OUT / "phase_c_interaction/interaction_results.jsonl", per_problem)
    write_jsonl(OUT / "controls/mention_suppression_results.jsonl", mention_rows)
    write_jsonl(OUT / "controls/irrelevant_suppression_results.jsonl", irrelevant_rows)

    interaction_stats: dict[str, Any] = {
        "primary_unit": "base_problem_id", "N_unique_bases": len(per_problem), "targets": {}
    }
    for target_id in ("target_a", "target_b"):
        native = [row["targets"][target_id]["D_native"] for row in per_problem]
        interaction_stats["targets"][target_id] = {
            label: retention_summary(
                native,
                [row["targets"][target_id]["D_by_cell"][label] for row in per_problem],
                seed=int(config["seed"]) + index,
            )
            for index, label in enumerate(cells)
        }
    base_native = [row["base_aggregated_D_native"] for row in per_problem]
    interaction_stats["base_aggregated"] = {
        label: retention_summary(
            base_native,
            [row["base_aggregated_D_by_cell"][label] for row in per_problem],
            seed=int(config["seed"]) + 100 + index,
        )
        for index, label in enumerate(cells)
    }
    interaction_values = [
        float(np.mean([
            row["base_aggregated_D_by_cell"]["C1"] - row["base_aggregated_D_by_cell"]["C3"],
            row["base_aggregated_D_by_cell"]["C2"] - row["base_aggregated_D_by_cell"]["C4"],
        ]))
        for row in per_problem
    ]
    interaction_stats["frozen_layer_by_time_interaction"] = signed_summary(
        interaction_values, seed=int(config["seed"]) + 299
    )
    phase_b_raw = result_map(OUT / "raw/phase_b")
    interaction_stats["cross_phase_reproduction"] = {
        "C3_equals_phase_b_T4": all(
            float(rows[base]["target_results"][target]["arms"]["C3"]["score"]["D"])
            == float(phase_b_raw[base]["target_results"][target]["arms"]["T4"]["score"]["D"])
            for base in expected for target in ("target_a", "target_b")
        ),
        "C4_equals_phase_b_T8": all(
            float(rows[base]["target_results"][target]["arms"]["C4"]["score"]["D"])
            == float(phase_b_raw[base]["target_results"][target]["arms"]["T8"]["score"]["D"])
            for base in expected for target in ("target_a", "target_b")
        ),
    }
    write_json(OUT / "phase_c_interaction/interaction_statistics.json", interaction_stats)

    control_summaries = {}
    for source, control_rows in (("M", mention_rows), ("I", irrelevant_rows)):
        per_base_values = [
            float(np.mean([
                row["targets"][target][window]["target_minus_control_loss"]
                for target in ("target_a", "target_b") for window in ("T0", "T4")
            ]))
            for row in control_rows
        ]
        control_summaries[source] = {
            "aggregation": "one value per base: mean target-minus-control suppression loss over two targets and T0/T4",
            "per_base": dict(zip(expected, per_base_values)),
            "summary": signed_summary(per_base_values, seed=int(config["seed"]) + (400 if source == "M" else 401)),
        }

    phase_a_stats = read_json(OUT / "phase_a_layer/layer_scope_statistics.json")
    phase_b_stats = read_json(OUT / "phase_b_time/temporal_statistics.json")
    ordered = [
        ("L1_vs_L0", phase_a_stats["frozen_contrasts_unadjusted"]["L1_vs_L0"]),
        ("L2_vs_L0", phase_a_stats["frozen_contrasts_unadjusted"]["L2_vs_L0"]),
        ("L3_vs_L0", phase_a_stats["frozen_contrasts_unadjusted"]["L3_vs_L0"]),
        ("L4_vs_L0", phase_a_stats["frozen_contrasts_unadjusted"]["L4_vs_L0"]),
        ("monotonic_layer_scope_trend", phase_a_stats["frozen_contrasts_unadjusted"]["monotonic_layer_scope_trend"]),
        ("T1_vs_T0", phase_b_stats["frozen_contrasts_unadjusted"]["T1_vs_T0"]),
        ("T2_vs_T0", phase_b_stats["frozen_contrasts_unadjusted"]["T2_vs_T0"]),
        ("T4_vs_T0", phase_b_stats["frozen_contrasts_unadjusted"]["T4_vs_T0"]),
        ("T8_vs_T0", phase_b_stats["frozen_contrasts_unadjusted"]["T8_vs_T0"]),
        ("T16_vs_T0", phase_b_stats["frozen_contrasts_unadjusted"]["T16_vs_T0"]),
        ("monotonic_temporal_window_trend", phase_b_stats["frozen_contrasts_unadjusted"]["monotonic_temporal_window_trend"]),
        ("T_vs_M_suppression", control_summaries["M"]["summary"]),
        ("T_vs_I_suppression", control_summaries["I"]["summary"]),
        ("frozen_layer_by_time_interaction", interaction_stats["frozen_layer_by_time_interaction"]),
    ]
    adjusted = holm_adjust([item[1]["wilcoxon_one_sided_greater_p"] for item in ordered])
    family_rows = []
    for (name, summary), adjusted_p in zip(ordered, adjusted):
        family_rows.append({
            "test": name,
            "median": summary["median"],
            "mean": summary["mean"],
            "positive_count": summary["positive_count"],
            "N": summary["N"],
            "raw_p": summary["wilcoxon_one_sided_greater_p"],
            "holm_adjusted_p": adjusted_p,
            "holm_significant_0_05": adjusted_p < 0.05,
        })
    family = {
        "primary_unit": "base_problem_id",
        "test_count": len(family_rows),
        "multiplicity": "Holm across exact frozen family",
        "rows": family_rows,
        "significant_count": sum(row["holm_significant_0_05"] for row in family_rows),
    }
    write_json(OUT / "analysis/primary_family_statistics.json", family)
    family_by_name = {row["test"]: row for row in family_rows}
    control_gate = all(
        family_by_name[name]["median"] > 0 and family_by_name[name]["holm_significant_0_05"]
        for name in ("T_vs_M_suppression", "T_vs_I_suppression")
    )
    target_specificity = {
        "N_unique_bases": len(expected),
        "controls": control_summaries,
        "holm_rows": {
            name: family_by_name[name] for name in ("T_vs_M_suppression", "T_vs_I_suppression")
        },
        "prospective_gate": decision_rule["control_gate"],
        "gate_passed": control_gate,
    }
    write_json(OUT / "analysis/target_specificity_analysis.json", target_specificity)

    layer_analysis = read_json(OUT / "analysis/layer_redundancy_analysis.json")
    temporal_analysis = read_json(OUT / "analysis/temporal_redundancy_analysis.json")
    threshold = float(decision_rule["substantial_retention_threshold"])
    values = {
        "layer_l4_retention": float(layer_analysis["median_retention"]["base_aggregated"]["L4"]),
        "time_t16_retention": float(temporal_analysis["median_retention_curves"]["base_aggregated"]["T16"]),
        "c_late4_retention": float(interaction_stats["base_aggregated"]["C1"]["retained_median"]),
        "c_all4_retention": float(interaction_stats["base_aggregated"]["C3"]["retained_median"]),
    }
    outcome = classify_spatiotemporal_outcome(**values, substantial_retention=threshold)
    validation_pass = read_json(OUT / "validation/validation_summary.json")["status"] == "PASS"
    if not validation_pass or not control_gate:
        recommendation = decision_rule["recommendation_rule"]["mechanical_or_control_failure"]
    elif outcome == "O4_earlier_nonvisual_storage":
        recommendation = decision_rule["recommendation_rule"]["O4_earlier_nonvisual_storage"]
    else:
        recommendation = decision_rule["recommendation_rule"]["O1_O2_O3"]
    classification = {
        "classification": outcome,
        "joint_values": values,
        "threshold": threshold,
        "rule": decision_rule["outcome_rule"],
        "target_specificity_gate_passed": control_gate,
        "mechanical_validation_passed": validation_pass,
        "recommendation": recommendation,
        "sink_causality_inferred": False,
        "carrier_identified": False,
    }
    write_json(OUT / "analysis/spatiotemporal_classification.json", classification)

    stage3b2 = read_json(ROOT / "outputs/stage3b2/analysis/bidirectional_retrieval_statistics.json")
    switch_lookup = {
        "target_a": {str(row["base_problem_id"]): row for row in stage3b2["late_checkpoints"]["Ed"]["per_base"]},
        "target_b": {str(row["base_problem_id"]): row for row in stage3b2["late_checkpoints"]["Ed_minus_1"]["per_base"]},
    }
    comparison_rows = []
    for base in expected:
        for target_id in ("target_a", "target_b"):
            comparison_rows.append({
                "base_problem_id": base,
                "target_id": target_id,
                "stage3b2_BRI": float(switch_lookup[target_id][base]["BRI"]),
                "stage3b2_normalized_BRI": float(switch_lookup[target_id][base]["normalized_BRI_raw"]),
                "stage3c4_T0_loss": float(phase_b[base]["targets"][target_id]["loss_by_window"]["T0"]),
                "stage3c4_T16_loss": float(phase_b[base]["targets"][target_id]["loss_by_window"]["T16"]),
            })
    comparison = {
        "N_unique_bases": len(expected),
        "N_target_base_events": len(comparison_rows),
        "distinction": {
            "stage3b2": "replace future all-visual K/V semantic identity",
            "stage3c4": "remove only target-ROI Value contribution",
        },
        "median_stage3b2_BRI": float(np.median([row["stage3b2_BRI"] for row in comparison_rows])),
        "median_stage3c4_T0_loss": float(np.median([row["stage3c4_T0_loss"] for row in comparison_rows])),
        "median_stage3c4_T16_loss": float(np.median([row["stage3c4_T16_loss"] for row in comparison_rows])),
        "correlations": {
            "BRI_vs_T0_loss": correlation(
                [row["stage3b2_BRI"] for row in comparison_rows],
                [row["stage3c4_T0_loss"] for row in comparison_rows],
            ),
            "BRI_vs_T16_loss": correlation(
                [row["stage3b2_BRI"] for row in comparison_rows],
                [row["stage3c4_T16_loss"] for row in comparison_rows],
            ),
        },
        "per_target_base": comparison_rows,
        "causal_objects_are_not_equivalent": True,
    }
    write_json(OUT / "secondary/stage3b2_comparison.json", comparison)
    write_jsonl(OUT / "secondary/optional_state_readout.jsonl", [])
    print(json.dumps({
        "N": len(expected),
        "interaction_median_retention": {
            label: interaction_stats["base_aggregated"][label]["retained_median"] for label in cells
        },
        "control_gate": control_gate,
        "significant_primary_tests": family["significant_count"],
        "classification": classification,
    }, indent=2))


if __name__ == "__main__":
    main()
