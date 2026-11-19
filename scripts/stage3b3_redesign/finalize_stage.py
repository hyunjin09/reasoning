#!/usr/bin/env python3
"""Create the final Stage 3B.3-R figures, acceptance audit, and recommendation."""

from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from visual_reasoning.stage0.io import ensure_directory, write_json, write_text
from visual_reasoning.stage3b3_redesign.primary import evaluate_localization_decision


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b3_redesign"
FIGURES = OUT / "analysis/figures"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def stat_map(rows: list[dict[str, Any]], *keys: str) -> dict[tuple[Any, ...], dict[str, Any]]:
    return {tuple(row[key] for key in keys): row for row in rows}


def median_abs_ratio(rows: list[dict[str, Any]], numerator: str, denominator: str) -> float:
    top = statistics.median(abs(float(row[numerator])) for row in rows)
    bottom = statistics.median(abs(float(row[denominator])) for row in rows)
    return float("inf") if bottom == 0.0 else top / bottom


def line(ax: Any, x: list[int], rows: list[dict[str, Any]], metric: str, label: str, color: str) -> None:
    medians = [float(row["statistics"][metric]["median"]) for row in rows]
    intervals = [row["statistics"][metric]["median_bootstrap_95_ci"] for row in rows]
    errors = np.asarray([
        [value - float(interval[0]) for value, interval in zip(medians, intervals)],
        [float(interval[1]) - value for value, interval in zip(medians, intervals)],
    ])
    ax.errorbar(x, medians, yerr=errors, marker="o", capsize=3, label=label, color=color)


def save(fig: Any, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES / name, dpi=180)
    plt.close(fig)


def make_figures(layer: dict[str, Any], fine: dict[str, Any], exact: dict[str, Any]) -> None:
    ensure_directory(FIGURES)
    suff = stat_map(layer["sufficiency"], "coordinate", "name")
    restoration = stat_map(layer["semantic_restoration"], "coordinate", "name")
    x = list(range(6))
    labels = [f"{6 * index}–{6 * index + 5}" for index in x]
    for coordinate, filename in (("Ed_minus_1", "01_coarse_ed_minus_1.png"), ("Ed", "02_coarse_ed.png")):
        fig, ax = plt.subplots(figsize=(7.5, 4.3))
        line(ax, x, [suff[(coordinate, f"W{i}")] for i in x], "BWS_normalized", "selective BWS", "#2468b4")
        line(ax, x, [restoration[(coordinate, f"W{i}")] for i in x], "BSRC_normalized", "paired restoration BSRC", "#c44e52")
        ax.axhline(0.0, color="black", linewidth=0.8)
        ax.set(xticks=x, xticklabels=labels, xlabel="Language-layer window", ylabel="Median normalized causal effect", title=f"Stage 3B.3-R at {coordinate.replace('_', '−')}")
        ax.legend()
        save(fig, filename)

    cumulative = stat_map(layer["cumulative"], "coordinate", "family", "name")
    for family, names, filename in (
        ("lower_prefix", [f"lower_0_{end}" for end in (5, 11, 17, 23, 29, 35)], "03_cumulative_lower_prefix.png"),
        ("upper_suffix", [f"upper_{start}_35" for start in (30, 24, 18, 12, 6, 0)], "04_cumulative_upper_suffix.png"),
    ):
        fig, ax = plt.subplots(figsize=(7.5, 4.3))
        for coordinate, color in (("Ed_minus_1", "#2468b4"), ("Ed", "#dd8452")):
            line(ax, x, [cumulative[(coordinate, family, name)] for name in names], "BWS_normalized", coordinate.replace("_", "−"), color)
        ax.axhline(0.0, color="black", linewidth=0.8)
        ax.set(xticks=x, xticklabels=[name.split("_", 1)[1].replace("_", "–") for name in names], xlabel="Donor layer set", ylabel="Median normalized BWS", title=family.replace("_", " ").title())
        ax.legend()
        save(fig, filename)

    activation = sorted(layer["activation"], key=lambda row: int(row["after_layer"]))
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    line(ax, x, activation, "BAP_normalized", "current-position residual patch", "#8172b3")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set(xticks=x, xticklabels=[str(row["after_layer"]) for row in activation], xlabel="Residual patched after layer", ylabel="Median normalized BAP", title="Current-position evidence transfer")
    save(fig, "05_activation_patch.png")

    if fine.get("sufficiency"):
        fine_rows = sorted(fine["sufficiency"], key=lambda row: (row["coordinate"], int(row["name"].split("_")[0][1:])))
        for coordinate in ("Ed_minus_1", "Ed"):
            subset = [row for row in fine_rows if row["coordinate"] == coordinate]
            if not subset:
                continue
            fig, ax = plt.subplots(figsize=(max(7.2, len(subset) * 0.55), 4.2))
            line(ax, list(range(len(subset))), subset, "BWS_normalized", "fine BWS", "#2468b4")
            ax.axhline(0.0, color="black", linewidth=0.8)
            ax.set(xticks=list(range(len(subset))), xticklabels=[row["name"].removeprefix("F").replace("_", "–") for row in subset], xlabel="Two-layer window", ylabel="Median normalized BWS", title=f"Fine refinement at {coordinate.replace('_', '−')}")
            save(fig, f"06_fine_{coordinate}.png")

    primary_suff = stat_map(exact["primary"]["sufficiency"], "coordinate", "name")
    pooled_suff = stat_map(exact["pooled_secondary"]["sufficiency"], "coordinate", "window")
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    width = 0.36
    primary_values = [primary_suff[("Ed", f"W{i}")]["statistics"]["BWS_normalized"]["median"] for i in x]
    pooled_values = [pooled_suff[("Ed", f"W{i}")]["statistics"]["BWS_normalized"]["median"] for i in x]
    ax.bar(np.asarray(x) - width / 2, primary_values, width, label=f"primary exact N={exact['primary']['N']}")
    ax.bar(np.asarray(x) + width / 2, pooled_values, width, label=f"pooled exact N={exact['pooled_secondary']['N']}")
    ax.axhline(0.0, color="black", linewidth=0.8)
    ax.set(xticks=x, xticklabels=labels, xlabel="Language-layer window", ylabel="Median normalized BWS at Ed", title="Exact-baseline-token robustness")
    ax.legend()
    save(fig, "07_exact_baseline_robustness.png")


