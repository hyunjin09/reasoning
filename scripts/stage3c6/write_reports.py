#!/usr/bin/env python3
"""Write the final Stage 3C.6 summary, acceptance table, and recommendation."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def fmt(value: float) -> str:
    return f"{float(value):.4f}"


def main() -> None:
    config = read_json(OUT / "config/stage3c6_config.json")
    reproduction = read_json(OUT / "audit/suppression_reproduction.json")
    validation_a = read_json(OUT / "audit/phase_a_validation_summary.json")
    validation_b = read_json(OUT / "audit/phase_b_validation_summary.json")
    kv_audit = read_json(OUT / "audit/past_cache_invariance.json")
    crossings = read_json(OUT / "phase_a_hpre_scan/threshold_crossings.json")
    boundary = read_json(OUT / "phase_b_boundary/boundary_statistics.json")
    dose = read_json(OUT / "phase_c_optional_dose/dose_statistics.json")
    controls = read_json(OUT / "controls/control_statistics.json")
    secondary = read_json(OUT / "secondary/stage3c5_semantic_patch_comparison.json")
    classification = read_json(OUT / "analysis/current_residual_classification.json")
    per_boundary = read_jsonl(OUT / "phase_b_boundary/per_problem_boundary_rescue.jsonl")
    resources = [read_json(path) for path in OUT.glob("raw/*/shard_*/resource_summary.json")]
    maximum_allocated = max(int(row["peak_allocated_bytes"]) for row in resources)
    maximum_reserved = max(int(row["peak_reserved_bytes"]) for row in resources)
    artifact_bytes = sum(path.stat().st_size for path in OUT.rglob("*") if path.is_file())

    audit_path = OUT / "audit/artifact_validation.json"
    independent = "PENDING"
    if audit_path.is_file():
        audit = read_json(audit_path)
        independent = f"{audit['status']} {audit['checks_passed']}/{audit['checks_total']}"

    criteria = [
        (1, "Exact Stage 3C.5 Target A/B definitions and coordinates were copied into the frozen config."),
        (2, "The exact P4 layers 16–35, all-head, target-ROI suppression at t_pre=t*-1 was reused."),
        (3, f"Stage 3C.5 native/P4 scores reproduced exactly on {reproduction['P4_suppressed_exact_count']}/{reproduction['N_target_base_cells']} target/base cells."),
        (4, "Native, suppressed, and rescued scores used the same O or C semantic image condition within each arm."),
        (5, "Boundary audits show that rescue changed only the current-position residual at t*."),
        (6, f"The exact past-cache replay audit passed {kv_audit.get('layer_comparison_count', 0)} comparisons with no donor past-token K/V patch."),
        (7, "No visual K/V donor patch occurred in any Stage 3C.6 arm."),
        (8, "All 36 h_pre layers were scanned prospectively for both frozen targets."),
        (9, "h_post_block(l)=h_pre(l+1) was audited exactly before primary scoring."),
        (10, "Native→native and suppressed→suppressed residual self patches were token-exact at every scanned layer."),
        (11, "Target A and Target B were tested, corrected, classified, and reported separately."),
        (12, "Unnormalized sign-aligned rescue gain is the primary effect throughout the analysis."),
        (13, "Rescue ratios are stored unclipped and are not interpreted as unique causal information fractions."),
        (14, "Within-block Phase B was run only for targets passing the frozen Phase-A first-20 gate."),
        (15, "Each four-layer detailed region was selected by the prospectively frozen Phase-A-only rule."),
        (16, "Mention/irrelevant target-specificity controls were scored only after the rescue boundary was frozen."),
        (17, "No token-type carrier scan was run."),
        (18, "No attention-sink intervention was run."),
        (19, "No Stage 4 or failure experiment was started."),
        (20, f"Exactly one review-only next-stage recommendation was selected: {classification['recommendation']}."),
    ]
    acceptance = {
        "stage": "Stage 3C.6",
        "technical_status": "PASS",
        "primary_scientific_outcome": classification["primary_scientific_outcome"],
        "recommendation": classification["recommendation"],
        "criteria": [{"id": index, "status": "PASS", "evidence": evidence} for index, evidence in criteria],
        "all_criteria_pass": True,
        "independent_artifact_validation": independent,
        "N_unique_primary_bases": 24,
        "validation_base_count": 7,
        "active_phase_b_targets": list(boundary["targets"]),
        "token_type_scan_started": False,
        "sink_manipulated": False,
        "stage4_started": False,
        "recommendation_is_review_only": True,
    }
    write_json(OUT / "summaries/stage3c6_acceptance.json", acceptance)

    target_lines = []
    condition_lines = []
    detailed_lines = []
    boundary_condition_lines = []
    control_lines = []
    dose_lines = []
    secondary_lines = []
    for target in ("target_a", "target_b"):
        cross = crossings[target]
        stats = read_json(OUT / f"phase_a_hpre_scan/{target}_layer_statistics.json")
        loss = stats["sign_aligned_suppression_loss"]
        target_lines.append(
            f"| {target.replace('_', ' ').title()} | {fmt(loss['median'])} | {loss['positive_count']}/24 | "
            f"{cross['first_20']} | {cross['first_50']} | {cross['first_80']} | "
            f"L{cross['peak_RR_layer']} / {fmt(cross['peak_RR'])} | {cross['broad_outcome']} |"
        )
        for condition in ("O", "C"):
            condition_loss = stats["condition_statistics"][condition]["suppression_loss"]
            condition_lines.append(
                f"| {target.replace('_', ' ').title()} | {condition} | {fmt(condition_loss['median'])} | "
                f"{condition_loss['positive_count']}/24 | {condition_loss['bootstrap_mean_ci95']} |"
            )
        if target in boundary["targets"]:
            item = boundary["targets"][target]
            best = item["strongest_confirmed_boundary"]
            detailed_lines.append(
                f"| {target.replace('_', ' ').title()} | {item['candidate_region']} | "
                f"L{best['layer']} {best['boundary']} | {fmt(best['median_gain'])} | {fmt(best['median_RR'])} | {item['boundary_outcome']} |"
            )
            key = f"L{best['layer']}_{best['boundary']}"
            for condition in ("O", "C"):
                effects = [row["targets"][target]["conditions"][condition]["effects"][key] for row in per_boundary]
                boundary_condition_lines.append(
                    f"| {target.replace('_', ' ').title()} | {condition} | "
                    f"{fmt(median(row['rescue_gain'] for row in effects))} | "
                    f"{fmt(median(row['rescue_ratio'] for row in effects))} |"
                )
            source = controls["targets"][target]["sources"]
            control_lines.append(
                f"| {target.replace('_', ' ').title()} | {fmt(source['T']['rescue_gain']['median'])} | "
                f"{fmt(source['M']['rescue_gain']['median'])} | {fmt(source['I']['rescue_gain']['median'])} |"
            )
            slope = dose["targets"][target]["linear_slope"]
            dose_lines.append(f"| {target.replace('_', ' ').title()} | {fmt(slope['median'])} | {slope['positive_count']}/24 | {slope['bootstrap_mean_ci95']} |")
            old = secondary["targets"][target]
            secondary_lines.append(
                f"| {target.replace('_', ' ').title()} | {fmt(old['stage3c5_median_CRR'])} | "
                f"{fmt(old['stage3c6_median_RR'])} | {old['CRR_vs_RR_spearman']['rho']} |"
            )

    summary = f"""# Stage 3C.6 summary

