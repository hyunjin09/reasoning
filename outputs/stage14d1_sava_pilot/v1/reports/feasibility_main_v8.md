# Stage14D-1 SAVA — completed 72-family feasibility pilot

Completed 2026-10-22T12:35:54.497671+00:00. **All 72 families and 432 logical arm assignments are complete, represented by 345 distinct physical continuations. All GPU allocations are terminal.**

**The pilot does not demonstrate a final-answer accuracy benefit from the tested SAVA implementation.** The primary QI−N contrast is −4.17 percentage points (95% family-bootstrap CI −12.50 to +4.17), with three rescues and six regressions. This is an uncertain negative estimate, not proof that every form of subgoal-addressed acquisition is ineffective.

## Design and validity

The cohort is the original source-selected, previously audited R72 development set: 36 global-required, 18 local-sufficient and 18 local-plus-global source opportunities. Selection used source metadata and frozen hash matching, not answer outcomes. These labels describe the historical source opportunity, not necessarily the controller’s actual query. This is a feasibility pilot, not an independent confirmation or full-benchmark accuracy estimate.

Every arm starts from the same original image and frozen 512-token prefix, reconstructed with a fresh fixed family seed. The checkpoint is Qwen3-VL-4B-Thinking revision `1de27d8c51f12e819435303b9e84c4e25ba8401e`, BF16, vLLM 0.11.0, Torch 2.8.0, Transformers 4.57.1. Sampling: temperature 1.0, top-p .95, top-k 20, repetition penalty 1.0, presence penalty 0; unchanged continuation cap 81,920. Helpers use compact structured output and a 2,048-token cap. Original image preprocessing remains 602,112–4,014,080 pixels.

| Arm | Operation |
|---|---|
| N | Fresh native continuation from the shared image-conditioned prefix |
| G | Generic full-image lookback readout, then continuation |
| Q | Subgoal query and text-only extra READ helper; the solver still receives its original image |
| QI | Same query with full-image READ |
| QIA | Same query, predicted address, and full-image READ |
| QGL | Same query/address, original unmodified global image plus valid predicted crop, then continuation |

The solver always retains the original image. Local views are helper inputs, generated from model-predicted coordinates; no human ROI, E* value or gold answer enters runtime. The global image is unmarked. GLOBAL/UNRESOLVABLE and invalid-address cases use frozen fallbacks. Helper JSON/provenance validity, query relevance, localization correctness, readout correctness, and solver completion are separate measurements.

## Technical recovery and preservation

1. Initial long-form helper outputs failed to commit JSON. The compact helper interface was repaired prospectively while keeping the native solver recipe fixed. The earlier QUERY/NONE grammar had a prompt/schema field-order mismatch that biased the branch space; both branches now pass independent grammar witnesses and generation controls. The original eight NONE outputs are not scientific evidence.

2. Literal model-written quotations failed on LaTeX/Unicode serialization and unsupported citations. The final interface uses deterministic host-created question/prefix span IDs, exact spans and hashes; no fuzzy fabricated match is accepted. Numeric/color/assertion guards and adversarial tests remain. A cited prefix can still be wrong: provenance is not source truth. Native image identifiers and the missing shape property were repaired prospectively.

3. LOCATE now emits integer 0–1000 coordinates, converted once to normalized boxes. Mode-first schema branches enforce LOCAL=1, MULTI=2, GLOBAL=0 and UNRESOLVABLE=0 boxes. Degenerate addresses are rejected without clipping or fabricated crops. Decimal grammar exclusion was disproved; the coordinate convention was a compatibility repair, not a proven full diagnosis of every bad box.

4. Replay diagnostics found identical prompt/image/prefix inputs and, at case33’s token30 divergence, identical RNG states but differing logits under changing prefill schedules. Greedy also diverged in default batch8. Disabling prefix caching alone was insufficient; `VLLM_ENABLE_V1_MULTIPROCESSING=0` restored tested same-schedule reproducibility. The later full-cap admission repair changed batch shape: v7 repeated 8/8 exactly within schedule and across workers, but only 5/8 matched the former batch8 reference. These failures remain preserved.

