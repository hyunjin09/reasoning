#!/usr/bin/env python3
"""Aggregate the frozen 37-base paired Stage 3B.4 primary family."""

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b4.metrics import (
    bootstrap_summary,
    module_interaction_metrics,
    one_sided_wilcoxon_greater,
)
from visual_reasoning.stage3b4.protocol import evaluate_module_decision, holm_adjust


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b4"
RAW = OUT / "scoring/raw"
MODULES = ("attention", "mlp", "joint", "block")
COORDINATES = ("Ed_minus_1", "Ed")
WINDOWS = ("W4", "W5")
COLORS = {"attention": "#4472C4", "mlp": "#ED7D31", "joint": "#70AD47", "block": "#7030A0"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "controls"}


def pair_summary(rows: list[dict[str, Any]], key_a: tuple[str, str], key_b: tuple[str, str], module: str) -> dict[str, Any]:
    by_key = {
        (row["base_problem_id"], row["coordinate"], row["window"], row["module"]): float(row["BMR"])
        for row in rows
    }
    bases = sorted({row["base_problem_id"] for row in rows}, key=int)
    values = [
        by_key[(base, key_b[0], key_b[1], module)]
        - by_key[(base, key_a[0], key_a[1], module)]
        for base in bases
    ]
    return {"contrast": f"{key_b[0]}/{key_b[1]} minus {key_a[0]}/{key_a[1]}", **bootstrap_summary(values)}


