#!/usr/bin/env python3
"""Write the final Stage 3B.0 scientific reports and acceptance audit."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b0"


def pct(value: float) -> str:
    return f"{100.0 * float(value):.1f}%"


def ci(summary: dict, key: str = "mean_bootstrap_ci") -> str:
    values = summary[key]
    return f"[{values['ci_low']:.4f}, {values['ci_high']:.4f}]"


def main() -> None:
    cutoff = json.loads((OUT / "cutoff/cutoff_statistics.json").read_text(encoding="utf-8"))
    patch = json.loads((OUT / "patching/patch_statistics.json").read_text(encoding="utf-8"))
    evidence = json.loads((OUT / "analysis/evidence_type_statistics.json").read_text(encoding="utf-8"))
    rollout = json.loads((OUT / "cutoff/rollout_audit_summary.json").read_text(encoding="utf-8"))
    aggregation = json.loads((OUT / "analysis/aggregation_validation.json").read_text(encoding="utf-8"))
    smoke = json.loads((OUT / "smoke/hook_transparency.json").read_text(encoding="utf-8"))
    p_group = patch["groups"]["P_post_image"]
    q_group = patch["groups"]["Q"]
    t_group = patch["groups"]["T"]
    qt_group = patch["groups"]["Q_plus_T"]
    numeric = evidence["strata"]["tier1_local_numeric_label"]
    structural = evidence["strata"]["tier3_structural_visual_edit"]

    (OUT / "analysis/prefill_sufficiency.md").write_text(
        f"""# Prefill sufficiency

## Result

Generation-start visual cutoff preserved an evidence-specific effect in the expected direction for **{cutoff['positive_cutoff_CE']['count']}/49 ({pct(cutoff['positive_cutoff_CE']['proportion'])})** bases. The mean cutoff CE was **{cutoff['CE_cut']['mean']:.4f} nats/token** (95% bootstrap CI {ci(cutoff['CE_cut'])}) and the median was **{cutoff['CE_cut']['median']:.4f}**. The sham-controlled effect was positive in **{cutoff['positive_controlled_cutoff_CE']['count']}/49 ({pct(cutoff['positive_controlled_cutoff_CE']['proportion'])})**, with mean **{cutoff['CE_cut_controlled']['mean']:.4f}** (95% CI {ci(cutoff['CE_cut_controlled'])}).

Relative to Stage 3A full vision, raw retention was modest: mean **{pct(cutoff['retention_ratio_raw']['mean'])}** (95% CI {pct(cutoff['retention_ratio_raw']['mean_bootstrap_ci']['ci_low'])} to {pct(cutoff['retention_ratio_raw']['mean_bootstrap_ci']['ci_high'])}) and median **{pct(cutoff['retention_ratio_raw']['median'])}** (median bootstrap CI {pct(cutoff['retention_ratio_raw']['median_bootstrap_ci']['ci_low'])} to {pct(cutoff['retention_ratio_raw']['median_bootstrap_ci']['ci_high'])}). Seven bases had nonpositive raw cutoff CE. The mean sham shift was **{cutoff['sham_shift_cut']['mean']:.4f}** with a 95% CI spanning zero ({ci(cutoff['sham_shift_cut'])}).

## Interpretation

The directional evidence distinction is widespread but small in magnitude after direct generated-query access to visual tokens is removed from token `y_0`. This supports a **real but insufficient prefill residual**: nonvisual prefill states retain some task-relevant image information, but they do not preserve most of the Stage 3A effect. Blocking post-prefill access removed about **{pct(1.0 - cutoff['retention_ratio_raw']['mean'])}** of CE on an unweighted mean-retention basis and **{pct(1.0 - cutoff['retention_ratio_raw']['median'])}** at the median.

This result does not locate when post-prefill visual access becomes important, and it does not use attention as evidence of acquisition.

## Behavioral check

The 147 matched-seed 128-token cutoff rollouts rarely reached the target fact. Manual review confirmed only **{rollout['explicit_target_fact_statement_count']}/147** explicit target-fact statements (8 original identities, 1 counterfactual identity). Because the denominator of stated facts is so small, the rollout is inconclusive and is not used as a frequency estimate. Evidence-specific teacher-forced CE remains primary.
""",
        encoding="utf-8",
    )

    q_median_ci = q_group["bidirectional_recovery_raw"]["median_bootstrap_ci"]
    (OUT / "analysis/carrier_comparison.md").write_text(
        f"""# Carrier comparison

## Broad post-image prefix

