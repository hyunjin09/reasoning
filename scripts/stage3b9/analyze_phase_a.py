#!/usr/bin/env python3
"""Aggregate the frozen fresh Phase-A shared-rank causal analysis."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b9.analysis import summarize, unclipped_ratio


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
RANKS = (1, 2, 4, 8, 16, 24, 32, 48)
TARGETS = ("target_a", "target_b_r")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def collect(prefix: str) -> dict[str, dict]:
    rows = {}
    for path in sorted((OUT / "scoring/raw").glob(f"{prefix}_*/examples/*/result.json")):
        base = path.parent.name
        if base in rows:
            raise RuntimeError(f"Duplicate {prefix} result for base {base}")
        rows[base] = read_json(path)
    return rows


def select_confirmation_results(
    rows: dict[str, dict], bases: list[str], *, name: str, allow_screening_extras: bool = False
) -> dict[str, dict]:
    """Select the frozen confirmation cohort from persisted scoring results.

    Full-V scoring is intentionally run before the applicability gate, so its
    raw directory also contains excluded screening examples.  Projected arms
    are scored only after the gate and must cover the frozen cohort exactly.
    """
    expected = set(bases)
    observed = set(rows)
    missing = expected - observed
    extras = observed - expected
    if missing or (extras and not allow_screening_extras):
        raise RuntimeError(
            f"{name} Phase-A results do not cover the frozen confirmation cohort: "
            f"missing={sorted(missing, key=int)}, extras={sorted(extras, key=int)}"
        )
    return {base: rows[base] for base in bases}


def arm_map(result: dict, target_id: str) -> dict[str, dict]:
    target = next(row for row in result["targets"] if row["target_id"] == target_id)
    return {row["arm_id"]: row for row in target["arms"]}


def main() -> None:
    manifest = read_jsonl(OUT / "phase_a_shared/fresh_confirmation_manifest.jsonl")
    bases = [str(row["base_problem_id"]) for row in manifest]
    full = select_confirmation_results(
        collect("phase_a_full"), bases, name="full", allow_screening_extras=True
    )
    learned = select_confirmation_results(collect("phase_a_learned"), bases, name="learned")
    random = select_confirmation_results(collect("phase_a_random"), bases, name="random")
    full_rows, learned_rows, complement_rows, sham_rows, random_rows = [], [], [], [], []
    statistics, decisions = {}, {}
    for target_id in TARGETS:
        per_rank = {}
        full_by_base = {}
        for base in bases:
            arm = arm_map(full[base], target_id)["full_V"]
            full_by_base[base] = float(arm["BVR"])
            full_rows.append({"base_problem_id": base, "target_id": target_id, **arm})
        for rank in RANKS:
            base_rows = []
            for base in bases:
                arms = arm_map(learned[base], target_id)
                parallel = arms[f"learned_rank_{rank}"]
                complement = arms[f"complement_rank_{rank}"]
                sham = arms[f"sham_rank_{rank}"]
                row = {
                    "base_problem_id": base,
                    "target_id": target_id,
                    "rank": rank,
                    "B_full": full_by_base[base],
                    "B_parallel": float(parallel["BVR"]),
                    "B_perp": float(complement["BVR"]),
                    "B_sham": float(sham["BVR"]),
                    "SR": unclipped_ratio(parallel["BVR"], full_by_base[base]),
                    "CR": unclipped_ratio(complement["BVR"], full_by_base[base]),
                    "learned_bidirectionally_consistent": bool(parallel["bidirectionally_source_consistent"]),
                }
                base_rows.append(row)
                learned_rows.append({"base_problem_id": base, "target_id": target_id, "rank": rank, **parallel})
                complement_rows.append({"base_problem_id": base, "target_id": target_id, "rank": rank, **complement})
                sham_rows.append({"base_problem_id": base, "target_id": target_id, "rank": rank, **sham})
            random_aggregates = []
            for random_index in range(100):
                values = []
                for base in bases:
                    arm = arm_map(random[base], target_id)[f"random_{random_index:03d}_rank_{rank}"]
                    values.append(float(arm["BVR"]))
                    random_rows.append({"base_problem_id": base, "target_id": target_id, "rank": rank, "random_index": random_index, **arm})
                random_aggregates.append(float(np.median(values)))
            learned_values = [row["B_parallel"] for row in base_rows]
            learned_median = float(np.median(learned_values))
            sham_median = float(np.median([row["B_sham"] for row in base_rows]))
            sr_values = [row["SR"] for row in base_rows if row["SR"] is not None]
            cr_values = [row["CR"] for row in base_rows if row["CR"] is not None]
            learned_summary = summarize(learned_values, seed=3909 + rank)
            random_95 = float(np.quantile(random_aggregates, 0.95))
            bidirectional = float(np.mean([row["learned_bidirectionally_consistent"] for row in base_rows]))
            checks = {
                "median_SR_at_least_0_80": float(np.median(sr_values)) >= 0.80,
                "median_CR_at_most_0_30": float(np.median(cr_values)) <= 0.30,
                "learned_robustly_positive": learned_summary["median_bootstrap_95ci"][0] > 0.0,
                "learned_exceeds_sham": learned_median > sham_median,
                "learned_exceeds_random_95th": learned_median > random_95,
                "bidirectional_consistency_at_least_0_75": bidirectional >= 0.75,
            }
            per_rank[str(rank)] = {
                "base_count": len(base_rows),
                "B_full": summarize([row["B_full"] for row in base_rows], seed=4000 + rank),
                "B_parallel": learned_summary,
                "B_perp": summarize([row["B_perp"] for row in base_rows], seed=5000 + rank),
                "B_sham": summarize([row["B_sham"] for row in base_rows], seed=6000 + rank),
                "SR": summarize(sr_values, seed=7000 + rank),
                "CR": summarize(cr_values, seed=8000 + rank),
                "bidirectional_consistency": bidirectional,
                "random_aggregate_median_distribution": summarize(random_aggregates, seed=9000 + rank),
                "random_aggregate_95th_percentile": random_95,
                "learned_percentile_among_random": float(np.mean(np.asarray(random_aggregates) < learned_median)),
                "checks": checks,
                "passes_all": all(checks.values()),
                "per_base": base_rows,
            }
        passing = [rank for rank in RANKS if per_rank[str(rank)]["passes_all"]]
        k_shared = min(passing) if passing else None
        label = "No-Robust-Shared-Compression" if k_shared is None else ("Shared-Moderate-Dimensional" if k_shared <= 24 else "Shared-High-Dimensional")
        statistics[target_id] = per_rank
        decisions[target_id] = {"k_shared": k_shared, "geometry_label": label, "passing_ranks": passing}
    write_jsonl(OUT / "phase_a_shared/scoring/full_v_results.jsonl", full_rows)
    write_jsonl(OUT / "phase_a_shared/scoring/learned_rank_results.jsonl", learned_rows)
    write_jsonl(OUT / "phase_a_shared/scoring/complement_results.jsonl", complement_rows)
    write_jsonl(OUT / "phase_a_shared/scoring/sham_rank_results.jsonl", sham_rows)
    write_jsonl(OUT / "phase_a_shared/scoring/random_rank_results.jsonl", random_rows)
    write_json(OUT / "phase_a_shared/analysis/rank_curve_statistics.json", statistics)
    write_json(OUT / "phase_a_shared/analysis/shared_geometry_decision.json", {
        "fresh_base_count": len(bases),
        "targets": decisions,
        "decision_rule_source": "outputs/stage3b9/config/statistical_analysis_spec_v2.json",
        "technical_mechanics_valid": all(
            result["mechanical_controls"]["all_layout_and_roi_mappings_exact"]
            and result["mechanical_controls"]["all_query_head_selectivity_valid"]
            and result["mechanical_controls"]["all_recipient_tensor_alignment_exact"]
            and result["mechanical_controls"]["all_self_restorations_exact"]
            and result["mechanical_controls"]["all_scores_finite"]
            for result in [*full.values(), *learned.values(), *random.values()]
        ),
    })

    figures = OUT / "analysis/figures"
    ensure_directory(figures)
    colors = {"target_a": "#1f77b4", "target_b_r": "#d62728"}
    for target_id in TARGETS:
        stats = statistics[target_id]
        for metric, filename, ylabel in (
            ("SR", f"shared_recovery_vs_rank_{target_id}.png", "Median SR (parallel / full)"),
            ("CR", f"shared_complement_vs_rank_{target_id}.png", "Median CR (complement / full)"),
        ):
            fig, ax = plt.subplots(figsize=(6.4, 4.2))
            ax.plot(RANKS, [stats[str(rank)][metric]["median"] for rank in RANKS], marker="o", color=colors[target_id])
            ax.axhline(0.8 if metric == "SR" else 0.3, color="black", linestyle="--", linewidth=1)
            ax.set(xlabel="Shared rank", ylabel=ylabel, title=f"Fresh Phase A — {target_id}")
            ax.grid(alpha=0.25); fig.tight_layout(); fig.savefig(figures / filename, dpi=180); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharex=True)
    for ax, target_id in zip(axes, TARGETS):
        stats = statistics[target_id]
        ax.plot(RANKS, [stats[str(rank)]["B_parallel"]["median"] for rank in RANKS], marker="o", label="learned")
        ax.plot(RANKS, [stats[str(rank)]["B_sham"]["median"] for rank in RANKS], marker="s", label="sham")
        ax.plot(RANKS, [stats[str(rank)]["random_aggregate_95th_percentile"] for rank in RANKS], marker="^", label="random 95th")
        ax.set_title(target_id); ax.set_xlabel("rank"); ax.grid(alpha=0.25)
    axes[0].set_ylabel("Median unnormalized BVR"); axes[0].legend(); fig.tight_layout(); fig.savefig(figures / "learned_vs_random_vs_sham_subspace_curves.png", dpi=180); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharex=True)
    for ax, target_id in zip(axes, TARGETS):
        for base in bases:
            ax.plot(RANKS, [next(row for row in statistics[target_id][str(rank)]["per_base"] if row["base_problem_id"] == base)["SR"] for rank in RANKS], alpha=0.3)
        ax.set_title(target_id); ax.set_xlabel("rank"); ax.grid(alpha=0.2)
    axes[0].set_ylabel("Per-base SR"); fig.tight_layout(); fig.savefig(figures / "representative_per_base_shared_rank_curves.png", dpi=180); plt.close(fig)
    print(json.dumps({"fresh_bases": len(bases), "decisions": decisions}, indent=2))


if __name__ == "__main__":
    main()