5. Prospective v8 requires same-schedule exact 64-token repeats at original and independent technical seeds, original-seed agreement with frozen v7, and original prompt-token equality. Both workers passed; all 32 cross-node comparisons also matched exactly. This does not guarantee arbitrary batch-shape or full 81,920-token bitwise identity, or restore a historical advanced RNG state.

6. The old failed shard oversubscribed eventual KV capacity and stalled; repeated preemption is suspected, not directly counted. No OOM was recorded. Full-cap reservation now accounts for prompt/visual expansion and the entire 81,920-token allowance, admitting two concurrent requests safely. New jobs use 48-hour Slurm limits and no six-hour internal deadline.

All 36 complete original families retain their internally paired six arms. All 36 previously incomplete families use the recovered schedule for all arms. Two old completed item2924 receipts are preserved outside primary analysis; selection was based on incomplete-family coverage, not correctness. Thus 170 original + 175 recovered physical receipts form the primary 345. Historical failures, seeds, code/protocol versions and source records remain immutable.

Final v6 technical gates:8/8 replay,7/8 query contracts,6/7 LOCATE contracts,31/31 READ contracts and48/48 transport slots. Synthetic outputs:20/20 valid/terminating and18/20 expected branch choices; the Roman positive-control NONE decisions remain false negatives rather than being prompted away. CPU coverage includes provenance/adversarial tests, image-ID handling, coordinate and mode/cardinality constraints, fallbacks, receipt reuse, capacity admission, family-coherent merge and bootstrap tests. The final merge/family/statistics/reuse suite passed 28 tests. [Technical findings](resumption_v8_technical_findings.md) and [earlier diagnostic evidence](../../../stage14d1_sava_recovery/v1/reports/technical_recovery_final.md) provide exact records.

## Final-answer results

| Arm | Correct / assigned | Correct / scorable | Wrong | Unscorable | Cap hits | Rescue vs N | Regression vs N |
|---|---|---|---:|---:|---:|---:|---:|

| N | 39/72 (54.17%) | 39/72 (54.17%) | 33 | 0 | 0 | — | — |

| G | 41/72 (56.94%) | 41/72 (56.94%) | 31 | 0 | 0 | 5 | 3 |

| Q | 39/72 (54.17%) | 39/72 (54.17%) | 33 | 0 | 0 | 3 | 3 |

| QI | 36/72 (50.00%) | 36/72 (50.00%) | 36 | 0 | 0 | 3 | 6 |

| QIA | 37/72 (51.39%) | 37/71 (52.11%) | 34 | 1 | 1 | 3 | 5 |

| QGL | 36/72 (50.00%) | 36/72 (50.00%) | 36 | 0 | 0 | 2 | 5 |


There are no missing executions. QIA item1537 is the only unscorable final: it reached81,920 tokens without closing its thought section. It is not counted as wrong. QIA’s known-correct lower bound is37/72=51.39%; its missingness bounds are51.39–52.78%. All other arms have 72 scorable finals.

The inherited scorer initially left 48 logical slots (45 physical outputs) pending:37 physical outputs had extracted but noncanonical strings, seven needed explicit prose-final extraction, and one had no closed final. Gold-hidden response review transcribed 44 explicit finals, preserving original parser strings and raw outputs. Examples include `\text{A}`→A, explicit prose numerals, and an already written11/7 fraction accompanying 11:7. No answer was derived from unfinished reasoning and no equivalence policy changed. Original automatic scores are preserved; use the reviewed final files below.

| Contrast | Paired n | Difference (pp) | 95% family-bootstrap interval (pp) | Rescues / regressions |
|---|---:|---:|---|---|

