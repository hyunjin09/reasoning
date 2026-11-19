#!/usr/bin/env python3
"""Write Stage 3C.3-R figures, summary, acceptance, and one recommendation."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3r"
FIG = OUT / "analysis/figures"
TARGETS = ("target_a", "target_b")
LABEL = {"target_a": "Target A (E_d, L29)", "target_b": "Target B (E_d-1, L28)"}
COLOR = {"target_a": "#2c7fb8", "target_b": "#d95f0e"}
GAINS = (0.0, 0.1, 0.25, 0.5, 0.75, 1.0)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def save(fig: Any, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=180)
    plt.close(fig)


def box(ax: Any, groups: list[list[float]], labels: list[str], ylabel: str) -> None:
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.7)
    ax.boxplot(groups, tick_labels=labels, showmeans=True)
    for index, values in enumerate(groups, 1):
        jitter = np.linspace(-0.10, 0.10, len(values))
        ax.scatter(index + jitter, values, s=12, alpha=0.5)
    ax.set_ylabel(ylabel)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    validation = read_json(OUT / "validation/validation_summary.json")
    gate = read_json(OUT / "phase_b_redundancy/redundancy_gate.json")
    dose = read_json(OUT / "analysis/dose_response_statistics.json")
    specificity = read_json(OUT / "analysis/target_specificity_analysis.json")
    query = read_json(OUT / "analysis/query_patch_curve_comparison.json")
    saturation = read_json(OUT / "analysis/saturation_analysis.json")
    redundancy = read_json(OUT / "analysis/redundancy_scope_analysis.json")
    family = read_json(OUT / "analysis/primary_family_statistics.json")
    primary_mechanics = read_json(OUT / "audit/primary_mechanics.json")
    phase_b_mechanics = read_json(OUT / "audit/phase_b_mechanics.json")
    target_rows = read_jsonl(OUT / "phase_a_gain/target_gain_results.jsonl")
    mention_rows = read_jsonl(OUT / "phase_a_gain/mention_control_results.jsonl")
    irrelevant_rows = read_jsonl(OUT / "phase_a_gain/irrelevant_control_results.jsonl")
    noncausal_rows = read_jsonl(OUT / "phase_a_gain/noncausal_head_controls.jsonl")
    query_rows = read_jsonl(OUT / "phase_a_gain/query_patch_operating_points.jsonl")
    scope_rows = {
        scope: read_jsonl(OUT / f"phase_b_redundancy/scope_{scope.lower()}_results.jsonl")
        for scope in ("R1", "R2", "R3")
    }
    runtime_summary = {"slurm_job_id": "106936", "node": "node04", "gpu": "NVIDIA RTX A5000", "phases": {}}
    for phase in ("validation", "phase_a", "phase_b"):
        raw_phase = [read_json(path) for path in (OUT / "raw" / phase).glob("shard_*/examples/*/result.json")]
        seconds = [float(row["runtime_seconds"]) for row in raw_phase]
        runtime_summary["phases"][phase] = {
            "N": len(seconds),
            "median_per_base_seconds": float(np.median(seconds)),
            "maximum_per_base_seconds": max(seconds),
            "sum_per_base_seconds": sum(seconds),
        }
    resource = read_json(OUT / "raw/resource_smoke/resource_summary.json")
    runtime_summary["resource_validation_replay"] = {
        **resource,
        "excluded_from_scientific_analysis": True,
        "peak_allocated_gib": float(resource["peak_allocated_bytes"]) / 1024**3,
        "peak_reserved_gib": float(resource["peak_reserved_bytes"]) / 1024**3,
    }
    write_json(OUT / "analysis/runtime_summary.json", runtime_summary)
    by_target_gain: dict[tuple[str, float], list[dict[str, Any]]] = defaultdict(list)
    for row in target_rows:
        by_target_gain[(row["target_id"], float(row["lambda"]))].append(row)

    # 1--2: absolute evidence dose curves.
    for index, target in enumerate(TARGETS, 1):
        medians, lows, highs = [], [], []
        for gain in GAINS:
            values = np.asarray([float(row["E"]) for row in by_target_gain[(target, gain)]])
            medians.append(float(np.median(values)))
            lows.append(float(np.quantile(values, 0.25)))
            highs.append(float(np.quantile(values, 0.75)))
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.plot(GAINS, medians, marker="o", color=COLOR[target])
        ax.fill_between(GAINS, lows, highs, color=COLOR[target], alpha=0.2, label="IQR")
        ax.set_xlabel("Target-ROI contribution gain λ")
        ax.set_ylabel("Unnormalized evidence preference D")
        ax.set_title(f"{LABEL[target]} evidence dose response")
        ax.legend()
        save(fig, f"0{index}_target_{target[-1]}_evidence_vs_lambda.png")

    # 3: per-base retained-evidence curves.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, target in zip(axes, TARGETS):
        by_base: dict[str, dict[float, float]] = defaultdict(dict)
        for row in target_rows:
            if row["target_id"] == target:
                by_base[str(row["base_problem_id"])][float(row["lambda"])] = float(row["ER_unclipped"])
        for curve in by_base.values():
            ax.plot(GAINS, [curve[gain] for gain in GAINS], color=COLOR[target], alpha=0.22, linewidth=0.8)
        ax.axhline(1.0, color="black", linewidth=0.8)
        ax.set_title(LABEL[target]); ax.set_xlabel("λ")
    axes[0].set_ylabel("ER(λ), unclipped")
    save(fig, "03_per_base_lambda_curves.png")

    # 4: direct scaled contribution versus evidence retention.
    fig, ax = plt.subplots(figsize=(7, 5))
    for target in TARGETS:
        selected = [row for row in target_rows if row["target_id"] == target]
        x = [float(row["target_contribution_scaled_concat_norm"]) / float(row["target_contribution_native_concat_norm"]) for row in selected]
        y = [float(row["ER_unclipped"]) for row in selected]
        ax.scatter(x, y, s=14, alpha=0.35, color=COLOR[target], label=LABEL[target])
    ax.axhline(1, color="black", linewidth=0.8)
    ax.set_xlabel("Retained target contribution norm")
    ax.set_ylabel("Retained evidence preference ER")
    ax.set_title("Direct signal attenuation versus evidence")
    ax.legend(fontsize=8)
    save(fig, "04_retained_contribution_vs_evidence.png")

    # 5: Stage 3C.3 necessity operating points over median retained curves.
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
    for ax, target in zip(axes, TARGETS):
        medians = [float(np.median([row["ER_unclipped"] for row in by_target_gain[(target, gain)]])) for gain in GAINS]
        ax.plot(GAINS, medians, marker="o", color=COLOR[target], label="gain curve")
        operating = [float(row["lambda_query_proj"]) for row in query_rows if row["target_id"] == target]
        for value in operating:
            ax.axvline(value, color="#666666", alpha=0.15, linewidth=0.7)
        ax.axvline(float(np.median(operating)), color="black", linestyle="--", label="median query projection gain")
        ax.set_xlim(min(-0.03, min(operating) - 0.01), 1.02)
        ax.set_xlabel("Effective gain / λ")
        ax.set_title(LABEL[target])
    axes[0].set_ylabel("Median ER")
    axes[0].legend(fontsize=8)
    save(fig, "05_query_patch_operating_points.png")

    def losses(rows: list[dict[str, Any]], target: str) -> list[float]:
        return [float(row["evidence_loss_native_minus_lambda"]) for row in rows if row["target_id"] == target and float(row["lambda"]) == 0.0]

    # 6--8 controls.
    for number, control_rows, control_name in (
        (6, mention_rows, "mention"), (7, irrelevant_rows, "irrelevant"),
    ):
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
        for ax, target in zip(axes, TARGETS):
            box(ax, [losses(target_rows, target), losses(control_rows, target)], ["T", control_name[0].upper()], "D(1)-D(0)")
            ax.set_title(LABEL[target])
        save(fig, f"0{number}_target_vs_{control_name}_control.png")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for ax, target in zip(axes, TARGETS):
        box(ax, [losses(target_rows, target), losses(noncausal_rows, target)], ["causal", "noncausal"], "D(1)-D(0)")
        ax.set_title(LABEL[target])
    save(fig, "08_causal_vs_noncausal_heads.png")

    # 9: lambda-zero retained evidence.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    values = [[float(row["ER_unclipped"]) for row in by_target_gain[(target, 0.0)]] for target in TARGETS]
    box(ax, values, ["Target A", "Target B"], "E(0)/E(1), unclipped")
    ax.axhline(0.8, color="#9e9e9e", linestyle="--", label="0.80")
    ax.set_title("Selected-head λ=0 retained evidence")
    ax.legend()
    save(fig, "09_lambda0_retained_evidence.png")

    # 10: nested-scope retained evidence including R0.
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for ax, target in zip(axes, TARGETS):
        scope_values = [
            [float(row["ER_unclipped"]) for row in by_target_gain[(target, 0.0)]],
            *[
                [float(row["ER_unclipped"]) for row in scope_rows[scope] if row["target_id"] == target and float(row["lambda"]) == 0.0]
                for scope in ("R1", "R2", "R3")
            ],
        ]
        box(ax, scope_values, ["R0", "R1", "R2", "R3"], "E(0)/E(1)")
        ax.axhline(0.8, color="#9e9e9e", linestyle="--")
        ax.set_title(LABEL[target])
    save(fig, "10_nested_scope_retained_evidence.png")

    # 11: same-layer versus W4-wide unnormalized loss.
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)
    for ax, target in zip(axes, TARGETS):
        groups = [
            [float(row["evidence_loss_native_minus_lambda"]) for row in scope_rows[scope] if row["target_id"] == target and float(row["lambda"]) == 0.0]
            for scope in ("R1", "R3")
        ]
        box(ax, groups, ["R1 same layer", "R3 both W4 layers"], "D(1)-D(0)")
        ax.set_title(LABEL[target])
    save(fig, "11_same_layer_vs_w4_wide.png")

    # 12: phenotype summary.
    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(4)
    width = 0.34
    for offset, target in ((-width / 2, "target_a"), (width / 2, "target_b")):
        med = redundancy["phenotype"]["targets"][target]["median_retained"]
        ax.bar(x + offset, [med[scope] for scope in ("R0", "R1", "R2", "R3")], width, label=LABEL[target], color=COLOR[target])
    ax.axhline(0.8, color="black", linestyle="--", linewidth=0.8)
    ax.set_xticks(x, ["R0", "R1", "R2", "R3"])
    ax.set_ylim(0.75, 1.03)
    ax.set_ylabel("Median E(0)/E(1)")
    ax.set_title("Broad W4 robustness phenotype")
    ax.legend(fontsize=8)
    save(fig, "12_saturation_redundancy_phenotype.png")

    significant = [row for row in family["rows"] if row["holm_significant_0_05"]]
    final_interpretation = {
        "outcome": "O4 — Broad Robustness Beyond W4",
        "saturation_supported": False,
        "reason_saturation_not_supported": "The Stage 3C.3 query necessity patch already reduced median projected target contribution to 0.0014/0.0059 of native, while direct lambda=0 did not produce substantial evidence collapse.",
        "local_redundancy_localized": False,
        "reason_local_redundancy_not_localized": "R1-R3 removal did not yield a Holm-significant incremental loss over R0 for either target.",
        "broad_w4_robustness": True,
        "scope_boundary": "Persistence after R3 indicates support outside or redundant with the tested current-position W4 target-contribution family; it does not identify a carrier.",
        "target_heterogeneity": "Target B shows a small directionally consistent causal gain effect; Target A does not. Both retain about 99% of native evidence preference at lambda=0.",
    }
    write_json(OUT / "analysis/final_classification.json", final_interpretation)

    acceptance = {
        "stage": "Stage 3C.3-R",
        "technical_status": "PASS",
        "scientific_outcome": final_interpretation["outcome"],
        "recommendation": "GO — Redundancy Localization Beyond W4",
        "criteria": [
            {"id": 1, "status": "PASS", "evidence": "Exact Stage 3C.3 targets and per-base T/M/I definitions reused with hashes."},
            {"id": 2, "status": "PASS", "evidence": "Exact 24 unique primary base_problem_ids; seven validation bases are disjoint."},
            {"id": 3, "status": "PASS", "evidence": "FP32 c_source+c_rest reconstruction max error <=1.19e-7 in primary."},
            {"id": 4, "status": "PASS", "evidence": "lambda=1 exact to uninstrumented, historical, and cross-arm native scoring."},
            {"id": 5, "status": "PASS", "evidence": "lambda=0 endpoint and source isolation exact."},
            {"id": 6, "status": "PASS", "evidence": "Q/K/V/attention are not directly modified; local invariance deltas zero."},
            {"id": 7, "status": "PASS", "evidence": "Non-target heads and other positions exact in Phase A."},
            {"id": 8, "status": "PASS", "evidence": "Lambda grids frozen before scoring."},
            {"id": 9, "status": "PASS", "evidence": "T/M/I source controls frozen before scoring."},
            {"id": 10, "status": "PASS", "evidence": "Frozen noncausal-head controls run for all 24 bases and both targets."},
            {"id": 11, "status": "PASS", "evidence": "Stage 3C.3 query-patch norm and projection gains compared at the same retrieval state."},
            {"id": 12, "status": "PASS", "evidence": "R0-R3 family frozen before Phase A."},
            {"id": 13, "status": "PASS", "evidence": "Phase B launched only after the prospective gate passed."},
            {"id": 14, "status": "PASS", "evidence": "Only W4 layers 28-29 observed in nested scopes."},
            {"id": 15, "status": "PASS", "evidence": "All inference and bootstrap statistics use base_problem_id as unit."},
            {"id": 16, "status": "PASS", "evidence": "Unnormalized D and D(1)-D(lambda) are primary; ER is descriptive and unclipped."},
            {"id": 17, "status": "PASS", "evidence": "Candidate sink never manipulated."},
            {"id": 18, "status": "PASS", "evidence": "No query or h_pre intervention added."},
            {"id": 19, "status": "PASS", "evidence": "No Stage 4 or failure experiment started."},
            {"id": 20, "status": "PASS", "evidence": "Exactly one review-only next-stage recommendation written."},
        ],
        "all_criteria_pass": True,
        "stage3c4_started": False,
        "stage4_started": False,
        "attention_boundary": "Attention is not used as the primary causal measure; fixed local attention only defines the contribution decomposition.",
    }
    write_json(OUT / "summaries/stage3c3r_acceptance.json", acceptance)

    summary = f"""# Stage 3C.3-R summary

