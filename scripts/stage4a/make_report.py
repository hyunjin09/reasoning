"""Write the final Stage4A report and the plan's20 technical acceptance criteria."""
from scripts.stage4a.prepare_config import ROOT, OUT, read_json, read_jsonl, write_json


def table(stats):
    lines=['| Contrast | N | Median | Mean | Mean bootstrap95% CI | Positive | Paired p | Holm p | Robust |',
           '|---|---:|---:|---:|---|---:|---:|---:|---|']
    for key,s in stats.items():
        lo,hi=s['bootstrap_mean_ci95']
        lines.append(f'| {key} | {s["N_unique_bases"]} | {s["median"]:.6g} | {s["mean"]:.6g} | [{lo:.6g}, {hi:.6g}] | {s["positive_count"]}/{s["N_unique_bases"]} | {s["wilcoxon_p"]:.4g} | {s["holm_p"]:.4g} | {"yes" if s["robust_positive"] else "no"} |')
    return '\n'.join(lines)


def main():
    (OUT/'summaries').mkdir(parents=True,exist_ok=True)
    audit=read_json(OUT/'audit/final_artifact_validation.json')
    assert audit['passed'] and audit['checks']['strict_stale_dominance_and_ties_distinguished']
    native=read_json(OUT/'analysis/selection_switch_refresh.json')
    semantic=read_json(OUT/'phase_d_counterfactual_refresh/counterfactual_refresh_statistics.json')
    trigger=read_json(OUT/'phase_c_trigger/trigger_statistics.json')
    claims=read_json(OUT/'analysis/paper_claim_assessment.json')
    resources=read_json(OUT/'audit/resource_summary.json')
    cohort=read_json(OUT/'cohort/cohort_freeze_complete.json')
    mechanics=read_json(OUT/'audit/mechanical_validation.json')
    figure_index=read_json(OUT/'analysis/figures/figure_index.json')
    next_step='HOLD — Review Stage4B mechanism-guided failure-rescue feasibility'
    recommendation='''# Stage4A next-stage recommendation

**HOLD — Review Stage4B mechanism-guided failure-rescue feasibility.**

This is the sole next-step recommendation, for user review only. No follow-on
experiment is authorized or running.

The 48-base native assay supports demand-aligned switching and visual re-engagement:
36 bases meet the complete W2 dynamic definition. Two bases,229 and345, have a
strict stale-B signature at A2; this gives a concrete, small candidate set for a
mechanism-guided rescue feasibility review.

The strongest objection is yield and effect size: only2/48 are stale-B cases,
with A2 selectivity −0.0625 and −0.058534 nats/candidate token. One has weak
demanded-A dependence. Base227 is tied at B, not an A-dominant failure. These
observations do not yet establish an adequately sized rescue cohort or explain
the failure mechanism. R16 trigger retargeting also fails the frozen robust
criterion at every event, so the Stage3C.10 trigger cannot be assumed to be the
right rescue lever.

Review the two saved causal profiles and the scope of a possible bounded pilot
before deciding whether Stage4B is justified. Hold execution and cohort expansion
pending that review. The broader-window and joint-state alternatives are not the
recommended next action because the native W2/W8 result already shows robust
crossover, with little median gain from joint suppression.

Evidence: [summary](stage4a_summary.md),
[native phenotypes](../analysis/native_failure_phenotypes.json),
[primary and sensitivity statistics](../analysis/selection_switch_refresh.json),
[trigger statistics](../phase_c_trigger/trigger_statistics.json).
'''
    (OUT/'summaries/next_stage_recommendation.md').write_text(recommendation)
    c=audit['checks']
    names=[
        ('cohort_rules_frozen_before_scoring',c['all_frozen_inputs_and_raw_hashes_unchanged'],'cohort/cohort_freeze_complete.json'),
        ('at_least36_valid_primary_bases',len(cohort['primary_bases'])>=36,'cohort/primary_manifest.jsonl'),
        ('two_validated_nonoverlapping_rois',c['roi_maps_disjoint_and_exact'],'annotations/roi_a_b.jsonl'),
        ('frozen_semantic_A1_B_A2_events',c['all_event_partitions_and_histories_exact'],'annotations/event_a1_b_a2.jsonl'),
        ('no_attention_or_effect_event_selection',c['selection_blind'],'cohort/prefix_review_ledger.jsonl'),
        ('readouts_frozen_before_scoring',c['all_scores_finite_and_readouts_exact'],'annotations/local_readouts.jsonl'),
        ('canonical_A6000_path_all_conditions',c['all16_rank_environments_canonical'] and c['validated_runtime_code_unchanged'],'audit/final_artifact_validation.json'),
        ('A_B_suppression_isolated',mechanics['checks']['roi_A_isolated'] and mechanics['checks']['roi_B_isolated'],'audit/mechanical_validation.json'),
        ('W2_primary_W8_predeclared',c['all_frozen_inputs_and_raw_hashes_unchanged'],'config/source_windows.json'),
        ('A_B_at_all_three_events',c['complete864_event_images_no_duplicates'],'phase_b_source_switch/dynamic_selectivity.json'),
        ('claims_use_causal_dependence',c['nine_primary_tests_independently_recomputed'],'analysis/paper_claim_assessment.json'),
        ('joint_secondary_explicit_union',mechanics['checks']['joint_union_exact'],'phase_b_source_switch/joint_ab.jsonl'),
        ('trigger_runs_only_under_gate',c['phase_c_gate_open_before_trigger'],'phase_b_source_switch/primary_freeze.json'),
        ('trigger_frozen_layers16_23',trigger['layers']==list(range(16,24)),'phase_c_trigger/trigger_statistics.json'),
        ('independent_semantic_edits',c['independent_image_assets_and_layout'],'counterfactuals/edit_validation.json'),
        ('fixed_history_challenge_secondary',semantic['fixed_history_exact'] and semantic['OO_primary_exact'],'phase_d_counterfactual_refresh/counterfactual_refresh_statistics.json'),
        ('passive_telemetry_no_reselection',c['selection_blind'] and c['all_frozen_inputs_and_raw_hashes_unchanged'],'telemetry/attention_qk_alphav.jsonl'),
        ('no_corrective_Stage4B_run',c['all_source_calls_coordinates_and_isolation'],'audit/final_artifact_validation.json'),
        ('no_post_Stage4_experiment',set(p.name for p in (OUT/'raw').iterdir())=={'validation_01','primary_01','trigger_01','semantic_01'},'audit/resource_summary.json'),
        ('exactly_one_next_recommendation',recommendation.count('**HOLD —')==1,'summaries/next_stage_recommendation.md')]
    acceptance={'passed':all(bool(v) for _,v,_ in names),'criteria_count':20,
        'criteria':[{'number':i,'criterion':name,'passed':bool(value),'evidence':'outputs/stage4a/'+path} for i,(name,value,path) in enumerate(names,1)],
        'mechanical_checks':15,'artifact_checks':audit['check_count'],'tests_passed':11,'figures':len(figure_index['figures']),
        'scientific_outcome':'O1/O2 supported in the frozen local assay; O3 not established; semantic challenge positive',
        'next_step':next_step,'follow_on_executed':False}
    write_json(OUT/'summaries/stage4a_acceptance.json',acceptance)
    assert acceptance['passed']
    report=f'''# Stage4A — Multi-evidence selection, switch and refresh

Completed 2026-09-06. **Technical PASS 20/20. O1/O2 supported; O3 not established.**

Visual-source dependence follows A→B→A demand in this frozen local numeric-fact
assay. All three primary source-selectivity tests and both switch/refresh tests
pass the complete prespecified robustness rule.36/48 bases satisfy the full W2
dynamic definition; W8 sensitivity gives30/48. This establishes demand-aligned
causal dependence and later re-engagement of A within the tested trajectory and
intervention scope. It does not establish the full recent-reasoning-trigger or
Q-mediated chain.

The secondary fixed-history semantic challenge is positive at all three events:
the demanded edit exceeds both the other-source edit and the absolute sham effect
on24/24 bases. At A2, median factorial A effect is9.30469 nats/candidate token;
median A-minus-B effect is8.59375 and A-minus-absolute-sham is9.11719. The image is
used throughout each fixed-history replay; this does not time-localize new-image
acquisition to A2 or simulate a natural free rollout.

## Cohort and provenance

- Main model: Qwen3-VL-4B-Thinking; MathVerse; independent base ID is the unit.
- The first238 screen entries were fully resolved, retaining8 validation and48
  primary bases. Prefix exclusions:123 independent-edit construction,40 semantic
  pair,15 fewer-than-two-fact,3 duplicate-stimulus,1 prior-stimulus overlap.
- Across bounded construction review,90 provisional annotations yielded74
  asset-valid cases; only the first56 eligible prefix cases were retained. The
  extra eligible cases do not replace members. No attention, causal score or final
  correctness filter selected the cohort, events, readouts, ROIs or PhaseD subset.
- Acquisition retained374 exactly matching A6000 native outcomes and243 new
  outcomes. This reuses native generation only; all Stage4A causal scores are new.
  All observed raw outcomes are preserved. Work beyond the selected prefix is
  accounted for but cannot change membership. Planned unneeded trajectories were
  intentionally not generated after cohort freeze.
- Primary final correctness:36 correct /12 wrong. Dynamic W2:27/36 correct and
  9/12 wrong, both75%, descriptively. Local selected physical fact references were
  reviewed as correct; global reasoning can still be wrong or tentative.
- PhaseD is the frozen first24 primary bases. The frozen irrelevant-control subset
  is40 bases. Earlier phase-memory prose said47; seven reviewed controls lacked
  the aggregate validation flag at freeze, and227 failed its B control. The
  frozen manifest and actual scoring agree at40; no post-effect expansion occurred.

Evidence: [screening accounting](../cohort/screening_accounting.json),
[freeze](../cohort/cohort_freeze_complete.json),
[generation reconciliation](../cohort/generation_completion.json),
[control reconciliation](../audit/irrelevant_subset_reconciliation.json).

## Primary causal evidence

D is mean log probability of the original numeric candidate minus that of its
counterfactual. VSD is native D minus source-suppressed D. W2 removes the selected
ROI contribution in the last two queries, all36 layers/all32 heads, without
attention renormalization. W8 is frozen sensitivity. All arms use independent
event roots and identical maximum2048-token prefix chunks followed by eight
single-query barriers. Joint A+B is one explicit union reduction, not a sum of
separately scored effects.

Inference: paired two-sided Wilcoxon,10000 base-bootstrap resamples,seed12348,
nine-test Holm. Robust means positive median, positive mean-CI lower bound,
at least75% positive bases and corrected p<.05. Trigger slots were p=1 when the
gate was evaluated; final results below include all nine tests. Units throughout:
nats per candidate token.

{table(native['primary_family'])}

W2 median A/B VSD at A1 is2.03125/0; at B −0.0625/0.686449;
at A2 0.375/−0.020132. W8 demanded medians are2.30540,0.816068,0.358459.
W8 does not replace the W2 primary classification. Joint-minus-demanded median
effects are0.006285,−0.017693 and approximately0 across A1/B/A2. These secondary
results do not support persistent joint availability *without* crossover, nor
do they quantify unique information fractions.

Evidence: [source statistics](../analysis/selection_switch_refresh.json),
[continuous base scores](../phase_b_source_switch/dynamic_selectivity.json),
[joint effects](../phase_b_source_switch/joint_ab.jsonl).

## Trigger continuity

Both primary switch contrasts opened the PhaseC gate. R16 intervention used only
the current query, layers16–23 and all32 heads; both source-necessity contrasts
were crossed with that intervention. All144 native denominators exactly replay
the frozen primary result, including current-logit hashes and candidate scores.

TS_A1 and TS_B have corrected p<.05 and positive mean CIs, but only35/48 and29/48
positive bases, below the75% rule. TS_A2 is near zero,22/48 positive, with a CI
crossing zero. **No TS event passes the full robust criterion; O3 is not
established.** This mixed result does not invalidate the native source crossover
or diagnose why the single-source trigger generalization is weak. No trigger
window, layer or rescue search was added.

## Secondary semantic challenge

Six images OO/AO/OB/AB/A_sham/B_sham were scored at every event on24 frozen bases.
Every condition retains the exact native token history; all72 OO denominators
exactly replay primary scoring. A effect averages OO−AO and OB−AB; B averages
OO−OB and AO−AB. Semantic effects must exceed absolute same-pipeline sham effects.
The separate nine-test secondary family was recorded before primary-subset
semantic scoring; it does not alter the primary statistical family.

{table(semantic['secondary_nine_test_family'])}

At A2, the direct native-B CE_A2=OO−AO has median11.12724 and mean11.35732,
mean95% CI[9.44878,13.28554],positive24/24. The changed-B context OB−AB has
median8.36841,positive24/24. B-edit contexts are heterogeneous: OO−OB median1.40625
versus AO−AB median−0.375. The factorial mean must not hide that interaction.
Strong A2 image sensitivity despite fixed prior A text supports re-engaged
semantic control. Its acquisition time remains unlocalized by this replay assay.

Evidence: [all contrasts and contexts](../phase_d_counterfactual_refresh/counterfactual_refresh_statistics.json),
[secondary protocol](../phase_d_counterfactual_refresh/secondary_analysis_protocol.json).

## Native phenotypes and paper claims

The predeclared0.05 floor gives43 successful switches,36 successful refreshes and
36 full dynamic bases.36 bases have mixed A/B support at at least one event;
9 have at least one locally insensitive event. These labels overlap.

There are **zero strict A-dominant B-event failures**, one tied B event (227),
and **two strict stale-B A2 cases (229,345)**. Their A2 S values are−0.0625 and
−0.058534. A tie was initially mislabeled A-dominant by a non-strict inequality;
the initial artifact and correction are preserved. No primary statistic, raw
score, cohort member or dynamic count changed. These few cases do not establish
that failed refresh is common, and their causes remain unknown.

| Outcome | Assessment |
|---|---|
| O1 dynamic multi-evidence retrieval | Supported in the frozen local assay |
| O2 visual re-engagement | Supported by native necessity and secondary semantic control |
| O3 trigger retargeting | Not established under the frozen robustness rule |
| O4 persistent joint support without crossover | Not the dominant pattern |
| O5 sticky/failed refresh | Two descriptive stale-B cases; no cohort-level headline |
| O6 local assay insufficient | Not supported as the cohort-level conclusion |

Passive A/B attention density, QK cosine/scaled logits, alphaV and post-WO norms,
sink mass, entropy, R16 quantities, residual norms and correctness are saved for
both frozen selected heads and all32 heads at layers28/29. They did not change
selection or causal classes. No Q mediation or sink causality is claimed.

## Validation, implementation and limits

- Mechanical validation:15/15 on8 bases and144 event/image files, including exact
  no-op, deterministic replay, A/B isolation, union arithmetic and telemetry.
- Final artifact audit:{audit['check_count']}/{audit['check_count']}, covering864 files,
  2448 arms,182208 source-layer-query calls and943 frozen hashes. Independent
  algebra/statistical reconstruction agrees with both reported test families.
- 11 focused tests pass, including the exact-tie regression. All16 required
  figures are saved as PNG and PDF; [figure gallery](../analysis/figures/README.md).
- Runtime code was unchanged across validation and all three scoring phases.
  Score path: BF16 A6000,36 layers,32 Q heads,8 KV heads,128 head dimension.
- Only tmux9 / Slurm108548 / node07 four RTX A6000 GPUs were used. No new
  allocation, dependency installation or global environment change occurred.
  Maximum saved peak: {resources['max_allocated_GiB']:.2f}GiB allocated /
  {resources['max_reserved_GiB']:.2f}GiB reserved. Summed event work is
  {resources['summed_event_seconds']:.1f}s across parallel ranks; this is not wall time
  and excludes model loading and separately recorded generation.
- The reviewed cohort favors editable, separated numeric labels. Exclusions
  describe what bounded review did not establish, not exhaustive impossibility
  of every alternative fact pair. Sixteen annotated constructions were rejected;
  detached bounds were repaired only with component evidence; geometry-connected
  glyphs were excluded. Constant connected units use matched semantic/sham redraws.
- Local events include explicit or tentative fact identification. They do not
  always demonstrate a correct reasoning operation or globally correct solution.
  Fresh base IDs can still share geometry templates; population generalization
  and template dependence remain limitations.
- Numerical reproducibility is established within the canonical path. Absolute
  scores from different BF16 execution shapes must not be pooled.
- A first figure command started before its analysis file existed and failed
  before rendering; rerun after analysis completion succeeded. No scoring was
  affected. Legacy generation flags describing unfinished planned work and the
  erroneous47-control prose count are reconciled, not silently rewritten.
- The local research-control skill was absent. Execution followed the explicit
  plan and its gates; no new research action or strategic pivot was selected.

Evidence: [acceptance](stage4a_acceptance.json),
[mechanics](../audit/mechanical_validation.json),
[artifact audit](../audit/final_artifact_validation.json),
[resource record](../audit/resource_summary.json),
[tie correction](../audit/phenotype_tie_correction.json).

## Stop and next-step recommendation

**{next_step}.** Only two small stale-B cases exist; their suitability for a
bounded pilot requires review. The full rationale and strongest objection are
in the [sole recommendation](next_stage_recommendation.md).

Stage4A is complete and stopped. No Stage4B rescue, later attention/failure
taxonomy, sink intervention or failure-mechanism deep dive has started.
'''
    (OUT/'summaries/stage4a_summary.md').write_text(report)
    print({'technical_pass':acceptance['passed'],'criteria':20,'outcomes':'O1/O2; O3 not established','recommendation':next_step})


if __name__=='__main__':main()