| QI-N | 72 | -4.17 | [-12.50, +4.17] | 3 / 6 |

| QI-G | 72 | -6.94 | [-15.28, +1.39] | 2 / 7 |

| QI-Q | 72 | -4.17 | [-12.50, +4.17] | 3 / 6 |

| QGL-QI | 72 | +0.00 | [-4.17, +2.78] | 1 / 1 |

| QGL-QIA | 71 | -1.41 | [-7.25, +4.23] | 2 / 3 |

| G-N | 72 | +2.78 | [-4.17, +11.11] | 5 / 3 |

| Q-N | 72 | +0.00 | [-6.94, +6.94] | 3 / 3 |

| QIA-N | 71 | -2.82 | [-10.14, +4.29] | 3 / 5 |

| QGL-N | 72 | -4.17 | [-11.11, +2.78] | 2 / 5 |


The primary contrast is QI−N. Secondary contrasts are QI−G, QI−Q, QGL−QI and QGL−QIA; other arm−N contrasts are descriptive. Intervals use 4,000 paired family-cluster bootstrap draws, seed 20261019, frozen answer-format×structured strata, and equal family weighting. Secondary intervals are not multiplicity-adjusted. Aliases/windows/tokens are not independent samples.

The QI−N estimate is negative in both execution blocks: original 36 families−2.78pp (2 rescues/3 regressions), recovered 36−5.56pp (1/3). This is descriptive sensitivity, not a randomized comparison of schedules. Source-opportunity subgroup correct counts are:

| Historical source opportunity | Families | N | G | Q | QI | QIA | QGL |
|---|---:|---:|---:|---:|---:|---:|---:|

| global_required | 36 | 18 | 19 | 18 | 16 | 17 (+1 unscorable) | 16 |

| local_plus_global | 18 | 10 | 11 | 11 | 11 | 11 | 11 |

| local_sufficient | 18 | 11 | 11 | 10 | 9 | 9 | 9 |


These small, correlated source strata do not establish a causal global-context interaction.

## Acquisition results, separately from answer accuracy

All 72 query/address reviews were completed before opening scientific finals. The controller emitted 69 QUERY and 3 NONE records. The host accepted 62 QUERY plus all 3 NONE; seven queries were rejected. Only 22/62 accepted queries (22/72 assigned families) were judged fully task-relevant. Across all 72, relevance was 25 yes, 33 partial, 11 no and 3 not applicable. In 47/72 source reviews, the requested information was already supplied or tentatively mentioned; this includes unresolved conjectures and must not all be called redundant. Two value-preloading flags were both rejected by the host.

LOCATE was attempted 62 times; 60 addresses passed transport checks, producing 49 local-view families. Among those 49,14 regions were judged correct for the requested target,20 had partial coverage,13 selected the wrong target, one the wrong source and one was underspecified. Correct localization of a requested target does not prove that target is useful. No region was manually repaired.

The acquisition-rate panel remains the frozen 24-family source-stratified hash sample (12 global,6 local,6 local-plus-global), not the outcome-enriched casebook. All 24 were reviewed before final-answer inspection. Whole-record correctness includes value, binding and supporting source. Unknown/absent/abstaining evidence is not imputed wrong.

| Helper arm | Verified correct record /24 | Explicitly wrong /24 | Unknown /24 | Demand answered /24 | New correct visual information /24 |
|---|---:|---:|---:|---:|---:|

| G | 13 | 3 | 8 | 7 | 2 |

| Q | 7 | 4 | 13 | 3 | 2 |

| QI | 10 | 2 | 12 | 7 | 3 |

| QIA | 11 | 1 | 12 | 7 | 3 |

| QGL | 11 | 1 | 12 | 8 | 4 |