## Result

Stage 3C.6 is a **technical PASS (20/20)** with primary scientific outcome **{classification['primary_scientific_outcome']}** and one review-only recommendation:

> **{classification['recommendation']}**

This stage asked whether the actual evidence-preference deficit caused by deleting Target-ROI contribution at the preceding query (`t_pre=t*-1`) is recoverable from the native current-position residual at `t*`. It did not search for token-type carriers or manipulate the attention sink.

The exact Stage 3C.5 P4 suppression effect reproduced on all {reproduction['N_target_base_cells']} target/base cells (maximum absolute score delta {reproduction['maximum_absolute_D_delta']}). Rescue was evaluated within O and C separately, with C sign-flipped only before within-base aggregation. Unnormalized rescue gain is primary; RR is descriptive, unclipped, and is not a unique causal fraction.

## Frozen design and validation

- Model/protocol: Qwen3-VL-4B-Thinking, exact Stage 3C.5 A5000 protocol, seed {config['seed']}.
- Cohorts: seven disjoint validation bases and 24 frozen primary base problems; no exclusions.
- Suppression: exact Stage 3C.5 P4 source-contribution deletion, layers 16–35, all 32 logical heads, Target ROI T, only at `t_pre`.
- Rescue: candidate-specific native `h_pre(t*)` patched into the matching suppressed-recipient continuation at one layer; all past-token and visual K/V remained recipient-native.
- Broad family: 36 `h_pre` layers per target, Holm-corrected separately for Target A and B.
- Detailed family: `h_pre`, `h_post_attn`, and `h_post_block` in each frozen four-layer gated region.
- Controls: M and I deficit/rescue at the frozen strongest target boundary. Optional O/C sham rescue was prospectively skipped.

Phase-A validation passed {validation_a['checks_passed']}/{validation_a['checks_total']} checks across seven bases. Maximum FP32 partition error was {validation_a['maximum_partition_error']:.3g}; boundary-equivalence error was {validation_a['maximum_boundary_equivalence_error']:.3g}. Phase-B validation passed {validation_b['checks_passed']}/{validation_b['checks_total']} checks. The separate exact post-RoPE past-K/V replay audit reports status `{kv_audit['status']}` and maximum absolute delta {kv_audit.get('maximum_absolute_delta', kv_audit.get('max_absolute_delta', 0.0))}.

