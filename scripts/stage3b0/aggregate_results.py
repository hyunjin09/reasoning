#!/usr/bin/env python3
"""Aggregate the frozen Stage 3B.0 shards and produce causal statistics/figures."""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3a.metrics import bootstrap_interval, summarize_effect_values


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "outputs/stage3b0/raw/shards"
OUT = ROOT / "outputs/stage3b0"
FIGURES = OUT / "analysis/figures"
GROUPS = ("P_post_image", "Q", "T", "Q_plus_T")
CROSS = ("cross_original_to_counterfactual", "cross_counterfactual_to_original")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def finite_values(rows: Iterable[dict[str, Any]], key: str) -> list[float]:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError(f"Expected nonempty finite values for {key}")
    return values


def proportion_summary(values: list[bool], *, seed: int) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "count": int(array.sum()),
        "n": int(array.size),
        "proportion": float(array.mean()),
        "bootstrap_ci": bootstrap_interval(array, statistic="mean", seed=seed),
    }


def oriented_shift(row: dict[str, Any]) -> float:
    direction = float(row["source_D_no_patch"] - row["recipient_D_no_patch"])
    return float(np.sign(direction) * float(row["D_shift"]))


def patch_group_statistics(rows: list[dict[str, Any]], group: str) -> dict[str, Any]:
    group_rows = [row for row in rows if row["group"] == group]
    result: dict[str, Any] = {"group": group, "row_count": len(group_rows), "directions": {}}
    for direction in CROSS:
        selected = [row for row in group_rows if row["patch_type"] == direction]
        result["directions"][direction] = {
            "recovery_raw": summarize_effect_values(finite_values(selected, "directional_recovery_raw")),
            "oriented_D_shift": summarize_effect_values([oriented_shift(row) for row in selected]),
            "source_consistent_shift": proportion_summary(
                [bool(row["source_consistent_shift"]) for row in selected], seed=51_000 + len(group) + len(direction)
            ),
        }
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in group_rows:
        if row["patch_type"] in CROSS:
            by_base[str(row["base_problem_id"])].append(row)
    if len(by_base) != 49 or any(len(values) != 2 for values in by_base.values()):
        raise RuntimeError(f"Group {group} lacks two cross-directions per base")
    bidirectional = []
    per_base = []
    for base, values in sorted(by_base.items(), key=lambda item: int(item[0])):
        recovery = float(np.mean([float(row["directional_recovery_raw"]) for row in values]))
        shift = float(np.mean([oriented_shift(row) for row in values]))
        bidirectional.append(recovery)
        per_base.append(
            {
                "base_problem_id": base,
                "evidence_type": values[0]["evidence_type"],
                "mean_bidirectional_recovery_raw": recovery,
                "mean_bidirectional_oriented_D_shift": shift,
                "both_directions_source_consistent": all(row["source_consistent_shift"] for row in values),
            }
        )
    self_rows = [row for row in group_rows if row["patch_type"].startswith("self_")]
    sham_rows = [row for row in group_rows if row["patch_type"] in {"sham_to_original", "original_to_sham"}]
    result.update(
        {
            "bidirectional_recovery_raw": summarize_effect_values(bidirectional),
            "bidirectional_oriented_D_shift": summarize_effect_values(
                [row["mean_bidirectional_oriented_D_shift"] for row in per_base]
            ),
            "both_directions_source_consistent": proportion_summary(
                [row["both_directions_source_consistent"] for row in per_base], seed=52_000 + len(group)
            ),
            "self_patch_absolute_D_shift": summarize_effect_values([abs(float(row["D_shift"])) for row in self_rows]),
            "sham_patch_absolute_D_shift": summarize_effect_values([abs(float(row["D_shift"])) for row in sham_rows]),
            "per_base": per_base,
        }
    )
    return result


def numeric_strings(text: str) -> set[str]:
    return set(re.findall(r"(?<![A-Za-z])\d+(?:\.\d+)?", str(text)))


