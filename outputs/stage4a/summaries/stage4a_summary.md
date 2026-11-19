# Stage4A — Multi-evidence selection, switch and refresh

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

| Contrast | N | Median | Mean | Mean bootstrap95% CI | Positive | Paired p | Holm p | Robust |
|---|---:|---:|---:|---|---:|---:|---:|---|
| S_A1 | 48 | 2.30045 | 2.97983 | [2.27965, 3.80308] | 47/48 | 2.397e-09 | 1.677e-08 | yes |
| S_B | 48 | 0.656265 | 1.66246 | [1.07686, 2.37045] | 47/48 | 2.396e-09 | 1.677e-08 | yes |
| S_A2 | 48 | 0.411214 | 0.629966 | [0.409631, 0.894446] | 43/48 | 1.836e-08 | 7.344e-08 | yes |
| Switch_AB | 48 | 3.22626 | 4.64229 | [3.54516, 5.94666] | 48/48 | 7.105e-15 | 6.4e-14 | yes |
| Refresh_BA | 48 | 1.22479 | 2.29242 | [1.62459, 3.05444] | 47/48 | 2.396e-09 | 1.677e-08 | yes |
| demanded_minus_irrelevant | 40 | 1.17207 | 1.67111 | [1.24514, 2.18901] | 40/40 | 1.819e-12 | 1.455e-11 | yes |
| TS_A1 | 48 | 0.278439 | 0.355387 | [0.125505, 0.590698] | 35/48 | 0.001198 | 0.003593 | no |
| TS_B | 48 | 0.078125 | 0.251926 | [0.0456736, 0.487909] | 29/48 | 0.01196 | 0.02392 | no |
| TS_A2 | 48 | -2.98021e-07 | 0.00787346 | [-0.0829859, 0.115823] | 22/48 | 0.4652 | 0.4652 | no |

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

| Contrast | N | Median | Mean | Mean bootstrap95% CI | Positive | Paired p | Holm p | Robust |
|---|---:|---:|---:|---|---:|---:|---:|---|
| A1_demanded_effect | 24 | 19.3975 | 19.3882 | [16.8589, 22.0089] | 24/24 | 1.192e-07 | 1.073e-06 | yes |
| A1_semantic_selectivity | 24 | 19.3647 | 19.3683 | [16.7974, 22.0392] | 24/24 | 1.192e-07 | 1.073e-06 | yes |
| A1_semantic_minus_sham | 24 | 19.2499 | 19.0727 | [16.6213, 21.5786] | 24/24 | 1.192e-07 | 1.073e-06 | yes |
| B_demanded_effect | 24 | 13.262 | 13.854 | [11.8705, 15.8932] | 24/24 | 1.192e-07 | 1.073e-06 | yes |
| B_semantic_selectivity | 24 | 12.5625 | 13.789 | [11.7351, 15.8838] | 24/24 | 1.192e-07 | 1.073e-06 | yes |
| B_semantic_minus_sham | 24 | 13.0761 | 13.6032 | [11.6437, 15.6082] | 24/24 | 1.192e-07 | 1.073e-06 | yes |
| A2_demanded_effect | 24 | 9.30469 | 10.1131 | [8.34842, 11.9583] | 24/24 | 1.192e-07 | 1.073e-06 | yes |
| A2_semantic_selectivity | 24 | 8.59375 | 9.53618 | [7.77405, 11.404] | 24/24 | 1.192e-07 | 1.073e-06 | yes |
| A2_semantic_minus_sham | 24 | 9.11719 | 9.95092 | [8.21698, 11.7881] | 24/24 | 1.192e-07 | 1.073e-06 | yes |

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
- Final artifact audit:21/21, covering864 files,
  2448 arms,182208 source-layer-query calls and943 frozen hashes. Independent
  algebra/statistical reconstruction agrees with both reported test families.
- 11 focused tests pass, including the exact-tie regression. All16 required
  figures are saved as PNG and PDF; [figure gallery](../analysis/figures/README.md).
- Runtime code was unchanged across validation and all three scoring phases.
  Score path: BF16 A6000,36 layers,32 Q heads,8 KV heads,128 head dimension.
- Only tmux9 / Slurm108548 / node07 four RTX A6000 GPUs were used. No new
  allocation, dependency installation or global environment change occurred.
  Maximum saved peak: 11.63GiB allocated /
  13.23GiB reserved. Summed event work is
  749.3s across parallel ranks; this is not wall time
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

**HOLD — Review Stage4B mechanism-guided failure-rescue feasibility.** Only two small stale-B cases exist; their suitability for a
bounded pilot requires review. The full rationale and strongest objection are
in the [sole recommendation](next_stage_recommendation.md).

Stage4A is complete and stopped. No Stage4B rescue, later attention/failure
taxonomy, sink intervention or failure-mechanism deep dive has started.
