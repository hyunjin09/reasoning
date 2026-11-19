#!/usr/bin/env python3
"""Aggregate reduced target/mention/irrelevant t_pre controls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage3c4.analysis import signed_summary


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
    rows = result_map(OUT / "raw/controls")
    phase_a = {row["base_problem_id"]: row for row in (json.loads(line) for line in (OUT / "phase_a_tpre_layer/per_problem_tpre_scope_results.jsonl").read_text().splitlines() if line.strip())}
    expected = config["primary_base_problem_ids"]
    if set(rows) != set(expected):
        raise RuntimeError("Control cohort mismatch")
    target_rows = []
    for base in expected:
        targets = {}
        for target_id, target in rows[base]["target_results"].items():
            native = float(target["native_A0"]["D"])
            losses = {source: native - float(target["arms"][f"{source}_tpre"]["D"]) for source in ("T", "M", "I")}
            prior_t = float(phase_a[base]["targets"][target_id]["D_native"]) - float(phase_a[base]["targets"][target_id]["D_by_scope"]["P4"])
            targets[target_id] = {"D_native": native, "loss": losses, "P4_target_reproduction_exact": losses["T"] == prior_t}
            target_rows.append({"base_problem_id": base, "target_id": target_id, **targets[target_id]})
        base_loss = {source: float(np.mean([targets[target]["loss"][source] for target in targets])) for source in ("T", "M", "I")}
        target_rows.append({
            "base_problem_id": base, "target_id": "base_aggregated",
            "loss": base_loss,
            "T_minus_M": base_loss["T"] - base_loss["M"],
            "T_minus_I": base_loss["T"] - base_loss["I"],
        })
    write_jsonl(OUT / "controls/mention_tpre_suppression.jsonl", [row for row in target_rows if row["target_id"] != "base_aggregated" and "M" in row["loss"]])
    write_jsonl(OUT / "controls/irrelevant_tpre_suppression.jsonl", [row for row in target_rows if row["target_id"] != "base_aggregated" and "I" in row["loss"]])
    base_rows = [row for row in target_rows if row["target_id"] == "base_aggregated"]
    statistics = {
        "primary_unit": "base_problem_id", "N_unique_bases": len(base_rows),
        "selected_scope": read_json(OUT / "analysis/phase_b_gate.json")["selected_layer_scope"],
        "P4_target_reproduction": {
            "N": len(expected) * 2,
            "exact_count": sum(row["P4_target_reproduction_exact"] for row in target_rows if row["target_id"] != "base_aggregated"),
        },
        "median_loss": {source: float(np.median([row["loss"][source] for row in base_rows])) for source in ("T", "M", "I")},
        "T_minus_M": signed_summary([row["T_minus_M"] for row in base_rows], seed=int(config["seed"]) + 1000),
        "T_minus_I": signed_summary([row["T_minus_I"] for row in base_rows], seed=int(config["seed"]) + 1001),
        "T_greater_M_count": sum(row["T_minus_M"] > 0 for row in base_rows),
        "T_greater_I_count": sum(row["T_minus_I"] > 0 for row in base_rows),
        "attention_used_as_primary_measure": False,
    }
    write_json(OUT / "controls/target_specificity_statistics.json", statistics)
    print(json.dumps(statistics, indent=2))


if __name__ == "__main__":
    main()
