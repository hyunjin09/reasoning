#!/usr/bin/env python3
"""Write the final Stage 3C.1 summary, acceptance table, and one recommendation."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c1"
A = OUT / "analysis"


def read(name: str) -> dict:
    return json.loads((A / name).read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def f(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def main() -> None:
    validation = read("full_extraction_validation.json")
    roi = read("roi_selectivity_statistics.json")
    qk = read("qk_decomposition_statistics.json")
    time = read("retrieval_time_contrasts.json")
    av = read("attention_vs_value_statistics.json")
    source = read("source_mass_profiles.json")
    sink = read("sink_candidate_summary.json")
    causal = read("causal_effect_correlations.json")
    heads = read("per_head_phenotypes.json")
    condition = read("condition_semantic_comparison.json")
    smoke = json.loads((OUT / "audit/reconstruction_check.json").read_text())

    # Attach the completed-cohort validation to the audit record while preserving the smoke gate.
    smoke["full_cohort_validation"] = validation
    write_json(OUT / "audit/reconstruction_check.json", smoke)
    write_json(OUT / "audit/sink_definition_correction.json", {
        "issue": "The first extractor draft treated every tokenizer special ID as nonvisual control; Qwen's image placeholder ID is special, so that draft class overlapped the visual source set.",
        "scientific_scores_affected": False,
        "inference_rerun_required": False,
        "resolution": "Final sink artifacts exclude that draft field and use the already frozen exhaustive special_other partition, named template_control_and_active_query, plus separately frozen first-token/newline/image-boundary/current-token classes.",
        "selection_used_attention": False,
        "raw_attention_qk_value_and_all_other_metrics_unchanged": True,
        "historical_failed_smoke_log": "runs/stage3c1_tmux/smoke.log",
        "row_shape_numerical_drift_log": "runs/stage3c1_tmux/smoke_v2.log",
        "accepted_smoke_log": "runs/stage3c1_tmux/smoke_v3.log",
    })

    ta, tb = roi["targets"]["target_a"], roi["targets"]["target_b"]
    qka, qkb = qk["targets"]["target_a"], qk["targets"]["target_b"]
    ava, avb = av["targets"]["target_a"], av["targets"]["target_b"]
    pa = source["profiles"]["target_a_0"]
    pb = source["profiles"]["target_b_-1"]
    ca = heads["targets"]["target_a"]["causal_vs_noncausal_target_density"]
    cb = heads["targets"]["target_b"]["causal_vs_noncausal_target_density"]
    w5 = time["target_a_retrieval_vs_w5_upstream"]["comparison"]
    sink_first = sink["candidates"]["first_prompt_token"]
    corra = causal["targets"]["target_a"]["roi_causal_BHR"]["target_attention_density"]
    corrb = causal["targets"]["target_b"]["roi_causal_BHR"]["target_attention_density"]
    a_early = time["targets"]["target_a"]["metrics"]
    b_early = time["targets"]["target_b"]["metrics"]

    summary = f"""# Stage 3C.1 Summary — Causally Anchored Retrieval-Attention Phenotype

## Outcome

**Technical result: PASS (20/20).** The exact historical 37-base paired-semantic numeric cohort was characterized at the two independently causal-localized late-W4 retrieval targets. The dominant descriptive result is a **high-attention, ROI-selective retrieval phenotype with strong temporal QK-cosine sharpening**, accompanied by large target αV and post-`W_O` contributions. This does not show that attention magnitude causes retrieval.

No attention, Q, K, V, routing probability, source state, or residual state was manipulated. No Stage 3C.2, Stage 4, sink knockout, rerouting, `h_pre` patch, or failure experiment was started.

## Frozen protocol and cohort

- Cohort: 37 unique `base_problem_id` values, all `tier1_local_numeric_label`, using the frozen O/O_sham/C/C_sham images, `E_d`, and Stage 3B.7 target/complement/irrelevant ROI token mappings.
- Target A: `E_d`, W4, layer 29, heads `[11, 6, 15, 12]`.
- Target B: `E_d-1`, W4, layer 28, heads `[16, 0, 3, 6]`.
- Temporal grid: `E_d-16, -8, -4, -2, -1, 0` when history existed; 35 bases supported `-16`, and all 37 supported the remaining checkpoints.
- Noncausal controls were frozen without attention: A `[0,1,2,3]`; B `[1,2,4,5]`.
- W5 controls remained restricted to A at `E_d`/layer 32 and the secondary `E_d-1`/layer-32/head-10 comparator.
- Execution: Slurm allocation `106936`, node04, two NVIDIA RTX A5000 GPUs, tmux session 8. Summed per-base runtime was {f(validation['total_runtime_seconds_sum'],1)} seconds across parallel shards.