Verified-record yield: QI−G−12.50pp (95% CI−33.33,+8.33), QI−Q+12.50pp (−8.33,+33.33), QGL−QI+4.17pp (−8.33,+16.67), QGL−QIA0pp (−12.50,+12.50). The stricter new-correct-demand counts are 2, 2, 3, 3, 4 for G,Q,QI,QIA,QGL. These sparse supporting observations do not prove fresh visual use or mediation. G can choose different facts from the targeted arms; record correctness alone is not a perfectly matched-target measure. [Full supporting bootstrap](../analysis/readout_stats_v8.json).

Additional source reviews cover five technical cases outside the fixed 24,17 source-flagged cases, three newly reviewed regression families, and three primary-rescue families:52 reviewed families total. All nine regression families are covered. The last six reviews are explicitly outcome-enriched and excluded from the fixed-panel rates. One AI reviewer performed the judgments, with prior source exposure and no independent reliability estimate.

## Fallbacks, costs and execution

The 432 logical slots use 345 primary physical solver calls; 87 slots are exact-payload aliases. Query-arm aliases to N occur in 10 families (seven rejected queries and three NONE). G always had its own physical continuation. Other aliases arise from exact identical injected records or address/global-view fallbacks. QGL used 49 actual full-image-plus-local helper calls; 13 accepted-query cases reused a full-image helper. A fallback is not a successful local acquisition.

| Arm | Logical slots | Slots reusing another solver receipt | Alias to N | Median generated tokens | Median request latency (s) |
|---|---:|---:|---:|---:|---:|

| N | 72 | 0 | 0 | 12,784.0 | 325.7 |

| G | 72 | 0 | 0 | 11,328.0 | 273.3 |

| Q | 72 | 10 | 10 | 12,292.5 | 268.3 |

| QI | 72 | 13 | 10 | 12,597.0 | 294.6 |

| QIA | 72 | 27 | 10 | 12,353.5 | 303.6 |

| QGL | 72 | 37 | 10 | 12,634.5 | 285.2 |


Actual cumulative Slurm allocation charge: **21.365278 GPU-hours**, including all failed/technical attempts; the final two resumed jobs used8.682500 GPU-hours. The prior total was12.682778GPU-hours. The former 16-hour ceiling was superseded for this fixed remainder by the user’s instruction to finish after the resource HOLD; no extra scientific cohort or arm was added. New jobs had48-hour limits and ended after their queues. Final Slurm states for149690/149691 are COMPLETED. A post-completion release request for149691 followed receipt authentication during a shutdown/status transition; no rollout was interrupted.

The primary 345 solver calls generated 5,198,520 tokens; median 12,985, IQR 5,919–21,143, maximum 81,920. There were 344 backend-stop completions and one cap completion. Reused scientific helpers comprise 439 distinct calls and 19,617 generated tokens; all 439 stopped normally. QUERY 72, LOCATE 62, and physical READ 305 calls are deduplicated across aliases. Helper visual tokens total 326,214, solver visual tokens 330,697. Measured image-preprocessing CPU time totals 13.44 s for helpers and 12.87 s for solvers; separately isolated GPU visual-encoder time is not available.

Solver request latency median 298.38 s (IQR 131.81–588.65), helper latency median 62.71 s. These include overlapping scheduling residence; summing them does not yield billed GPU-hours. Per-arm costs also share alias receipts. The Slurm ledger is authoritative and includes failed work/startup. Two archived completed partial-family outputs and eight earlier interrupted records remain outside primary metrics. [Execution costs](../analysis/execution_metrics_v8.json) · [allocation ledger](../audit/resource_accounting_final_v8.json).

## Case interpretation

- Item633: targeted helpers report rabbit 99 while the source places it at 100. QI/QIA regress from native 76 to 75, but QGL returns 76 despite its wrong helper fact. This supports an explicit helper error; it does not establish a simple one-to-one mediation from that value to every final.

- Item2919: G claims four gray cells per face; the source has 12. Targeted image helpers abstain despite valid image transport. All treatment finals regress. Missing readouts are not labeled visual misreads.

