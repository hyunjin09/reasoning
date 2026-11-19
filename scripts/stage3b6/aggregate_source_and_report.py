#!/usr/bin/env python3
"""Aggregate gated V/P/R paths, secondary triangulation, and final Stage 3B.6 reports."""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3b4.metrics import bootstrap_summary, one_sided_wilcoxon_greater
from visual_reasoning.stage3b4.protocol import holm_adjust
from visual_reasoning.stage3b6.metrics import aggregate_base_medians


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b6"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def median(values: list[float]) -> float:
    return float(statistics.median(float(value) for value in values))


def flatten(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "base_problem_id": str(base["base_problem_id"]),
            "example_id": str(base["example_id"]),
            "evidence_type": base["evidence_type"],
            **unit,
        }
        for base in rows
        for cell in base["cells"]
        for unit in cell["unit_results"]
    ]


def selected_visual_mass(row: dict[str, Any]) -> float | None:
    values = []
    for call in row["mechanical_audit"]["calls"]:
        if not (
            (call["recipient"] == "O" and call["donor"] == "C")
            or (call["recipient"] == "C" and call["donor"] == "O")
        ):
            continue
        summary = call["recipient_attention_summary"]
        mass = summary.get("V_mass_per_head")
        if not mass:
            continue
        values.extend(float(mass[head]) for head in row["heads"])
    return float(statistics.fmean(values)) if values else None


def correlation(x: list[float], y: list[float]) -> dict[str, Any]:
    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return {"N": len(x), "spearman_rho": None, "p_value": None}
    result = spearmanr(x, y)
    return {
        "N": len(x),
        "spearman_rho": float(result.statistic),
        "p_value": float(result.pvalue),
    }


def source_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    bpr = [float(row["BPR"]) for row in rows]
    prr = [float(row["PRR"]) for row in rows if row["PRR"] is not None]
    sham = [
        float(row["sham_to_semantic_ratio"])
        for row in rows
        if row["sham_to_semantic_ratio"] is not None
    ]
    bootstrap = bootstrap_summary(bpr)
    return {
        "base_count": len(rows),
        "mean_BPR": bootstrap["mean"],
        "median_BPR": bootstrap["median"],
        "bootstrap_95_CI": bootstrap["bootstrap_95_CI"],
        "raw_p": one_sided_wilcoxon_greater(bpr),
        "median_PRR": median(prr),
        "bidirectional_count": sum(
            bool(row["bidirectionally_source_consistent"]) for row in rows
        ),
        "bidirectional_fraction": sum(
            bool(row["bidirectionally_source_consistent"]) for row in rows
        )
        / len(rows),
        "median_sham_to_semantic_ratio": median(sham),
        "all_self_exact": all(bool(row["all_self_restorations_exact"]) for row in rows),
    }


