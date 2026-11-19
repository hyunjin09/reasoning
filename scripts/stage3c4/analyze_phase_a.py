#!/usr/bin/env python3
"""Aggregate Stage 3C.4 same-time layer-scope results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage3c4.analysis import retention_summary, signed_summary


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


def main() -> None:
    config = read_json(OUT / "config/stage3c4_config.json")
    rows = result_map(OUT / "raw/phase_a")
    expected = config["primary_base_problem_ids"]
    if set(rows) != set(expected):
        raise RuntimeError(f"Phase A cohort mismatch: observed={sorted(rows)}")
    scope_ids = read_json(OUT / "config/layer_scopes.json")["scopes"].keys()
    scopes = list(scope_ids)
    historical = result_map(ROOT / "outputs/stage3c3r/raw/phase_b")

    per_problem = []
    w4_checks = []
    for base in expected:
        row = rows[base]
        targets = {}
        for target_id in ("target_a", "target_b"):
            target = row["target_results"][target_id]
            native = float(target["native"]["D"])
            values = {label: float(target["arms"][label]["score"]["D"]) for label in scopes}
            historical_w4 = float(
                historical[base]["target_results"][target_id]["arms"]["R3"]["lambda_results"]["0.0"]["D"]
            )
            w4_checks.append({
                "base_problem_id": base,
                "target_id": target_id,
                "stage3c4_L0_D": values["L0"],
                "stage3c3r_R3_D": historical_w4,
                "exact": values["L0"] == historical_w4,
                "absolute_delta": abs(values["L0"] - historical_w4),
            })
            targets[target_id] = {
                "D_native": native,
                "D_by_scope": values,
                "loss_by_scope": {label: native - value for label, value in values.items()},
                "retention_by_scope": {label: value / native for label, value in values.items()},
            }
        per_problem.append({
            "base_problem_id": base,
            "targets": targets,
            "base_aggregated_D_native": float(np.mean([targets[target]["D_native"] for target in targets])),
            "base_aggregated_D_by_scope": {
                label: float(np.mean([targets[target]["D_by_scope"][label] for target in targets]))
                for label in scopes
            },
            "base_aggregated_retention_by_scope": {
                label: float(np.mean([targets[target]["retention_by_scope"][label] for target in targets]))
                for label in scopes
            },
        })
    write_jsonl(OUT / "phase_a_layer/per_problem_layer_scope_results.jsonl", per_problem)

    statistics: dict[str, Any] = {
        "primary_unit": "base_problem_id",
        "N_unique_bases": len(per_problem),
        "scopes": scopes,
        "targets": {},
    }
    for target_id in ("target_a", "target_b"):
        native = [row["targets"][target_id]["D_native"] for row in per_problem]
        statistics["targets"][target_id] = {
            label: retention_summary(
                native,
                [row["targets"][target_id]["D_by_scope"][label] for row in per_problem],
                seed=int(config["seed"]) + index,
            )
            for index, label in enumerate(scopes)
        }
    base_native = [row["base_aggregated_D_native"] for row in per_problem]
    statistics["base_aggregated"] = {
        label: retention_summary(
            base_native,
            [row["base_aggregated_D_by_scope"][label] for row in per_problem],
            seed=int(config["seed"]) + 100 + index,
        )
        for index, label in enumerate(scopes)
    }
    contrasts = {}
    for label in ("L1", "L2", "L3", "L4"):
        values = [
            row["base_aggregated_D_by_scope"]["L0"] - row["base_aggregated_D_by_scope"][label]
            for row in per_problem
        ]
        contrasts[f"{label}_vs_L0"] = signed_summary(values, seed=int(config["seed"]) + 200 + int(label[1:]))
    slopes = []
    x = np.arange(len(scopes), dtype=np.float64)
    for row in per_problem:
        y = np.asarray([row["base_aggregated_D_by_scope"][label] for label in scopes], dtype=np.float64)
        slopes.append(float(-np.polyfit(x, y, 1)[0]))
    contrasts["monotonic_layer_scope_trend"] = signed_summary(slopes, seed=int(config["seed"]) + 299)
    statistics["frozen_contrasts_unadjusted"] = contrasts
    write_json(OUT / "phase_a_layer/layer_scope_statistics.json", statistics)

    threshold = float(read_json(OUT / "config/primary_family.json")["substantial_retention_threshold"])
    first_below = {}
    for group in ("target_a", "target_b", "base_aggregated"):
        summaries = statistics["targets"][group] if group != "base_aggregated" else statistics[group]
        first_below[group] = next(
            (label for label in scopes if float(summaries[label]["retained_median"]) < threshold), None
        )
    analysis = {
        "N_unique_bases": len(per_problem),
        "current_query_only": True,
        "w4_reproduction": {
            "N": len(w4_checks),
            "exact_count": sum(row["exact"] for row in w4_checks),
            "all_exact": all(row["exact"] for row in w4_checks),
            "maximum_absolute_delta": max(row["absolute_delta"] for row in w4_checks),
            "per_target_base": w4_checks,
        },
        "substantial_retention_threshold": threshold,
        "first_scope_with_median_retention_below_threshold": first_below,
        "median_retention": {
            "target_a": {label: statistics["targets"]["target_a"][label]["retained_median"] for label in scopes},
            "target_b": {label: statistics["targets"]["target_b"][label]["retained_median"] for label in scopes},
            "base_aggregated": {label: statistics["base_aggregated"][label]["retained_median"] for label in scopes},
        },
        "attention_used_as_primary_measure": False,
    }
    write_json(OUT / "analysis/layer_redundancy_analysis.json", analysis)
    print(json.dumps({
        "N": len(per_problem),
        "w4_all_exact": analysis["w4_reproduction"]["all_exact"],
        "median_retention": analysis["median_retention"],
        "first_below": first_below,
    }, indent=2))


if __name__ == "__main__":
    main()
