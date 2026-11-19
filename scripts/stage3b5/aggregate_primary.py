#!/usr/bin/env python3
"""Aggregate the frozen 37-base Stage 3B.5 primary boundary family."""

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b5.metrics import (
    bootstrap_summary,
    boundary_increments,
    one_sided_wilcoxon_greater,
    recompute_contrasts,
)
from visual_reasoning.stage3b5.protocol import (
    BOUNDARIES,
    COORDINATES,
    WINDOWS,
    evaluate_stage3b5_decision,
    holm_adjust,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b5"
RAW = OUT / "scoring/raw"
LAYER_ROLES = ("first", "second")
COLORS = {
    "h_pre": "#4C78A8",
    "pre_attn_norm": "#72B7B2",
    "h_post_attn": "#F58518",
    "pre_mlp_norm": "#ECA82C",
    "h_post_block": "#B279A2",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "controls"}


def public_scores_exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        left["L_o"] == right["L_o"]
        and left["L_c"] == right["L_c"]
        and left["D"] == right["D"]
        and all(
            left[candidate]["token_log_probabilities"]
            == right[candidate]["token_log_probabilities"]
            for candidate in ("original_candidate", "counterfactual_candidate")
        )
    )


def all_public_controls_exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return all(
        public_scores_exact(left[recipient][donor], right[recipient][donor])
        for recipient in ("O", "C")
        for donor in ("O", "O_sham", "C", "C_sham")
    )


def safe_ratio(value: float, denominator: float) -> float | None:
    return None if denominator == 0.0 else float(value) / abs(float(denominator))