def classify_rollout(row: dict[str, Any]) -> dict[str, Any]:
    text = str(row["continuation_text"])
    original = numeric_strings(row["original_fact"])
    counterfactual = numeric_strings(row["counterfactual_fact"])
    original_unique = original - counterfactual
    counterfactual_unique = counterfactual - original
    original_hit = bool(original_unique) and any(re.search(rf"(?<!\d){re.escape(value)}(?!\d)", text) for value in original_unique)
    counterfactual_hit = bool(counterfactual_unique) and any(
        re.search(rf"(?<!\d){re.escape(value)}(?!\d)", text) for value in counterfactual_unique
    )
    target_matches = []
    for identity, values in (("original", original_unique), ("counterfactual", counterfactual_unique)):
        for value in values:
            match = re.search(rf"(?<!\d){re.escape(value)}(?!\d)", text)
            if match:
                target_matches.append((match.start(), match.end(), identity, value))
    if original_hit and not counterfactual_hit:
        label = "original_only"
    elif counterfactual_hit and not original_hit:
        label = "counterfactual_only"
    elif original_hit and counterfactual_hit:
        label = "both"
    else:
        label = "neither_or_non_numeric"
    first = min(target_matches) if target_matches else None
    return {
        **row,
        "automatic_fact_mention": label,
        "original_unique_numeric_strings": sorted(original_unique),
        "counterfactual_unique_numeric_strings": sorted(counterfactual_unique),
        "first_target_numeric_mention": (
            {
                "character_start": first[0],
                "character_end": first[1],
                "identity": first[2],
                "value": first[3],
                "context": text[max(0, first[0] - 60) : min(len(text), first[1] + 60)],
            }
            if first is not None
            else None
        ),
    }