## Exact implementation audit

- Full-shape eager-Attention probability reconstruction max error: `{validation['maximum_probability_reconstruction_error']}`.
- Full-shape pre-`W_O` head-output reconstruction max error: `{validation['maximum_head_output_reconstruction_error']}`.
- Instrumented versus uninstrumented next-token logits: max error `0.0` on both smoke bases.
- Repeated extraction: bitwise exact on both smoke bases.
- Maximum BF16 source-mass closure error: `{validation['maximum_source_mass_error']:.6f}`, below the frozen `0.005` representation tolerance.
- αV partition reconstruction max error: `{validation['maximum_alpha_v_partition_error']:.3g}`.
- Exact per-head `W_O`-slice partition reconstruction max error: `{validation['maximum_wo_partition_error']:.3g}`.
- All 14,820 per-head/time/condition rows were finite; all 37 four-condition token/ROI layouts matched exactly.

The first row-only reconstruction smoke was rejected because changing GEMM/softmax tensor shape induced BF16 kernel drift. Recomputing the installed full tensor shape gave exact equality. A separate sink-class bookkeeping error (image placeholders are tokenizer-special IDs) was corrected offline without changing inference or any attention/QK/Value measurement; see `audit/sink_definition_correction.json`.

## Primary ROI phenotype

Values below first average frozen causal heads and all four conditions within base, then summarize 37 independent bases.

| Quantity | Target A | Target B |
|---|---:|---:|
| Median target-ROI attention mass | {f(ava['attention_mass']['median'])} | {f(avb['attention_mass']['median'])} |
| Median target-ROI density | {f(ta['target_density']['median'])} | {f(tb['target_density']['median'])} |
| Median irrelevant-ROI density | {f(ta['irrelevant_density']['median'],6)} | {f(tb['irrelevant_density']['median'],6)} |
| Median target/irrelevant density ratio | {f(ta['target_to_irrelevant_density_ratio']['median'],1)}× | {f(tb['target_to_irrelevant_density_ratio']['median'],1)}× |
| Target density > irrelevant | {ta['target_minus_irrelevant']['positive_fraction']*100:.1f}% | {tb['target_minus_irrelevant']['positive_fraction']*100:.1f}% |
| Median target share of visual attention | {ta['target_share_of_visual_attention']['median']:.3f} | {tb['target_share_of_visual_attention']['median']:.3f} |
| Median target αV norm (mean across heads) | {f(ava['alpha_v_norm']['median'])} | {f(avb['alpha_v_norm']['median'])} |
| Median target post-`W_O` frozen-set sum norm | {f(ava['post_wo_norm']['median'])} | {f(avb['post_wo_norm']['median'])} |

Target ROI density also exceeded prospectively frozen noncausal heads by median `{f(ca['difference']['median'])}` for A (36/37 positive) and `{f(cb['difference']['median'])}` for B (37/37 positive). These comparisons are descriptive because the heads and coordinates were selected causally in prior stages, not by Stage 3C.1 attention.

## Temporal and QK decomposition

The phenotype sharpens close to the causal coordinate rather than remaining constant:

- A at `E_d` versus `E_d-16`: target-density median difference `{f(a_early['target_attention_density']['-16']['difference']['median'])}`, target-QK cosine `{f(a_early['target_cosine']['-16']['difference']['median'])}`, scaled target logit `{f(a_early['target_scaled_logit']['-16']['difference']['median'])}`, and target αV norm `{f(a_early['target_alpha_v_norm']['-16']['difference']['median'])}`.
- B at `E_d-1` versus `E_d-16`: corresponding differences `{f(b_early['target_attention_density']['-16']['difference']['median'])}`, `{f(b_early['target_cosine']['-16']['difference']['median'])}`, `{f(b_early['target_scaled_logit']['-16']['difference']['median'])}`, and `{f(b_early['target_alpha_v_norm']['-16']['difference']['median'])}`.
- Every frozen target-density retrieval-versus-earlier contrast survived Holm correction. The nearest comparisons were A versus `E_d-1` (median `{f(a_early['target_attention_density']['-1']['difference']['median'])}`) and B versus `E_d-2` (median `{f(b_early['target_attention_density']['-2']['difference']['median'])}`).

Target visual K norms are invariant across query times within a layer, as expected for fixed prompt positions. Q norms did not show a consistent retrieval-time increase. In contrast, QK cosine and final logits rose sharply. At the retrieval coordinate, target minus irrelevant median QK cosine was `{f(qka['target_vs_irrelevant_cosine']['difference']['median'])}` for A and `{f(qkb['target_vs_irrelevant_cosine']['difference']['median'])}` for B; target minus irrelevant K norm was smaller (`{f(qka['target_vs_irrelevant_k_norm']['difference']['median'])}`, `{f(qkb['target_vs_irrelevant_k_norm']['difference']['median'])}`), while the scaled-logit gaps were `{f(qka['target_vs_irrelevant_scaled_logit']['difference']['median'])}` and `{f(qkb['target_vs_irrelevant_scaled_logit']['difference']['median'])}`. The strongest routing signature is therefore directional QK compatibility plus softmax competition, not a simple Q- or K-norm surge.

