# Stage14E: completed visual-evidence acquisition development cycle

Closed 2026-10-23T01:05:20.728767+00:00. **The selected Source-Premise Ledger did not demonstrate improved visual evidence acquisition.** The full bounded cycle is complete:72-family SAVA postmortem, 24-family controlled diagnostic, one prospective 24-family development revision, and one disjoint 32-family evaluation. No follow-on experiment is launched. The old Stage14D 375-GPU-hour experiment remains HOLD; Stage14C-V remains unfinished.

## 1. Main final results

| Condition | Useful source-correct acquisition /32 | Correct final /32 | Wrong | Unscorable | Scorable accuracy |
|---|---:|---:|---:|---:|---:|
| Native continuation (N) | Not separately elicited | 19 | 13 | 0 | 59.38% |
| Original SAVA-style full-image reader (S) | 1 | 20 | 12 | 0 | 62.50% |
| Source-Premise Ledger (M) | 0 | 20 | 12 | 0 | 62.50% |

Primary acquisition M−S = **−3.125pp**,95%family-bootstrapCI **[−9.375,0]**:0gains,1loss. M has0/17 useful reads among accepted queries and0/32 among all assigned families; S has1/28 and1/32 respectively. The sole success is a partial reinspection, not full recovery of a source structure. Same-target M_noimage produces0/32 useful source-correct facts; a text-only helper is not visual acquisition. The primary criterion requires source correctness, correct binding, task relevance and novelty or justified reinspection, with no explicitly wrong task-critical statement in the same readout.

Zero useful recovery does not mean every emitted statement was false: 10 of the 17 M readouts repeat source-correct information already established in the prefix or supplied by the question. Those records are retained as known/given evidence, rather than credited as newly acquired information.

| Paired final-answer contrast | Scorable families | Difference (pp) |95%bootstrapCI (pp)| Rescues | Regressions |
|---|---:|---:|---|---:|---:|
| S-N | 32 | 3.12 | [0.00, 9.38] | 1 | 0 |
| M-N | 32 | 3.12 | [0.00, 9.38] | 1 | 0 |
| M-S | 32 | 0.00 | [0.00, 0.00] | 0 | 0 |

Both treatments rescue the same single family,166, with no regressions; their correctness vectors are identical across all32 families. The ledger’s +3.125pp downstream difference is one additional correct answer, with an interval that includes zero. This is not reliable evidence of a general accuracy benefit. The M−S bootstrap[0,0] reflects no observed paired differences; it does not establish population equivalence.

In166, both helper records only repeat known/given information: the old reader gives the larger square’s side length2, and the ledger repeats that the squares abut. Both treated solvers answer1 versus native1/2, but their final geometrical explanations differ. The ledger calls the combined figure a rectangle, while the source reference defines an apex triangle excluding the smaller square. A matching final number does not certify faithful visual interpretation. Exact quotes, character offsets and source/output hashes are in analysis/shared_rescue_provenance_v1.json; the source judgments and answer scores are unchanged.

Final-answer changes are a separate downstream endpoint. No M final-answer rescue is evidence of a newly recovered task-critical helper fact, because the independently sealed M acquisition assessment contains no useful recovery. The experiment does not identify causal mediation. All assigned families and aliases remain in the analysis; unscorable finals are not called wrong. Full missingness bounds and scorable/assigned rates are preserved in final_accuracy_v1.json.

The acquisition endpoint measures the standardized helper evidence record. It is not an exhaustive audit of every later visual claim in the solver continuation. Solvers retain their original images, so later visual recovery or other reasoning changes remain possible and are not identified by the helper score.

M_noimage is an acquisition-only control; it has no downstream solver continuation. Final-answer comparisons therefore do not isolate fresh helper-image information from the text or extra inference introduced by the acquisition pipeline.

## 2. What prevented useful acquisition in SAVA?