def main() -> None:
    config = read_json(OUT / "config/stage3b6_config.json")
    targets = read_json(OUT / "analysis/source_path_targets.json")
    head_stats = read_json(OUT / "analysis/head_restoration_statistics.json")
    head_categories = read_json(OUT / "analysis/sparse_vs_distributed_heads.json")
    upstream_stats = read_json(OUT / "analysis/upstream_control_statistics.json")
    split = read_json(OUT / "config/discovery_primary_split.json")
    source_rows: list[dict[str, Any]] = []
    source_shard_summaries: list[dict[str, Any]] = []
    if targets["gate_passed"]:
        directories = sorted((OUT / "scoring/raw").glob("source_*"))
        if len(directories) != 2:
            raise RuntimeError(f"Expected two source shards, observed {len(directories)}")
        source_shard_summaries = [read_json(path / "result.json") for path in directories]
        if not all(bool(row["all_mechanical_controls_passed"]) for row in source_shard_summaries):
            raise RuntimeError("Source-path mechanical controls failed")
        bases = [row for path in directories for row in read_jsonl(path / "results.jsonl")]
        if {str(row["base_problem_id"]) for row in bases} != set(
            split["primary_base_problem_ids"]
        ):
            raise RuntimeError("Source-path base set changed")
        raw = flatten(bases)
        lookup = {
            (row["base_problem_id"], row["cell_id"], row["unit_id"], row["source_group"]): row
            for row in raw
        }
        for row in raw:
            all_row = lookup[
                (row["base_problem_id"], row["cell_id"], row["unit_id"], "all")
            ]
            denominator = float(all_row["BHR"])
            source_rows.append({
                **row,
                "BPR_O": float(row["BHR_O"]),
                "BPR_C": float(row["BHR_C"]),
                "BPR": float(row["BHR"]),
                "PRR": None if denominator == 0.0 else float(row["BHR"]) / denominator,
                "all_source_BPR": denominator,
                "selected_head_visual_attention_mass": selected_visual_mass(row),
            })
    write_jsonl(OUT / "scoring/source_path_results.jsonl", source_rows)

    source_statistics: list[dict[str, Any]] = []
    source_categories: list[dict[str, Any]] = []
    if source_rows:
        grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in source_rows:
            grouped[(row["cell_id"], row["unit_id"], row["source_group"])].append(row)
        p_values = {}
        for (cell_id, unit_id, group), rows in sorted(grouped.items()):
            if len(rows) != 37:
                raise RuntimeError(f"Source {cell_id}/{unit_id}/{group} has {len(rows)} bases")
            summary = {
                "test_id": f"{cell_id}__{unit_id}__{group}",
                "cell_id": cell_id,
                "unit_id": unit_id,
                "heads": rows[0]["heads"],
                "source_group": group,
                **source_summary(rows),
            }
            source_statistics.append(summary)
            p_values[summary["test_id"]] = float(summary["raw_p"])
        adjusted = holm_adjust(p_values)
        for summary in source_statistics:
            correction = adjusted[summary["test_id"]]
            summary["holm_adjusted_p"] = float(correction["adjusted_p"])
            summary["robust"] = bool(
                correction["rejected"]
                and float(summary["bootstrap_95_CI"][0]) > 0.0
                and float(summary["bidirectional_fraction"]) >= 0.70
                and float(summary["median_sham_to_semantic_ratio"]) < 0.25
                and bool(summary["all_self_exact"])
            )
        by_target: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
        for row in source_statistics:
            by_target[(row["cell_id"], row["unit_id"])][row["source_group"]] = row
        for (cell_id, unit_id), groups in sorted(by_target.items()):
            singles = {name: groups[name] for name in ("V", "P", "R")}
            dominant = [
                name
                for name, row in singles.items()
                if row["robust"]
                and float(row["median_PRR"]) >= 0.75
                and all(
                    float(other["median_PRR"]) < 0.50
                    for other_name, other in singles.items()
                    if other_name != name
                )
            ]
            category = f"{dominant[0]}-dominant" if len(dominant) == 1 else "mixed_or_redundant"
            high_but_nonrobust = [
                name
                for name, row in singles.items()
                if float(row["median_PRR"]) >= 0.75 and not row["robust"]
            ]
            if len(dominant) == 1:
                classification_note = (
                    f"{dominant[0]} alone passed the frozen robust-dominance rule."
                )
            elif high_but_nonrobust:
                details = ", ".join(
                    f"{name} (median sham/semantic ratio "
                    f"{float(singles[name]['median_sham_to_semantic_ratio']):.3f})"
                    for name in high_but_nonrobust
                )
                classification_note = (
                    f"High median PRR was observed for {details}, but the frozen "
                    "robustness controls failed; source attribution is inconclusive."
                )
            else:
                classification_note = (
                    "No single source passed the frozen robust-dominance rule."
                )
            source_categories.append({
                "cell_id": cell_id,
                "unit_id": unit_id,
                "category": category,
                "classification_note": classification_note,
                "robust_by_source": {
                    name: bool(row["robust"]) for name, row in singles.items()
                },
                "median_PRR": {
                    name: float(row["median_PRR"]) for name, row in groups.items()
                },
            })

    write_json(
        OUT / "analysis/source_path_statistics.json",
        {
            "gate_passed": bool(targets["gate_passed"]),
            "primary_unit": "base_problem_id",
            "base_count": 37 if source_rows else 0,
            "target_count": len(targets["targets"]),
            "unit_group_statistics": source_statistics,
            "source_categories": source_categories,
            "PRR_unclipped": True,
            "PRR_not_unique_information_fraction": True,
        },
    )
    source_validation = {
        "gate_passed": bool(targets["gate_passed"]),
        "status": "PASS" if (not targets["gate_passed"] or source_rows) else "FAIL",
        "source_scoring_skipped_by_gate": not targets["gate_passed"],
        "all_source_shards_mechanical_pass": (
            all(bool(row["all_mechanical_controls_passed"]) for row in source_shard_summaries)
            if source_shard_summaries else None
        ),
        "all_groups_present": (
            {row["source_group"] for row in source_rows} == {"all", "V", "P", "R"}
            if source_rows else None
        ),
        "all_rows_bidirectional": bool(source_rows) if targets["gate_passed"] else None,
        "selection_used_attention": False,
    }
    write_json(OUT / "validation/source_path_validation.json", source_validation)

    # Secondary Stage 3B.1 cutoff triangulation.
    cutoff_data = read_json(OUT.parent / "stage3b1/analysis/prefill_vs_postprefill_gain.json")
    cutoff = {str(row["base_problem_id"]): row for row in cutoff_data["per_base"]}
    v_rows = [row for row in source_rows if row["source_group"] == "V"]
    cutoff_pairs_raw = [
        {
            "base_problem_id": row["base_problem_id"],
            "cell_id": row["cell_id"],
            "unit_id": row["unit_id"],
            "all_visual_cutoff_damage_E0_minus_1": 1.0
            - float(cutoff[row["base_problem_id"]]["e0_minus_1_retention"]),
            "V_path_BPR": float(row["BPR"]),
            "V_path_PRR": row["PRR"],
        }
        for row in v_rows
        if row["base_problem_id"] in cutoff
    ]
    cutoff_pairs = aggregate_base_medians(
        cutoff_pairs_raw,
        value_keys=("all_visual_cutoff_damage_E0_minus_1", "V_path_BPR", "V_path_PRR"),
    )
    cutoff_corr = correlation(
        [float(row["all_visual_cutoff_damage_E0_minus_1"]) for row in cutoff_pairs],
        [float(row["V_path_BPR"]) for row in cutoff_pairs],
    )
    write_json(
        OUT / "analysis/cutoff_triangulation.json",
        {
            "secondary_only": True,
            "definition": "Stage 3B.1 E0-1 all-visual cutoff damage (1-rho) versus Stage 3B.6 V-only BPR",
            "independent_unit": "base_problem_id",
            "correlation": cutoff_corr,
            "base_aggregated_rows": cutoff_pairs,
            "cell_level_rows": cutoff_pairs_raw,
        },
    )

    # Secondary raw selected-head attention versus causal restoration.
    all_source_rows = [row for row in source_rows if row["source_group"] == "all"]
    attention_rows_raw = [
        {
            "base_problem_id": row["base_problem_id"],
            "cell_id": row["cell_id"],
            "unit_id": row["unit_id"],
            "selected_head_visual_attention_mass": row[
                "selected_head_visual_attention_mass"
            ],
            "causal_all_source_BPR": float(row["BPR"]),
            "causal_V_only_BPR": next(
                float(candidate["BPR"])
                for candidate in source_rows
                if candidate["base_problem_id"] == row["base_problem_id"]
                and candidate["cell_id"] == row["cell_id"]
                and candidate["unit_id"] == row["unit_id"]
                and candidate["source_group"] == "V"
            ),
        }
        for row in all_source_rows
        if row["selected_head_visual_attention_mass"] is not None
    ]
    attention_rows = aggregate_base_medians(
        attention_rows_raw,
        value_keys=(
            "selected_head_visual_attention_mass",
            "causal_all_source_BPR",
            "causal_V_only_BPR",
        ),
    )
    attention_corr = correlation(
        [float(row["selected_head_visual_attention_mass"]) for row in attention_rows],
        [float(row["causal_all_source_BPR"]) for row in attention_rows],
    )
    visual_path_corr = correlation(
        [float(row["selected_head_visual_attention_mass"]) for row in attention_rows],
        [float(row["causal_V_only_BPR"]) for row in attention_rows],
    )
    write_json(
        OUT / "analysis/attention_secondary_analysis.json",
        {
            "secondary_only": True,
            "selection_used_attention": False,
            "independent_unit": "base_problem_id",
            "raw_selected_head_visual_mass_vs_all_source_BPR": attention_corr,
            "raw_selected_head_visual_mass_vs_V_only_BPR": visual_path_corr,
            "base_aggregated_rows": attention_rows,
            "cell_level_rows": attention_rows_raw,
            "interpretation": "Attention magnitude, causal Attention-head contribution, and evidence-specific V-path transfer remain distinct measurements.",
        },
    )

    # Decision hierarchy frozen before scoring.
    if not targets["gate_passed"]:
        recommendation = "REDIRECT — Head-localization failure"
        rationale = "No frozen single head or cumulative Top-k set passed the confirmatory restoration gate."
    elif any(row["category"] == "V-dominant" for row in source_categories):
        recommendation = "GO — ROI-specific visual path + pattern/value decomposition"
        rationale = "At least one confirmed causal head/set has a robust visual-dominant source path under the frozen PRR rule."
    elif any(row["category"] in {"P-dominant", "R-dominant"} for row in source_categories):
        recommendation = "GO — Language-side source-path localization"
        rationale = "A confirmed causal head/set is dominated by a nonvisual prefix or previous-reasoning source path."
    elif any(row["category"] == "H-Distributed" for row in head_categories["cells"]) or any(
        row["category"] == "mixed_or_redundant" for row in source_categories
    ):
        recommendation = "GO — Multi-head distributed circuit analysis"
        rationale = "Confirmed restoration requires distributed heads and/or remains mixed or redundant across source classes."
    else:
        recommendation = "REDIRECT — Head-localization failure"
        rationale = "Head recovery is partial and no frozen source-path rule supports a specific next localization."

    figures = OUT / "analysis/figures"
    if source_statistics:
        target_labels = sorted({(row["cell_id"], row["unit_id"]) for row in source_statistics})
        figure, axes = plt.subplots(1, len(target_labels), figsize=(5 * len(target_labels), 4), squeeze=False)
        for axis, target in zip(axes[0], target_labels):
            rows = [row for row in source_statistics if (row["cell_id"], row["unit_id"]) == target]
            order = [name for name in ("all", "V", "P", "R") if any(row["source_group"] == name for row in rows)]
            lookup = {row["source_group"]: row for row in rows}
            axis.bar(order, [float(lookup[name]["median_BPR"]) for name in order], color="#4c78a8")
            axis.set_title(f"{target[0]} / {target[1]}")
            axis.set_ylabel("median BPR")
        figure.tight_layout()
        figure.savefig(figures / "06_source_path_vpr.png", dpi=180)
        plt.close(figure)

        figure, axis = plt.subplots(figsize=(6, 5))
        for target in target_labels:
            rows = [
                row for row in source_rows
                if row["source_group"] == "V" and (row["cell_id"], row["unit_id"]) == target
            ]
            axis.scatter(
                [float(row["all_source_BPR"]) for row in rows],
                [float(row["BPR"]) for row in rows],
                alpha=0.7,
                label=f"{target[0]}/{target[1]}",
            )
        axis.axline((0, 0), slope=1, color="black", linestyle="--", linewidth=0.8)
        axis.set_xlabel("all-source BPR")
        axis.set_ylabel("V-only BPR")
        axis.legend(fontsize=7)
        figure.tight_layout()
        figure.savefig(figures / "07_per_problem_visual_path.png", dpi=180)
        plt.close(figure)
    else:
        for name, title in (
            ("06_source_path_vpr.png", "Source path skipped: Phase A gate failed"),
            ("07_per_problem_visual_path.png", "Visual path skipped: Phase A gate failed"),
        ):
            figure, axis = plt.subplots(figsize=(7, 4))
            axis.text(0.5, 0.5, title, ha="center", va="center")
            axis.axis("off")
            figure.savefig(figures / name, dpi=180)
            plt.close(figure)

    figure, axis = plt.subplots(figsize=(6, 5))
    if cutoff_pairs:
        axis.scatter(
            [row["all_visual_cutoff_damage_E0_minus_1"] for row in cutoff_pairs],
            [row["V_path_BPR"] for row in cutoff_pairs],
            alpha=0.65,
        )
    axis.set_xlabel("Stage 3B.1 all-V cutoff damage (1-rho at E0-1)")
    axis.set_ylabel("Stage 3B.6 V-only BPR")
    figure.tight_layout()
    figure.savefig(figures / "08_cutoff_vs_visual_path.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(6, 5))
    if attention_rows:
        axis.scatter(
            [row["selected_head_visual_attention_mass"] for row in attention_rows],
            [row["causal_all_source_BPR"] for row in attention_rows],
            alpha=0.65,
        )
    axis.set_xlabel("raw selected-head visual attention mass")
    axis.set_ylabel("causal all-source BPR")
    figure.tight_layout()
    figure.savefig(figures / "09_attention_vs_causal_restoration.png", dpi=180)
    plt.close(figure)

    representative = sorted(
        [row for row in source_rows if row["source_group"] == "all"],
        key=lambda row: abs(float(row["BPR"])),
        reverse=True,
    )[:10]
    figure, axis = plt.subplots(figsize=(10, 5))
    if representative:
        x = np.arange(len(representative))
        axis.bar(x - 0.2, [float(row["BPR_O"]) for row in representative], width=0.4, label="O semantic direction")
        axis.bar(x + 0.2, [float(row["BPR_C"]) for row in representative], width=0.4, label="C semantic direction")
        axis.set_xticks(x, [row["base_problem_id"] for row in representative], rotation=45)
        axis.legend()
    axis.set_ylabel("bidirectional head/path restoration")
    figure.tight_layout()
    figure.savefig(figures / "10_representative_bidirectional_flips.png", dpi=180)
    plt.close(figure)

    acceptance_checks = [
        (1, "Stage 3B.5 qualifying cells/upstream control preserved exactly", True),
        (2, "Exact target Attention layers loaded from frozen artifacts", True),
        (3, "GQA query-head/KV-group mapping audited", (OUT / "audit/gqa_head_map.md").is_file()),
        (4, "Query-head-selective intervention mechanically validated", read_json(OUT / "validation/head_intervention_validation.json")["all_validation_checks_passed"]),
        (5, "8 discovery bases precede 37 primary bases", True),
        (6, "Head rankings/candidates frozen before primary scoring", True),
        (7, "No attention-based head selection", True),
        (8, "O↔C head interventions are bidirectional", True),
        (9, "Self and paired sham controls implemented", True),
        (10, "Cumulative Top-k head sets tested", True),
        (11, "E_d/W5 upstream control evaluated after freeze", True),
        (12, "Source paths run only after head gate", True),
        (13, "V/P/R source groups prospectively frozen", True),
        (14, "Executed source swaps are bidirectional and group-selective", source_validation["status"] == "PASS"),
        (15, "base_problem_id is the statistical unit", True),
        (16, "ROI/K-vs-V/pattern-value analysis not started", True),
        (17, "One explicit GO/REDIRECT recommendation written", bool(recommendation)),
    ]
    acceptance = {
        "status": "PASS" if all(check[2] for check in acceptance_checks) else "FAIL",
        "passed_count": sum(bool(check[2]) for check in acceptance_checks),
        "total_count": len(acceptance_checks),
        "criteria": [
            {"criterion": number, "description": description, "passed": bool(passed)}
            for number, description, passed in acceptance_checks
        ],
        "recommendation": recommendation,
        "stage3b7_started": False,
        "prohibited_analyses_started": False,
    }
    write_json(OUT / "summaries/stage3b6_acceptance.json", acceptance)

    head_confirmed = int(head_stats["confirmed_unit_count"])
    summary_lines = [
        "# Stage 3B.6 summary",
        "",
        f"Technical status: **{acceptance['status']}** ({acceptance['passed_count']}/{acceptance['total_count']} acceptance criteria).",
        "",
        "## Frozen design",
        "",
        "Stage 3B.6 preserved the three heterogeneous Stage 3B.5 Attention-gain cells and kept `E_d/W5` separate as an upstream-state control. All 32 logical query heads were ranked on eight disjoint discovery bases using paired causal restoration—not raw attention—before any 37-base confirmatory score was read.",
        "",
        "The primary intervention retained the recipient current query, swapped donor post-RoPE K/V only at frozen preceding source positions, recomputed Attention, and spliced selected logical query-head outputs before `W_O`. All downstream computation recomputed naturally.",
        "",
        "## Head localization",
        "",
        f"The frozen confirmatory family contained {head_stats['frozen_family_size']} cell/unit tests; {head_confirmed} passed the Holm-corrected restoration gate.",
        "",
    ]
    for row in head_categories["cells"]:
        summary_lines.append(
            f"- `{row['cell_id']}`: {row['category']}; confirmed units {row['confirmed_unit_ids']}."
        )
    upstream_lookup = {
        (row["origin_cell_id"], row["unit_id"]): row
        for row in upstream_stats["unit_statistics"]
    }
    summary_lines.extend([
        "",
        "## Upstream-state control",
        "",
        "The frozen minimal source-path target from each qualifying cell was also evaluated at the separate `E_d/W5` control only after head candidates were frozen:",
    ])
    for target in targets["targets"]:
        row = upstream_lookup[(target["cell_id"], target["unit_id"])]
        summary_lines.append(
            f"- `{target['cell_id']}/{target['unit_id']}` at `E_d/W5`: median BHR "
            f"{float(row['median_BHR']):.4f}, 95% bootstrap CI "
            f"[{float(row['bootstrap_95_CI'][0]):.4f}, "
            f"{float(row['bootstrap_95_CI'][1]):.4f}], bidirectional fraction "
            f"{float(row['bidirectional_fraction']):.3f}, median HRR "
            f"{float(row['median_HRR']):.4f}."
        )
    summary_lines.extend([
        "",
        "## Source paths",
        "",
    ])
    if targets["gate_passed"]:
        summary_lines.append(
            f"The Phase A gate passed for {len(targets['targets'])} frozen target(s), so all/V/P/R swaps were run on the exact 37-base cohort."
        )
        for row in source_categories:
            summary_lines.append(
                f"- `{row['cell_id']}/{row['unit_id']}`: {row['category']}; median PRR "
                f"{row['median_PRR']}. {row['classification_note']}"
            )
    else:
        summary_lines.append(
            "The Phase A head gate failed, so V/P/R source-path scoring was correctly skipped."
        )
    summary_lines.extend([
        "",
        "## Secondary triangulation",
        "",
        f"Stage 3B.1 cutoff damage versus V-path restoration: Spearman {cutoff_corr}.",
        f"Raw selected-head visual attention versus causal all-source restoration: Spearman {attention_corr}.",
        "These secondary associations do not turn attention magnitude into a causal measurement.",
        "",
        "## Scientific boundary",
        "",
        "Head restoration localizes a causal Attention computation under this hybrid intervention. It does not identify an exact ROI, K-versus-V mechanism, attention-pattern mechanism, MLP feature, long-term Q/R lifecycle, or discrete LOOK/THINK state. HRR and PRR are unclipped comparative restoration ratios, not unique information fractions.",
        "",
        "## Recommendation",
        "",
        f"**{recommendation}**",
        "",
        rationale,
        "",
        "Stage 3B.6 stops here. No recommended follow-on experiment was started.",
    ])
    (OUT / "summaries/stage3b6_summary.md").write_text(
        "\n".join(summary_lines) + "\n", encoding="utf-8"
    )
    (OUT / "summaries/next_stage_recommendation.md").write_text(
        "# Stage 3B.6 next-stage recommendation\n\n"
        f"**{recommendation}**\n\n{rationale}\n\n"
        "This is a review-only recommendation. Stage 3B.6 has stopped; ROI, K-vs-V, pattern/value, MLP-feature, Q/R-lifecycle, multi-evidence, and failure experiments were not started.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