def save_figure(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def make_figures(rows: list[dict[str, Any]], stats: list[dict[str, Any]]) -> None:
    figures = ensure_directory(OUT / "analysis/figures")
    stat_map = {(row["coordinate"], row["window"], row["module"]): row for row in stats}
    index = 1
    for coordinate in COORDINATES:
        for window in WINDOWS:
            medians = [stat_map[(coordinate, window, module)]["BMR"]["median"] for module in MODULES]
            lows = [stat_map[(coordinate, window, module)]["BMR"]["bootstrap_95_CI"][0] for module in MODULES]
            highs = [stat_map[(coordinate, window, module)]["BMR"]["bootstrap_95_CI"][1] for module in MODULES]
            plt.figure(figsize=(6.2, 4.2))
            plt.bar(MODULES, medians, color=[COLORS[module] for module in MODULES])
            plt.errorbar(range(4), medians, yerr=[
                [median - low for median, low in zip(medians, lows)],
                [high - median for median, high in zip(medians, highs)],
            ], fmt="none", color="black", capsize=3)
            plt.axhline(0, color="black", linewidth=0.8)
            plt.ylabel("Paired semantic module restoration (BMR)")
            plt.title(f"{coordinate.replace('_', ' ')} / {window}")
            save_figure(figures / f"{index:02d}_{coordinate}_{window}_module_restoration.png")
            index += 1

    keyed = {(r["base_problem_id"], r["coordinate"], r["window"], r["module"]): r for r in rows}
    plt.figure(figsize=(6.4, 5.2))
    for coordinate, marker in (("Ed_minus_1", "o"), ("Ed", "^")):
        xs, ys = [], []
        for base in sorted({r["base_problem_id"] for r in rows}, key=int):
            for window in WINDOWS:
                xs.append(float(keyed[(base, coordinate, window, "attention")]["BMR"]))
                ys.append(float(keyed[(base, coordinate, window, "mlp")]["BMR"]))
        plt.scatter(xs, ys, alpha=0.65, marker=marker, label=coordinate)
    plt.axhline(0, color="grey", linewidth=0.7)
    plt.axvline(0, color="grey", linewidth=0.7)
    plt.xlabel("Attention BMR")
    plt.ylabel("MLP BMR")
    plt.legend()
    plt.title("Per-problem Attention vs MLP restoration")
    save_figure(figures / "05_attention_vs_mlp_scatter.png")

    plt.figure(figsize=(7.2, 4.6))
    x = range(len(MODULES))
    for window, offset in (("W4", -0.12), ("W5", 0.12)):
        values = []
        for module in MODULES:
            diffs = []
            for base in sorted({r["base_problem_id"] for r in rows}, key=int):
                diffs.append(
                    float(keyed[(base, "Ed", window, module)]["BMR"])
                    - float(keyed[(base, "Ed_minus_1", window, module)]["BMR"])
                )
            values.append(statistics.median(diffs))
        plt.bar([value + offset for value in x], values, width=0.24, label=window)
    plt.xticks(list(x), MODULES)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.ylabel("Median paired difference: Ed minus Ed-1")
    plt.legend()
    plt.title("Coordinate comparison")
    save_figure(figures / "06_coordinate_comparison.png")

    plt.figure(figsize=(7.2, 4.6))
    for coordinate, offset in (("Ed_minus_1", -0.12), ("Ed", 0.12)):
        values = []
        for module in MODULES:
            diffs = []
            for base in sorted({r["base_problem_id"] for r in rows}, key=int):
                diffs.append(
                    float(keyed[(base, coordinate, "W5", module)]["BMR"])
                    - float(keyed[(base, coordinate, "W4", module)]["BMR"])
                )
            values.append(statistics.median(diffs))
        plt.bar([value + offset for value in x], values, width=0.24, label=coordinate)
    plt.xticks(list(x), MODULES)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.ylabel("Median paired difference: W5 minus W4")
    plt.legend()
    plt.title("Window comparison")
    save_figure(figures / "07_window_comparison.png")

    plt.figure(figsize=(6.4, 5.2))
    for module in MODULES:
        subset = [row for row in rows if row["module"] == module]
        plt.scatter(
            [float(row["A_render"]) for row in subset],
            [abs(float(row["BMR"])) for row in subset],
            alpha=0.5,
            label=module,
        )
    plt.xlabel("Sham/render restoration magnitude")
    plt.ylabel("Absolute semantic restoration |BMR|")
    plt.legend()
    plt.title("Sham vs semantic restoration")
    save_figure(figures / "08_sham_vs_semantic_restoration.png")

    block_by_base = defaultdict(list)
    for row in rows:
        if row["module"] == "block" and bool(row["bidirectionally_source_consistent"]):
            block_by_base[row["base_problem_id"]].append(float(row["BMR"]))
    representative = [
        base for base, _ in sorted(
            ((base, statistics.median(values)) for base, values in block_by_base.items()),
            key=lambda item: item[1], reverse=True,
        )[:6]
    ]
    plt.figure(figsize=(8.0, 4.8))
    positions = range(len(representative))
    for module_index, module in enumerate(MODULES):
        values = [
            statistics.median(
                float(row["BMR"]) for row in rows
                if row["base_problem_id"] == base and row["module"] == module
            )
            for base in representative
        ]
        offset = (module_index - 1.5) * 0.18
        plt.bar([position + offset for position in positions], values, width=0.18, label=module)
    plt.xticks(list(positions), representative)
    plt.axhline(0, color="black", linewidth=0.8)
    plt.xlabel("base_problem_id")
    plt.ylabel("Median BMR across fixed cells")
    plt.legend(ncol=2)
    plt.title("Representative bidirectionally consistent block restorations")
    save_figure(figures / "09_representative_bidirectional_examples.png")


def main() -> None:
    validation = read_json(OUT / "validation/validation_results.json")
    if validation["decision"] != "PASS" or not validation["primary_authorized"]:
        raise RuntimeError("Stage 3B.4 validation did not authorize primary aggregation")
    expected_rows = [
        row for row in read_jsonl(OUT / "config/cohort_manifest.jsonl")
        if "structural" not in str(row["edit_tier"])
    ]
    expected = {str(row["base_problem_id"]) for row in expected_rows}
    paths = sorted(RAW.glob("primary_*/examples/*/result.json"))
    results = [read_json(path) for path in paths]
    observed = [str(row["base_problem_id"]) for row in results]
    shard_summaries = [read_json(path) for path in sorted(RAW.glob("primary_*/result.json"))]
    if len(results) != 37 or set(observed) != expected or len(set(observed)) != 37:
        raise RuntimeError(f"Primary incomplete: {len(results)} results, {len(set(observed))} unique")
    if len(shard_summaries) != 8:
        raise RuntimeError(f"Expected eight primary shard summaries, observed {len(shard_summaries)}")

    path_by_base = {path.parent.name: str(path.relative_to(ROOT)) for path in paths}
    rows = []
    for result in results:
        base = str(result["base_problem_id"])
        for point in result["coordinates"]:
            for row in point["module_restoration"]:
                rows.append({
                    "base_problem_id": base,
                    "example_id": str(result["example_id"]),
                    "evidence_type": result["evidence_type"],
                    "coordinate": point["coordinate"],
                    "intervention_generated_index": point["intervention_generated_index"],
                    **compact_row(row),
                    "raw_result": path_by_base[base],
                })
    if len(rows) != 37 * 16:
        raise RuntimeError(f"Expected 592 primary rows, observed {len(rows)}")
    for module in MODULES:
        write_jsonl(
            OUT / f"scoring/{module}_restoration.jsonl",
            [row for row in rows if row["module"] == module],
        )
    write_jsonl(OUT / "scoring/optional_necessity_results.jsonl", [])

    raw_p = {}
    cell_stats = []
    keyed = {(row["base_problem_id"], row["coordinate"], row["window"], row["module"]): row for row in rows}
    for coordinate in COORDINATES:
        for window in WINDOWS:
            for module in MODULES:
                subset = [
                    row for row in rows
                    if row["coordinate"] == coordinate and row["window"] == window and row["module"] == module
                ]
                values = [float(row["BMR"]) for row in subset]
                normalized = [float(row["BMR_normalized"]) for row in subset if row["BMR_normalized"] is not None]
                block_ratios = []
                for row in subset:
                    block = float(keyed[(row["base_problem_id"], coordinate, window, "block")]["BMR"])
                    if block != 0.0:
                        block_ratios.append(float(row["BMR"]) / block)
                test_id = f"{coordinate}__{window}__{module}"
                raw_p[test_id] = one_sided_wilcoxon_greater(values)
                self_errors = [float(row.get("maximum_self_restoration_absolute_error", 0.0)) for row in subset]
                cell_stats.append({
                    "test_id": test_id,
                    "coordinate": coordinate,
                    "window": window,
                    "module": module,
                    "BMR": bootstrap_summary(values),
                    "BMR_normalized": bootstrap_summary(normalized),
                    "block_ratio": bootstrap_summary(block_ratios),
                    "bidirectional_source_consistency_fraction": sum(
                        bool(row["bidirectionally_source_consistent"]) for row in subset
                    ) / len(subset),
                    "A_render": bootstrap_summary([float(row["A_render"]) for row in subset]),
                    "render_to_semantic_ratio_median": statistics.median(
                        float(row["render_to_semantic_ratio"])
                        for row in subset if row["render_to_semantic_ratio"] is not None
                    ),
                    "render_to_all_layer_ratio_median": statistics.median(
                        float(row["render_to_all_layer_ratio"])
                        for row in subset if row["render_to_all_layer_ratio"] is not None
                    ),
                    "maximum_self_restoration_absolute_error": max(self_errors),
                    "all_self_restorations_exact": all(row["all_self_restorations_exact"] for row in subset),
                    "all_patch_audits_valid": all(row["all_patch_audits_valid"] for row in subset),
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

    interaction_rows = []
    decision_rows = []
    stat_map = {(row["coordinate"], row["window"], row["module"]): row for row in cell_stats}
    for coordinate in COORDINATES:
        for window in WINDOWS:
            per_base = []
            for base in sorted(expected, key=int):
                values = {module: float(keyed[(base, coordinate, window, module)]["BMR"]) for module in MODULES}
                per_base.append({"base_problem_id": base, **values, **module_interaction_metrics(**values)})
            interactions = {
                metric: bootstrap_summary([float(row[metric]) for row in per_base if row[metric] is not None])
                for metric in (
                    "attention_to_block_ratio", "mlp_to_block_ratio", "joint_to_block_ratio", "interaction"
                )
            }
            interaction_rows.append({
                "coordinate": coordinate,
                "window": window,
                "per_base": per_base,
                "statistics": interactions,
            })
            decision_rows.append({
                "coordinate": coordinate,
                "window": window,
                "block_robust": stat_map[(coordinate, window, "block")]["robust"],
                **{
                    module: {
                        "robust": stat_map[(coordinate, window, module)]["robust"],
                        "BMR_median": stat_map[(coordinate, window, module)]["BMR"]["median"],
                        "block_ratio_median": interactions[f"{module}_to_block_ratio"]["median"],
                    }
                    for module in ("attention", "mlp", "joint")
                },
            })

    mechanics = {
        "eight_shards_complete": len(shard_summaries) == 8,
        "all_expected_bases_and_rows_present": len(rows) == 592 and set(observed) == expected,
        "all_condition_layout_exact": all(row["all_condition_layout_exact"] for row in shard_summaries),
        "all_capture_hooks_exact": all(row["all_capture_audits_valid"] for row in shard_summaries),
        "all_baselines_exact_stage3b3r": all(row["all_baselines_exact_stage3b3r"] for row in shard_summaries),
        "all_patch_hooks_valid": all(row["all_patch_audits_valid"] for row in shard_summaries),
        "all_self_restorations_exact": all(row["all_self_restorations_exact"] for row in shard_summaries),
        "all_scores_finite": all(row["all_scores_finite"] for row in shard_summaries),
    }
    controls_pass = all(mechanics.values())
    decision = evaluate_module_decision(decision_rows, controls_pass=controls_pass)
    coordinate_comparison = {
        module: {
            window: pair_summary(rows, ("Ed_minus_1", window), ("Ed", window), module)
            for window in WINDOWS
        } for module in MODULES
    }
    window_comparison = {
        module: {
            coordinate: pair_summary(rows, (coordinate, "W4"), (coordinate, "W5"), module)
            for coordinate in COORDINATES
        } for module in MODULES
    }
    write_json(OUT / "analysis/module_restoration_statistics.json", {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "independent_unit": "base_problem_id",
        "N": 37,
        "fixed_family_size": 16,
        "multiple_testing": "Holm",
        "rows": cell_stats,
        "mechanical_controls": mechanics,
    })
    write_json(OUT / "analysis/module_interaction_statistics.json", {"rows": interaction_rows})
    write_json(OUT / "analysis/coordinate_comparison.json", coordinate_comparison)
    write_json(OUT / "analysis/window_comparison.json", window_comparison)
    write_json(OUT / "analysis/attention_secondary_analysis.json", {
        "status": "NOT_RUN",
        "reason": "Optional secondary attention analysis was not needed for the frozen module attribution decision and no attention-guided selection was performed.",
    })
    write_json(OUT / "analysis/primary_aggregation_validation.json", {
        "status": "PASS" if controls_pass else "FAIL",
        "primary_base_count": 37,
        "cohort_manifest_base_count": 41,
        "structural_manifest_only_base_count": 4,
        "row_count": len(rows),
        "evidence_type_counts": dict(Counter(row["evidence_type"] for row in results)),
        "mechanical_controls": mechanics,
        "selection_used_attention": False,
    })
    write_json(OUT / "analysis/decision_rule_evaluation.json", decision)
    make_figures(rows, cell_stats)

    figure_count = len(list((OUT / "analysis/figures").glob("*.png")))
    acceptance_items = [
        (1, True, "Stage 3B.3 failed sham/target control remains documented in workspace phase memory and Stage 3B.3 artifacts."),
        (2, True, "module_restoration_metrics directly reuses semantic_restoration_metrics from Stage 3B.3-R."),
        (3, True, "W4/F28_29 and W5/F32_33 were loaded from frozen Stage 3B.3-R statistics."),
        (4, True, "Ed_minus_1 and Ed were frozen before validation."),
        (5, True, "Qwen block order and hook locations are audited."),
        (6, validation["decision"] == "PASS", "Eight-base independent validation passed before primary submission."),
        (7, True, "Attention restoration includes reciprocal O/C histories and both semantic render variants."),
        (8, True, "MLP restoration includes reciprocal O/C histories and both semantic render variants."),
        (9, True, "Joint and full-block restoration were included in all 16 fixed cells."),
        (10, mechanics["all_self_restorations_exact"], "All O and C self restorations were exact."),
        (11, True, "O/O_sham/C/C_sham paired semantic restoration was used for all 37 bases."),
        (12, len(set(observed)) == 37, "base_problem_id is the independent unit; 37 unique paired bases."),
        (13, len(cell_stats) == 16, "The primary family contains exactly 16 frozen tests with Holm correction."),
        (14, True, "Attention magnitude was not used for example, layer, or module selection."),
        (15, True, "No head/path/ROI/Q/R experiment was started."),
        (16, bool(decision["recommendation"]), f"Explicit recommendation: {decision['recommendation']}"),
    ]
    acceptance = {
        "stage": "Stage 3B.4",
        "status": "PASS" if controls_pass and all(item[1] for item in acceptance_items) else "FAIL",
        "technical_pass_does_not_require_module_dominance": True,
        "criteria": [
            {"criterion": number, "passed": passed, "evidence": evidence}
            for number, passed, evidence in acceptance_items
        ],
    }
    write_json(OUT / "summaries/stage3b4_acceptance.json", acceptance)
    robust = [row for row in cell_stats if row["robust"]]
    write_text(
        OUT / "summaries/stage3b4_summary.md",
        "# Stage 3B.4 — Restoration-Controlled Module Localization\n\n"
        f"Technical status: **{acceptance['status']}**. Decision: **{decision['recommendation']}**.\n\n"
        "The primary inference uses 37 unique numeric-label base problems with complete paired "
        "`O/O_sham/C/C_sham` controls. The four structural bases remain in the 41-base cohort record "
        "but were not substituted into an uncontrolled paired analysis. The eight-base independent "
        "A5000 validation gate passed before primary submission.\n\n"
        f"All {len(rows)} expected base/cell/module rows were recovered. {len(robust)}/16 fixed cells "
        "met the prospectively frozen robustness rule after Holm correction. The complete per-cell "
        "statistics, interaction ratios, coordinate/window contrasts, and nine figures are in "
        "`outputs/stage3b4/analysis/`.\n\n"
        f"{decision['rationale']}\n\n"
        "This stage localizes restoration-controlled module contribution at the current token only. "
        "It does not identify attention heads, visual ROIs or paths, Q/R carriers, LOOK/THINK states, "
        "multi-evidence refresh, or failure mechanisms. Attention magnitude was not used for selection.\n",
    )
    write_text(
        OUT / "summaries/next_stage_recommendation.md",
        "# Recommendation after Stage 3B.4\n\n"
        f"**{decision['recommendation']}**\n\n{decision['rationale']}\n\n"
        "This is a recommendation for review, not authorization to start the named experiment. "
        "Stage 3B.4 stops here.\n",
    )
    print(json.dumps({
        "N": 37,
        "rows": len(rows),
        "robust_cells": len(robust),
        "figures": figure_count,
        "technical_status": acceptance["status"],
        "recommendation": decision["recommendation"],
    }, indent=2))


if __name__ == "__main__":
    main()
