# Stage 7A-Bench v2 — reduced sweep

**Status: COMPLETE / STOP — 2026-09-15T16:05:01.936417+09:00.**

The reduced sweep contains 1,382 reviewed native conditions from 1,392 frozen conditions/1,000 base IDs (990 bases with responses). Four fixed pilots contain 187 events: 17 strong faithful, 66 weaker faithful, 3 strong WRONG_SOURCE_READ and 101 unresolved. The three strong failures belong to three different native bases/source families. No additional benchmark or downstream intervention was started.

Phantom and CharXiv are preserved. MathWild passed the unchanged 96-review semantic gate A with 19 localizable candidates/12 bases and completed only its original 264-condition sample. MMMU and MMLong are complete. MathSight, MicroVQA and MedXpertQA-MM remain deferred; their historical artifacts and original broader plan remain preserved.

The research question is which benchmark regimes provide source-faithfulness failures that can support causal diagnosis and a later grounding monitor or intervention. The fixed model is Qwen3-VL-4B-Thinking with BF16 model weights and inputs; relevant numerical reductions retain the established runtime precision.

## Native screening

Accuracy is source-reviewed final correctness among adjudicated responses, not official full-test accuracy. Unknowns remain explicit. Local errors and whole-response F0 controls are separate from causal certification.

| Benchmark / condition | Reviewed / frozen | Final accuracy | Local visual/source errors | Binding errors | F0 candidates |
|---|---:|---|---|---|---:|
| Phantom-0 / silent_no_image | 200/200 | N/A | N/A | N/A | N/A |
| Phantom-0 / explicit_guess | 200/200 | N/A | N/A | N/A | N/A |
| MMMU-Pro / explicit_guess | 64/64 | 10/43 (23.3%); 21 unknown | N/A | N/A | 0 |
| MMMU-Pro / image_present | 200/200 | 96/124 (77.4%); 76 unknown | 78/160 (48.8%); 40 unknown | 64/170 (37.6%); 30 unknown | 37 |
| MMMU-Pro / silent_no_image | 64/64 | 16/45 (35.6%); 19 unknown | 1/2 (50.0%); 62 unknown | 0/1 (0.0%); 63 unknown | 0 |
| CharXiv / image_present | 200/200 | 110/187 (58.8%); 13 unknown | 168/198 (84.8%); 2 unknown | 48/195 (24.6%); 5 unknown | 28 |
| MMLongBench-Doc / image_present | 190/200 | 89/169 (52.7%); 21 unknown | 103/189 (54.5%); 1 unknown | 73/190 (38.4%); 0 unknown | 70 |
| MathWild / photo | 200/200 | 103/172 (59.9%); 28 unknown | 117/196 (59.7%); 4 unknown | 85/185 (45.9%); 15 unknown | 25 |
| MathWild / screenshot | 64/64 | 34/58 (58.6%); 6 unknown | 35/61 (57.4%); 3 unknown | 28/61 (45.9%); 3 unknown | 7 |

MMLong exclusions: five runtime OOMs, two missing PDFs and three context-limit exclusions. All 190 generated responses, including seven capped traces, were fully reviewed. Complete pre-cap local claims may remain eligible under the frozen rules. Final-accuracy identification bounds and all condition-specific unsupported-claim counts are retained in the linked accounting.

## Causal yield and source/readout feasibility

| Benchmark | Pilot events / bases / families | Strong faithful | Weaker faithful | Strong wrong-source | Unresolved | Strong failures /100 reviewed conditions | Strong failures /pilot event | Accounted GPUh |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Phantom-0 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | 3.93 |
| MMMU-Pro | 33/31/31 | 1 | 24 | 0 | 8 | 0.000 | 0.0000 | 48.50 |
| CharXiv | 64/61/61 | 6 | 25 | 1 | 32 | 0.500 | 0.0156 | 16.19 |
| MMLongBench-Doc | 42/36/29 | 7 | 14 | 2 | 19 | 1.053 | 0.0476 | 36.83 |
| MathWild | 48/45/45 | 3 | 3 | 0 | 42 | 0.000 | 0.0000 | 50.58 |

All four pilots have zero assigned PRIOR_FILL, STALE_SOURCE_READ, SOURCE_COUPLED_EXTRACTION_ERROR, DOWNSTREAM_INTEGRATION_ERROR and SOURCE_ANOMALY states. These zeros describe captured labels, not fully tested state absence. Candidate anomaly flags (3 CharXiv, 8 MathWild, 2 MMMU,5 MMLong) remain nested within unresolved outcomes. Full raw/certified state counts and base/family nesting are in `analysis/failure_state_yield.json`.

Strong-failure yield per 100 frozen native bases is 0.5 for CharXiv and 1.0 for MMLong; MathWild/MMMU are 0 and Phantom is N/A. MMLong’s per-reviewed-condition yield uses 190 responses; its frozen-base denominator remains 200. Repeated event, base and source-family counts are not interchangeable.