def plot_results(cutoff: list[dict[str, Any]], patches: list[dict[str, Any]], patch_stats: dict[str, Any]) -> None:
    ensure_directory(FIGURES)
    full = np.asarray([row["CE_full"] for row in cutoff])
    cut = np.asarray([row["CE_cut"] for row in cutoff])
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(full, cut, c=["#4472c4" if "numeric" in row["evidence_type"] else "#ed7d31" for row in cutoff])
    bounds = [float(min(full.min(), cut.min())), float(max(full.max(), cut.max()))]
    ax.plot(bounds, bounds, "--", color="gray", linewidth=1)
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set(xlabel="Stage 3A full-vision CE", ylabel="Generation-start-cutoff CE", title="Full vision vs generation-start cutoff")
    fig.tight_layout(); fig.savefig(FIGURES / "01_full_vs_cutoff_ce.png", dpi=180); plt.close(fig)

    retention = np.sort(np.asarray([row["retention_ratio_raw"] for row in cutoff]))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(np.arange(1, len(retention) + 1), retention, marker="o", markersize=3)
    ax.axhline(0, color="black", linewidth=0.7); ax.axhline(1, color="gray", linestyle="--")
    ax.set(xlabel="Problem (sorted)", ylabel="Raw retention ratio ρ", title="Per-problem cutoff retention")
    fig.tight_layout(); fig.savefig(FIGURES / "02_cutoff_retention_ratio.png", dpi=180); plt.close(fig)

    condition_values = [[row[f"D_{name}_cut"] for row in cutoff] for name in ("original", "counterfactual", "sham")]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.boxplot(condition_values, tick_labels=["Original", "Counterfactual", "Sham"], showfliers=True)
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set(ylabel="Evidence preference D under cutoff", title="Condition-specific preference under cutoff")
    fig.tight_layout(); fig.savefig(FIGURES / "03_cutoff_condition_preferences.png", dpi=180); plt.close(fig)

    for number, group, title in ((4, "P_post_image", "Broad post-image prefix"), (5, "Q", "Question-only")):
        values = np.sort([row["mean_bidirectional_recovery_raw"] for row in patch_stats["groups"][group]["per_base"]])
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(np.arange(1, len(values) + 1), values, marker="o", markersize=3, color="#5b9bd5")
        ax.axhline(0, color="black", linewidth=0.8); ax.axhline(1, color="gray", linestyle="--")
        ax.set_yscale("symlog", linthresh=0.1)
        ax.set(xlabel="Problem (sorted)", ylabel="Mean bidirectional recovery (raw, symlog)", title=f"{title} patch recovery")
        fig.tight_layout(); fig.savefig(FIGURES / f"{number:02d}_{group.lower()}_recovery.png", dpi=180); plt.close(fig)

    p = {row["base_problem_id"]: row["mean_bidirectional_recovery_raw"] for row in patch_stats["groups"]["P_post_image"]["per_base"]}
    q = {row["base_problem_id"]: row["mean_bidirectional_recovery_raw"] for row in patch_stats["groups"]["Q"]["per_base"]}
    fig, ax = plt.subplots(figsize=(6, 5))
    display_limit = 2.2
    for base in p:
        q_display = min(display_limit, max(-display_limit, q[base]))
        ax.plot([0, 1], [p[base], q_display], color="#9ec3e6", alpha=0.45, linewidth=0.8)
        ax.scatter([0, 1], [p[base], q_display], color=["#4472c4", "#70ad47"], s=13, zorder=3)
    extreme_base = max(q, key=lambda key: abs(q[key]))
    ax.annotate(
        f"base {extreme_base}: raw Q recovery={q[extreme_base]:.2g}\n(off-scale; denominator ≈ 0)",
        xy=(1, display_limit), xytext=(0.45, 1.65),
        arrowprops={"arrowstyle": "->", "color": "#555555"}, fontsize=8,
    )
    ax.axhline(0, color="black", linewidth=0.5); ax.axhline(1, color="gray", linestyle="--")
    ax.set_xticks([0, 1], ["P_post-image", "Q-only"])
    ax.set_ylim(-display_limit - 0.15, display_limit + 0.15)
    ax.set(ylabel="Mean bidirectional recovery (raw)", title="Per-problem broad-prefix vs question-only recovery")
    fig.tight_layout(); fig.savefig(FIGURES / "06_broad_vs_question_recovery.png", dpi=180); plt.close(fig)

    numeric = [row["retention_ratio_raw"] for row in cutoff if "numeric" in row["evidence_type"]]
    structural = [row["retention_ratio_raw"] for row in cutoff if "structural" in row["evidence_type"]]
    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.boxplot([numeric, structural], tick_labels=[f"Numeric\nN={len(numeric)}", f"Structural\nN={len(structural)}"])
    ax.axhline(0, color="black", linewidth=0.7); ax.axhline(1, color="gray", linestyle="--")
    ax.set(ylabel="Raw cutoff retention ρ", title="Retention by evidence stratum")
    fig.tight_layout(); fig.savefig(FIGURES / "07_evidence_strata_retention.png", dpi=180); plt.close(fig)

    q_rows = patch_stats["groups"]["Q"]["per_base"]
    ordered = sorted(q_rows, key=lambda row: row["mean_bidirectional_recovery_raw"])
    representatives = [ordered[0], ordered[len(ordered) // 2], ordered[-1]]
    patch_lookup = {(row["base_problem_id"], row["group"], row["patch_type"]): row for row in patches}
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), sharey=False)
    for ax, representative in zip(axes, representatives):
        base = representative["base_problem_id"]
        p_row = patch_lookup[(base, "P_post_image", "cross_original_to_counterfactual")]
        q_row = patch_lookup[(base, "Q", "cross_original_to_counterfactual")]
        values = [p_row["recipient_D_no_patch"], q_row["patched_D"], p_row["patched_D"], p_row["source_D_no_patch"]]
        ax.bar(["C", "C←O,Q", "C←O,P", "O"], values, color=["#ed7d31", "#70ad47", "#5b9bd5", "#4472c4"])
        ax.axhline(0, color="black", linewidth=0.6); ax.set_title(f"Base {base}\nQ recovery={representative['mean_bidirectional_recovery_raw']:.2g}")
        ax.tick_params(axis="x", rotation=25)
    axes[0].set_ylabel("Evidence preference D")
    fig.suptitle("Representative original→counterfactual cache transfers")
    fig.tight_layout(); fig.savefig(FIGURES / "08_representative_patch_examples.png", dpi=180); plt.close(fig)

    group_values = [[row["mean_bidirectional_recovery_raw"] for row in patch_stats["groups"][group]["per_base"]] for group in GROUPS]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.boxplot(group_values, tick_labels=["P", "Q", "T", "Q+T"], showfliers=True)
    ax.axhline(0, color="black", linewidth=0.7); ax.axhline(1, color="gray", linestyle="--")
    ax.set_yscale("symlog", linthresh=0.1)
    ax.set(ylabel="Mean bidirectional recovery (raw)", title="Prospectively frozen carrier groups")
    fig.tight_layout(); fig.savefig(FIGURES / "09_all_group_recovery.png", dpi=180); plt.close(fig)