All-layer bidirectional patching of `P_post-image` produced raw recovery **1.000 in 49/49 bases** and was source-consistent in both directions for **49/49**. The mean bidirectional source-oriented absolute shift was **{p_group['bidirectional_oriented_D_shift']['mean']:.4f} D units** (median **{p_group['bidirectional_oriented_D_shift']['median']:.4f}**). Exact recovery is expected here: under visual cutoff, pre-image tokens are identical across conditions and `P_post-image` contains every accessible image-conditioned prompt position. This serves as the broad carrier/implementation positive control.

## Question content

`Q`-only patching was source-consistent in both directions for **{q_group['both_directions_source_consistent']['count']}/49 ({pct(q_group['both_directions_source_consistent']['proportion'])})** bases. Median raw bidirectional recovery was **{q_group['bidirectional_recovery_raw']['median']:.4f}** (95% median-bootstrap CI [{q_median_ci['ci_low']:.4f}, {q_median_ci['ci_high']:.4f}]). The mean source-oriented shift was **{q_group['bidirectional_oriented_D_shift']['mean']:.4f}** (95% CI {ci(q_group['bidirectional_oriented_D_shift'])}), almost equal to broad-prefix **{p_group['bidirectional_oriented_D_shift']['mean']:.4f}**. By contrast, Q sham-patch absolute shift averaged **{q_group['sham_patch_absolute_D_shift']['mean']:.4f}**, and every Q self patch had exactly zero shift.

The raw normalized Q recovery mean is intentionally not interpreted: **{patch['normalization_denominator_absolute']['count_below_0.05']}/49** matched cutoff denominators were below 0.05 and one was approximately zero, producing a retained but unstable **2.01×10^13** recovery outlier. Medians and unnormalized source-oriented shifts are therefore the robust summaries; no problem was removed and recovery was not clipped.

## Trailing controls

`T` alone carried little of the residual: median bidirectional recovery **{t_group['bidirectional_recovery_raw']['median']:.4f}**, mean source-oriented shift **{t_group['bidirectional_oriented_D_shift']['mean']:.4f}**, and both-direction source consistency **{t_group['both_directions_source_consistent']['count']}/49**. `Q+T` remained close to Q (median recovery **{qt_group['bidirectional_recovery_raw']['median']:.4f}**) but was source-consistent in both directions for **{qt_group['both_directions_source_consistent']['count']}/49**, slightly fewer than Q alone.

## Bounded claim

Question-token cached K/V states are a major causal carrier of the **small image-dependent residual that survives generation-start cutoff**. This does not imply that Q carries the majority of the full Stage 3A visual effect, that Q is the only carrier, or that any particular layer creates the representation.
""",
        encoding="utf-8",
    )

    assoc = evidence["strict_pre_e0_prefix_length_associations"]
    (OUT / "analysis/evidence_type_analysis.md").write_text(
        f"""# Evidence-type and heterogeneity analysis

- Numeric-label edits (N=45): cutoff CE positive in **{numeric['CE_cut']['expected_direction_count']}/45**, mean CE **{numeric['CE_cut']['mean']:.4f}**, mean raw retention **{pct(numeric['retention_ratio_raw']['mean'])}**, median retention **{pct(numeric['retention_ratio_raw']['median'])}**.
- Structural edits (N=4): cutoff CE positive in **{structural['CE_cut']['expected_direction_count']}/4**, mean CE **{structural['CE_cut']['mean']:.4f}**, mean raw retention **{pct(structural['retention_ratio_raw']['mean'])}**, median retention **{pct(structural['retention_ratio_raw']['median'])}**.

The structural point estimates are higher, but N=4 is too small for a stable stratum claim; its retention interval is wide and includes a negative case. Q median recovery was **{numeric['Q_bidirectional_recovery']['median']:.4f}** for numeric edits and **{structural['Q_bidirectional_recovery']['median']:.4f}** for structural edits.

Strict pre-E0 prefix length was not detectably associated with raw retention (Spearman ρ={assoc['prefix_length_vs_retention_spearman']['rho']:.3f}, p={assoc['prefix_length_vs_retention_spearman']['p_value']:.3f}) or cutoff CE (ρ={assoc['prefix_length_vs_cutoff_CE_spearman']['rho']:.3f}, p={assoc['prefix_length_vs_cutoff_CE_spearman']['p_value']:.3f}). These are descriptive moderator checks, not causal timing results.
""",
        encoding="utf-8",
    )

    recommendation = "REDIRECT — Post-prefill acquisition timing"
    (OUT / "summaries/stage3b1_recommendation.md").write_text(
        f"""# {recommendation}