- Item2898: DA/DC are correctly named, but the needed inner/outer shading relation remains unaddressed. Item847 similarly repeats a correct row count instead of resolving position/offsets. Correct but unhelpful readouts can accompany regressions.

- All three QI rescues were inspected after scoring. Item471’s helper is uncertain; item423 repeats six identical gray rectangles without the needed orientation/layout; item1380 says rectangular, already given, rather than resolving the string configuration. None provides a clearly new task-critical fact in the standardized QI helper readout. Final-answer rescue alone therefore cannot establish better acquisition.

- Item2924 has a correct parallelogram readout but all final answers remain wrong. Item487 obtains a correct 19-hexagon readout while native and all treatment finals are already correct. These preserve positive acquisition observations without inventing downstream benefit.

[Final casebook with exact raw outputs, images, source notes and score provenance](casebook_final_v8.md). The earlier 46-family [source-only casebook](source_casebook_v8.md) is preserved.

## H1–H4 and one recommendation

**H1, subgoal-query benefit: not demonstrated.** QI is below G by 6.94 pp (CI−15.28,+1.39) and below Q by 4.17 pp (−12.50,+4.17). Source-readout gains over Q are uncertain and do not exceed G on overall verified-record yield. Small new-fact counts leave uncertainty.

**H2, source-address/global-local increment: not demonstrated.** QGL−QI is 0 pp (−4.17,+2.78); QGL−QIA is−1.41pp among 71 scorable pairs (−7.25,+4.23). One additional fixed-panel new-correct readout is a limited positive observation. No crop-only or matched-image-budget extension was run, so pure global-context necessity or a cost-isolated crop effect is untested.

**H3, downstream accuracy: no demonstrated improvement.** Primary QI−N is−4.17pp, with uncertainty spanning zero. Generic G has a small uncertain+2.78pp change. These data neither justify a positive SAVA efficacy claim nor precisely rule out small gains.

**H4, target-selection bottleneck: supported descriptively, not causally isolated.** Few accepted queries are fully relevant; many are underspecified, repeated, or ask for mathematical unknowns rather than source-resolvable facts. An oracle-target counterfactual was not run. The pilot cannot prove how much a better target selector would recover.

**Recommendation — not executed:** Before an online Stage14E controller or scale-up, validate a demand-resolution interface that distinguishes a genuinely unresolved, source-resolvable visual premise from an already supplied fact or a mathematical unknown, and abstains when that distinction cannot be made. Keep the next development question focused on target selection/readout sufficiency; this pilot provides no basis to prioritize additional crop machinery. A prospective protocol and independent evaluation of that change remain future work.

The tested implementation remains a small development pilot with one stochastic continuation per family/arm, single-reviewer acquisition labels, previously observed families, mixed but family-coherent execution blocks, and extra-image/compute differences. No latent acquisition mediation or novelty claim is established. The old 1,674-continuation/375GPU-hour Stage14D grid remains HOLD. Stage14C-V remains unfinished. **No Stage14E or other follow-on experiment was launched. STOP.**

## Final artifact map

- [Reviewed family/arm scores](../analysis/scored_logical_rows_final_v8.json) and [clean CSV](../analysis/scored_logical_rows_final_v8_clean.csv); original automatic scores and original CSV export are retained.

- [Final paired estimates and source/schedule strata](../analysis/accuracy_and_pairs_final_v8.json).

- [Gold-hidden response reviews](../annotations/response_review_v8.json), [regression coverage](../annotations/regression_review_complete_v8.json), [primary-rescue review](../annotations/primary_rescue_review_complete_v8.json).

- [Generation/receipt freeze](../audit/scientific_generation_freeze_v8.json), [cross-node validation](../audit/resumption_v8_cross_node_validation.json), [historical preservation](../audit/final_historical_preservation_v8.json).

- [Final package verification](../audit/final_result_verification_v8.json) and [reproduction notes](../audit/analysis_execution_notes_v8.json).
