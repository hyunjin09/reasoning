# Stage8B Block3A — complete at the finite-cohort yield stop

Completed 2026-09-19T16:14:47.759947+00:00. The approved execution is complete; its scientific confirmation criterion is **not met**.

All **128/128** frozen trajectories were generated and semantically reviewed. The sealed same-item cohort contains **4 disjoint L+/L− pairs from 3 items / 3 independent visual families**, below the frozen minimum **20 pairs / 16 families**. The yield gate fails. New-rollout source-routing replication, weakening, rescue and selectivity assays were **not run**. No routing effect was estimated, and no causal-intervention null was observed.

## Scope and verified execution

The question was whether reduced target-vs-confuser routing reproducibly separates successful and failed reads of the same exact visual subgoal, and, conditional on confirmation, causally controls read quality. The hypothesis remains untested causally in this stage.

The frozen sample contains 32 MathVision items / 31 independent visual families and four new seeds (1235–1238). Items1707/1245 share a rescaled drawing; their original IDs, labels and source geometry remain unchanged. Original seed1234 remains discovery evidence and was not inserted into primary pairs. Selection included all11 original source-localizable failure families plus21 low-margin controls before new outcomes. This enriched sample does not estimate population failure prevalence.

Canonical Qwen3-VL-2B-Thinking BF16, temperature1.0, top-p0.95, top-k20, repetition1.0, presence0, frozen preprocessing and 40960-token cap were preserved. Native results comprise14 preserved completions plus114 resumed completions, **1,511,000 generated tokens**,126 normal EOS and2 capped trajectories (`756_s1236`, `510_s1238`). Both caps and four interrupted old attempts remain preserved. All128 receipts,640 native artifact hashes and token/passive-array alignments passed the completion audit. Original and resumed worker layout checks passed exact parity. Terminal accounting for118116 expired; saved batch completion, worker receipts and artifact integrity establish completion.

## Sealed semantic and retrieval yield

| First exact-subgoal judgment | All trajectories | Eligible active-retrieval reads |
|---|---:|---:|
| L+ | 79 | 62 |
| L− | 28 | 20 |
| L? | 1 | 0 |
| No matched committed/source-resolved claim | 20 | 0 |
| Total | 128 | 82 |

The20 eligible L− reads span9 items /9 families. There are25 resolved claims outside the frozen episode-association window (17 L+,8 L−),1 unresolved exact read, and20 unmatched claims. Unmatched reasons:8 no-committed-exact-subgoal,6 ambiguous source positions,3 same-subgoal-not-committed,3 same-subgoal-not-identified. Categories preserve their original review codes in the seal.

Reviews use the first committed claim addressing the frozen subgoal, not final-answer correctness or a later error. Hypothetical geometry, unanswered questions, unbound values and different visual properties cannot create a pair. Readout spans are aligned to native tokens and associated using the unchanged gap4 detector window [episode start−16, episode end+128]. A single main agent reviewed images, prefixes and targeted subgoal contexts; per-record coverage and rationale are recorded. These are single-annotator judgments with no inter-rater agreement estimate. Ambiguous commitment/source boundaries remain a limitation. New source-routing values remained unopened throughout review and after the yield stop.

| Item | Frozen category | L+ seed | L− seed |
|---|---|---:|---:|
| 398 | geometry | 1236 | 1235 |
| 67 | binding | 1237 | 1236 |
| 756 | geometry | 1235 | 1236 |
| 756 | geometry | 1237 | 1238 |

One pair includes the early valid local read in capped trajectory756_s1236; no final answer is required for this local subgoal. As attrition accounting only, ignoring retrieval eligibility would yield5 disjoint pairs across4 items (the additional item is1128), still far below the minimum. That accounting does not relax the primary gate. No original-new pairing, new seed, changed anchor, or ROI retuning was used to increase yield.

The immediate confirmed bottleneck is **insufficient within-item outcome variation under exact semantic and active-retrieval matching**, rather than the complete absence of failures. Many source-resolved items remain locally correct or locally wrong across seeds. The deeper reason for the low switching yield is unknown. This result does not distinguish routing from extraction/content errors, falsify the Block2 association, or establish that natural benchmarks never yield such pairs.

## Preserved pre-outcome native routing taxonomy

All117 original Block2 source-localizable records are retained verbatim. Routing inventory uses21 existing plus79 exact supplemental captures;17 records lack a usable capture (13 L+,4 L?). Those17 records and2 measured but unresolved routing cases constitute R4. The operational low-margin boundary remains QK T−X≤1.0 nat for target-top cases, with the frozen native observational window (layers19–22/all16 heads). This does not verify every head as causal.

| Native subtype | L+ | L− | L? |
|---|---:|---:|---:|
| R1 | 21 | 7 | 0 |
| R2 | 6 | 2 | 0 |
| R3 | 0 | 3 | 0 |
| R4 | 15 | 0 | 4 |
| SELECTIVE_LPLUS | 59 | 0 | 0 |

R1 and R2 among L+ are control strata, not unfaithfulness diagnoses. R3 is an extraction/content candidate, not a causal diagnosis. These subtype counts describe the original inventory and are not new-rollout routing measurements. Block2 activation confidence intervals including zero do not establish equivalence.

## Gate disposition and resources

Yield: **FAIL**. Routing replication: **not evaluated**. C1 weakening, C2 rescue, C3 selectivity: **not run**. Required JSON artifacts use null effect estimates and explicit status, rather than fabricated zeros. The five figures include the actual original subtype map plus explicit unperformed panels for unavailable paired/causal analyses.

Approximate allocated compute:0.405 GPU-hours for supplemental replay;1.688 for the cancelled two-GPU native allocation (including technical checks and partial attempts);13.468 for the four-GPU continuation. **Total≈15.561 GPU-hours**. Single-agent annotation burden:128 trajectory reviews with32 source images; human labor hours were not measured. CPU reporting/review required no allocation. All stage GPUs are released, and remaining authorized GPU work is zero. No download or environment installation was needed.

## Exactly one recommendation

**Stop routing branch under the current frozen cohort.** Preserve Block2's descriptive routing evidence and this negative feasibility result. This stage does not support promoting routing to a causal mechanism or anchoring an intervention story on it. No next experiment, larger sample, model change, intervention controller, or Block3B was launched.

## Evidence and deliverables

- [Semantic seal](annotations/semantic_seal.json), [yield gate](audit/yield_gate.json), [item-level yield](audit/review_yield_by_item.json).
- [Same-item pairs](stage8b_block3a_same_item_pairs.parquet), [routing replication status](stage8b_block3a_routing_replication.json).
- [Original native taxonomy](stage8b_block3a_routing_subtypes.json), [intervention manifest](stage8b_block3a_intervention_manifest.json).
- [Weakening](stage8b_block3a_weakening_results.json), [rescue](stage8b_block3a_rescue_results.json), [selectivity](stage8b_block3a_selectivity_controls.json).
- Figures: [paired routing](figures/figure1_same_item_routing.png), [subtypes](figures/figure2_routing_subtypes.png), [weakening](figures/figure3_weakening.png), [rescue](figures/figure4_rescue.png), [controls](figures/figure5_selectivity_controls.png); PDF exports accompany each.
- [Native integrity audit](audit/resume_four_v1/completion_audit.json), [final resource accounting](audit/resource_accounting_final.json), [acceptance](audit/final_acceptance.json), [freeze](stage8b_block3a_freeze.json).

Historical manifests and original protocol/resource estimates remain unchanged. Earlier state entries describing1/128 review or running jobs are superseded by this final checkpoint. STOP.