| Benchmark | Prepared / eligible / selected events | Selected failure / faithful candidates | Localized T / X / valid value readouts | Failure events with T / X semantic-sham pairs |
|---|---:|---:|---:|---:|
| CharXiv | 67/66/64 | 32/32 | 64/64/64 | 4/4 |
| MathWild | 49/48/48 | 19/29 | 48/20/48 | 3/6 |
| MMMU-Pro | 34/33/33 | 5/28 | 33/33/33 | 0/0 |
| MMLongBench-Doc | 53/42/42 | 15/27 | 42/42/42 | 1/3 |

The source-reviewed prepared pools are bounded; unprepared errors are unassessed. Eligible failure readouts are correctly oriented before scoring. Semantic/sham availability does not itself establish followability or certify a state. MMLong’s 15 failure events span 11 bases/10 families; its three alternative-control failures span two bases/families. All 42 selected MMLong events have localizable sources and valid value readouts; most native document errors were not exhaustively prepared.

## What the retained axes establish

- **Prior/no-valid-source:** Phantom has four unsupported silent-no-image claims/200 bases and none in explicit guess mode; all four switch to abstention. MMMU preserves 200 image-present responses plus 64 silent and 64 explicit conditions; specific absent-image F3 claims occur 4/64 silent versus 1/64 explicit. Its local 17/25/22 behavioral partition and 19 image-correct/both-absent-wrong pairs are not causal B-Clean. All 187 selected pilot events have intact targets, and no absent-image PRIOR_FILL certificate was tested. This axis remains behavioral/selection-feasibility evidence.

- **Source confusion:** CharXiv retains exactly 1 strong wrong-source, 6 strong faithful, 25 weaker faithful and 32 unresolved. MMLong adds 2 strong wrong-source cases: a 3M table fair-value total of 132 is replaced by the gross-notional field 2,277; HOVER4/ProgramFC recall 49.93% is replaced by the FEVEROUS-S bar 85.65%. Alternative suppression reduces wrong-value preference, and alternative semantic edits move the readout beyond matched sham. One is a document table-field error; the other is a chart binding error inside a document. Their source sheets and signed W2/W8/control effects were reviewed in `audit/mmlong_certified_case_validity_review_v25.json`.

- **Degraded extraction:** MathWild passed its semantic gate but its 48-event pilot captured no strong unfaithful state. Complete 64-base pairing shows 9 response-level clean-correct→photo-local-error changes and 6 reverse changes; these may involve different claims/sources and are not matched-demand causal transitions. The gate and 48-event selection were not expanded after effects.

## Cost, ranking and decision

Accounted native generation plus causal science/mechanics totals 156.03 GPUh. Including separately recorded MMLong native wrapper/startup/OOM overhead raises that to 160.77 GPUh (MMLong 41.56 versus 36.83 in the comparable accounted column). MMLong causal science sums two one-GPU worker runtimes; it is not two-worker wall time. Full-pipeline overhead and annotation minutes are incomplete. Review burden is 1,382 responses, 187 selected events and 110 unique local-control images; MMLong alone has 2,122,005 reviewed response characters and about 135 documented agent review minutes, excluding some source/control preparation. This is not measured human labor.

Track A evidence order: MMLong, CharXiv, MathWild. Track B behavioral-bridge order: MMMU, Phantom; no causal PRIOR_FILL winner is established. MMLong leads captured failures, while CharXiv is cheaper per captured failure. Accuracy does not determine either ordering. Two MMLong failures would require a 12-fold linear scaling to reach 24 if yield stayed unchanged; that illustrative calculation costs about 442 accounted GPUh, or 499 with recorded native wrapper overhead, before unknown annotation/other costs. The extrapolation from two failure families is not an established feasible cohort. No natural primary benchmark is frozen for expansion.

**Exactly one recommendation: Controlled Confusable-Source Construction**, anchored to the verified MMLong table-field case. Limited control preparation could be a major yield bottleneck, so this is not a claim that natural failures are intrinsically rare. The proposal makes T/X/readout/control identifiability explicit while preserving a natural reference. See `next_stage_recommendation.md`; no recommended work has begun.

## Verification and limits

The replacement allocation 114451 used two node02 A6000 GPUs in tmux 10. The unchanged 42-event MMLong seal completed, including both 199k-token cases. Exact KV/logit/RoPE and original source/candidate/no-op/repeat mechanics passed on both devices against the immutable native document backend. The earlier dense-versus-document full-tensor comparison failed and remains preserved; dense-document tensor equivalence is not claimed. BF16 input conversion/cache residency repairs retain full pages, readouts and inherited causal definitions.

Historical embedded annotation status strings such as “bank pending” or “pilot_selected:false” are preparation snapshots; the outer frozen pilot and hash-bound control-review receipts govern executed membership/control availability. They were not rewritten. Early CPU reporting commands omitted explicit cache/temp environment binding; external effects were not inspected or verified. Later commands bind allowed project paths. Dataset lookup/download provenance is preserved separately.

Detailed limits: `reduced_sweep_interpretation_limits_v20.md`. Raw A–J dimensions, nested accounting, rankings, coverage and costs are indexed in `analysis/benchmark_comparison.json`. Final figure coverage and the 23 technical criteria are recorded in `stage7a_bench_v2_acceptance.json`.