The completed72-family postmortem joined source images, frozen prefixes, raw queries, predicted addresses, helper outputs and final scores. Existing52 source reviews were preserved; the remaining20 received100explicitly versioned supplementary helper reviews. Their rubrics are not silently pooled. All 9 any-arm regressions (33,633,847,1067,1207,2317,2390,2898,2919) and 3 primary QI rescues(423,471,1380) have exact provenance in the casebooks.

Original QI36/72 versus N39/72 gives−4.17pp,95%CI[−12.50,+4.17],3rescues and6regressions. Only 22/62 accepted queries were fully task-relevant (bootstrapCI24.19–46.77%);14/49local views correctly localized the requested source (16.33–40.82%). In the frozen24 acquisition panel, QI supplied new correct information in3/24 versus2/24generic lookback. None of the3QIanswer rescues supplied a clearly new task-critical fact in the standardized readout. This does not establish the mechanism of a rescue or regression.

The72-prefix audit distinguishes16already-correct source states,26tentative claims,16unresolved premises, 12explicit source/text errors and2text/mathematical states. A mention is not confirmed acquisition; absence is not a latent acquisition-failure diagnosis. Fixed512-token timing sometimes encounters no new visual need, but many other cases have unresolved or erroneous premises. Timing was not randomized.

Concrete obstacles were: mathematical unknowns requested as visible values; broad entity/property queries omitting task-critical bindings; redundant queries despite unresolved different relations; predicted regions missing the requested source; and incomplete or wrong reading even when a useful source was available. Global-context difficulty is an association from the earlier audit, not proof that another crop fixes it.

## 3. Competing mechanisms, diagnostic and selected method

The prospective diagnostic compared old versus redesigned targets, prefix-conditioned versus independent reading, structural readouts, source-informed diagnostic targets, no-image reading and predicted local/global views. Demand recognition, semantic target binding, prefix influence, localization, reading and checkpoint timing were kept as competing explanations. Prior-art assessment covers all11requested works with primary links in prior_art_and_hypotheses_v1.md. Query generation, checklists, crop/zoom and image reinjection are not claimed as novel.

On the24 development families, useful yields were4/24old-target/context,3/24old-target/independent, 0/24redesigned-target/context,1/24redesigned-target/independent(candidateA),0/24structural(candidateB), 6/24source-informed-target/context,3/24source-informed-target/independent,1/24no-image,3/24local/global. The initial controller made20NONE decisions including15unresolved/tentative missed opportunities. The T targets carry some qualitative hints (1067crossing presupposition;2702anti-checkerboard advice); therefore T versus model-target is not a clean value-free identity-only factorial contrast or oracle upper bound. Those inputs never enter either deployable candidate or final evaluation. Matched T reader comparisons hold the same enriched query fixed; their limitations remain explicit.

The sole scientific revision, Source-Premise Ledger R, enumerates up to 3 source obligations before assigning coverage. Deterministic source-span references replace rewritten quotations; the host selects the first UNKNOWN/TENTATIVE obligation, otherwise NONE. The selected reader uses the original full image and explicitly unverified prefix, returns a compact evidence record, and resumes the unchanged solver through an unverified observation wrapper. No E*, gold, human ROI or answer verification enters deployment.

Matched A4000 development yielded3/24useful R_context reinspections versus0/24matched A, difference+12.5pp,95%CI[0,25]. R_independent yielded1/24 and R_noimage0/24. The3R successes (487,1067,2471) were all partial;0complete source structures were recovered. Selection followed the frozen acquisition criterion, with fewer wrong readouts as tie-break, before any final 32 outcomes. No further method tuning occurred.

## 4. Why the selected method did not generalize

Final 32 M has17accepted queries,12invalid-ledger fallbacks and3legitimate NONE decisions. Of17accepted targets,9are only partially task-relevant and8unhelpful; none is fully relevant. Ten reads repeat known/given information,4contain explicit task-critical errors,1is unknown and2are irrelevant/derived. Two NONE decisions are useful abstentions;1277misses an unsettled premise. Invalid fallbacks are not successful abstention.

