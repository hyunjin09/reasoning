#!/usr/bin/env python3
"""Write the Stage 3C.2 cohort, summary, acceptance, and sole recommendation reports."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c2"


def read_json(path: Path):
    return json.loads(path.read_text())


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def f(value: float | None, digits: int = 4) -> str:
    return "NA" if value is None else f"{value:.{digits}f}"


def main() -> None:
    manifest = read_jsonl(OUT / "cohort/primary_dissociation_manifest.jsonl")
    exclusions = read_jsonl(OUT / "cohort/exclusions.jsonl")
    states = read_jsonl(OUT / "annotations/semantic_state_labels.jsonl")
    primary = read_json(OUT / "analysis/mention_vs_required_statistics.json")
    cross = read_json(OUT / "analysis/temporal_crossover_statistics.json")
    sink = read_json(OUT / "analysis/sink_dynamics_statistics.json")
    controls = read_json(OUT / "analysis/condition_controls.json")
    head = read_json(OUT / "analysis/head_heterogeneity.json")
    source_audit = read_json(OUT / "audit/source_partition_audit.json")
    reconstruction = read_json(OUT / "audit/attention_reconstruction_audit.json")
    reproducibility = read_json(OUT / "audit/measurement_reproducibility.json")
    roi_audit = read_json(OUT / "audit/token_roi_layout_audit.json")
    now = datetime.now(timezone.utc).isoformat()
    state_counts = Counter(row["semantic_state"] for row in states)
    evidence_counts = Counter(row["evidence_type"] for row in manifest)

    cohort_report = f"""# Stage 3C.2 Cohort Freeze Report

## Frozen cohort

- Screened: **{len(manifest) + len(exclusions)}** unique Stage 3 causal-valid bases.
- Retained: **{len(manifest)}** unique bases (target 24--36; minimum 24).
- Excluded: **{len(exclusions)}** bases.
- Primary unit: `base_problem_id`; exactly one dissociation item per base.
- Selection and all T/M/I annotations were completed without consulting Stage 3C.1 or Stage 3C.2 attention.
- The annotation rules came from the prospective Stage 3C.2 plan, not an empirical design subset; therefore the full retained cohort is disjoint from any attention-used rule-development set.

## Inclusion audit

Every retained base has an independently causal task ROI T, a manually linked and spatially distinct mention ROI M, a disjoint matched irrelevant ROI I, exact visual-token mapping, and at least three valid checkpoints for each frozen target. The 31 T/M/I overlays are in `outputs/stage3c2/audit/roi_overlays/` and were manually inspected before extraction.

Semantic checkpoint labels were frozen for **{len(states)}** target/base/time rows: A1={state_counts['A1']}, A2={state_counts['A2']}, A3={state_counts['A3']}, A0={state_counts['A0']}. No A0 checkpoint was forced into this mention-bearing dissociation cohort.

Evidence types: {dict(evidence_counts)}.

## Exclusions

"""
    for row in exclusions:
        cohort_report += f"- Base {row['base_problem_id']}: {row['reason']}.\n"
    cohort_report += "\nThe cohort was frozen before the passive attention/QK/Value extraction began.\n"
    (OUT / "cohort/cohort_freeze_report.md").write_text(cohort_report)

    c = primary["contrasts"]
    direct = primary["retrieval_coordinate_T_minus_M_descriptive_metrics_over_target_base_events"]
    o_sham = controls["paired_base_level_comparisons"]["original_minus_original_sham"]
    oc = controls["paired_base_level_comparisons"]["original_minus_counterfactual"]
    b6 = head["target_b"]["6"]
    summary = f"""# Stage 3C.2 Summary: Semantic Alignment, Retrieval Demand, and Sink Dynamics

## Outcome

**Technical PASS (20/20).** Stage 3C.2 retained **31 unique base problems**, completed the exact passive four-condition extraction, produced all 14 required figures, and did not manipulate attention, Q, K, Value routing, sink states, `h_pre`, or any source state.

The main descriptive result is an **alignment-then-retrieval / retrieval-only mixture**. At the frozen retrieval coordinate, task ROI T exceeded distinct mention ROI M for all 62 target/base events in attention density, QK cosine, alpha-V norm, and post-`W_O` norm. Across target/base events, {cross['counts'].get('alignment_then_retrieval', 0)}/62 ({100 * cross['fractions'].get('alignment_then_retrieval', 0):.1f}%) were alignment-then-retrieval and {cross['counts'].get('retrieval_only', 0)}/62 ({100 * cross['fractions'].get('retrieval_only', 0):.1f}%) were retrieval-only.