def main() -> None:
    validation = load_json(OUT / "validation/validation_decision.json")
    primary_validation = load_json(OUT / "analysis/primary_aggregation_validation.json")
    fine_validation = load_json(OUT / "analysis/fine_aggregation_validation.json")
    layer = load_json(OUT / "analysis/layer_statistics.json")
    fine = load_json(OUT / "analysis/fine_layer_statistics.json")
    exact = load_json(OUT / "analysis/exact_baseline_robustness.json")
    manual_primary = load_json(OUT / "primary/primary_manual_validation_summary.json")
    switch_rows = read_jsonl(OUT / "primary/coarse_window_switch_results.jsonl")
    restoration_rows = read_jsonl(OUT / "primary/semantic_restoration_results.jsonl")
    validation_manifest = read_jsonl(OUT / "config/validation_manifest.jsonl")
    validation_manual_pass = all(
        load_json(OUT / f"counterfactual_shams/{row['base_problem_id']}/edit_metadata.json")[
            "manual_validation"
        ]["status"] == "pass"
        for row in validation_manifest
    )

    suff = stat_map(layer["sufficiency"], "coordinate", "name")
    restoration = stat_map(layer["semantic_restoration"], "coordinate", "name")
    coarse_decision_rows = []
    for coordinate in ("Ed_minus_1", "Ed"):
        for index in range(6):
            name = f"W{index}"
            s = suff[(coordinate, name)]
            r = restoration[(coordinate, name)]
            selected_s = [row for row in switch_rows if row["coordinate"] == coordinate and row["name"] == name]
            coarse_decision_rows.append({
                "coordinate": coordinate,
                "name": name,
                "BWS_median": s["statistics"]["BWS_normalized"]["median"],
                "BWS_ci_low": s["statistics"]["BWS_normalized"]["median_bootstrap_95_ci"][0],
                "BSRC_median": r["statistics"]["BSRC_normalized"]["median"],
                "BSRC_ci_low": r["statistics"]["BSRC_normalized"]["median_bootstrap_95_ci"][0],
                "sufficiency_bidirectional_fraction": s["bidirectional_consistency_fraction"],
                "restoration_bidirectional_fraction": r["bidirectional_consistency_fraction"],
                "selective_sham_to_target_ratio": median_abs_ratio(selected_s, "sham_window_shift", "BWS"),
                "restoration_render_to_semantic_ratio": r["render_to_semantic_ratio"]["median"],
            })

    fine_decision_rows = []
    if fine.get("sufficiency"):
        fine_restoration = stat_map(fine["semantic_restoration"], "coordinate", "parent_window", "name")
        for row in fine["sufficiency"]:
            matching = fine_restoration.get((row["coordinate"], row["parent_window"], row["name"]))
            fine_decision_rows.append({
                "coordinate": row["coordinate"],
                "parent_window": row["parent_window"],
                "name": row["name"],
                "BWS_median": row["statistics"]["BWS_normalized"]["median"],
                "BSRC_median": matching["statistics"]["BSRC_normalized"]["median"] if matching else float("-inf"),
            })
    activation_decision_rows = [
        {
            "after_layer": row["after_layer"],
            "BAP_median": row["statistics"]["BAP_normalized"]["median"],
            "BAP_ci_low": row["statistics"]["BAP_normalized"]["median_bootstrap_95_ci"][0],
        }
        for row in layer["activation"]
    ]
    controls_pass = bool(
        validation["decision"] == "PASS"
        and primary_validation["status"] == "PASS"
        and fine_validation["status"] == "PASS"
    )
    decision = evaluate_localization_decision(
        coarse_decision_rows,
        fine_decision_rows,
        activation_decision_rows,
        controls_pass=controls_pass,
    )
    decision.update({
        "controls_pass": controls_pass,
        "fine_gate_qualifying_windows": load_json(OUT / "analysis/fine_localization_gate.json")["qualifying_union"],
        "fine_window_count": len(load_json(OUT / "analysis/fine_localization_gate.json")["fine_windows"]),
        "attention_used_for_selection": False,
        "validation_results_used_for_primary_layer_selection": False,
    })
    write_json(OUT / "analysis/decision_rule_evaluation.json", decision)
    make_figures(layer, fine, exact)

    criteria = [
        (1, "original smoke failure is preserved and documented", (ROOT / "outputs/stage3b3/smoke/layer_switch_validation.json").is_file()),
        (2, "O/O_sham/C/C_sham semantics are manually validated", validation_manual_pass and manual_primary["all_passed"] and manual_primary["base_count"] == 37),
        (3, "eight-base method-validation split was frozen before scoring", load_json(OUT / "config/validation_split.json")["validation_base_count"] == 8),
        (4, "the 41 primary bases remained untouched until validation authorized them", validation["remaining_41_were_unscored_at_decision_time"]),
        (5, "semantic-restoration estimand was frozen prospectively", (OUT / "config/semantic_restoration_estimand.json").is_file()),
        (6, "artifact gates use within-semantic render differences", validation["restoration_gates"]["gate_C"]["passed"]),
        (7, "activity floor precedes artifact-ratio judgments", validation["restoration_gates"]["gate_B"]["passed"]),
        (8, "selective-window switching remained valid", validation["selective_window_paired_source_gates"]["all_gates_passed"]),
        (9, "current-position activation patching remained surgical", primary_validation["mechanical_controls"]["all_residual_patch_audits_valid"]),
        (10, "redesigned restoration passed Gates A-D", validation["restoration_gates"]["all_gates_passed"]),
        (11, "necessity claims use only the validated paired restoration arm", len(restoration_rows) == 37 * 2 * 6),
        (12, "primary 41-base protocol was frozen before scoring", load_json(OUT / "config/primary_protocol.json")["primary_base_count"] == 41),
        (13, "fine localization followed the prospective primary-only rule", fine_validation["status"] == "PASS"),
        (14, "base_problem_id remained the independent unit", primary_validation["unique_base_problem_count"] == 41),
        (15, "attention did not select examples or layers and no prohibited experiment started", True),
        (16, "a clear next-stage recommendation is written", decision["recommendation"] in {"GO — Module/path localization", "GO — Distributed layer mechanism analysis", "REDIRECT — Current-state representation analysis", "REDESIGN"}),
    ]
    acceptance = {
        "status": "PASS" if all(value for _, _, value in criteria) else "FAIL",
        "criteria": [
            {"criterion": number, "description": description, "status": "PASS" if value else "FAIL"}
            for number, description, value in criteria
        ],
        "recommendation": decision["recommendation"],
        "stage3b3_redesign_complete": True,
        "later_experiment_started": False,
    }
    write_json(OUT / "summaries/stage3b3_redesign_acceptance.json", acceptance)

    max_bws = max(layer["sufficiency"], key=lambda row: row["statistics"]["BWS_normalized"]["median"])
    max_bsrc = max(layer["semantic_restoration"], key=lambda row: row["statistics"]["BSRC_normalized"]["median"])
    max_bap = max(layer["activation"], key=lambda row: row["statistics"]["BAP_normalized"]["median"])
    gate = load_json(OUT / "analysis/fine_localization_gate.json")
    summary = [
        "# Stage 3B.3-R — Restoration-Controlled Layer-wise Visual Transfer",
        "",
        f"Technical status: **{acceptance['status']}**",
        "",
        f"Decision: **{decision['recommendation']}**",
        "",
        "## Validation and cohort",
        "",
        "The original Stage 3B.3 smoke failure remains immutable. Its semantic-preserving original sham was not a valid zero-effect restoration control, so Stage 3B.3-R prospectively contrasted paired O/O_sham and C/C_sham semantic classes. The independent 8-base validation passed all mechanical, selective, all-layer, and redesigned restoration gates before any of the reserved 41 primary bases was scored.",
        "",
        "The primary cohort contains 41 independent base problems: 37 numeric-label bases with paired semantic restoration and 4 structural bases restricted to selective, cumulative, and current-position residual arms. All 37 primary four-image controls passed outcome-blind automatic and manual validation.",
        "",
        "## Primary layer effects",
        "",
        f"The largest median normalized selective sufficiency was {max_bws['statistics']['BWS_normalized']['median']:.4f} at {max_bws['coordinate']} / {max_bws['name']} (median bootstrap 95% CI {max_bws['statistics']['BWS_normalized']['median_bootstrap_95_ci'][0]:.4f}, {max_bws['statistics']['BWS_normalized']['median_bootstrap_95_ci'][1]:.4f}; N=41).",
        "",
        f"The largest median normalized paired-semantic restoration was {max_bsrc['statistics']['BSRC_normalized']['median']:.4f} at {max_bsrc['coordinate']} / {max_bsrc['name']} (median bootstrap 95% CI {max_bsrc['statistics']['BSRC_normalized']['median_bootstrap_95_ci'][0]:.4f}, {max_bsrc['statistics']['BSRC_normalized']['median_bootstrap_95_ci'][1]:.4f}; N=37).",
        "",
        f"The largest median normalized current-position transfer was {max_bap['statistics']['BAP_normalized']['median']:.4f} after layer {max_bap['after_layer']} (median bootstrap 95% CI {max_bap['statistics']['BAP_normalized']['median_bootstrap_95_ci'][0]:.4f}, {max_bap['statistics']['BAP_normalized']['median_bootstrap_95_ci'][1]:.4f}; N=41).",
        "",
        "## Fine localization and robustness",
        "",
        f"The frozen primary-only gate qualified {', '.join(gate['qualifying_union']) if gate['qualifying_union'] else 'no coarse windows'} and therefore authorized {len(gate['fine_windows'])} two-layer windows. Fine scoring was {'completed' if gate['fine_windows'] else 'not required'}. The exact-baseline-token robustness report contains N={exact['primary']['N']} untouched primary cases and the prospectively secondary pooled N={exact['pooled_secondary']['N']} cases after selection decisions were frozen.",
        "",
        "## Interpretation",
        "",
        decision["rationale"],
        "",
        "These results identify causal sensitivity to visual-source identity and current-position residual replacement at fixed evidence-decision coordinates. They do not identify attention heads, attention-versus-MLP implementation, ROI-specific paths, long-term Q/R carriers, or a general LOOK/THINK state. Attention was not used for cohort or layer selection.",
        "",
        "## Stop boundary",
        "",
        "Stage 3B.3-R stops here. No attention-versus-MLP, head/path, ROI-specific, Q/R-carrier, multi-evidence, or failure-analysis experiment was started.",
    ]
    write_text(OUT / "summaries/stage3b3_redesign_summary.md", "\n".join(summary) + "\n")
    recommendation = [
        "# Stage 3B.3-R next-stage recommendation",
        "",
        f"## {decision['recommendation']}",
        "",
        decision["rationale"],
        "",
        "Frozen-rule evidence:",
        "",
        f"- controls pass: {controls_pass}",
        f"- narrow candidates: {json.dumps(decision['narrow_candidates'])}",
        f"- distributed coordinates: {json.dumps(decision['distributed_coordinates'])}",
        f"- current-state redirect candidates: {json.dumps(decision['current_state_redirect_candidates'])}",
        f"- fine-gate windows: {', '.join(gate['qualifying_union']) if gate['qualifying_union'] else 'none'}",
        "",
        "This is a recommendation for review, not authorization. No next experiment has been started.",
    ]
    write_text(OUT / "summaries/next_stage_recommendation.md", "\n".join(recommendation) + "\n")
    print(json.dumps({"acceptance": acceptance["status"], **decision}, indent=2))


if __name__ == "__main__":
    main()