Whole-ledger provenance is also brittle:7rejected records have a valid first eligible entry but another invalid obligation. This descriptive audit did not execute alternatives or relax the frozen validator. Even accepted targets fail to recover the needed structure:943tape count/range errors,62uniform-row error,784horizontal/vertical binding error,1829wrong arithmetic-layout support. Source error is not inferred from a wrong final. There is no localization module in the selected final method; those4failures are not labeled ROI failures.

Source-only prefix QC has9already-established,13tentative and10unresolved cases; M useful yield is0in each. The dominant actionable obstacle is producing and reading the precise relational binding the task needs, not merely naming an object or passing a JSON/provenance check. The evidence supports this operational bottleneck, but does not isolate one causal reason among target selection, validation, readout and timing.

## 5. Reproducibility, engineering and resource use

Pinned Qwen3-VL-4B-Thinking revision1de27d8c51f12e819435303b9e84c4e25ba8401e; vLLM0.11.0/torch2.8.0/transformers4.57.1; BF16; temperature1/top-p.95/top-k20/repetition1/presence0. Helper cap 2048, native continuation cap 81920, original 512-token anchors, original MathVision image/template preprocessing, family seeds, MP0 and prefix-cacheoff. Fresh same-prefix continuations are compared; no fictional historical advanced RNG state is reconstructed.

A CPU token-ID audit verifies that all 32 re-encoded frozen prefixes exactly match the historical first 512 generated token IDs. It does not assert that the fresh continuation restores the historical advanced RNG or KV state.

All final arms use matched A6000 hardware. Acquisition completes before solver output review; each of 4 solver workers passes 2/2 repeated 64-token input/token gates.32 families map to 96 logical solver assignments,77 physical solver generations and 19 explicit native aliases. Source review has96 logical S/M/noimage assignments. Response-only finals are reviewed without gold before inherited MathVision grading.

Engineering repairs preserved failed attempts: unsupported schema uniqueItems removed while host duplicate checks remain; source-catalog tags separated from visual frame; A4000KV-capacity failures led to a prospectively versioned acquisition/long-solver split without shortening output caps; prose dimensions such as7-foot-by-7-foot normalized without changing true negative values; transient missing Slurm accounting retried in a new CPU launcher, failing closed if unresolved. Numeric repair changed0/48saved development transports. No scientific prompt was tuned on final 32 results. Source-informed target contamination is a diagnostic design limitation, not relabeled as an engineering success.

CPU test evidence is under audit/:51prelaunch tests,18support tests with overlaps, and6dispatcher/accounting repair tests. Exact coverage includes malformed/adversarial provenance, JSON branch/schema support, numeric signs, native aliases, cap preservation, family-level missingness and resource admission. Runtime gates and final receipt/input/hash checks provide integration evidence; a syntax flag is not source correctness.

New allocation charges: **7.148889GPU-hours /24**. Unused allowance: 16.851111GPU-hours. Historical SAVA21.365278GPU-hours remains separate; historical-plus-new 28.514167. All submitted GPU jobs, including failures/startup/cancellation, are charged from Slurm elapsed×allocatedGPUs. 48hour scheduler limits were used; finite queues released allocations on completion. No idle GPU allocation remains. Request latencies overlap under helper batching and are not used as billing.

| Arm | Physical executions | Native aliases | Generated tokens, median [Q1,Q3] | Cap hits |
|---|---:|---:|---|---:|
| N | 32 | 0 | 14261 [7063.25, 22700.75] | 0 |
| S | 28 | 4 | 11053 [7433.75, 24275.0] | 0 |
| M | 17 | 15 | 13126 [6610.0, 21103.25] | 0 |


Helper component costs (request latency, not allocation billing):

| Component | Calls | Median generated tokens | Median request seconds | Image representations processed |
|---|---:|---:|---:|---:|
| S_query | 32 | 33 | 6.50 | 0 |
| M_query | 32 | 202 | 37.44 | 0 |
| S_read | 28 | 48 | 1.78 | 28 |
| M_read | 17 | 55 | 2.30 | 17 |
| M_noimage_read | 17 | 38 | 1.64 | 0 |

