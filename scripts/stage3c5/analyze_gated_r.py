#!/usr/bin/env python3
"""Aggregate the prospectively gated R_last2/R_last4 carrier family."""

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


def target_row(base: str, target_id: str, target: dict[str, Any], carrier: str) -> dict[str, Any]:
    pairs = target["carriers"][carrier]["pairs"]
    restoration = carrier_restoration(
        native_o=float(target["native"]["O"]["D"]),
        native_c=float(target["native"]["C"]["D"]),
        donor_o_into_c=float(pairs["semantic_O_into_C"]["score"]["D"]),
        donor_c_into_o=float(pairs["semantic_C_into_O"]["score"]["D"]),
    )
    sham = []
    for key in ("sham_Osham_into_O", "sham_O_into_Osham", "sham_Csham_into_C", "sham_C_into_Csham"):
        pair = pairs[key]
        sham.append(abs(float(pair["score"]["D"]) - float(target["native"][pair["recipient"]]["D"])))
    self_shift = max(
        abs(float(pairs[key]["score"]["D"]) - float(target["native"][pairs[key]["recipient"]]["D"]))
        for key in ("self_O", "self_C")
    )
    return {
        "base_problem_id": base, "target_id": target_id, "carrier": carrier,
        **restoration, "sham_absolute_shifts": sham,
        "mean_sham_absolute_shift": float(np.mean(sham)),
        "max_self_absolute_shift": self_shift, "self_exact": self_shift == 0.0,
        "source_positions": target["carriers"][carrier]["source_positions"],
        "selected_layers": target["carriers"][carrier]["selected_layers"],
    }


def main() -> None:
    config = read_json(OUT / "config/stage3c5_config.json")
    initial = read_json(OUT / "phase_b_handoff/handoff_statistics.json")
    if not initial["r_expansion_gate"]["run_R_last2_R_last4"]:
        raise RuntimeError("R_last2/R_last4 were not prospectively gated")
    rows = result_map(OUT / "raw/phase_b_gated_r")
    expected = config["primary_base_problem_ids"]
    if set(rows) != set(expected):
        raise RuntimeError("Gated R cohort mismatch")
    target_rows = {carrier: [] for carrier in ("R_last2", "R_last4")}
    for base in expected:
        for target_id, target in rows[base]["target_results"].items():
            for carrier in target_rows:
                target_rows[carrier].append(target_row(base, target_id, target, carrier))
    write_jsonl(OUT / "phase_b_handoff/r_last2_results.jsonl", target_rows["R_last2"])
    write_jsonl(OUT / "phase_b_handoff/r_last4_results.jsonl", target_rows["R_last4"])
    initial_bases = {row["base_problem_id"]: row for row in read_jsonl(OUT / "phase_b_handoff/per_problem_handoff.jsonl")}
    base_rows = []
    for base in expected:
        values = {}
        for carrier in ("R_last2", "R_last4"):
            selected = [row for row in target_rows[carrier] if row["base_problem_id"] == base]
            bcr = float(np.mean([row["BCR"] for row in selected]))
            gap = float(np.mean([row["reference_gap"] for row in selected]))
            sham = float(np.mean([row["mean_sham_absolute_shift"] for row in selected]))
            values[carrier] = {
                "BCR": bcr, "reference_gap": gap, "CRR": bcr / gap,
                "mean_sham_absolute_shift": sham,
                "semantic_to_sham_ratio": bcr / sham if sham > 0 else math.inf,
            }
        base_rows.append({"base_problem_id": base, "carriers": values})
    summaries = {}
    for index, carrier in enumerate(("R_last2", "R_last4")):
        values = [row["carriers"][carrier] for row in base_rows]
        summaries[carrier] = {
            "BCR": signed_summary([row["BCR"] for row in values], seed=int(config["seed"]) + 800 + index),
            "BCR_values": [row["BCR"] for row in values],
            "CRR_values": [row["CRR"] for row in values],
            "CRR_mean": float(np.mean([row["CRR"] for row in values])),
            "CRR_median": float(np.median([row["CRR"] for row in values])),
            "sham_absolute_shift_median": float(np.median([row["mean_sham_absolute_shift"] for row in values])),
            "semantic_to_sham_ratio_median": float(np.median([row["semantic_to_sham_ratio"] for row in values])),
            "self_patches_exact": all(row["self_exact"] for row in target_rows[carrier]),
        }
    r1_bcr = [float(initial_bases[base]["carriers"]["R_last1"]["BCR"]) for base in expected]
    r1_crr_median = float(initial["carriers"]["R_last1"]["CRR_median"])
    contrasts = {}
    for index, carrier in enumerate(("R_last2", "R_last4")):
        values = [row["carriers"][carrier]["BCR"] - r1 for row, r1 in zip(base_rows, r1_bcr)]
        contrasts[f"{carrier}_minus_R_last1"] = {
            "values": values, **signed_summary(values, seed=int(config["seed"]) + 900 + index)
        }
    adjusted = holm_adjust([row["wilcoxon_one_sided_greater_p"] for row in contrasts.values()])
    for row, value in zip(contrasts.values(), adjusted):
        row["holm_adjusted_p"] = value
    rule = read_json(OUT / "config/carrier_family.json")["R_expansion_decision_rule"]
    expansion_cells = {}
    for carrier in ("R_last2", "R_last4"):
        contrast = contrasts[f"{carrier}_minus_R_last1"]
        crr_gain = float(summaries[carrier]["CRR_median"]) - r1_crr_median
        checks = {
            "increment_positive_on_at_least_75_percent": int(contrast["positive_count"]) >= 18,
            "holm_significant": float(contrast["holm_adjusted_p"]) < 0.05,
            "median_CRR_gain_at_least_0_05": crr_gain >= float(rule["minimum_median_CRR_gain"]),
        }
        expansion_cells[carrier] = {"expands": all(checks.values()), "checks": checks, "median_CRR_gain": crr_gain}
    output = {
        "primary_unit": "base_problem_id", "N_unique_bases": len(base_rows),
        "r_last1_reference": initial["carriers"]["R_last1"],
        "carriers": summaries, "contrasts": contrasts,
        "expansion_cells": expansion_cells,
        "short_history_expansion": any(row["expands"] for row in expansion_cells.values()),
        "base_rows": base_rows,
    }
    write_json(OUT / "phase_b_handoff/gated_r_statistics.json", output)
    print(json.dumps({
        "N": len(base_rows),
        "R_last1_CRR_median": r1_crr_median,
        "carriers": {carrier: {"BCR_median": row["BCR"]["median"], "positive": row["BCR"]["positive_count"], "CRR_median": row["CRR_median"], "sham_median": row["sham_absolute_shift_median"]} for carrier, row in summaries.items()},
        "expansion_cells": expansion_cells,
    }, indent=2))


if __name__ == "__main__":
    main()
