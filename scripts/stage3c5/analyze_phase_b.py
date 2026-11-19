#!/usr/bin/env python3
"""Aggregate Stage 3C.5 carrier restoration and evaluate the R-window gate."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage3c4.analysis import holm_adjust, signed_summary
from visual_reasoning.stage3c5.protocol import carrier_restoration


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


def target_carrier_row(base: str, target_id: str, target: dict[str, Any], carrier: str) -> dict[str, Any]:
    native_o = float(target["native"]["O"]["D"])
    native_c = float(target["native"]["C"]["D"])
    pairs = target["carriers"][carrier]["pairs"]
    semantic = carrier_restoration(
        native_o=native_o,
        native_c=native_c,
        donor_o_into_c=float(pairs["semantic_O_into_C"]["score"]["D"]),
        donor_c_into_o=float(pairs["semantic_C_into_O"]["score"]["D"]),
    )
    sham_keys = (
        "sham_Osham_into_O", "sham_O_into_Osham",
        "sham_Csham_into_C", "sham_C_into_Csham",
    )
    sham_shifts = []
    for key in sham_keys:
        pair = pairs[key]
        sham_shifts.append(abs(float(pair["score"]["D"]) - float(target["native"][pair["recipient"]]["D"])))
    self_shifts = [
        abs(float(pairs[key]["score"]["D"]) - float(target["native"][pairs[key]["recipient"]]["D"]))
        for key in ("self_O", "self_C")
    ]
    return {
        "base_problem_id": base, "target_id": target_id,
        "coordinate": target["coordinate"], "carrier": carrier,
        **semantic,
        "sham_absolute_shifts": sham_shifts,
        "mean_sham_absolute_shift": float(np.mean(sham_shifts)),
        "max_self_absolute_shift": max(self_shifts),
        "self_exact": max(self_shifts) == 0.0,
        "source_positions": target["carriers"][carrier]["source_positions"],
        "selected_layers": target["carriers"][carrier]["selected_layers"],
    }


def main() -> None:
    config = read_json(OUT / "config/stage3c5_config.json")
    rows = result_map(OUT / "raw/phase_b")
    expected = config["primary_base_problem_ids"]
    if set(rows) != set(expected):
        raise RuntimeError(f"Phase-B cohort mismatch: {sorted(rows)}")
    carriers = ("R_last1", "Q", "h_pre")
    target_rows: dict[str, list[dict[str, Any]]] = {carrier: [] for carrier in carriers}
    for base in expected:
        for target_id, target in rows[base]["target_results"].items():
            for carrier in carriers:
                target_rows[carrier].append(target_carrier_row(base, target_id, target, carrier))
    for carrier, filename in (
        ("R_last1", "r_last1_results.jsonl"),
        ("Q", "q_results.jsonl"),
        ("h_pre", "hpre_results.jsonl"),
    ):
        write_jsonl(OUT / "phase_b_handoff" / filename, target_rows[carrier])
    write_jsonl(OUT / "phase_b_handoff/sham_controls.jsonl", [
        {
            "base_problem_id": row["base_problem_id"], "target_id": row["target_id"],
            "carrier": row["carrier"], "sham_absolute_shifts": row["sham_absolute_shifts"],
            "mean_sham_absolute_shift": row["mean_sham_absolute_shift"],
            "max_self_absolute_shift": row["max_self_absolute_shift"], "self_exact": row["self_exact"],
        }
        for carrier in carriers for row in target_rows[carrier]
    ])
    base_rows = []
    for base in expected:
        carrier_values = {}
        for carrier in carriers:
            selected = [row for row in target_rows[carrier] if row["base_problem_id"] == base]
            bcr = float(np.mean([row["BCR"] for row in selected]))
            gap = float(np.mean([row["reference_gap"] for row in selected]))
            sham = float(np.mean([row["mean_sham_absolute_shift"] for row in selected]))
            carrier_values[carrier] = {
                "BCR": bcr, "reference_gap": gap, "CRR": bcr / gap,
                "mean_sham_absolute_shift": sham,
                "semantic_to_sham_ratio": bcr / sham if sham > 0 else math.inf,
                "targets": {row["target_id"]: {"BCR": row["BCR"], "CRR": row["CRR"], "reference_gap": row["reference_gap"]} for row in selected},
            }
        base_rows.append({"base_problem_id": base, "carriers": carrier_values})
    write_jsonl(OUT / "phase_b_handoff/per_problem_handoff.jsonl", base_rows)

    statistics: dict[str, Any] = {
        "primary_unit": "base_problem_id", "N_unique_bases": len(base_rows),
        "selected_scope": read_json(OUT / "analysis/phase_b_gate.json")["selected_layer_scope"],
        "carriers": {}, "targets": {},
    }
    for carrier_index, carrier in enumerate(carriers):
        values = [row["carriers"][carrier] for row in base_rows]
        bcr_summary = signed_summary([row["BCR"] for row in values], seed=int(config["seed"]) + 500 + carrier_index)
        statistics["carriers"][carrier] = {
            "BCR": bcr_summary,
            "BCR_values": [row["BCR"] for row in values],
            "CRR_values": [row["CRR"] for row in values],
            "CRR_mean": float(np.mean([row["CRR"] for row in values])),
            "CRR_median": float(np.median([row["CRR"] for row in values])),
            "reference_gap_median": float(np.median([row["reference_gap"] for row in values])),
            "sham_absolute_shift_median": float(np.median([row["mean_sham_absolute_shift"] for row in values])),
            "semantic_to_sham_ratio_median": float(np.median([row["semantic_to_sham_ratio"] for row in values])),
            "self_patches_exact": all(row["self_exact"] for row in target_rows[carrier]),
        }
        statistics["targets"][carrier] = {}
        for target_id in ("target_a", "target_b"):
            selected = [row for row in target_rows[carrier] if row["target_id"] == target_id]
            statistics["targets"][carrier][target_id] = {
                "BCR": signed_summary([row["BCR"] for row in selected], seed=int(config["seed"]) + 600 + carrier_index),
                "CRR_median": float(np.median([row["CRR"] for row in selected])),
                "sham_absolute_shift_median": float(np.median([row["mean_sham_absolute_shift"] for row in selected])),
            }
    contrasts = {
        "R_last1_vs_Q": [row["carriers"]["R_last1"]["BCR"] - row["carriers"]["Q"]["BCR"] for row in base_rows],
        "R_last1_vs_h_pre": [row["carriers"]["R_last1"]["BCR"] - row["carriers"]["h_pre"]["BCR"] for row in base_rows],
        "Q_vs_h_pre": [row["carriers"]["Q"]["BCR"] - row["carriers"]["h_pre"]["BCR"] for row in base_rows],
    }
    statistics["carrier_contrasts"] = {
        name: {"values": values, **signed_summary(values, seed=int(config["seed"]) + 700 + index)}
        for index, (name, values) in enumerate(contrasts.items())
    }
    phase_a = read_json(OUT / "phase_a_tpre_layer/tpre_layer_statistics.json")["phase_a_tests"]
    phase_a_names = [row["test"] for row in phase_a]
    phase_b_tests = [
        ("R_last1_semantic_restoration", statistics["carriers"]["R_last1"]["BCR"]),
        ("Q_semantic_restoration", statistics["carriers"]["Q"]["BCR"]),
        ("h_pre_semantic_restoration", statistics["carriers"]["h_pre"]["BCR"]),
        ("R_last1_vs_Q", statistics["carrier_contrasts"]["R_last1_vs_Q"]),
        ("R_last1_vs_h_pre", statistics["carrier_contrasts"]["R_last1_vs_h_pre"]),
        ("Q_vs_h_pre", statistics["carrier_contrasts"]["Q_vs_h_pre"]),
    ]
    all_names = phase_a_names + [name for name, _ in phase_b_tests]
    all_p = [float(row["wilcoxon_one_sided_greater_p"]) for row in phase_a] + [float(row["wilcoxon_one_sided_greater_p"]) for _, row in phase_b_tests]
    adjusted = holm_adjust(all_p)
    family = [
        {"test": name, "raw_p": raw, "holm_adjusted_p": adj, "reject_0_05": adj < 0.05}
        for name, raw, adj in zip(all_names, all_p, adjusted)
    ]
    statistics["primary_15_test_family"] = family
    robust_rule = read_json(OUT / "config/primary_family.json")["carrier_robustness"]
    family_map = {row["test"]: row for row in family}
    robustness = {}
    for carrier, test_name in (("R_last1", "R_last1_semantic_restoration"), ("Q", "Q_semantic_restoration"), ("h_pre", "h_pre_semantic_restoration")):
        row = statistics["carriers"][carrier]
        checks = {
            "positive_on_at_least_75_percent": int(row["BCR"]["positive_count"]) >= 18,
            "holm_significant": bool(family_map[test_name]["reject_0_05"]),
            "median_CRR_at_least_0_20": float(row["CRR_median"]) >= float(robust_rule["minimum_median_CRR"]),
            "semantic_to_sham_ratio_at_least_2": float(row["semantic_to_sham_ratio_median"]) >= float(robust_rule["minimum_semantic_to_sham_ratio"]),
        }
        robustness[carrier] = {"robust": all(checks.values()), "checks": checks}
    statistics["robustness"] = robustness
    r = statistics["carriers"]["R_last1"]
    r_family = family_map["R_last1_semantic_restoration"]
    expansion_checks = {
        "R_last1_positive_nonzero": float(r["BCR"]["median"]) > 0.0,
        "positive_on_at_least_75_percent": int(r["BCR"]["positive_count"]) >= 18,
        "holm_significant": bool(r_family["reject_0_05"]),
        "median_CRR_below_0_80": float(r["CRR_median"]) < 0.80,
    }
    expansion = {"run_R_last2_R_last4": all(expansion_checks.values()), "checks": expansion_checks}
    statistics["r_expansion_gate"] = expansion
    write_json(OUT / "phase_b_handoff/handoff_statistics.json", statistics)
    print(json.dumps({
        "N": len(base_rows),
        "carriers": {name: {"BCR_median": row["BCR"]["median"], "positive": row["BCR"]["positive_count"], "CRR_median": row["CRR_median"], "sham_median": row["sham_absolute_shift_median"], "robust": robustness[name]["robust"]} for name, row in statistics["carriers"].items()},
        "r_expansion_gate": expansion,
    }, indent=2))


if __name__ == "__main__":
    main()
