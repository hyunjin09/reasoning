#!/usr/bin/env python3
"""Aggregate held-out local geometry and frozen secondary mixture diagnostics."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b9.analysis import (
    base_balanced_boolean_fraction,
    summarize,
    unclipped_ratio,
)
from visual_reasoning.stage3b9.geometry import principal_angle_degrees, projector_similarity


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
TARGETS = ("target_a", "target_b_r")
RANKS = (1, 2, 3)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def collect(prefix: str) -> dict[str, dict]:
    rows = {}
    for path in sorted((OUT / "phase_b_local/scoring/raw").glob(f"{prefix}_*/examples/*/result.json")):
        base = path.parent.name
        if base in rows:
            raise RuntimeError(f"Duplicate {prefix} result for base {base}")
        rows[base] = read_json(path)
    return rows


def target_map(result: dict) -> dict[str, dict]:
    return {row["target_id"]: row for row in result["targets"]}


def main() -> None:
    manifest = read_jsonl(OUT / "phase_b_local/cohort_manifest.jsonl")
    bases = [str(row["base_problem_id"]) for row in manifest]
    full, projected = collect("phase_b_full"), collect("phase_b_projected")
    if set(full) != set(bases) or set(projected) != set(bases):
        raise RuntimeError("Phase-B scoring does not exactly cover the frozen cohort")
    gates = {(str(row["base_problem_id"]), row["target_id"]): row for row in read_jsonl(OUT / "phase_b_local/applicability_gate.jsonl")}
    full_rows, local_rows, complement_rows, global_rows, random_rows = [], [], [], [], []
    statistics, decisions = {}, {}
    for target_id in TARGETS:
        per_rank = {}
        for base in bases:
            for pair in target_map(full[base])[target_id]["pairs"]:
                full_rows.append({"base_problem_id": base, "target_id": target_id, **pair})
        for rank in RANKS:
            base_rows, usable_fold_rows = [], []
            random_by_index = {index: [] for index in range(100)}
            for base in bases:
                gate = gates[(base, target_id)]
                if not gate["eligible"]:
                    continue
                full_pairs = {row["pair_id"]: row for row in target_map(full[base])[target_id]["pairs"]}
                projected_pairs = {row["pair_id"]: row for row in target_map(projected[base])[target_id]["pairs"]}
                fold_rows = []
                for pair_id, pair_gate in ((row["pair_id"], row) for row in gate["pairs"] if row["usable"]):
                    full_arm = full_pairs[pair_id]["full_v_arm"]
                    arms = {row["arm_id"]: row for row in projected_pairs[pair_id]["arms"]}
                    local = arms[f"local_rank_{rank}"]
                    complement = arms[f"local_complement_rank_{rank}"]
                    global_arm = arms[f"global_rank_{rank}"]
                    fold = {
                        "base_problem_id": base,
                        "target_id": target_id,
                        "pair_id": pair_id,
                        "rank": rank,
                        "B_full": float(full_arm["BVR"]),
                        "B_local": float(local["BVR"]),
                        "B_local_complement": float(complement["BVR"]),
                        "B_global_matched": float(global_arm["BVR"]),
                        "Local_SR": unclipped_ratio(local["BVR"], full_arm["BVR"]),
                        "Local_CR": unclipped_ratio(complement["BVR"], full_arm["BVR"]),
                        "GlobalMatched_SR": unclipped_ratio(global_arm["BVR"], full_arm["BVR"]),
                        "local_bidirectionally_consistent": bool(local["bidirectionally_source_consistent"]),
                        "local_effect_positive": float(local["BVR"]) > 0.0,
                    }
                    fold_rows.append(fold); usable_fold_rows.append(fold)
                    local_rows.append({"base_problem_id": base, "target_id": target_id, "pair_id": pair_id, "rank": rank, **local})
                    complement_rows.append({"base_problem_id": base, "target_id": target_id, "pair_id": pair_id, "rank": rank, **complement})
                    global_rows.append({"base_problem_id": base, "target_id": target_id, "pair_id": pair_id, "rank": rank, **global_arm})
                    for random_index in range(100):
                        random_arm = arms[f"random_{random_index:03d}_rank_{rank}"]
                        random_by_index[random_index].append((base, pair_id, float(random_arm["BVR"])))
                        random_rows.append({"base_problem_id": base, "target_id": target_id, "pair_id": pair_id, "rank": rank, "random_index": random_index, **random_arm})
                if fold_rows:
                    base_rows.append({
                        "base_problem_id": base,
                        "usable_fold_count": len(fold_rows),
                        "median_B_local": float(np.median([row["B_local"] for row in fold_rows])),
                        "median_Local_SR": float(np.median([row["Local_SR"] for row in fold_rows if row["Local_SR"] is not None])),
                        "median_Local_CR": float(np.median([row["Local_CR"] for row in fold_rows if row["Local_CR"] is not None])),
                        "median_GlobalMatched_SR": float(np.median([row["GlobalMatched_SR"] for row in fold_rows if row["GlobalMatched_SR"] is not None])),
                    })
            random_aggregates = []
            for random_index, values in random_by_index.items():
                by_base = {}
                for base, _pair, value in values:
                    by_base.setdefault(base, []).append(value)
                if by_base:
                    random_aggregates.append(float(np.median([np.median(items) for items in by_base.values()])))
            local_values = [row["median_B_local"] for row in base_rows]
            observed_local_median = float(np.median(local_values)) if local_values else float("nan")
            bidirectional_summary = base_balanced_boolean_fraction(
                usable_fold_rows, field="local_bidirectionally_consistent"
            )
            positive_summary = base_balanced_boolean_fraction(
                usable_fold_rows, field="local_effect_positive"
            )
            bidirectional = bidirectional_summary["across_base_mean"]
            positive = positive_summary["across_base_mean"]
            random_95 = float(np.quantile(random_aggregates, 0.95)) if random_aggregates else float("nan")
            checks = {
                "median_Local_SR_at_least_0_80": bool(base_rows) and float(np.median([row["median_Local_SR"] for row in base_rows])) >= 0.80,
                "median_Local_CR_at_most_0_30": bool(base_rows) and float(np.median([row["median_Local_CR"] for row in base_rows])) <= 0.30,
                "local_exceeds_random_95th": bool(random_aggregates) and observed_local_median > random_95,
                "bidirectional_consistency_at_least_0_75": bidirectional >= 0.75,
                "held_out_positive_fraction_at_least_0_75": positive >= 0.75,
            }
            per_rank[str(rank)] = {
                "eligible_base_count": len(base_rows),
                "usable_fold_count": len(usable_fold_rows),
                "B_local": summarize(local_values, seed=10000 + rank),
                "Local_SR": summarize([row["median_Local_SR"] for row in base_rows], seed=11000 + rank),
                "Local_CR": summarize([row["median_Local_CR"] for row in base_rows], seed=12000 + rank),
                "GlobalMatched_SR": summarize([row["median_GlobalMatched_SR"] for row in base_rows], seed=13000 + rank),
                "bidirectional_consistency": bidirectional,
                "bidirectional_consistency_per_base": bidirectional_summary["per_base"],
                "held_out_positive_fraction": positive,
                "held_out_positive_fraction_per_base": positive_summary["per_base"],
                "random_aggregate_95th_percentile": random_95,
                "local_percentile_among_random": float(np.mean(np.asarray(random_aggregates) < observed_local_median)) if random_aggregates else None,
                "checks": checks,
                "passes_all": all(checks.values()),
                "per_base": base_rows,
            }
        strong = [rank for rank in (1, 2) if per_rank[str(rank)]["passes_all"]]
        decisions[target_id] = {"local_low_dimensional": bool(strong), "smallest_passing_rank": min(strong) if strong else None, "rank_3_reported_only": per_rank["3"]["passes_all"]}
        statistics[target_id] = per_rank
    write_jsonl(OUT / "phase_b_local/scoring/leave_one_value_out_full.jsonl", full_rows)
    write_jsonl(OUT / "phase_b_local/scoring/local_rank_results.jsonl", local_rows)
    write_jsonl(OUT / "phase_b_local/scoring/local_complement_results.jsonl", complement_rows)
    write_jsonl(OUT / "phase_b_local/scoring/global_matched_results.jsonl", global_rows)
    write_jsonl(OUT / "phase_b_local/scoring/random_local_results.jsonl", random_rows)
    write_json(OUT / "phase_b_local/analysis/local_rank_statistics.json", statistics)
    write_json(OUT / "phase_b_local/analysis/local_vs_global_statistics.json", {
        target: {rank: {
            "median_Local_SR": statistics[target][str(rank)]["Local_SR"]["median"],
            "median_GlobalMatched_SR": statistics[target][str(rank)]["GlobalMatched_SR"]["median"],
            "median_difference": (statistics[target][str(rank)]["Local_SR"]["median"] - statistics[target][str(rank)]["GlobalMatched_SR"]["median"]),
        } for rank in RANKS} for target in TARGETS
    })
    write_json(OUT / "phase_b_local/analysis/local_geometry_decision.json", {"targets": decisions, "rule_source": "outputs/stage3b9/config/statistical_analysis_spec_v2.json"})

    canonical = {target: {} for target in TARGETS}
    full_vector_paths = {}
    for path in (OUT / "phase_b_local/scoring/raw").glob("phase_b_full_*/examples/*/vectors.npz"):
        full_vector_paths[path.parent.name] = path
    for base, path in full_vector_paths.items():
        with np.load(path) as values:
            for target in TARGETS:
                matrix = np.stack([values[f"{target}__value_{index}__semantic_delta"] for index in range(1, 5)]).astype(np.float64)
                _, _, vh = np.linalg.svd(matrix, full_matrices=False)
                canonical[target][base] = vh[:2].T
    angles, similarities = [], []
    for target in TARGETS:
        eligible_bases = [base for base in bases if gates[(base, target)]["eligible"] and base in canonical[target]]
        for left, right in combinations(eligible_bases, 2):
            angle = principal_angle_degrees(canonical[target][left], canonical[target][right])
            angles.append({"target_id": target, "left_base": left, "right_base": right, "principal_angles_degrees": angle.tolist()})
            similarities.append({"target_id": target, "left_base": left, "right_base": right, "projector_similarity": projector_similarity(canonical[target][left], canonical[target][right])})
    ensure_directory(OUT / "phase_c_secondary")
    write_json(OUT / "phase_c_secondary/principal_angles.json", {"rank": 2, "pairs": angles, "exploratory_only": True})
    write_json(OUT / "phase_c_secondary/projector_similarity.json", {"rank": 2, "pairs": similarities, "exploratory_only": True})
    write_json(OUT / "phase_c_secondary/exploratory_clusters.json", {"status": "not_run", "reason": "pairwise geometry is reported; confirmatory cluster selection would require a fresh cohort", "mixture_claim_made": False})

    figures = OUT / "analysis/figures"; ensure_directory(figures)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, target in zip(axes, TARGETS):
        ax.plot(RANKS, [statistics[target][str(rank)]["Local_SR"]["median"] for rank in RANKS], marker="o", label="local")
        ax.axhline(0.8, color="black", linestyle="--", linewidth=1); ax.set(title=target, xlabel="local rank", ylabel="median Local SR"); ax.grid(alpha=0.25)
    fig.tight_layout(); fig.savefig(figures / "leave_one_value_out_local_recovery.png", dpi=180); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, target in zip(axes, TARGETS):
        ax.plot(RANKS, [statistics[target][str(rank)]["Local_SR"]["median"] for rank in RANKS], marker="o", label="local")
        ax.plot(RANKS, [statistics[target][str(rank)]["GlobalMatched_SR"]["median"] for rank in RANKS], marker="s", label="global matched")
        ax.set(title=target, xlabel="matched rank", ylabel="median recovery"); ax.grid(alpha=0.25); ax.legend()
    fig.tight_layout(); fig.savefig(figures / "local_vs_matched_global_recovery.png", dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for target in TARGETS:
        values = [angle for row in angles if row["target_id"] == target for angle in row["principal_angles_degrees"]]
        if values: ax.hist(values, bins=15, alpha=0.5, label=target)
    ax.set(xlabel="Rank-2 principal angle (degrees)", ylabel="count", title="Cross-problem local-subspace angles"); ax.legend(); fig.tight_layout(); fig.savefig(figures / "local_subspace_principal_angle_distribution.png", dpi=180); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(TARGETS)); width = 0.23
    ax.bar(x-width, [statistics[t]["2"]["Local_SR"]["median"] for t in TARGETS], width, label="local r2")
    ax.bar(x, [statistics[t]["2"]["GlobalMatched_SR"]["median"] for t in TARGETS], width, label="global r2")
    ax.bar(x+width, [statistics[t]["2"]["Local_CR"]["median"] for t in TARGETS], width, label="local complement")
    ax.set_xticks(x, TARGETS); ax.set_ylabel("median recovery ratio"); ax.set_title("Global vs local geometry outcome"); ax.legend(); fig.tight_layout(); fig.savefig(figures / "global_vs_local_outcome_summary.png", dpi=180); plt.close(fig)
    first_base = next((base for base in bases if base in full_vector_paths), None)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    if first_base:
        with np.load(full_vector_paths[first_base]) as values:
            for ax, target in zip(axes, TARGETS):
                matrix = np.stack([values[f"{target}__value_{index}__semantic_delta"] for index in range(1, 5)]).astype(np.float64)
                centered = matrix - matrix.mean(axis=0, keepdims=True); _, _, vh = np.linalg.svd(centered, full_matrices=False); xy = centered @ vh[:2].T
                ax.scatter(xy[:, 0], xy[:, 1]);
                for index, point in enumerate(xy, 1): ax.text(point[0], point[1], f"C{index}")
                ax.set_title(f"base {first_base} — {target}")
    fig.tight_layout(); fig.savefig(figures / "within_problem_multi_value_geometry_example.png", dpi=180); plt.close(fig)
    print(json.dumps({"bases": len(bases), "decisions": decisions, "principal_angle_pairs": len(angles)}, indent=2))


if __name__ == "__main__":
    main()