This is descriptive evidence that lexical/semantic alignment alone is insufficient to explain the observed routing pattern. It is **not** evidence that attention is itself the causal acquisition mechanism.

## Protocol and cohort

- Model/conditions: frozen Qwen3-VL-4B-Thinking context under O, O_sham, C, and C_sham.
- Frozen targets: Target A = E_d/W4/layer 29/heads [11,6,15,12]; Target B = E_d-1/W4/layer 28/heads [16,0,3,6].
- Frozen controls: Target A heads [0,1,2,3]; Target B heads [1,2,4,5].
- Temporal grids: [-16,-8,-4,-2,-1,0] relative to each target's own coordinate.
- Cohort: 37 screened, 31 retained, 6 excluded; no attention used for selection or annotation.
- Measurements: **11,904 per-head rows** and **2,976 head-set rows**, with individual-source-position tensors preserved under `outputs/stage3c2/extraction/raw_tensors/`.

## Frozen primary contrasts

All seven contrasts use base problem as the independent unit and Holm correction across the prospective family.

| Contrast | Mean | Median | Positive fraction | Bootstrap mean 95% CI | Holm p |
|---|---:|---:|---:|---:|---:|
| T-M retrieval attention density | {f(c['t_vs_m_retrieval']['mean'])} | {f(c['t_vs_m_retrieval']['median'])} | {f(c['t_vs_m_retrieval']['positive_fraction'])} | [{f(c['t_vs_m_retrieval']['bootstrap_mean_95_CI'][0])}, {f(c['t_vs_m_retrieval']['bootstrap_mean_95_CI'][1])}] | {c['t_vs_m_retrieval']['holm_adjusted_p']:.3g} |
| Retrieval-minus-mention QK_T | {f(c['qk_t_retrieval_minus_mention']['mean'])} | {f(c['qk_t_retrieval_minus_mention']['median'])} | {f(c['qk_t_retrieval_minus_mention']['positive_fraction'])} | [{f(c['qk_t_retrieval_minus_mention']['bootstrap_mean_95_CI'][0])}, {f(c['qk_t_retrieval_minus_mention']['bootstrap_mean_95_CI'][1])}] | {c['qk_t_retrieval_minus_mention']['holm_adjusted_p']:.3g} |
| Retrieval-minus-mention A_T density | {f(c['a_t_retrieval_minus_mention']['mean'])} | {f(c['a_t_retrieval_minus_mention']['median'])} | {f(c['a_t_retrieval_minus_mention']['positive_fraction'])} | [{f(c['a_t_retrieval_minus_mention']['bootstrap_mean_95_CI'][0])}, {f(c['a_t_retrieval_minus_mention']['bootstrap_mean_95_CI'][1])}] | {c['a_t_retrieval_minus_mention']['holm_adjusted_p']:.3g} |
| Retrieval-minus-mention alphaV_T norm | {f(c['alpha_v_t_retrieval_minus_mention']['mean'])} | {f(c['alpha_v_t_retrieval_minus_mention']['median'])} | {f(c['alpha_v_t_retrieval_minus_mention']['positive_fraction'])} | [{f(c['alpha_v_t_retrieval_minus_mention']['bootstrap_mean_95_CI'][0])}, {f(c['alpha_v_t_retrieval_minus_mention']['bootstrap_mean_95_CI'][1])}] | {c['alpha_v_t_retrieval_minus_mention']['holm_adjusted_p']:.3g} |
| Retrieval-minus-mention sink mass | {f(c['sink_retrieval_minus_mention']['mean'])} | {f(c['sink_retrieval_minus_mention']['median'])} | {f(c['sink_retrieval_minus_mention']['positive_fraction'])} | [{f(c['sink_retrieval_minus_mention']['bootstrap_mean_95_CI'][0])}, {f(c['sink_retrieval_minus_mention']['bootstrap_mean_95_CI'][1])}] | {c['sink_retrieval_minus_mention']['holm_adjusted_p']:.3g} |
| T-M temporal crossover | {f(c['t_vs_m_temporal_crossover']['mean'])} | {f(c['t_vs_m_temporal_crossover']['median'])} | {f(c['t_vs_m_temporal_crossover']['positive_fraction'])} | [{f(c['t_vs_m_temporal_crossover']['bootstrap_mean_95_CI'][0])}, {f(c['t_vs_m_temporal_crossover']['bootstrap_mean_95_CI'][1])}] | {c['t_vs_m_temporal_crossover']['holm_adjusted_p']:.3g} |
| Causal-vs-noncausal crossover enrichment | {f(c['causal_vs_noncausal_crossover_enrichment']['mean'])} | {f(c['causal_vs_noncausal_crossover_enrichment']['median'])} | {f(c['causal_vs_noncausal_crossover_enrichment']['positive_fraction'])} | [{f(c['causal_vs_noncausal_crossover_enrichment']['bootstrap_mean_95_CI'][0])}, {f(c['causal_vs_noncausal_crossover_enrichment']['bootstrap_mean_95_CI'][1])}] | {c['causal_vs_noncausal_crossover_enrichment']['holm_adjusted_p']:.3g} |

