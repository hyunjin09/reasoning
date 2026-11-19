#!/usr/bin/env python3
"""Aggregate gated within-block rescue and freeze dose/control boundaries."""

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
BOUNDARIES = ("h_pre", "h_post_attn", "h_post_block")


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


def main() -> None:
    config = read_json(OUT / "config/stage3c6_config.json")
    freeze = read_json(OUT / "phase_a_hpre_scan/candidate_region_freeze.json")
    rows = result_map(OUT / "raw/phase_b_boundary")
    expected = set(config["primary_base_problem_ids"])
    if set(rows) != expected:
        raise RuntimeError(f"Boundary cohort mismatch: {sorted(rows)}")
    active = {target: value["candidate_region"]["layers"] for target, value in freeze["targets"].items() if value["run_phase_b"]}
    per_problem = []
    for base in config["primary_base_problem_ids"]:
        targets: dict[str, Any] = {}
        for target_id, region in active.items():
            condition_rows: dict[str, Any] = {}
            for condition in CONDITIONS:
                source = rows[base]["target_results"][target_id]["conditions"][condition]
                effects = {
                    key: rescue_effect(
                        native_d=float(source["native"]["D"]), suppressed_d=float(source["suppressed"]["D"]),
                        rescued_d=float(value["rescue"]["D"]), condition=condition,
                    )
                    for key, value in source["scans"].items()
                }
                condition_rows[condition] = {
                    "D_native_raw": float(source["native"]["D"]), "D_suppressed_raw": float(source["suppressed"]["D"]),
                    "aligned_native": aligned_evidence_score(float(source["native"]["D"]), condition),
                    "aligned_suppressed": aligned_evidence_score(float(source["suppressed"]["D"]), condition),
                    "effects": effects,
                }
            aligned_native = float(np.mean([condition_rows[c]["aligned_native"] for c in CONDITIONS]))
            aligned_suppressed = float(np.mean([condition_rows[c]["aligned_suppressed"] for c in CONDITIONS]))
            loss = aligned_native - aligned_suppressed
            aggregate = {}
            for layer in region:
                for boundary in BOUNDARIES:
                    key = f"L{layer}_{boundary}"
                    gain = float(np.mean([condition_rows[c]["effects"][key]["rescue_gain"] for c in CONDITIONS]))
                    aggregate[key] = {"layer": layer, "boundary": boundary, "rescue_gain": gain, "rescue_ratio": gain / loss}
            targets[target_id] = {"conditions": condition_rows, "sign_aligned_suppression_loss": loss, "sign_aligned": aggregate}
        per_problem.append({"base_problem_id": base, "targets": targets})
    write_jsonl(OUT / "phase_b_boundary/per_problem_boundary_rescue.jsonl", per_problem)

    boundary_statistics: dict[str, Any] = {"primary_unit": "base_problem_id", "N_unique_bases": len(per_problem), "targets": {}}
    attention_output: dict[str, Any] = {}
    mlp_output: dict[str, Any] = {}
    strongest: dict[str, Any] = {}
    for target_index, (target_id, region) in enumerate(active.items()):
        rescue_rows = []
        for layer in region:
            for boundary in BOUNDARIES:
                key = f"L{layer}_{boundary}"
                gains = [row["targets"][target_id]["sign_aligned"][key]["rescue_gain"] for row in per_problem]
                ratios = [row["targets"][target_id]["sign_aligned"][key]["rescue_ratio"] for row in per_problem]
                summary = signed_summary(gains, seed=20264904 + target_index * 100 + layer * 3 + BOUNDARIES.index(boundary))
                rescue_rows.append({
                    "key": key, "layer": layer, "boundary": boundary, "gain": summary,
                    "median_gain": float(summary["median"]), "median_RR": float(np.median(ratios)),
                    "mean_RR": float(np.mean(ratios)), "RR_values": ratios,
                })
        for row, adjusted in zip(rescue_rows, holm_adjust([float(row["gain"]["wilcoxon_one_sided_greater_p"]) for row in rescue_rows])):
            row["holm_adjusted_p"] = adjusted
            row["robust_positive"] = bool(adjusted < 0.05 and float(row["gain"]["bootstrap_mean_ci95"][0]) > 0 and int(row["gain"]["positive_count"]) >= 18)
        transition_rows = []
        for layer in region:
            for name, upper, lower in (("Attention", "h_post_attn", "h_pre"), ("MLP", "h_post_block", "h_post_attn")):
                upper_key, lower_key = f"L{layer}_{upper}", f"L{layer}_{lower}"
                values = [
                    row["targets"][target_id]["sign_aligned"][upper_key]["rescue_gain"]
                    - row["targets"][target_id]["sign_aligned"][lower_key]["rescue_gain"]
                    for row in per_problem
                ]
                summary = signed_summary(values, seed=20265904 + target_index * 100 + layer * 2 + (name == "MLP"))
                transition_rows.append({"layer": layer, "transition": name, "values": values, **summary})
        for row, adjusted in zip(transition_rows, holm_adjust([float(row["wilcoxon_one_sided_greater_p"]) for row in transition_rows])):
            row["holm_adjusted_p"] = adjusted
            row["robust_positive"] = bool(adjusted < 0.05 and float(row["bootstrap_mean_ci95"][0]) > 0 and int(row["positive_count"]) >= 18)
        robust_rescues = [row for row in rescue_rows if row["robust_positive"]]
        if not robust_rescues:
            raise RuntimeError(f"Gated target {target_id} has no confirmed boundary rescue")
        best = max(robust_rescues, key=lambda row: (float(row["median_gain"]), -int(row["layer"])))
        strongest[target_id] = {
            "layer": int(best["layer"]), "boundary": str(best["boundary"]),
            "robust_positive": bool(best["robust_positive"]), "median_gain": float(best["median_gain"]), "median_RR": float(best["median_RR"]),
        }
        attention_rows = [row for row in transition_rows if row["transition"] == "Attention"]
        mlp_rows = [row for row in transition_rows if row["transition"] == "MLP"]
        attention_output[target_id] = attention_rows
        mlp_output[target_id] = mlp_rows
        robust_attention = [row for row in attention_rows if row["robust_positive"]]
        robust_mlp = [row for row in mlp_rows if row["robust_positive"]]
        if robust_attention and not robust_mlp:
            boundary_outcome = "B_Attention_integration"
        elif robust_mlp and not robust_attention:
            boundary_outcome = "B_MLP_integration"
        elif not robust_attention and not robust_mlp and max(float(row["median_RR"]) for row in rescue_rows if row["boundary"] == "h_pre") >= 0.20:
            boundary_outcome = "B_Upstream_state"
        else:
            boundary_outcome = "B_Distributed_or_nonmonotonic"
        boundary_statistics["targets"][target_id] = {
            "candidate_region": region, "rescue_rows": rescue_rows, "transition_rows": transition_rows,
            "strongest_confirmed_boundary": strongest[target_id], "boundary_outcome": boundary_outcome,
        }
    write_json(OUT / "phase_b_boundary/boundary_statistics.json", boundary_statistics)
    write_json(OUT / "phase_b_boundary/attention_boundary_gain.json", attention_output)
    write_json(OUT / "phase_b_boundary/mlp_boundary_gain.json", mlp_output)
    freeze_value = {
        "frozen_before_dose_or_control_scoring": True,
        "selection_used_controls": False, "selection_used_attention": False,
        "targets": strongest,
    }
    write_json(OUT / "phase_c_optional_dose/dose_boundary_freeze.json", freeze_value)
    write_json(OUT / "phase_b_boundary/control_boundary_freeze.json", freeze_value)
    print(json.dumps({"targets": {target: {"outcome": row["boundary_outcome"], "strongest": row["strongest_confirmed_boundary"]} for target, row in boundary_statistics["targets"].items()}}, indent=2))


if __name__ == "__main__":
    main()