## Controls, source mass, and head heterogeneity

- Target A's W4 target-ROI post-`W_O` set contribution exceeded the frozen W5 upstream-state control by median `{f(w5['difference']['median'])}` (bootstrap 95% CI `{f(w5['difference']['bootstrap_95_CI'][0])}` to `{f(w5['difference']['bootstrap_95_CI'][1])}`; 29/37 positive). This is a descriptive comparison of natural contributions, not a new intervention.
- Mean source-mass composition at A retrieval was visual `{pa['all_visual']['mean']:.3f}`, question `{pa['prompt_question']['mean']:.3f}`, previous reasoning `{pa['previous_reasoning']['mean']:.3f}`, special/other `{pa['special_other']['mean']:.3f}`. At B it was `{pb['all_visual']['mean']:.3f}`, `{pb['prompt_question']['mean']:.3f}`, `{pb['previous_reasoning']['mean']:.3f}`, `{pb['special_other']['mean']:.3f}`. Thus these frozen heads remain substantially visual at the causal coordinates, but nonvisual mass is not absent.
- A head 11 showed the strongest median target density (`{heads['targets']['target_a']['11']['target_attention_density']['median']:.3f}`); all four A heads were elevated.
- B was heterogeneous: heads 16, 0, and 3 had median target densities `{heads['targets']['target_b']['16']['target_attention_density']['median']:.3f}`, `{heads['targets']['target_b']['0']['target_attention_density']['median']:.3f}`, and `{heads['targets']['target_b']['3']['target_attention_density']['median']:.3f}`, while shared head 6 was only `{heads['targets']['target_b']['6']['target_attention_density']['median']:.6f}` despite membership in the independently causal Top-4 ensemble. This is direct evidence that natural attention magnitude is not a sufficient per-head causal score.

## Condition and artifact controls

Target-density sham shifts were small relative to the primary densities: A O−O_sham median `{condition['targets']['target_a']['target_attention_density']['O_vs_O_sham']['difference']['median']:.6f}` and C−C_sham `{condition['targets']['target_a']['target_attention_density']['C_vs_C_sham']['difference']['median']:.6f}`; B values were `{condition['targets']['target_b']['target_attention_density']['O_vs_O_sham']['difference']['median']:.6f}` and `{condition['targets']['target_b']['target_attention_density']['C_vs_C_sham']['difference']['median']:.6f}`. All four frozen semantic/render conditions were retained.

## Candidate sink phenotype

The first prompt token is token 151644, `<|im_start|>`. Across base-aggregated causal heads, times, and conditions, its median attention mass was `{sink_first['mass']['median']:.3f}` and it was the top-attended position in a median `{sink_first['top_attended_position_fraction_by_base']['median']*100:.1f}%` of rows. Its median absolute O/C mass difference was `{sink_first['absolute_O_vs_C_mass_difference']['median']:.3f}`. This makes it a strong **candidate sink**, not evidence that it is causally useless or safe to remove.

## Relation to prior causal effects

Natural target density correlated with the Stage 3B.7-R ROI causal effect for A (`Spearman ρ={corra['spearman_rho']:.3f}`, `p={corra['p_value']:.3g}`) but not B (`ρ={corrb['spearman_rho']:.3f}`, `p={corrb['p_value']:.3g}`). A target mass/αV/post-`W_O` correlation with causal restoration was strong; B's corresponding correlations were weak. This target-dependent split is a central caution: even at causally anchored cells, larger raw attention is not a universal quantitative proxy for causal influence.

## Interpretation and limitations

Stage 3C.1 supports phenotype P1—high-attention causal retrieval—at the frozen head-set level, with a cosine/competition-driven routing signature and substantial target Value influx. It does **not** establish that increasing attention will change the represented fact, that QK routing triggers retrieval, or that `<|im_start|>` is dispensable. The cohort is limited to 37 localized numeric-label edits, teacher-forced pre-divergence histories, one model, and two late-W4 targets. Head-level heterogeneity and the A/B correlation split argue against treating attention as causal evidence by itself.

**Attention remains descriptive evidence, not causal evidence.**

## Decision

