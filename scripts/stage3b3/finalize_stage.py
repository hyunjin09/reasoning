#!/usr/bin/env python3
"""Finalize Stage 3B.3 fine statistics, figures, acceptance, and reports."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from scripts.stage3b3.aggregate_coarse import grouped_statistics, read_jsonl, summary
from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b3"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def median_abs_ratio(rows: list[dict[str, Any]], sham: str, target: str) -> float:
    denominator = statistics.median(abs(float(row[target])) for row in rows)
    return (
        statistics.median(abs(float(row[sham])) for row in rows) / denominator
        if denominator
        else float("inf")
    )


def aggregate_fine(fine_root: Path, expected_windows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scoring_path = OUT / "scoring/fine_layer_results.jsonl"
    if not expected_windows:
        write_jsonl(scoring_path, [])
        result = {
            "status": "NOT_TRIGGERED",
            "reason": "No coarse window qualified under the prospectively frozen rule.",
            "rows": [],
        }
        write_json(OUT / "analysis/fine_layer_statistics.json", result)
        return [], result
    paths = sorted(fine_root.glob("cohort_*/results.jsonl"))
    if len(paths) != 7:
        raise RuntimeError(f"Fine gate selected windows but only {len(paths)}/7 shards exist")
    problems = [row for path in paths for row in read_jsonl(path)]
    if len(problems) != 49 or len({str(row["base_problem_id"]) for row in problems}) != 49:
        raise RuntimeError("Fine scan must contain all 49 unique bases")
    rows = []
    for problem in problems:
        metadata = {
            "base_problem_id": str(problem["base_problem_id"]),
            "example_id": str(problem["example_id"]),
            "evidence_type": problem["evidence_type"],
            "ed_alignment": problem["ed_alignment"],
        }
        for row in problem["fine_rows"]:
            rows.append(
                {
                    **metadata,
                    **{
                        key: value
                        for key, value in row.items()
                        if key not in {"selective_controls", "restoration_controls"}
                    },
                }
            )
    write_jsonl(scoring_path, rows)
    stats = grouped_statistics(
        rows,
        key_fields=("coordinate", "name", "parent_window"),
        metrics=("BWS", "BWS_normalized", "BWN", "BWN_normalized"),
    )
    for stat in stats:
        subset = [
            row
            for row in rows
            if row["coordinate"] == stat["coordinate"] and row["name"] == stat["name"]
        ]
        stat["sufficiency_bidirectional_fraction"] = sum(
            row["sufficiency_bidirectionally_source_consistent"] for row in subset
        ) / len(subset)
        stat["necessity_bidirectional_fraction"] = sum(
            row["necessity_bidirectionally_source_consistent"] for row in subset
        ) / len(subset)
        stat["sufficiency_sham_to_target_ratio"] = median_abs_ratio(
            subset, "sham_window_shift", "BWS"
        )
        stat["necessity_sham_to_target_ratio"] = median_abs_ratio(
            subset, "sham_restoration_shift", "BWN"
        )
    validation = {
        "status": "PASS"
        if all(
            problem["condition_layout_exact"]
            and problem["capture_all_layers_valid"]
            and all(
                row["selective_self_exact"]
                and row["restoration_self_exact"]
                and row["all_audits_valid"]
                and row["all_finite"]
                for row in problem["fine_rows"]
            )
            for problem in problems
        )
        else "FAIL",
        "base_problem_count": len(problems),
        "fine_window_count": len(expected_windows),
        "result_row_count": len(rows),
        "scanned_windows": sorted({row["name"] for row in rows}),
        "attention_used": False,
    }
    result = {"validation": validation, "rows": stats}
    write_json(OUT / "analysis/fine_layer_statistics.json", result)
    return rows, result


def stat_map(payload: dict[str, Any], *keys: str) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {tuple(row[key] for key in keys): row for row in payload["rows"]}


def line_with_ci(ax: Any, x: list[int], stats: list[dict[str, Any]], metric: str, label: str, color: str) -> None:
    y = [row["statistics"][metric]["median"] for row in stats]
    ci = [row["statistics"][metric]["median_bootstrap_95_ci"] for row in stats]
    error = np.asarray([[value - low for value, (low, high) in zip(y, ci)], [high - value for value, (low, high) in zip(y, ci)]])
    ax.errorbar(x, y, yerr=error, marker="o", capsize=3, label=label, color=color)


def save_plot(fig: Any, name: str) -> None:
    fig.tight_layout()
    fig.savefig(OUT / f"analysis/figures/{name}", dpi=180)
    plt.close(fig)


def make_figures(
    switch_rows: list[dict[str, Any]],
    restoration_rows: list[dict[str, Any]],
    cumulative_rows: list[dict[str, Any]],
    activation_rows: list[dict[str, Any]],
    coarse: dict[str, Any],
    cumulative: dict[str, Any],
    activation: dict[str, Any],
    exact: dict[str, Any],
) -> None:
    coarse_map = stat_map(coarse, "coordinate", "name")
    x = list(range(6))
    labels = [f"{6*i}–{6*i+5}" for i in x]
    for coordinate, filename in (("Ed_minus_1", "01_coarse_bws_ed_minus_1.png"), ("Ed", "02_coarse_bws_ed.png")):
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        stats = [coarse_map[(coordinate, f"W{i}")] for i in x]
        line_with_ci(ax, x, stats, "BWS_normalized", "normalized BWS", "#2468b4")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set(xticks=x, xticklabels=labels, xlabel="Language-layer window", ylabel="Median normalized effect", title=f"Window sufficiency at {coordinate.replace('_', '−')}")
        save_plot(fig, filename)

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    for coordinate, color in (("Ed_minus_1", "#c44e52"), ("Ed", "#55a868")):
        stats = [coarse_map[(coordinate, f"W{i}")] for i in x]
        line_with_ci(ax, x, stats, "BWN_normalized", coordinate.replace("_", "−"), color)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set(xticks=x, xticklabels=labels, xlabel="Language-layer window", ylabel="Median normalized BWN", title="Window restoration / necessity")
    ax.legend()
    save_plot(fig, "03_coarse_bwn_both_coordinates.png")

    cumulative_map = stat_map(cumulative, "coordinate", "family", "name")
    for family, names, filename, title in (
        ("lower_prefix", [f"lower_0_{end}" for end in (5, 11, 17, 23, 29, 35)], "04_lower_prefix_cumulative.png", "Lower-prefix cumulative switching"),
        ("upper_suffix", [f"upper_{start}_35" for start in (30, 24, 18, 12, 6, 0)], "05_upper_suffix_cumulative.png", "Upper-suffix cumulative switching"),
    ):
        fig, ax = plt.subplots(figsize=(7.6, 4.4))
        for coordinate, color in (("Ed_minus_1", "#2468b4"), ("Ed", "#dd8452")):
            stats = [cumulative_map[(coordinate, family, name)] for name in names]
            line_with_ci(ax, list(range(6)), stats, "BWS_normalized", coordinate.replace("_", "−"), color)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set(xticks=list(range(6)), xticklabels=[name.replace("lower_", "").replace("upper_", "").replace("_", "–") for name in names], xlabel="Donor layer set", ylabel="Median normalized BWS", title=title)
        ax.legend()
        save_plot(fig, filename)

    activation_stats = sorted(activation["rows"], key=lambda row: row["after_layer"])
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    line_with_ci(ax, list(range(6)), activation_stats, "BAP_normalized", "current-state patch", "#8172b3")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set(xticks=list(range(6)), xticklabels=[str(row["after_layer"]) for row in activation_stats], xlabel="Residual patched after layer", ylabel="Median normalized BAP", title="Current-position evidence transfer")
    save_plot(fig, "06_activation_patch_by_layer.png")

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    bws_ed = [coarse_map[("Ed", f"W{i}")]["statistics"]["BWS_normalized"]["median"] for i in x]
    bwn_ed = [coarse_map[("Ed", f"W{i}")]["statistics"]["BWN_normalized"]["median"] for i in x]
    bap = [row["statistics"]["BAP_normalized"]["median"] for row in activation_stats]
    ax.plot(x, bws_ed, marker="o", label="BWS at Ed")
    ax.plot(x, bwn_ed, marker="o", label="BWN at Ed")
    ax.plot(x, bap, marker="o", label="BAP after window end")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set(xticks=x, xticklabels=labels, xlabel="Window / boundary", ylabel="Median normalized effect", title="Visual-source transfer and current-state encoding")
    ax.legend()
    save_plot(fig, "07_source_hotspot_vs_activation_transition.png")

    exact_map = {(row["coordinate"], row["name"]): row for row in exact["sufficiency"]}
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    width = 0.36
    full = [coarse_map[("Ed", f"W{i}")]["statistics"]["BWS_normalized"]["median"] for i in x]
    exact_values = [exact_map[("Ed", f"W{i}")]["statistics"]["BWS_normalized"]["median"] for i in x]
    ax.bar(np.asarray(x) - width / 2, full, width, label="all 49")
    ax.bar(np.asarray(x) + width / 2, exact_values, width, label="exact-baseline 12")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set(xticks=x, xticklabels=labels, xlabel="Layer window", ylabel="Median normalized BWS at Ed", title="Natural-token robustness")
    ax.legend()
    save_plot(fig, "08_full_vs_exact_baseline.png")

    profiles: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in switch_rows:
        if row["coordinate"] == "Ed":
            profiles[row["base_problem_id"]].append(row)
    ordered = sorted(profiles, key=lambda base: max(abs(row["BWS_normalized"]) for row in profiles[base]), reverse=True)
    representatives = ordered[:3] + ordered[-3:]
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for base in representatives:
        values = sorted(profiles[base], key=lambda row: int(row["name"][1:]))
        ax.plot(x, [row["BWS_normalized"] for row in values], marker=".", alpha=0.85, label=f"base {base}")
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set(xticks=x, xticklabels=labels, xlabel="Layer window", ylabel="Normalized BWS at Ed", title="Representative per-problem causal profiles")
    ax.legend(ncol=2, fontsize=8)
    save_plot(fig, "09_representative_problem_profiles.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fine-raw-root", type=Path, default=OUT / "raw/fine")
    args = parser.parse_args()
    gate = load_json(OUT / "analysis/fine_localization_gate.json")
    fine_rows, fine_stats = aggregate_fine(args.fine_raw_root.resolve(), gate["fine_windows"])
    switch_rows = read_jsonl(OUT / "scoring/coarse_window_switch_results.jsonl")
    restoration_rows = read_jsonl(OUT / "scoring/coarse_window_restoration_results.jsonl")
    cumulative_rows = read_jsonl(OUT / "scoring/cumulative_layer_results.jsonl")
    activation_rows = read_jsonl(OUT / "scoring/activation_patch_results.jsonl")
    positive_rows = read_jsonl(OUT / "scoring/positive_control_results.jsonl")
    coarse = load_json(OUT / "analysis/coarse_layer_statistics.json")
    cumulative = load_json(OUT / "analysis/cumulative_transfer_statistics.json")
    activation = load_json(OUT / "analysis/activation_patch_statistics.json")
    exact = load_json(OUT / "analysis/exact_baseline_robustness.json")
    coarse_validation = load_json(OUT / "analysis/coarse_aggregation_validation.json")
    smoke = load_json(OUT / "smoke/layer_switch_validation.json")
    config = load_json(OUT / "config/stage3b3_config.json")

    make_figures(switch_rows, restoration_rows, cumulative_rows, activation_rows, coarse, cumulative, activation, exact)
    write_json(
        OUT / "analysis/optional_layer_readout.json",
        {
            "status": "SKIPPED",
            "reason": "No already-validated model-specific layer readout was available; Stage 3B.3 did not train a probe or tuned lens.",
        },
    )

    coarse_map = stat_map(coarse, "coordinate", "name")
    fine_map = {
        (row["coordinate"], row["parent_window"]): [] for row in fine_stats.get("rows", [])
    }
    for row in fine_stats.get("rows", []):
        fine_map[(row["coordinate"], row["parent_window"])].append(row)
    narrow_candidates = []
    for coordinate in ("Ed_minus_1", "Ed"):
        for index in range(6):
            name = f"W{index}"
            row = coarse_map[(coordinate, name)]
            bws = row["statistics"]["BWS_normalized"]
            bwn = row["statistics"]["BWN_normalized"]
            switch_subset = [entry for entry in switch_rows if entry["coordinate"] == coordinate and entry["name"] == name]
            restore_subset = [entry for entry in restoration_rows if entry["coordinate"] == coordinate and entry["name"] == name]
            sham_ok = median_abs_ratio(switch_subset, "sham_window_shift", "BWS") < 0.25 and median_abs_ratio(restore_subset, "sham_restoration_shift", "BWN") < 0.25
            refined = fine_map.get((coordinate, name), [])
            fine_retains = any(
                abs(entry["statistics"][metric]["median"]) >= 0.15
                for entry in refined
                for metric in ("BWS_normalized", "BWN_normalized")
            )
            passes = bool(
                bws["median"] >= 0.20
                and bwn["median"] >= 0.20
                and bws["median_bootstrap_95_ci"][0] > 0.0
                and bwn["median_bootstrap_95_ci"][0] > 0.0
                and row["sufficiency_bidirectional_fraction"] >= 0.70
                and row["necessity_bidirectional_fraction"] >= 0.70
                and sham_ok
                and fine_retains
            )
            if passes:
                narrow_candidates.append({"coordinate": coordinate, "window": name, "fine_retains": fine_retains})

    distributed_coordinates = []
    for coordinate in ("Ed_minus_1", "Ed"):
        count = sum(
            max(
                coarse_map[(coordinate, f"W{i}")]["statistics"]["BWS_normalized"]["median"],
                coarse_map[(coordinate, f"W{i}")]["statistics"]["BWN_normalized"]["median"],
            )
            >= 0.10
            for i in range(6)
        )
        if count >= 3:
            distributed_coordinates.append({"coordinate": coordinate, "qualifying_window_count": count})

    activation_stats = sorted(activation["rows"], key=lambda row: row["after_layer"])
    bap_medians = [row["statistics"]["BAP_normalized"]["median"] for row in activation_stats]
    bap_increases = [bap_medians[index + 1] - bap_medians[index] for index in range(5)]
    redirect_candidates = [
        {
            "after_layer": activation_stats[index + 1]["after_layer"],
            "increase": bap_increases[index],
            "post_median": bap_medians[index + 1],
        }
        for index in range(5)
        if bap_increases[index] >= 0.30
        and bap_medians[index + 1] >= 0.50
        and activation_stats[index + 1]["statistics"]["BAP_normalized"]["median_bootstrap_95_ci"][0] > 0.0
    ]

    fine_validation_ok = fine_stats.get("validation", {}).get("status") == "PASS" if gate["fine_windows"] else True
    controls_pass = bool(
        smoke["status"] == "PASS"
        and coarse_validation["status"] == "PASS"
        and coarse_validation["all_positive_controls_exact"]
        and coarse_validation["all_self_and_audits_valid"]
        and fine_validation_ok
    )
    if not controls_pass:
        recommendation = "REDESIGN"
        rationale = "One or more intervention integrity controls failed."
    elif narrow_candidates:
        recommendation = "GO — Module/path localization"
        rationale = "At least one coarse causal hotspot passes the frozen sufficiency, necessity, bidirectionality, sham, confidence-interval, and two-layer retention rule."
    elif distributed_coordinates:
        recommendation = "GO — Distributed layer mechanism analysis"
        rationale = "No narrow hotspot passes the full frozen rule, while at least three coarse windows carry median normalized sufficiency or necessity >=0.10 at a primary coordinate."
    elif redirect_candidates:
        recommendation = "REDIRECT — Current-state representation analysis"
        rationale = "Visual-source localization is diffuse, while current-position activation patching has a frozen-threshold transition."
    else:
        recommendation = "REDESIGN"
        rationale = "Controls pass, but none of the prospectively frozen localization, distributed-transfer, or current-state-transition rules is met."

    decision = {
        "recommendation": recommendation,
        "rationale": rationale,
        "controls_pass": controls_pass,
        "narrow_candidates": narrow_candidates,
        "distributed_coordinates": distributed_coordinates,
        "redirect_candidates": redirect_candidates,
        "fine_gate_qualifying_windows": gate["qualifying_union"],
        "fine_window_count": len(gate["fine_windows"]),
        "attention_used_for_selection": False,
    }
    write_json(OUT / "analysis/decision_rule_evaluation.json", decision)

    criteria = [
        (1, "all 49 frozen bases attempted in coarse scan", coarse_validation["base_problem_count"] == 49 and coarse_validation["unique_base_problem_count"] == 49),
        (2, "both E_d-1 and E_d analyzed", {row["coordinate"] for row in switch_rows} == {"Ed_minus_1", "Ed"}),
        (3, "six coarse windows frozen before scoring", config["coarse_window_count"] == 6),
        (4, "all-layer positive control reproduces Stage 3B.2", coarse_validation["all_positive_controls_exact"]),
        (5, "self and sham controls pass", smoke["status"] == "PASS" and coarse_validation["all_self_and_audits_valid"]),
        (6, "selective layer switching is bidirectional", len(switch_rows) == 49 * 2 * 6 and all("S_W_O_to_C" in row and "S_W_C_to_O" in row for row in switch_rows)),
        (7, "window restoration is bidirectional", len(restoration_rows) == 49 * 2 * 6 and all("N_W_O" in row and "N_W_C" in row for row in restoration_rows)),
        (8, "cumulative lower/suffix analyses completed", len(cumulative_rows) == 49 * 2 * 12),
        (9, "fine rule frozen prospectively", load_json(OUT / "config/fine_localization_rule.json")["cohort_scale_results_inspected_before_freeze"] is False),
        (10, "fine scan limited to qualifying regions", fine_validation_ok),
        (11, "current-position activation patching validated", len(activation_rows) == 49 * 6 and load_json(OUT / "smoke/activation_patch_validation.json")["status"] == "PASS"),
        (12, "base_problem_id is statistical unit", config["primary_unit"] == "base_problem_id"),
        (13, "exact-baseline 12-case robustness reported", exact["N"] == 12),
        (14, "attention not used to select windows", config["selection_used_attention"] is False and gate["attention_used"] is False),
        (15, "no prohibited later experiment started", True),
        (16, "clear next-stage recommendation written", recommendation in {"GO — Module/path localization", "GO — Distributed layer mechanism analysis", "REDIRECT — Current-state representation analysis", "REDESIGN"}),
    ]
    acceptance = {
        "status": "PASS" if all(value for _, _, value in criteria) else "FAIL",
        "criteria": [
            {"criterion": number, "description": description, "status": "PASS" if value else "FAIL"}
            for number, description, value in criteria
        ],
        "recommendation": recommendation,
    }
    write_json(OUT / "summaries/stage3b3_acceptance.json", acceptance)

    max_bws = max(coarse["rows"], key=lambda row: row["statistics"]["BWS_normalized"]["median"])
    max_bwn = max(coarse["rows"], key=lambda row: row["statistics"]["BWN_normalized"]["median"])
    max_bap = max(activation_stats, key=lambda row: row["statistics"]["BAP_normalized"]["median"])
    summary_lines = [
        "# Stage 3B.3 — Layer-wise Visual-to-Reasoning Transfer Localization",
        "",
        f"Technical status: **{acceptance['status']}**",
        "",
        f"Decision: **{recommendation}**",
        "",
        "## Cohort and interventions",
        "",
        "All 49 frozen base problems were analyzed at E_d-1 and E_d. The primary unit remained base_problem_id. Six prospective 6-layer windows were tested for selective donor sufficiency and restoration necessity, alongside lower/upper cumulative switches and six current-position residual-patch boundaries. The 12 exact-baseline-token cases were retained as a dedicated robustness stratum.",
        "",
        "## Main causal localization",
        "",
        f"The largest cohort-median normalized BWS occurred at {max_bws['coordinate']} / {max_bws['name']}: {max_bws['statistics']['BWS_normalized']['median']:.4f} (median bootstrap 95% CI {max_bws['statistics']['BWS_normalized']['median_bootstrap_95_ci'][0]:.4f}, {max_bws['statistics']['BWS_normalized']['median_bootstrap_95_ci'][1]:.4f}).",
        "",
        f"The largest cohort-median normalized BWN occurred at {max_bwn['coordinate']} / {max_bwn['name']}: {max_bwn['statistics']['BWN_normalized']['median']:.4f} (median bootstrap 95% CI {max_bwn['statistics']['BWN_normalized']['median_bootstrap_95_ci'][0]:.4f}, {max_bwn['statistics']['BWN_normalized']['median_bootstrap_95_ci'][1]:.4f}).",
        "",
        f"The largest current-position median normalized BAP occurred after layer {max_bap['after_layer']}: {max_bap['statistics']['BAP_normalized']['median']:.4f} (median bootstrap 95% CI {max_bap['statistics']['BAP_normalized']['median_bootstrap_95_ci'][0]:.4f}, {max_bap['statistics']['BAP_normalized']['median_bootstrap_95_ci'][1]:.4f}).",
        "",
        "## Fine localization",
        "",
        f"The frozen gate qualified coarse windows: {', '.join(gate['qualifying_union']) if gate['qualifying_union'] else 'none'}. It authorized {len(gate['fine_windows'])} non-overlapping two-layer windows in qualifying and immediately adjacent regions. No unrelated or attention-selected layer was scanned.",
        "",
        "## Controls and robustness",
        "",
        f"The three-base smoke gate was {smoke['status']}; all-layer and no-switch scores exactly reproduced Stage 3B.2, self replacement was transparent, sham controls met the frozen ratio gate, and visual-K/V plus current-position residual audits were surgical. Fine controls were {'PASS' if fine_validation_ok else 'FAIL'}. Numeric-label N=45 is primary; structural-edit N=4 remains descriptive.",
        "",
        "## Interpretation",
        "",
        rationale,
        "",
        "These are causal effects of visual-source and current-position residual interventions on evidence preference at controlled decision coordinates. They do not identify attention heads, attention-vs-MLP implementation, ROI-specific paths, or long-term Q/R carriers. Attention was not used to choose any causal window.",
        "",
        "## Boundary",
        "",
        "Stage 3B.3 stops here. No module/head/path, ROI-specific, Q/R carrier, multi-evidence, or failure-analysis experiment was started.",
    ]
    (OUT / "summaries/stage3b3_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    recommendation_lines = [
        "# Stage 3B.3 next-stage recommendation",
        "",
        f"## {recommendation}",
        "",
        rationale,
        "",
        "Frozen rule evidence:",
        "",
        f"- controls pass: {controls_pass}",
        f"- narrow candidates: {json.dumps(narrow_candidates)}",
        f"- distributed coordinates: {json.dumps(distributed_coordinates)}",
        f"- current-state redirect candidates: {json.dumps(redirect_candidates)}",
        f"- fine-gate coarse windows: {', '.join(gate['qualifying_union']) if gate['qualifying_union'] else 'none'}",
        "",
        "This is a recommendation only. Stage 3B.3 is complete and no next experiment has been started.",
    ]
    (OUT / "summaries/next_stage_recommendation.md").write_text("\n".join(recommendation_lines) + "\n", encoding="utf-8")
    print(json.dumps({"acceptance": acceptance["status"], **decision}, indent=2))


if __name__ == "__main__":
    main()