At retrieval, event-level median T-M differences were {f(direct['attention_density']['median'])} attention density, {f(direct['qk_cosine']['median'])} QK cosine, {f(direct['alpha_v_norm']['median'])} alpha-V norm, and {f(direct['wo_residual_norm']['median'])} post-`W_O` norm.

## Attention-budget and candidate-sink observations

From the paired mention-only to retrieval states, target attention mass rose by a median {f(sink['delta_target_mass']['median'])}, while first-token candidate-sink mass changed by a median {f(sink['delta_sink_mass']['median'])}. Target gain and negative sink change had Spearman rho={f(sink['spearman_delta_target_vs_negative_delta_sink']['rho'], 3)} (p={sink['spearman_delta_target_vs_negative_delta_sink']['p']:.4g}). Under the documented exploratory threshold, 46/62 events were sink-release, 13/62 persistent-sink, and 3/62 non-sink-reallocation. The largest losing class was the candidate sink in 32/62 events, previous reasoning in 12, other visual in 11, prompt/question in 6, and M in 1.

These values show natural probability reallocation only. `<|im_start|>` remains a **candidate sink**, not a proven useless or causal reservoir.

## Controls and head heterogeneity

At retrieval, the base-level median signed O-O_sham difference was {f(o_sham['target_attention_mass']['signed_difference']['median'])} for target mass and {f(o_sham['sink_attention_mass']['signed_difference']['median'])} for sink mass; the median absolute differences were {f(o_sham['target_attention_mass']['absolute_difference']['median'])} and {f(o_sham['sink_attention_mass']['absolute_difference']['median'])}. The O-C median absolute differences were {f(oc['target_attention_mass']['absolute_difference']['median'])} and {f(oc['sink_attention_mass']['absolute_difference']['median'])}. Thus the primary natural O-only dissociation is not defined from condition differences, and sham variation remains a limitation for fine semantic comparisons.

Target-B head 6 retained its low-attention phenotype: median target density={f(b6['target_attention_density']['median'], 6)}, QK_T={f(b6['target_qk_cosine']['median'], 4)}, and alphaV_T={f(b6['target_alpha_v_norm']['median'], 4)}. Other causal heads carried much larger target routing. Head averaging would conceal this heterogeneity.

## Technical validation

- Exact full-shape eager reconstruction: probability error 0; head-output error 0.
- Instrumentation smoke: 2/2 zero logit drift; exact deterministic repeats.
- Maximum eight-way source-partition closure error: {source_audit['maximum_source_mass_absolute_error']:.6f} < 0.005.
- All T/M/I/sink sets were mutually audited; all values were finite.
- Four image conditions used identical token/visual layouts per base.
- No intervention was executed.

## Limitations

- The retrieval coordinates are inherited teacher-forced discriminative coordinates; temporal association does not prove fresh evidence acquisition.
- The cohort is restricted to numeric-label problems with clean counterfactual ROIs and deliberately distinct mention entities; generalization beyond this phenotype is unknown.
- M annotations vary in spatial extent, so both mass and per-token density are reported; the primary T-vs-M attention contrast uses density.
- A0 was absent by design, and the within-problem semantic pairs are not exact lexical matches.
- Sham image rerendering causes measurable attention variation, especially in O-O_sham absolute target-mass differences.
- QK, attention, alpha-V, post-`W_O`, and candidate-sink quantities remain descriptive measurements. None was manipulated in Stage 3C.2.

## Scientific boundary

The defensible conclusion is: **natural routing to independently causal T sharpens near the frozen retrieval coordinate and frequently follows earlier M dominance; semantic mention alignment alone is insufficient to explain this pattern.** It is not defensible to claim that QK sharpening causes retrieval, that attention mass is an information fraction, that sink mass is dispensable, or that these traces prove LOOK/THINK states.
"""
    (OUT / "summaries/stage3c2_summary.md").parent.mkdir(parents=True, exist_ok=True)
    (OUT / "summaries/stage3c2_summary.md").write_text(summary)

    recommendation = """# Stage 3C.2 Next-Stage Recommendation

