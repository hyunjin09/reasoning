#!/usr/bin/env python3
"""Aggregate Stage 3C.6 residual-delta dose and M/I rescue controls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage3c4.analysis import holm_adjust, signed_summary
from visual_reasoning.stage3c6.protocol import aligned_evidence_score, rescue_effect


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"
CONDITIONS = ("O", "C")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def result_map(root: Path) -> dict[str, dict[str, Any]]:
    return {str(row["base_problem_id"]): row for path in sorted(root.glob("shard_*/examples/*/result.json")) for row in [read_json(path)]}


def aggregate_condition_effects(values: dict[str, dict[str, Any]]) -> dict[str, float]:
    aligned_native = float(np.mean([aligned_evidence_score(float(values[c]["native"]["D"]), c) for c in CONDITIONS]))
    aligned_suppressed = float(np.mean([aligned_evidence_score(float(values[c]["suppressed"]["D"]), c) for c in CONDITIONS]))
    aligned_rescued = float(np.mean([aligned_evidence_score(float(values[c]["rescue"]["D"]), c) for c in CONDITIONS]))
    loss = aligned_native - aligned_suppressed
    return {
        "aligned_native": aligned_native, "aligned_suppressed": aligned_suppressed,
        "aligned_rescued": aligned_rescued, "suppression_loss": loss,
        "rescue_gain": aligned_rescued - aligned_suppressed,
        "rescue_ratio": (aligned_rescued - aligned_suppressed) / loss,
    }


def analyze_dose(config: dict[str, Any], active_targets: list[str]) -> None:
    rows = result_map(OUT / "raw/phase_c_dose")
    expected = set(config["primary_base_problem_ids"])
    if set(rows) != expected:
        raise RuntimeError("Dose cohort mismatch")
    lambdas = [float(value) for value in read_json(OUT / "config/primary_family.json")["dose_lambdas"]]
    per_problem = []
    for base in config["primary_base_problem_ids"]:
        targets = {}
        for target in active_targets:
            conditions = rows[base]["target_results"][target]["conditions"]
            by_lambda = {}
            for gain in lambdas:
                effects = {
                    condition: rescue_effect(
                        native_d=float(conditions[condition]["native"]["D"]),
                        suppressed_d=float(conditions[condition]["suppressed"]["D"]),
                        rescued_d=float(conditions[condition]["dose"][str(gain)]["D"]),
                        condition=condition,
                    )
                    for condition in CONDITIONS
                }
                aligned_gain = float(np.mean([effects[c]["rescue_gain"] for c in CONDITIONS]))
                aligned_loss = float(np.mean([effects[c]["suppression_loss"] for c in CONDITIONS]))
                by_lambda[str(gain)] = {"conditions": effects, "rescue_gain": aligned_gain, "rescue_ratio": aligned_gain / aligned_loss}
            targets[target] = {"layer": conditions["O"]["layer"], "boundary": conditions["O"]["boundary"], "dose": by_lambda}
        per_problem.append({"base_problem_id": base, "targets": targets})
    write_jsonl(OUT / "phase_c_optional_dose/residual_delta_dose_results.jsonl", per_problem)
    statistics: dict[str, Any] = {"primary_unit": "base_problem_id", "N_unique_bases": len(per_problem), "targets": {}}
    for target_index, target in enumerate(active_targets):
        curve = []
        for index, gain in enumerate(lambdas):
            values = [row["targets"][target]["dose"][str(gain)]["rescue_gain"] for row in per_problem]
            ratios = [row["targets"][target]["dose"][str(gain)]["rescue_ratio"] for row in per_problem]
            curve.append({"lambda": gain, "gain": signed_summary(values, seed=20266904 + 100 * target_index + index), "median_RR": float(np.median(ratios)), "mean_RR": float(np.mean(ratios))})
        slopes = [
            float(np.polyfit(np.asarray(lambdas), np.asarray([row["targets"][target]["dose"][str(g)]["rescue_gain"] for g in lambdas]), 1)[0])
            for row in per_problem
        ]
        statistics["targets"][target] = {
            "curve": curve, "linear_slope": signed_summary(slopes, seed=20267904 + target_index),
            "lambda_zero_exact_suppressed": all(abs(row["targets"][target]["dose"]["0.0"]["rescue_gain"]) == 0.0 for row in per_problem),
            "ratios_unclipped": True,
        }
    write_json(OUT / "phase_c_optional_dose/dose_statistics.json", statistics)


def analyze_controls(config: dict[str, Any], active_targets: list[str]) -> None:
    rows = result_map(OUT / "raw/controls")
    expected = set(config["primary_base_problem_ids"])
    if set(rows) != expected:
        raise RuntimeError("Control cohort mismatch")
    boundary_rows = [json.loads(line) for line in (OUT / "phase_b_boundary/per_problem_boundary_rescue.jsonl").read_text().splitlines() if line.strip()]
    boundary_by_base = {str(row["base_problem_id"]): row for row in boundary_rows}
    per_problem = []
    for base in config["primary_base_problem_ids"]:
        targets = {}
        for target in active_targets:
            source_values = {}
            for source in ("M", "I"):
                condition_values = {
                    condition: rows[base]["target_results"][target]["conditions"][condition]["controls"][source]
                    for condition in CONDITIONS
                }
                source_values[source] = aggregate_condition_effects(condition_values)
            freeze = read_json(OUT / "phase_b_boundary/control_boundary_freeze.json")["targets"][target]
            key = f"L{freeze['layer']}_{freeze['boundary']}"
            target_value = boundary_by_base[base]["targets"][target]["sign_aligned"][key]
            source_values["T"] = {
                "suppression_loss": boundary_by_base[base]["targets"][target]["sign_aligned_suppression_loss"],
                "rescue_gain": target_value["rescue_gain"], "rescue_ratio": target_value["rescue_ratio"],
            }
            targets[target] = {"layer": freeze["layer"], "boundary": freeze["boundary"], "sources": source_values}
        per_problem.append({"base_problem_id": base, "targets": targets})
    write_jsonl(OUT / "controls/mention_deficit_rescue.jsonl", [
        {"base_problem_id": row["base_problem_id"], "targets": {target: value["sources"]["M"] for target, value in row["targets"].items()}}
        for row in per_problem
    ])
    write_jsonl(OUT / "controls/irrelevant_deficit_rescue.jsonl", [
        {"base_problem_id": row["base_problem_id"], "targets": {target: value["sources"]["I"] for target, value in row["targets"].items()}}
        for row in per_problem
    ])
    write_jsonl(OUT / "controls/optional_sham_rescue.jsonl", [])
    statistics: dict[str, Any] = {"primary_unit": "base_problem_id", "N_unique_bases": len(per_problem), "optional_sham_run": False, "targets": {}}
    for target_index, target in enumerate(active_targets):
        source_stats = {}
        for source_index, source in enumerate(("T", "M", "I")):
            source_stats[source] = {
                "suppression_loss": signed_summary([row["targets"][target]["sources"][source]["suppression_loss"] for row in per_problem], seed=20268904 + 100 * target_index + 10 * source_index),
                "rescue_gain": signed_summary([row["targets"][target]["sources"][source]["rescue_gain"] for row in per_problem], seed=20268905 + 100 * target_index + 10 * source_index),
                "median_RR": float(np.median([row["targets"][target]["sources"][source]["rescue_ratio"] for row in per_problem])),
            }
        contrasts = []
        for control in ("M", "I"):
            values = [row["targets"][target]["sources"]["T"]["rescue_gain"] - row["targets"][target]["sources"][control]["rescue_gain"] for row in per_problem]
            contrasts.append({"contrast": f"T_vs_{control}", "values": values, **signed_summary(values, seed=20269904 + target_index * 10 + (control == "I"))})
        for row, adjusted in zip(contrasts, holm_adjust([float(row["wilcoxon_one_sided_greater_p"]) for row in contrasts])):
            row["holm_adjusted_p"] = adjusted
        statistics["targets"][target] = {"sources": source_stats, "contrasts": contrasts}
    write_json(OUT / "controls/control_statistics.json", statistics)


def main() -> None:
    config = read_json(OUT / "config/stage3c6_config.json")
    freeze = read_json(OUT / "phase_a_hpre_scan/candidate_region_freeze.json")
    targets = [target for target, row in freeze["targets"].items() if row["run_phase_b"]]
    analyze_dose(config, targets)
    analyze_controls(config, targets)
    print(json.dumps({"dose": "complete", "controls": "complete", "targets": targets}, indent=2))


if __name__ == "__main__":
    main()