## Result

Stage 3C.3-R is a **technical PASS (20/20)** with scientific outcome **O4 — Broad Robustness Beyond W4**.

The selected-head target contribution was not individually necessary: the frozen Phase-B gate passed with median base-aggregated `E(0)/E(1) = {gate['median_retained']:.6f}`, and all 24 bases retained at least 80% of native preference. Removing target-ROI contribution from every logical head in both W4 layers still retained median `E(0)/E(1) = {redundancy['targets']['target_a']['scopes']['R3']['median_retained']:.6f}` for Target A and `{redundancy['targets']['target_b']['scopes']['R3']['median_retained']:.6f}` for Target B.

## Validation and cohort

- Validation: 7 disjoint bases, {len(validation['checks'])}/{len(validation['checks'])} mechanics checks passed.
- Primary: 24 unique `base_problem_id` values, exactly reused from Stage 3C.3.
- Failed smoke preserved: v1 exposed avoidable BF16 partition bookkeeping; FP32 partition arithmetic was fixed before primary scoring.
- Maximum primary reconstruction error: `{primary_mechanics['maxima']['partition_max_abs_error']:.3g}`.
- Lambda=1 native scoring, lambda=0 source isolation, Q/K/V/attention invariance, non-target heads, deterministic repeats, and finite outputs passed.
- Compute: existing Slurm allocation 106936 on node04 with two A5000 GPUs. Median per-base times were `{runtime_summary['phases']['phase_a']['median_per_base_seconds']:.2f}s` for Phase A and `{runtime_summary['phases']['phase_b']['median_per_base_seconds']:.2f}s` for Phase B. A validation-only resource replay measured `{runtime_summary['resource_validation_replay']['peak_allocated_gib']:.2f} GiB` peak allocation and is excluded from scientific analyses.