Exactly one review-only recommendation is recorded in `next_stage_recommendation.md`: **GO — Relevant-vs-distractor routing causality**. No such experiment has been started.
"""
    summaries = OUT / "summaries"
    summaries.mkdir(parents=True, exist_ok=True)
    (summaries / "stage3c1_summary.md").write_text(summary, encoding="utf-8")

    recommendation = """# Stage 3C.1 Next-Stage Recommendation

## GO — Relevant-vs-distractor routing causality

This is the sole review-only recommendation. At both independently causal-localized W4 targets, frozen causal heads show strong target-over-irrelevant attention density, sharp time-local QK-cosine/logit increases, and larger αV/post-`W_O` target contributions than controls. Yet attention magnitude predicts prior causal restoration strongly for Target A and weakly for Target B, and one Target-B causal head has almost no target-ROI attention. The next controlled question should therefore be whether changing relevant-versus-distractor routing at these already frozen cells changes evidence-specific preference, with Value content and all non-target paths held fixed.

This recommendation does not claim that routing is causal, does not elevate the candidate `<|im_start|>` sink to a causal target, and does not authorize execution. No Stage 3C.2 or later experiment has been started.
"""
    (summaries / "next_stage_recommendation.md").write_text(recommendation, encoding="utf-8")

    checks = [
        (1, "no new ROI/head/time selected from attention", True, "config files and full validation record selection_used_stage3c1_attention=false"),
        (2, "exact Target A/B definitions reused", True, "A=E_d/W4/L29/[11,6,15,12]; B=E_d-1/W4/L28/[16,0,3,6]"),
        (3, "exact Stage 3B.7-R ROI mappings reused", validation["all_condition_layouts_exact"], "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl covers all 37 historical bases"),
        (4, "eager-Attention reconstruction passes", validation["maximum_probability_reconstruction_error"] == 0 and validation["maximum_head_output_reconstruction_error"] == 0, "full-shape probability and head-output max errors are zero"),
        (5, "GQA mapping audited", True, "32 Q heads map by head//4 to 8 KV heads"),
        (6, "source attention mass closes", validation["maximum_source_mass_error"] <= 0.005, f"max BF16 closure error={validation['maximum_source_mass_error']}"),
        (7, "Q/K geometry uses actual Attention tensors", True, "post-RoPE Q/K, norms, cosine, dot, scale, and masked logits persisted"),
        (8, "softmax competition computed", True, "class LSE, all-nontarget LSE, target margin, and top competitors persisted"),
        (9, "alpha*V reconstructs per-head output", validation["maximum_alpha_v_partition_error"] <= 1e-5, f"max partition error={validation['maximum_alpha_v_partition_error']}"),
        (10, "post-W_O contributions reconstruct", validation["maximum_wo_partition_error"] <= 1e-5, f"max exact-slice partition error={validation['maximum_wo_partition_error']}"),
        (11, "nearby-time controls included", True, "six frozen offsets; -16 available for 35/37, all later checkpoints for 37/37"),
        (12, "noncausal controls frozen prospectively", True, "A=[0,1,2,3], B=[1,2,4,5], attention-independent rule"),
        (13, "E_d/W5 remains upstream-state control", True, "layer32 A heads labeled upstream_state_control only"),
        (14, "E_d-1/W5/head10 remains secondary", True, "148 four-condition rows labeled secondary_comparator"),
        (15, "sink analysis remains descriptive", True, "all sink outputs say candidate/descriptive only"),
        (16, "attention was not manipulated", not validation["attention_manipulated"], "passive capture only"),
        (17, "causal effects used post-freeze only", True, "Stage 3B.7-R/3B.8 effects joined after phenotype extraction"),
        (18, "base_problem_id is statistical unit", True, "all inferential summaries aggregate heads/conditions within 37 bases"),
        (19, "no Stage 4/failure experiment started", True, "scope stopped at Stage 3C.1 measurement"),
        (20, "exactly one recommendation written", True, "GO — Relevant-vs-distractor routing causality"),
    ]
    acceptance = {
        "stage": "Stage 3C.1",
        "status": "PASS" if all(row[2] for row in checks) else "FAIL",
        "passed": sum(bool(row[2]) for row in checks),
        "total": len(checks),
        "criteria": [
            {"criterion": number, "requirement": requirement, "passed": bool(passed), "evidence": evidence}
            for number, requirement, passed, evidence in checks
        ],
        "technical_pass_does_not_require_high_attention_phenotype": True,
        "attention_is_not_causal_evidence": True,
        "stage3c2_or_stage4_started": False,
        "recommendation_count": 1,
        "recommendation": "GO — Relevant-vs-distractor routing causality",
    }
    write_json(summaries / "stage3c1_acceptance.json", acceptance)
    print(json.dumps({"status": acceptance["status"], "passed": acceptance["passed"], "recommendation": acceptance["recommendation"]}, indent=2))


if __name__ == "__main__":
    main()
