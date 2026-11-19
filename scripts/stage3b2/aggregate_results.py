#!/usr/bin/env python3
"""Aggregate the frozen Stage 3B.2 cohort and generate causal timing analyses."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3a.metrics import bootstrap_interval, summarize_effect_values
from visual_reasoning.stage3b2.analysis import (
    checkpoint_passes_go_rule,
    match_switch_and_cutoff_timings,
    retrieval_category,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b2"
RAW = OUT / "raw/shards"
FIGURES = OUT / "analysis/figures"
SEED = 1_234
RESAMPLES = 10_000
RELATIVE_LABELS = tuple(
    ["generation_start"]
    + [f"Ed_minus_{value}" for value in (64, 32, 16, 8, 4, 2, 1)]
    + ["Ed"]
)
PROGRESS_LABELS = tuple(f"progress_{value}" for value in (0, 25, 50, 75, 90))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def finite(values: Iterable[float | None]) -> list[float]:
    result = [float(value) for value in values if value is not None]
    if not result or not all(math.isfinite(value) for value in result):
        raise ValueError("Expected at least one finite value")
    return result


def summary(values: Iterable[float | None], seed: int) -> dict[str, Any]:
    return summarize_effect_values(finite(values), seed=seed, resamples=RESAMPLES)


def proportion(values: Iterable[bool], seed: int) -> dict[str, Any]:
    array = np.asarray([bool(value) for value in values], dtype=np.float64)
    if not array.size:
        return {"count": 0, "n": 0, "proportion": None, "bootstrap_ci": None}
    return {
        "count": int(array.sum()),
        "n": int(array.size),
        "proportion": float(array.mean()),
        "bootstrap_ci": bootstrap_interval(
            array,
            statistic="mean",
            seed=seed,
            resamples=RESAMPLES,
        ),
    }


def compact_timing(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "switch_generated_index",
        "labels",
        "requested_coordinates",
        "tokens_before_ed",
        "actual_progress",
        "D_OO",
        "D_OC",
        "D_CC",
        "D_CO",
        "D_OS",
        "S_O_to_C",
        "S_C_to_O",
        "BRI",
        "S_O_to_Sham",
        "O_to_C_source_consistent",
        "C_to_O_source_consistent",
        "bidirectionally_source_consistent",
        "normalized_BRI_raw",
        "normalized_S_O_to_C_raw",
        "normalized_S_C_to_O_raw",
        "normalized_sham_raw",
        "normalization_valid",
        "self_O_exact",
        "self_C_exact",
        "all_switch_audits_valid",
        "all_finite",
    )
    return {key: row[key] for key in keys}


def checkpoint_statistics(results: list[dict[str, Any]], label: str, seed: int) -> dict[str, Any]:
    selected = [
        (result, timing)
        for result in results
        for timing in result["timing"]
        if label in timing["labels"]
    ]
    if not selected:
        return {"label": label, "n": 0}
    timings = [timing for _, timing in selected]
    normalized = [timing["normalized_BRI_raw"] for timing in timings]
    normalized_valid = [value for value in normalized if value is not None]
    return {
        "label": label,
        "n": len(timings),
        "S_O_to_C": summary((row["S_O_to_C"] for row in timings), seed),
        "S_C_to_O": summary((row["S_C_to_O"] for row in timings), seed + 10),
        "BRI": summary((row["BRI"] for row in timings), seed + 20),
        "S_O_to_Sham": summary((row["S_O_to_Sham"] for row in timings), seed + 30),
        "normalized_BRI_raw": summary(normalized_valid, seed + 40),
        "normalization_valid_count": len(normalized_valid),
        "O_to_C_source_consistency": proportion(
            (row["O_to_C_source_consistent"] for row in timings), seed + 50
        ),
        "C_to_O_source_consistency": proportion(
            (row["C_to_O_source_consistent"] for row in timings), seed + 60
        ),
        "bidirectional_source_consistency": proportion(
            (row["bidirectionally_source_consistent"] for row in timings), seed + 70
        ),
        "median_absolute_S_O_to_C": float(np.median([abs(row["S_O_to_C"]) for row in timings])),
        "median_absolute_sham": float(np.median([abs(row["S_O_to_Sham"]) for row in timings])),
        "median_absolute_sham_to_target_ratio": float(
            np.median([abs(row["S_O_to_Sham"]) for row in timings])
            / np.median([abs(row["S_O_to_C"]) for row in timings])
        ),
        "all_self_switches_exact": all(
            row["self_O_exact"] and row["self_C_exact"] for row in timings
        ),
        "all_switch_audits_valid": all(row["all_switch_audits_valid"] for row in timings),
        "per_base": [
            {
                "base_problem_id": result["base_problem_id"],
                "switch_generated_index": timing["switch_generated_index"],
                "tokens_before_ed": timing["tokens_before_ed"],
                "actual_progress": timing["actual_progress"],
                "S_O_to_C": timing["S_O_to_C"],
                "S_C_to_O": timing["S_C_to_O"],
                "BRI": timing["BRI"],
                "S_O_to_Sham": timing["S_O_to_Sham"],
                "normalized_BRI_raw": timing["normalized_BRI_raw"],
                "bidirectionally_source_consistent": timing[
                    "bidirectionally_source_consistent"
                ],
            }
            for result, timing in selected
        ],
    }


def replay_diagnostic(
    results: list[dict[str, Any]],
    annotations: dict[str, dict[str, Any]],
    stage3a: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    per_base = []
    for result in results:
        base = str(result["base_problem_id"])
        start = int(annotations[base]["common_prefix_token_count"])
        differences = []
        token_ids_equal = True
        for condition in ("original", "counterfactual", "sham"):
            for candidate in ("original_candidate", "counterfactual_candidate"):
                observed = result["no_switch"][condition][candidate]
                expected = stage3a[base]["condition_scores"][condition][candidate]
                expected_ids = expected["candidate_token_ids"][start:]
                expected_probs = expected["token_log_probabilities"][start:]
                token_ids_equal = token_ids_equal and observed["candidate_token_ids"] == expected_ids
                differences.extend(
                    abs(float(left) - float(right))
                    for left, right in zip(observed["token_log_probabilities"], expected_probs)
                )
        maximum = max(differences, default=0.0)
        per_base.append(
            {
                "base_problem_id": base,
                "bit_exact": bool(result["stage3a_divergent_tail_exact"]),
                "token_ids_equal": token_ids_equal,
                "maximum_absolute_log_probability_difference": maximum,
                "within_1e_minus_6": token_ids_equal and maximum <= 1e-6,
            }
        )
    return {
        "definition": "Stage 3B.2 no-switch divergent suffix versus the matching frozen Stage 3A suffix",
        "bit_exact_base_count": sum(row["bit_exact"] for row in per_base),
        "within_1e_minus_6_base_count": sum(row["within_1e_minus_6"] for row in per_base),
        "maximum_absolute_log_probability_difference": max(
            row["maximum_absolute_log_probability_difference"] for row in per_base
        ),
        "exceptions": [row for row in per_base if not row["bit_exact"]],
        "per_base": per_base,
    }


def cutoff_comparison(results: list[dict[str, Any]]) -> dict[str, Any]:
    stage3b1 = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b1/scoring/per_problem_timing_results.jsonl")
    }
    matches = []
    latest = []
    for result in results:
        base = str(result["base_problem_id"])
        joined = match_switch_and_cutoff_timings(result["timing"], stage3b1[base]["timing"])
        base_rows = []
        for item in joined:
            switch = item["switch"]
            cutoff = item["cutoff"]
            damage_ratio = 1.0 - float(cutoff["retention_ratio_raw"])
            normalized_switch = switch["normalized_BRI_raw"]
            high_cutoff = damage_ratio >= 0.50
            high_switch = normalized_switch is not None and float(normalized_switch) >= 0.50
            quadrant = (
                "high_cutoff_damage_high_switch"
                if high_cutoff and high_switch
                else "high_cutoff_damage_low_switch"
                if high_cutoff
                else "low_cutoff_damage_high_switch"
                if high_switch
                else "low_cutoff_damage_low_switch"
            )
            row = {
                "base_problem_id": base,
                "generated_index": item["generated_index"],
                "stage3b1_labels": cutoff["labels"],
                "stage3b2_labels": switch["labels"],
                "stage3b1_cutoff_damage": float(stage3b1[base]["CE_full"] - cutoff["CE"]),
                "stage3b1_cutoff_damage_ratio": damage_ratio,
                "stage3b2_BRI": switch["BRI"],
                "stage3b2_normalized_BRI": normalized_switch,
                "quadrant_at_reference_threshold_0_50": quadrant,
            }
            matches.append(row)
            base_rows.append(row)
        latest.append(max(base_rows, key=lambda row: row["generated_index"]))
    valid_pairs = [
        row
        for row in matches
        if row["stage3b2_normalized_BRI"] is not None
        and math.isfinite(row["stage3b1_cutoff_damage_ratio"])
    ]
    correlation = spearmanr(
        [row["stage3b1_cutoff_damage_ratio"] for row in valid_pairs],
        [row["stage3b2_normalized_BRI"] for row in valid_pairs],
    )
    valid_latest = [row for row in latest if row["stage3b2_normalized_BRI"] is not None]
    latest_correlation = spearmanr(
        [row["stage3b1_cutoff_damage_ratio"] for row in valid_latest],
        [row["stage3b2_normalized_BRI"] for row in valid_latest],
    )
    return {
        "comparison_rule": "exact identical generated-query index only",
        "matched_problem_checkpoint_count": len(matches),
        "matched_base_problem_count": len({row["base_problem_id"] for row in matches}),
        "matches_per_base_distribution": dict(
            sorted(Counter(Counter(row["base_problem_id"] for row in matches).values()).items())
        ),
        "quadrant_reference_threshold": 0.50,
        "quadrant_threshold_is_descriptive_not_a_decision_rule": True,
        "latest_exact_match_per_base_quadrants": dict(
            sorted(Counter(row["quadrant_at_reference_threshold_0_50"] for row in latest).items())
        ),
        "spearman_all_exact_matches": {
            "rho": float(correlation.statistic),
            "p_value": float(correlation.pvalue),
            "n": len(valid_pairs),
            "warning": "Problem-checkpoint rows are repeated within base problems; this is descriptive only.",
        },
        "spearman_latest_exact_match_per_base": {
            "rho": float(latest_correlation.statistic),
            "p_value": float(latest_correlation.pvalue),
            "n": len(valid_latest),
            "unit": "one latest exact matched checkpoint per base_problem_id",
        },
        "latest_exact_match_per_base": latest,
        "all_exact_matches": matches,
    }


def evidence_analysis(results: list[dict[str, Any]]) -> dict[str, Any]:
    strata = {}
    for evidence_type in sorted({row["evidence_type"] for row in results}):
        subset = [row for row in results if row["evidence_type"] == evidence_type]
        strata[evidence_type] = {
            "n": len(subset),
            "retrieval_categories": dict(
                sorted(Counter(row["retrieval_timing_category"] for row in subset).items())
            ),
            "Ed_minus_1": checkpoint_statistics(subset, "Ed_minus_1", SEED + 40_000),
            "Ed": checkpoint_statistics(subset, "Ed", SEED + 41_000),
            "normalized_progress_median_BRI": {
                label: checkpoint_statistics(subset, label, SEED + 42_000 + index * 100)[
                    "normalized_BRI_raw"
                ]["median"]
                for index, label in enumerate(PROGRESS_LABELS)
            },
        }
    alignment_strata = {}
    for alignment in sorted({row["ed_alignment"] for row in results}):
        subset = [row for row in results if row["ed_alignment"] == alignment]
        alignment_strata[alignment] = {
            "n": len(subset),
            "Ed_minus_1": checkpoint_statistics(subset, "Ed_minus_1", SEED + 44_000),
            "Ed": checkpoint_statistics(subset, "Ed", SEED + 45_000),
        }
    return {
        "primary_unit": "base_problem_id",
        "strata": strata,
        "annotation_alignment_strata": alignment_strata,
        "structural_stratum_is_small": len(
            [row for row in results if row["evidence_type"] == "tier3_structural_visual_edit"]
        )
        == 4,
    }


def attention_comparison(results: list[dict[str, Any]]) -> dict[str, Any]:
    stage3b1_attention = read_json(
        ROOT / "outputs/stage3b1/analysis/attention_timing_comparison.json"
    )
    stage3a_attention = read_json(
        ROOT / "outputs/stage3a/analysis/attention_moderator_analysis.json"
    )
    density = {
        str(row["base_problem_id"]): row for row in stage3a_attention["matched_rows"]
    }
    results_by_base = {str(row["base_problem_id"]): row for row in results}
    matched = []
    for event in stage3b1_attention["matched_rows"]:
        base = str(event["base_problem_id"])
        result = results_by_base[base]
        ed_minus_1 = next(row for row in result["timing"] if "Ed_minus_1" in row["labels"])
        ed = next(row for row in result["timing"] if "Ed" in row["labels"])
        matched.append(
            {
                "base_problem_id": base,
                "example_id": event["example_id"],
                "evidence_id": event["evidence_id"],
                "stage2c_timing_category": event["stage2c_timing_category"],
                "attention_peak_generated_index": event["attention_peak_generated_index"],
                "attention_peak_offset_from_e0": event["attention_peak_offset_from_e0"],
                "pre_e0_roi_density": density[base]["pre_e0_roi_density"],
                "Ed_minus_1_BRI": ed_minus_1["BRI"],
                "Ed_minus_1_normalized_BRI": ed_minus_1["normalized_BRI_raw"],
                "Ed_minus_1_bidirectional": ed_minus_1[
                    "bidirectionally_source_consistent"
                ],
                "Ed_BRI": ed["BRI"],
                "Ed_normalized_BRI": ed["normalized_BRI_raw"],
                "Ed_bidirectional": ed["bidirectionally_source_consistent"],
            }
        )

    def correlation(x_key: str, y_key: str) -> dict[str, Any] | None:
        rows = [row for row in matched if row[x_key] is not None and row[y_key] is not None]
        if len(rows) < 3:
            return None
        statistic = spearmanr([row[x_key] for row in rows], [row[y_key] for row in rows])
        return {"rho": float(statistic.statistic), "p_value": float(statistic.pvalue), "n": len(rows)}

    return {
        "analysis_role": "secondary exact Stage 2C event overlap after primary Stage 3B.2 scores were frozen",
        "matched_problem_count": len(matched),
        "unmatched_problem_count": len(results) - len(matched),
        "matched_rows": matched,
        "timing_category_counts": dict(
            sorted(Counter(row["stage2c_timing_category"] for row in matched).items())
        ),
        "pre_e0_roi_density_vs_Ed_minus_1_normalized_BRI": correlation(
            "pre_e0_roi_density", "Ed_minus_1_normalized_BRI"
        ),
        "pre_e0_roi_density_vs_Ed_normalized_BRI": correlation(
            "pre_e0_roi_density", "Ed_normalized_BRI"
        ),
        "mention_centered_with_bidirectional_Ed_source_control": sum(
            row["stage2c_timing_category"] == "T2_mention_centered" and row["Ed_bidirectional"]
            for row in matched
        ),
        "attention_is_descriptive_not_causal": True,
        "small_overlap_limits_inference": True,
    }


def aggregate_rollouts(expected_bases: set[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    shard_dirs = sorted(
        path
        for path in (OUT / "raw/rollouts").glob("cohort_*")
        if (path / "result.json").is_file()
    )
    if len(shard_dirs) != 7:
        raise RuntimeError(f"Expected 7 completed rollout shards, observed {len(shard_dirs)}")
    rows = [row for path in shard_dirs for row in read_jsonl(path / "rollout_results.jsonl")]
    if {str(row["base_problem_id"]) for row in rows} != expected_bases:
        raise RuntimeError("Rollout aggregation does not exactly cover the frozen cohort")
    switched_conditions = ("O_history_C_vision", "O_history_sham_vision", "C_history_O_vision")
    audits = [row["conditions"][condition]["switch_audit"] for row in rows for condition in switched_conditions]
    if not all(
        audit["layers"] == list(range(36))
        and audit["queries_before_switch_modified"] == 0
        and audit["nonvisual_key_value_entries_replaced"] == 0
        for audit in audits
    ):
        raise RuntimeError("A rollout visual-source switch audit failed")
    summaries = {}
    for label in ("Ed_minus_16", "Ed_minus_4", "Ed"):
        selected = [row for row in rows if row["checkpoint_label"] == label]
        classifications = {
            condition: dict(
                sorted(
                    Counter(
                        row["conditions"][condition][
                            "first_discriminative_token_classification"
                        ]
                        for row in selected
                    ).items()
                )
            )
            for condition in (
                "O_history_O_vision",
                "O_history_C_vision",
                "O_history_sham_vision",
                "C_history_O_vision",
            )
        }
        summaries[label] = {
            "n": len(selected),
            "O_to_C_overrides_old_identity": proportion(
                (row["O_to_C_overrides_old_identity"] for row in selected),
                SEED + 50_000 + len(selected),
            ),
            "C_to_O_overrides_old_identity": proportion(
                (row["C_to_O_overrides_old_identity"] for row in selected),
                SEED + 51_000 + len(selected),
            ),
            "first_discriminative_token_classifications": classifications,
        }
    raw_summaries = [read_json(path / "result.json") for path in shard_dirs]
    return rows, {
        "analysis_role": "secondary matched-seed behavioral validation; one rollout is not a frequency estimate",
        "base_problem_count": len(expected_bases),
        "rollout_checkpoint_count": len(rows),
        "condition_rollout_count": 4 * len(rows),
        "all_capture_layers_valid": all(row["capture_all_layers_valid"] for row in rows),
        "all_switch_audits_valid": True,
        "peak_gpu_allocated_bytes": max(row["peak_gpu_allocated_bytes"] for row in raw_summaries),
        "by_checkpoint": summaries,
    }


def plot_results(
    results: list[dict[str, Any]],
    checkpoints: dict[str, Any],
    cutoff: dict[str, Any],
    evidence: dict[str, Any],
    attention: dict[str, Any],
) -> None:
    ensure_directory(FIGURES)
    relative = [label for label in RELATIVE_LABELS if label.startswith("Ed_") or label == "Ed"]
    x_relative = np.asarray(
        [-int(label.split("_")[-1]) if "minus" in label else 0 for label in relative],
        dtype=float,
    )
    relative_stats = [checkpoints["ed_relative"][label] for label in relative]

    fig, ax = plt.subplots(figsize=(7.5, 4.7))
    ax.plot(x_relative, [row["S_O_to_C"]["median"] for row in relative_stats], marker="o", label="O history + C vision")
    ax.plot(x_relative, [row["S_C_to_O"]["median"] for row in relative_stats], marker="s", label="C history + O vision")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set(xlabel="Switch time relative to E_d (tokens)", ylabel="Median source-consistent shift", title="Bidirectional source-switch effects")
    ax.legend(); fig.tight_layout(); fig.savefig(FIGURES / "01_bidirectional_switch_effect_vs_ed.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.7))
    med = np.asarray([row["BRI"]["median"] for row in relative_stats])
    low = np.asarray([row["BRI"]["median_bootstrap_ci"]["ci_low"] for row in relative_stats])
    high = np.asarray([row["BRI"]["median_bootstrap_ci"]["ci_high"] for row in relative_stats])
    ax.plot(x_relative, med, marker="o"); ax.fill_between(x_relative, low, high, alpha=0.2); ax.axhline(0, color="gray", linewidth=0.8)
    ax.set(xlabel="Switch time relative to E_d (tokens)", ylabel="Median BRI (unnormalized)", title="Cohort evidence-identity retrieval curve")
    fig.tight_layout(); fig.savefig(FIGURES / "02_cohort_bri_vs_ed.png", dpi=180); plt.close(fig)

    x_progress = np.asarray([0, 0.25, 0.5, 0.75, 0.9])
    progress_stats = [checkpoints["normalized_progress"][label] for label in PROGRESS_LABELS]
    fig, ax = plt.subplots(figsize=(7.5, 4.7))
    ax.plot(x_progress, [row["BRI"]["median"] for row in progress_stats], marker="o", label="Unnormalized BRI")
    ax2 = ax.twinx(); ax2.plot(x_progress, [row["normalized_BRI_raw"]["median"] for row in progress_stats], marker="s", color="#d95f02", label="Normalized BRI")
    ax.set(xlabel="Normalized progress to E_d", ylabel="Median BRI"); ax2.set_ylabel("Median normalized BRI")
    ax.set_title("Source control across normalized reasoning progress"); fig.tight_layout(); fig.savefig(FIGURES / "03_bri_vs_normalized_progress.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for result in results:
        ax.plot([row["actual_progress"] for row in result["timing"]], [row["normalized_BRI_raw"] for row in result["timing"]], alpha=0.25, linewidth=0.8)
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8); ax.set(xlabel="Actual progress to E_d", ylabel="Normalized BRI (secondary)", title="All 49 unsmoothed per-problem retrieval curves")
    fig.tight_layout(); fig.savefig(FIGURES / "04_per_problem_retrieval_curves.png", dpi=180); plt.close(fig)

    ed1 = [next(row for row in result["timing"] if "Ed_minus_1" in row["labels"]) for result in results]
    fig, ax = plt.subplots(figsize=(6, 5)); ax.scatter([row["S_O_to_Sham"] for row in ed1], [row["S_O_to_C"] for row in ed1], alpha=0.75)
    ax.axhline(0, color="gray", linewidth=0.8); ax.axvline(0, color="gray", linewidth=0.8); ax.set(xlabel="O→sham effect at E_d−1", ylabel="O→C effect at E_d−1", title="Target switch dominates sham source switch")
    fig.tight_layout(); fig.savefig(FIGURES / "05_target_vs_sham_effect.png", dpi=180); plt.close(fig)

    latest = [row for row in cutoff["latest_exact_match_per_base"] if row["stage3b2_normalized_BRI"] is not None]
    fig, ax = plt.subplots(figsize=(6, 5)); ax.scatter([row["stage3b1_cutoff_damage_ratio"] for row in latest], [row["stage3b2_normalized_BRI"] for row in latest], alpha=0.75)
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8); ax.axvline(0.5, color="gray", linestyle="--", linewidth=0.8); ax.set(xlabel="Stage 3B.1 cutoff-damage ratio", ylabel="Stage 3B.2 normalized BRI", title="Latest exact shared checkpoint per base")
    fig.tight_layout(); fig.savefig(FIGURES / "06_cutoff_damage_vs_switch_effect.png", dpi=180); plt.close(fig)

    representatives = []
    for category in sorted({row["retrieval_timing_category"] for row in results}):
        candidates = [row for row in results if row["retrieval_timing_category"] == category]
        representatives.append(candidates[len(candidates) // 2])
    fig, ax = plt.subplots(figsize=(7.5, 4.7))
    for result in representatives:
        ax.plot([row["actual_progress"] for row in result["timing"]], [row["normalized_BRI_raw"] for row in result["timing"]], marker="o", markersize=3, label=f"{result['retrieval_timing_category'].split('_')[0]}: {result['base_problem_id']}")
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8); ax.set(xlabel="Actual progress to E_d", ylabel="Normalized BRI", title="Observed frozen retrieval-timing categories"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIGURES / "07_retrieval_category_examples.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.5, 4.7))
    for evidence_type, color in (("tier1_local_numeric_label", "#4472c4"), ("tier3_structural_visual_edit", "#ed7d31")):
        stratum = evidence["strata"][evidence_type]
        ax.plot(x_progress, [stratum["normalized_progress_median_BRI"][label] for label in PROGRESS_LABELS], marker="o", color=color, label=f"{evidence_type} (N={stratum['n']})")
    ax.set(xlabel="Normalized progress to E_d", ylabel="Median normalized BRI", title="Source control by evidence stratum"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIGURES / "08_numeric_vs_structural.png", dpi=180); plt.close(fig)

    representatives = sorted(results, key=lambda row: next(point for point in row["timing"] if "Ed" in point["labels"])["BRI"], reverse=True)[:8]
    names = [str(row["base_problem_id"]) for row in representatives]
    original = [next(point for point in row["timing"] if "Ed" in point["labels"])["D_OO"] for row in representatives]
    switched = [next(point for point in row["timing"] if "Ed" in point["labels"])["D_OC"] for row in representatives]
    x = np.arange(len(names)); width = 0.38
    fig, ax = plt.subplots(figsize=(8, 4.8)); ax.bar(x - width / 2, original, width, label="O history + O vision"); ax.bar(x + width / 2, switched, width, label="O history + C vision")
    ax.axhline(0, color="gray", linewidth=0.8); ax.set_xticks(x, names); ax.set(xlabel="Base problem", ylabel="Original-minus-counterfactual preference D", title="Representative E_d evidence-preference flips"); ax.legend()
    fig.tight_layout(); fig.savefig(FIGURES / "09_representative_fact_flips.png", dpi=180); plt.close(fig)


def main() -> None:
    config = read_json(OUT / "config/stage3b2_config.json")
    expected = read_jsonl(OUT / "config/cohort_manifest.jsonl")
    schedules = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "config/switch_checkpoint_schedule.jsonl")}
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "annotations/discriminative_event_annotations.jsonl")}
    stage3a = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3a/scoring/fact_preference.jsonl")}
    expected_bases = {str(row["base_problem_id"]) for row in expected}
    shard_dirs = sorted(path for path in RAW.glob("cohort_*") if (path / "result.json").is_file())
    if len(shard_dirs) != 7:
        raise RuntimeError(f"Expected 7 completed shards, observed {len(shard_dirs)}")
    raw_results = [row for path in shard_dirs for row in read_jsonl(path / "switch_results.jsonl")]
    if len(raw_results) != 49 or {str(row["base_problem_id"]) for row in raw_results} != expected_bases:
        raise RuntimeError("Switch aggregation does not exactly cover the frozen 49-base cohort")
    if sum(len(row["timing"]) for row in raw_results) != 588:
        raise RuntimeError("Switch aggregation does not contain the frozen 588 checkpoints")
    for result in raw_results:
        frozen = schedules[str(result["base_problem_id"])]["checkpoints"]
        observed = result["timing"]
        if [(row["switch_generated_index"], row["labels"]) for row in observed] != [
            (row["switch_generated_index"], row["labels"]) for row in frozen
        ]:
            raise RuntimeError(f"Schedule mismatch for base {result['base_problem_id']}")
    if not all(row["capture_all_layers_valid"] and row["condition_layout_exact"] for row in raw_results):
        raise RuntimeError("A full-cohort capture/layout audit failed")
    if not all(point["all_switch_audits_valid"] and point["all_finite"] for row in raw_results for point in row["timing"]):
        raise RuntimeError("A switch boundary or finiteness audit failed")
    if not all(point["self_O_exact"] and point["self_C_exact"] for row in raw_results for point in row["timing"]):
        raise RuntimeError("A self-source switch was not transparent")

    replay = replay_diagnostic(raw_results, annotations, stage3a)
    if replay["within_1e_minus_6_base_count"] != 49:
        raise RuntimeError("A no-switch Stage 3A suffix replay exceeded numerical tolerance")

    results = []
    for row in sorted(raw_results, key=lambda value: int(value["base_problem_id"])):
        compact = {
            key: row[key]
            for key in (
                "base_problem_id",
                "example_id",
                "evidence_type",
                "prefix_sha256",
                "e0_start_token",
                "ed_generated_index",
                "ed_alignment",
                "prompt_token_count",
                "visual_token_count",
                "condition_layout_exact",
                "selection_used_attention",
                "no_switch_evidence_gap",
                "capture_all_layers_valid",
                "stage3a_divergent_tail_exact",
            )
        }
        compact["no_switch"] = {
            condition: {
                "L_o": row["no_switch"][condition]["L_o"],
                "L_c": row["no_switch"][condition]["L_c"],
                "D": row["no_switch"][condition]["D"],
            }
            for condition in ("original", "counterfactual", "sham")
        }
        compact["timing"] = [compact_timing(point) for point in row["timing"]]
        compact["retrieval_timing_category"] = retrieval_category(compact["timing"])
        results.append(compact)

    ensure_directory(OUT / "scoring")
    ensure_directory(OUT / "analysis")
    write_jsonl(OUT / "scoring/per_problem_switch_results.jsonl", results)
    checkpoint = {
        "primary_unit": "base_problem_id",
        "primary_metric": "unnormalized BRI",
        "normalization_is_secondary": True,
        "ed_relative": {
            label: checkpoint_statistics(results, label, SEED + 10_000 + index * 100)
            for index, label in enumerate(RELATIVE_LABELS)
        },
        "normalized_progress": {
            label: checkpoint_statistics(results, label, SEED + 20_000 + index * 100)
            for index, label in enumerate(PROGRESS_LABELS)
        },
    }
    write_json(OUT / "scoring/per_checkpoint_statistics.json", checkpoint)

    curves = {
        "primary_unit": "base_problem_id",
        "n": len(results),
        "primary_metric": "unnormalized BRI",
        "retrieval_category_counts": dict(sorted(Counter(row["retrieval_timing_category"] for row in results).items())),
        "ed_relative_checkpoint_statistics": checkpoint["ed_relative"],
        "normalized_progress_checkpoint_statistics": checkpoint["normalized_progress"],
        "curves": [
            {
                "base_problem_id": row["base_problem_id"],
                "evidence_type": row["evidence_type"],
                "retrieval_timing_category": row["retrieval_timing_category"],
                "points": row["timing"],
            }
            for row in results
        ],
    }
    write_json(OUT / "analysis/retrieval_timing_curves.json", curves)

    late = {label: checkpoint["ed_relative"][label] for label in ("Ed_minus_1", "Ed")}
    early = {
        label: checkpoint["ed_relative"][label]
        for label in ("Ed_minus_64", "Ed_minus_32", "Ed_minus_16")
        if checkpoint["ed_relative"][label]["n"]
    }
    late_passing = [label for label, value in late.items() if checkpoint_passes_go_rule(value)]
    early_passing = [label for label, value in early.items() if checkpoint_passes_go_rule(value)]
    late_normalized_median = max(value["normalized_BRI_raw"]["median"] for value in late.values())
    if late_passing:
        decision = "GO — Layer-wise visual-to-reasoning transfer analysis"
    elif early_passing and late_normalized_median < 0.25:
        decision = "GO — Earlier commitment / non-visual carrier analysis"
    else:
        decision = "REDIRECT — Generic/distributed visual dependence"
    bidirectional = {
        "primary_unit": "base_problem_id",
        "late_checkpoints": late,
        "early_checkpoints": early,
        "retrieval_category_counts": curves["retrieval_category_counts"],
        "frozen_decision_rule": config["decision_rules"],
        "late_passing_checkpoints": late_passing,
        "early_passing_checkpoints": early_passing,
        "prospective_decision": decision,
    }
    write_json(OUT / "analysis/bidirectional_retrieval_statistics.json", bidirectional)

    cutoff = cutoff_comparison(results)
    write_json(OUT / "analysis/cutoff_vs_switch_comparison.json", cutoff)
    evidence = evidence_analysis(results)
    write_json(OUT / "analysis/evidence_type_analysis.json", evidence)
    validation = {
        "frozen_base_problem_count": len(expected_bases),
        "attempted_base_problem_count": len(results),
        "problem_checkpoint_count": sum(len(row["timing"]) for row in results),
        "all_capture_layers_valid": all(row["capture_all_layers_valid"] for row in results),
        "all_switch_audits_valid": all(point["all_switch_audits_valid"] for row in results for point in row["timing"]),
        "all_self_switches_exact": all(point["self_O_exact"] and point["self_C_exact"] for row in results for point in row["timing"]),
        "all_finite": all(point["all_finite"] for row in results for point in row["timing"]),
        "stage3a_suffix_replay": replay,
        "peak_gpu_allocated_bytes": max(read_json(path / "result.json")["peak_gpu_allocated_bytes"] for path in shard_dirs),
        "attention_used_for_selection_or_checkpoint_placement": False,
        "prohibited_localization_started": False,
    }
    write_json(OUT / "analysis/aggregation_validation.json", validation)

    rollout_rows, rollout_summary = aggregate_rollouts(expected_bases)
    write_jsonl(OUT / "scoring/rollout_results.jsonl", rollout_rows)
    write_json(OUT / "scoring/rollout_summary.json", rollout_summary)

    # The primary causal artifacts above are persisted before this secondary attention join.
    attention = attention_comparison(results)
    write_json(OUT / "analysis/attention_secondary_comparison.json", attention)
    plot_results(results, checkpoint, cutoff, evidence, attention)
    print(json.dumps({"bases": len(results), "checkpoints": sum(len(row["timing"]) for row in results), "decision": decision, "late_passing": late_passing}, indent=2))


if __name__ == "__main__":
    main()
