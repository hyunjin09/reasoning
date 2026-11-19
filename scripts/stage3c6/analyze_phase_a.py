#!/usr/bin/env python3
"""Aggregate the Stage 3C.6 broad h_pre rescue scan and freeze Phase B."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage3c4.analysis import holm_adjust, signed_summary
from visual_reasoning.stage3c6.protocol import (
    aligned_evidence_score,
    rescue_effect,
    select_candidate_region,
    threshold_crossings,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"
TARGETS = ("target_a", "target_b")
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
    return {
        str(row["base_problem_id"]): row
        for path in sorted(root.glob("shard_*/examples/*/result.json"))
        for row in [read_json(path)]
    }


def broad_outcome(rows: list[dict[str, Any]], crossings: dict[str, int | None]) -> str:
    robust_rows = [row for row in rows if bool(row["robust_positive"])]
    peak = max(robust_rows, key=lambda row: float(row["median_RR"])) if robust_rows else None
    final_rr = float(next(row for row in rows if int(row["layer"]) == 35)["median_RR"])
    if (
        peak is not None
        and float(peak["median_RR"]) >= 0.20
        and final_rr < 0.20
        and final_rr < 0.5 * float(peak["median_RR"])
    ):
        return "R4_transient_rescue_decay"
    first = crossings["first_20"]
    if first is None:
        return "R5_no_substantial_residual_rescue"
    if first <= 11:
        return "R1_early_current_residual_integration"
    if first <= 27:
        return "R2_mid_late_current_residual_integration"
    return "R3_late_only_rescue"


def main() -> None:
    config = read_json(OUT / "config/stage3c6_config.json")
    rows = result_map(OUT / "raw/phase_a")
    expected = [str(value) for value in config["primary_base_problem_ids"]]
    if set(rows) != set(expected):
        raise RuntimeError(f"Phase-A cohort mismatch: observed={sorted(rows)}")
    layers = [int(value) for value in config["hpre_scan_layers"]]
    per_problem: list[dict[str, Any]] = []
    reproduction_rows = []
    for base in expected:
        target_rows: dict[str, Any] = {}
        for target_id in TARGETS:
            target = rows[base]["target_results"][target_id]
            conditions: dict[str, Any] = {}
            for condition in CONDITIONS:
                source = target["conditions"][condition]
                layer_effects = {
                    str(layer): rescue_effect(
                        native_d=float(source["native"]["D"]),
                        suppressed_d=float(source["suppressed"]["D"]),
                        rescued_d=float(source["rescue_by_layer"][str(layer)]["rescue"]["D"]),
                        condition=condition,
                    )
                    for layer in layers
                }
                conditions[condition] = {
                    "D_native_raw": float(source["native"]["D"]),
                    "D_suppressed_raw": float(source["suppressed"]["D"]),
                    "aligned_native": aligned_evidence_score(float(source["native"]["D"]), condition),
                    "aligned_suppressed": aligned_evidence_score(float(source["suppressed"]["D"]), condition),
                    "suppression_loss": next(iter(layer_effects.values()))["suppression_loss"],
                    "layers": layer_effects,
                    "hpre_delta_summaries": source["hpre_delta_summaries"],
                }
                if condition == "O":
                    reproduction_rows.append({
                        "base_problem_id": base, "target_id": target_id,
                        **source["stage3c5_reproduction"],
                    })
            aggregate_layers: dict[str, Any] = {}
            aligned_native = float(np.mean([conditions[c]["aligned_native"] for c in CONDITIONS]))
            aligned_suppressed = float(np.mean([conditions[c]["aligned_suppressed"] for c in CONDITIONS]))
            loss = aligned_native - aligned_suppressed
            if loss == 0.0:
                raise RuntimeError(f"Zero aligned suppression loss for {base}/{target_id}")
            for layer in layers:
                gain = float(np.mean([conditions[c]["layers"][str(layer)]["rescue_gain"] for c in CONDITIONS]))
                aggregate_layers[str(layer)] = {
                    "rescue_gain": gain,
                    "rescue_ratio": gain / loss,
                    "rescue_ratio_is_clipped": False,
                    "residual_delta_l2": float(np.mean([
                        conditions[c]["hpre_delta_summaries"][candidate][layer]["delta_l2"]
                        for c in CONDITIONS for candidate in ("original_candidate", "counterfactual_candidate")
                    ])),
                }
            target_rows[target_id] = {
                "conditions": conditions,
                "sign_aligned": {
                    "native": aligned_native, "suppressed": aligned_suppressed,
                    "suppression_loss": loss, "layers": aggregate_layers,
                },
            }
        per_problem.append({"base_problem_id": base, "targets": target_rows})
    write_jsonl(OUT / "phase_a_hpre_scan/per_problem_layer_rescue.jsonl", per_problem)
    reproduction = {
        "N_target_base_cells": len(reproduction_rows),
        "native_exact_count": sum(bool(row["native_exact"]) for row in reproduction_rows),
        "P4_suppressed_exact_count": sum(bool(row["P4_suppressed_exact"]) for row in reproduction_rows),
        "all_exact": all(bool(row["native_exact"] and row["P4_suppressed_exact"]) for row in reproduction_rows),
        "maximum_absolute_D_delta": max(max(abs(float(row["native_D_delta"])), abs(float(row["P4_D_delta"]))) for row in reproduction_rows),
        "rows": reproduction_rows,
    }
    write_json(OUT / "audit/suppression_reproduction.json", reproduction)

    all_statistics: dict[str, Any] = {}
    crossing_output: dict[str, Any] = {}
    region_output: dict[str, Any] = {
        "frozen_before_within_block_scoring": True,
        "selection_used_boundary_outcomes": False,
        "selection_used_attention": False,
        "targets": {},
    }
    for target_index, target_id in enumerate(TARGETS):
        condition_statistics: dict[str, Any] = {}
        for condition_index, condition in enumerate(CONDITIONS):
            losses = [row["targets"][target_id]["conditions"][condition]["suppression_loss"] for row in per_problem]
            condition_statistics[condition] = {
                "suppression_loss": signed_summary(losses, seed=20260904 + 1000 * target_index + condition_index),
                "layers": {},
            }
            for layer in layers:
                effects = [row["targets"][target_id]["conditions"][condition]["layers"][str(layer)] for row in per_problem]
                gains = [item["rescue_gain"] for item in effects]
                ratios = [item["rescue_ratio"] for item in effects]
                condition_statistics[condition]["layers"][str(layer)] = {
                    "gain": signed_summary(gains, seed=20261904 + layer + 1000 * target_index + 100 * condition_index),
                    "RR_median": float(np.median(ratios)), "RR_mean": float(np.mean(ratios)),
                    "RR_values": ratios,
                }
        aggregate_rows = []
        raw_p = []
        for layer in layers:
            gains = [row["targets"][target_id]["sign_aligned"]["layers"][str(layer)]["rescue_gain"] for row in per_problem]
            ratios = [row["targets"][target_id]["sign_aligned"]["layers"][str(layer)]["rescue_ratio"] for row in per_problem]
            summary = signed_summary(gains, seed=20262904 + layer + 1000 * target_index)
            aggregate_rows.append({
                "layer": layer, "median_gain": float(summary["median"]),
                "mean_gain": float(summary["mean"]), "gain_bootstrap_mean_ci95": summary["bootstrap_mean_ci95"],
                "positive_count": int(summary["positive_count"]), "positive_fraction": float(summary["positive_fraction"]),
                "N": int(summary["N"]), "wilcoxon_one_sided_greater_p": float(summary["wilcoxon_one_sided_greater_p"]),
                "median_RR": float(np.median(ratios)), "mean_RR": float(np.mean(ratios)),
                "RR_values": ratios,
                "median_residual_delta_l2": float(np.median([
                    row["targets"][target_id]["sign_aligned"]["layers"][str(layer)]["residual_delta_l2"] for row in per_problem
                ])),
            })
            raw_p.append(float(summary["wilcoxon_one_sided_greater_p"]))
        for row, adjusted in zip(aggregate_rows, holm_adjust(raw_p)):
            row["holm_adjusted_p"] = adjusted
            row["robust_positive"] = bool(
                adjusted < 0.05 and float(row["gain_bootstrap_mean_ci95"][0]) > 0.0 and int(row["positive_count"]) >= 18
            )
        crossings = threshold_crossings(aggregate_rows)
        gate = crossings["first_20"] is not None
        region = select_candidate_region(aggregate_rows) if gate else None
        crossing_output[target_id] = {
            **crossings, "phase_b_gate": gate, "broad_outcome": broad_outcome(aggregate_rows, crossings),
            "peak_RR_layer": int(max(aggregate_rows, key=lambda row: float(row["median_RR"]))["layer"]),
            "peak_RR": float(max(row["median_RR"] for row in aggregate_rows)),
            "peak_gain_layer": int(max(aggregate_rows, key=lambda row: float(row["median_gain"]))["layer"]),
            "peak_median_gain": float(max(row["median_gain"] for row in aggregate_rows)),
        }
        region_output["targets"][target_id] = {
            "phase_b_gate": gate,
            "candidate_region": region,
            "run_phase_b": bool(gate and region is not None),
            "reason_if_not_run": None if gate and region is not None else ("no robust first_20 crossing" if not gate else "no valid four-layer region"),
        }
        all_statistics[target_id] = {
            "condition_statistics": condition_statistics,
            "sign_aligned_suppression_loss": signed_summary(
                [row["targets"][target_id]["sign_aligned"]["suppression_loss"] for row in per_problem],
                seed=20263904 + target_index,
            ),
            "sign_aligned_layers": aggregate_rows,
        }
        write_json(OUT / f"phase_a_hpre_scan/{target_id}_layer_statistics.json", all_statistics[target_id])
    write_json(OUT / "phase_a_hpre_scan/threshold_crossings.json", crossing_output)
    write_json(OUT / "phase_a_hpre_scan/candidate_region_freeze.json", region_output)
    write_json(OUT / "analysis/suppression_deficit_analysis.json", {
        "primary_unit": "base_problem_id", "N_unique_bases": len(per_problem),
        "stage3c5_P4_reproduction": reproduction,
        "targets": {target: all_statistics[target]["sign_aligned_suppression_loss"] for target in TARGETS},
        "O_and_C_reported_separately": True, "C_sign_aligned_before_aggregation": True,
    })
    write_json(OUT / "analysis/residual_rescue_analysis.json", {
        "primary_unit": "base_problem_id", "N_unique_bases": len(per_problem),
        "targets": crossing_output, "phase_b_freeze": region_output,
        "primary_readout": "unnormalized sign-aligned rescue gain",
        "rescue_ratio_clipped": False,
    })
    print(json.dumps({"reproduction_all_exact": reproduction["all_exact"], "targets": crossing_output, "regions": region_output["targets"]}, indent=2))


if __name__ == "__main__":
    main()