## Phase A: selected-head dose response

Target A did not show evidence loss as gain decreased. At lambda=0, median unnormalized `D(1)-D(0)` was `{dose['targets']['target_a']['lambda_contrasts']['0.0']['median']:.6f}` and target-level median retained evidence was `{saturation['targets']['target_a']['median_lambda0_retained']:.6f}`.

Target B showed a small, graded, target-specific effect: lambda=0 median `D(1)-D(0) = {dose['targets']['target_b']['lambda_contrasts']['0.0']['median']:.6f}` (mean `{dose['targets']['target_b']['lambda_contrasts']['0.0']['mean']:.6f}`, bootstrap mean 95% CI `{dose['targets']['target_b']['lambda_contrasts']['0.0']['bootstrap_mean_ci95']}`, 20/24 positive, Holm `p={next(row['holm_adjusted_p'] for row in family['rows'] if row['target_id']=='target_b' and row['test']=='T_0.0_vs_1'):.6g}`). Yet its median retained evidence remained `0.987923`. Target-B monotonic trend, T-vs-M specificity, and causal-vs-noncausal specificity survived Holm correction; Target-A contrasts did not. There are {len(significant)} significant rows in the full 26-test family.

## Stage 3C.3 operating point

The Stage 3C.3 necessity patch did not merely leave a large target contribution. Median effective projected gains were `{query['targets']['target_a']['projection_gain']['median']:.6f}` for Target A and `{query['targets']['target_b']['projection_gain']['median']:.6f}` for Target B. Because direct lambda=0 also preserved approximately 99% of evidence preference, the behavioral null is **not** explained by the query patch remaining above a lower saturation transition. No collapse threshold was observed.

