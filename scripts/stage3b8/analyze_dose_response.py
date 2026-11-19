#!/usr/bin/env python3
"""Aggregate the frozen 37-base Stage 3B.8 dose-response experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b8.analysis import summarize_dose_target


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--expected-bases", type=int, default=37)
    args = parser.parse_args()
    directories = [args.raw_root / f"{args.prefix}_{rank:02d}" for rank in range(2)]
    if not all((path / "result.json").is_file() for path in directories):
        raise RuntimeError("Both completed dose-response shards are required")
    raw = [row for path in directories for row in read_jsonl(path / "results.jsonl")]
    if len(raw) != args.expected_bases or len({row["base_problem_id"] for row in raw}) != args.expected_bases:
        raise RuntimeError(f"Expected {args.expected_bases} independent bases, observed {len(raw)}")
    config = read_json(OUT / "config/stage3b8_config.json")
    rows = []
    for result in raw:
        for target in result["targets"]:
            for arm in target["arms"]:
                rows.append({
                    "base_problem_id": str(result["base_problem_id"]),
                    "example_id": str(result["example_id"]),
                    "target_id": target["target_id"],
                    "cell_id": target["cell_id"],
                    "lambda": float(arm["dose"]),
                    "BVR": float(arm["BVR"]),
                    "BVR_O": float(arm["BVR_O"]),
                    "BVR_C": float(arm["BVR_C"]),
                    "sham_effect": float(arm["sham_effect"]),
                    "bidirectionally_source_consistent": bool(arm["bidirectionally_source_consistent"]),
                    "native_endpoint_exact": arm["native_endpoint_exact"],
                    "reference_endpoint_within_tolerance": arm["stage3b7r_v_reference_within_tolerance"],
                    "reference_endpoint_max_abs_D_error": arm["stage3b7r_v_reference_max_abs_D_error"],
                    "mechanical_pass": bool(
                        arm["all_self_restorations_exact"]
                        and arm["all_scores_finite"]
                        and arm["all_query_head_selectivity_valid"]
                        and arm["all_recipient_tensor_alignment_exact"]
                        and result["mechanical_controls"]["all_layout_and_roi_mappings_exact"]
                    ),
                })
    target_ids = [target["target_id"] for target in config["targets"]]
    lambdas = [float(value) for value in config["dose_response"]["lambdas"]]
    summaries = []
    for offset, target_id in enumerate(target_ids):
        summary = summarize_dose_target(
            [row for row in rows if row["target_id"] == target_id],
            lambdas=lambdas,
            bootstrap_iterations=10_000,
            seed=1234 + 100 * offset,
            median_drop_tolerance=float(config["dose_response"]["phase_b_gate"]["cohort_median_nondecreasing_tolerance"]),
            median_within_base_spearman_minimum=float(config["dose_response"]["phase_b_gate"]["within_base_spearman_median_minimum"]),
        )
        summaries.append({"target_id": target_id, **summary})
    ensure_directory(OUT / "dose_response")
    ensure_directory(OUT / "analysis/figures")
    write_jsonl(OUT / "dose_response/per_problem_interpolation_results.jsonl", rows)
    write_jsonl(OUT / "dose_response/sham_interpolation_results.jsonl", [
        {
            "base_problem_id": row["base_problem_id"],
            "target_id": row["target_id"],
            "lambda": row["lambda"],
            "sham_effect": row["sham_effect"],
        }
        for row in rows
    ])
    payload = {
        "independent_unit": "base_problem_id",
        "base_count": args.expected_bases,
        "targets": summaries,
        "both_targets_passed_phase_b_gate": all(row["dose_response_gate_passed"] for row in summaries),
        "stage3b7r_endpoint_tolerance": 1e-6,
    }
    write_json(OUT / "dose_response/dose_response_statistics.json", payload)
    write_json(OUT / "analysis/dose_response_analysis.json", payload)

    for summary in summaries:
        values = summary["lambda_summaries"]
        x = [row["lambda"] for row in values]
        y = [row["median_BVR"] for row in values]
        ci = np.asarray([row["median_BVR_bootstrap_95_CI"] for row in values])
        sham = [row["median_sham_effect"] for row in values]
        fig, axis = plt.subplots(figsize=(6.4, 4.2))
        axis.plot(x, y, marker="o", label="semantic BVR")
        axis.fill_between(x, ci[:, 0], ci[:, 1], alpha=0.22)
        axis.plot(x, sham, marker="s", linestyle="--", label="sham magnitude")
        axis.axhline(0, color="black", linewidth=0.8)
        axis.set(xlabel="donor Value dose λ", ylabel="bidirectional Value restoration", title=f"Stage 3B.8 dose response — {summary['target_id']}")
        axis.legend()
        fig.tight_layout()
        fig.savefig(OUT / f"analysis/figures/dose_response_{summary['target_id']}.png", dpi=180)
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharex=True)
    for axis, target_id in zip(axes, target_ids):
        target_rows = [row for row in rows if row["target_id"] == target_id]
        for base in sorted({row["base_problem_id"] for row in target_rows}, key=int):
            base_rows = sorted([row for row in target_rows if row["base_problem_id"] == base], key=lambda row: row["lambda"])
            axis.plot([row["lambda"] for row in base_rows], [row["BVR"] for row in base_rows], alpha=0.24, linewidth=0.9)
        axis.axhline(0, color="black", linewidth=0.7)
        axis.set_title(target_id)
        axis.set_xlabel("λ")
    axes[0].set_ylabel("per-base BVR")
    fig.tight_layout()
    fig.savefig(OUT / "analysis/figures/per_problem_dose_trajectories.png", dpi=180)
    plt.close(fig)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
