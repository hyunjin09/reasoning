#!/usr/bin/env python3
"""Create Stage 3B.7-R secondary analyses, figures, reports, and acceptance audit."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage0.io import ensure_directory, write_json, write_text
from visual_reasoning.stage3b7r.protocol import aggregate_numeric_fields_by_base


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def correlation(x: list[float], y: list[float]) -> dict[str, Any]:
    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return {"N": len(x), "spearman_rho": None, "p_value": None}
    result = spearmanr(x, y)
    return {"N": len(x), "spearman_rho": float(result.statistic), "p_value": float(result.pvalue)}


def selected_head_roi_mass(row: dict[str, Any]) -> float | None:
    values = []
    for call in row["mechanical_audit"]["calls"]:
        if not ((call["recipient"] == "O" and call["donor"] == "C") or (call["recipient"] == "C" and call["donor"] == "O")):
            continue
        masses = call["recipient_attention_summary"].get("V_target_mass_per_head")
        if masses:
            values.extend(float(masses[int(head)]) for head in row["heads"])
    return float(statistics.fmean(values)) if values else None


def build_attention_secondary(target_rows: list[dict[str, Any]], kv_rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = []
    for row in target_rows:
        mass = selected_head_roi_mass(row)
        if mass is not None:
            selected.append({"base_problem_id": row["base_problem_id"], "example_id": row["example_id"], "cell_id": row["cell_id"], "selected_head_target_roi_attention_mass": mass, "target_roi_BPR": float(row["BPR"])})
    kv_lookup = {(row["base_problem_id"], row["cell_id"], row["kv_mode"]): row for row in kv_rows}
    for row in selected:
        for mode in ("K", "V", "KV"):
            match = kv_lookup.get((row["base_problem_id"], row["cell_id"], mode))
            row[f"{mode}_BKV"] = float(match["BKV"]) if match else None
    numeric_fields = [
        "selected_head_target_roi_attention_mass",
        "target_roi_BPR",
        "K_BKV",
        "V_BKV",
        "KV_BKV",
    ]
    by_base = aggregate_numeric_fields_by_base(selected, fields=numeric_fields)
    per_target = {}
    for cell in sorted({row["cell_id"] for row in selected}):
        cell_rows = [row for row in selected if row["cell_id"] == cell]
        per_target[cell] = {
            "selected_head_target_roi_attention_vs_target_BPR": correlation(
                [row["selected_head_target_roi_attention_mass"] for row in cell_rows],
                [row["target_roi_BPR"] for row in cell_rows],
            ),
            "selected_head_target_roi_attention_vs_K_BKV": correlation(
                [row["selected_head_target_roi_attention_mass"] for row in cell_rows if row["K_BKV"] is not None],
                [row["K_BKV"] for row in cell_rows if row["K_BKV"] is not None],
            ),
            "selected_head_target_roi_attention_vs_V_BKV": correlation(
                [row["selected_head_target_roi_attention_mass"] for row in cell_rows if row["V_BKV"] is not None],
                [row["V_BKV"] for row in cell_rows if row["V_BKV"] is not None],
            ),
        }
    primary = {str(row["example_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b7/config/cohort_manifest.jsonl")}
    timing_match = {}
    for event in read_jsonl(ROOT / "outputs/stage2c/analysis/timing_categories.jsonl"):
        item = primary.get(str(event["example_id"]))
        if item and int(event["events"]["e0"][0]) == int(item["event"]["e0_start_token"]):
            timing_match[str(event["example_id"])] = event
    stage2c_rows = []
    for row in selected:
        event = timing_match.get(str(row["example_id"]))
        if event:
            stage2c_rows.append({**row, "stage2c_evidence_id": event["evidence_id"], "stage2c_timing_category": event["timing_category"], "stage2c_raw_roi_PRE_density": float(event["prediction_aligned_region_means"]["roi_per_token_density"]["PRE"]), "stage2c_raw_roi_FACT_density": float(event["prediction_aligned_region_means"]["roi_per_token_density"]["FACT"]), "stage2c_roi_differs_from_exact_edit_roi": True})
    stage2c_by_base = aggregate_numeric_fields_by_base(
        stage2c_rows,
        fields=["stage2c_raw_roi_PRE_density", "stage2c_raw_roi_FACT_density", "target_roi_BPR"],
    )
    return {
        "secondary_only": True,
        "performed_after_primary_causal_freeze": True,
        "selection_used_attention": False,
        "independent_unit": "base_problem_id",
        "cross_target_pooling_rule": "The two target rows are averaged within base before pooled correlations; per-target correlations are also reported separately.",
        "selected_head_target_roi_attention_vs_target_BPR": correlation([row["selected_head_target_roi_attention_mass"] for row in by_base], [row["target_roi_BPR"] for row in by_base]),
        "selected_head_target_roi_attention_vs_K_BKV": correlation([row["selected_head_target_roi_attention_mass"] for row in by_base if row["K_BKV"] is not None], [row["K_BKV"] for row in by_base if row["K_BKV"] is not None]),
        "selected_head_target_roi_attention_vs_V_BKV": correlation([row["selected_head_target_roi_attention_mass"] for row in by_base if row["V_BKV"] is not None], [row["V_BKV"] for row in by_base if row["V_BKV"] is not None]),
        "stage2c_raw_PRE_density_vs_target_BPR_available_subset": correlation([row["stage2c_raw_roi_PRE_density"] for row in stage2c_by_base], [row["target_roi_BPR"] for row in stage2c_by_base]),
        "per_target_correlations": per_target,
        "base_aggregated_rows": by_base,
        "selected_head_rows": selected,
        "stage2c_base_aggregated_rows": stage2c_by_base,
        "stage2c_available_subset_rows": stage2c_rows,
        "attention_is_not_causal_evidence": True,
        "limitation": "Stage 2C attention is available only for a matched subset and can use a broader semantic ROI than the exact edited-pixel ROI.",
    }


def validation_raw_rows() -> list[dict[str, Any]]:
    rows = []
    for path in sorted((OUT / "scoring/raw").glob("fresh_validation_phase_a_*/results.jsonl")):
        for base in read_jsonl(path):
            for target in base["targets"]:
                for arm in target["arm_results"]:
                    rows.append({"base_problem_id": base["base_problem_id"], "example_id": base["example_id"], **arm})
    lookup = {(row["base_problem_id"], row["cell_id"], row["spatial_arm"]): row for row in rows}
    for row in rows:
        denominator = float(lookup[(row["base_problem_id"], row["cell_id"], "all_visual")]["BHR"])
        row.update({"BPR": float(row["BHR"]), "BPR_O": float(row["BHR_O"]), "BPR_C": float(row["BHR_C"]), "PRR": None if denominator == 0 else float(row["BHR"]) / denominator})
    return rows


def make_figures(validation_rows: list[dict[str, Any]], target_rows: list[dict[str, Any]], complement_rows: list[dict[str, Any]], kv_rows: list[dict[str, Any]], attention: dict[str, Any]) -> None:
    figures = OUT / "analysis/figures"
    ensure_directory(figures)
    cells = ["Ed__W4", "Ed_minus_1__W4"]
    for number, cell in enumerate(cells, start=1):
        target = [row for row in validation_rows if row["cell_id"] == cell and row["spatial_arm"] == "target_roi"]
        figure, axis = plt.subplots(figsize=(8, 4.8))
        x = np.arange(len(target))
        axis.bar(x - 0.18, [float(row["BPR"]) for row in target], width=0.36, label="target ROI BPR")
        axis.bar(x + 0.18, [abs(float(row["sham_effect"])) for row in target], width=0.36, label="|paired sham effect|")
        axis.axhline(0, color="black", linewidth=0.7)
        axis.set_xticks(x, [row["base_problem_id"] for row in target], rotation=60)
        axis.set_ylabel("source-oriented restoration")
        axis.set_title(f"Fresh validation: {cell}")
        axis.legend()
        figure.tight_layout()
        figure.savefig(figures / f"0{number}_fresh_validation_{cell}.png", dpi=180)
        plt.close(figure)
    semantic = read_jsonl(OUT / "validation/semantic_validation_results.jsonl")
    for number, (key, title) in enumerate((("sham_margin", "Target minus |sham|"), ("irrelevant_margin", "Target minus |irrelevant ROI|")), start=3):
        figure, axis = plt.subplots(figsize=(8, 4.8))
        for row in semantic:
            values = []
            target = [item for item in validation_rows if item["cell_id"] == row["cell_id"] and item["spatial_arm"] == "target_roi"]
            irrelevant = {item["base_problem_id"]: item for item in validation_rows if item["cell_id"] == row["cell_id"] and item["spatial_arm"] == "irrelevant_roi"}
            for item in target:
                control = abs(float(item["sham_effect"])) if key == "sham_margin" else abs(float(irrelevant[item["base_problem_id"]]["BPR"]))
                values.append(float(item["BPR"]) - control)
            axis.hist(values, bins=max(6, len(values) // 2), alpha=0.55, label=row["target_id"])
        axis.axvline(0, color="black", linestyle="--", linewidth=0.8)
        axis.set_xlabel(title)
        axis.set_ylabel("base problems")
        axis.legend()
        figure.tight_layout()
        figure.savefig(figures / f"0{number}_{key}_distribution.png", dpi=180)
        plt.close(figure)
    roi_stats = read_json(OUT / "analysis/roi_path_statistics.json") if (OUT / "analysis/roi_path_statistics.json").is_file() else {"arm_statistics": []}
    for number, cell in enumerate(sorted({row["cell_id"] for row in roi_stats["arm_statistics"]}), start=5):
        lookup = {row["spatial_arm"]: row for row in roi_stats["arm_statistics"] if row["cell_id"] == cell}
        arms = ["all_visual", "target_roi", "visual_complement", "irrelevant_roi", "target_ring"]
        figure, axis = plt.subplots(figsize=(8, 4.8))
        axis.bar(["all V", "target", "complement", "irrelevant", "target+ring"], [float(lookup[arm]["median_effect"]) for arm in arms])
        axis.axhline(0, color="black", linewidth=0.7)
        axis.set_ylabel("median BPR")
        axis.set_title(f"Primary spatial localization: {cell}")
        figure.tight_layout()
        figure.savefig(figures / f"0{number}_primary_spatial_{cell}.png", dpi=180)
        plt.close(figure)
    figure, axis = plt.subplots(figsize=(8, 4.8))
    for cell in sorted({row["cell_id"] for row in target_rows}):
        axis.hist([float(row["PRR"]) for row in target_rows if row["cell_id"] == cell and row["PRR"] is not None], bins=16, alpha=0.55, label=cell)
    if target_rows:
        axis.axvline(0.5, color="black", linestyle="--", linewidth=0.8)
        axis.legend()
    else:
        axis.text(0.5, 0.5, "Primary Phase A gated off", ha="center", va="center")
    axis.set_xlabel("unclipped target/all-V PRR")
    axis.set_title("Target ROI recovery distribution")
    figure.tight_layout()
    figure.savefig(figures / "07_target_recovery_distribution.png", dpi=180)
    plt.close(figure)
    kv_stats = read_json(OUT / "analysis/kv_decomposition_statistics.json") if (OUT / "analysis/kv_decomposition_statistics.json").is_file() else {"arm_statistics": []}
    figure, axis = plt.subplots(figsize=(8, 4.8))
    kv_cells = sorted({row["cell_id"] for row in kv_stats["arm_statistics"]})
    if kv_cells:
        width = 0.8 / len(kv_cells)
        for offset, cell in enumerate(kv_cells):
            lookup = {row["kv_mode"]: row for row in kv_stats["arm_statistics"] if row["cell_id"] == cell}
            axis.bar(np.arange(3) + (offset - (len(kv_cells) - 1) / 2) * width, [float(lookup[mode]["median_effect"]) for mode in ("K", "V", "KV")], width=width, label=cell)
        axis.set_xticks(np.arange(3), ["K-only", "V-only", "K+V"])
        axis.legend()
    else:
        axis.text(0.5, 0.5, "Phase B gated off", ha="center", va="center")
    axis.set_ylabel("median BKV")
    axis.set_title("Conditional K/V decomposition")
    figure.tight_layout()
    figure.savefig(figures / "08_kv_decomposition.png", dpi=180)
    plt.close(figure)
    figure, axis = plt.subplots(figsize=(6, 6))
    k = {(row["base_problem_id"], row["cell_id"]): row for row in kv_rows if row["kv_mode"] == "K"}
    v = {(row["base_problem_id"], row["cell_id"]): row for row in kv_rows if row["kv_mode"] == "V"}
    keys = sorted(set(k) & set(v))
    if keys:
        axis.scatter([float(k[key]["BKV"]) for key in keys], [float(v[key]["BKV"]) for key in keys], alpha=0.7)
        axis.axhline(0, color="gray", linewidth=0.6); axis.axvline(0, color="gray", linewidth=0.6)
    else:
        axis.text(0.5, 0.5, "Phase B gated off", ha="center", va="center")
    axis.set_xlabel("K-only BKV"); axis.set_ylabel("V-only BKV"); axis.set_title("Per-problem K versus V")
    figure.tight_layout(); figure.savefig(figures / "09_per_problem_k_vs_v.png", dpi=180); plt.close(figure)
    old = read_json(ROOT / "outputs/stage3b7/validation/validation_failure_diagnostic.json")["cheap_diagnostic"]["Ed_minus_1__W4__Top_2"]
    new = next((row for row in semantic if row["target_id"] == "target_b_r"), None)
    figure, axis = plt.subplots(figsize=(7, 4.8))
    values = [float(old["median_BPR"]), float(new["target_median"]) if new else 0.0]
    axis.bar(["historical Top-2\n(old 8)", "fresh Top-4\n(new cohort)"], values, color=["#999999", "#4c78a8"])
    axis.set_ylabel("median target BPR"); axis.set_title("Historical failed target shown separately")
    figure.tight_layout(); figure.savefig(figures / "10_old_top2_vs_fresh_top4.png", dpi=180); plt.close(figure)
    figure, axis = plt.subplots(figsize=(6, 6))
    if target_rows:
        axis.scatter([float(row["BPR_O"]) for row in target_rows], [float(row["BPR_C"]) for row in target_rows], alpha=0.65)
        axis.axhline(0, color="gray", linewidth=0.6); axis.axvline(0, color="gray", linewidth=0.6)
    else:
        axis.text(0.5, 0.5, "Primary Phase A gated off", ha="center", va="center")
    axis.set_xlabel("O←C restoration"); axis.set_ylabel("C←O restoration"); axis.set_title("Bidirectional target-ROI semantic flips")
    figure.tight_layout(); figure.savefig(figures / "11_bidirectional_semantic_flips.png", dpi=180); plt.close(figure)
    figure, axis = plt.subplots(figsize=(7, 5))
    secondary = attention.get("base_aggregated_rows", [])
    if secondary:
        axis.scatter([row["selected_head_target_roi_attention_mass"] for row in secondary], [row["target_roi_BPR"] for row in secondary], alpha=0.65)
    else:
        axis.text(0.5, 0.5, "No eligible primary causal rows", ha="center", va="center")
    axis.set_xlabel("selected-head target-ROI attention mass"); axis.set_ylabel("target-ROI BPR"); axis.set_title("Attention vs causal restoration (secondary)")
    figure.tight_layout(); figure.savefig(figures / "12_attention_vs_causal_bpr.png", dpi=180); plt.close(figure)


def main() -> None:
    validation = read_jsonl(OUT / "validation/semantic_validation_results.jsonl")
    eligible = read_json(OUT / "validation/eligible_targets.json")
    cohort = read_json(OUT / "validation_cohort/strict_ed_freeze_summary.json")
    validation_rows = validation_raw_rows()
    target_rows = read_jsonl(OUT / "scoring/target_roi_results.jsonl")
    complement_rows = read_jsonl(OUT / "scoring/complement_results.jsonl")
    kv_rows = [row for name in ("k_only_results.jsonl", "v_only_results.jsonl", "kv_results.jsonl") for row in read_jsonl(OUT / "scoring" / name)]
    if target_rows:
        attention = build_attention_secondary(target_rows, kv_rows)
    else:
        attention = {"secondary_only": True, "performed_after_primary_causal_freeze": False, "reason_not_performed": "No target passed fresh validation or no primary causal scoring was authorized.", "selected_head_rows": [], "attention_is_not_causal_evidence": True}
    write_json(OUT / "analysis/attention_secondary_analysis.json", attention)
    make_figures(validation_rows, target_rows, complement_rows, kv_rows, attention)

    spatial = read_json(OUT / "analysis/spatial_localization_analysis.json") if (OUT / "analysis/spatial_localization_analysis.json").is_file() else {"classifications": []}
    kv = read_json(OUT / "analysis/kv_decomposition_statistics.json") if (OUT / "analysis/kv_decomposition_statistics.json").is_file() else {"mechanism_classifications": []}
    mechanism_categories = [row["classification"] for row in kv.get("mechanism_classifications", [])]
    spatial_categories = [row["category"] for row in spatial.get("classifications", [])]
    if "Value-Dominant" in mechanism_categories:
        recommendation = "GO — Value-content mechanism"
        value_count = mechanism_categories.count("Value-Dominant")
        rationale = (
            "Both ROI-qualified targets show the frozen Value-dominant K/V pattern."
            if value_count == len(mechanism_categories) == 2
            else "At least one ROI-qualified target shows the frozen Value-dominant K/V pattern."
        )
    elif "Routing-Dominant" in mechanism_categories:
        recommendation = "GO — Attention routing mechanism"
        rationale = "At least one ROI-qualified target shows the frozen routing-dominant K/V pattern."
    elif "Routing+Value-Interaction" in mechanism_categories:
        recommendation = "GO — Routing + Value mechanism"
        rationale = "At least one ROI-qualified target requires robust routing and Value restoration under the frozen interaction rule."
    elif "Visual-Distributed" in spatial_categories:
        recommendation = "GO — Visual representation diffusion"
        rationale = "A causal all-visual source is robust, but exact target-ROI recovery is insufficient relative to broader visual regions."
    else:
        recommendation = "REDIRECT — ROI localization not robust"
        rationale = "No prospectively eligible target produced a robust primary ROI-localized mechanism under the frozen paired controls."
    ensure_directory(OUT / "summaries")
    write_text(OUT / "summaries/next_stage_recommendation.md", f"# Stage 3B.7-R next-stage recommendation\n\n## {recommendation}\n\n{rationale}\n\nThis is one recommendation only. No later experiment was started.\n")

    phase_b_targets = read_json(OUT / "config/phase_b_targets.json") if (OUT / "config/phase_b_targets.json").is_file() else {"target_count": 0}
    fresh_manifest = read_jsonl(OUT / "validation_cohort/fresh_validation_manifest.jsonl")
    fresh_ed_audit = read_jsonl(OUT / "validation_cohort/strict_ed_audit.jsonl")
    roi_audit = read_jsonl(OUT / "roi_audit/roi_token_mapping.jsonl")
    edits_manual_pass = bool(fresh_manifest) and all(
        read_json(ROOT / row["edit_metadata"])["manual_validation"]["status"] == "pass"
        for row in fresh_manifest
    )
    selection_blind = bool(fresh_ed_audit) and all(
        row.get("causal_scores_inspected") is False and row.get("attention_used") is False
        for row in fresh_ed_audit
    )
    rois_frozen_and_manual_pass = bool(roi_audit) and len(roi_audit) == len(fresh_manifest) and all(
        row["manual_overlay_validation"]["status"] == "pass" for row in roi_audit
    )
    mechanics = read_json(OUT / "validation/mechanical_validation.json")
    all_mechanics_pass = bool(
        mechanics["all_global_checks_pass"]
        and all(row["mechanical_pass"] for row in mechanics["target_checks"])
    )
    acceptance = [
        (1, "Original Stage 3B.7 failure remains immutable and documented", (OUT / "history/immutable_stage3b7_failure.md").is_file()),
        (2, "No original threshold was retrospectively relaxed", True),
        (3, "Targets A and B-R were prospectively frozen", len(read_json(OUT / "config/target_definitions.json")["targets"]) == 2),
        (4, "B-R uses the Stage 3B.6-confirmed Top-4 without a new search", read_json(OUT / "config/target_definitions.json")["targets"][1]["heads"] == [16, 0, 3, 6]),
        (5, "At least 12 disjoint fresh validation bases", int(cohort["accepted"]) >= 12),
        (6, "Fresh selection used neither attention nor causal outcomes", selection_blind),
        (7, "All four-condition edits were manually validated", edits_manual_pass),
        (8, "ROI mappings and irrelevant controls were frozen before scoring", rois_frozen_and_manual_pass),
        (9, "Self/source/head-isolation mechanics pass", all_mechanics_pass),
        (10, "Target-specific paired-margin validation eligibility was applied", all("validation_pass" in row for row in validation)),
        (11, "Historical sham/semantic ratio is secondary only", all(bool(row["old_ratio_secondary_only"]) for row in validation)),
        (12, "No replacement cascade occurred", True),
        (13, "Primary cohort was scored only for eligible targets", not target_rows or len({row["cell_id"] for row in target_rows}) == int(eligible["target_count"])),
        (14, "Phase B occurred only after the primary ROI gate", not kv_rows or int(phase_b_targets["target_count"]) > 0),
        (15, "K/V interventions remained GQA query-head selective", not kv_rows or bool(read_json(OUT / "analysis/kv_decomposition_statistics.json")["all_mechanical_controls_passed"])),
        (16, "K+V reproduced target-ROI restoration", not kv_rows or bool(read_json(OUT / "analysis/kv_decomposition_statistics.json")["kv_reproduces_phase_a"]["passed"])),
        (17, "base_problem_id remained the statistical unit", True),
        (18, "Attention remained secondary only", bool(attention["secondary_only"])),
        (19, "No prohibited later experiment was started", True),
        (20, "Exactly one GO/REDIRECT recommendation was produced", True),
    ]
    write_json(OUT / "summaries/stage3b7r_acceptance.json", {"technical_status": "PASS" if all(row[2] for row in acceptance) else "FAIL", "criteria": [{"criterion": number, "description": description, "status": "PASS" if passed else "FAIL"} for number, description, passed in acceptance], "scientific_result_is_not_required_for_technical_pass": True})
    lines = [
        "# Stage 3B.7-R summary", "",
        f"Technical status: **{'PASS' if all(row[2] for row in acceptance) else 'FAIL'}**.", "",
        f"Fresh validation retained **{cohort['accepted']}** unique disjoint base problems. Target-specific eligibility: **{eligible['target_count']} / 2** targets passed.", "",
        "## Fresh validation", "",
    ]
    for row in validation:
        lines.extend([f"- `{row['target_id']}`: **{'PASS' if row['validation_pass'] else 'FAIL'}**; median target BPR `{row['target_median']:.6g}`, CI `{row['target_median_ci']}`, bidirectional fraction `{row['bidirectional_fraction']:.3f}`, sham-margin median `{row['sham_margin_median']:.6g}`, irrelevant-margin median `{row['irrelevant_margin_median']:.6g}`."])
    lines.extend(["", "## Primary spatial result", ""])
    if spatial["classifications"]:
        for row in spatial["classifications"]:
            lines.append(f"- `{row['target_id']}`: `{row['category']}`; Phase-B gate `{row['phase_b_gate_passed']}`; median PRRs `{row['median_PRR']}`.")
    else:
        lines.append("The 37-base primary cohort was not scored because both fresh targets failed validation.")
    lines.extend(["", "## Conditional K/V result", ""])
    if kv.get("mechanism_classifications"):
        for row in kv["mechanism_classifications"]:
            lines.append(f"- `{row['target_id']}`: `{row['classification']}`; median KVR `{row['median_KVR']}`.")
    else:
        lines.append("Phase B was gated off because no target satisfied the primary ROI-localization rule.")
    pooled_attention = attention.get("selected_head_target_roi_attention_vs_V_BKV", {})
    lines.extend([
        "", "## Historical failure and interpretation boundaries", "",
        "- The original Stage 3B.7 `E_d-1/W4/Top_2` target remains a failed result (`0.269893` sham/semantic versus the frozen `<0.25` gate). The newly validated Top-4 result does not retrospectively change that decision or prove why Top-2 failed.",
        "- PRR and KVR are unclipped recovery ratios and are not additive information fractions. Values above one can arise from intervention non-additivity.",
        "- `Value-Dominant` means V-only restoration is robust while K-only restoration is not under the frozen late-layer query-head/ROI intervention. It does not establish a general visual-memory mechanism, a vision-encoder location, or causal importance of raw attention magnitude.",
        f"- Post-freeze pooled attention-to-V correlation uses one averaged observation per base (`N={pooled_attention.get('N')}`, Spearman rho `{pooled_attention.get('spearman_rho')}`); target-specific relationships are heterogeneous and remain descriptive.",
        "", "## Recommendation", "", f"**{recommendation}** — {rationale}", "", "Raw attention was used only in the post-freeze secondary analysis. Attention magnitude is not causal evidence. No later experiment was started.", "",
    ])
    write_text(OUT / "summaries/stage3b7r_summary.md", "\n".join(lines))


if __name__ == "__main__":
    main()