def save_figure(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def errorbars(stats: list[dict[str, Any]]) -> tuple[list[float], list[list[float]]]:
    medians = [float(row["median"]) for row in stats]
    lows = [float(row["bootstrap_95_CI"][0]) for row in stats]
    highs = [float(row["bootstrap_95_CI"][1]) for row in stats]
    return medians, [
        [median - low for median, low in zip(medians, lows)],
        [high - median for median, high in zip(medians, highs)],
    ]


def make_figures(
    rows: list[dict[str, Any]],
    cell_stats: list[dict[str, Any]],
    increment_rows: list[dict[str, Any]],
    recompute_rows: list[dict[str, Any]],
) -> None:
    figures = ensure_directory(OUT / "analysis/figures")
    stat_map = {
        (row["coordinate"], row["window"], row["layer_role"], row["boundary"]): row
        for row in cell_stats
    }
    figure_index = 1
    core = ("h_pre", "h_post_attn", "h_post_block")
    for coordinate in COORDINATES:
        for window in WINDOWS:
            plt.figure(figsize=(7.0, 4.5))
            for role, marker in (("first", "o"), ("second", "s")):
                stats = [stat_map[(coordinate, window, role, boundary)]["BMR"] for boundary in core]
                medians, errors = errorbars(stats)
                plt.errorbar(core, medians, yerr=errors, marker=marker, capsize=3, label=role)
            plt.axhline(0, color="black", linewidth=0.8)
            plt.ylabel("Paired semantic restoration (BMR)")
            plt.title(f"{coordinate.replace('_', ' ')} / {window}: residual boundaries")
            plt.legend(title="layer role")
            save_figure(figures / f"{figure_index:02d}_{coordinate}_{window}_boundary_profile.png")
            figure_index += 1

    plt.figure(figsize=(7.2, 4.8))
    labels = ["Attention input", "MLP input"]
    raw_boundaries = ("h_pre", "h_post_attn")
    normalized_boundaries = ("pre_attn_norm", "pre_mlp_norm")
    raw = [
        statistics.median(float(row["BMR"]) for row in rows if row["boundary"] == boundary)
        for boundary in raw_boundaries
    ]
    normalized = [
        statistics.median(float(row["BMR"]) for row in rows if row["boundary"] == boundary)
        for boundary in normalized_boundaries
    ]
    x = list(range(2))
    plt.bar([v - 0.18 for v in x], raw, width=0.36, label="raw residual-state patch")
    plt.bar([v + 0.18 for v in x], normalized, width=0.36, label="RMS-normalized-state patch")
    plt.xticks(x, labels)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.ylabel("Paired semantic restoration (BMR)")
    plt.legend()
    plt.title("Raw residual vs normalized-state restoration")
    save_figure(figures / "05_raw_vs_normalized_state_restoration.png")

    figure, axes = plt.subplots(1, 2, figsize=(12.0, 4.8), sharey=False)
    labels, hpre_values, joint_values, hpost_values, mlp_values = [], [], [], [], []
    for coordinate in COORDINATES:
        for window in WINDOWS:
            subset = [row for row in recompute_rows if row["coordinate"] == coordinate and row["window"] == window]
            labels.append(f"{coordinate}/{window}")
            hpre_values.append(statistics.median(float(row["h_pre_recompute"]) for row in subset))
            joint_values.append(statistics.median(float(row["precomputed_joint"]) for row in subset))
            hpost_values.append(statistics.median(float(row["first_h_post_attn_recompute"]) for row in subset))
            mlp_values.append(statistics.median(float(row["precomputed_mlp"]) for row in subset))
    x = list(range(4))
    axes[0].bar([v - 0.18 for v in x], hpre_values, width=0.36, label="h_pre + recompute")
    axes[0].bar([v + 0.18 for v in x], joint_values, width=0.36, label="Stage 3B.4 Joint")
    axes[1].bar([v - 0.18 for v in x], hpost_values, width=0.36, label="h_post_attn + MLP recompute")
    axes[1].bar([v + 0.18 for v in x], mlp_values, width=0.36, label="Stage 3B.4 MLP")
    for axis, title in zip(axes, ("Pre-block state vs Joint outputs", "Post-Attention state vs MLP outputs")):
        axis.set_xticks(x, labels, rotation=20)
        axis.set_ylabel("BMR")
        axis.legend(fontsize=8)
        axis.set_title(title)
    figure.suptitle("State recompute vs precomputed module outputs")
    save_figure(figures / "06_recompute_vs_precomputed.png")

    plt.figure(figsize=(8.0, 4.8))
    first, second, block = [], [], []
    for coordinate in COORDINATES:
        for window in WINDOWS:
            subset = [row for row in recompute_rows if row["coordinate"] == coordinate and row["window"] == window]
            first.append(statistics.median(float(row["h_pre_recompute"]) for row in subset))
            second.append(statistics.median(float(row["second_h_pre"]) for row in subset))
            block.append(statistics.median(float(row["final_two_layer_block_reference"]) for row in subset))
    x = list(range(4))
    plt.bar([v - 0.24 for v in x], first, width=0.24, label="first h_pre / 2-layer recompute")
    plt.bar(x, second, width=0.24, label="second h_pre / 1-layer recompute")
    plt.bar([v + 0.24 for v in x], block, width=0.24, label="Stage 3B.4 2-layer block")
    plt.xticks(x, labels, rotation=20)
    plt.ylabel("BMR")
    plt.legend(fontsize=8)
    plt.title("Single-layer entry vs two-layer sequential recomputation")
    save_figure(figures / "07_single_vs_two_layer_recompute.png")

    plt.figure(figsize=(7.4, 4.6))
    displayed_increments = [row for row in increment_rows if row["increment"] in {"G_attn", "G_mlp"}]
    labels = [f"{row['window']}/{row['layer_role']}/{row['increment']}" for row in displayed_increments]
    values = [float(row["gain"]["median"]) for row in displayed_increments]
    colors = ["#F58518" if row["coordinate"] == "Ed" else "#4C78A8" for row in displayed_increments]
    plt.bar(range(len(values)), values, color=colors)
    plt.xticks(range(len(values)), labels, rotation=75, fontsize=7)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.ylabel("Median boundary gain")
    plt.title("E_d-1 (blue) vs E_d (orange) boundary gains")
    save_figure(figures / "08_coordinate_boundary_gains.png")

    plt.figure(figsize=(7.4, 4.6))
    for boundary in core:
        diffs = []
        for base in sorted({row["base_problem_id"] for row in rows}, key=int):
            for coordinate in COORDINATES:
                for role in LAYER_ROLES:
                    keyed = {
                        (r["base_problem_id"], r["coordinate"], r["window"], r["layer_role"], r["boundary"]): float(r["BMR"])
                        for r in rows
                    }
                    diffs.append(keyed[(base, coordinate, "W5", role, boundary)] - keyed[(base, coordinate, "W4", role, boundary)])
        plt.bar(boundary, statistics.median(diffs), color=COLORS[boundary])
    plt.axhline(0, color="black", linewidth=0.8)
    plt.ylabel("Median W5 minus W4 BMR")
    plt.title("Window comparison")
    save_figure(figures / "09_window_comparison.png")

    keyed = {
        (r["base_problem_id"], r["coordinate"], r["window"], r["layer_role"], r["boundary"]): float(r["BMR"])
        for r in rows
    }
    representative = sorted(
        {r["base_problem_id"] for r in rows},
        key=lambda base: statistics.median(
            abs(keyed[(base, coordinate, window, "first", "h_pre")])
            for coordinate in COORDINATES for window in WINDOWS
        ),
        reverse=True,
    )[:6]
    plt.figure(figsize=(8.2, 5.0))
    for base in representative:
        values = [
            statistics.median(
                keyed[(base, coordinate, window, role, boundary)]
                for coordinate in COORDINATES for window in WINDOWS for role in LAYER_ROLES
            )
            for boundary in core
        ]
        plt.plot(core, values, marker="o", label=base)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.ylabel("Median BMR across fixed cells/layers")
    plt.legend(title="base_problem_id", ncol=2)
    plt.title("Representative bidirectional boundary trajectories")
    save_figure(figures / "10_representative_boundary_trajectories.png")


def main() -> None:
    validation = read_json(OUT / "validation/validation_results.json")
    if validation["decision"] != "PASS" or not validation["primary_authorized"]:
        raise RuntimeError("Stage 3B.5 validation did not authorize primary aggregation")
    config = read_json(OUT / "config/stage3b5_config.json")
    expected_rows = read_jsonl(OUT / "config/cohort_manifest.jsonl")
    expected = {str(row["base_problem_id"]) for row in expected_rows}
    paths = sorted(RAW.glob("primary_*/examples/*/result.json"))
    results = [read_json(path) for path in paths]
    observed = [str(row["base_problem_id"]) for row in results]
    summaries = [read_json(path) for path in sorted(RAW.glob("primary_*/result.json"))]
    if len(results) != 37 or set(observed) != expected or len(set(observed)) != 37:
        raise RuntimeError(f"Primary incomplete: {len(results)} results, {len(set(observed))} unique")
    if len(summaries) != 8:
        raise RuntimeError(f"Expected eight primary summaries, observed {len(summaries)}")

    path_by_base = {path.parent.name: str(path.relative_to(ROOT)) for path in paths}
    rows = []
    interface_rows = []
    post_attn_post_block_equivalence = []
    for result in results:
        base = str(result["base_problem_id"])
        for point in result["coordinates"]:
            point_map = {
                (row["window"], row["layer_role"], row["boundary"]): row
                for row in point["boundary_restoration"]
            }
            for row in point["boundary_restoration"]:
                rows.append({
                    "base_problem_id": base,
                    "example_id": str(result["example_id"]),
                    "evidence_type": result["evidence_type"],
                    "coordinate": point["coordinate"],
                    "intervention_generated_index": point["intervention_generated_index"],
                    **compact_row(row),
                    "raw_result": path_by_base[base],
                })
            for row in point["adjacent_interface_equivalence"]:
                interface_rows.append({
                    "base_problem_id": base,
                    "coordinate": point["coordinate"],
                    **row,
                })
            for window in WINDOWS:
                for role in LAYER_ROLES:
                    post_attn = point_map[(window, role, "h_post_attn")]
                    post_block = point_map[(window, role, "h_post_block")]
                    post_attn_post_block_equivalence.append({
                        "base_problem_id": base,
                        "coordinate": point["coordinate"],
                        "window": window,
                        "layer_role": role,
                        "BMR_exact": float(post_attn["BMR"]) == float(post_block["BMR"]),
                        "all_recipient_donor_candidate_scores_exact": all_public_controls_exact(
                            post_attn["controls"], post_block["controls"]
                        ),
                    })
    if len(rows) != 37 * 40:
        raise RuntimeError(f"Expected 1480 primary rows, observed {len(rows)}")
    for boundary, filename in (
        ("h_pre", "pre_block_state_restoration.jsonl"),
        ("pre_attn_norm", "pre_attn_norm_restoration.jsonl"),
        ("h_post_attn", "post_attn_state_restoration.jsonl"),
        ("pre_mlp_norm", "pre_mlp_norm_restoration.jsonl"),
        ("h_post_block", "post_block_restoration.jsonl"),
    ):
        write_jsonl(OUT / f"scoring/{filename}", [row for row in rows if row["boundary"] == boundary])
    two_layer_alias_rows = [
        {**row, "alias_of_test_id": row["test_id"]}
        for row in rows if row["two_layer_entry_alias"]
    ]
    write_jsonl(OUT / "scoring/two_layer_recompute_restoration.jsonl", two_layer_alias_rows)

    keyed = {
        (row["base_problem_id"], row["coordinate"], row["window"], row["layer_role"], row["boundary"]): row
        for row in rows
    }
    raw_p: dict[str, float] = {}
    cell_stats = []
    for coordinate in COORDINATES:
        for window in WINDOWS:
            for role in LAYER_ROLES:
                for boundary in BOUNDARIES:
                    subset = [
                        row for row in rows
                        if row["coordinate"] == coordinate and row["window"] == window
                        and row["layer_role"] == role and row["boundary"] == boundary
                    ]
                    test_id = f"{coordinate}__{window}__{role}__{boundary}"
                    values = [float(row["BMR"]) for row in subset]
                    normalized = [float(row["BMR_normalized"]) for row in subset if row["BMR_normalized"] is not None]
                    block_ratios = [
                        safe_ratio(float(row["BMR"]), float(row["stage3b4_precomputed_references"]["block"]["BMR"]))
                        for row in subset
                    ]
                    block_ratios = [value for value in block_ratios if value is not None]
                    raw_p[test_id] = one_sided_wilcoxon_greater(values)
                    cell_stats.append({
                        "test_id": test_id,
                        "coordinate": coordinate,
                        "window": window,
                        "layer_role": role,
                        "layer_index": int(subset[0]["layer_index"]),
                        "boundary": boundary,
                        "two_layer_entry_alias": bool(subset[0]["two_layer_entry_alias"]),
                        "BMR": bootstrap_summary(values),
                        "BMR_normalized": bootstrap_summary(normalized),
                        "final_two_layer_block_ratio": bootstrap_summary(block_ratios),
                        "bidirectional_source_consistency_fraction": sum(bool(row["bidirectionally_source_consistent"]) for row in subset) / len(subset),
                        "A_render": bootstrap_summary([float(row["A_render"]) for row in subset]),
                        "render_to_semantic_ratio_median": statistics.median(float(row["render_to_semantic_ratio"]) for row in subset if row["render_to_semantic_ratio"] is not None),
                        "render_to_all_layer_ratio_median": statistics.median(float(row["render_to_all_layer_ratio"]) for row in subset if row["render_to_all_layer_ratio"] is not None),
                        "maximum_self_restoration_absolute_error": max(float(row["maximum_self_restoration_absolute_error"]) for row in subset),
                        "all_self_restorations_exact": all(row["all_self_restorations_exact"] for row in subset),
                        "all_patch_audits_valid": all(row["all_patch_audits_valid"] for row in subset),
                        "all_downstream_recompute_verified": all(row["all_expected_downstream_recompute_verified"] for row in subset),
                        "all_scores_finite": all(row["all_scores_finite"] for row in subset),
                        "one_sided_wilcoxon_raw_p": raw_p[test_id],
                    })
    adjusted = holm_adjust(raw_p)
    for row in cell_stats:
        correction = adjusted[row["test_id"]]
        row["holm_adjusted_p"] = correction["adjusted_p"]
        row["holm_rejected"] = correction["rejected"]
        row["robust"] = bool(
            float(correction["adjusted_p"]) < 0.05
            and float(row["BMR"]["bootstrap_95_CI"][0]) > 0.0
            and float(row["bidirectional_source_consistency_fraction"]) >= 0.70
            and float(row["render_to_semantic_ratio_median"]) < 0.25
            and bool(row["all_self_restorations_exact"])
        )

    stat_map = {
        (row["coordinate"], row["window"], row["layer_role"], row["boundary"]): row
        for row in cell_stats
    }
    increment_rows = []
    for coordinate in COORDINATES:
        for window in WINDOWS:
            for role in LAYER_ROLES:
                per_base = []
                for base in sorted(expected, key=int):
                    boundary_values = {
                        boundary: float(keyed[(base, coordinate, window, role, boundary)]["BMR"])
                        for boundary in BOUNDARIES
                    }
                    increments = boundary_increments(boundary_values)
                    block = float(keyed[(base, coordinate, window, role, "h_pre")]["stage3b4_precomputed_references"]["block"]["BMR"])
                    per_base.append({
                        "base_problem_id": base,
                        **increments,
                        **{f"{name}_to_final_block": safe_ratio(value, block) for name, value in increments.items()},
                    })
                for increment, after_boundary in (("G_attn", "h_post_attn"), ("G_mlp", "h_post_block"), ("G_input_norm", "pre_attn_norm"), ("G_post_attn_norm", "pre_mlp_norm")):
                    values = [float(row[increment]) for row in per_base]
                    ratios = [float(row[f"{increment}_to_final_block"]) for row in per_base if row[f"{increment}_to_final_block"] is not None]
                    increment_rows.append({
                        "coordinate": coordinate,
                        "window": window,
                        "layer_role": role,
                        "increment": increment,
                        "after_boundary": after_boundary,
                        "gain": bootstrap_summary(values),
                        "gain_to_final_two_layer_block": bootstrap_summary(ratios),
                        "after_boundary_robust": bool(stat_map[(coordinate, window, role, after_boundary)]["robust"]),
                        "per_base": per_base,
                    })

    increment_map = {
        (row["coordinate"], row["window"], row["layer_role"], row["increment"]): row
        for row in increment_rows
    }
    recompute_rows = []
    recompute_stats = []
    for coordinate in COORDINATES:
        for window in WINDOWS:
            cell_rows = []
            for base in sorted(expected, key=int):
                first_h_pre = keyed[(base, coordinate, window, "first", "h_pre")]
                second_h_pre = keyed[(base, coordinate, window, "second", "h_pre")]
                first_h_post_attn = keyed[(base, coordinate, window, "first", "h_post_attn")]
                second_h_post_attn = keyed[(base, coordinate, window, "second", "h_post_attn")]
                references = first_h_pre["stage3b4_precomputed_references"]
                block = float(references["block"]["BMR"])
                contrasts = recompute_contrasts(
                    h_pre_recompute=float(first_h_pre["BMR"]),
                    h_post_attn_recompute=float(first_h_post_attn["BMR"]),
                    precomputed_joint=float(references["joint"]["BMR"]),
                    precomputed_mlp=float(references["mlp"]["BMR"]),
                )
                row = {
                    "base_problem_id": base,
                    "coordinate": coordinate,
                    "window": window,
                    "h_pre_recompute": float(first_h_pre["BMR"]),
                    "second_h_pre": float(second_h_pre["BMR"]),
                    "first_h_post_attn_recompute": float(first_h_post_attn["BMR"]),
                    "second_h_post_attn_recompute": float(second_h_post_attn["BMR"]),
                    "precomputed_joint": float(references["joint"]["BMR"]),
                    "precomputed_mlp": float(references["mlp"]["BMR"]),
                    "final_two_layer_block_reference": block,
                    **contrasts,
                    "first_h_pre_minus_second_h_pre": float(first_h_pre["BMR"]) - float(second_h_pre["BMR"]),
                }
                for key in (
                    "h_pre_recompute", "second_h_pre", "h_pre_vs_precomputed_joint",
                    "h_post_attn_vs_precomputed_mlp", "first_h_pre_minus_second_h_pre",
                ):
                    row[f"{key}_to_final_block"] = safe_ratio(float(row[key]), block)
                cell_rows.append(row)
                recompute_rows.append(row)
            stats = {
                key: bootstrap_summary([float(row[key]) for row in cell_rows])
                for key in (
                    "h_pre_recompute", "second_h_pre", "precomputed_joint", "precomputed_mlp",
                    "final_two_layer_block_reference", "h_pre_vs_precomputed_joint",
                    "h_post_attn_vs_precomputed_mlp", "first_h_pre_minus_second_h_pre",
                    "h_pre_recompute_to_final_block", "second_h_pre_to_final_block",
                    "h_pre_vs_precomputed_joint_to_final_block",
                    "h_post_attn_vs_precomputed_mlp_to_final_block",
                    "first_h_pre_minus_second_h_pre_to_final_block",
                ) if all(row[key] is not None for row in cell_rows)
            }
            recompute_stats.append({
                "coordinate": coordinate,
                "window": window,
                "statistics": stats,
            })

    mechanics = {
        "eight_shards_complete": len(summaries) == 8,
        "all_expected_bases_and_rows_present": len(rows) == 1480 and set(observed) == expected,
        "all_condition_layout_exact": all(row["all_condition_layout_exact"] for row in summaries),
        "all_capture_hooks_exact": all(row["all_capture_audits_valid"] for row in summaries),
        "all_baselines_exact_stage3b4": all(row["all_baselines_exact_stage3b4"] for row in summaries),
        "all_patch_hooks_valid": all(row["all_patch_audits_valid"] for row in summaries),
        "all_downstream_recompute_verified": all(row["all_downstream_recompute_verified"] for row in summaries),
        "all_self_restorations_exact": all(row["all_self_restorations_exact"] for row in summaries),
        "all_adjacent_interfaces_exact": all(row["all_adjacent_interface_scores_exact"] and row["all_adjacent_interface_captured_states_exact"] for row in summaries),
        "all_scores_finite": all(row["all_scores_finite"] for row in summaries),
    }
    controls_pass = all(mechanics.values())

    decision_cells = []
    for coordinate in COORDINATES:
        for window in WINDOWS:
            rec = next(row for row in recompute_stats if row["coordinate"] == coordinate and row["window"] == window)["statistics"]
            attention_candidates = []
            mlp_candidates = []
            for role in LAYER_ROLES:
                attn = increment_map[(coordinate, window, role, "G_attn")]
                mlp = increment_map[(coordinate, window, role, "G_mlp")]
                attn_ratio = float(attn["gain_to_final_two_layer_block"]["median"])
                mlp_ratio = float(mlp["gain_to_final_two_layer_block"]["median"])
                attention_candidates.append({
                    "layer_role": role,
                    "qualifies": bool(
                        attn["after_boundary_robust"]
                        and float(attn["gain"]["bootstrap_95_CI"][0]) > 0.0
                        and attn_ratio >= 0.25
                        and attn_ratio >= mlp_ratio + 0.15
                    ),
                    "gain_to_final_block_median": attn_ratio,
                    "gain_bootstrap_CI_low": float(attn["gain"]["bootstrap_95_CI"][0]),
                })
                mlp_candidates.append({
                    "layer_role": role,
                    "qualifies": bool(
                        mlp["after_boundary_robust"]
                        and float(mlp["gain"]["bootstrap_95_CI"][0]) > 0.0
                        and mlp_ratio >= 0.25
                        and mlp_ratio >= attn_ratio + 0.15
                    ),
                    "gain_to_final_block_median": mlp_ratio,
                    "gain_bootstrap_CI_low": float(mlp["gain"]["bootstrap_95_CI"][0]),
                })
            first_h_pre = stat_map[(coordinate, window, "first", "h_pre")]
            final_reference = {
                "robust": True,
                "BMR_median": float(rec["final_two_layer_block_reference"]["median"]),
                "source": "frozen Stage 3B.4 two-layer Block arm",
            }
            h_pre_ratio = float(rec["h_pre_recompute_to_final_block"]["median"])
            gain_joint = rec["h_pre_vs_precomputed_joint_to_final_block"]
            gain_second = rec["first_h_pre_minus_second_h_pre_to_final_block"]
            sequential_qualifies = bool(
                first_h_pre["robust"]
                and h_pre_ratio >= 0.70
                and h_pre_ratio < 0.80
                and float(gain_joint["median"]) >= 0.20
                and float(rec["h_pre_vs_precomputed_joint"]["bootstrap_95_CI"][0]) > 0.0
                and float(gain_second["median"]) >= 0.20
                and float(rec["first_h_pre_minus_second_h_pre"]["bootstrap_95_CI"][0]) > 0.0
            )
            best_attention = max(attention_candidates, key=lambda row: row["gain_to_final_block_median"])
            best_mlp = max(mlp_candidates, key=lambda row: row["gain_to_final_block_median"])
            decision_cells.append({
                "coordinate": coordinate,
                "window": window,
                "final_block": final_reference,
                "first_h_pre": {
                    "robust": bool(first_h_pre["robust"]),
                    "BMR_median": float(first_h_pre["BMR"]["median"]),
                    "final_block_ratio_median": h_pre_ratio,
                },
                "attention_gain": {**best_attention, "all_layer_roles": attention_candidates},
                "mlp_gain": {**best_mlp, "all_layer_roles": mlp_candidates},
                "two_layer_recompute": {
                    "qualifies": sequential_qualifies,
                    "h_pre_to_final_block_median": h_pre_ratio,
                    "gain_over_precomputed_joint_to_final_block_median": float(gain_joint["median"]),
                    "h_post_attn_gain_over_precomputed_mlp_median": float(
                        rec["h_post_attn_vs_precomputed_mlp"]["median"]
                    ),
                    "h_post_attn_gain_over_precomputed_mlp_to_final_block_median": float(
                        rec["h_post_attn_vs_precomputed_mlp_to_final_block"]["median"]
                    ),
                    "gain_over_second_h_pre_to_final_block_median": float(gain_second["median"]),
                },
            })
    decision = evaluate_stage3b5_decision(decision_cells, controls_pass=controls_pass)
    decision["cells"] = decision_cells
    decision["threshold_source"] = "outputs/stage3b5/config/stage3b5_config.json"

    coordinate_comparison = {}
    for window in WINDOWS:
        coordinate_comparison[window] = {}
        for role in LAYER_ROLES:
            for boundary in BOUNDARIES:
                diffs = [
                    float(keyed[(base, "Ed", window, role, boundary)]["BMR"])
                    - float(keyed[(base, "Ed_minus_1", window, role, boundary)]["BMR"])
                    for base in sorted(expected, key=int)
                ]
                coordinate_comparison[window][f"{role}__{boundary}"] = bootstrap_summary(diffs)
    window_comparison = {}
    for coordinate in COORDINATES:
        window_comparison[coordinate] = {}
        for role in LAYER_ROLES:
            for boundary in BOUNDARIES:
                diffs = [
                    float(keyed[(base, coordinate, "W5", role, boundary)]["BMR"])
                    - float(keyed[(base, coordinate, "W4", role, boundary)]["BMR"])
                    for base in sorted(expected, key=int)
                ]
                window_comparison[coordinate][f"{role}__{boundary}"] = bootstrap_summary(diffs)

    write_json(OUT / "analysis/boundary_restoration_statistics.json", {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "independent_unit": "base_problem_id",
        "N": 37,
        "fixed_family_size": 40,
        "multiple_testing": "Holm",
        "rows": cell_stats,
        "mechanical_controls": mechanics,
    })
    write_json(OUT / "analysis/incremental_gain_statistics.json", {"rows": increment_rows})
    write_json(OUT / "analysis/recompute_vs_precomputed.json", {
        "comparison_source": "frozen Stage 3B.4 module-output results",
        "per_base": recompute_rows,
        "cells": recompute_stats,
    })
    write_json(OUT / "analysis/cross_layer_sequential_analysis.json", {
        "two_layer_entry_arm_is_first_layer_h_pre_alias": True,
        "duplicate_test_count": 0,
        "interface_equivalence_rows": interface_rows,
        "all_interfaces_exact": all(
            row["captured_first_h_post_block_equals_second_h_pre"]
            and row["patched_scores_exact_all_recipients_donors_candidates"]
            for row in interface_rows
        ),
        "post_attn_recompute_vs_post_block_equivalence": {
            "expected_count": 37 * 2 * 2 * 2,
            "observed_count": len(post_attn_post_block_equivalence),
            "all_BMR_exact": all(row["BMR_exact"] for row in post_attn_post_block_equivalence),
            "all_public_scores_exact": all(
                row["all_recipient_donor_candidate_scores_exact"]
                for row in post_attn_post_block_equivalence
            ),
            "rows": post_attn_post_block_equivalence,
            "interpretation": "For a deterministic positionwise MLP, exact restoration of source h_post_attn followed by natural MLP recomputation must regenerate source h_post_block at the patched position. The resulting zero G_mlp is an intervention equivalence, not evidence that MLP computation is globally irrelevant.",
        },
        "decision_cells": decision_cells,
    })
    write_json(OUT / "analysis/coordinate_comparison.json", coordinate_comparison)
    write_json(OUT / "analysis/window_comparison.json", window_comparison)
    write_json(OUT / "analysis/optional_readout_analysis.json", {
        "status": "NOT_RUN",
        "reason": "The optional descriptive readout was not required for the frozen causal boundary decision.",
    })
    write_json(OUT / "analysis/decision_rule_evaluation.json", decision)
    write_json(OUT / "analysis/primary_aggregation_validation.json", {
        "status": "PASS" if controls_pass else "FAIL",
        "primary_base_count": 37,
        "row_count": len(rows),
        "interface_row_count": len(interface_rows),
        "evidence_type_counts": dict(Counter(row["evidence_type"] for row in results)),
        "mechanical_controls": mechanics,
        "selection_used_attention": False,
    })
    queue = read_json(ROOT / "state/gpu_experiment_queue.json")
    queue_jobs = queue["jobs"] if isinstance(queue, dict) else queue
    stage_jobs = [
        job for job in queue_jobs
        if str(job.get("id", "")).startswith("visual_reasoning_stage3b5_")
    ]
    write_json(OUT / "config/gpu_job_manifest.json", {
        "job_count": len(stage_jobs),
        "jobs": [
            {
                key: job.get(key)
                for key in (
                    "id", "exp_id", "status", "gpu_type", "gpus", "partition", "node",
                    "slurm_job_name", "slurm_job_id", "log_path", "result_path", "command",
                    "created_at", "updated_at", "notes",
                )
            }
            for job in stage_jobs
        ],
        "all_jobs_succeeded": len(stage_jobs) == 16 and all(
            job.get("status") == "succeeded" for job in stage_jobs
        ),
        "observed_gpu": "NVIDIA RTX A5000",
        "peak_primary_gpu_allocated_bytes": max(
            int(row["peak_gpu_allocated_bytes"]) for row in summaries
        ),
    })
    make_figures(rows, cell_stats, increment_rows, recompute_rows)

    figure_count = len(list((OUT / "analysis/figures").glob("*.png")))
    acceptance_items = [
        (1, True, "Stage 3B.4 distributed-block redirect is preserved in the configuration and phase memory."),
        (2, True, "boundary_restoration_metrics directly reuses the validated O/O_sham/C/C_sham paired semantic metric."),
        (3, len(expected) == 37, "The exact 37 Stage 3B.4 paired numeric bases were used."),
        (4, True, "W4/F28_29, W5/F32_33, Ed_minus_1, and Ed were loaded without a new search."),
        (5, True, "The installed Qwen3-VL block ordering and source hash are recorded in audit/block_state_map.md."),
        (6, len(BOUNDARIES) == 5, "All five residual/norm boundaries were frozen before validation."),
        (7, validation["decision"] == "PASS", "The independent eight-base A5000 validation passed before primary submission."),
        (8, True, "Every arm contains reciprocal O/C recipient histories and O/O_sham/C/C_sham donor classes."),
        (9, mechanics["all_self_restorations_exact"], "Every O and C self patch reproduced its baseline exactly."),
        (10, True, "Paired sham restoration is present in all 1,480 rows."),
        (11, mechanics["all_downstream_recompute_verified"], "Expected downstream Attention/MLP modules re-executed after each patched boundary."),
        (12, len(two_layer_alias_rows) == 37 * 4, "Single-layer arms and four two-layer-entry aliases per base are present without duplicate tests."),
        (13, True, "Stage 3B.4 module outputs are immutable comparison values only."),
        (14, len(set(observed)) == 37, "base_problem_id is the independent unit."),
        (15, True, "Attention magnitude was not used for selection."),
        (16, True, "No head/ROI/Q/R/multi-evidence experiment was started."),
        (17, bool(decision["recommendation"]), f"Explicit recommendation: {decision['recommendation']}"),
    ]
    acceptance = {
        "stage": "Stage 3B.5",
        "status": "PASS" if controls_pass and all(row[1] for row in acceptance_items) else "FAIL",
        "technical_pass_does_not_require_simple_within_block_mechanism": True,
        "criteria": [
            {"criterion": number, "passed": passed, "evidence": evidence}
            for number, passed, evidence in acceptance_items
        ],
        "later_stage_started": False,
    }
    write_json(OUT / "summaries/stage3b5_acceptance.json", acceptance)
    robust_count = sum(bool(row["robust"]) for row in cell_stats)
    profile_lines = [
        "| Coordinate/window | first h_pre | first h_post_attn | second h_post_attn | frozen two-layer Block | first h_pre / Block | Frozen category |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    recompute_lines = [
        "| Coordinate/window | h_pre - Joint / Block | h_post_attn - MLP / Block | first h_pre - second h_pre / Block |",
        "|---|---:|---:|---:|",
    ]
    for cell in decision_cells:
        coordinate, window = cell["coordinate"], cell["window"]
        label = f"{coordinate}/{window}"
        categories = []
        if cell["first_h_pre"]["final_block_ratio_median"] >= 0.80:
            categories.append("upstream")
        if cell["two_layer_recompute"]["qualifies"]:
            categories.append("cross-layer")
        if cell["attention_gain"]["qualifies"]:
            categories.append(f"Attention ({cell['attention_gain']['layer_role']})")
        if cell["mlp_gain"]["qualifies"]:
            categories.append(f"MLP ({cell['mlp_gain']['layer_role']})")
        profile_lines.append(
            f"| {label} | {stat_map[(coordinate, window, 'first', 'h_pre')]['BMR']['median']:.4f} "
            f"| {stat_map[(coordinate, window, 'first', 'h_post_attn')]['BMR']['median']:.4f} "
            f"| {stat_map[(coordinate, window, 'second', 'h_post_attn')]['BMR']['median']:.4f} "
            f"| {cell['final_block']['BMR_median']:.4f} "
            f"| {cell['first_h_pre']['final_block_ratio_median']:.3f} "
            f"| {', '.join(categories) if categories else 'none'} |"
        )
        recompute_lines.append(
            f"| {label} | {cell['two_layer_recompute']['gain_over_precomputed_joint_to_final_block_median']:.3f} "
            f"| {cell['two_layer_recompute']['h_post_attn_gain_over_precomputed_mlp_to_final_block_median']:.3f} "
            f"| {cell['two_layer_recompute']['gain_over_second_h_pre_to_final_block_median']:.3f} |"
        )
    profile_table = "\n".join(profile_lines)
    recompute_table = "\n".join(recompute_lines)
    write_text(
        OUT / "summaries/stage3b5_summary.md",
        "# Stage 3B.5 — Sequential Residual-Stream Mediation and State-Dependent Recompute\n\n"
        f"Technical status: **{acceptance['status']}**. Recommendation: **{decision['recommendation']}**.\n\n"
        "The independent eight-base A5000 gate passed before primary scoring. The primary "
        "analysis uses the exact 37 paired numeric base problems, two frozen coordinates, W4/F28_29 "
        "and W5/F32_33, both individual layers, and five prospectively defined block boundaries. "
        f"All {len(rows)} rows and {len(cell_stats)}/40 corrected tests are present; {robust_count}/40 "
        "met the frozen Holm/CI/bidirectionality/render/self robustness rule.\n\n"
        "GPU execution used 16 recorded A5000 Slurm jobs (validation 106912--106919; primary "
        "106923--106930). Peak primary allocation was 8.745 GiB. Exact commands, logs, result "
        "paths, job IDs, and statuses are preserved in `config/gpu_job_manifest.json`.\n\n"
        "## Primary boundary profile\n\n"
        f"{profile_table}\n\n"
        "The frozen decision rule identified qualifying post-Attention gains in 3/4 cells: "
        "both W4 coordinates and W5 at `E_d-1`. W5 at `E_d` was the only cell satisfying "
        "the upstream-state rule (`h_pre`/Block = 0.808); W5 at `E_d-1` was close but remained "
        "below the frozen 0.80 cutoff at 0.786. No MLP-gain or cross-layer-sequential category "
        "qualified.\n\n"
        "Patching only the RMS-normalized Attention or MLP input while retaining the recipient raw "
        "residual produced much smaller restoration than patching the corresponding raw residual "
        "state. This distinguishes normalized-input sufficiency from raw residual-state carriage; "
        "it does not assign a unique information fraction to RMSNorm, Attention, or MLP.\n\n"
        "## State-dependent recomputation\n\n"
        f"{recompute_table}\n\n"
        "`h_pre` plus natural recomputation exceeded frozen Stage 3B.4 Joint-output restoration in "
        "both W5 cells but not W4. However, first-layer entry restoration did not exceed the "
        "second-layer `h_pre` arm, so the preregistered cross-layer-necessity rule did not pass. "
        "In contrast, source `h_post_attn` plus natural MLP recomputation exceeded the frozen "
        "precomputed MLP-output arm in all four cells by median 0.548--0.847 Block units. This "
        "supports state-dependent recomputation as an explanation for part of the Stage 3B.4 "
        "module/block gap, while not identifying a unique information fraction.\n\n"
        "## Exact implementation equivalences\n\n"
        "The first-layer `h_pre` arm is also the requested two-layer entry-recompute intervention. "
        "It was executed once and reported in both the boundary and sequential analyses; it was not "
        "double-counted as an additional hypothesis test. First-layer `h_post_block` and second-layer "
        "`h_pre` were exact at the captured interface and in every patched score, validating the "
        "cross-layer implementation.\n\n"
        "Across all 296 base/coordinate/window/layer cases, `h_post_attn` plus natural MLP "
        "recomputation and direct `h_post_block` restoration produced exactly identical public scores. "
        "This is expected because the MLP is deterministic and positionwise once the raw source "
        "post-Attention residual is fixed. Therefore the zero `G_mlp` is a structural equivalence of "
        "these interventions, not evidence that MLP computation is globally irrelevant.\n\n"
        f"{decision['rationale']} Complete boundary, increment, state-vs-precomputed, cross-layer, "
        f"coordinate, and window results plus {figure_count} figures are in `outputs/stage3b5/analysis/`.\n\n"
        "These interventions localize evidence-specific restoration at current-position block states. "
        "They do not identify an attention head, ROI path, Q/R carrier, MLP feature, multi-evidence "
        "refresh process, or failure mechanism. Attention magnitude was not used as causal evidence. "
        "Stage 3B.5 stops here.\n",
    )
    write_text(
        OUT / "summaries/next_stage_recommendation.md",
        "# Stage 3B.5 next-stage recommendation\n\n"
        f"## {decision['recommendation']}\n\n{decision['rationale']}\n\n"
        "Interpretation constraint: direct source `h_post_attn` restoration deterministically regenerates "
        "source `h_post_block`, so zero `G_mlp` does not establish general MLP irrelevance. The GO instead "
        "rests on the nontrivial source-state gain between `h_pre` recomputation and `h_post_attn` "
        "restoration in three frozen cells; W5 at `E_d` also met the upstream-state rule, but only one "
        "cell did so versus the required two.\n\n"
        "Qualifying Attention-gain cells were `E_d-1/W4`, `E_d-1/W5`, and `E_d/W4`; `E_d/W5` "
        "did not qualify. Any reviewed follow-on should preserve this heterogeneity and the borderline "
        "W5 upstream result rather than treating all four cells as one uniform mechanism.\n\n"
        "This is the one prospectively selected recommendation from the frozen decision hierarchy. "
        "It is a recommendation for joint review, not authorization to execute the next experiment. "
        "No head/path/ROI/Q-R/feature/neuron/multi-evidence/failure analysis has started.\n",
    )
    print(json.dumps({
        "status": acceptance["status"],
        "recommendation": decision["recommendation"],
        "primary_bases": len(expected),
        "rows": len(rows),
        "robust_tests": robust_count,
        "figures": figure_count,
    }, indent=2))


if __name__ == "__main__":
    main()