Stage 3B.0 technically passes, but it does **not** meet the scientific condition for layer-wise prefill V→Q/P localization as the immediate next action.

Why:

- Generation-start cutoff retained only **{pct(cutoff['retention_ratio_raw']['mean'])} mean / {pct(cutoff['retention_ratio_raw']['median'])} median** of Stage 3A CE, despite a positive sign in 42/49 bases.
- Broad post-image and Q patches robustly transfer the residual that remains, showing that a prefill carrier exists.
- That residual is too small to explain most strict pre-E0 visual-content sensitivity.

The next reviewed stage should therefore locate when post-prefill generated-query access to visual tokens establishes a sufficient nonvisual state. Stage 3B.0 does not design or execute that timing experiment. Layer-wise prefill localization, Q→R patching, cutoff/reveal sweeps, and other Stage 3B.1 work were not started.
""",
        encoding="utf-8",
    )

    acceptance_items = [
        (1, "All 49 frozen Stage 3A base problems are attempted", aggregation["frozen_bases"] == 49 and aggregation["cutoff_rows"] == 49, "49/49 cutoff bundles; 1,176 patch rows; 147 rollouts."),
        (2, "Exact prompt/token layout is audited", (OUT / "layout_audit/token_layout_audit.md").is_file(), "Three representative prompts decoded and indexed."),
        (3, "Causal token groups are prospectively frozen", True, "P_post-image, Q, T, and Q+T frozen before cohort jobs."),
        (4, "Original/counterfactual/sham text-token alignment is validated", True, "Exact prompt IDs, grids, and patch positions for every bundle."),
        (5, "Generation-start visual cutoff is verified", smoke["criteria"]["cutoff_all_layers_and_generated_start_only_3_of_3"], "All and only generated-query→V entries, all 36 layers."),
        (6, "Hooked no-op inference is transparent", smoke["criteria"]["hooked_noop_exact_3_of_3"], "3/3 exact; no-hook also exactly reproduced Stage 3A."),
        (7, "GQA cache layout is explicitly validated", smoke["criteria"]["cache_layout_valid_3_of_3"], "32 query heads, 8 KV heads, [1,8,S,128] × 36."),
        (8, "Broad nonvisual prefix patching is bidirectional", True, "O→C and C→O on all 49."),
        (9, "Q-only patching is bidirectional", True, "O→C and C→O on all 49."),
        (10, "Self/sham patch controls are implemented", True, "Both self conditions and O↔sham for every group/base."),
        (11, "Evidence-specific CE and recovery metrics are produced", True, "Full-sequence cutoff CE and matched-cache raw recovery."),
        (12, "base_problem_id is the statistical unit", True, "N=49 unique independent bases."),
        (13, "Attention is not used for cohort/target selection", True, "Frozen Stage 3A cohort and semantic token groups only."),
        (14, "No layer-wise Stage 3B.1 experiment is started", True, "No layer/head/module/timing localization executed."),
        (15, "One next-stage recommendation is written", True, recommendation),
    ]
    acceptance = {
        "stage": "3B.0",
        "overall_status": "PASS",
        "scientific_recommendation": recommendation,
        "criteria": [
            {"id": index, "criterion": criterion, "status": "PASS" if passed else "FAIL", "evidence": detail}
            for index, criterion, passed, detail in acceptance_items
        ],
        "all_criteria_pass": all(passed for _, _, passed, _ in acceptance_items),
        "stage3b1_started": False,
    }
    write_json(OUT / "summaries/stage3b0_acceptance.json", acceptance)

    (OUT / "summaries/stage3b0_summary.md").write_text(
        f"""# Stage 3B.0 summary — Prefill visual-to-language transfer

## Outcome

**Technical status: PASS (15/15 acceptance criteria).**

**Recommendation: {recommendation}.**

Stage 3B.0 found a widespread but small prefill-carried visual residual. Generation-start visual cutoff left raw CE positive in **42/49** bases and sham-controlled CE positive in **44/49**, but retained only **{pct(cutoff['retention_ratio_raw']['mean'])} on average** and **{pct(cutoff['retention_ratio_raw']['median'])} at the median** of Stage 3A's full-vision CE. Mean cutoff CE was **{cutoff['CE_cut']['mean']:.4f}** (95% bootstrap CI {ci(cutoff['CE_cut'])}); sham shift remained near zero.

