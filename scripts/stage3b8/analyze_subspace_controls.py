#!/usr/bin/env python3
"""Aggregate frozen Stage 3B.8 primary, random, and cross-target controls."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_two_shards(raw_root: Path, prefix: str, expected_bases: int) -> list[dict[str, Any]]:
    directories = [raw_root / f"{prefix}_{index:02d}" for index in range(2)]
    if not all((path / "result.json").is_file() for path in directories):
        raise RuntimeError(f"Both completed shards are required for {prefix}")
    rows = [row for path in directories for row in read_jsonl(path / "results.jsonl")]
    bases = [str(row["base_problem_id"]) for row in rows]
    if len(rows) != expected_bases or len(set(bases)) != expected_bases:
        raise RuntimeError(f"{prefix} is incomplete or duplicated")
    return rows


def bootstrap_median(values: list[float], seed: int) -> list[float]:
    vector = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    resampled = np.median(vector[rng.integers(0, len(vector), size=(10_000, len(vector)))], axis=1)
    return [float(value) for value in np.quantile(resampled, [0.025, 0.975])]


def summary(values: list[float], seed: int) -> dict[str, Any]:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        raise RuntimeError("Cannot summarize an empty finite effect vector")
    return {
        "N": len(finite),
        "mean": float(statistics.fmean(finite)),
        "median": float(statistics.median(finite)),
        "median_bootstrap_95_CI": bootstrap_median(finite, seed),
        "positive_fraction": float(np.mean(np.asarray(finite) > 0)),
    }


def target_row(result: dict[str, Any], target_id: str) -> dict[str, Any]:
    return next(row for row in result["targets"] if row["target_id"] == target_id)


def arm(row: dict[str, Any], arm_id: str) -> dict[str, Any]:
    return next(value for value in row["arms"] if value["arm_id"] == arm_id)


def analyze_primary(raw_root: Path, prefix: str, expected_bases: int) -> dict[str, Any]:
    results = load_two_shards(raw_root, prefix, expected_bases)
    config = read_json(OUT / "config/stage3b8_config.json")
    detail, complements, shams, target_summaries = [], [], [], []
    for target_offset, target in enumerate(config["targets"]):
        target_id = target["target_id"]
        per_target = []
        for result in results:
            row = target_row(result, target_id)
            values = {name: arm(row, name) for name in (
                "full_V", "learned_parallel", "orthogonal_complement", "sham_derived_parallel"
            )}
            full = float(values["full_V"]["BVR"])
            learned = float(values["learned_parallel"]["BVR"])
            complement = float(values["orthogonal_complement"]["BVR"])
            sham = float(values["sham_derived_parallel"]["BVR"])
            mechanics = all(
                bool(value["all_self_restorations_exact"])
                and bool(value["all_scores_finite"])
                and bool(value["all_query_head_selectivity_valid"])
                and bool(value["all_recipient_tensor_alignment_exact"])
                for value in values.values()
            ) and all(bool(result["mechanical_controls"][key]) for key in (
                "all_layout_and_roi_mappings_exact",
                "all_query_head_selectivity_valid",
                "all_recipient_tensor_alignment_exact",
                "all_self_restorations_exact",
                "all_scores_finite",
            ))
            item = {
                "base_problem_id": str(result["base_problem_id"]),
                "target_id": target_id,
                "B_full": full,
                "B_parallel": learned,
                "B_perp": complement,
                "B_sham_subspace": sham,
                "SR_parallel_over_full": None if full == 0 else learned / full,
                "CR_complement_over_full": None if full == 0 else complement / full,
                "all_mechanical_controls_passed": mechanics,
            }
            detail.append(item)
            complements.append({"base_problem_id": item["base_problem_id"], "target_id": target_id, "B_perp": complement, "B_full": full})
            shams.append({"base_problem_id": item["base_problem_id"], "target_id": target_id, "B_sham_subspace": sham, "B_parallel": learned})
            per_target.append(item)
        ratios = [row["SR_parallel_over_full"] for row in per_target if row["SR_parallel_over_full"] is not None and math.isfinite(row["SR_parallel_over_full"])]
        complement_ratios = [row["CR_complement_over_full"] for row in per_target if row["CR_complement_over_full"] is not None and math.isfinite(row["CR_complement_over_full"])]
        target_summaries.append({
            "target_id": target_id,
            "base_count": len(per_target),
            "full_V": summary([row["B_full"] for row in per_target], 1234 + target_offset * 100),
            "learned_parallel": summary([row["B_parallel"] for row in per_target], 1235 + target_offset * 100),
            "orthogonal_complement": summary([row["B_perp"] for row in per_target], 1236 + target_offset * 100),
            "sham_derived_parallel": summary([row["B_sham_subspace"] for row in per_target], 1237 + target_offset * 100),
            "median_unclipped_SR": float(np.median(ratios)),
            "median_unclipped_CR": float(np.median(complement_ratios)),
            "all_mechanical_controls_passed": all(row["all_mechanical_controls_passed"] for row in per_target),
        })
    write_jsonl(OUT / "subspace/primary_projected_results.jsonl", detail)
    write_jsonl(OUT / "subspace/complement_results.jsonl", complements)
    write_jsonl(OUT / "subspace/sham_subspace_results.jsonl", shams)
    payload = {
        "cohort_role": "untouched_37_base_primary_confirmation",
        "independent_unit": "base_problem_id",
        "base_count": expected_bases,
        "targets": target_summaries,
    }
    write_json(OUT / "analysis/subspace_restoration_statistics.json", payload)
    write_json(OUT / "analysis/sham_subspace_statistics.json", {
        "base_count": expected_bases,
        "targets": [{
            "target_id": row["target_id"],
            "learned_semantic": row["learned_parallel"],
            "sham_derived": row["sham_derived_parallel"],
            "median_margin": row["learned_parallel"]["median"] - row["sham_derived_parallel"]["median"],
        } for row in target_summaries],
    })

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    labels = ["full", "learned", "perp", "sham"]
    for axis, target in zip(axes, config["targets"]):
        rows = [row for row in detail if row["target_id"] == target["target_id"]]
        data = [[row[key] for row in rows] for key in ("B_full", "B_parallel", "B_perp", "B_sham_subspace")]
        axis.boxplot(data, tick_labels=labels, showfliers=True)
        axis.axhline(0, color="black", linewidth=0.7)
        axis.set(title=target["target_id"], ylabel="bidirectional Value restoration")
    fig.tight_layout()
    fig.savefig(OUT / "analysis/figures/learned_sham_complement_restoration.png", dpi=180)
    plt.close(fig)

    for filename, comparison_key, comparison_label, title in (
        ("learned_vs_sham_derived_subspace.png", "B_sham_subspace", "sham-derived", "Learned semantic vs sham-derived subspace"),
        ("in_subspace_vs_orthogonal_complement.png", "B_perp", "orthogonal complement", "In-subspace vs orthogonal-complement restoration"),
    ):
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
        for axis, target in zip(axes, config["targets"]):
            rows = [row for row in detail if row["target_id"] == target["target_id"]]
            axis.boxplot(
                [[row["B_parallel"] for row in rows], [row[comparison_key] for row in rows]],
                tick_labels=["learned", comparison_label],
                showfliers=True,
            )
            axis.axhline(0, color="black", linewidth=0.7)
            axis.set(title=target["target_id"], ylabel="bidirectional Value restoration")
        fig.suptitle(title)
        fig.tight_layout()
        fig.savefig(OUT / f"analysis/figures/{filename}", dpi=180)
        plt.close(fig)
    return payload


def analyze_random(raw_root: Path, prefix: str, expected_bases: int) -> dict[str, Any]:
    results = load_two_shards(raw_root, prefix, expected_bases)
    primary = read_json(OUT / "analysis/subspace_restoration_statistics.json")
    config = read_json(OUT / "config/stage3b8_config.json")
    rows, summaries = [], []
    for target in config["targets"]:
        target_id = target["target_id"]
        target_rows = [target_row(result, target_id) for result in results]
        arm_ids = sorted({value["arm_id"] for row in target_rows for value in row["arms"]})
        if arm_ids != [f"random_{index:03d}" for index in range(100)]:
            raise RuntimeError(f"Random controls for {target_id} do not contain exactly 100 arms")
        medians = []
        for arm_id in arm_ids:
            effects = [float(arm(row, arm_id)["BVR"]) for row in target_rows]
            median = float(np.median(effects))
            medians.append(median)
            rows.append({"target_id": target_id, "random_subspace_id": arm_id, "base_count": len(effects), "median_BVR": median, "mean_BVR": float(np.mean(effects))})
        learned = next(row for row in primary["targets"] if row["target_id"] == target_id)["learned_parallel"]["median"]
        summaries.append({
            "target_id": target_id,
            "random_subspace_count": 100,
            "learned_median_BVR": float(learned),
            "random_median_BVR_distribution": summary(medians, 4444),
            "learned_percentile_among_random": float(np.mean(np.asarray(medians) <= learned)),
            "one_sided_empirical_p": float((1 + np.sum(np.asarray(medians) >= learned)) / 101),
        })
    write_jsonl(OUT / "subspace/random_subspace_results.jsonl", rows)
    payload = {"base_count": expected_bases, "targets": summaries}
    write_json(OUT / "analysis/random_control_statistics.json", payload)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for axis, target in zip(axes, config["targets"]):
        values = [row["median_BVR"] for row in rows if row["target_id"] == target["target_id"]]
        learned = next(row for row in summaries if row["target_id"] == target["target_id"])["learned_median_BVR"]
        axis.hist(values, bins=18, alpha=0.8)
        axis.axvline(learned, color="tab:red", linewidth=2, label="learned")
        axis.set(title=target["target_id"], xlabel="median primary BVR", ylabel="random subspaces")
        axis.legend()
    fig.tight_layout()
    fig.savefig(OUT / "analysis/figures/learned_vs_random_subspaces.png", dpi=180)
    plt.close(fig)
    return payload


def analyze_cross(raw_root: Path, prefix: str, expected_bases: int) -> dict[str, Any]:
    results = load_two_shards(raw_root, prefix, expected_bases)
    primary_rows = read_jsonl(OUT / "subspace/primary_projected_results.jsonl")
    config = read_json(OUT / "config/stage3b8_config.json")
    rows, summaries = [], []
    for offset, target in enumerate(config["targets"]):
        target_id = target["target_id"]
        own = {row["base_problem_id"]: row for row in primary_rows if row["target_id"] == target_id}
        effects = []
        for result in results:
            base = str(result["base_problem_id"])
            cross = float(arm(target_row(result, target_id), "cross_target_parallel")["BVR"])
            rows.append({"base_problem_id": base, "target_id": target_id, "B_cross_target": cross, "B_own_learned": own[base]["B_parallel"], "B_full": own[base]["B_full"]})
            effects.append(cross)
        summaries.append({"target_id": target_id, "cross_target": summary(effects, 5555 + offset), "own_learned_median": float(np.median([row["B_parallel"] for row in own.values()])), "full_median": float(np.median([row["B_full"] for row in own.values()]))})
    write_jsonl(OUT / "subspace/cross_target_results.jsonl", rows)
    payload = {"base_count": expected_bases, "secondary_only": True, "targets": summaries}
    write_json(OUT / "analysis/cross_target_analysis.json", payload)
    fig, axis = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(summaries))
    axis.bar(x - 0.2, [row["own_learned_median"] for row in summaries], width=0.4, label="own learned")
    axis.bar(x + 0.2, [row["cross_target"]["median"] for row in summaries], width=0.4, label="cross target")
    axis.set_xticks(x, [row["target_id"] for row in summaries])
    axis.set(ylabel="median BVR", title="Cross-target Value-subspace transfer")
    axis.legend()
    fig.tight_layout()
    fig.savefig(OUT / "analysis/figures/cross_target_transfer.png", dpi=180)
    plt.close(fig)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("primary", "random", "cross"), required=True)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--expected-bases", type=int, default=37)
    args = parser.parse_args()
    ensure_directory(OUT / "subspace")
    ensure_directory(OUT / "analysis/figures")
    function = {"primary": analyze_primary, "random": analyze_random, "cross": analyze_cross}[args.mode]
    print(json.dumps(function(args.raw_root, args.prefix, args.expected_bases), indent=2))


if __name__ == "__main__":
    main()