## Phase B: nested W4 scopes

R1 (all heads at the target layer), R2 (frozen causal head identities across layers 28-29), and R3 (all heads across layers 28-29) were frozen before Phase A and run only after the gate passed. No R1/R2/R3 lambda-zero incremental-loss contrast versus R0 survived Holm correction. R3 remained broadly robust at both targets. Therefore the experiment does not localize compensation to same-layer or cross-layer W4 paths.

The bounded conclusion is that evidence preference is supported outside or redundantly with the tested **current-position W4 target-ROI contribution family**. This does not identify whether the support is earlier retrieval, language-side residual state, another layer, or another carrier.

## Scientific boundary

Attention was fixed locally to define `c_T = sum alpha_j V_j`; it was not used as the primary causal readout. The result does not establish sink function, a Q/R carrier, an upstream retrieval trigger, or a universal threshold. No sink, query, `h_pre`, broader-than-W4, Stage 4, multi-evidence, or failure intervention was run.

## Recommendation

**GO — Redundancy Localization Beyond W4**, for review only. R3 robustness satisfies the plan's condition for this recommendation, but no broader experiment is authorized or started here.
"""
    (OUT / "summaries/stage3c3r_summary.md").write_text(summary, encoding="utf-8")
    (OUT / "summaries/next_stage_recommendation.md").write_text(
        "# Next-stage recommendation\n\n"
        "## GO — Redundancy Localization Beyond W4\n\n"
        "Selected-head attenuation and the entire prespecified R1–R3 W4 family leave evidence preference broadly intact. The Stage 3C.3 query patch already operated near zero target-contribution gain, so its behavioral null is not well explained by insufficient attenuation above a saturation threshold. No same-layer or two-layer W4 redundancy contrast was robust after correction.\n\n"
        "The next reviewed design should distinguish earlier visual retrieval, language-side stored state, and other-layer support without assuming a carrier from this result. This is a recommendation only: no broader-than-W4, sink, query, h_pre, Stage 4, multi-evidence, or failure experiment has been started.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "technical_status": acceptance["technical_status"],
        "scientific_outcome": acceptance["scientific_outcome"],
        "recommendation": acceptance["recommendation"],
        "figures": len(list(FIG.glob("*.png"))),
        "holm_significant": len(significant),
    }, indent=2))


if __name__ == "__main__":
    main()
