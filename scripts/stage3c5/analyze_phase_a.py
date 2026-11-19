#!/usr/bin/env python3
"""Aggregate Stage 3C.5 t_pre layer localization and evaluate the Phase-B gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage3c4.analysis import holm_adjust, retention_summary, signed_summary
from visual_reasoning.stage3c5.protocol import evaluate_phase_b_gate, select_necessary_scope


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c5"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def main() -> None:
    config = read_json(OUT / "config/stage3c5_config.json")
    scopes = list(read_json(OUT / "config/tpre_layer_scopes.json")["scopes"])
    rows = result_map(OUT / "raw/phase_a")
    expected = config["primary_base_problem_ids"]
    if set(rows) != set(expected):
        raise RuntimeError(f"Phase-A cohort mismatch: {sorted(rows)}")
    prior_layer = result_map(ROOT / "outputs/stage3c4/raw/phase_a")
    prior_time = result_map(ROOT / "outputs/stage3c4/raw/phase_b")
    per_problem = []
    reproductions = []
    for base in expected:
        targets = {}
        for target_id in ("target_a", "target_b"):
            target = rows[base]["target_results"][target_id]
            native = float(target["native_A0"]["D"])
            values = {label: float(target["arms"][label]["D"]) for label in scopes}
            a1 = float(target["arms"]["A1_current"]["D"])
            a3 = float(target["arms"]["A3_joint"]["D"])
            prior_native = float(prior_layer[base]["target_results"][target_id]["native"]["D"])
            prior_a1 = float(prior_layer[base]["target_results"][target_id]["arms"]["L4"]["score"]["D"])
            prior_a3 = float(prior_time[base]["target_results"][target_id]["arms"]["T1"]["score"]["D"])
            reproductions.append({
                "base_problem_id": base, "target_id": target_id,
                "native_exact": native == prior_native,
                "A1_current_exact": a1 == prior_a1,
                "A3_joint_exact": a3 == prior_a3,
                "native_abs_delta": abs(native - prior_native),
                "A1_abs_delta": abs(a1 - prior_a1),
                "A3_abs_delta": abs(a3 - prior_a3),
            })
            targets[target_id] = {
                "t_star_generated_index": int(target["t_star_generated_index"]),
                "t_pre_generated_index": int(target["t_pre_generated_index"]),
                "D_native": native,
                "D_by_scope": values,
                "loss_by_scope": {label: native - value for label, value in values.items()},
                "retention_by_scope": {label: value / native for label, value in values.items()},
                "D_current_only": a1,
                "D_tpre_only": values["P5"],
                "D_joint": a3,
                "loss_current_only": native - a1,
                "loss_tpre_only": native - values["P5"],
                "loss_joint": native - a3,
            }
        base_native = float(np.mean([targets[target]["D_native"] for target in targets]))
        base_scopes = {
            label: float(np.mean([targets[target]["D_by_scope"][label] for target in targets]))
            for label in scopes
        }
        per_problem.append({
            "base_problem_id": base,
            "targets": targets,
            "base_aggregated_D_native": base_native,
            "base_aggregated_D_by_scope": base_scopes,
            "base_aggregated_loss_by_scope": {label: base_native - value for label, value in base_scopes.items()},
            "base_aggregated_retention_by_scope": {label: value / base_native for label, value in base_scopes.items()},
            "base_aggregated_D_current_only": float(np.mean([targets[target]["D_current_only"] for target in targets])),
            "base_aggregated_D_tpre_only": base_scopes["P5"],
            "base_aggregated_D_joint": float(np.mean([targets[target]["D_joint"] for target in targets])),
        })
    write_jsonl(OUT / "phase_a_tpre_layer/per_problem_tpre_scope_results.jsonl", per_problem)

    native_values = [row["base_aggregated_D_native"] for row in per_problem]
    stats: dict[str, Any] = {"primary_unit": "base_problem_id", "N_unique_bases": len(per_problem), "scopes": scopes, "targets": {}}
    for target_id in ("target_a", "target_b"):
        native = [row["targets"][target_id]["D_native"] for row in per_problem]
        stats["targets"][target_id] = {
            label: retention_summary(native, [row["targets"][target_id]["D_by_scope"][label] for row in per_problem], seed=int(config["seed"]) + i)
            for i, label in enumerate(scopes)
        }
    stats["base_aggregated"] = {
        label: retention_summary(native_values, [row["base_aggregated_D_by_scope"][label] for row in per_problem], seed=int(config["seed"]) + 100 + i)
        for i, label in enumerate(scopes)
    }
    baseline_names = {"A1_current": "base_aggregated_D_current_only", "A2_tpre": "base_aggregated_D_tpre_only", "A3_joint": "base_aggregated_D_joint"}
    stats["baselines"] = {
        label: retention_summary(native_values, [row[key] for row in per_problem], seed=int(config["seed"]) + 150 + i)
        for i, (label, key) in enumerate(baseline_names.items())
    }
    test_values: dict[str, list[float]] = {
        f"{label}_vs_native": [row["base_aggregated_D_native"] - row["base_aggregated_D_by_scope"][label] for row in per_problem]
        for label in scopes
    }
    test_values["tpre_only_vs_current_only"] = [
        row["base_aggregated_D_current_only"] - row["base_aggregated_D_tpre_only"] for row in per_problem
    ]
    test_values["joint_vs_current_only"] = [
        row["base_aggregated_D_current_only"] - row["base_aggregated_D_joint"] for row in per_problem
    ]
    x = np.arange(len(scopes), dtype=np.float64)
    test_values["monotonic_layer_scope_trend"] = [
        float(-np.polyfit(x, np.asarray([row["base_aggregated_D_by_scope"][label] for label in scopes]), 1)[0])
        for row in per_problem
    ]
    tests = []
    for index, (name, values) in enumerate(test_values.items()):
        summary = signed_summary(values, seed=int(config["seed"]) + 300 + index)
        tests.append({"test": name, "values": values, **summary})
    adjusted = holm_adjust([row["wilcoxon_one_sided_greater_p"] for row in tests])
    for row, value in zip(tests, adjusted):
        row["phase_a_9_test_holm_adjusted_p"] = value
        row["prospective_15_test_bonferroni_upper_bound"] = min(1.0, 15.0 * float(row["wilcoxon_one_sided_greater_p"]))
    stats["phase_a_tests"] = tests
    write_json(OUT / "phase_a_tpre_layer/tpre_layer_statistics.json", stats)

    by_name = {row["test"]: row for row in tests}
    selection_rows = {
        label: {
            "median_loss": float(stats["base_aggregated"][label]["loss_summary"]["median"]),
            "positive_count": int(stats["base_aggregated"][label]["loss_summary"]["positive_count"]),
            "adjusted_p": float(by_name[f"{label}_vs_native"]["prospective_15_test_bonferroni_upper_bound"]),
        }
        for label in scopes
    }
    selection = select_necessary_scope(selection_rows, n=len(per_problem), fraction_of_p5=0.80)
    p5 = selection_rows["P5"]
    gate = evaluate_phase_b_gate(
        median_loss=p5["median_loss"], positive_count=p5["positive_count"], adjusted_p=p5["adjusted_p"],
        n=len(per_problem), historical_increment=1.3069, minimum_historical_fraction=0.20,
    )
    gate["multiplicity_for_gate"] = "Bonferroni upper bound over all 15 prospectively frozen tests; this guarantees final Holm significance if passed"
    gate["selected_layer_scope"] = selection
    write_json(OUT / "analysis/phase_b_gate.json", gate)
    write_json(OUT / "phase_a_tpre_layer/baseline_reproduction.json", {
        "N": len(reproductions),
        "native_exact_count": sum(row["native_exact"] for row in reproductions),
        "A1_current_exact_count": sum(row["A1_current_exact"] for row in reproductions),
        "A3_joint_exact_count": sum(row["A3_joint_exact"] for row in reproductions),
        "all_exact": all(row["native_exact"] and row["A1_current_exact"] and row["A3_joint_exact"] for row in reproductions),
        "maximum_absolute_delta": max(max(row["native_abs_delta"], row["A1_abs_delta"], row["A3_abs_delta"]) for row in reproductions),
        "rows": reproductions,
    })
    selected = selection["scope_id"]
    if not gate["pass"]:
        outcome = "A5_no_localized_tpre_layer"
    elif selected == "P0":
        outcome = "A1_W4_local_tpre_retrieval"
    elif selected == "P1":
        outcome = "A2_W5_local_tpre_retrieval"
    elif selected in {"P2", "P3"}:
        outcome = "A3_late_distributed_tpre_retrieval"
    else:
        outcome = "A4_broad_depth_tpre_retrieval"
    write_json(OUT / "analysis/necessary_window_analysis.json", {
        "outcome": outcome,
        "phase_b_gate_pass": gate["pass"],
        "selected_scope": selection,
        "median_loss": {label: selection_rows[label]["median_loss"] for label in scopes},
        "median_retention": {label: stats["base_aggregated"][label]["retained_median"] for label in scopes},
        "baseline_median_retention": {label: stats["baselines"][label]["retained_median"] for label in baseline_names},
        "attention_used_as_primary_measure": False,
    })
    print(json.dumps({
        "N": len(per_problem), "baseline_all_exact": all(row["native_exact"] and row["A1_current_exact"] and row["A3_joint_exact"] for row in reproductions),
        "median_loss": {label: selection_rows[label]["median_loss"] for label in scopes},
        "median_retention": {label: stats["base_aggregated"][label]["retained_median"] for label in scopes},
        "gate": gate, "outcome": outcome,
    }, indent=2))


if __name__ == "__main__":
    main()
