#!/usr/bin/env python3
"""Select Stage 3B.8 ranks using discovery causal results only."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b8.geometry import select_discovery_rank


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
    parser.add_argument("--expected-bases", type=int, required=True)
    args = parser.parse_args()
    directories = [args.raw_root / f"{args.prefix}_{rank:02d}" for rank in range(2)]
    if not all((path / "result.json").is_file() for path in directories):
        raise RuntimeError("Both discovery-rank scoring shards are required")
    raw = [row for path in directories for row in read_jsonl(path / "results.jsonl")]
    if len(raw) != args.expected_bases or not 16 <= len(raw) <= 20:
        raise RuntimeError("Discovery-rank scoring must contain 16--20 unique bases")
    if len({row["base_problem_id"] for row in raw}) != len(raw) or not all(row["cohort_role"] == "discovery" for row in raw):
        raise RuntimeError("Discovery-rank scoring is duplicated or contaminated")
    config = read_json(OUT / "config/stage3b8_config.json")
    svd = read_json(OUT / "subspace/svd_statistics.json")
    fitted = dict(np.load(OUT / "subspace/discovery_fitted_bases.npz"))
    detail_rows, target_summaries, selected_arrays = [], [], {}
    for target in config["targets"]:
        target_id = target["target_id"]
        target_rows = [next(row for row in result["targets"] if row["target_id"] == target_id) for result in raw]
        eligible = next(row for row in svd["targets"] if row["target_id"] == target_id)["candidate_ranks"]
        rank_summaries = []
        for rank in eligible:
            per_base = []
            for result, target_row in zip(raw, target_rows):
                arms = {arm["arm_id"]: arm for arm in target_row["arms"]}
                full = float(arms["full_V"]["BVR"])
                parallel = float(arms[f"rank_{rank}_parallel"]["BVR"])
                complement = float(arms[f"rank_{rank}_complement"]["BVR"])
                row = {
                    "base_problem_id": str(result["base_problem_id"]),
                    "target_id": target_id,
                    "rank": int(rank),
                    "B_full": full,
                    "B_parallel": parallel,
                    "B_perp": complement,
                    "projected_ratio": None if full == 0.0 else parallel / full,
                    "complement_ratio": None if full == 0.0 else complement / full,
                    "projected_sham_effect": float(arms[f"rank_{rank}_parallel"]["sham_effect"]),
                    "full_sham_effect": float(arms["full_V"]["sham_effect"]),
                    "all_mechanical_pass": all(
                        bool(arms[name]["all_self_restorations_exact"])
                        and bool(arms[name]["all_scores_finite"])
                        and bool(arms[name]["all_query_head_selectivity_valid"])
                        and bool(arms[name]["all_recipient_tensor_alignment_exact"])
                        for name in ("full_V", f"rank_{rank}_parallel", f"rank_{rank}_complement")
                    ),
                }
                per_base.append(row)
                detail_rows.append(row)
            projected_ratios = [row["projected_ratio"] for row in per_base if row["projected_ratio"] is not None and math.isfinite(row["projected_ratio"])]
            complement_ratios = [row["complement_ratio"] for row in per_base if row["complement_ratio"] is not None and math.isfinite(row["complement_ratio"])]
            rank_summaries.append({
                "rank": int(rank),
                "base_count": len(per_base),
                "median_full_BVR": float(np.median([row["B_full"] for row in per_base])),
                "median_projected_BVR": float(np.median([row["B_parallel"] for row in per_base])),
                "median_complement_BVR": float(np.median([row["B_perp"] for row in per_base])),
                "median_projected_ratio": float(np.median(projected_ratios)),
                "median_complement_ratio": float(np.median(complement_ratios)),
                "median_projected_sham_effect": float(np.median([row["projected_sham_effect"] for row in per_base])),
                "all_mechanical_pass": all(row["all_mechanical_pass"] for row in per_base),
            })
        selection = select_discovery_rank(rank_summaries)
        selected_rank = int(selection["rank"])
        selected_arrays[f"{target_id}__learned"] = fitted[f"{target_id}__semantic_rank_{selected_rank}"]
        selected_arrays[f"{target_id}__sham"] = fitted[f"{target_id}__sham_rank_{selected_rank}"]
        target_summaries.append({
            "target_id": target_id,
            "rank_summaries": rank_summaries,
            "selection": selection,
            "low_dimensional_hypothesis_status": "confirmed_on_discovery_gate" if selection["rule_satisfied"] else "partial_exploratory",
        })
    ensure_directory(OUT / "subspace")
    ensure_directory(OUT / "analysis/figures")
    write_jsonl(OUT / "subspace/discovery_rank_results.jsonl", detail_rows)
    write_json(OUT / "subspace/discovery_rank_statistics.json", {
        "cohort_role": "discovery_only",
        "base_count": len(raw),
        "targets": target_summaries,
        "primary_confirmation_results_inspected_or_used": False,
    })
    np.savez_compressed(OUT / "subspace/frozen_subspace_definition.npz", **selected_arrays)
    arms = {
        "frozen_from_discovery_only": True,
        "arms": [
            {"arm_id": "full_V", "dose": 1.0},
            {"arm_id": "learned_parallel", "dose": 1.0, "basis_key": "{target_id}__learned", "component": "parallel"},
            {"arm_id": "orthogonal_complement", "dose": 1.0, "basis_key": "{target_id}__learned", "component": "complement"},
            {"arm_id": "sham_derived_parallel", "dose": 1.0, "basis_key": "{target_id}__sham", "component": "parallel"}
        ],
        "selected_ranks": {row["target_id"]: row["selection"]["rank"] for row in target_summaries},
    }
    write_json(OUT / "config/primary_projected_arms.json", arms)
    lines = [
        "# Stage 3B.8 discovery-only rank selection", "",
        f"Discovery bases: **{len(raw)}**. The 37 confirmation bases were not scored or used for fitting/rank selection.", "",
    ]
    for row in target_summaries:
        lines.extend([
            f"## {row['target_id']}", "",
            f"Frozen `k_primary = {row['selection']['rank']}`. Rule satisfied: **{row['selection']['rule_satisfied']}**.", "",
            f"Selection basis: {row['selection']['selection_reason']}.", "",
        ])
        for rank in row["rank_summaries"]:
            lines.append(
                f"- k={rank['rank']}: median projected/full={rank['median_projected_ratio']:.4f}; "
                f"median complement/full={rank['median_complement_ratio']:.4f}; "
                f"median projected BVR={rank['median_projected_BVR']:.6f}."
            )
        lines.append("")
    write_text(OUT / "subspace/rank_selection_report.md", "\n".join(lines))

    fig, axes = plt.subplots(1, len(target_summaries), figsize=(6 * len(target_summaries), 4.5), squeeze=False)
    for axis, row in zip(axes[0], target_summaries):
        ranks = [item["rank"] for item in row["rank_summaries"]]
        axis.plot(ranks, [item["median_projected_ratio"] for item in row["rank_summaries"]], marker="o", label="parallel/full")
        axis.plot(ranks, [item["median_complement_ratio"] for item in row["rank_summaries"]], marker="s", label="complement/full")
        axis.axhline(0.8, linestyle="--", color="tab:blue", alpha=0.5)
        axis.axhline(0.3, linestyle="--", color="tab:orange", alpha=0.5)
        axis.set(xlabel="discovery SVD rank", ylabel="median un-clipped ratio", title=row["target_id"])
        axis.legend()
    fig.tight_layout()
    fig.savefig(OUT / "analysis/figures/discovery_causal_restoration_vs_rank.png", dpi=180)
    plt.close(fig)
    print(json.dumps({"base_count": len(raw), "selections": arms["selected_ranks"]}, indent=2))


if __name__ == "__main__":
    main()