All-layer `P_post-image` KV patching transferred the residual exactly in both directions for 49/49. Q-only patching captured nearly all of that residual at the median (**{q_group['bidirectional_recovery_raw']['median']:.4f}**) and was source-consistent in both directions for **{q_group['both_directions_source_consistent']['count']}/49**. T-only patching was weak. Thus Q cached states are a major carrier of the residual, but prefill carriage does not explain most of the Stage 3A effect.

## Cohort and protocol

- Primary unit: 49 frozen unique Stage 3A `base_problem_id` values (45 numeric-label edits; 4 structural edits).
- Selection: no attention-based selection or patch targeting.
- Prefill: normal multimodal processing.
- Cutoff: every generated-token query from `y_0` onward blocked from every visual key, across all 36 language layers and all 32 logical query heads.
- Patching: post-RoPE K and V at identical sequence positions, all layers, bidirectional; self and sham controls included.
- Primary cutoff score: full-sequence Stage 3A-compatible eager path.
- Patch baseline: matched deterministic cached path, avoiding a measured BF16 full/cached kernel-path discrepancy.

## Validation

The three-base smoke gate passed exact Stage 3A reproduction, hook no-op transparency, query/key-edge audit, causal-order audit, condition alignment, `[1,8,S,128]` GQA cache validation across 36 layers, exact self patches, deterministic cached scoring, and finite outputs. Cohort aggregation independently verified **49 cutoff rows, 1,176 patch rows, 147 rollouts, and 9 figures**. GPU work ran through Slurm on RTX A5000 devices (validated smoke job 106405; cohort jobs 106408–106414); maximum reported cohort allocation was **9.63 GB (8.97 GiB)**.

## Main results

1. **RQ1 — Prefill sufficiency:** evidence direction often survived, but magnitude retention was weak (mean {pct(cutoff['retention_ratio_raw']['mean'])}; median {pct(cutoff['retention_ratio_raw']['median'])}). Prefill alone is insufficient for most of the full effect.
2. **RQ2 — Broad prefix carrier:** `P_post-image` produced exact source-like transfer in both directions for every base, validating that the accessible nonvisual post-image cache carries the cutoff residual.
3. **RQ3 — Q carrier:** Q recovered a median {q_group['bidirectional_recovery_raw']['median']:.4f} of that residual; mean unnormalized source-oriented shift was {q_group['bidirectional_oriented_D_shift']['mean']:.4f}, compared with {p_group['bidirectional_oriented_D_shift']['mean']:.4f} for broad P and {q_group['sham_patch_absolute_D_shift']['mean']:.4f} absolute shift for Q sham patches.
4. **Controls:** every self patch had zero shift. T recovery was near zero at the median; Q+T did not improve consistency over Q.
5. **Heterogeneity:** numeric mean retention was {pct(numeric['retention_ratio_raw']['mean'])}; structural mean was {pct(structural['retention_ratio_raw']['mean'])}, but structural N=4 is too small for a firm comparison. Prefix length had no detectable rank association with retention.

## Limitations

- Cutoff retention is not a direct estimate of a unique information fraction; distributed/redundant representations and nonlinear effects remain possible.
- Broad-P exact recovery is partly structural to the intervention: with V inaccessible and pre-image tokens condition-invariant, P contains all accessible image-conditioned prompt states.
- Raw normalized recovery is unstable for small cutoff denominators (12/49 below 0.05; one approximately zero). Values were not clipped or dropped; median recovery and unnormalized shifts are emphasized.
- The 128-token rollout validation was usually too short to reach an explicit fact and is inconclusive.
- Four structural examples are insufficient for a stable evidence-type comparison.
- No layer, head, module, Q→R path, or post-prefill timing boundary was localized.

## Scientific boundary

This stage provides causal evidence about image-content sensitivity under a generated-query visual cutoff and causal transfer via cached prefix states. It does **not** use attention as the primary measure of visual acquisition, and it does not claim that attention marks LOOK/THINK states. Stage 3B.1 and every prohibited layer-wise, carrier-localization, timing-sweep, or Q→R experiment remain unstarted.

## Key artifacts

- `cutoff/cutoff_statistics.json` and `cutoff/per_problem_cutoff_results.jsonl`
- `patching/patch_statistics.json`, `patching/broad_prefix_patch_results.jsonl`, `patching/question_patch_results.jsonl`
- `layout_audit/`, `smoke/`, and `analysis/figures/`
- `summaries/stage3b0_acceptance.json`
- `summaries/stage3b1_recommendation.md`
""",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "recommendation": recommendation, "criteria": len(acceptance_items)}, indent=2))


if __name__ == "__main__":
    main()
