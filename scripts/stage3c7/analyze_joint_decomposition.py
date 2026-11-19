#!/usr/bin/env python3
"""Aggregate the prospectively gated Target-A joint K/V decomposition."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage3c4.analysis import holm_adjust, signed_summary
from visual_reasoning.stage3c7.protocol import rescue_effect, robust_effect


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c7"
CONDITIONS = ("O", "C")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def result_map(root: Path) -> dict[str, dict[str, Any]]:
    return {str(row["base_problem_id"]): row for path in sorted(root.glob("shard_*/examples/*/result.json")) for row in [read_json(path)]}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def main() -> None:
    config = read_json(OUT / "config/stage3c7_config.json")
    gated = result_map(OUT / "raw/joint_kv_primary")
    prior = result_map(OUT / "raw/primary")
    expected = [str(v) for v in config["primary_base_problem_ids"]]
    if set(gated) != set(expected):
        raise RuntimeError("Gated decomposition cohort mismatch")
    rows = []
    for base in expected:
        conditions = {}
        for condition in CONDITIONS:
            old = prior[base]["target_results"]["target_a"]["conditions"][condition]
            new = gated[base]["target_results"]["target_a"]["conditions"][condition]
            conditions[condition] = {
                mode: rescue_effect(
                    native_d=float(old["native"]["D"]), suppressed_d=float(old["suppressed"]["D"]),
                    rescued_d=float(new["arms"][mode]["D"]), condition=condition,
                ) for mode in ("K", "V", "KV")
            }
        aggregate = {}
        for mode in ("K", "V", "KV"):
            loss = float(np.mean([conditions[c][mode]["suppression_loss"] for c in CONDITIONS]))
            gain = float(np.mean([conditions[c][mode]["rescue_gain"] for c in CONDITIONS]))
            aggregate[mode] = {"rescue_gain": gain, "rescue_ratio": gain / loss, "rescue_ratio_is_clipped": False}
        rows.append({"base_problem_id": base, "target_id": "target_a", "conditions": conditions, "sign_aligned": aggregate})
    rows.append({
        "target_id": "target_b", "status": "NOT_RUN_GATED_OFF",
        "reason": "J4 did not meet the frozen substantial-joint rule (median RR<0.50)",
    })
    write_jsonl(OUT / "phase_b_joint/optional_joint_kv_decomposition.jsonl", rows)
    base_rows = [row for row in rows if row.get("base_problem_id")]
    gains = {mode: [row["sign_aligned"][mode]["rescue_gain"] for row in base_rows] for mode in ("K", "V", "KV")}
    ratios = {mode: [row["sign_aligned"][mode]["rescue_ratio"] for row in base_rows] for mode in ("K", "V", "KV")}
    vectors = {
        "joint_K_gt_0": gains["K"], "joint_V_gt_0": gains["V"], "joint_KV_gt_0": gains["KV"],
        "joint_KV_minus_K": (np.asarray(gains["KV"]) - np.asarray(gains["K"])).tolist(),
        "joint_KV_minus_V": (np.asarray(gains["KV"]) - np.asarray(gains["V"])).tolist(),
    }
    stats = {}
    for index, (name, values) in enumerate(vectors.items()):
        summary = signed_summary(values, seed=20268000 + index)
        stats[name] = {
            "N": summary["N"], "mean_gain": summary["mean"], "median_gain": summary["median"],
            "gain_bootstrap_mean_ci95": summary["bootstrap_mean_ci95"], "positive_count": summary["positive_count"],
            "positive_fraction": summary["positive_fraction"], "wilcoxon_one_sided_greater_p": summary["wilcoxon_one_sided_greater_p"],
            "values": values,
        }
        mode = name.split("_")[1] if name in {"joint_K_gt_0", "joint_V_gt_0", "joint_KV_gt_0"} else None
        if mode:
            stats[name]["median_RR"] = float(np.median(ratios[mode]))
            stats[name]["RR_values"] = ratios[mode]
    adjusted = holm_adjust([row["wilcoxon_one_sided_greater_p"] for row in stats.values()])
    for row, p in zip(stats.values(), adjusted):
        row["holm_adjusted_p"] = p
        row["robust_positive"] = robust_effect(row)
    kv_gain = stats["joint_KV_gt_0"]["median_gain"]
    k_near = stats["joint_K_gt_0"]["robust_positive"] and stats["joint_K_gt_0"]["median_gain"] >= 0.8 * kv_gain
    v_near = stats["joint_V_gt_0"]["robust_positive"] and stats["joint_V_gt_0"]["median_gain"] >= 0.8 * kv_gain
    if v_near and not k_near:
        mechanism = "joint_value_dominant"
    elif k_near and not v_near:
        mechanism = "joint_key_dominant"
    elif stats["joint_KV_minus_K"]["robust_positive"] and stats["joint_KV_minus_V"]["robust_positive"]:
        mechanism = "joint_KV_interaction"
    else:
        mechanism = "joint_mixed_or_redundant"
    output = {
        "gate": read_json(OUT / "phase_b_joint/joint_kv_decomposition_gate.json"),
        "target_a": {"N_unique_bases": len(base_rows), "tests": stats, "mechanism": mechanism},
        "target_b": {"status": "NOT_RUN_GATED_OFF"},
    }
    write_json(OUT / "analysis/joint_kv_decomposition_statistics.json", output)
    print(json.dumps({"mechanism": mechanism, "medians": {k: v["median_gain"] for k, v in stats.items()}}, indent=2))


if __name__ == "__main__":
    main()