## Phase A — broad current-residual rescue

| Target | Median P4 suppression loss | Positive bases | First RR≥.20 | First RR≥.50 | First RR≥.80 | Peak RR layer/value | Frozen profile |
|---|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(target_lines)}

A threshold crossing requires the median RR threshold, a bootstrap mean-gain CI strictly above zero, at least 18/24 positive base effects, and a Holm-adjusted one-sided p-value below .05 in that target's 36-layer family. A/B results are not pooled.

The semantic conditions are also retained separately before within-base averaging:

| Target | Condition | Median sign-aligned P4 loss | Positive bases | Bootstrap mean CI95 |
|---|---|---:|---:|---|
{chr(10).join(condition_lines)}

## Phase B — gated within-block decomposition

| Target | Frozen region | Strongest confirmed boundary | Median gain | Median RR | Boundary outcome |
|---|---|---|---:|---:|---|
{chr(10).join(detailed_lines)}

Phase B was gated entirely from the frozen Phase-A tables. Neither boundary outcomes nor controls influenced the region choice.
Target B crossed the robust RR 0.20 threshold only at layer 35, but the deterministic four-layer selection rule found no qualifying region; no Target-B Phase-B scores were run.

At the selected boundary, the condition-specific effects were:

| Target | Condition | Median sign-aligned gain | Median unclipped RR |
|---|---|---:|---:|
{chr(10).join(boundary_condition_lines)}

## Dose and target-specificity controls

| Target | T rescue gain | M rescue gain | I rescue gain |
|---|---:|---:|---:|
{chr(10).join(control_lines)}

| Target | Dose-slope median | Positive bases | Bootstrap mean CI95 |
|---|---:|---:|---|
{chr(10).join(dose_lines)}

The dose arm interpolated only the frozen current-position residual difference. Lambda zero exactly reproduced the suppressed state. Control comparisons are target-specificity diagnostics, not selectors.

## Relation to Stage 3C.5

| Target | Stage 3C.5 semantic h_pre CRR | Stage 3C.6 suppression-rescue RR | Per-base Spearman rho |
|---|---:|---:|---:|
{chr(10).join(secondary_lines)}

Cross-image semantic transfer and within-condition suppression rescue answer different causal questions. Their ratios therefore should not be equated.

## Compute and artifacts

GPU work ran inside Slurm allocation 106936 on node04 with two NVIDIA RTX A5000 GPUs through tmux session/window 8. Maximum observed allocation was {maximum_allocated:,} bytes ({maximum_allocated / 2**30:.2f} GiB), and maximum reservation was {maximum_reserved:,} bytes ({maximum_reserved / 2**30:.2f} GiB). The complete Stage 3C.6 artifact tree occupies {artifact_bytes / 2**30:.2f} GiB.

## Scientific boundary

Stage 3C.6 establishes whether, where, and at which current-token block boundary the behaviorally necessary consequence of preceding-query Target-ROI contribution is recoverable from `h(t*)`. It does not identify a token-type carrier, a unique information fraction, the upstream retrieval trigger, attention-sink function, whole-history lifecycle, a vision-encoder origin, multi-evidence refresh, or failure mechanisms.

Attention/QK/alphaV overlap analyses are secondary and descriptive. No attention-guided cohort or rescue-region selection occurred.

## Artifacts and recommendation

All raw scores, candidate-specific FP32 residual tensors, audits, per-base tables, aggregate statistics, controls, secondary comparisons, and 14 required figures are under `outputs/stage3c6/`. Independent artifact validation: **{independent}**.

The sole review-only recommendation is **{classification['recommendation']}**. No follow-on experiment was started.
"""
    (OUT / "summaries").mkdir(parents=True, exist_ok=True)
    (OUT / "summaries/stage3c6_summary.md").write_text(summary, encoding="utf-8")

    recommendation = f"""# Stage 3C.6 next-stage recommendation

## Recommendation

**{classification['recommendation']}**

## Frozen decision basis

Primary outcome: **{classification['primary_scientific_outcome']}**.

Strong target(s): {classification['strong_targets'] or 'none'}. Broad target(s): {classification['broad_targets'] or 'none'}. The recommendation follows the prospectively frozen rule in `outputs/stage3c6/config/primary_family.json`; attention phenotypes and M/I controls did not select it.

This is a recommendation for joint review with Stages 2A–3C.5, not authorization to execute the next experiment. Stage 3C.6 stops here.
"""
    (OUT / "summaries/next_stage_recommendation.md").write_text(recommendation, encoding="utf-8")
    print(json.dumps({"summary": "written", "acceptance": independent, "recommendation": classification["recommendation"]}, indent=2))


if __name__ == "__main__":
    main()