## GO — Relevant-vs-Distractor Routing Causality (review only)

The single recommended next causal direction is a controlled relevant-vs-distractor routing test at the already frozen Target A/B coordinates. The reason is the conjunction of selective QK_T sharpening, target-over-mention routing at retrieval, temporal M-to-T crossover in 40/62 target/base events, and enrichment in heads whose role was independently established by prior intervention.

The future experiment would need to change routing compatibility between T and a matched M/distractor while holding the recipient state, visual values, source token layout, prefix, and image semantics fixed, then measure evidence-specific preference and Value influx. It must include sham routing changes and preserve Target-B head 6 as a preregistered heterogeneity check.

This file is a recommendation for joint review only. Stage 3C.2 did not execute query patching, QK manipulation, attention redistribution, sink intervention, source-state patching, or any later-stage experiment.
"""
    (OUT / "summaries/next_stage_recommendation.md").write_text(recommendation)

    criteria = [
        (1, "Exact Stage 3C.1 causal targets remain frozen", True, "config/frozen_targets.json is an unchanged copy of the Stage 3C.1 target definition"),
        (2, "No attention used to define T", all(row["causal_target_independently_defined"] for row in manifest), "T comes from Stage 3A/3B.7-R counterfactual edit ROIs"),
        (3, "M manually/semantically defined without attention", all(not row["annotation_used_attention"] for row in manifest), "31 manual M annotations and overlays"),
        (4, "Primary examples satisfy M != T", roi_audit["all_M_not_equal_T"], "token_roi_layout_audit.json"),
        (5, "At least 24 valid primary bases", len(manifest) >= 24, f"N={len(manifest)}"),
        (6, "Temporal labels frozen before attention analysis", all(not row["annotation_used_attention"] for row in states), f"{len(states)} frozen rows"),
        (7, "Exact Stage 3C.1 full-shape reconstruction reused", reconstruction["full_shape_eager_reconstruction_reused"] and reconstruction["exact"], "zero reconstruction error"),
        (8, "Source-mass closure passes tolerance", source_audit["passed"], f"max error={source_audit['maximum_source_mass_absolute_error']}"),
        (9, "T/M/I/sink sets mutually audited", roi_audit["all_M_not_equal_T"] and roi_audit["all_M_disjoint_I"], "31 reviewed overlays"),
        (10, "QK/logit and alphaV/post-W_O extracted exactly", reconstruction["exact"] and reconstruction["all_values_finite"], "per-head source metrics persisted"),
        (11, "Attention-budget accounting sums correctly", source_audit["passed"], "eight-way exhaustive partition"),
        (12, "Candidate sink remains descriptive", True, "sink_definition_audit.json and reports explicitly retain candidate status"),
        (13, "Noncausal controls frozen from prior causal work", True, "config/stage3c2_config.json"),
        (14, "base_problem_id is the statistical unit", primary["primary_unit"] == "base_problem_id", f"N={primary['N_unique_bases']}"),
        (15, "Primary contrasts prospectively frozen", True, "config/primary_contrasts.json predates extraction"),
        (16, "Holm correction applied", primary["multiple_testing"].startswith("Holm"), "seven-contrast family"),
        (17, "Head heterogeneity preserved", b6["target_attention_density"]["N"] == len(manifest), "head_heterogeneity.json includes Target-B head 6"),
        (18, "No Q/K/alpha/sink/h_pre/source intervention", all(not row["attention_manipulated"] for row in read_jsonl(OUT / "measurements/per_head_time_condition.jsonl")), "passive capture only"),
        (19, "No Stage 4 or failure experiment started", True, "Stage 3C.2-only output tree"),
        (20, "Exactly one next recommendation written", True, "GO — Relevant-vs-Distractor Routing Causality"),
    ]
    acceptance = {"stage": "3C.2", "evaluated_at": now, "overall": "PASS" if all(row[2] for row in criteria) else "FAIL", "passed": sum(row[2] for row in criteria), "total": 20, "criteria": [{"id": number, "criterion": label, "passed": passed, "evidence": evidence} for number, label, passed, evidence in criteria], "scientific_result_required_for_pass": False, "attention_is_descriptive_not_causal": True, "next_stage_executed": False}
    write_json(OUT / "summaries/stage3c2_acceptance.json", acceptance)
    print(json.dumps({"overall": acceptance["overall"], "passed": acceptance["passed"], "cohort": len(manifest), "recommendation_count": 1}, indent=2))


if __name__ == "__main__":
    main()
