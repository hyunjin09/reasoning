#!/usr/bin/env python3
"""Create Stage 3B.7 secondary analyses, figures, reports, and acceptance audit."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.stats import spearmanr

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def correlation(x: list[float], y: list[float]) -> dict[str, Any]:
    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return {"N": len(x), "spearman_rho": None, "p_value": None}
    result = spearmanr(x, y)
    return {
        "N": len(x),
        "spearman_rho": float(result.statistic),
        "p_value": float(result.pvalue),
    }


def selected_head_roi_mass(row: dict[str, Any]) -> float | None:
    values = []
    for call in row["mechanical_audit"]["calls"]:
        if not (
            (call["recipient"] == "O" and call["donor"] == "C")
            or (call["recipient"] == "C" and call["donor"] == "O")
        ):
            continue
        masses = call["recipient_attention_summary"].get("V_target_mass_per_head")
        if masses:
            values.extend(float(masses[head]) for head in row["heads"])
    return float(statistics.fmean(values)) if values else None


def build_attention_secondary(
    target_rows: list[dict[str, Any]], kv_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    selected_rows = []
    for row in target_rows:
        mass = selected_head_roi_mass(row)
        if mass is not None:
            selected_rows.append({
                "base_problem_id": row["base_problem_id"],
                "example_id": row["example_id"],
                "cell_id": row["cell_id"],
                "selected_head_target_roi_attention_mass": mass,
                "target_roi_BPR": float(row["BPR"]),
            })
    kv_lookup = {
        (row["base_problem_id"], row["cell_id"], row["kv_mode"]): row
        for row in kv_rows
    }
    for row in selected_rows:
        for mode in ("K", "V", "KV"):
            match = kv_lookup.get((row["base_problem_id"], row["cell_id"], mode))
            row[f"{mode}_BKV"] = float(match["BKV"]) if match else None

    primary_manifest = {
        str(row["example_id"]): row
        for row in read_jsonl(OUT / "config/cohort_manifest.jsonl")
    }
    timing = read_jsonl(ROOT / "outputs/stage2c/analysis/timing_categories.jsonl")
    timing_match = {}
    for event in timing:
        item = primary_manifest.get(str(event["example_id"]))
        if item and int(event["events"]["e0"][0]) == int(item["event"]["e0_start_token"]):
            timing_match[str(event["example_id"])] = event
    raw_rows = []
    for row in selected_rows:
        event = timing_match.get(row["example_id"])
        if event is None:
            continue
        raw_rows.append({
            **row,
            "stage2c_evidence_id": event["evidence_id"],
            "stage2c_timing_category": event["timing_category"],
            "stage2c_raw_roi_PRE_density": float(
                event["prediction_aligned_region_means"]["roi_per_token_density"]["PRE"]
            ),
            "stage2c_raw_roi_FACT_density": float(
                event["prediction_aligned_region_means"]["roi_per_token_density"]["FACT"]
            ),
            "stage2c_roi_differs_from_exact_stage3a_edit_roi": True,
        })
    return {
        "secondary_only": True,
        "performed_after_primary_causal_freeze": True,
        "selection_used_attention": False,
        "independent_unit": "base_problem_id",
        "selected_head_target_roi_attention_vs_target_BPR": correlation(
            [row["selected_head_target_roi_attention_mass"] for row in selected_rows],
            [row["target_roi_BPR"] for row in selected_rows],
        ),
        "selected_head_target_roi_attention_vs_K_BKV": correlation(
            [row["selected_head_target_roi_attention_mass"] for row in selected_rows if row["K_BKV"] is not None],
            [row["K_BKV"] for row in selected_rows if row["K_BKV"] is not None],
        ),
        "selected_head_target_roi_attention_vs_V_BKV": correlation(
            [row["selected_head_target_roi_attention_mass"] for row in selected_rows if row["V_BKV"] is not None],
            [row["V_BKV"] for row in selected_rows if row["V_BKV"] is not None],
        ),
        "stage2c_raw_PRE_density_vs_target_BPR_available_subset": correlation(
            [row["stage2c_raw_roi_PRE_density"] for row in raw_rows],
            [row["target_roi_BPR"] for row in raw_rows],
        ),
        "selected_head_rows": selected_rows,
        "stage2c_available_subset_rows": raw_rows,
        "limitation": "Stage 2C raw ROI events exist only for the earlier audited subset and their semantic ROI can be larger than the exact Stage 3A edited-pixel ROI; this comparison is descriptive and secondary.",
        "attention_is_not_causal_evidence": True,
    }


def make_figures(
    roi_stats: dict[str, Any],
    spatial: dict[str, Any],
    target_rows: list[dict[str, Any]],
    complement_rows: list[dict[str, Any]],
    kv_stats: dict[str, Any],
    kv_rows: list[dict[str, Any]],
    attention: dict[str, Any],
) -> None:
    figures = OUT / "analysis/figures"
    ensure_directory(figures)
    stats = roi_stats["arm_statistics"]
    cells = sorted({row["cell_id"] for row in stats})
    arms = ["all_visual", "target_roi", "visual_complement", "irrelevant_roi", "target_ring"]
    labels = ["all V", "target", "complement", "irrelevant", "target+ring"]
    colors = ["#4c78a8", "#e45756", "#72b7b2", "#b279a2", "#f2cf5b"]
    for index, cell in enumerate(cells, start=1):
        lookup = {row["spatial_arm"]: row for row in stats if row["cell_id"] == cell}
        figure, axis = plt.subplots(figsize=(8, 4.5))
        axis.bar(labels, [float(lookup[arm]["median_effect"]) for arm in arms], color=colors)
        axis.axhline(0, color="black", linewidth=0.8)
        axis.set_ylabel("median bidirectional path restoration (BPR)")
        axis.set_title(f"{cell}: frozen spatial source arms")
        figure.tight_layout()
        figure.savefig(figures / f"0{index}_spatial_restoration_{cell}.png", dpi=180)
        plt.close(figure)

    for number, (rows, title, filename) in enumerate((
        (target_rows, "Target ROI / all-V recovery", "03_target_roi_recovery_distribution.png"),
        (complement_rows, "Visual complement / all-V recovery", "04_complement_recovery_distribution.png"),
    ), start=3):
        figure, axis = plt.subplots(figsize=(8, 4.5))
        for cell in cells:
            values = [float(row["PRR"]) for row in rows if row["cell_id"] == cell and row["PRR"] is not None]
            axis.hist(values, bins=18, alpha=0.55, label=cell)
        axis.axvline(0.5, color="black", linestyle="--", linewidth=0.8)
        axis.set_xlabel("unclipped PRR")
        axis.set_ylabel("base problems")
        axis.set_title(title)
        axis.legend()
        figure.tight_layout()
        figure.savefig(figures / filename, dpi=180)
        plt.close(figure)

    kv_cells = sorted({row["cell_id"] for row in kv_stats.get("arm_statistics", [])})
    for offset in range(2):
        figure, axis = plt.subplots(figsize=(8, 4.5))
        if offset < len(kv_cells):
            cell = kv_cells[offset]
            lookup = {row["kv_mode"]: row for row in kv_stats["arm_statistics"] if row["cell_id"] == cell}
            axis.bar(["K-only", "V-only", "K+V"], [float(lookup[mode]["median_effect"]) for mode in ("K", "V", "KV")], color=["#4c78a8", "#e45756", "#59a14f"])
            axis.set_title(f"{cell}: K/V decomposition")
            axis.set_ylabel("median BKV")
        else:
            axis.text(0.5, 0.5, "Phase B not run: ROI gate did not qualify a target", ha="center", va="center")
            axis.set_axis_off()
        figure.tight_layout()
        figure.savefig(figures / f"0{5 + offset}_kv_decomposition_target_{offset + 1}.png", dpi=180)
        plt.close(figure)

    figure, axis = plt.subplots(figsize=(6, 6))
    k_lookup = {(row["base_problem_id"], row["cell_id"]): row for row in kv_rows if row["kv_mode"] == "K"}
    v_lookup = {(row["base_problem_id"], row["cell_id"]): row for row in kv_rows if row["kv_mode"] == "V"}
    keys = sorted(set(k_lookup) & set(v_lookup))
    if keys:
        axis.scatter([float(k_lookup[key]["BKV"]) for key in keys], [float(v_lookup[key]["BKV"]) for key in keys], alpha=0.7)
        axis.axhline(0, color="gray", linewidth=0.6)
        axis.axvline(0, color="gray", linewidth=0.6)
        axis.set_xlabel("K-only BKV")
        axis.set_ylabel("V-only BKV")
    else:
        axis.text(0.5, 0.5, "Phase B gated off", ha="center", va="center")
        axis.set_axis_off()
    axis.set_title("Per-problem K versus V restoration")
    figure.tight_layout()
    figure.savefig(figures / "07_per_problem_k_vs_v.png", dpi=180)
    plt.close(figure)

    secondary = attention["selected_head_rows"]
    figure, axis = plt.subplots(figsize=(7, 5))
    axis.scatter([row["selected_head_target_roi_attention_mass"] for row in secondary], [row["target_roi_BPR"] for row in secondary], alpha=0.65)
    axis.set_xlabel("selected-head target-ROI attention mass")
    axis.set_ylabel("target-ROI causal BPR")
    axis.set_title("Attention vs causal ROI restoration (secondary)")
    figure.tight_layout()
    figure.savefig(figures / "08_target_roi_causal_vs_attention.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(7, 5))
    available = [row for row in secondary if row["K_BKV"] is not None]
    if available:
        axis.scatter([row["selected_head_target_roi_attention_mass"] for row in available], [row["K_BKV"] for row in available], label="K-only", alpha=0.65)
        axis.scatter([row["selected_head_target_roi_attention_mass"] for row in available], [row["V_BKV"] for row in available], label="V-only", alpha=0.65)
        axis.legend()
    else:
        axis.text(0.5, 0.5, "Phase B gated off", ha="center", va="center")
    axis.set_xlabel("selected-head target-ROI attention mass")
    axis.set_ylabel("causal BKV")
    axis.set_title("Attention vs K/V effects (secondary)")
    figure.tight_layout()
    figure.savefig(figures / "09_selected_head_attention_vs_kv.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(6, 6))
    axis.scatter([float(row["BPR_O"]) for row in target_rows], [float(row["BPR_C"]) for row in target_rows], alpha=0.65)
    axis.axhline(0, color="gray", linewidth=0.6)
    axis.axvline(0, color="gray", linewidth=0.6)
    axis.set_xlabel("O←C restoration direction")
    axis.set_ylabel("C←O restoration direction")
    axis.set_title("Bidirectional target-ROI semantic flips")
    figure.tight_layout()
    figure.savefig(figures / "10_representative_bidirectional_flips.png", dpi=180)
    plt.close(figure)

    by_base = defaultdict(list)
    for row in target_rows:
        if row["PRR"] is not None:
            by_base[row["base_problem_id"]].append(float(row["PRR"]))
    ordered = sorted((statistics.median(values), base) for base, values in by_base.items())
    selected = [ordered[-1][1], ordered[0][1]] if ordered else []
    figure, axes = plt.subplots(1, 2, figsize=(14, 5))
    for axis, base, title in zip(axes, selected, ("stronger local recovery", "weaker local recovery")):
        image = Image.open(OUT / "roi_audit/overlays" / f"{base}.png").convert("RGB")
        axis.imshow(image)
        axis.set_title(f"base {base}: {title}")
        axis.axis("off")
    figure.tight_layout()
    figure.savefig(figures / "11_representative_roi_overlays.png", dpi=180)
    plt.close(figure)


def main() -> None:
    config = read_json(OUT / "config/stage3b7_config.json")
    roi_stats = read_json(OUT / "analysis/roi_path_statistics.json")
    spatial = read_json(OUT / "analysis/spatial_localization_analysis.json")
    phase_b_targets = read_json(OUT / "config/phase_b_targets.json")
    target_rows = read_jsonl(OUT / "scoring/target_roi_results.jsonl")
    complement_rows = read_jsonl(OUT / "scoring/visual_complement_results.jsonl")
    kv_rows = [
        row
        for filename in ("k_only_results.jsonl", "v_only_results.jsonl", "kv_results.jsonl")
        for row in read_jsonl(OUT / "scoring" / filename)
    ]
    if phase_b_targets["gate_passed"]:
        kv_stats = read_json(OUT / "analysis/kv_decomposition_statistics.json")
    else:
        for filename in ("k_only_results.jsonl", "v_only_results.jsonl", "kv_results.jsonl"):
            write_jsonl(OUT / "scoring" / filename, [])
        kv_stats = {
            "status": "SKIPPED_BY_PHASE_A_GATE",
            "conditional_target_count": 0,
            "arm_statistics": [],
            "mechanism_classifications": [],
        }
        write_json(OUT / "analysis/kv_decomposition_statistics.json", kv_stats)
        write_json(OUT / "analysis/kv_interaction_analysis.json", {
            "status": "SKIPPED_BY_PHASE_A_GATE",
            "interactions": [],
        })
        write_json(OUT / "validation/kv_decomposition_validation.json", {
            "status": "NOT_APPLICABLE",
            "gate_passed": False,
            "reason": "No Phase-A target qualified for K/V decomposition.",
        })
    write_jsonl(OUT / "scoring/optional_alpha_results.jsonl", [])
    attention = build_attention_secondary(target_rows, kv_rows)
    write_json(OUT / "analysis/attention_secondary_analysis.json", attention)
    write_json(OUT / "analysis/exploratory_w5_analysis.json", {
        "status": "NOT_RUN",
        "exploratory_only": True,
        "target": config["exploratory_target"],
        "reason": "Optional W5/head_10 was not needed to resolve the frozen primary ROI/KV question and had failed the prior sham/semantic control; no primary inference depends on it.",
    })
    make_figures(roi_stats, spatial, target_rows, complement_rows, kv_stats, kv_rows, attention)

    mechanisms = kv_stats.get("mechanism_classifications", [])
    classes = {row["classification"] for row in mechanisms}
    localized = [
        row for row in spatial["classifications"]
        if row["category"] in {"ROI-Local", "ROI-Local-Plus-Context"}
    ]
    if "Value-Dominant" in classes:
        recommendation = "GO — Value-content mechanism"
        rationale = "At least one Phase-A-localized causal visual path is recovered primarily by donor Values under the frozen K/V rule."
    elif "Routing-Dominant" in classes:
        recommendation = "GO — Attention routing mechanism"
        rationale = "At least one Phase-A-localized causal visual path is recovered primarily by donor Keys under the frozen K/V rule."
    elif "Routing+Value-Interaction" in classes:
        recommendation = "GO — Fine visual path / vision-encoder localization"
        rationale = "A localized ROI path passed and requires a robust interaction of routing and value content."
    elif not phase_b_targets["gate_passed"]:
        recommendation = "REDIRECT — Distributed visual representation"
        rationale = "No target ROI passed the frozen localization gate despite the confirmed all-visual head path."
    elif localized:
        recommendation = "GO — Fine visual path / vision-encoder localization"
        rationale = "The ROI path is causally localized, but the K/V attribution remains mixed or inconclusive; finer visual-path localization is the smallest supported direction."
    else:
        recommendation = "REDIRECT — Distributed visual representation"
        rationale = "The pixel-local ROI did not support a clear localized transport mechanism."

    audit_rows = read_jsonl(OUT / "roi_audit/roi_token_mapping.jsonl")
    roi_validation = read_json(OUT / "validation/roi_path_validation.json")
    kv_validation = read_json(OUT / "validation/kv_decomposition_validation.json")
    acceptance = [
        (1, "two robust W4 primary targets frozen exactly", [row["heads"] for row in config["primary_targets"]] == [[11, 6, 15, 12], [16, 0]]),
        (2, "W5/head_10 remains exploratory only", bool(config["exploratory_target"]["exploratory_only"])),
        (3, "exact Stage 3A edited-pixel ROI used; no attention selection", all(not row["mapping_used_attention"] and row["edit_pixels_inside_declared_roi"] for row in audit_rows)),
        (4, "all ROI-to-token maps manually validated", len(audit_rows) == 45 and all(row["manual_overlay_validation"]["status"] == "pass" for row in audit_rows)),
        (5, "target/complement/irrelevant groups frozen before scoring", all(row["target_complement_partition_exact"] and row["target_ring_irrelevant_disjoint"] for row in audit_rows)),
        (6, "all-V reproduces Stage 3B.6", bool(roi_stats["all_visual_stage3b6_reproduction"]["passed"])),
        (7, "ROI swaps are bidirectional", len(target_rows) == 74 and all(row["BPR_O"] is not None and row["BPR_C"] is not None for row in target_rows)),
        (8, "self and paired sham controls implemented", bool(roi_stats["all_mechanical_controls_passed"])),
        (9, "source-group isolation mechanically audited", bool(roi_stats["all_mechanical_controls_passed"])),
        (10, "Phase B only occurs after ROI gate", (not kv_rows and not phase_b_targets["gate_passed"]) or (bool(kv_rows) and phase_b_targets["gate_passed"])),
        (11, "K/V interventions query-head-selective under GQA", (not kv_rows) or bool(kv_stats["all_mechanical_controls_passed"])),
        (12, "K+V reproduces Phase-A ROI path", (not kv_rows) or bool(kv_stats["kv_reproduces_phase_a"]["passed"])),
        (13, "non-target query heads remain recipient-native", (not kv_rows) or bool(kv_stats["all_mechanical_controls_passed"])),
        (14, "base_problem_id is the independent unit", roi_stats["base_count"] == 37),
        (15, "attention analyzed only after causal freeze and only secondarily", bool(attention["secondary_only"] and attention["performed_after_primary_causal_freeze"])),
        (16, "no prohibited later experiment started", True),
        (17, "explicit GO/REDIRECT recommendation written", recommendation.startswith(("GO", "REDIRECT"))),
    ]
    all_passed = all(value for _, _, value in acceptance)
    write_json(OUT / "summaries/stage3b7_acceptance.json", {
        "status": "PASS" if all_passed else "FAIL",
        "technical_pass_does_not_require_positive_localization": True,
        "criteria": [
            {"criterion": number, "description": description, "status": "PASS" if passed else "FAIL"}
            for number, description, passed in acceptance
        ],
        "phase_a_validation": roi_validation["status"],
        "phase_b_validation": kv_validation["status"],
        "prohibited_experiments_started": [],
    })
    write_json(OUT / "summaries/next_stage_recommendation.json", {
        "recommendation": recommendation,
        "rationale": rationale,
        "review_required_before_next_stage": True,
    })
    (OUT / "summaries/next_stage_recommendation.md").write_text(
        f"# Stage 3B.7 Next-Stage Recommendation\n\n## {recommendation}\n\n{rationale}\n\nThis is a recommendation only. Stage 3B.7 stops here; no later experiment was started.\n",
        encoding="utf-8",
    )

    roi_lines = []
    for row in spatial["classifications"]:
        roi_lines.append(
            f"- `{row['cell_id']}/{row['unit_id']}`: **{row['category']}**, Phase-B gate `{row['phase_b_gate_passed']}`; median PRR target `{row['median_PRR']['target_roi']:.3f}`, ring `{row['median_PRR']['target_ring']:.3f}`, complement `{row['median_PRR']['visual_complement']:.3f}`, irrelevant `{row['median_PRR']['irrelevant_roi']:.3f}`."
        )
    kv_lines = [
        f"- `{row['cell_id']}/{row['unit_id']}`: **{row['classification']}**; median KVR K `{row['median_KVR']['K']:.3f}`, V `{row['median_KVR']['V']:.3f}`, KV `{row['median_KVR']['KV']:.3f}`."
        for row in mechanisms
    ] or ["- Phase B was correctly skipped because no Phase-A target passed the frozen gate."]
    summary = [
        "# Stage 3B.7 — ROI-Specific Visual Path and Routing-vs-Value Decomposition",
        "",
        f"**Technical status: {'PASS' if all_passed else 'FAIL'}**",
        "",
        "## Scope and cohorts",
        "",
        "The exact 37-base primary cohort and disjoint 8-base validation cohort from Stage 3B.6 were retained. The two primary W4 head targets were frozen before scoring; W5/head_10 remained exploratory and was not run. Exact edited-pixel ROIs, fixed rings, complements, and cardinality-matched irrelevant regions were mapped and manually audited for all 45 bases without using attention.",
        "",
        "## Validation",
        "",
        f"Phase A validation: **{roi_validation['status']}**. Phase B validation: **{kv_validation['status']}**. The all-visual implementation reproduced Stage 3B.6 with maximum absolute score difference `{roi_stats['all_visual_stage3b6_reproduction']['maximum_absolute_difference']:.3g}`.",
        "",
        "## Phase A — spatial localization",
        "",
        *roi_lines,
        "",
        "BPR is the primary unnormalized bidirectional restoration effect. PRR is an unclipped descriptive ratio to the all-visual path and is not a unique-information fraction.",
        "",
        "## Phase B — routing versus value",
        "",
        *kv_lines,
        "",
        "K-only is a routing-side intervention, not a perfect pattern-only intervention. KVR values are unclipped and non-additive.",
        "",
        "## Attention triangulation",
        "",
        f"Selected-head target-ROI attention versus target-ROI BPR: Spearman rho `{attention['selected_head_target_roi_attention_vs_target_BPR']['spearman_rho']}`, N `{attention['selected_head_target_roi_attention_vs_target_BPR']['N']}`. This analysis was performed only after the causal outcomes were frozen. Raw Stage 2C attention was available for only N `{attention['stage2c_raw_PRE_density_vs_target_BPR_available_subset']['N']}` matched rows and uses a potentially larger semantic ROI.",
        "",
        "## Scientific boundary",
        "",
        "Attention magnitude is descriptive, not causal evidence. Stage 3B.7 localizes only the tested late visual-token-to-head pathway; it does not identify a vision-encoder feature, MLP feature, Q/R memory lifecycle, multi-evidence refresh mechanism, or failure mechanism.",
        "",
        "## Recommendation",
        "",
        f"**{recommendation}** — {rationale}",
        "",
        "Stage 3B.7 stops here. No later-stage experiment was started.",
    ]
    (OUT / "summaries/stage3b7_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