Token distributions above describe logical assignments and repeat native aliases. Full physical-call tokens, latency, image preprocessing, pixel counts and allocation records are in execution_efficiency_v1.json and resource_accounting_final_v1.json. All 5,357 historical closure files remain byte-identical.

## 6. Scope of inference and recommendation

The 32 conservative families have32 unique image hashes, source-only frozen hash selection with answer-format×structured stratification, and no overlap with the old72or all300Stage14D-0audit families. Prior benchmark exposure remains; this is not an untouched independent benchmark confirmation. One AI reviewer, condition-visible, supplies source judgments. References may be imperfect; all original pixels and exact outputs remain inspectable. One stochastic seed per family cannot separately estimate seed variance. Family-equal 4,000-draw stratified bootstrap(seed20261022) does not treat requests/tokens as independent. Zero-event[0,0]bootstrap intervals are degenerate:0/32 does not prove a zero population rate (descriptive unstratified exact upper 95% bound 10.89%).

Helpers use the prospectively frozen compact structured-output mode with an explicit empty think section. This result concerns that interface and checkpoint protocol; it is not a ceiling on the model’s visual reading ability under every possible readout protocol. No further helper prompt or decoding search was performed on the final evaluation cases.

Development selection used matched A4000 arms; final evaluation used matched A6000 arms after a prospective infrastructure amendment. Within-evaluation comparisons retain matched hardware, but the development-to-evaluation change cannot be attributed solely to cohort generalization. Sample, hardware-sensitive sampling and sparse event counts are not separately identified.

1. **Most actionable obstacle:** precise task-critical source binding, followed by faithful reading; controller/provenance validity alone is insufficient. Whole-ledger rejection is an additional observed bottleneck.

2. **Mechanism developed:** obligation-first Source-Premise Ledger with deterministic source-span provenance, coverage-aware selection/abstention and a full-image evidence reader. It is implemented and evaluated, but no novelty or efficacy claim is established.

3. **Acquisition improvement:** no;0/32useful M versus1/32S. The partial development benefit did not reproduce.

4. **Final-answer improvement:** M−N=3.12pp, 95%CI[0.00, 9.38], 1rescues/0regressions on32paired-scorable families. One additional correct answer does not establish a reliable benefit; there is no advantage over the SAVA-style reader. Interpret separately from acquisition.

5. **Unresolved:** whether better relation-complete target selection, visual binding/readout supervision or different checkpoint timing can improve acquisition; how much prefix-conditioned reading reflects image input versus copied assumptions; and generalization beyond this small, previously benchmark-exposed cohort.

6. **Recommendation:** do not scale this ledger implementation to a larger efficacy study. A subsequent, separately scoped development study should first demonstrate reliable entity–relation binding in a bounded source-reading task with independent evidence-level validation. This is one recommendation, not a launched experiment.

## Artifact map

- Postmortem: sava_failure_postmortem_v1.md, sava_all72_casebook_v1.md, postmortem_source_coverage_supplement_v1.md.
- Ideation/prior art: prior_art_and_hypotheses_v1.md; diagnostic_v1.md and diagnostic_interpretation_limits_v1.md.
- Development: development_revision_v2.md; protocol/final_method_selection_v1.json.
- Final acquisition: final_acquisition_review_v1.md; annotations/evaluation_source_review_v1.json.
- Final outcomes: analysis/final_accuracy_v1.json, final_scored_rows_v1.json; response-only annotations preserved separately.
- Casebooks: final32_casebook_v1.md, final_answer_change_casebook_v1.md; analysis/final_case_index_v1.csv and final_casebook_v1.json.
- Implementation: scripts/stage14e/README.md, ledger_v2.py, contracts_v2.py, engine_runtime.py, continuation_worker.py and frozen protocol/manifests.
- Verification/resources: audit/final_execution_verification_v1.json, historical_preservation_final_v1.json, resource_accounting_final_v1.json and final closure seal.
