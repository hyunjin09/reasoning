#!/usr/bin/env python3
"""Aggregate Stage 3C.4 backward temporal-suppression results."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage3c4.analysis import (
    retention_summary,
    signed_summary,
    tested_window_threshold,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c4"


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
    config = read_json(OUT / "config/stage3c4_config.json")
    rows = result_map(OUT / "raw/phase_b")
    expected = config["primary_base_problem_ids"]
    if set(rows) != set(expected):
        raise RuntimeError(f"Phase B cohort mismatch: observed={sorted(rows)}")
    windows = list(read_json(OUT / "config/temporal_windows.json")["backward_offsets"])
    per_problem = []
    for base in expected:
        row = rows[base]
        targets = {}
        for target_id in ("target_a", "target_b"):
            target = row["target_results"][target_id]
            native = float(target["native"]["D"])
            values = {label: float(target["arms"][label]["score"]["D"]) for label in windows}
            targets[target_id] = {
                "D_native": native,
                "D_by_window": values,
                "loss_by_window": {label: native - value for label, value in values.items()},
                "retention_by_window": {label: value / native for label, value in values.items()},
            }
        aggregated_d = {
            label: float(np.mean([targets[target]["D_by_window"][label] for target in targets]))
            for label in windows
        }
        aggregated_retention = {
            label: float(np.mean([targets[target]["retention_by_window"][label] for target in targets]))
            for label in windows
        }
        per_problem.append({
            "base_problem_id": base,
            "targets": targets,
            "base_aggregated_D_native": float(np.mean([targets[target]["D_native"] for target in targets])),
            "base_aggregated_D_by_window": aggregated_d,
            "base_aggregated_retention_by_window": aggregated_retention,
            "w_80": tested_window_threshold(aggregated_retention, threshold=0.80),
            "w_50": tested_window_threshold(aggregated_retention, threshold=0.50),
        })
    write_jsonl(OUT / "phase_b_time/per_problem_temporal_results.jsonl", per_problem)

    statistics: dict[str, Any] = {
        "primary_unit": "base_problem_id",
        "N_unique_bases": len(per_problem),
        "windows": windows,
        "N_by_window": {label: len(per_problem) for label in windows},
        "targets": {},
    }
    for target_id in ("target_a", "target_b"):
        native = [row["targets"][target_id]["D_native"] for row in per_problem]
        statistics["targets"][target_id] = {
            label: retention_summary(
                native,
                [row["targets"][target_id]["D_by_window"][label] for row in per_problem],
                seed=int(config["seed"]) + index,
            )
            for index, label in enumerate(windows)
        }
    base_native = [row["base_aggregated_D_native"] for row in per_problem]
    statistics["base_aggregated"] = {
        label: retention_summary(
            base_native,
            [row["base_aggregated_D_by_window"][label] for row in per_problem],
            seed=int(config["seed"]) + 100 + index,
        )
        for index, label in enumerate(windows)
    }
    contrasts = {}
    for label in ("T1", "T2", "T4", "T8", "T16"):
        values = [
            row["base_aggregated_D_by_window"]["T0"]
            - row["base_aggregated_D_by_window"][label]
            for row in per_problem
        ]
        contrasts[f"{label}_vs_T0"] = signed_summary(
            values, seed=int(config["seed"]) + 200 + int(label[1:])
        )
    x = np.arange(len(windows), dtype=np.float64)
    slopes = []
    for row in per_problem:
        y = np.asarray([row["base_aggregated_D_by_window"][label] for label in windows], dtype=np.float64)
        slopes.append(float(-np.polyfit(x, y, 1)[0]))
    contrasts["monotonic_temporal_window_trend"] = signed_summary(
        slopes, seed=int(config["seed"]) + 299
    )
    statistics["frozen_contrasts_unadjusted"] = contrasts
    write_json(OUT / "phase_b_time/temporal_statistics.json", statistics)

    median_curves = {
        "target_a": {
            label: statistics["targets"]["target_a"][label]["retained_median"] for label in windows
        },
        "target_b": {
            label: statistics["targets"]["target_b"][label]["retained_median"] for label in windows
        },
        "base_aggregated": {
            label: statistics["base_aggregated"][label]["retained_median"] for label in windows
        },
    }
    necessity = {
        "thresholds_are_tested_windows_only": True,
        "no_exact_boundary_inference": True,
        "median_retention_curves": median_curves,
        "median_curve_w_80": {
            group: tested_window_threshold(curve, threshold=0.80) for group, curve in median_curves.items()
        },
        "median_curve_w_50": {
            group: tested_window_threshold(curve, threshold=0.50) for group, curve in median_curves.items()
        },
        "per_base_w_80_counts": dict(Counter(str(row["w_80"]) for row in per_problem)),
        "per_base_w_50_counts": dict(Counter(str(row["w_50"]) for row in per_problem)),
        "N_unique_bases": len(per_problem),
    }
    write_json(OUT / "phase_b_time/temporal_necessity_summary.json", necessity)
    write_json(OUT / "analysis/temporal_redundancy_analysis.json", {
        **necessity,
        "current_all_layer_retention": median_curves["base_aggregated"]["T0"],
        "longest_tested_retention": median_curves["base_aggregated"]["T16"],
        "all_queries_before_each_window_native": True,
        "teacher_forced_token_identities_frozen": True,
        "attention_used_as_primary_measure": False,
    })
    print(json.dumps({
        "N": len(per_problem),
        "median_retention": median_curves,
        "w_80": necessity["median_curve_w_80"],
        "w_50": necessity["median_curve_w_50"],
    }, indent=2))


if __name__ == "__main__":
    main()