def main() -> None:
    expected = read_jsonl(OUT / "config/cohort_manifest.jsonl")
    expected_bases = {str(row["base_problem_id"]) for row in expected}
    shard_dirs = sorted(path for path in RAW.glob("cohort_*") if (path / "result.json").is_file())
    if len(shard_dirs) != 7:
        raise RuntimeError(f"Expected 7 completed shards, found {len(shard_dirs)}")
    cutoff: list[dict[str, Any]] = []
    patches: list[dict[str, Any]] = []
    rollouts: list[dict[str, Any]] = []
    for shard in shard_dirs:
        cutoff.extend(read_jsonl(shard / "cutoff_results.jsonl"))
        patches.extend(read_jsonl(shard / "patch_results.jsonl"))
        rollouts.extend(read_jsonl(shard / "rollout_results.jsonl"))
    observed_bases = {str(row["base_problem_id"]) for row in cutoff}
    if len(cutoff) != 49 or observed_bases != expected_bases:
        raise RuntimeError("Cutoff aggregation does not exactly cover the frozen 49 bases")
    if len(patches) != 49 * 4 * 6 or len(rollouts) != 49 * 3:
        raise RuntimeError("Patch/rollout row counts do not match the frozen design")
    cutoff.sort(key=lambda row: int(row["base_problem_id"]))
    patches.sort(key=lambda row: (int(row["base_problem_id"]), GROUPS.index(row["group"]), row["patch_type"]))
    classified_rollouts = [classify_rollout(row) for row in rollouts]
    classified_rollouts.sort(key=lambda row: (int(row["base_problem_id"]), row["condition"]))
    write_jsonl(OUT / "cutoff/per_problem_cutoff_results.jsonl", cutoff)
    write_jsonl(OUT / "cutoff/rollout_results.jsonl", classified_rollouts)
    write_jsonl(OUT / "patching/broad_prefix_patch_results.jsonl", [row for row in patches if row["group"] == "P_post_image"])
    write_jsonl(OUT / "patching/question_patch_results.jsonl", [row for row in patches if row["group"] == "Q"])
    write_jsonl(OUT / "patching/optional_group_patch_results.jsonl", [row for row in patches if row["group"] in {"T", "Q_plus_T"}])

    cutoff_stats = {
        "primary_unit": "base_problem_id",
        "n": 49,
        "all_frozen_bases_attempted": True,
        "CE_full": summarize_effect_values(finite_values(cutoff, "CE_full")),
        "CE_cut": summarize_effect_values(finite_values(cutoff, "CE_cut")),
        "CE_cut_controlled": summarize_effect_values(finite_values(cutoff, "CE_controlled_cut")),
        "sham_shift_cut": summarize_effect_values(finite_values(cutoff, "sham_shift_cut")),
        "retention_ratio_raw": summarize_effect_values(finite_values(cutoff, "retention_ratio_raw")),
        "retention_ratio_controlled_raw": summarize_effect_values(finite_values(cutoff, "retention_ratio_controlled_raw")),
        "positive_cutoff_CE": proportion_summary([float(row["CE_cut"]) > 0 for row in cutoff], seed=61_001),
        "positive_controlled_cutoff_CE": proportion_summary(
            [float(row["CE_controlled_cut"]) > 0 for row in cutoff], seed=61_002
        ),
        "rollout_automatic_mention_counts": {
            condition: {
                label: sum(
                    row["condition"] == condition and row["automatic_fact_mention"] == label
                    for row in classified_rollouts
                )
                for label in ("original_only", "counterfactual_only", "both", "neither_or_non_numeric")
            }
            for condition in ("original", "counterfactual", "sham")
        },
        "scoring_path": "full-sequence Stage 3A-compatible eager attention",
        "attention_used_for_selection": False,
    }
    write_json(OUT / "cutoff/cutoff_statistics.json", cutoff_stats)

    patch_stats = {
        "primary_unit": "base_problem_id",
        "n": 49,
        "normalization": "matched cached recipient/source no-patch evidence preferences",
        "recovery_values_unclipped": True,
        "groups": {group: patch_group_statistics(patches, group) for group in GROUPS},
    }
    cross_denominators = [
        abs(float(row["source_D_no_patch"] - row["recipient_D_no_patch"]))
        for row in patches
        if row["group"] == "Q" and row["patch_type"] == "cross_original_to_counterfactual"
    ]
    patch_stats["normalization_denominator_absolute"] = {
        "summary": summarize_effect_values(cross_denominators),
        "count_below_1e-6": int(sum(value < 1e-6 for value in cross_denominators)),
        "count_below_0.05": int(sum(value < 0.05 for value in cross_denominators)),
        "interpretation_guardrail": "Raw normalized recovery is retained for every problem; means can be unstable when the matched cutoff denominator is near zero, so medians and unnormalized oriented D shifts are primary summaries.",
    }
    write_json(OUT / "patching/patch_statistics.json", patch_stats)
    cutoff_by_base = {str(row["base_problem_id"]): row for row in cutoff}
    evidence_stats = {}
    for evidence_type in sorted({row["evidence_type"] for row in cutoff}):
        selected = [row for row in cutoff if row["evidence_type"] == evidence_type]
        bases = {str(row["base_problem_id"]) for row in selected}
        evidence_stats[evidence_type] = {
            "n": len(selected),
            "CE_cut": summarize_effect_values(finite_values(selected, "CE_cut")),
            "retention_ratio_raw": summarize_effect_values(finite_values(selected, "retention_ratio_raw")),
            "P_post_image_bidirectional_recovery": summarize_effect_values(
                [
                    row["mean_bidirectional_recovery_raw"]
                    for row in patch_stats["groups"]["P_post_image"]["per_base"]
                    if row["base_problem_id"] in bases
                ]
            ),
            "Q_bidirectional_recovery": summarize_effect_values(
                [
                    row["mean_bidirectional_recovery_raw"]
                    for row in patch_stats["groups"]["Q"]["per_base"]
                    if row["base_problem_id"] in bases
                ]
            ),
        }
    prefix_lengths = [float(row["prefix_token_count"]) for row in cutoff]
    rho_values = [float(row["retention_ratio_raw"]) for row in cutoff]
    ce_values = [float(row["CE_cut"]) for row in cutoff]
    evidence_analysis = {
        "primary_unit": "base_problem_id",
        "strata": evidence_stats,
        "strict_pre_e0_prefix_length_associations": {
            "prefix_length_vs_retention_spearman": {
                "rho": float(spearmanr(prefix_lengths, rho_values).statistic),
                "p_value": float(spearmanr(prefix_lengths, rho_values).pvalue),
            },
            "prefix_length_vs_cutoff_CE_spearman": {
                "rho": float(spearmanr(prefix_lengths, ce_values).statistic),
                "p_value": float(spearmanr(prefix_lengths, ce_values).pvalue),
            },
            "descriptive_only": True,
        },
        "per_base_prefix_and_retention": [
            {
                "base_problem_id": base,
                "prefix_token_count": cutoff_by_base[base]["prefix_token_count"],
                "CE_cut": cutoff_by_base[base]["CE_cut"],
                "retention_ratio_raw": cutoff_by_base[base]["retention_ratio_raw"],
            }
            for base in sorted(cutoff_by_base, key=int)
        ],
    }
    write_json(OUT / "analysis/evidence_type_statistics.json", evidence_analysis)
    plot_results(cutoff, patches, patch_stats)
    write_json(
        OUT / "analysis/aggregation_validation.json",
        {
            "status": "PASS",
            "completed_shards": [path.name for path in shard_dirs],
            "frozen_bases": 49,
            "cutoff_rows": len(cutoff),
            "patch_rows": len(patches),
            "patch_rows_per_base": 24,
            "rollout_rows": len(classified_rollouts),
            "figure_count": len(list(FIGURES.glob("*.png"))),
            "unique_base_problem_ids": sorted(observed_bases, key=int),
        },
    )
    print(json.dumps({"cutoff": cutoff_stats, "patch_groups": {group: patch_stats["groups"][group]["bidirectional_recovery_raw"] for group in GROUPS}}, indent=2))


if __name__ == "__main__":
    main()
