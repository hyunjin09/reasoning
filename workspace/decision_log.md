# Decision Log

## D-001 — Pivot to visual–reasoning dynamics

- Date: 2026-08-25.
- Status: approved.
- Decision: Replace PIQD/FastV continuation as the active research program with the analysis-first visual–reasoning dynamics program in `plan/overview.md`.
- Basis: The user explicitly authorized the pivot, and the overview defines a new central question, primary model, staged evidence program, and methodological rules.
- Consequence: Stage 0 instrumentation becomes active. Qwen3-VL-4B-Thinking and MathVerse are the primary model and benchmark. New method design is deferred.

## D-002 — Preserve prior PIQD work as smoke evidence only

- Date: 2026-08-25.
- Status: supported by completed audit.
- Decision: Retain the Phase 1–2b artifacts for provenance and reusable engineering lessons, but do not use them as evidence for causal visual dependence or visual-memory claims.
- Evidence: `workspace/phase_memory/phase_2b_phase2_audit.md` records conclusion B and `hook_smoke_only: true` because Phase 1 used approximate static input-level FastV pruning.
- Consequence: The new instrumentation must validate causal measurements independently and must not equate attention or token-pruning behavior with visual usage.

## D-003 — Authorize bounded Stage 0 execution

- Date: 2026-08-25.
- Status: approved.
- Decision: Execute `plan/stage0_plan.md`, including implementation, 2–5-example baseline-faithfulness smoke validation, and a conditional 30–50-example run.
- Gate: The larger run may start only if the smoke acceptance checks pass. Any instrumentation-faithfulness, visual-token mapping, alignment, cache-validity, or resource-safety failure must be fixed before continuing.
- Stop boundary: Produce the Stage 0 deliverables and acceptance-criterion status, then stop without beginning Stage 1.

## D-004 — Decode multibyte tokens against the completed string

- Date: 2026-08-25.
- Status: supported by direct tokenizer diagnostics and independent validation.
- Decision: Derive per-token display text from stable boundaries in the completed decoded string, rather than assuming every decoded prefix extends the previous prefix.
- Evidence: Qwen token prefixes for symbols including `⊥` and `∠` temporarily decoded as `�` until the final byte token arrived. The deterministic repair report is `outputs/stage0/summaries/decode_alignment_repair.json`; all 30 reconstructed token streams pass `outputs/stage0/summaries/validation.json`.
- Consequence: Future stages must retain the Unicode-aware decoder and directly verify that joined token text reconstructs the raw decoded response.

## D-005 — Treat high bounded-generation truncation as a Stage 1 design constraint

- Date: 2026-08-25.
- Status: supported by the fixed 30-example Stage 0 run.
- Decision: Preserve the 2,048-token results and their filtering labels; do not silently discard, rerun, or reinterpret capped trajectories as completed reasoning.
- Evidence: `outputs/stage0/summaries/stage0_summary.json` records 4 correct, 26 truncated, 0 wrong, and 0 invalid trajectories under a fixed deterministic configuration.
- Consequence: Stage 0 instrumentation is accepted, but later causal analyses cannot assume that the raw 30-example set provides 30 eligible completed trajectories. Any change to generation handling or sample eligibility must be specified and approved in the next plan.

## D-006 — Authorize gated descriptive Stage 1

- Date: 2026-08-26.
- Status: approved.
- Decision: Execute Stage 1A with a fixed 20-example 4,096-token pilot and conditional 8,192-token escalation, then execute descriptive Stage 1B only if the selected-cap truncation, 3/3 faithfulness, practicality, and minimum-cohort gates pass.
- Fixed boundaries: Qwen3-VL-4B-Thinking, MathVerse, greedy decoding, Stage 0 prompt/preprocessing/evaluator/instrumentation, at most 200 raw discovery attempts, and no Stage 2 causal experiment.
- Consequence: All new outputs belong under `outputs/stage1`; Stage 0 remains immutable. Attention peaks and correlations are hypothesis-generating descriptions only.

## D-007 — Stop Stage 1 at the failed generation-protocol gate

- Date: 2026-08-26.
- Status: supported by completed prospective pilots and independent validation.
- Decision: Do not select 4,096 or 8,192 tokens and do not start Stage 1B. The fixed 4,096 pilot truncated 10/20 traces, and the conditional 8,192 rerun truncated 5/10 traces; both rates exceed the allowed 10%.
- Evidence: `outputs/stage1/protocol_pilot/protocol_report.json`, `outputs/stage1/protocol_pilot/validation_4096.json`, and `outputs/stage1/protocol_pilot/validation_8192.json`.
- Consequence: Selected-cap faithfulness, discovery generation, temporal dynamics statistics, representative inspection, paired-variant preparation, and Stage 2 are not run. Any higher cap or change to the cohort, model, or decoding protocol requires explicit approval.
- Boundary: Pilot attention artifacts remain descriptive only and were not interpreted as causal visual usage.

## D-008 — Authorize Stage 1A.2 natural-EOS protocol revision

- Date: 2026-08-26.
- Status: explicitly approved by the user.
- Decision: Replace the unexecuted 16,384 incremental-cap proposal with a same-cohort comparison of greedy versus official Qwen Thinking sampling under a 40,960 safety ceiling. Use normal EOS as the intended stop.
- Official-style condition: seed 1,234, `do_sample=true`, temperature 0.6, top-p 0.95, top-k 20, repetition penalty 1.0, presence penalty 0.0, and `max_new_tokens=40960`, following Qwen's repository evaluation-reproduction settings.
- Gate: Prefer >=90% normal termination. Permit 80–90% only with explicit pathology/bias/feasibility justification. Require 3/3 exact selected-protocol instrumentation faithfulness before Stage 1B.
- Consequence: Stage 1B becomes conditionally authorized again; Stage 2 remains prohibited.

## D-009 — Lock official-style Qwen Thinking inference for Stage 1B

- Date: 2026-08-26.
- Status: supported by direct protocol comparison, manual review, independent artifact validation, and 3/3 exact faithfulness.
- Decision: Use Qwen's official evaluation-style sampling on NVIDIA RTX A5000 with seed 1,234, temperature 0.6, top-p 0.95, top-k 20, repetition penalty 1.0, presence penalty 0.0, EOS normal stop, and a 40,960-token safety ceiling.
- Evidence: `outputs/stage1/protocol_pilot/protocol_40960_report.md`, `outputs/stage1/protocol_pilot/protocol_40960_selection.json`, and `outputs/stage1/protocol_pilot/faithfulness_check_40960.json`.
- Basis: Official-style sampling terminated normally on 10/10 shared examples; greedy terminated on 8/10 and its two cap hits were extreme repetition loops. Instrumented and uninstrumented generated token IDs then matched exactly on all three selected official-protocol traces.
- Limitation: The official pilot was only 3/10 correct and its five longest traces were materially pathological. The lock represents intended-use generation and reliable termination, not clean reasoning.
- Consequence: Stage 1B is authorized on the prospectively frozen 200-attempt cohort. Preserve all outcomes, require at least 80 completed-correct trajectories for primary dynamics analysis, keep attention claims descriptive, and stop before Stage 2.

## D-010 — Accept Stage 1 with the reduced discovery cohort and scale-sensitive recurrence result

- Date: 2026-08-26.
- Status: supported by 200/200 independent bundle validation and manual review.
- Decision: Accept Stage 1 as complete with 82 completed-correct trajectories, the predeclared minimum-cohort path. Preserve the missed target of 100 as a limitation rather than weakening eligibility.
- Evidence: `outputs/stage1/summaries/stage1_discovery_validation.json`, `outputs/stage1/summaries/stage1_statistics.json`, `outputs/stage1/discovery/manual_review/segmentation_review.json`, and `outputs/stage1/summaries/stage1_acceptance.json`.
- Result: Visual attention is early-heavy on average but recurrently modulated and heterogeneous across trajectories. Fixed 64-token windows find at least two peaks in 85.37% of eligible traces and fixed 128-token windows in 59.76%, so broad recurrence is supported while exact event rates and timings remain segmentation/scale-sensitive.
- Limitations: Semantic labels are noisy, many long correct traces are meandering, pooled span statistics are non-independent, uncertainty is lower at candidate peaks, and the aggregate variant comparison shows no robust shift in visual mass or peak count.
- Consequence: Retain recurrence and input dependence as candidate hypotheses only. Do not treat peaks as causal visual access or begin Stage 2 without review and explicit authorization.

## D-011 — Authorize Stage 2A existing-artifact paired and ROI discovery

- Date: 2026-08-26.
- Status: explicitly approved by the user.
- Decision: Execute `plan/stage2a.md` using only immutable Stage 1 artifacts. Audit VI/VD pair interpretability, perform within-problem descriptive comparisons if the gate passes, and build a manually validated evidence-ROI subset with candidate future windows.
- Fixed boundary: No new model inference, causal intervention, image counterfactual, activation/KV patching, attention manipulation, or Stage 2B execution.
- Gate: Audit 10 seeded-random both-correct pairs first; target at least 20 clean A/B examples for GO, allow 10–19 only as a documented conditional result, and issue NO-GO below 10 or when mappings/stages are unreliable.
- Consequence: New outputs belong under `outputs/stage2a`; Stage 0 and Stage 1 remain immutable.

## D-012 — Constrain the next causal target to a five-example evidence-specific pilot

- Date: 2026-08-26.
- Status: supported recommendation; Stage 2B not yet approved.
- Decision: Accept Stage 2A as complete, reject a broad VI/VD or attention-peak intervention, and recommend only a conditional five-example evidence-specific pilot for later review.
- Evidence: `outputs/stage2a/paired_analysis/paired_analysis.md`, `outputs/stage2a/evidence_subset/evidence_subset_report.md`, `outputs/stage2a/summaries/stage2a_acceptance.json`, and `outputs/stage2a/summaries/validation.json`.
- Basis: Only 13/36 both-correct VI/VD pairs are clear information shifts, global paired visual-allocation effects are mostly null, and only five ROI examples combine high-confidence annotation with descriptive A-to-B alignment (`699, 739, 2799, 3044, 3764`).
- Required controls if later approved: no intervention, target evidence ROI, same-size irrelevant ROI, evidence-identity ROI, and off-window timing control, all paired within example and seed.
- Consequence: Stop before Stage 2B. Attention and ROI focus remain descriptive; any causal implementation requires a separate plan, explicit authorization, and fresh instrumentation-faithfulness validation.

## D-013 — Accept Stage 3A pre-E0 visual-content sensitivity and recommend carrier review

- Date: 2026-08-31.
- Status: supported by a frozen 49-base counterfactual cohort, matched sham controls, exact-prefix validation, bootstrap analysis, and manual rollout audit.
- Decision: Accept Stage 3A as technically complete and issue **GO** as a recommendation to review a future carrier-tracing stage. This recommendation does not authorize or start Stage 3B.
- Evidence: `outputs/stage3a/analysis/primary_statistics.json`, `outputs/stage3a/analysis/temporal_sensitivity_statistics.json`, `outputs/stage3a/analysis/rollout_manual_audit.md`, and `outputs/stage3a/summaries/stage3a_acceptance.json`.
- Result: CE and sham-controlled CE are positive for 49/49 independent base problems. Mean controlled CE is 3.1864 nats/candidate-token (95% bootstrap CI 2.8688--3.4988), compared with mean sham shift 0.0392. All 46 problems with an available E0-8 checkpoint meet the frozen early-sensitivity rule.
- Scope: The result supports the claim that changing localized visual content causally alters evidence preference before explicit E0 mention. It does not identify V, Q, or R as the carrier, establish visual memory, or validate attention timing as acquisition timing.
- Limitations: Forty-five of 49 edits are localized numeric labels, no clean C3 irrelevant edit was available, fixed early probes can be locally ungrammatical, and the post-freeze Stage 2C moderator overlaps only nine T2 mention-centered cases.
- Consequence: Review Stage 3A jointly with Stages 2A--2C before specifying any next causal experiment. Keep all carrier patching, cache interventions, cutoff/reveal tests, and attention-guided interventions stopped until separately approved.

## D-014 — Redirect from prefill localization to post-prefill acquisition timing

- Date: 2026-08-31.
- Status: supported by the frozen 49-base Stage 3B.0 cutoff/patch experiment and passing controls.
- Decision: Accept Stage 3B.0 as technically complete, but do not recommend immediate layer-wise prefill V→Q/P localization. Return **REDIRECT — Post-prefill acquisition timing** for review; this does not authorize Stage 3B.1.
- Evidence: `outputs/stage3b0/cutoff/cutoff_statistics.json`, `outputs/stage3b0/patching/patch_statistics.json`, `outputs/stage3b0/smoke/hook_transparency.json`, and `outputs/stage3b0/summaries/stage3b0_acceptance.json`.
- Result: Generation-start cutoff preserved positive CE in 42/49 bases but only 14.5% mean and 6.1% median of full-vision CE. Broad post-image patching exactly transferred the residual; Q-only patching recovered 0.9884 at the median and was source-consistent in both directions for 46/49. Self patches were exactly null and sham shifts were small.
- Consequence: Treat Q as a causal carrier of the small prefill residual, not of most of the Stage 3A effect and not as the unique carrier. Any future timing sweep, Q→R patch, or layer/head/module localization requires a separate reviewed plan.

## D-015 — Authorize bounded Stage 3B.1 visual-sufficiency timing

- Date: 2026-08-31.
- Status: explicitly approved by the user.
- Decision: Execute `plan/stage3b1_plan.md` on the frozen 49-base Stage 3A cohort using prospectively frozen pre-E0 timing checkpoints and one full-sequence eager scoring path.
- Basis: Stage 3B.0 retained only 14.5% mean / 6.1% median full-vision CE at generation start, so the predeclared redirect calls for locating when later direct visual access becomes dispensable.
- Fixed boundary: attention is secondary and post-freeze only; no Q/R patching, layer/module/head/path localization, or Stage 3B.2 may begin.
- Consequence: Run a mandatory three-base timing smoke gate before the cohort, produce one GO / CONDITIONAL GO / REDIRECT recommendation, and stop.

## D-016 — Do not advance to Stage 3B.2 after visual-sufficiency timing

- Date: 2026-08-31.
- Status: supported by the complete frozen Stage 3B.1 cohort.
- Decision: Return **REDIRECT — Persistent direct-vision dependence** and stop before carrier localization.
- Evidence: 49/49 bases and 489/489 checkpoints validated; 0/49 first or stable rho>=0.80 crossings; median E0-1 retention 0.1114; median maximum post-prefill gain 0.0313; mean E0-1 sham shift 0.0027.
- Interpretation boundary: this shows that future direct visual access remains important for preserving the evidence-specific effect under the tested all-visual cutoff. It does not identify where evidence is stored, prove a unique information fraction, or establish an attention-defined state.
- Consequence: Stage 3B.2 Q/R carrier patching is not justified as the immediate next step. Selecting a redirected experiment requires separate review and authorization.

## D-017 — Authorize bounded Stage 3B.2 visual-source switching

- Date: 2026-08-31.
- Status: explicitly approved by the user after reviewing the Stage 3B.1 result.
- Decision: Execute `plan/stage3b2_plan.md` as an evidence-identity source-switching experiment, not as Q/R carrier patching.
- Basis: Stage 3B.1 all-visual cutoff established persistent direct-vision dependence but could not distinguish target-evidence retrieval from generic/distributed visual support. Replacing future visual K/V with the counterfactual source preserves a valid visual pathway and directly tests evidence identity.
- Fixed boundary: exact 49-base cohort, prospective `E_d` and checkpoint freezes, bidirectional/self/sham controls, attention secondary only, and no layer/Q/R/module/head/path or ROI-specific localization.
- Consequence: pass a three-base smoke before cohort scoring, produce one final Stage 3B.2 recommendation, and stop.

## D-018 — Accept late evidence-specific visual-source control and recommend layerwise review

- Date: 2026-09-01.
- Status: supported by the frozen 49-base Stage 3B.2 experiment, reciprocal controls, sham controls, fixed-seed behavioral validation, and 16/16 technical acceptance criteria.
- Decision: Accept Stage 3B.2 as complete and return **GO — Layer-wise visual-to-reasoning transfer analysis** for review. This recommendation does not authorize or start localization.
- Evidence: `outputs/stage3b2/analysis/bidirectional_retrieval_statistics.json`, `outputs/stage3b2/scoring/rollout_summary.json`, `outputs/stage3b2/analysis/cutoff_vs_switch_comparison.json`, and `outputs/stage3b2/summaries/stage3b2_acceptance.json`.
- Result: At E_d-1 and E_d, 49/49 independent bases were bidirectionally source-consistent. Median unnormalized BRI was 12.0118 and 9.0923; median normalized BRI was 0.9703 and 0.8022; median sham/target ratios were 0.0107 and 0.0115. The frozen late-GO rule passed at both checkpoints.
- Scope: The result supports causal control by evidence-specific future visual content at the frozen decision. It does not identify an ROI, layer, module, head, path, or Q/R carrier, and attention remains secondary.
- Limitation: Thirty-seven of 49 E_d annotations use frozen semantic teacher-forced candidate leads rather than exact baseline-trace continuations, so exact natural-trajectory timing claims must be restricted.
- Consequence: Stop before all localization. Any layerwise transfer analysis requires a separate reviewed plan and explicit user authorization.

## D-019 — Authorize bounded Stage 3B.3 layer-wise transfer localization

- Date: 2026-09-01.
- Status: explicitly approved by the user after Stage 3B.2 completion.
- Decision: Execute `plan/stage3b3_plan.md` as one bounded layer-localization action on the exact frozen 49-base cohort.
- Basis: Stage 3B.2 showed strong reciprocal evidence-specific source control at E_d-1 and E_d, while its all-layer intervention cannot distinguish a hotspot, sequential transfer, redundancy, or distributed synergy.
- Fixed boundary: six prospective coarse windows, cumulative lower/suffix sets, current-query-only residual patching, a prospective fine-window rule, exact-baseline robustness, and attention-independent selection.
- Consequence: require the three-base A5000 smoke before cohort execution; produce one GO/REDIRECT/REDESIGN recommendation and stop before all module/head/path/Q-R/ROI-specific or later experiments.

## D-020 — Stop Stage 3B.3 at the restoration sham gate

- Date: 2026-09-01.
- Status: supported by the prospectively frozen three-base smoke and one bounded diagnostic.
- Decision: return **REDESIGN** and do not launch the 49-base Stage 3B.3 cohort under the current protocol.
- Evidence: `outputs/stage3b3/smoke/layer_switch_validation.json`, `outputs/stage3b3/smoke/restoration_sham_diagnostic.json`, and `outputs/stage3b3/summaries/stage3b3_acceptance.json`.
- Result: 11/12 smoke checks passed. All-layer/no-switch scores exactly reproduced Stage 3B.2; self, layer/query, visual-position, nonvisual-K/V, residual-patch, sign, finite-value, and determinism controls passed. Coarse restoration sham/target was 0.314949, exceeding the frozen 0.25 maximum.
- Diagnosis: unknown. Median absolute target restoration was 0.134651 and sham restoration 0.042408, so the failure is not solely a zero-denominator artifact.
- Consequence: the coarse atlas, cumulative cohort curves, fine scan, exact-baseline robustness, and all later experiments remain unrun. Any new restoration control or threshold is a new prospective protocol requiring explicit review and approval.

## D-021 — Authorize bounded Stage 3B.3-R paired-restoration redesign

- Date: 2026-09-01.
- Status: explicitly approved by the user after the Stage 3B.3 smoke failure.
- Decision: execute `plan/stage3b3_redesign_plan.md` as one bounded restoration-control redesign. Preserve the original failure, freeze an independent seed-20260901 eight-base method-validation split, compare paired original- and counterfactual-semantic render variants, and reserve the remaining 41 bases until the validation decision is fixed.
- Prospective gate interpretation: `base_problem_id` is the independent validation unit. Gate A requires at least 7/8 bases to have an active window and positive bidirectional base-median restoration, giving one-sided exact-binomial p < 0.05 against chance, plus positive cohort-median BSRC. Gate B defines activity per base/window at 10% of that base's Stage 3B.2 all-layer BRI. Gates C and D are medians across active bases after within-base median aggregation. These rules are frozen before any redesign score is read.
- Conditional consequence: PASS authorizes the reserved 41-base selective/cumulative/residual atlas with paired restoration; RESTORATION-DROP authorizes the same reserved atlas without restoration or necessity claims; STOP/REDESIGN prohibits the primary run. In all cases, stop after Stage 3B.3-R and do not begin module/head/path/Q-R/ROI-specific or later experiments.

## D-022 — Accept late-layer paired sufficiency/restoration localization

- Date: 2026-09-01.
- Status: supported by independent method validation, a frozen 41-base primary cohort, paired render controls, prospective fine localization, and 16/16 acceptance criteria.
- Decision: accept Stage 3B.3-R as complete and return **GO — Module/path localization** for review. This recommendation does not authorize or start the next experiment.
- Evidence: `outputs/stage3b3_redesign/analysis/layer_statistics.json`, `outputs/stage3b3_redesign/analysis/fine_layer_statistics.json`, `outputs/stage3b3_redesign/analysis/decision_rule_evaluation.json`, and `outputs/stage3b3_redesign/summaries/stage3b3_redesign_acceptance.json`.
- Result: W4 (layers 24--29) is the strongest coarse region at both evidence coordinates. At `E_d-1`, median normalized selective BWS is 0.6107 (95% bootstrap CI 0.5709--0.6547; N=41) and paired semantic-restoration BSRC is 0.6531 (0.6217--0.6936; N=37). The prospective fine scan retains the effect at F28_29 and a smaller secondary effect at F32_33. The distributed-coordinate rule does not pass.
- Controls and robustness: all mechanical controls pass; W4 paired restoration is bidirectionally consistent for 37/37 bases at both coordinates; median W4 restoration render/semantic ratios are 0.0129 at `E_d-1` and 0.0231 at `E_d`. The untouched exact-baseline-token stratum is N=7, with a prospectively secondary pooled N=12 robustness analysis.
- Scope: the result localizes causal sensitivity to visual-source identity and current-position residual transfer at fixed evidence-decision coordinates. It does not identify an attention head, attention-versus-MLP implementation, ROI-specific path, Q/R carrier, or general reasoning state.
- Consequence: stop after Stage 3B.3-R. Any module/path study requires a separate prospectively reviewed plan and explicit authorization.

## D-023 — Redirect module attribution to unresolved distributed block computation

- Date: 2026-09-01.
- Status: supported by an independent eight-base gate, the frozen 37-base paired primary family, exact self/baseline controls, and 16/16 technical acceptance criteria.
- Decision: accept Stage 3B.4 as technically complete and return **REDIRECT — Distributed block computation** for review. This recommendation does not authorize a follow-on experiment.
- Evidence: `outputs/stage3b4/validation/validation_results.json`, `outputs/stage3b4/analysis/module_restoration_statistics.json`, `outputs/stage3b4/analysis/decision_rule_evaluation.json`, and `outputs/stage3b4/summaries/stage3b4_acceptance.json`.
- Result: full-block restoration is robust in all four E_d-1/E_d × W4/W5 cells. Attention and Joint effects are often robust, but median Attention/Block ratios are 0.137--0.411 and Joint/Block ratios 0.329--0.539; MLP/Block is 0.040--0.143 and MLP fails the robustness rule in both W4 cells. No frozen dominance or cascade category passes in at least two cells.
- Interpretation boundary: the result rules out the prespecified simple component attributions under this restoration protocol. It does not uniquely prove a distributed mechanism; sequential block interactions, normalization/residual effects, cross-layer dependence, and restoration non-additivity remain possible.
- Consequence: stop before head/path/ROI/Q-R/multi-evidence/failure or other later experiments. The next action requires separate scientific review and explicit authorization.

## D-024 — Localize nontrivial restoration gains to the post-Attention boundary

- Date: 2026-09-01.
- Status: supported by independent method validation, the frozen 37-base paired cohort, exact boundary/recompute controls, 20/20 persisted-artifact validation checks, and 17/17 technical acceptance criteria.
- Decision: accept Stage 3B.5 as technically complete and return **GO — Attention head/path localization** for review. This recommendation does not authorize or start a head/path experiment.
- Evidence: `outputs/stage3b5/validation/validation_results.json`, `outputs/stage3b5/analysis/boundary_restoration_statistics.json`, `outputs/stage3b5/analysis/decision_rule_evaluation.json`, and `outputs/stage3b5/analysis/artifact_validation.json`.
- Result: 26/40 Holm-corrected boundary tests are robust. The frozen post-Attention gain rule passes in `E_d-1/W4`, `E_d-1/W5`, and `E_d/W4`; it does not pass in `E_d/W5`. The upstream rule passes only in `E_d/W5` (`h_pre`/Block 0.808), with `E_d-1/W5` borderline below the 0.80 cutoff at 0.786. No MLP-gain or cross-layer-necessity category passes.
- State-dependent recomputation: `h_pre` recomputation exceeds frozen Joint restoration only in W5, whereas source `h_post_attn` plus natural MLP recomputation exceeds frozen precomputed MLP restoration in all four cells by median 0.548--0.847 Block units.
- Interpretation boundary: R3 plus natural MLP recomputation and direct R5 restoration are exactly score-equivalent in all 296 base/coordinate/window/layer cases because the MLP is deterministic and positionwise once source `h_post_attn` is fixed. Zero `G_mlp` is therefore a structural intervention equivalence, not evidence of general MLP irrelevance. The three-cell result is evidence for a nontrivial post-Attention state gain under the tested hybrid restoration, not proof that attention weights or a particular head/path carry the effect.
- Consequence: stop after Stage 3B.5. Any head/path study requires a separate prospective plan, joint review of the W5 upstream heterogeneity and equivalence caveat, and explicit user authorization.

## D-025 — Localize two robust visual-source paths within late Attention heads

- Date: 2026-09-01.
- Status: supported by an eight-base discovery screen, frozen 37-base confirmation, paired O/O_sham/C/C_sham controls, reciprocal source swaps, 17/17 technical acceptance criteria, and 20/20 independent artifact checks.
- Decision: accept Stage 3B.6 as complete and return **GO — ROI-specific visual path + pattern/value decomposition** for review. This recommendation does not authorize or start that experiment.
- Evidence: `outputs/stage3b6/analysis/head_restoration_statistics.json`, `outputs/stage3b6/analysis/source_path_statistics.json`, `outputs/stage3b6/analysis/upstream_control_statistics.json`, and `outputs/stage3b6/analysis/artifact_validation.json`.
- Result: 10/14 frozen head/set tests confirmed. Two minimal targets pass the robust V-dominance rule: `E_d/W4` Top-4 has median V PRR 0.979 and `E_d-1/W4` Top-2 has 0.885, with P/R paths nonrobust. `E_d-1/W5` head-10 has V PRR 0.989 but fails the sham-control gate at 0.436 and is therefore inconclusive rather than a third positive attribution.
- Heterogeneity: at the separate `E_d/W5` upstream control, the W4-derived minimal targets show near-zero transfer, while `E_d-1/W5` head-10 has median BHR 0.984 and HRR 0.977. Do not pool these cells into one mechanism.
- Secondary lesson: raw selected-head visual attention was not a positive proxy for restoration on the base-aggregated N=37 analysis; attention remains neither a selection criterion nor causal usage evidence.
- Consequence: stop after Stage 3B.6. Any ROI, K-vs-V, or pattern/value decomposition requires a new prospective plan and explicit user authorization.

## D-026 — Stop Stage 3B.7 at the disjoint sham-relative validation gate

- Date: 2026-09-02.
- Status: supported by the prospectively frozen eight-base validation run, exact legacy equivalence, deterministic repeats, and one bounded read-only diagnostic.
- Decision: return **REDESIGN** and do not launch the 37-base Stage 3B.7 primary ROI-localization cohort under the current protocol.
- Evidence: `outputs/stage3b7/validation/roi_path_validation.json`, `outputs/stage3b7/validation/validation_failure_diagnostic.json`, and `outputs/stage3b7/summaries/stage3b7_acceptance.json`.
- Result: all mechanical checks passed, including exact Stage 3B.6 all-V equivalence, ROI/source isolation, self transparency, logical-query-head selectivity under GQA, finite scores, and deterministic repeats. `E_d/W4/Top_4` passed with median BPR 0.836429 and sham/semantic 0.114337. `E_d-1/W4/Top_2` had positive median BPR 0.213821 and 0.75 bidirectional consistency but sham/semantic 0.269893, exceeding the frozen `<0.25` limit.
- Diagnosis: supported sham-relative semantic-strength limitation, not an implementation failure. Median absolute sham shift was modest (0.059710), but semantic restoration was near zero on validation bases 83 and 101. This evidence does not justify retrospectively relaxing the ratio threshold.
- Consequence: zero Stage 3B.7 primary bases were scored. Phase B, W5/head_10, optional alpha, attention triangulation, vision-encoder localization, and later experiments remain unrun. Any target change, artifact metric change, or new validation design is a prospective redesign requiring explicit user review and approval.

## D-027 — Accept revalidated ROI-local Value-content transport

- Date: 2026-09-02.
- Status: supported by 13 fresh disjoint validation bases, the untouched 37-base primary cohort, paired semantic/sham/irrelevant controls, exact intervention mechanics, and 20/20 technical acceptance criteria.
- Decision: accept Stage 3B.7-R as complete and return **GO — Value-content mechanism** for review. This recommendation does not authorize or start a later experiment.
- Evidence: `outputs/stage3b7r/validation/semantic_validation_statistics.json`, `outputs/stage3b7r/analysis/roi_path_statistics.json`, `outputs/stage3b7r/analysis/kv_decomposition_statistics.json`, and `outputs/stage3b7r/summaries/stage3b7r_acceptance.json`.
- Fresh validation: both prospectively frozen targets pass every semantic paired-margin and mechanical gate on N=13. Target A median ROI BPR is 0.6369 (95% bootstrap CI 0.3123--0.9531); Target B-R is 0.1551 (0.0938--0.5000); both are bidirectionally consistent on 12/13 bases.
- Primary ROI result: both targets are `ROI-Local` on N=37. Target A median target PRR is 0.886 versus complement 0.047 and irrelevant 0.001; Target B-R is 0.848 versus complement 0.115 and irrelevant 0.005. Both target effects and paired sham/irrelevant margins are robust.
- K/V result: both targets are `Value-Dominant`. K-only is nonrobust; V-only is robust with median KVR 1.154 at `E_d/W4` and 1.044 at `E_d-1/W4`; K+V exactly reproduces target-ROI restoration. Ratios are unclipped and are not additive information fractions.
- Attention boundary: attention was analyzed only after causal freeze. Pooled correlations average the two target rows within each base (N=37); they are not significant, while target-specific relationships differ. This secondary heterogeneity does not define or invalidate the causal Value result.
- Scope: under the tested late-layer query-head/source-position intervention, counterfactual evidence identity is restored through Value content from the exact edited visual ROI more reliably than through K-only routing. This does not prove that raw attention is causal evidence, identify a query/key subspace, localize vision-encoder features, or establish a general memory/lifecycle mechanism.
- Consequence: stop after Stage 3B.7-R. Any next experiment requires a separate prospective plan and explicit authorization.

## D-028 — Accept graded but distributed late Value geometry

- Date: 2026-09-02.
- Status: supported by an endpoint-exact representation audit, a fresh disjoint 20-base discovery cohort, untouched 37-base confirmation, paired sham/complement controls, 100 same-rank random controls per target, cross-target transfer, and 20/20 technical acceptance criteria.
- Decision: accept Stage 3B.8 as complete and return **GO — Distributed Value geometry** for review. This recommendation does not authorize or start another experiment.
- Dose result: both late-W4 targets pass the frozen causal dose-response gate. Median full-dose BVR is 0.7758 for Target A and 0.1537 for Target B-R; median within-base Spearman values are 1.0 and 0.9. Endpoint, self, determinism, and paired sham controls pass.
- Compression result: discovery-only rank 8 passed its fitting-set rule but did not generalize at the required strength. On the untouched primary cohort, median projected/full restoration is 0.368 for Target A and 0.532 for Target B-R, while orthogonal-complement/full is 0.472 and 0.348.
- Specificity controls: learned rank-8 effects exceed the sham-derived bases and all 100 random rank-8 controls for both targets (learned percentile 1.0; empirical one-sided `p=0.0099`). This establishes non-arbitrary shared structure, not recovery of most causal information.
- Cross-target/attention boundary: cross-target medians are only 0.0040 into Target A and 0.0017 into Target B-R under an ordinal four-head mapping. Post-freeze attention correlations are target-heterogeneous and remain secondary; neither result defines causal visual use.
- Interpretation: donor Value content causally and gradedly controls evidence preference, but the tested common rank-8 geometry is insufficient across untouched problems and substantial causal effect remains outside it. The failure's cause is unknown; broader dimensionality, sample conditioning, nonlinearity, and discovery/confirmation distribution mismatch remain alternatives.
- Consequence: stop after Stage 3B.8. Do not start vision-encoder/projector origin localization, multi-evidence refresh, Q/R lifecycle, MLP-feature/neuron, failure analysis, or another Value-geometry experiment without a separately reviewed plan and explicit authorization.

## D-029 — Authorize final single-evidence distributed-geometry test

- Date: 2026-09-02.
- Status: explicitly approved by the user after Stage 3B.8 completion.
- Decision: execute `plan/stage3b9_plan.md` as one bounded Stage 3B.9 action comparing fresh-confirmed shared ranks with within-problem leave-one-value-out local ranks.
- Basis: Stage 3B.8 established graded causal Value transport and non-random rank-8 structure, but failed the untouched 80%/30% compression rule and left substantial complement effect.
- Fixed boundary: historical 57 bases are training-only; Phase A and B are fresh and mutually disjoint; ranks/values/controls freeze before causal outcomes; attention and mixture diagnostics are secondary only.
- Consequence: complete one shared/local geometry classification and one GO/REDIRECT recommendation, then stop before multi-evidence refresh or any other later experiment.

## D-030 — Require explicit protected-set disjointness checks for prospective cohorts

- Date: 2026-09-02.
- Status: supported by a pre-generation Stage 3B.9 cohort audit.
- Observation: candidate base 751 appeared novel under the expansion's high-index range but was already one of the 57 Stage 3B.8 historical basis-fit bases. A direct set comparison found the overlap before base 751 generation, strict E_d auditing, or Stage 3B.9 Value/causal scoring.
- Decision: exclude base 751 through a versioned corrected manifest and preserve the original manifest plus the exclusion record. No outcome-based replacement is introduced.
- Evidence: `outputs/stage3b9/config/cohort_split.json`, `outputs/stage3b9/config/generation_expansion_shards_v2/freeze.json`, and `outputs/stage3b9/exclusions/prospective_disjointness_exclusions.jsonl`.
- Promoted lesson: future prospective cohorts must be checked by explicit `base_problem_id` set intersection against every protected cohort; dataset index ranges or labels such as “unseen” are not sufficient evidence of independence.

## D-031 — Accept shared moderate-dimensional late Value geometry

- Date: 2026-09-03.
- Status: supported by fresh disjoint Phase-A confirmation, separate five-value Phase-B leave-one-value-out testing, frozen sham/random/complement controls, exact v3 mechanics, and 20/20 technical acceptance criteria.
- Decision: accept Stage 3B.9 as complete with joint outcome **G1 — Shared higher-dimensional** and return **GO — Multi-Evidence Causal Refresh** for review. This recommendation does not authorize or start the next experiment.
- Phase-A result: on N=24 fresh bases, Target A first passes all six frozen shared-geometry checks at rank 24 (median SR 0.8108, CR 0.0599); Target B-R first passes at rank 16 (median SR 0.8829, CR 0.2210). Learned effects exceed sham and the 95th percentile of 100 random controls, with bidirectional consistency 1.0 at both selected ranks.
- Phase-B result: on 14 eligible bases per target from the separate N=15 five-value cohort, no local rank 1 or 2 passes. Median Local SR is 0.3650/0.3772 for Target A and 0.4257/0.4699 for Target B-R; median Local CR remains 0.4624/0.4189 and 0.6125/0.4636. Local effects exceed random controls and are usually positive, but do not recover most held-out causal effect.
- Interpretation: the tested late-W4 ROI→Value→head causal code has shared cross-problem linear geometry, but the smallest confirmed representation is moderate-dimensional rather than a compact universal rank-8 or same-problem rank-1/2 code.
- Scope: SR/CR are unclipped, geometry is conditional on two frozen targets and localized numeric MathVerse evidence, and raw attention remains secondary. No vision-encoder, MLP, Q/R lifecycle, failure, or multi-evidence experiment was started.
- Evidence: `outputs/stage3b9/phase_a_shared/analysis/shared_geometry_decision.json`, `outputs/stage3b9/phase_b_local/analysis/local_geometry_decision.json`, `outputs/stage3b9/analysis/geometry_outcome_matrix.json`, and `outputs/stage3b9/summaries/stage3b9_acceptance.json`.

## D-032 — Accept a time-local, ROI-selective retrieval-attention phenotype without a causal attention claim

- Date: 2026-09-03.
- Status: supported by exact eager-Attention reconstruction, a frozen 37-base/four-condition cohort, prospective controls, independent artifact validation, and 20/20 technical acceptance criteria.
- Decision: accept Stage 3C.1 as complete and return **GO — Relevant-vs-distractor routing causality** as the sole review-only recommendation. This recommendation does not authorize or start the intervention.
- Result: at the frozen causal coordinates, median target-ROI attention density is 0.1057 for Target A and 0.0690 for Target B, exceeding matched irrelevant density in 36/37 and 37/37 bases. The phenotype sharpens near retrieval through QK cosine/logit and softmax competition rather than a consistent Q- or K-norm surge, with substantial target alpha-V and post-`W_O` contributions.
- Heterogeneity: natural target density correlates with the prior Stage 3B.7-R causal ROI effect for Target A (`rho=0.536`) but not Target B (`rho=0.199`); Target-B head 6 has near-zero target density despite belonging to the causal ensemble. Attention magnitude is therefore not a universal per-head or per-target causal score.
- Numerical lesson: exact BF16 validation required recomputing the installed full Attention tensor shape; a row-only mathematically equivalent recomputation changed kernel reductions and failed exact equality.
- Scope: the result characterizes natural routing at independently causal-localized coordinates but does not show that attention probability, QK alignment, or the high-mass `<|im_start|>` candidate sink is causal.
- Evidence: `outputs/stage3c1/audit/reconstruction_check.json`, `outputs/stage3c1/analysis/roi_selectivity_statistics.json`, `outputs/stage3c1/analysis/retrieval_time_contrasts.json`, `outputs/stage3c1/summaries/artifact_validation.json`, and `outputs/stage3c1/summaries/stage3c1_acceptance.json`.
- Consequence: stop before Stage 3C.2, Stage 4, rerouting, query/alpha manipulation, sink knockout, or failure analysis. Any next action requires a separate reviewed plan and explicit authorization.

## D-033 — Authorize bounded Stage 3C.2 semantic/retrieval dissociation

- Date: 2026-09-03.
- Status: explicitly approved by the user after Stage 3C.1 completion.
- Decision: execute `plan/stage3c2_plan.md` as one bounded, causally anchored descriptive action separating a distinct mention-matched ROI `M` from the independently causal task-required ROI `T`, while accounting for candidate-sink and other source-mass dynamics.
- Fixed boundary: reuse exact Stage 3C.1 causal targets/noncausal controls; define cohort, `M`, `T`, `I`, and semantic states without attention; require at least 24 `M != T` bases; use exact passive full-shape eager reconstruction; and treat `base_problem_id` as the inferential unit.
- Consequence: write exactly one review-only recommendation and stop. No query/QK/alpha/routing/sink/`h_pre`/source-state intervention, Stage 4, multi-evidence refresh, or failure analysis is authorized.

## D-034 — Accept a descriptive alignment-then-retrieval phenotype and stop before routing intervention

- Date: 2026-09-03.
- Status: supported by a prospectively frozen 31-base `M != T` cohort, exact passive reconstruction, four image/render conditions, frozen causal/noncausal heads, Holm-corrected base-level inference, and independent artifact validation.
- Decision: accept Stage 3C.2 as technically complete (20/20) and return **GO — Relevant-vs-Distractor Routing Causality** as the sole recommendation for review. This does not authorize or execute the intervention.
- Result: T exceeds M at retrieval on all 62 target/base events in attention density, QK cosine, alpha-V, and post-`W_O`; 40/62 events show earlier M dominance followed by T dominance, while 22/62 are retrieval-only. The seven frozen base-level contrasts all pass Holm correction.
- Sink result: target-mass gain is paired with median candidate-sink change -0.2166 at the base level; 46/62 events meet the exploratory sink-release rule, but candidate-sink status remains descriptive and no sink function is causally established.
- Heterogeneity: Target-B head 6 retains median target density 0.000337 and alpha-V norm 0.0177 despite prior causal-ensemble membership. Attention magnitude remains neither a universal causal score nor an information fraction.
- Evidence: `outputs/stage3c2/analysis/mention_vs_required_statistics.json`, `outputs/stage3c2/analysis/temporal_crossover_statistics.json`, `outputs/stage3c2/analysis/sink_dynamics_statistics.json`, `outputs/stage3c2/audit/independent_validation.json`, and `outputs/stage3c2/summaries/stage3c2_acceptance.json`.
- Consequence: stop after Stage 3C.2. Any routing, query/QK, alpha, sink, `h_pre`, source-state, Stage 4, multi-evidence, or failure experiment requires a new reviewed plan and explicit user authorization.

## D-035 — Authorize bounded relevant-vs-distractor routing causality

- Date: 2026-09-03.
- Status: explicitly approved by the user after Stage 3C.2 completion.
- Decision: execute `plan/stage3c3_plan.md` as one bounded reciprocal query-routing intervention, with gated current-position `h_pre` comparison only if query causality passes.
- Basis: Stage 3C.2 separated mention alignment from task-target sharpening descriptively at independently causal Target A/B anchors, but did not manipulate query routing.
- Fixed boundary: exact Stage 3C.2 T/M/I and head targets; attention-blind 7/24 validation-primary split; recipient-native K/V; prospective RoPE-formulation and statistical gates; sink observation only; no alpha rescue of a null query result.
- Consequence: produce exactly one review-only GO/REDIRECT recommendation and stop before Stage 3C.4, sink manipulation, Stage 4, multi-evidence refresh, or failure analysis.

## D-036 — Accept causal routing redistribution without reciprocal behavioral evidence control

- Date: 2026-09-04.
- Status: supported by a prospectively frozen seven-base validation, 24 untouched primary bases, exact self/KV/head controls, frozen noncausal-head controls, and 21/21 independent artifact checks.
- Decision: accept Stage 3C.3 as technically complete but scientifically failing its Phase-A gate; return **REDIRECT — Routing Intervention Not Behavioral**. This recommendation does not authorize another experiment.
- Mechanics: both direct post-RoPE and content/recipient-RoPE query forms were exact. The latter was frozen before primary scoring by a mechanics-only rule. Recipient visual/nonvisual K/V and non-target heads remained exact, and self patches were bit-exact.
- Routing/Value result: necessity and sufficiency T-vs-M RDS, attention density, and target alpha-V changed in the expected direction on 24/24 bases at both targets. Median reciprocal causal-minus-noncausal RDS was 0.7886 for Target A and 1.5040 for Target B.
- Evidence result: Target A evidence medians were -0.00113 necessity and +0.00282 sufficiency; Target B was +0.11865 necessity and -0.00579 sufficiency. Thus neither target exhibited the required reciprocal evidence-preference control.
- Interpretation: selected query heads causally control the measured routing and Value-influx intermediates, but those changes are insufficient to establish behavioral evidence control under this intervention. The cause is unknown; broader state dependence and redundant evidence support remain alternatives rather than diagnoses.
- Evidence: `outputs/stage3c3/analysis/query_causality_statistics.json`, `outputs/stage3c3/phase_a_query/phase_a_gate.json`, `outputs/stage3c3/summaries/artifact_validation.json`, and `outputs/stage3c3/summaries/stage3c3_acceptance.json`.
- Consequence: Phase B, optional alpha manipulation, Stage 3C.4, Stage 4, multi-evidence refresh, sink intervention, and failure analysis were not started. Any follow-up requires separate review and explicit authorization.

## D-037 — Accept broad robustness beyond the tested current-position W4 target-contribution family

- Date: 2026-09-04.
- Status: supported by a prospectively frozen seven-base mechanics gate, exact 24-base Stage 3C.3 primary cohort, selected-head dose curve, target/mention/irrelevant/noncausal controls, gated R1--R3 W4 family, Holm correction, and 20/20 independent artifact checks.
- Decision: accept Stage 3C.3-R as technically complete with **O4 — Broad Robustness Beyond W4** and return **GO — Redundancy Localization Beyond W4** for review only. This does not authorize the recommended experiment.
- Mechanics: FP32 contribution partitioning reconstructs the native pre-`W_O` head output within `1.19e-7`; lambda-one scoring is exact, lambda-zero source isolation is exact, local Q/K/V/attention and untargeted heads are unchanged, and deterministic repeats pass. The initial BF16-bookkeeping smoke remains preserved as failed validation evidence.
- Phase A: the redundancy gate passed with median base-aggregated `E(0)/E(1)=0.996591` and 24/24 bases at least 0.80. Target A showed no gain dependence. Target B showed a small graded and target-specific effect, but still retained median evidence 0.9879 at lambda zero.
- Stage 3C.3 relation: query-patch median projected gains were already only 0.0014/0.0059 of native for Targets A/B. Direct zero gain did not yield substantial collapse, so insufficient attenuation above a saturation threshold does not explain the prior reciprocal behavioral null.
- Phase B: R3 all-head removal at both W4 layers retained median evidence 0.9864/0.9910. No R1, R2, or R3 incremental loss over R0 survived the frozen 26-test Holm family, so same-layer and cross-layer W4 compensation were not localized.
- Boundary: persistence after R3 indicates support outside or redundant with the tested current-position W4 target-ROI contribution family; it does not identify earlier retrieval, language residual state, another layer, or another carrier. Attention remains an intermediate coefficient, not a behavioral importance fraction.
- Evidence: `outputs/stage3c3r/analysis/dose_response_statistics.json`, `outputs/stage3c3r/analysis/query_patch_curve_comparison.json`, `outputs/stage3c3r/analysis/redundancy_scope_analysis.json`, and `outputs/stage3c3r/summaries/artifact_validation.json`.
- Consequence: Stage 3C.3-R is stopped. No broader-than-W4, sink, query, `h_pre`, Stage 3C.4, Stage 4, multi-evidence, or failure experiment was started; any next action requires a separate reviewed plan and explicit approval.

## D-038 — Authorize bounded spatiotemporal redundancy localization

- Date: 2026-09-04.
- Status: explicitly approved by the user after Stage 3C.3-R completion.
- Decision: execute `plan/stage3c4_plan.md` as one bounded target-ROI contribution-suppression action across the prospectively frozen layer, late-time, and interaction scopes.
- Basis: all-head removal across W4 at the current evidence query retained median evidence 0.9864/0.9910, leaving same-time outside-W4 support, earlier late retrieval, spatiotemporal redundancy, and earlier nonvisual carriage unresolved.
- Fixed boundary: exact Stage 3C.3-R 7/24 split, Target A/B coordinates, T/M/I definitions, and FP32 pre-`W_O` contribution semantics; L0--L4, T0--T16, C1--C4, reduced M/I controls, and the 14-test Holm family must be frozen before scoring.
- Consequence: produce one O1--O4 classification and exactly one recommendation, then stop. No sink manipulation, Q/R/current-residual patching, temporal scope earlier than 16 tokens, Stage 4, multi-evidence refresh, or failure analysis is authorized.

## D-039 — Accept late temporal redundancy with an additional layer-depth component

- Date: 2026-09-04.
- Status: supported by seven-base mechanical validation, the exact 24-base Stage 3C.3-R primary cohort, frozen L0--L4/T0--T16/C1--C4 families, target/mention/irrelevant controls, Holm correction, and 20/20 independent artifact checks.
- Decision: accept Stage 3C.4 as technically complete with joint outcome **O2 — Temporal Redundancy** and return **GO — Behaviorally Necessary Visual Window Mechanism** for review only.
- Same-time result: W4 L0 retained median base-aggregated evidence 0.9859 and exactly reproduced Stage 3C.3-R on 48/48 target/base comparisons. All-layer L4 retained 0.8436; Target A crossed below 0.80 while Target B did not.
- Temporal result: expanding all-layer suppression from T0 to T1 lowered median retention from 0.8436 to 0.6515, with 24/24 positive incremental losses. Retention reached 0.5519 at T16; tested base-aggregate `w_80=T1`, while no tested `w_50` exists.
- Interaction/control result: layers24--35 over four queries retained 0.7597 and all layers retained 0.5653; the frozen interaction survived Holm correction. Target suppression exceeded M and I controls on 24/24 bases, and all 14 frozen tests were Holm-significant.
- Boundary: the result localizes necessity over late reasoning time and distributed layers but does not identify an exact retrieval token, Q/R/residual carrier, or sink function. Attention is not interpreted as an importance fraction.
- Evidence: `outputs/stage3c4/analysis/spatiotemporal_classification.json`, `outputs/stage3c4/analysis/primary_family_statistics.json`, `outputs/stage3c4/audit/artifact_validation.json`, and `outputs/stage3c4/summaries/stage3c4_acceptance.json`.
- Consequence: Stage 3C.4 is stopped. No carrier patch, sink manipulation, window earlier than `t*-16`, Stage 4, multi-evidence refresh, or failure experiment was started; any follow-up requires separate review and explicit authorization.

## D-040 — Authorize preceding-query necessity and state-handoff localization

- Date: 2026-09-04.
- Status: explicitly authorized by the user through `plan/stage3c5_plan.md`.
- Decision: execute Stage 3C.5 as one bounded action: isolate target-ROI contribution at `t_pre=t*-1` across frozen P0--P5 layer scopes, and run gated R/Q/`h_pre` carrier localization only if isolated `t_pre` necessity passes the prospective gate.
- Frozen quantitative interpretation: Phase B requires P5 loss positive on at least 18/24 bases, Holm significance, and median loss at least 0.26138; the necessary layer family is the smallest passing scope reaching at least 80% of P5 median loss. R_last2/4 run only for significant but incomplete R_last1 recovery.
- Constraint: no visual K/V donor patch in Phase B, no sink manipulation, whole-history search, earlier-than-`t_pre` rescue, Stage 4, multi-evidence refresh, or failure analysis.
- Consequence: produce one final Stage 3C.5 classification and exactly one review-only recommendation, then stop.

## D-041 — Accept broad preceding-query necessity without a clean pooled carrier

- Date: 2026-09-04.
- Status: supported by seven-base Phase-A/Phase-B mechanical validation, all 24 frozen primary bases, paired self/sham controls, the gated short-R family, reduced T/M/I controls, and 20/20 independent artifact checks.
- Decision: accept Stage 3C.5 as technically complete with **O5 — No Clean Carrier** and return **GO — Current-Residual Mechanism** for review only.
- Necessary-window result: P4 (layers 16--35) was the smallest frozen scope reaching 80% of P5 median loss; P4/P5 median loss was 0.5172/0.4979, while W4/W5-local loss was small. A1/A3 reproduced Stage 3C.4 exactly.
- Carrier result: R_last1/Q/`h_pre` median BCR was 0.8463/0.1451/2.4347 and CRR was 0.0719/0.0109/0.1832. All effects exceeded sham descriptively and survived Holm correction, but none passed the frozen pooled 0.20 CRR rule. R_last4 added only 0.0091 median CRR.
- Heterogeneity: Target-A `h_pre` median CRR was 0.3226 versus 0.0205 for Target B. This is the basis for prioritizing current-residual mechanism work without claiming a universal carrier.
- Boundary: attention/QK/alphaV/sink overlap remains descriptive; no sink manipulation, current-residual follow-on, whole-history search, earlier rescue, Stage 4, multi-evidence refresh, or failure experiment was started.
- Evidence: `outputs/stage3c5/analysis/handoff_classification.json`, `outputs/stage3c5/analysis/target_heterogeneity.json`, `outputs/stage3c5/audit/artifact_validation.json`, and `outputs/stage3c5/summaries/stage3c5_acceptance.json`.

## D-042 — Authorize suppression-to-current-residual rescue

- Date: 2026-09-04.
- Status: explicitly authorized by the user through `plan/stage3c6_plan.md`.
- Decision: execute Stage 3C.6 as one bounded action: recreate the exact within-condition P4 target-ROI deficit at `t_pre`, scan all 36 `h_pre(t*)` layers for native-state rescue, and run only target-gated boundary/dose/control analyses.
- Fixed boundary: exact Stage 3C.5 7/24 split, Target A/B, T/M/I, P4, A5000 runtime, and seed; separate O/C sign alignment; unnormalized gain primary; deterministic four-layer region selection; no donor visual or past-token K/V.
- Consequence: produce one residual-mechanism classification and exactly one review-only recommendation, then stop before token-type carriers, sinks, learned subspaces, Stage 4, multi-evidence, or failure analysis.

## D-043 — Accept late incomplete current-residual rescue

- Date: 2026-09-04.
- Status: supported by exact Stage 3C.5 P4 reproduction, seven-base Phase-A and Phase-B mechanical validation, all 24 frozen primary bases, a prospectively gated boundary/dose/control family, and 20/20 independent artifact checks.
- Decision: accept Stage 3C.6 as technically complete with **O4 — Residual Insufficiency** and return **GO — Prior-Cache / Two-Query Interaction** for review only.
- Broad scan: Target A first robustly crossed RR 0.20 at layer 34 and Target B at layer 35; neither target reached a robust RR 0.50/0.80 crossing. Peak descriptive RR at layer 35 was 0.6035/0.3410 for A/B, but RR is unclipped and not a unique causal information fraction.
- Boundary result: only Target A had a valid frozen four-layer region (31--34). Its strongest confirmed point was L33 `h_post_attn` (median gain 0.2014; median RR 0.4162), while no within-block Attention or MLP increment survived the frozen robustness rule.
- Controls: Target-A residual-delta dose slope was positive on 22/24 bases with bootstrap mean CI above zero. Target rescue exceeded mention and irrelevant rescue after Holm correction; M/I median unnormalized rescue gains were near zero.
- Interpretation: the preceding-query causal deficit is partly represented in late current-position residual state, especially for Target A, but current residual alone does not robustly recover half the deficit. Suppressed prior caches or a distributed two-query interaction remain viable; this is not evidence for a specific cache mechanism.
- Evidence: `outputs/stage3c6/analysis/current_residual_classification.json`, `outputs/stage3c6/phase_a_hpre_scan/threshold_crossings.json`, `outputs/stage3c6/phase_b_boundary/boundary_statistics.json`, `outputs/stage3c6/controls/control_statistics.json`, and `outputs/stage3c6/audit/artifact_validation.json`.
- Consequence: Stage 3C.6 is stopped. No prior-cache/two-query, token-type, sink, learned-subspace, Stage 4, multi-evidence, or failure experiment was started; any follow-up requires a new reviewed plan and explicit authorization.

## D-044 — Authorize within-condition prior-cache and residual joint rescue

- Date: 2026-09-04.
- Status: explicitly authorized by the user through `plan/stage3c7_plan.md`.
- Decision: execute Stage 3C.7 as one bounded action testing native `t_pre` K/V cache rescue of the exact P4 deficit and frozen residual-plus-downstream-cache joint rescue.
- Basis: Stage 3C.6 reproduced the behavioral deficit but found no robust 50% current-residual rescue crossing; suppressed prior cache and a two-query interaction remain unresolved.
- Fixed boundary: exact 7/24 split, Target A/B, P4, native GQA post-RoPE K/projected V, A `L33 h_post_attn` plus L34--35 downstream cache, B `L35 h_pre` plus L35 cache, 12-test target-specific Holm families, and effect-independent mechanical exclusions.
- Consequence: produce one outcome and one review-only recommendation, then stop. No token-type, sink, residual-feature, Stage 4, multi-evidence, or failure experiment is authorized.

## D-045 — Accept native prior-cache carriage with target-heterogeneous joint rescue

- Date: 2026-09-04.
- Status: supported by seven-base mechanical validation, all 24 frozen primary bases, exact endpoint controls, the prospectively gated Target-A K/V decomposition, 28/28 independent artifact checks, and 258/258 repository-owned regression tests.
- Decision: accept Stage 3C.7 as technically complete with overall outcome **target-heterogeneous O2-A/O1-B** and return **GO — Token-Type Carrier Atlas** for review only.
- Cache result: full native `t_pre` K+V exactly recovered the native endpoint for both targets (median RR 1.0). V-only rescue was robust; K-only rescue was not; K+V provided a robust increment beyond V.
- Joint result: Target A's frozen residual/downstream-cache joint was near-complete (median RR 1.0006), supporting O2 residual-cache complementarity. Target B's corresponding joint was robustly positive but not substantial under the frozen threshold (median RR 0.4611), supporting O1 prior-cache carrier.
- Interpretation boundary: RR is unclipped and is not a unique information fraction. The result establishes sufficiency for the exact tested deficit and states, not universal or exclusive carriage across tasks or positions.
- Evidence: `outputs/stage3c7/analysis/two_query_classification.json`, `outputs/stage3c7/analysis/exact_endpoint_analysis.json`, `outputs/stage3c7/audit/artifact_validation.json`, and `outputs/stage3c7/summaries/stage3c7_acceptance.json`.
- Consequence: Stage 3C.7 is stopped. No token-type atlas, sink, residual-feature, Stage 4, multi-evidence, or failure experiment was started; any follow-on requires a new reviewed plan and explicit authorization.

## D-046 — Authorize the Token-Type Carrier Atlas

- Date: 2026-09-04.
- Status: explicitly authorized by the user through `plan/stage3c8_plan.md`.
- Decision: execute Stage 3C.8 as one bounded action separating lexical/semantic type, recency, structural role, visual alignment, K/V function, and prefill versus late-reasoning carriage.
- Fresh-cohort rule: freeze 240 outcome-blind A5000 baseline attempts disjoint from all earlier attempt/screen/generation pools; retain 64 target / 56 minimum only by correctness, edit, strict-`E_d`, ROI/layout, history, and annotation validity.
- Fixed causal boundary: exact inherited P4, T16, and generation-start cutoff semantics; cache rescue is primary, attention is unused for selection/intervention, and `base_problem_id` is the independent unit.
- Consequence: run Phase D only if its frozen carrier gate passes, produce exactly one recommendation, and stop before sink, unconstrained history, residual-feature, Stage 4, multi-evidence, or failure work.

## D-047 — Accept recency-dominant, phase-specific token-cache carriage

- Date: 2026-09-05.
- Status: supported by eight-base mechanical validation, exact 24 historical anchors, a prospectively frozen 64-base fresh cohort, exhaustive recent/prompt position analyses, matched controls, gated K/V decomposition, 16/16 independent artifact checks, and 37/37 focused tests.
- Decision: accept Stage 3C.8 as technically complete with **O4 recency-dominant plus O6 phase-specific carrier structure**, retain the coordinate-specific later visual-entity effect, and return **CONDITIONAL GO — Dedicated Long-Horizon Causal-Checkpoint Cohort** for review only.
- Phase A: fresh all-layer `t_pre` K+V rescue was robust for A-like (64/64 positive; median 1.125) and B-like (57/64; median 0.151) coordinates; V carried most of the positive effect.
- Phase B: rescue was concentrated at distances 1--2 and null at 4--16. Recency-matched A-like `FUNCTION_WORD` and B-like `VISUAL_ENTITY`/`TARGET_ALIGNED` effects survived, showing semantic modulation within a strongly recency-dominant structure.
- Phase C: full-Q transfer was robust (61/64 positive; median 0.624). Gated `NUMERIC_LITERAL` transfer was K-associated and `PUNCTUATION` transfer V-associated, but punctuation was weaker than nearest matched controls, so no general boundary-integration claim is accepted.
- Phase D: only 15 fresh bases met the frozen long-horizon rule versus 28 minimum. No Phase-D inference was run, and the absence of a checkpoint result is treated as cohort infeasibility rather than a causal null.
- Evidence: `outputs/stage3c8/analysis/token_type_atlas.json`, `outputs/stage3c8/analysis/position_vs_type_analysis.json`, `outputs/stage3c8/analysis/phase_specificity_analysis.json`, `outputs/stage3c8/audit/artifact_validation.json`, and `outputs/stage3c8/summaries/stage3c8_acceptance.json`.
- Consequence: Stage 3C.8 is stopped. The recommended long-horizon cohort requires separate review and authorization; no sink, unconstrained history, residual-feature, Stage 4, multi-evidence, or failure experiment was started.

## D-048 — Stop A6000 platform calibration at the full/cache parity gate

- Date: 2026-09-05.
- Status: supported by a prospectively frozen hardware amendment, 12-base calibration cohort, four-device pool, `1e-5` numerical tolerance, one risk-first A6000 smoke, and one focused score-path diagnostic.
- Decision: classify the calibration **FAIL — F1 full/cached parity** and do not run Layers B--D or restart Stage 3C.9 under the current calibration protocol.
- Passing smoke evidence: base 74 had exact three-repeat deterministic full-path scores/states, exact full-path K/V/KV/residual self patches, the expected 36-layer/32-query-head/8-KV-head GQA layout, finite outputs, and 9.15 GB peak allocation.
- Failure evidence: full-versus-bounded aggregate |ΔD| ranged 0.0203--2.9393 and maximum token-log-probability differences ranged 0.1481--8.8680. One-shot-cache versus full also differed by 0.0998 (O) and 0.0342 (C) in aggregate D; chunk-size sensitivity was nonzero.
- Diagnosis boundary: the result corroborates earlier deterministic BF16 matrix-shape/path sensitivity and does not establish an A6000 device anomaly or scientific hardware effect. The prospectively frozen tolerance may not be relaxed after observing the failure.
- Evidence: `outputs/a6000_calibration/layer_a_internal/full_vs_memory_bounded.json`, `outputs/a6000_calibration/layer_a_internal/cached_vs_full.json`, `outputs/a6000_calibration/summaries/a6000_calibration_acceptance.json`, and `outputs/a6000_calibration/summaries/a6000_calibration_summary.md`.
- Consequence: Stage 3C.9 restart remains unauthorized. Any matched-cache causal baseline design or alternative scoring implementation is a prospective calibration amendment requiring review before execution.

## D-049 — Freeze one matched A6000 cached path and restart Stage 3C.9 cleanly

- Date: 2026-09-05.
- Status: supported by six prospective memory stresses, three first-divergence probes, a frozen 12-base strong/medium/small bridge, exact same-path mechanics, four-device replay, and 17/17 calibration-v2 acceptance criteria.
- Decision: retain calibration v1 as an immutable FAIL under its cross-path equality gate, while accepting calibration v2 as **PASS — A6000 CANONICAL PATH READY** for matched within-path causal contrasts.
- Canonical path: P1 one-shot cache was infeasible on the 30,574-token stress prefix. P2 therefore selected the largest repaired fixed chunk that passed every frozen stress case: 2,048 tokens with allocator-cache release between chunks, eager language attention, and no per-example path switching.
- Numerical result: prefill residual/post-RoPE K/projected V tensors were exact in all first-divergence probes; deterministic divergence first appeared at language layers 2–3 after execution shapes differed. Same-path scores and self patches were exact within `1e-6`.
- Scientific continuity: all 24 strong/medium suppression, K+V-rescue, and residual-rescue signs were retained; target suppression exceeded irrelevant-ROI suppression on 8/8 bridge bases. Absolute cross-shape D drift remains diagnostic, not a model-behavior result.
- Hardware result: all six stress cases stayed below the frozen 90% reserved-VRAM ceiling, and all four RTX A6000 devices passed strong, medium, small, and long-prefix probes without OOM, truncation, backend fallback, or device drift.
- Consequence: preserve the 58 partial A5000 Stage 3C.9 bundles only as provenance, restart the exact outcome-blind screen from 0/600 on four A6000s, and never pool A5000/A6000 outcomes. No experiment beyond the already authorized Stage 3C.9 plan is authorized.
- Evidence: `outputs/a6000_calibration_v2/summaries/a6000_calibration_v2_acceptance.json`, `outputs/a6000_calibration_v2/summaries/a6000_calibration_v2_summary.md`, `outputs/a6000_calibration_v2/summaries/stage3c9_restart_authorization.md`, and `outputs/stage3c9/config/a6000_execution_freeze.json`.

## D-050 — Do not infer repeated sparse checkpoints from Stage 3C.9

- Date: 2026-09-06.
- Status: supported by a prospectively frozen 48-base primary cohort, eight disjoint validation bases, 16/16 mechanics checks, the gated causal pipeline, and a post-hoc score-stability audit.
- Decision: accept Stage 3C.9 as technically complete, but do not claim recurrent sparse event-span checkpoints under the tested W8/W16 assay and do not run route decomposition.
- Result: 29/144 events passed the Phase-A source gate, two nominal events classified C2, none classified C3, and 0/48 bases contained two separated C2/C3 checkpoints. The Phase-D gate failed at 0 versus 16 required. Base 38 showed local rescue followed by subthreshold/negative distal rescue; base 149 had no distinct distal readout.
- Validity qualification: Phase-A and independently recomputed Phase-B source losses differed by median absolute 0.12363 nats/candidate-token, changing 24/33 event-window source gates at the frozen 0.05 threshold. The exact isolated-checkpoint count is therefore provisional. Zero repeated-checkpoint bases remained unchanged across thresholds 0.025--0.15 and the documented path sensitivity checks.
- Interpretation: the result does not prove absence of visual propagation. Wrong acquisition windows, distributed state, redundancy, direct refresh, and semantically mislocalized spans remain viable alternatives. Attention was not used for selection or causal interpretation.
- Consequence: Stage 3C.9 stops. Its sole written recommendation remains a qualified review of checkpoint-pair yield, with score-path stability to be resolved before any expansion. No Phase D, sink, residual-feature, whole-history, Stage 4, multi-evidence, or failure experiment was started.
- Evidence: `outputs/stage3c9/summaries/stage3c9_summary.md`, `outputs/stage3c9/analysis/repeated_checkpoint_analysis.json`, `outputs/stage3c9/analysis/lifetime_analysis.json`, `outputs/stage3c9/analysis/posthoc_score_stability.json`, and `outputs/stage3c9/summaries/stage3c9_acceptance.json`.

## D-051 — Same-path repair preserves the repeated-checkpoint negative

- Date: 2026-09-06.
- Status: supported by the exact frozen 48-base / 144-event cohort, eight
  disjoint validation bases, all 288 W8/W16 event-window quartets scored before
  classification, 15/15 mechanics and 20/20 independent acceptance checks.
- Decision: Stage 3C.9R is complete. Recommend **GO — Retrieval Trigger** for
  joint review only; do not expand the cohort to seek checkpoint pairs.
- Result: 33 events (37 event windows) are source-sensitive; 10 isolated
  checkpoints comprise 9 C2 and 1 C3. All 48 bases have at most one checkpoint.
  Counts at floors 0.025/0.05/0.10/0.15 are 12/10/6/3 isolated checkpoints and
  0/0/0/0 repeated bases. Exact isolated counts remain threshold-dependent.
- Promoted lesson: numerical comparability must include sham conditions and
  every rescue control. Repair source losses exactly reproduce all 66 matched
  Phase-B O/C cells, but four legacy gates change when shams are recomputed on
  that same path. Score all frozen events before scientific gates when a
  numerical pre-gate would otherwise determine which rescues get measured.
- Lifetime: three cases are explicitly right-censored. Five retain the qualified
  L-Short label and two satisfy the original L-Persistent mean-gain semantics;
  C3's reciprocal distinct-final criterion is stricter. Unobserved intervals
  do not establish a 16–32-token decay time. Base 38 remains C2; base 149 drops.
- Interpretation: repeated sparse semantic checkpoints are not supported under
  the frozen W8/W16 assay. Visual processing, distributed/redundant local state
  and renewed direct retrieval remain viable; their causes are not diagnosed.
- Scope: necessity was gated off by the prospectively recorded robust-at-0.15
  definition (3 versus 4 required); routes were gated off (0 versus 16 bases).
  Only existing tmux 9 / Slurm 108548 four-A6000 resources were used. All 4,751
  original artifact hashes are unchanged; no later experiment started.
- Evidence: `outputs/stage3c9r/summaries/stage3c9r_summary.md`,
  `outputs/stage3c9r/analysis/threshold_sensitivity.json`,
  `outputs/stage3c9r/analysis/stage3c9_phase_comparison.json`, and
  `outputs/stage3c9r/audit/independent_artifact_validation.json`.

## D-052 — Recent reasoning controls retrieval dependence; late-Q mediation unresolved

- Date:2026-09-06. User explicitly authorized `plan/stage3c10_retrieval_trigger_plan.md`.
- Status: exact historical7/24 split;15/15 mechanics,20/20 acceptance,45 tests,
  21 artifact checks and4 independent statistical/mediation crosschecks.
- Result: both targets pass the frozen behavioral-trigger gate. Median T-state
  TE_VSD A=.793223/B=.651588, positive20/24 and24/24; M, E16, irrelevant-ROI and
  question-source comparisons survive per-target Holm. E16 has22 paired T bases.
- Localization: k80=16 both, but A R8 and B R4 are close to the80% cutoff; do not
  infer a sharp16-token mechanism. Only upstream layers16–23 are robust bins.
- Negative mediation evidence: all-/selected-head native Q exactly restore RDS
  at both targets, but all-head VSD gains are nonrobust (A median-.000843,
  B.046476). The prospectively gated h_pre rescue is also nonrobust. Accept O1/M2,
  not an end-to-end Q-mediated behavioral chain. Failure cause remains unknown.
- Promoted lesson: upstream recent-source control of VSD and late-Q control of
  routing are distinct causal findings. Exact routing restoration alone does not
  establish mediation, and native h_pre can bypass prior visual suppression.
- Qualifications: generic language/residual/noncausal-head quantities also move;
  early M windows shorter than16 are retained. Position/type analysis is
  descriptive and distance-controlled; no universal token type or sink causality.
- Decision: complete and stop Stage3C.10. Sole review-only recommendation is
  **GO — Stage4 Multi-Evidence Retrieval/Refresh**. No Stage4 plan is authorized
  by this result, and no sink, wider-history or new-cohort experiment started.
- Resources: reused only tmux9 / Slurm108548 / node07 four A6000 GPUs; no requests,
  packages or historical artifacts changed.5121 arms across412 raw state files.
- Evidence: `outputs/stage3c10/summaries/stage3c10_summary.md`,
  `phase_b_primary/primary_statistics.json`, `phase_e_mediation/mediation_statistics.json`,
  `phase_e_mediation/hpre_statistics.json`, `audit/independent_artifact_validation.json`.

## D-053 — Multi-evidence source dependence switches; trigger generalization is qualified

- Date:2026-09-06. User authorized the bounded Stage4A plan.
- Status: technical PASS20/20;8 validation /48 primary /24 semantic bases,
  15/15 mechanics,21/21 raw/statistical checks,11 tests and16 figures.
- Result: all three W2 source-selectivity tests and both switch/refresh tests
  robust under nine-test Holm.36/48 full dynamic bases;30/48 in W8 sensitivity.
  Native O1/O2 supported within the selected local numeric-fact assay.
- Trigger qualification: TS_A1/TS_B positive35/48 and29/48, below the75% rule;
  TS_A2 positive22/48 with a mean CI crossing zero. None passes the full robust
  rule. Do not promote the Stage3C.10 trigger into an established universal
  multi-source retargeting mechanism or assume Q-mediated behavior.
- Semantic evidence: all24 bases show demanded edit effects exceeding other-source
  edits and absolute sham effects at A1/B/A2. At A2, median factorial A effect
  is9.30469, A-minus-B8.59375, A-minus-sham9.11719. Full image replay with fixed
  native text cannot time-localize acquisition of the changed fact to A2.
- Promoted lesson: later native ROI necessity, fixed-history image sensitivity,
  trigger retargeting and acquisition timing are distinct claims. Positive
  switching does not require every proposed trigger mechanism to generalize.
- Native failures: two strict stale-B A2 cases (229,345), zero strict A-dominant
  B failures and one B tie (227). Strict dominance must exclude exact ties.
  The two small stale effects do not establish a common failure or its cause.
- Reconciliation: frozen irrelevant-control N=40; earlier47 prose was incorrect.
  Seven individually reviewed controls lacked the aggregate validation flag at
  freeze. Preserve the frozen manifest instead of expanding after effects.
- Decision: complete and stop Stage4A. Sole recommendation is **HOLD — Review
  Stage4B mechanism-guided failure-rescue feasibility** on the two candidates;
  no rescue, cohort expansion, sink or later taxonomy experiment started.
- Resources: only existing tmux9 / Slurm108548 four A6000 GPUs.864 event-image
  files /2448 arms;943 frozen hashes unchanged. No new allocation or package.
- Evidence:`outputs/stage4a/summaries/stage4a_summary.md`,
  `outputs/stage4a/analysis/paper_claim_assessment.json`,
  `outputs/stage4a/audit/final_artifact_validation.json`,
  `outputs/stage4a/audit/irrelevant_subset_reconciliation.json`.


## D-054 — Candidate-margin source dominance does not identify an error cause

- Date:2026-09-07. Stage5A complete and stopped; technical20/20 PASS.
- Evidence:10 frozen Tier2 H-MR events on9 bases have alternative-source
  dominance for D=mean logP(correct)−mean logP(foil). Removing that alternative
  worsens D in all10. It increases the wrong candidate's probability in7;
  only1 event has an error-token source contribution above0.05 nats/token.
- Promoted lesson: preserve both candidate log probabilities and the actual
  generated direction. An effect on their difference cannot by itself identify
  a source as causing the observed error. A frozen operational label may remain
  valid while its stronger causal interpretation is unsupported.
- Stage5A scope: natural200/550 events; atlas128/347; CF48/85; trigger96/256.
  216 demanded-dominant profiles;82/85 semantic effects exceed absolute sham.
  13 reviewed integration-error events on7 bases separate correct local grounding
  from a wrong final answer. No automatic final-answer hallucination labeling.
- Confirmation limitation:139/267 held-out events matched; zero strict alignment
  or mirage cases. Only2 sink pairs and0 strict utility events; no forced inference.
- Decision: sole recommendation is HOLD — Stage5B failure-rescue feasibility review
  of source identity and error-specific readouts. No rescue or other next stage run.
- Evidence: `outputs/stage5a/audit/hmr_readout_orientation_diagnostic.json`,
  `outputs/stage5a/summaries/stage5a_summary.md`,
  `outputs/stage5a/analysis/paper_claim_assessment.json`, and
  `outputs/stage5a/audit/final_artifact_validation.json`.


## D-055 — Numeric crop validity does not establish prompt-to-source equivalence

- Date:2026-09-07. Stage6A construction/acquisition remains in progress.
- Direct evidence: DocVQA56412has a correctly cropped300glyph on the1980UNMCSalaryContributionbar, but its ARprompt names1980SCNDirect(actual210). R-onlyasks the tallest1980bar(300), so the pair addresses different sources despite a prior numeric-crop pass.
- Decision: preserve original prompts/native traces and exclude the entire family from the primary factorial release. One fixed source-only revalidation of all32families found31valid mappings and only this failure;124prospective events remain,31percell. No replacement, prompt tuning, attention/causal selection or extra acquisition.
- Promoted lesson: check source entity/row/column identity and equivalent prompt reference in addition to glyph/ROI correctness. The demonstrated failure concerns this chart-series mapping; it does not invalidate every correctly reviewed numeral or justify outcome-based filtering.
- Evidence: `outputs/stage6a/audit/c2_series_prompt_roi_mismatch.json`, `outputs/stage6a/audit/c2_source_mapping_revalidation.json`, `outputs/stage6a/audit/c2_source_mapping_reviews.jsonl`.

## D-056 — Preserve controlled cohort acceptance and insufficient natural-case yield

- Date: 2026-09-09. Stage6A is complete.
- Observation: C1/C2/C3 construction gates pass. C4 has 10 confirmed, 50 unresolved and 940 no-detected whole-trace object-error labels in the fixed 1,000-image sample. The frozen atlas has 10 matched pairs, below the 60-pair minimum. The 1–6% protocol identification range is not a confidence interval.
- Supported lesson: construction availability, natural-EOS feasibility, category-protocol yield and causal grounding are distinct. Keep capped traces, unresolved labels and the fixed sample; do not enlarge the current sample or change definitions to meet the atlas gate.
- Decision: GO — Natural Failure Extension, recommendation only; no next-stage execution.
- Evidence: `outputs/stage6a/summaries/stage6a_cohort_summary.md`, `outputs/stage6a/summaries/stage6a_acceptance.json`, `outputs/stage6a/c4_natural_failure/unbiased_prevalence.json`, `outputs/stage6a/audit/release_integrity.json`.


## D-057 — Joint readout eligibility determines causal dynamic coverage

- Date: 2026-09-10. Stage6B completed and stopped; technical acceptance 21/21 PASS.
- Direct evidence: the semantic-only diagnostic found 181 valid numeric anchors,
  69 transition intervals and four hold intervals before frozen sampling/matching.
  The accepted panel has 20 bases, 34 primary transitions and zero matched holds.
  Compound source mentions do not resolve a single within-span subgoal. Correct
  numeric claims also fail to supply a contrast for a geometric-role error.
- Promoted lesson: validate jointly eligible pre/post readouts and matchable
  stable-demand controls before treating coarse semantic candidate counts as
  causal dynamic coverage. More passive states cannot supply unmeasured causal
  source identities or error-oriented contrasts.
- Other evidence remains valid: C2 focal-demand necessity and C1 sham-controlled
  target grounding loss are robust. Nine strict C1 confirmation candidates occur
  across eight bases, but broad divergence fails its full gate. C3 replication
  and strong C2 dissociation are not established; C4 remains exploratory.
- Decision: **GO — Cohort/Assay Repair**, recommendation only. Repair the primary
  dynamic annotation/readout panel; do not rerun a valid assay merely because it
  gave a mixed result. Re-annotated inspected traces are not fresh confirmation
  by themselves. No rescue, new method, sink intervention or natural extension ran.
- Evidence: `outputs/stage6b/audit/dynamic_readout_coverage_diagnostic.json`,
  `outputs/stage6b/c1_dynamics/demand_coupling.json`,
  `outputs/stage6b/c1_dynamics/error_readout_diagnostics.json`,
  `outputs/stage6b/summaries/stage6b_summary.md`, and
  `outputs/stage6b/summaries/next_stage_recommendation.md`.


## D-058 — Preserve clause scope and input provenance in localized readouts

- Date:2026-09-10. Stage6BR stopped at its panel gate before causal scoring.
- Direct evidence: splitting "If diameter is11, radius is5.5" loses the
  condition and can turn a true conditional into a false error label. Parsing
  "AE=AD-ED=4" as ED=4 misassigns an operand. Both received concrete repairs.
- CE13.5 in mathvista804 is supplied in the question. Six chord-based hold
  exclusions were reopened; a question-provided number does not itself establish
  a new visual demand. The final optimistic bound treats these cases as valid.
- Promoted lesson: retain parent qualification and distinguish image facts,
  question facts and derived values before assigning demand or error validity.
  Neither an alias match nor an image-value mismatch is sufficient by itself.
- Evidence: `outputs/stage6br/audit/conditional_scope_diagnostic.json`,
  `outputs/stage6br/audit/arithmetic_lhs_diagnostic.json`,
  `outputs/stage6br/annotation_repair/interval_review_corrections.jsonl`.
- The constructed pool's optimistic62 matched-hold capacity is below64;
  independent matching and a vertex-cover certificate agree. This bounds the
  current repair, not all possible C1 readouts or the frequency of failures.
  No GPU scoring, rescue, new cohort or next stage ran.


## D-059 — Separate causal-case identification from monitor readiness

- Date:2026-09-11. Stage7A technically complete,20/20 PASS; recommendation STOP / REPORT.
- Direct evidence:181 strong faithful events,3 wrong-source,1 extraction-error and2 downstream-integration events; no strong prior-fill or stale-source event. Only faithful exceeds24 fresh strong events. All four passive-probe tasks are unavailable under frozen independent-family coverage minima.
- Lesson: rare strictly identified failure cases can support case-level mechanisms while providing insufficient class coverage for a held-out monitor. Preserve the distinction between an unavailable probe and failed classification performance; do not change causal definitions to improve yield.
- Scope: fixed controlled cohort and singleton visual readouts, not natural prevalence. Zero certified cases do not establish absence.
- Evidence: `outputs/stage7a/summaries/stage7a_acceptance.json`, `outputs/stage7a/analysis/paper_claim_assessment.json`, `outputs/stage7a/analysis/monitor_readiness.json`.
- Subsequent user approval: execute Stage7A-Bench to measure natural failure and causal-identification yield before choosing a full cohort. No monitor or intervention has been authorized by these results.

## D-060 — Group benchmark sources by content as well as filename

- Date:2026-09-11. During Stage7A-Bench v2 preparation, two distinct MMLongBench-Doc filenames were found to prescribe the same pinned SHA256 and resolve to identical local PDF bytes. Five frozen native bases had been split into two filename-based families.
- Lesson: successful release-hash verification establishes byte provenance, not independent source identity or question/content correspondence. Merge confirmed content aliases for analysis while preserving immutable native provenance; adjudicate suspected question/content mismatches separately.
- Evidence: `outputs/stage7a_bench_v2/audit/mmlong_duplicate_pdf_diagnostic.json`, `outputs/stage7a_bench_v2/audit/mmlong_duplicate_pdf_review.json`, and `outputs/stage7a_bench_v2/cohort/source_family_overrides.json`. Derived MMLong source families are105, rather than106 filename families; no native rows or inputs were changed.


## D-061 — User-approved reduction to distinct mechanistic benchmark axes

- Date:2026-09-13. Explicit user amendment supersedes the broad remaining Stage7A-Bench v2 queue; this is approved scope, not an inference from a new causal result.
- Preserve Phantom and CharXiv completed evidence. CharXiv64-event pilot remains1 strong wrong-source,6 strong faithful,25 weaker faithful,32 unresolved; do not reinterpret it after testing documents.
- Continue only gated MathWild, MMMU-Pro and MMLongBench-Doc, in that order. Defer MathSight, MicroVQA and MedXpertQA-MM with no further generation/download/review/scoring. Original2376-condition manifests and completed preparation stay historical;984 conditions are deferred.
- MathWild96-review continuation gate uses semantic/source/readout eligibility only: A≥12 localizable failure candidates OR B≥16 properly eligible failure events OR C≥10 interpretable exact paired clean→wildphoto error transitions. No passive/causal-effect-driven continuation, threshold weakening or sample expansion.
- Selection criterion is failure yield × causal identifiability × error-readout validity × intervention relevance with adequate faithful controls. Accuracy alone is insufficient. Sparse strict failures across retained regimes are a valid result; no automatic benchmark expansion, model-scale study or controlled cohort follows.
- Authorized stop: retained sweep/pilots → reduced comparison → exactly one recommendation → STOP. User selects any subsequent monitor/intervention/scale/cohort action.
- Authority: `plan/stage7a_bench_v2_scope_amendment_20260913.md`. Execution evidence: `outputs/stage7a_bench_v2/audit/scope_amendment_queue_cancellation_20260913.json`; resource estimate: `outputs/stage7a_bench_v2/audit/reduced_scope_resource_estimate_20260913.json`.


### D-062 — Fixed MathWild96 semantic gate passes (2026-09-13 KST)

User-approved reduced sweep: all96 primary native photos fully reviewed at a safe completed-worker boundary. Frozen semantic/source/readout evidence verifies19 distinct localizable failure claims on12 bases/families, exceeding unchanged A≥12. B7 eligible/6 bases remains partial and all64 clean/photo transitions remain unmeasured; neither is reported as negative. Continue only the original104-photo+64-screenshot remainder, then the already retained MMMU/Doc sequence. No causal/passive features or effect sizes informed continuation, and gate passage does not admit/certify a causal pilot. Preserve CharXiv/Phantom and all deferred history. Evidence: `outputs/stage7a_bench_v2/audit/mathwild_gate96_semantic_eligibility_096_frozen_v5.json` SHA955cb747c9d6a06b2c68507c51fdb81547429fde113b4635104b7f0b126b45c6 and frozen interim report. This is a plan-execution decision, not a new strategy.


## D-063 — User pause immediately before MMLong launch

- Date:2026-09-14T14:57:37.947199+09:00. Explicit user instruction narrows the current execution boundary to completed MMMU review/report and MMLong launch preparation. It does not authorize crossing into document GPU preflight or native execution.
- Action fulfilled:328 full MMMU reviews, native/paired report, six figures, costs and family nesting;195-ready/5-excluded document release frozen, sources checked,26 CPU tests and full static validation pass. No MMLong registration/dispatch/launch, no causal pilot or next recommendation.
- Broader reduced scope remains preserved beyond this pause: documents, eligible pilots, mechanistic comparison, exactly one recommendation and STOP. Await a future user instruction before launching.
- Evidence: `outputs/stage7a_bench_v2/summaries/mmmu_complete_pre_mmlong_handoff_20260914.md`, `outputs/stage7a_bench_v2/audit/mmlong_prelaunch_static_release_validation_20260914_v1.json`, `plan/stage7a_bench_v2_pre_mmlong_handoff_20260914.md`.


## D-064 — User-authorized MMLong launch with bounded monitoring

- Date:2026-09-14T15:40:20.433983+09:00. User lifted the prelaunch pause, authorized MMLong launch and a few-sample check, then asked the agent to stop monitoring and wait for their return after completion.
- Fulfilled with existing113280/node02/tmux10 four GPUs:32 CPU release checks, allfour GPU preflights and five complete native samples across allfour workers verified. Versioned reference-only memory repair retains all200 frozen rows,195-ready/5-excluded accounting, all physical pages and the byte-identical science body. Initial failed/rejected launches remain in phase evidence.
- Leave only MMLong native dispatcher running; no automatic benchmark, causal pilot or new research recommendation after completion. Agent monitoring stops at this handoff.
- Evidence: `outputs/stage7a_bench_v2/summaries/mmlong_v8_launch_handoff_20260914.md`, `outputs/stage7a_bench_v2/audit/mmlong_v8_first_samples_verified_20260914.json`.


## D-065 — User-authorized per-sample native OOM exclusions

**2026-09-14T16:44:10.236537+09:00: user-authorized per-sample OOM continuation v9 launched in existing113280.13/node02, tmux10 window `mmlong-v9` /pane%22.** Preserve original v8 and its35 dependencies. Replacement workers wait for their own GPU's prior model process to exit; unstarted work is dispatched immediately on available allocated GPUs. Native sample CUDA OOM becomes an explicit unavailable result and causes a clean model-process restart; terminal outputs are reused and OOM samples are not retried. Other errors remain fatal.50 continuation batch registrations replace42 unstarted old queue entries; historical manifests/dispatch/results retained.53 CPU tests passed,15 focused recovery tests passed after the final narrow guard; scientific call ASTs unchanged. Startup verification is in progress. No new allocation or benchmark/pilot. Plan: `plan/stage7a_bench_v2_mmlong_oom_continuation_20260914.md`.

An OOM exclusion is a resource-coverage limitation. Retain it in the original native denominator and report completed-response accuracy separately; never count it as a model reasoning error or causal state. Preserve exact sample identity/traceback/cost and do not proactively exclude other long documents based on this one failure. The direct native OOM is supported by `outputs/stage7a_bench_v2/audit/mmlong_v8_native_runtime_oom_status_20260914_1626.json`; deeper memory cause is unresolved.


## D-066 — User authorizes concurrent MMLong review through reduced-sweep completion

**2026-09-14T23:23:48.776140+09:00: user authorizes MMLong review now, waiting for unfinished generation if necessary, then completion of the reduced sweep.** Review saved full native responses/source evidence without touching live37 v9 dependencies; preserve caps, OOMs, original source ownership and family overrides. Then finish remaining native reviews, eligible MathWild/MMMU/MMLong pilots, reduced comparison, exactly one recommendation and STOP. Execution detail: `plan/stage7a_bench_v2_review_to_completion_20260914.md`. Existing113280/node02/tmux10 only; no new GPU, benchmark or downstream intervention.


## D-067 — Native generation capacity does not certify causal-cache capacity

- Date:2026-09-15. Code-level memory preflight for the sealed MMLong pilot finds root/state/candidate cache cloning can keep three independent KV-cache copies. Two selected native148 prefixes require up to90.229GiB cache plus stored weights, before temporaries, on the existing path; native generation retains fewer copies.
- Evidence: `outputs/stage7a_bench_v2/audit/mmlong_causal_cache_memory_preflight_v15.json` records model dimensions, token counts, exact source hashes and per-event bounds. No actual MMLong causal CUDA attempt occurred; this is a supported static capacity limit, not a measured OOM or causal null.
- Lesson: qualify native and causal memory separately. Preserve scientific membership and explicit resource uncertainty; use an exact-preserving operational memory repair with real model parity checks rather than silently dropping long-document events. Four-GPU layer sharding remains an unvalidated candidate, not an adopted scientific method or new resource authorization.


## D-068 — Exact operational repair is relative to the actual native backend

- Date: 2026-09-15T16:05:01.936417+09:00. Both authorized node02 devices passed exact KV/logit/RoPE and original source/candidate/no-op/repeat mechanics against immutable native document_runtime_v2. CPU cache offload/reload allowed all 42 sealed MMLong events, including both approximately 199k-token prefixes, to complete without changing scientific selection or thresholds.
- Preserve the earlier dense-versus-document full-tensor mismatch. Exact repair parity does not establish dense/document equivalence; verify the backend actually used for native evidence. Evidence: `outputs/stage7a_bench_v2/audit/mmlong_v15_actual_gpu_mechanics_verified.json`, `audit/mmlong_v15_prefix_reference_scope_correction.json`, `audit/mmlong_first199k_event_capacity_verified_v23.json` and completed wrapper under the same output root.

## D-069 — Reduced sweep complete; control coverage qualifies low captured failure yield

- Date: 2026-09-15T16:05:01.936417+09:00. Fixed pilots contain 187 events: 17 strong faithful, 66 weaker faithful, 3 strong wrong-source across three families and 101 unresolved. CharXiv's one strong failure and MMLong's two are preserved positive evidence. MMLong has alternative semantic controls for only 3/15 selected failure events (two bases), and two certify; limited preparation may therefore constrain captured yield. Its two certified cases are a financial table-field error and a chart-binding error within a PDF, not two independent pure document-field mechanisms.
- Do not infer population prevalence or intrinsic natural-benchmark scarcity from these bounded pools, or equate zero assigned PRIOR_FILL/extraction/integration states with comprehensive negative tests. The natural-primary scalable gate is not demonstrated; illustrative scaling from one/two families is not a validated yield forecast.
- Exactly one recommendation: Controlled Confusable-Source Construction anchored to the verified MMLong table-field case. Proposal only; no new action or natural primary frozen. STOP for user review. Evidence: `outputs/stage7a_bench_v2/analysis/selected_benchmark.json`, `analysis/reduced_semantic_control_coverage_v24.json`, `audit/mmlong_certified_case_validity_review_v25.json`, and final acceptance under the same output root.


## D-070 — User authorizes Stage8A2B retrieval/transport calibration

2026-09-16: user explicitly requests `plan/stage8a_plan.md`, including necessary model download, on the existing two GPUs. This authorizes the2B/MathVerse stage despite the previous completed-stage no-follow-up boundary. Use fresh2B native prefixes, its own functional localization and disjoint discovery/confirmation families. The2B model is locally complete; no download. Stage7A-Bench v2 evidence and its unexecuted controlled-construction proposal remain preserved. Reinjection is outside Stage8A.


## D-071 — Stage8A separates retrieval observability from controller readiness

- Date:2026-09-16. Frozen held-out2B/MathVerse retrieval AUROC0.9776, mentionFPR0.1277; paired improvements over lexical/position exclude0. Gate1PASS within selected reviewed prefixes, not whole-trajectory deployment evidence.
- Frozen dual JS/full-span CE weakness yields19 states/18 families (9 held-out), below required24events. Conditional Value semantics remain positive16/16 evaluable states;3 locally wrong claims lack an error-oriented contrast,4 positives are mention-only negatives. Cheap transport models fail held-out ranking (AUROCs0.346–0.425), so passive retrieval detection alone does not supply a validated intervention gate.
- Decision: Stage8A execution complete, overall controller criterion unmet. Exactly one recommendation: stop the Value-reinjection branch under the current calibration and preserve this mechanistic boundary. Do not retune thresholds, switch to the25 JS-only states, flip learned signs, expand the cohort or launch reinjection after seeing these results.
- Scope: selected MathVerse edit-bearing sources and reviewed prefixes, with93,749/1,507,425 tokens reviewed and4 whole trajectories; not a natural failure prevalence estimate. Retained Value semantics in locally correct claims do not demonstrate an accuracy repair opportunity.
- Evidence: `outputs/stage8a/summaries/stage8a_summary.md`, frozen analysis JSONs and `audit/gpu_work_complete_v1.json`. User-requested allocation115046released immediately after final GPU validation; `audit/allocation_released_verified_v2.json`. No follow-up experiment.


## D-072 — User authorizes Stage8B frozen-detector MathVision diagnosis

- Date:2026-09-16. User explicitly requests Stage8B with two GPUs on node03 through Slurm, no tmux. This authorizes a new diagnostic stage after completed Stage8A, not Value reinjection or an intervention.
- Reuse the unchanged joint/max Stage8A detector. First32 examples are the beginning of the frozen3,040-item census order and provide a score-blind transfer audit before scaling. Both actual-device parity checks pass; scientific transfer is untested.
- Preserve all prior evidence and unresolved local truth. A gate failure stops the branch without correctness-label refitting or unapproved recalibration.
- Evidence: approved Stage8B plan, operational checklist/census/annotation protocols, input freeze and actual-GPU parity receipt under outputs/stage8b.


## D-073 — User authorizes revised Stage8B MathVision protocol

- Date:2026-09-17T04:45:34.041860+00:00. Explicit v2 approval supersedes v1: T=1.0, Qwen-compatible prompt/pixels, benchmark answer extraction independent of cap/think termination, completion-controlled outcomes. Latest resource steering selects two GPUs on node03 through Slurm, no tmux.
- Preserve T=0.6 pilot and all old scoring/reviews; exclude it from primary v2 outcomes. A missing final section is not proof of benchmark unscorability. No detector refit.
- Pinned Qwen source confirms full-response fallback and an upstream GPT-4o extraction fallback. Local deterministic/manual extraction records this difference explicitly; no credential/API access. Source: outputs/stage8b/v2/protocol_sources/provenance.json.
- Same32 audit IDs, new traces/reviews required. Slurm116063 pending; gated32-only batch releases on exit. Scientific gates0–5 and full census remain pending.


## D-074 — Revised MathVision pilot supports census feasibility, not causal grounding

- Date:2026-09-18. All32 T=1.0 native outputs and new semantic reviews complete; unchanged detector passes23/23 item coverage,35/38 T alignment and6/62 control false alarms. Review scope49,152/623,719 reasoning tokens, one annotator. No causal certificate follows from this transfer result.
- Local cap-independent scoring plus two ground-truth-blind final-format normalizations yields12 correct/16 wrong/4 unresolved. Three whole-response capped extractions remain ambiguous; one cap interrupts the prescribed post-think section. Cap status is not the grading rule, and upstream GPT-4o extraction is not reproduced.
- Initial census feasibility is met because most responses have labels and both outcomes occur. Larger outcome/local/paired/causal gates remain pending. A bounded continuation must preserve the frozen order and protocol; none was launched during this result check. Full remaining3,008 native examples project8.8–12.3 days on4 comparable GPUs, before later stages.
- Preserve all historicalT=0.6 results and user-cancelled allocation evidence.22-to4 cap reduction coincides with temperature, prompt and pixel changes, so it is not an isolated temperature-effect estimate. GPUs released at batch exit. Evidence: `outputs/stage8b/v2/summaries/transfer32_results.md`, its linked review freezes, scores and resource receipt.


## D-075 — User authorizes bounded256 MathVision discovery checkpoint

- Date:2026-09-18T00:43:40.517336+00:00. Approved Stage8B.1a adds exactly224 next-order native examples to the completed32 T=1.0 audit; no outcome/category selection or rerun of completed examples. Four GPUs/node02 via scheduler-managed Slurm, no tmux. Existing broader census plans are preserved; the immediate execution is bounded to256.
- Evidence D-074 supports a useful bounded sample, while full remaining census would take8.8–12.3 days on4GPUs. Pilot-based native estimate for224 is15.8–21.9h, with48h scheduler headroom and automatic release.
- Frozen model, prompt/pixels, T=1.0 sampling, seed1234,40960 cap and detector remain unchanged. Cap-independent correctness and completion status remain separate. Native passive arrays lack source-specific QK/Value, so later descriptive source/transport measures require bounded observational replay; no causal assay or new native rollout is authorized here.
- Stop after bounded passive/semantic evidence, controlled effects, gates A–D and one go/no-go recommendation. No automatic larger cohort, paired seeds, detector refit or intervention. Evidence: approved plan and `plan/stage8b1a_execution_checklist.md`.


## D-076 — User authorizes Block 0 shared construction

2026-09-19: exactly256 completed native trajectories, four GPUs/node02 through Slurm, no regeneration. The approved Block0 primary episode rule merges up to4 intervening inactive tokens; preserve legacy gap0 summaries and materialize sensitivity gaps0/8 separately. Freeze pooled passive standardization and temporal review membership independently of correctness. Cap-independent extraction and previous32 reviewed outcomes remain unchanged. No scientific comparisons or causal work in Block0. Evidence: plan/stage8b_block0_compute_once_shared_dataset_plan.md and plan/stage8b_block0_execution_protocol.md.

D-076 completion: Block0 is frozen for256 trajectories,2358 primarygap4 episodes and456 temporal review members. All12 required artifacts hashed; no scientific comparisons. Native256 first-prediction R values remain undefined, explicitly masked; all standardized finite pooled feature variances verified. Slurm117930 completed in104s and released. Next blocks must reuse this freeze; the separately referenced Block1 plan is currently absent. Evidence: outputs/stage8b_block0/v1/stage8b_block0_freeze.json and audit/acceptance_checks.json.


## D-077 — User authorizes Block1 whole-trajectory analysis

2026-09-19: execute the newly supplied Block1 plan using two GPUs/node06 through scheduler-managed Slurm. Reuse Block0 labels/episodes/features;4000 item-bootstrap resamples; freeze primary families and confound/matching rules before contrasts. Cap remains independent of outcome. Exactly one interpretation and one Block2 emphasis; no local L labels, detector refit, generation or causal interventions in Block1. Evidence: plan/stage8b_block1_analysis_protocol_v1.md and outputs/stage8b_block1/v1/audit/execution_freeze.json.


## D-078 — Block1 complete: retain null full-control phenotype and local-read handoff

2026-09-19T07:27:35.846492+00:00:134 correct/105 wrong/17 unresolved among256 frozen MathVision items.
Raw count/tortuosity differences exist; count and mean movement survive
length/completion-only controls, but no primary family establishes a robust
difference after all prespecified input controls. All11 full family intervals
include zero; matching64 pairs and normal completion retain uncertainty.
Selected interpretation: no broad outcome-level retrieval difference established,
not equivalence. Do not attribute all attenuation to capping/length or a cause.

Confirmed design limit: all18 capped lengths exceed the normal range;17 capped
outcomes are unresolved and only1 is correct. Cap-adjusted effects extrapolate;
normal-only coefficients nearly duplicate the all-scorable analysis. Keep this
limitation when interpreting completion adjustment in later phases.

Exactly one recommendation: emphasize local L+ versus L− at active task-required
retrieval events across final-outcome groups, preserving frozen membership and
eligibility. No Block2 action executed. Both logical GPU workers completed on
node06 after user placement amendments; rank1 preserved, node03 pendingrank0
cancelled,40 allocatedGPU-seconds and automatic release. Evidence:
`outputs/stage8b_block1/v1/stage8b_block1_summary.md`, interpretation/final freezes,
acceptance checks and resource receipt.


## D-079 — Block2 user approval

2026-09-19T07:54:24.514020+00:00: Execute the supplied retrieval-event/local-read plan using two GPUs/node06. Reuse exact Block0 membership; seal semantic/local/source labels before replay. Respect the24 L− yield limit and item clustering. Record coverage nonidentifiability rather than adding review members. No Block3 or intervention. Protocol: `plan/stage8b_block2_execution_protocol_v1.md`.


## D-080 — Block2 complete: descriptive routing candidate, failure-yield gate not met

2026-09-19T09:08:09.965700+00:00. Exact456 frozen events produced148T/253M/55U and120L+/17L-/11L?. Seventeen failures in16families are below the24-event preferred minimum; do not promote an earliest reproducible divergence claim. Activation primary intervals include zero. The bounded21-event source replay (12failures,9controls) shows weaker target-confuser margins and greater ambiguity in failures, including complete-pair/family-weighted sensitivities. This remains observational and incompletely controlled; no causal source failure or activation-equivalence claim.

All21 captures exactly matched untouched logits and saved native global features. Preserve9 L-/final-correct and62 L+/final-wrong events as post-read follow-up candidates, not established recovery/integration diagnoses. Population demand coverage and continuous source dynamics remain unidentified by this selected sample. One handoff emphasis:post-read recovery/evidence use after weak source separation, only when separately authorized. No Block3 or intervention launched.

Evidence:`outputs/stage8b_block2/v1/stage8b_block2_summary.md`, annotation seal, ordered comparisons and final freeze b12c4588fadd08bb13253b7e4bc96aaf3437a84563ed0f783d86073691f2893e. Slurm118076 used two node06 A6000s for4m49s and released them. Full Block0/1 freezes remain unchanged.


## D-081 — User approves Block3A gated routing confirmation and causality

2026-09-19T10:19:42.774627+00:00. Follow supplied Stage8B Block3A plan using two GPUs/node02. Preserve Block2; supplement native routing inventory, freeze32 items/four new seeds, seal same-subgoal reads, then test within-item replication. Causal weakening/rescue/controls only after yield and replication pass. Finite128-rollout budget; no threshold tuning or automatic Block3B. Protocol: `plan/stage8b_block3a_execution_protocol_v1.md`.


## D-082 — Block3A pre-outcome image-family alias

2026-09-19T10:47:51.339694+00:00. Direct inspection of all32 selected images confirms that1707 and1245 share the same drawing at different resolutions despite different decoded-image hashes. Preserve all original IDs/labels/ROIs and both fixed subgoals; cluster them together for Block3A inference (32 items/31 visual families). Do not assume exact-image hashes eliminate rescaled drawing duplication. Record this before new scientific rollout results, with no cohort replacement or sample expansion. Evidence: `outputs/stage8b_block3a/v1/annotations/image_crosscheck.json`; operational clarification: `plan/stage8b_block3a_family_clarification_v1.md`.


## D-083 — User requests four-node02-GPU continuation

2026-09-19T11:36:19.263618+00:00. Cancelled Slurm118099 at user request;14 complete outputs hash-verified and reused,4 interrupted attempts preserved. Slurm118116 resumes exactly114 remaining item/seed tasks on4 node02 GPUs, two workers/GPU. Model, sampling, membership, anchors and statistical gates unchanged. Artifact union through `audit/active_native_run.json`; no old scientific files rewritten. Resource amendment:`plan/stage8b_block3a_four_gpu_resume_v1.md`.

## D-084 — Block3A complete at insufficient same-item pair yield

2026-09-19T16:15:00+00:00 (2026-09-20 KST). All128 frozen new trajectories reviewed and sealed:79 L+,28 L−,1 L?,20 unmatched. Active-retrieval eligibility leaves62 L+/20 L−; failures span9 families, but seed-disjoint exact-subgoal pairing yields only4 pairs/3 independent families against the frozen20/16 minimum. Thus failure count alone does not establish same-item confirmation feasibility. Independent pairing/alignment checks and740 upstream artifact hashes pass; semantic labels are single-annotator judgments. The reason for limited outcome switching remains unknown.

The prescribed stop is enforced: no new-rollout source replay, routing replication, weakening, rescue, controls, adaptive seeds/items, or Block3B. This is a yield failure, not an observed null routing or intervention effect. Exactly one recommendation: stop routing branch under the current frozen cohort, preserving the original Block2 descriptive evidence. Eight outputs/five figures finalized; GPUs released. Evidence: `outputs/stage8b_block3a/v1/stage8b_block3a_summary.md`, `annotations/semantic_seal.json`, `audit/yield_gate.json`, `audit/final_acceptance.json` under the same stage root.


## D-085 — User approves Stage8C v2 diverse retrieval-triggered visual gain

2026-09-20T02:47:48.058077+00:00. New bounded action explicitly authorized after Block3A stop. Exactly2 node02 GPUs. Freeze dev128/test512 independent visual families; validate two-pass cache/RNG/no-oracle behavior before four-dose development. Conditional held-out/timing/audit and narrowly defined extension only; a negative result stops the branch without launching Block3B. Source plan remains unchanged.


## D-086 — Stage8C v2 technical V3 stop preserves untested scientific scope

2026-09-20T03:15:01.201602+00:00. Two initial validation-harness errors were repaired using native trace
coverage and a focused CPU position-ID reproduction. The third2-GPU/node02 run
118518 reached the numerical visual-decomposition assertion and failed on both
initial prefixes. Preserve the predeclared relative-L2.02/abs.125 bounds; no
further retry or science. Exact failure magnitudes were not serialized, so cause
is unknown. Gain/no-op/cache comparisons preceding the failure do not establish
a complete V1–V6 pass. Frozen128/512 cohorts and prior-stage evidence remain
unchanged.0 scientific trajectories, no dose, no efficacy conclusion;0.1083 GPUh,
all allocations released. One recommendation: bounded decomposition diagnosis
and repair followed by full revalidation. No follow-up or Block3B launched.
Evidence:`outputs/stage8c_v2/v1/stage8c_v2_summary.md` and technical validation.


## D-087 — User authorizes bounded Stage8C-R repair and conditional dev resume

2026-09-20T03:59:20.995385+00:00. Diagnose partition -> head-space -> projection -> residual using saved metrics, preserve strict.02/.125 bounds and native BF16 semantics. Exactly2 node02 GPUs. One supported implementation repair candidate and full V1–V6; only a complete pass permits frozen dev128 calibration. No scientific retuning or automatic Block3B.


## D-088 — Stage8C-R bounded repair fails native BF16 decomposition

2026-09-20T04:21:34.878226+00:00. Eight fixed cases from four families and 4,128 records across original
and full-KV BF16 candidate localize the first failure before W_O. Partition,
GQA, head layout and native replay pass; separate BF16 source sums reach .25
maximum absolute error against the unchanged .125 bound (48/2064 rows in each
implementation). A higher-precision diagnostic improves agreement but cannot
certify the BF16 intervention. Supported localization is split reduction/cast
order, not an exact CUDA accumulator diagnosis or universal impossibility.

Plan section26 requires stopping after the bounded candidate fails. Exactly
one recommendation: stop intervention branch. No fresh V1–V6 pass, dev128,
held-out run, precision change or Block3B. Scientific efficacy remains untested;
all frozen cohorts and historical evidence preserved. Jobs118525/118526 completed,
two node02 GPUs released; approximately .397 GPU-hours. Preserve per-prefix
absolute-error failures even when relative L2 is small.
Evidence: `outputs/stage8c_repair/v1/stage8c_repair_summary.md` and the adjacent pre-W_O audit / forensic Parquet.


## D-089 — User approves direct FP32 Stage8C v3

2026-09-20T04:44:10.787638+00:00. Explicit new plan supersedes BF16 repair, BF16/FP32 transfer work,
detector recalibration and pre-efficacy V1–V6. Both arms use full FP32;
inherited detector/threshold is a fixed policy without a transfer-certification
claim. Reuse byte-identical frozen cohorts and item seeds. Direct four-dose
512-trajectory dev run, then conditional held-out and secondary stages.
Two node02 GPUs via scheduler/Slurm; no precision fallback on OOM.
Source: `plan/stage8c_v3_fp32_direct_retrieval_gain_plan.md`.


## D-090 — User requests four-node02-GPU FP32 resume

2026-09-20T05:07:29.862968+00:00. Cancelled118529 and preserved two interrupted attempts (zero complete).
Resume the identical512-task dev queue on four GPUs with the same FP32 model,
seed/dose pairs, detector, sampling and scorer. No mid-trajectory checkpoint
exists; interrupted tasks restart from original seeds. Operational amendment:
`plan/stage8c_v3_four_gpu_resume_v1.md`.


## D-091 — FP32 visual gain stops at the frozen development no-go

2026-09-22T01:45:25.268824+00:00. User-approved Stage8C v3 completed512 trajectories on128 frozen items.
Reviewed accuracy47.66/46.88/46.09/44.53% for gains1/1.25/1.5/2. W→C/C→W4/4,3/4,3/7;
unresolved answers12/13/14/14. All gains fail plan §18 positive-accuracy and
rescue-balance guards. Stop before held-out; no new doses or cohorts. This is a
negative development result for the current frozen FP32 policy, with mechanism
unknown, not a claim about every retrieval intervention or BF16/FP32 equivalence.

Evidence: `outputs/stage8c_v3/v1/stage8c_v3_dose_freeze.json` and
`outputs/stage8c_v3/v1/stage8c_v3_dev_dose_results_reviewed_v1.json`. All78 masked
extraction exceptions were sealed before gold comparison, with single-annotator
limitations;53 outcomes remain unresolved under the unchanged adapter. Versioned
analysis repair distinguishes closed review from unresolved labels; no-credit
accuracy and unresolved transitions are preserved. Original sources/automatic
results remain intact. Job118545 exited0; all GPUs released.

One recommendation: close the gain branch and return Block3B recovery/wandering
dynamics for the user's next-action decision. No Block3B execution authorized by
this completion; no next experiment launched.


## D-092 — User authorizes Block3B post-read observational lifecycle

2026-09-22T02:35:05.165250+00:00. Execute plan/stage8b_block3b_post_read_recovery_wandering_plan.md on the frozen256-item Stage8B cohort. Preserve148 original T anchors/labels and known image-family aliases. Freeze four primary endpoints and confound controls before new lineage outcomes. Practical masking, explicit unresolveds, family clustering; no generation, intervention, detector refit or adaptive expansion. GPUs, if needed, only on node02/node03/node06, at most4 available total through scheduler/Slurm; none allocated for review. Prior Stage8C stop is motivation, not a diagnosis of downstream failures. Stop after required outputs and one paper-emphasis recommendation.


## D-093 — Block3B completion with limited lineage and symmetric exposure (2026-09-22T03:18:59.890142+00:00)

Approved plan completed at its stop boundary. Observed: all148 T anchors retained;
only27/120 L+ have full symmetric256-token windows. The fully exposed re-retrieval
contrast includes zero; mutation and geometry bootstrap coverage fails the frozen
95% validity rule, and refresh is measurable for one anchor. Three corrections
and two mutations are existence examples, not population rates. Only16 complete
remainder reviews were performed;132 reference reviews leave substantial unknowns.

Promoted lesson: assess actual pre-anchor exposure before treating the nominal
local-read cohort as powered for symmetric geometry. Preserve unknown lineage
and distinguish semantic reinspection from detector-supported refresh or staleness.
Evidence: outputs/stage8b_block3b/v1/stage8b_block3b_summary.md and audit/final_validation.json.
One paper-emphasis recommendation is recorded in audit/paper_recommendation.json;
no new research action was selected or executed.


## D-094 — User authorizes Stage9A matched-scale native regime comparison (2026-09-23T07:38:14.513309+00:00)

Execute the approved Stage9A plan only. Freeze128 unused conservative families, three prompts/checkpoints, primary endpoints, length caliper and semantic/causal eligibility before outcomes. Preserve prior Stage8 stops and all frozen artifacts. At most4 currently available GPUs across node02/node03/node06 through scheduler/Slurm. A positive detector contrast alone cannot support advancement; null or insufficient eligibility remains valid. No later-stage automatic launch.


## D-095 — Stage9A node07 authorization and bounded resource recovery (2026-09-23T07:53:04.025557+00:00)

User adds node07 without changing the four-GPU ceiling or science. Preserve original and effective resource-amended generation configs. First node07 preflight stopped before inference due to observed startup RPC/filesystem wait (underlying service unknown; phase-local diagnosis). Same frozen preflight may proceed on already-authorized healthy nodes as capacity appears. No checkpoint, cohort, precision, prompt or primary endpoint change. No scientific null inferred from infrastructure failure.


## D-096 — Stage9A completed at its negative advancement gate (2026-09-24T06:06:40.819303+00:00)

All128 families across three arms retained;0/4 positive primary Thinking−CoT contrasts. The positive exploratory total-episode contrast coexists with lower per-token density; nine matched pairs and16/16/18 causal events cannot certify a robust arm difference or equivalence. Demand alignment exceeds circular shifts in all arms. Secondary reviewed accuracy45.31/29.69/25.00% (Thinking/CoT/Direct) does not override the mechanism gate.

Promoted lesson: keep total counts distinct from exposure-normalized recurrence, and report actual paired annotation support instead of comparing unpaired arm means as a paired effect. Preserve uncertain calibration, fine-subtype coverage and causal/length precision; no unsupported causal diagnosis.

Evidence: `outputs/stage9a/v1/stage9a_summary.md`, `stage9a_primary_effects.json`, `stage9a_causal_validation.json` and final audit under outputs/stage9a/v1. Exactly one recommendation: stop the Stage9 bottleneck/bypass branch and retain reasoning-conditioned dynamic visual retrieval. No next experiment launched; all GPUs released.


## D-097 — User authorizes Stage9A VAB necessity reimplementation (2026-09-24T06:54:05.843128+00:00)

The new explicit plan tests direct generated-query image-key access necessity, distinct from the negative native-usage pilot. Preserve the pilot; implement paper-specification controlled counting, greedy BF16, all layer/time cutoffs, baseline validity gates and image-cluster inference. No calibration/prompt search or Stage9B rescue. Up to4 available authorized GPUs via scheduler/Slurm; terminal jobs release automatically.


## D-098 — User replaces VAB reproduction with MathVision temporal necessity (2026-09-24T07:03:51.428269+00:00)

Stop D-097 execution; preserve prototype/protocol/four CPU tests with no GPU or synthetic data produced. Execute the newly named dynamics plan on existing128 families and384 native trajectories, retaining original prompts and sampling if no-op parity allows baseline reuse. Cumulative/local/demand interventions use established repo layers19–22; full VAB grid and synthetic primary task are cancelled. Stop after required outputs/one recommendation; no Stage9B launch.


## D-099 — User-approved prospective Stage9A compute reduction (2026-09-24T08:23:11.658176+00:00)

The user amended only resolution/sample allocation before masked scientific analysis. The fixed primary question and intervention semantics remain unchanged. Freeze64 metadata-stratified families,5 coarse cutoffs includingFULL,5 normalized20% windows and one accepted radius16 demand/control pair per eligible family/arm. Preserve128 native families,all annotations and50 readouts. Main1904 distinct continuations plus87 deferred controls;78 old outputs preserved,8 exact matches reused. Reserve64 split32+32; no automatic extension. The seven-item report preceded relaunch. Evidence: plan/stage9a_compute_amendment_v1.md and five amendment artifacts in outputs/stage9a_dynamics/amendment_v1.


## D-100 — Sealed Stage9A main necessity inference (2026-09-26T14:22:11.491964+00:00)

Main1904 continuations complete on64 families; reviewed P1(512/2048),P2,P3 simultaneous intervals all include zero. P2−2.34pp;P3+10.71pp(28 paired families) becomes0 without algebra(21 families). No positive late-necessity or optional-extension gate is satisfied.87 prescribed null-sink controls remain mandatory and queued; this entry does not close the stage.

Promoted lesson: preserve both literal-reviewed and raw extraction effects; raw cutoff2048/P2 have opposite point signs here, and neither supports the positive claim. Keep uncertain output extraction/completion separate from visual-mechanism interpretation.40/50 local shifted controls are after readout and unexposed; report actual causal exposure and family support. Evidence: outputs/stage9a_dynamics/amendment_v1/stage9a_primary_inference.json, audit/local_readouts_secondary.json, audit/main_postprocess_validation.json.


## D-101 — User authorizes bounded model-wide VAB calibration (2026-09-26T16:06:49.530101+00:00)

New Stage9A.3 plan explicitly redirects unfinished prior controls per§27; D-100 control requirement is superseded for the remaining queue, not its immutable main inference or completed controls. Qwen2.5 CoT must pass technical, genuine-CoT, accuracy and positive calibration gates before Qwen3. Freeze32 synthetic images,16 reserve, shared prompt/options, coarse normalized layer/time grid and bootstrap tie rules before masking. No prompt search, Thinking, MathVision rerun or automatic follow-on. Phase memory: workspace/phase_memory/phase_9a3_vab_calibration.md.


## D-102 — Bounded VAB calibration passes; Qwen3 validity prevents transfer inference (2026-09-26T17:10:02.265640+00:00)

Predeclared16-image extension resolves Qwen2.5 calibration at(L,64) on48 images: zero damage21.875pp, selected damage−1.0417pp,99.35% joint stability. Raw extraction and bounded null-sink support the pattern. Qwen3 technical masks pass but FULL accuracy20/64 and CoT56/64 fail. Keep this distinct from evidence for a generation-level visual-access shift; no Qwen3 masked science was run.

Promoted lesson: a validated intervention backend cannot rescue an invalid comparator baseline. Here even treating all18 unscorable outputs as correct leaves38/64<60%, so a censoring-only explanation cannot rescue the observed floor while completed outputs stay fixed. Underlying cause remains unknown. Preserve the shared-cap limitation and do not tune after outcomes.

Exactly one recommendation: separately approve bounded Qwen3 FULL baseline repair/validation. STOP; all GPUs released. Evidence: outputs/stage9a3/v1/stage9a3_summary.md, stage9a3_qwen25_positive_control.json, audit/qwen3_validity_stop.json and audit/final_validation.json.


## D-103 — User authorizes bounded4B baseline repair (2026-09-27T03:22:21.287028+00:00)
Execute Stage9A.4 exactly: same Stage9A.3 task/prompt/scoring,4B-Instruct and prospective512cap. FULL gates precede masked science; native DeepStack unchanged. Follow sequential cutoffs and conditional reserve/control only. D-102 negative2B result and positiveQwen2.5 calibration remain immutable. One recommendation then stop.


## D-104 — Valid Qwen3-4B comparator selects later finite access (2026-09-27T03:45:15.232826+00:00)
Stage9A.4 complete at Outcome B.4B/512 FULL45/64 passes all gates. ZERO26.5625pp damage;64 damage12.5pp;128 damage−1.5625pp CI[−4.6875,0] selects128, with no256/reserve. Paired primary32 Qwen3−Qwen2.5 token64 damage shift15.625pp CI[4.6875,26.5625]. Bounded null-sink128 point damage3.125pp butCI[0,7.8125] crosses5pp; preserve this uncertainty.
Promoted lesson: establishing comparator validity can reveal a later sufficient tested access budget without identifying an architectural cause. Finite access and cross-checkpoint differences are compatible. Do not attribute to DeepStack/capacity/training or overstate null-sink equivalence.
One recommendation: characterize the Qwen2.5→Qwen3 regime shift before Thinking attribution. STOP; no follow-on launched. Evidence: outputs/stage9a4/v1/stage9a4_summary.md and audit/final_validation.json.


## D-105 — User authorizes matched4B native Thinking comparison (2026-09-27T04:31:19.038303+00:00)
Execute Stage9A.5 with frozen CoT reference and native Thinking template, removing only the explicit CoT instruction. Shared task/scoring and512 cap; FULL gates first. Scratchpad candidate options are not final responses. Conditional absolute/relative/control/reserve assays remain bounded; no cap repair without amendment and no automatic follow-on.


## D-106 — Shared standard cutoff with failed redistribution robustness (2026-09-27T04:58:23.950354+00:00)
Stage9A.5 complete. Native4B Thinking FULL58/64 passes G1-G5; standard ZERO
26.5625pp,64 18.75pp and128 1.5625pp [0,4.6875] selects128, matching CoT.
Paired Thinking−CoT128 difference3.125pp [0,7.8125] does not support a prolonged
regime claim. Null-sink128 Thinking damage10.9375pp [3.125,21.875] fails preservation;
paired control difference7.8125pp [−1.5625,18.75] also remains uncertain.
Promoted lesson: retain completion as part of the bounded-performance endpoint
but separate it from local visual-read error. All12 standard64 losses,1 standard128
loss and7 null-sink128 losses are missing final answers at512. Their cause remains
unknown; do not silently increase the cap or present standard-mask sufficiency as
robust to redistribution. No256, normalized assay or reserve gate opened.
Exactly one recommendation: Retain dynamic visual re-access as the main Thinking mechanism and emphasize the dissociation between native causal use and ablation necessity rather than a Thinking-specific VAB claim.
STOP; all GPUs released and no next experiment launched. Evidence:
outputs/stage9a5/v1/stage9a5_summary.md, audit/control_completion_diagnostic.json,
audit/final_validation.json and audit/closeout_verification.json.


## D-107 — Stage10A authorization and eight-GPU ceiling (2026-09-27T09:56:14.122572+00:00)
User authorizes the Stage10A perceptual-to-textual handoff plan and, separately, up to8 GPUs from now on. Reuse Stage9A.5 native Thinking traces; freeze24 independent-image events and8 reserve. Execute fresh text-only and cached image-off blocks before text edits and2x2 gates. The user-approved new mechanism test supersedes the prior STOP for this action only. No CoT/Stage10B or automatic follow-on. Record prefix completion losses separately from semantic errors; no retrospective cap repair.


## D-108 — Text is a causal carrier without a demonstrated phase handoff (2026-09-27T10:45:59.465004+00:00)
Stage10A completes at Outcome C. On24 independent images, fresh text-only
post−pre accuracy rises16.67pp [4.17,33.33], but cached image-off remains20/24
at all three anchors (necessity decrease0 [0,0]). Emit CF text yields13/24
edited-count final answers versus0/24 original/sham; CF−sham score1.417
[1.125,1.667], correct-fact and both attribute directions agree. Eight CF outputs
lack finals at the unchanged512 cap. Post2×2 on12 frozen correct-fact/no-option-
binding images gives text−image−0.333 [−0.833,0.083], no text-dominance support.
Promoted lesson: explicit textual causal influence, fresh text sufficiency and
loss of future direct visual necessity are separable claims. A positive text
edit effect alone cannot establish perceptual phase termination. Here pre
already contains inventories and post edits retain later recounts; neither a
sharp boundary nor a joint edit of all textual carriers was tested.
Exactly one recommendation: retain bounded causal text-carrier influence
alongside native visual-use evidence; do not promote the phase-handoff claim.
Reserve/bridge gates fail; no CoT/Stage10B launched.264 new generations,
0.402 GPUh;16 tests and independent audit pass; all GPUs released. Evidence:
outputs/stage10a/v1/stage10a_summary.md and audit/final_validation.json.


## D-109 — User authorizes prospective Stage10AR localization (2026-09-27T11:48:03.443352+00:00)
The new approved plan explicitly reopens phase localization using earlier frozen
anchors and a successful-reasoning cohort (correct FULL eligibility), while
preserving Stage10A Outcome C. Freeze all anchors before new intervention outcomes;
no repeated full text-edit panel and no post-null anchor search. Use existing
4B Thinking/corpus/native path, up to8 Slurm GPUs and stage compute caps.


## D-110 — Stage10AR supports bounded functional localization; STOP (2026-09-27T12:24:33.595293+00:00)
Prospectively sealed24-image successful-FULL cohort (12 color/12 shape), A0–A4,
no outcome-selected anchors. Necessity decrease P1+29.17pp [8.33,54.17]; text
sufficiency P2+95.83pp [83.33,100]; evidence-resolution P3+41.67pp [16.67,66.67]
and P4+45.83pp [12.50,75.00], all multiplicity-adjusted family-wise95% intervals.
Both attribute directions and deletion-of-one/small-group checks pass; complete-A2
sensitivity agrees. Optional sealed12-image A3 edits follow the new count9/12
versus3/12 original and1/12 sham; signed CF−original+1.00 [0.333,1.583],
CF−sham+1.333 [0.833,1.750], secondary ordinary95% intervals. No reserve used.
Promoted lesson: earlier prospective evidence-resolution anchors can establish
a population-level functional shift in this controlled successful cohort while
Stage10A's later-anchor necessity null remains valid. Do not infer its sole cause,
a universal boundary, text dominance or disappearance of prefill-derived state.
A0 image-off already succeeds17/24; all fresh A0 runs lack finals at512 tokens;
necessity rises A0→A1 before declining. Completion and semantic error remain
combined under the fixed scoring budget. Existing null-sink sensitivity remains
a limitation; no new robustness method was introduced here.
Exactly one recommendation: promote phase-structured multimodal reasoning as the
bounded main framework and next test whether new demand reopens perceptual access
in a controlled recurrent-demand task. Do not launch it automatically.
190 new generations,0.553GPUh including two metadata-assertion failures and
unchanged-ID resume. Six tests, three new technical cases/eight reused cases,
separate arithmetic/provenance audit,11 artifacts/four figures; GPUs released.
Evidence: outputs/stage10ar/v1/stage10ar_summary.md and audit/final_audit.json.


## D-111 — User authorizes Stage10B natural recurrent-demand census (2026-09-27T14:44:35.188730+00:00)
Use all224 existing main native Thinking traces, independent semantic passes sealed
before passive C5 signals. C4 requires B absent from all prior text; source switching
or raw image attention alone never certifies reopening. Census/GO decision only;
no causal follow-on. Primary zeroGPU, optional passive repair≤32 and<1GPUh.


## D-112 — Stage10B reaches frozen Strong GO; causal follow-on remains unlaunched (2026-09-27T15:45:21.767951+00:00)
All224 existing natural Thinking traces retained, no correctness/detector selection.
Two blinded semantic passes sealed before target routing:37 new-demand trajectories;
26 clean candidates (MathVision15, MathVerse11). Pooled yield11.6% [8.0,16.5];
C5 given C1–C4=70.3% [54.2,82.5]. Raw clean kappa0.738; matched availability0.785;
onset36/45/source43/43 pass frozen thresholds. Broader event-union kappa0.108
reflects unmatched nominations and remains an annotation limitation, not erased
by adjudication. All primary cases S1;5 trajectories have secondary S3; no S2.
Promoted lesson: natural tasks supply enough sequential new-demand/passive-re-access
candidates for a bounded causal test, but neither this census nor source switching
establishes causal phase reopening or a complete return cycle.111/224 primary
negatives were already textualized;7 clean semantic demands lacked qualifying
re-access and4 had ambiguous targets. Preserve those exclusions.
Exactly one recommendation: bounded causal reopening on frozen clean cases.
STOP; do not launch it automatically.14 passive repairs,0.016667GPUh, no generation,
all GPUs released. Evidence: outputs/stage10b/v1/stage10b_summary.md and final audit.

## D-113 — Stage10C approved (2026-09-27T16:04:15.191998+00:00)
Execute the frozen natural24-case causal reopening plan:16 primary/8 reserve, local B correctness and native-span NLL, all-layer24-token PRE/POST/source masks. No correctness-based cohort selection; sampled historical continuations cannot serve as exact greedy baselines. Total GPU cap<4h; STOP after exactly one recommendation.


## D-114 — Stage10C mixed evidence fails causal reopening gate; STOP (2026-09-27T16:34:52.824632+00:00)
Frozen 16 natural independent trajectories (8 MathVision/8 MathVerse), five local
conditions each; exactly three reserve-compatible technical cases pass all checks.
Condition-blinded 80 local ratings sealed before mask labels/native-span NLL reveal.
P1 +12.5pp, adjusted interval [−18.75,43.75]; P2 +0.3996 nats/token [0.1447,0.7076];
P3 +6.25pp [−18.75,31.25]; P4 +0.1772 [−0.0133,0.4719]. MathVerse P1/P3 both
−12.5pp; MathVision +37.5/+25pp. Historical-faithful P3=0; deleting small groups
also fails behavioral direction checks. Outcome D; no reserve or optional blocks.
Promoted lesson: passive source-aligned candidates and reduced probability of their
native assertions do not alone establish causal reopening of correct visual reads.
Preserve positive P2 evidence; do not call this a uniformly null intervention result.
Fresh greedy local baseline resolves B in3/16, versus8/16 historical sampled spans;
fixed64-token local budget, branch divergence and retained cache constrain inference.
No diagnosis of the failed behavioral convergence is established, and no universal
impossibility claim follows. All anchors, cohort and endpoint rules stayed frozen.
Exactly one recommendation: stop the reopening branch and finalize the paper around
the established visual-to-text transition plus separate dynamic source retargeting.
Eleven required artifacts/four figure pairs, seven focused tests and final provenance
and gate audit pass.0.120833 allocated GPUh, peak2, all GPUs released. No follow-on.
Evidence: outputs/stage10c/v1/stage10c_summary.md and audit/final_audit.json.


## D-115 — Stage11A approved (2026-09-28T01:29:57.971133+00:00)
User authorizes the bounded visual-evidence bottleneck census after preserved Stage10C OutcomeD. Start with image/question-only E* construction, two independent sufficiency passes and strict annotation sealing before outcome joins. Probe capability is demand-conditioned recoverability, not proof of encoding; native trace absence is not hidden-state absence. Maximum192 probes, optional12-family text-only pilot, hard2.5GPUh. No automatic full Equal-Evidence Oracle/Stage11B.


## D-116 — Stage11A insufficient clean bottleneck localization; STOP (2026-09-28T03:44:11.667130+00:00)
All128 families/384 native traces preserved;61 image/question-only E* sets sealed
before outcomes.183 native labels sealed before183 short probe reviews;32-family
independent agreement and chronology/provenance checks pass. Raw fine kappa0.886,
coarse1.0. Thinking accuracy25/61 versus CoT17/61; paired gain13.1pp,95% interval
[0.0,24.6]. Only4/12 forward discordances uniquely localize: availability1,
native access1,downstream2;8 mixed. Reverse4/4 mixed. Frozen NO_GO because4<8
informative families, despite passing eligibility and agreement. Optional pilot
skipped; no Stage11B. Probe recovery16/61 Thinking versus18/61 CoT is measured
under a512-token cap hit by57/61 Thinking,24/61 CoT and0/61 Direct responses.
This budget asymmetry limits recoverability claims; it is not evidence of absent
encoding or a causal explanation of Thinking. Preserve both the accuracy gain
and negative feasibility evidence. Exactly one recommendation: stop the bottleneck
branch and finalize the established causal retrieval/visual-to-text lifecycle
claims. No automatic paper or research follow-on.14 artifacts/four figure pairs,
12 focused checks and final audits pass.0.450278GPUh including import failures;
all GPUs released. Evidence: outputs/stage11a/v1/stage11a_summary.md and
audit/completion_audit.json; audit/final_numeric_and_presentation_review.json.


## D117 — Stage11B approved discovery and conditional oracle (2026-09-28T06:12:22.593884+00:00)

User explicitly approves the Stage11B plan despite historical11A NO_GO. Freeze128 harder fresh families,6 candidate strata and dual blinded E* reviews before opening outcomes; common16384cap/greedy avoids post hoc mode-specific cap repair. Execute discovery gate first; no large oracle without GO. Target<6/hard8 allocated GPUh; all optional Direct/probe arms omitted. Protocol: outputs/stage11b/v1/stage11b_equal_evidence_spec.md.


## D118 — Stage11B source-only execution pruning (2026-09-28T07:19:41.213992+00:00)
Before opening new native answers/correctness, two independent reviews and one bounded8-item representation repair froze49/128 E*-eligible families. Five of six original strata cannot meet40% eligibility; only levels3–4 (36/88) remains possible. Preserve all128 families,256-task manifest,16 complete outputs and partial attempts; stop calls that cannot change selection. Resume66 required original comparisons plus6 original batching fillers under identical models/prompts/greedy16384/batch4. This is compute pruning by frozen source eligibility, not individual outcome selection or a GO decision. Four finite90minute shards keep total allocation envelope7.4075GPUh under8. A logical early rejection is allowed only when even all unobserved eligible results cannot supply the original12 forward discordances; missing outcomes stay unknown. Evidence: outputs/stage11b/v1/audit/source_pruning_compute_record_v1.json; source_feasible_tasks.json; audit/logical_futility_policy_v1.json.


## D119 — Stage11B discovery gate cannot pass; STOP (2026-09-28T08:36:21.424232+00:00)
128 source-blind families and dual semantic reviews yield49 E*-eligible. Five
frozen strata fail40% source eligibility. The remaining levels3–4 rule has36/88
eligible; after27 Thinking and31 CoT outputs receive no credit, even all missing
results cannot produce more than9 of the required12 forward discordances.
Granting one explicitly flagged ambiguous extraction favors Thinking but raises
the bound only to10. Unknown outputs are not imputed as wrong; no full-stratum
accuracy or sequential significance claim is made. No held-out/oracle experiment
was launched and Claim3 remains unresolved.68 completed native outputs and all
partial attempts are preserved;61 capped/no-final. Batch4 replay reproduces8/8
prefixes, but single-item prefixes diverge; noncompletion cause remains unknown.
This observation does not negate Stage11A's13pp native advantage or identify an
upstream/downstream mechanism. All10 Slurm jobs terminal,5.499444GPUh.
Exactly one recommendation: keep Thinking-vs-CoT discussion-level and finalize
the established causal retrieval/visual-to-text lifecycle claims. Recommendation
not executed. Evidence: outputs/stage11b/v1/stage11b_summary.md;
audit/logical_stop_decision.json; audit/final_closure_audit.json.


## D120 — Stage11C explicitly approved (2026-09-28T11:25:51.381951+00:00)
Primary comparison changes to Thinking versus Instruct Direct as requested in the new plan; prompted CoT is a conditional same-checkpoint control. Use Stage9A/11A only for source-rule development, fresh level2–4 confirmation, dual blinded evidence review and batch1. Prior Stage11B evidence remains valid for its frozen regime; its noncompletion cause is unresolved. No new benchmark search, cap rescue or follow-on without a new instruction. Hard8 allocated GPUh.

## D121 — Stage11C completion gate stops Claim3 localization (2026-09-28T13:51:23.239244+00:00)
Stage11C COMPLETE / prescribed technical STOP (2026-09-28T13:51:23.239244+00:00).250 sources reviewed twice,120 eligible;80 primary/40 reserve sealed before outcomes.48 calibration calls and32 native completion-gate calls preserved. Native cap hits Thinking16/16,Direct15/16 at8192; remaining128 native calls, oracle and conditional blocks NOT_RUN. P1–P3 NOT_ESTIMATED; Claim3 unresolved. All GPUs released;3.583889 allocatedGPUh. No follow-on launched.
The batch1/common-cap protocol still exhibits severe noncompletion; cause is unknown. A failed technical gate is not a null mechanism effect. Preserve raw annotations, completed traces and unknown outcomes; no selective rescue. Keep Thinking-vs-Instruct as an unresolved performance observation and finalize the paper around the established causal retrieval and visual-to-text lifecycle claims. Recommendation not executed. Evidence:outputs/stage11c/v1/stage11c_summary.md;stage11c_native_gate.json;audit/closure_validation.json.

## D122 — Stage11C-R technical repair explicitly approved (2026-09-28T14:14:19.162976+00:00)
Reconstruct historical completion-valid protocols, freeze12 technical known-good calls, and validate on the original12 nonprimary technical cases before the unchanged80-family scientific rerun. Sampling/backend/state differences are candidates, not diagnoses. No correctness-based protocol selection, family/E* changes or pooling invalid generations. Prior Stage11C STOP preserved; new approved plan hard9GPUh.

## D123 — Stage11C-R historical repair reproduces but assay validation stops (2026-09-28T15:28:03.193796+00:00)
Stage11C-R COMPLETE / prescribed nonprimary technical STOP (2026-09-28T15:28:03.193796+00:00). Historical12/12 replay exact; bounded sampling-only diagnostic resolves2/2 greedy loop/cap cases. Original12 nonprimary families×T/D at recovered40960cap yield Thinking1/12 and Direct4/12 cap hits; completion gate fails. Frozen80 primary/40 reserve/E*/subsets unchanged,160 primary calls and oracle/controls NOT_RUN. P1–P3 NOT_ESTIMATED. All GPUs released;5.875278 allocatedGPUh. No follow-on launched.
Input tensors match exactly; sampled eager historical recipe restores all12 selected traces token-for-token. Sampling-only SDPA diagnostic resolves both fixed greedy loops, without correctness selection. The original nonprimary pool still fails completion at the recovered historical budget; selected known-good reproduction cannot substitute for assay validity. No scientific performance/oracle result or new mechanism claim. Recommendation: Close the Thinking-performance mechanism branch and finalize the paper around Claims 1 and 2. Not executed. Evidence:outputs/stage11cr/v1/stage11cr_summary.md;stage11cr_nonprimary_validation.json;audit/closure_validation.json.

## D124 — Official Qwen baseline validation authorized (2026-09-28T15:45:47.706454+00:00)
User explicitly approves source audit and frozen12-case model-specific sanity check, not Claim3 rerun. Stage11CR historical replay does not establish benchmark faithfulness. Freeze official protocol before outputs; hard3GPUh; conditional at-most-three one-factor variants; no accuracy selection.

## D125 — 2026-09-28T16:27:34.723462+00:00: Official MathVision baseline audit closed
OFFICIAL_PROTOCOL_STILL_INVALID. Official fixed12 sanity: Direct 7/12 committed finals, 5 caps, 5 repetition pathologies; Thinking 12/12 finals, 0 caps, 0 pathologies. Allocated 0.571111 GPUh; all stage GPUs released.
Conditional ablation NOT_RUN.
Direct official recipe includes canonical Hint/Question/Choices, temperature0.7/top-p0.8/presence1.5/cap32768; old recovered recipe used raw question,1.0/.95/presence0/cap40960. Runtime and prompt also differ. Completion-only evidence does not uniquely attribute historical loops. Source/audit/result evidence: outputs/qwen3vl_official_eval/v1/qwen3vl_official_sanity_summary.md. No Claim3 rerun authorized by this result.

## D126 — 2026-09-29T06:54:37.096473+00:00: Stage12A pilot explicitly approved
New61-family same-Instruct E/D/C pilot authorized by plan/stage12a_multimodal_lost_keys_pilot_plan.md; earlier NO_GO results remain historical. Preserve157 E* facts,12 deterministic technical cases,128/16/8192 caps,target2.5/hard4GPUh. Source preflight finds37 open-ended questions incompatible with universal option-letter contract. Clarification requested before prompt freeze/generation; no families dropped or choices invented.

## D127 — 2026-09-29T07:07:33.872924+00:00: Prospective Stage12A native-answer specification repair approved
User explicitly approves MCQ option letters and open-ended native values/expressions for D/C, preserving all61 families,E*,caps,technical IDs and numerical gates. Repair occurred before Stage12A generation/outcome inspection; original plan/source manifest preserved. Evidence: outputs/stage12a/v1/audit/spec_versions/output_contract_v2.json. Open-ended grading retains frozen stage8b/v2_scoring.py equivalence.

## D128 — 2026-09-29T07:45:21.991573+00:00: Stage12A technical gate blocks scientific interpretation
Prospectively approved native output formats retained all61 families/157 E* facts. On the fixed12 technical cases, one plan-permitted output-only wording repair improves D compliance1→9 but misses>=10 and leaves3 calculations (>1 allowed). C has8 finals (<10),4 caps (>2),6 severe cycles (>1). E11/12 passes. Correctness remains unopened, remaining49 not run, scientific P1–P4/GO/NO-GO not evaluable.0.500278 allocatedGPUh, all released. Preserve this as technical validity evidence; do not convert noncompliance into a Lost-Keys null or relax gates after outputs. Root cause unknown. Evidence:outputs/stage12a/v1/stage12a_summary.md. Exactly one recommendation is recorded there and not executed.

## D129 — 2026-09-29T08:11:49.348221+00:00: Stage12A-R explicitly approved
Execute the bounded same-checkpoint D/C contract-validation plan. New D64 and exactly C0/C1 at32768 are prospective user-approved condition definitions; historical Stage12A technical stop preserved. Freeze disjoint12 validation families before generation; all61/E*/images retained; no correctness, no E search, hard2.5GPUh, no automatic scientific rerun. D failure stops before conditional C development.

## D130 — 2026-09-29T08:21:35.016310+00:00: Stage12A-R stops at fixed D development gate
The approved silent-solve D64 condition yields0/12 strict format-valid,3 committed finals,9 caps,6 substantive visible-reasoning responses,0 severe repetition. All12 actual input/output receipts verify. Cause remains unknown; technical gate failure is not a Lost-Keys null. Plan section15 stops before C0/C1 or fresh validation; all61 families/157 facts preserved, correctness unopened,0.123333 allocatedGPUh, all released. Evidence:outputs/stage12ar/v1/stage12ar_summary.md. No scientific rerun or further wording/budget search launched.


2026-09-29T10:01:16.852096+00:00
## D131 — Stage12B explicitly approved
Native4B E/N/O profile on preserved61/157; drops AnswerOnly. Exact question/facts retained, source-only oracle review61 plus random13 second pass. Frozen12 technical gate before correctness; hard8GPUh. No CoT/Thinking or follow-on.


## D132 — 2026-09-29T10:18:02.228368+00:00: Stage12B technical gate stops failure profiling
All61/157sources preserved;4B Instruct E/N/O fixed12 yields E12parseable,N12finals/O11finals,zero caps and normal stopping on all36calls. Severe semantic cycles N4/O3 exceed<=1 gates, despite eventual final commitment; causeunknown. Complete receipts verify actual image/native and image-free oracle inputs. Long advancing enumerations are retained as nonsevere. Scientific correctness remains unopened;147conditional calls NOT_RUN, no B1–B4/P1–P6 estimates.0.389167allocatedGPUh, both jobs released. Evidence:outputs/stage12b/v1/stage12b_summary.md. Exactly one recommendation: repair native/oracle assay before scientific interpretation/additional conditions; not executed.


## D133 — 2026-09-29T10:31:17.831561+00:00: Stage12B-R validity repair explicitly approved
User approves prospective input/scoreability criterion on12fresh families,with R1–R5 behavior retained. Original12 become development/audit only; no correctness used. Preserve all61/157/model/prompts/runtime,36calls/hard1GPUh. Full profiling requires separate authorization under section21.


## D134 — 2026-09-29T11:01:30.232324+00:00: Prospective pathology-aware validity passes on untouched families
Stage12B-R inputs12/12 in E/N/O, scoreable12/11/11, pre-outcome truncations0/1/1. Four caps include two oracle outcomes with surviving explicit commitments; cap-hit alone and R1–R4 are not valid automatic exclusions under the frozen repair. Native/oracle severe repetition8/7 of12 remains data, with correctness unopened and cause unknown. All192 Stage12B artifacts preserved. No protocol tuning or scientific profiling. Section21 requires separate authorization before remaining Stage12B calls; original61/157/P1–P6/B1–B4 and exclusion-of12/24 sensitivities remain fixed. Evidence: outputs/stage12br/v1/stage12br_summary.md; audit/manual_validation_decisions.json; audit/closure_validation.json.


## D135 — 2026-09-29T11:15:30.604027+00:00: Stage12B-S full scientific profiling explicitly approved
The new plan authorizes111 remaining calls and first correctness opening after generation and integrity review. Reuse72calls from24technical families; preserve61/157,model/runtime/prompt/caps/seeds and Stage12B-R validity. Primary complete-profile failures exclude technical missingness; arm-separated scoring and prospective ambiguity/random audits required. No automatic CoT/Thinking. Hard7GPUh.


## D136 — 2026-09-29T12:06:58.975823+00:00: Stage12B-S profile is informative with qualified upstream labels
The frozen 61-family main profile passes:29/57 scoreable native failures,26 complete failure profiles, B1/B2/B3/B4=11/1/3/11 and oracle rescue12/26 (46.2%, Wilson95%28.8–64.5). Four B1 and four B4 families contain unresolved/underspecified evidence without an explicitly incorrect atom, so E− and operational B1 do not establish a visual misread. B2=1 cannot support a substantial Lost-Keys prevalence claim; B3=3 is imprecise. The fresh37 sensitivity has18 native failures and is PROFILE_SPARSE; retain main61 as preregistered. Labels/denominators sealed in order,103 second reviews and3 adjudications preserved; same-agent QC is not independent reliability. Exactly one plan-prescribed recommendation: freeze labels and test prompted CoT/native Thinking selective rescue on the same families. Not launched. All GPUs released;1.467222 new GPUh. Evidence:outputs/stage12bs/v1/stage12bs_summary.md and audit/final_verification.json.


## D137 — 2026-09-29T14:05:06.737812+00:00: Stage12C selective rescue explicitly approved
Execute plan/stage12c_selective_rescue_cot_thinking_plan.md with sealed Stage12B-S labels, C/T on all61, identity-only12 sanity gate, primary B1/B4 and descriptive B2/B3, no E/N/O rerun.122 maximum calls,target<6/hard8GPUh. Historical4B Thinking artifact uses greedy512 on synthetic tasks while section8 lists sampled40960; clarification requested prospectively, before C/T generation.


## D138 — 2026-09-29T14:16:38.768198+00:00: Stage12C Thinking recipe prospectively clarified
User explicitly approves sampled40960 for pinned4B Thinking,temperature1.0/top-p.95/top-k20/repetition1/presence0. Inheritance excludes task-specific synthetic counting greedy512. No Stage12C generation existed; retain sealed sanity IDs, labels, prompt definitions and family seeds. Proceed with12-family C/T technical sanity gate, then conditional remainder under approved plan. Evidence:outputs/stage12c/v1/audit/thinking_recipe_resolution.json.


## D139 — 2026-09-29T14:56:56.684411+00:00: Stage12C stops at pre-outcome truncation gate
The prospectively approved4B Thinking sampled40960 recipe yields12 valid inputs,10 scoreable final responses and2 pre-outcome caps on the frozen identity-only12 families. The cap maximum is1; C passes with11 scoreable/0 caps. Repetition remains descriptive and is not a stop criterion. The98 conditional calls are not launched, correctness remains unopened, and scientific rescue is not evaluated. This is technical validity evidence, not a sparse-rescue finding; cause unknown. All1742 historical artifacts unchanged, both Slurm allocations released,0.703611 GPUh. Evidence:outputs/stage12c/v1/stage12c_summary.md and stage12c_technical_sanity.json. Exactly one recommendation: separately approved technical validation before a rerun; not executed.


## D140 — 2026-09-29T15:31:08.975677+00:00: Stage12C-R explicitly approved and frozen
Decouple49new CoT calls/science from12same Thinking cap-only81920 completion validation. Fresh12 hash/answer-type selected before generation; only phase1pass unlocks it. Preserve1979historicalfiles. Inherited full C gate61/51/5 retained prospectively. No T correctness, no further cap/search. Evidence:outputs/stage12cr/v1/audit/prospective_freeze.json.


## D141 — 2026-09-29T17:24:53.590583+00:00: CoT rescue sparse in frozen native-failure strata
Stage12C-R reuses12C and generates49once. All61inputs valid,57scoreable,3pre-outcome caps; frozen B1=11 yields1/10scoreable rescue with1missing, B4=0/11. Selectivity+.10 with4000familybootstrap95%[0,.30]; paired54 has3rescues and3regressions. All26trace annotations sealed before C correctness,61blind first scores and47 separate-pass reviews retained. The sole rescuedB1 trace contains conflicting evidence, giving0TRACE_E_FULL rescues. No B4 rescue supports a convergence-repair bridge. Exactly one recommendation: keep Stage12B-S as main Claim1 and stop CoT rescue. Evidence:outputs/stage12cr/v1/stage12cr_cot_summary.md. No new experiment launched.

## D142 — 2026-09-29T17:24:53.590583+00:00: Extended Thinking completion validates, without a pure-cap attribution
Frozen cap-only81920 recipe gives12/12scoreable and0caps on original12, then11/12scoreable and1pre-outcome cap on prospectively hash-selected fresh12. THINKING_REGIME_VALIDATED under the frozen input/scoreability gates, with no repetition exclusion and no task correctness. Severe repetition12/12original,10/12fresh remains data. Previously capped2198/3011 now finalize but diverge beforeoldcap;2864also diverges. Nine other trajectories match exactly; underlying divergence cause unknown, no tuning. Thus validated completion does not establish Thinking accuracy or a pure output-budget explanation. Section27 required Stage12T-S draft is created, pending separate authorization. Evidence:outputs/stage12cr/v1/stage12tr_summary.md. Total new stage compute2.599167GPUh, allallocations released.


## D143 — 2026-09-30T02:39:01.377307+00:00: Stage12T-S visual-evidence rescue explicitly approved
The user names the new visual_evidence_recovery plan, superseding the earlier draft. Exactly37new+24reusedT calls;61families/157facts/labels fixed. Technical and26trace annotations sealed before T-only scoring; inherited61/51/5full gate retained prospectively. Frozen primary rescue/evidence-link thresholds and4000familybootstrapseed120220260929. S2 includes actual earlier technical exposures in lineage, including official baseline audit; never-run selection is not exposure. No decoding search or automatic follow-on. Evidence:outputs/stage12ts/v1/audit/prospective_freeze.json.


## D144 — 2026-09-30T06:51:44.124135+00:00: Thinking rescue meets downstream signal, not the visual-recovery threshold
Stage12T-S completes61 families (24 reused,37 new):61input-valid,59scoreable,two pre-outcome caps; all missingness/26trace labels sealed before T correctness. B1=3/10scoreable, B4=5/11; selectivity−.1545,4000familybootstrap95%[−.5455,.2727]. Only two B1 T-only successes and one T-only FULL-evidence case (2007, unresolved-only subtype); explicit-wrong B1 FULL rescues=0. All five B4 rescues also fail under CoT. Operational THINKING_DOWNSTREAM_SIGNAL does not isolate a downstream mechanism: checkpoints/recipes/budgets differ. S1 B4=3/8; S2=0/2 with tiny untouched strata. Long-trace annotation coverage is documented and partial, and same-agent second-pass agreement is not independent reliability. No label/gate relaxation. Exactly one recommendation: Thinking Equal-Evidence Oracles on rescued B4 families; not executed. Evidence:outputs/stage12ts/v1/stage12ts_summary.md and audit/final_verification.json. All16 artifacts/five figure pairs complete,2,828 historical files unchanged,1.531944newGPUh,allthree jobs released.


## D145 — 2026-09-30T10:02:22.981937+00:00: Stage12U-S reasoning-state transfer approved
Use the exact five frozen B4 and two B1 C−T+ families. Freeze answer-safe canonical prefixes and evidence/derivation states before image-free assistant-prefix continuation. Validate on two disjoint identity-hash-selected families. No source regeneration, decoding search or hidden-state experiment; three seeds, target<5/hard7GPUh. D144 supports cohort selection, not mechanism attribution.

## D146 — 2026-09-30T12:35:46.064019+00:00: Thinking-generated text supports portable state production on the frozen cohort
Stage12U-S meets STATE_PRODUCTION_SIGNAL: primary R_T→T5/5,R_T→I4/5,production support4/5; Q→I0/5,both shuffled panels0/5. Three seeds,>=2/3 family success; two secondary B1 families support production descriptively. Strict utilization/repair0/5 is not exclusionary: no primary CoT source met the adequate-state prerequisite, and control/corresponding Instruct outcomes preclude repair support. Four pre-answer caps remain missing. Useful text portability does not certify every deduction or prove production is the sole cause; n5 selected families and intended checkpoint-specific recipes limit generalization. Evidence: outputs/stage12us/v1/stage12us_primary_inference.json, stage12us_summary.md, audit/final_verification.json. Exactly one recommendation is frozen in stage12us_decision.json; no follow-on launched.

## D147 — 2026-09-30T13:15:23.120728+00:00: Stage12V-S localization explicitly approved
Use four U-S production-support families and unchanged Thinking sources; freeze semantic steps/categories before new replay, replicate P0/Pm, then bounded binary localization and content controls. D146 supports portability but not exclusive production mechanism. Preserve991 descriptively. Exact original plan and7GPUh hard budget; no source regeneration or hidden-state follow-on.

## D148 — 2026-10-01T10:13:16.824965+00:00: Prefix-search transitions do not establish necessary single-step portability
Stage12V-S replicates full-prefix usability4/4,localizes two adjacent search transitions,retains one nonmonotonic and one missing-boundary family,and yields0/2 eligible joint causal signatures. Fresh-seed DROP uses exactly the same input tokens/prompt/recipe as the earlier before-prefix but succeeds2/3 and3/3 versus1/3 in search;do not treat the search majority threshold as replicated content necessity. Both critical steps repeat earlier propositions;automatic novelty flags are not semantic proof. E*-only remains majorityincorrect and optionalE*+step0/3 both,which does not rescue the failed necessity gate. DecisionPORTABILITY_NONMONOTONIC carries the explicit one-family missingness caveat;not a prevalence or hidden-state claim. Evidence:outputs/stage12vs/v1/stage12vs_summary.md,audit/deletion_replication_identity.json,audit/final_verification.json.162calls,156scoreable/six missing;46same-agent QC;5,219 prior files unchanged;2.405556GPUh/all GPUs released. Sole recommendation is in stage12vs_decision.json;not launched.


## D149 — 2026-10-02T03:55:28.592498+00:00: Stage12W-S completion budget reconciled and explicitly approved
Original8GPUh ceiling could not be verified after stalled-job cleanup records were purged. User approved≤3additionalGPUh and14total; original source/conditions/seeds/caps/no-retry rule unchanged. Three never-started Ccalls executed once; four interrupted calls remain missing. Resource accounting retains conservative historical bounds and explicit worker/queue bounds for two subsequently purged E records. Final resumption upper1.1736GPUh,totalupper11.3019GPUh. Evidence:outputs/stage12ws/v1/audit/resource_amendment_approved_v1.json,stage12ws_resource_accounting.json.

## D150 — 2026-10-02T03:55:28.592498+00:00: Local derived-state effects do not establish distributed construction
Stage12W-S completes four selected families/seven paired seeds. Full-prefix advantage replicates3/4; derivedaddition anddeletion jointly pass2975/2908(2/4),belowthe3/4globalgate. No singleblockloss≥3/7; fixed backwardelimination leavesB7alone6/7inbothsearchedfamilies,notglobalminimality. Composite losses cannot establish distributed necessity: nearest low-importance control lengths are0.371/0.567of targets,belowfrozen0.8–1.25; other controls unavailable. Order effect0/4. Frozen750naturalprefixpanel4/7→5/7→6/7doesnotreplicatetheearlierinterference/repairpattern. DecisionUNRESOLVED preserves localpositivecontent evidence andlengthconfounding,notaclean null. Exactly one recommendation: Retain Stage12U-S as the strongest supported production result and stop fine externalized-state localization while the block-level mechanism remains unresolved. NOT_LAUNCHED.420slots,416raw,411scoreable,ninemissing,101same-agentQCchecks;6,709priorfilesunchanged. Evidence:outputs/stage12ws/v1/stage12ws_primary_inference.json,stage12ws_summary.md,audit/independent_final_verification.json.


## D151 — 2026-10-02T10:00:25.475655+00:00: Stage12X-S source pool fails before scientific generation
Historical exclusion removes2336items and leaves659fresh families. Metadata-hash selection sealed96initial+32reserve before source-only review;64+19=83 are provisionally E*-eligible.45 source exclusions include41 text-complete tasks; a narrower33-case second reread alone bounds the maximum eligible pool at95. Preserve this as source feasibility, not sparseB4 or nonreplication. Plan section6 restricts replacements to frozen reserves, now exhausted. Exactly one proposal: up to64additional candidates in unchanged pre-outcome hash order, stopping at96eligible afterQC; not activated.0modelcalls/0GPUh;10,002priorfilesunchanged. Evidence:outputs/stage12xs/v1/stage12xs_summary.md.

## D152 — 2026-10-02T10:33:36.254919+00:00: Stage12X-S approved source amendment resolves preflight
User explicitly approves at most exactnext64 fixed hash-order candidates. Source-only review stops at96final-QC-passed families after28extensions(14accepted), replacing one original provisional ambiguity.193facts frozen;36approved candidates unused. Original96+32 manifests and shortfall preserved. No model outcomes used. Resume originalStage12XS A/B/C gates under unchanged14GPUh hard limit. Evidence:outputs/stage12xs/v2/audit/final_source_seal.json.

## D153 — 2026-10-02T12:02:42.052901+00:00: Fresh candidate yield is insufficient for held-out portability testing
Stage12X-S completes the approved amendment and scientific stop rule: exactly 96 final-QC-passed source families; 28 extension candidates reviewed, 14 accepted, 36 unused. A has 39 complete native failures, B1/B2/B3/B4=13/3/3/20 and oracle rescue16/39 (all scoreable N−/O pairs17/41). All20 B4 families screened once: C2/15 scoreable with5missing; T2/20 with0caps. Paired transitions11both-fail,2C-only,2T-only,0both-success,5technicalmissing. Only2888/936 satisfy C−T+; K2<3 forces HELDOUT_CANDIDATE_SPARSE. No PhaseC prefix/replay or portability-null claim. Same-agent QC127, source/history hashes unchanged,328calls,4.218611GPUh,allGPUsreleased. Sole recommendation: harder fresh E*-annotated cohort to increase B4 Thinking-only yield before re-testing portability; not launched. Evidence:outputs/stage12xs/v2/stage12xs_summary.md, stage12xs_decision.json and audit/final_verification.json.


## D154 — 2026-10-02T17:22:14.889243+00:00: Stage12Y-S whole-cohort role decomposition approved
User explicitly authorizes Stage12Y-S on the exact source-frozen X-S96, superseding automatic pursuit of any earlier recommendation. Reuse Instruct E/N/O as historical screens;288newThinking evidence/native/equal-evidence calls, fresh-seed3-replicate role confirmation, then gated image-free equal-evidence state transfer5seeds. Intended variant-specific recipes/caps32768/81920 remain explicit; historical E_I256cap is preserved and disclosed. No one-run role claim, formal mediation, latent-access-absence inference, or pure Thinking-switch claim. Target<12/hard16GPUh and exactlyone final recommendation. Evidence:outputs/stage12ys/v1/stage12ys_role_decomposition_spec.md and audit/preflight.json.


## D155 — 2026-10-02T19:43:43.211610+00:00: Stage12Y-S role confirmation remains unresolved despite local positive evidence
The exact X-S96 paired study completes640new calls. Descriptive native gap+3.45pp(n87) versus equal-evidence+13.98pp(n93) is not mediation. Fresh role support is1/5access,8/15downstream(one unknown; bounds53.3–60.0%),belowfrozen60% gates. PhaseC supports2888/2066 only:2/8entered,2/6resolvedcontrols;381stateunknown,1694replayfails. Preserve local portability and downstream successes without promoting a broad role claim. Missing caps are never scientific errors; clear off-task shuffled finals are scientific behavior. Same-agent177secondreviews are not independent reliability.18artifacts/5figurepairs,11,478historicalfilesunchanged,10.914911GPUh,20jobsreleased. Exactly one recommendation: Stop role-mechanism expansion and retain the narrower supported claims about evidence bottlenecks and developmental state portability. NOT_LAUNCHED. Evidence:outputs/stage12ys/v1/stage12ys_primary_inference.json and reports/stage12ys/v1/index.md.


## D156 — 2026-10-03T15:49:02.764385+00:00: Full-cohort Stage13A confirmation explicitly approved
User authorizes576fresh equal-evidence calls on exactX-S96 after D155's selected-panel gate failure. This supersedes the prior STOP for this specified stage only. All cohort/prompts/E*/golds/checkpoints/model-specific recipes/caps fixed. Prospective optional24 selection and analysis/missingness/QC rules frozen before generation. No negative-result subgroup/prompt search; exactlyone recommendation at completion,notlaunched. Target<10/hard14GPUh.


## D157 — 2026-10-03T18:06:29.900363+00:00: Equal-evidence Thinking advantage survives full-cohort confirmation
Stage13A frozen96/threefreshseeds:84 complete families,+11.11pp,95%familybootstrap[5.56,17.06],passing all gates.32k-comparable82:+11.38pp[6.10,17.48];full96 missingness bounds[9.72,15.28]pp. This supports a deployed4B post-evidence reasoning advantage; it does not isolate checkpoint/decoding effects or establish a universal state-construction mechanism. Stage13A supersedes same-cohort Stage12Y descriptive estimate; no pooling.185 same-agent QC reviews,15,807 priorfiles unchanged,8.568611GPUh and all9allocations released. Exactly one recommendation: Run a cross-scale image-vs-equal-evidence study at 2B/4B/8B to test whether the functional role of Thinking changes with model size. NOT_LAUNCHED. Evidence:outputs/stage13a/v1/stage13a_primary_inference.json and reports/stage13a/v1/index.md.

## D158 — 2026-10-04T02:25:11.378523+00:00: Stage13B approved cross-scale study

Execute the exact new plan: outcome-independent stratified48, technical4, fixed recipes at2B/4B/8B, reuse4B EQ, 1440new sciencecalls. Local checkpoints available; no download. Record Hamilton quota/tie rules, separate technical/initial8 hashes, integer paired bootstrap before generation. Primary2B EQ and common-family role-shift thresholds unchanged; hard32GPUh and technical gates control completion. Preserve D157/Stage13A evidence and stop after exactlyone unlaunched recommendation.

## D159 — 2026-10-04T03:41:11.757219+00:00: Stage13B stopped by its frozen technical-validity gate

The initial eight-family equal-evidence tranche yielded 14/24 pre-outcome truncations for 2B Instruct (58.3% >20%). Seventeen cap hits include three retained clear unretracted answers; cap hits are not automatically technical missingness. The 2B-Thinking and 8B-Instruct arms had 1/24 and 2/24 missing, respectively. Pending 8B-Thinking work was cancelled; already-started calls finished unchanged. This establishes a validity limitation under this frozen protocol, not an accuracy gap, a scaling null, or a cause of repetition. Cause remains unknown. No tuning, expansion or new correctness inference was performed.

Decision: CROSS_SCALE_ROLE_UNRESOLVED. Retain the confirmed 4B post-evidence result as the strongest claim and stop scaling-based role interpretation. Evidence: `outputs/stage13b/v1/stage13b_summary.md`, `audit/stop_trigger.json`, `audit/gates/2B_I_EQ_initial8.json`, `audit/final_verification.json`. All 120 outputs and 19,705 historical files preserved; all GPUs released after 3.269722 GPU-hours. No follow-on launched.


## D160 — 2026-10-04T07:30:06.822188+00:00: Stage13C approved post-evidence decomposition

User authorizes the exact source-only24-family 4B computational-buffer/derived-state study. Scientific and disjointtechnical4 selection is sealed before trace outcome inspection. First technically resolved source replicate used without correctness selection. Validate actual token-by-token forcing first; no prefix-prefill shortcut. Preserve D157 confirmed evidence and D159 cross-scale technical stop. Original numeric gates and target14/hard18GPUh apply; exactly one recommendation and no follow-on.


## D161 — 2026-10-04T07:49:46.841106+00:00: Native closing-token enforcement does not establish zero further reasoning

Stage13C technical check passes exact token-by-token dummy forcing and firstclose in8/8 receipts, yet5/7 complete outputs emit a second </think> after2,016–7,751free tokens; another shows explicit reconsideration. This violates the approved no-additional-free-reasoning contract. No scientific calls, correctness inference or prompt/grammar/cap tuning. The mechanism question is not evaluated, not null. Decision FORCED_TRACE_CONTRACT_BLOCKED; sole recommendation: retain Stage13A confirmed post-evidence advantage and do not expand the mechanism story. Original+repaired loader versions,28source traces/drafts and completed outputs preserved; all4jobs closed at0.307778GPUh. Evidence: outputs/stage13c/v1/stage13c_forced_trace_technical_validation.json and stage13c_summary.md.


## D162 — 2026-10-04T08:25:12.879808+00:00: Stage13D approved separate semantic and immediate-buffer tests
User explicitly authorizes new Stage13D plan after D161 contract stop. Reuse unchanged24+technical4/source traces. Final source-only QC admits23semantic families;936has no safe derived content identified and remains in MC buffer11. All controls/seeds/representation frozen before outputs. Immediate raw-logit scoring uses zero free tokens; source errors retained separately. Initial8 >20% missingness stops PhaseA only; buffer technical gate separate. Hard12GPUh; exactly one recommendation/no follow-on. Evidence:outputs/stage13d/v1/audit/prospective_seal.json.


## D163 — 2026-10-04T10:33:00.542484+00:00: Stage13D bounded mechanism study complete
POST_EVIDENCE_MECHANISM_PARTIAL. Semantic23eligible/13complete families, five fresh seeds per arm; derived−dummy=0.015384615384615385,95%CI[-0.13846153846153847, 0.13846153846153847]; source errors and missingness explicit. Buffer11MCpairs,meanmarginΔ=-0.3437500866976651,95%CI[-0.8068184419111772, 0.12215909090909091],positivefraction=0.2727272727272727. No free tokens after close; all12technical checks pass and four short repeats match exactly. Stage13Aunchanged; not a hybrid ThinkingON/OFF decomposition. Exactly one recommendation: Preserve the supported component as secondary mechanism evidence and stop additional decomposition unless a cleaner hybrid ON/OFF model becomes available. NOT_LAUNCHED. Evidence:outputs/stage13d/v1/stage13d_summary.md and audit/final_verification.json. All GPUsreleased,4.783333GPUh.


## D164 — 2026-10-04T13:11:07.324349+00:00: Stage14A source-only construction authorized
The approved plan replaces mechanism experimentation with source construction only. Reuse local3040 MATH-Vision IDs and MathVerse788×6; inheritance of source-only alias edges yields2109 conservative MATH-Vision families, distinct from benchmark ID count. Source-stratified ordering/representatives, exclusion taxonomy, exact rendering and same-agent QC are frozen before screening. Historical exposure records IDs/provenance only and cannot select candidates. No evaluated-model or external-annotator calls. Final acceptance1000 governs stopping; no target relaxation or follow-on launch. Evidence:outputs/stage14a/v1/audit/pre_review_code_seal.json.


## D165 — 2026-10-04T13:56:53.304284+00:00: Stage14A structured-atom interpretation explicitly approved
User chooses coherent structured layouts as one primary atom when directly read, jointly task-critical and minimal; no derived summaries, unrelated packing, or answer leakage. Separate meaningful sources remain separate atoms. Record scalar_relation/structured_layout and structured_subfact_count. All first16source decisions rechecked in immutablev2 records before resuming:11pass/5exclude; original exclusions retained. Candidate order and four-primary-atom ceiling unchanged; no model outcomes inspected. Evidence:outputs/stage14a/v1/audit/atom_count_user_amendment_v2.json.


## D166 — 2026-10-04T21:47:33.853889+00:00: Stage14A source foundation completed

Approved structured-source atom rule yields exactly1000final-QC conservative MATH-Vision families, with explicit per-atom internal sizes. Preserve primary count separately from information volume (797families include structured atoms). Source-only full reread rejected1174; replacement came from next frozen rank1727, never from outcomes.

Repeated MathVerse source defects show six-version file completeness does not establish semantic equivalence/sufficiency. Preserve all788native families and validity flags;350pass all recorded source checks. No generic assumption that Text Only is actually sufficient. Catalog exposure covers all families; untouched-only size is0under the frozen definition. Alias expansion is not direct-item-use evidence.

Evidence:outputs/stage14a/v1/stage14a_summary.md and stage14a_source_statistics.json. This source-only result does not establish a model-performance claim. Stage14Acomplete; next scientific study not launched.


## D167 — 2026-10-05T06:53:16.097449+00:00: Stage14B prospective large-scale specification
User authorizes Stage14B phenomenon study on immutable Stage14A populations. Before new outcomes, freeze17536main calls and9600new confirmatory calls (three seeds total including main seed0), exact native/E* prompts and350source-clean MathVerse families. Reuse validated4B BF16/vLLM model-specific decoding with explicitly preregistered32768/81920 caps; no causal mode-toggle/equal-compute claim. Gold/source defects and dependence remain explicit; unscorable/technical missing distinct from wrong. Fixed24-call implementation preflight; no correctness gate or prompt tuning. Optional heterogeneous evidence-recovery scoring omitted; required rescue retained. No next-stage launch. Evidence:`outputs/stage14b/audit/prospective_seal.json`.


## D168 — 2026-10-05T07:12:02.359638+00:00: Stage14B technical scheduling and import repair
Initial technical jobs136000/136001 failed before any model requests because a new unsealed analysis statistics.py shadowed stdlib statistics.median. Exact CPU reproduction/rename regression passes; no frozen generation settings or source decisions changed. Preserve failed jobs/logs and renamed source. Node02GPU-only capacity concealedCPU exhaustion, so use authorized node-agnostic A6000Slurm routing. Finite0GPU coordinator may mechanically validate preflight and launch the already-authorized main census; correctness is excluded from this gate and scientific results still require sealed scoring/QC. No confirmation/follow-on automatic launch. Evidence:outputs/stage14b/audit/stdlib_shadow_repair.json and coordinator_prospective_contract.json.


## D169 — 2026-10-05T08:39:35.579592+00:00: Stage14B technical format hold resolved without rerunning generation
All24preflight receipts valid, exactshortseedreplay bothmodels. Automaticextraction missed source-requested two-letter MathVerse440answers; response-only manualfallback was alreadypreregistered. Preserve originalFAIL and recordmanualreviewv2/gatePASS. One Instruct nativeMATH-Vision capbeforefinal remainsunscorable; no prompt/cap/seed/case tuning. No correctnessused. Proceedwith alreadyauthorized17536maincalls,submitted136129–136136,upto8GPUs; confirmationandfollow-onnotlaunched. Evidence:outputs/stage14b/audit/preflight_validation.json.


## D170 — 2026-10-05T09:43:41.481573+00:00: Stage14B user-approved GPU OOM skip/continue
User requests skipping an OOM sample and continuing the queue. Identifiable GPU OOM becomes final TECHNICAL_MISSING, never wrong. Unknown batched culprit is not guessed: interrupted requests resume once at singleton concurrency; singleton OOM then skips and restarts the engine. Add a finite CPU-only supervisor over136129–136136, at most one replacement per failed original and maximum8GPUs. Preserve original source/config/worker seals and all completed outputs.42CPUtests pass, including subprocess OOM recovery. Supervisor136205 submitted; activation confirmation pending. No scientific outcomes used. Evidence:plan/stage14b_oom_skip_amendment_v1.md and outputs/stage14b/audit/oom_recovery_seal_v1.json.

D170 deployment complete — 2026-10-05T09:53:51.544333+00:00: CPU-only OOM supervisor136212 RUNNING, first heartbeat confirms all8originaljobs. Pending136205/136206 cancelled/preserved; no GPU worker restarted. Original seals verified unchanged. Evidence:outputs/stage14b/audit/oom_recovery_deployment_v1.json.


## D171 — 2026-10-08T13:50:33.598109+00:00: Stage14B large-scale phenomenon established and closed

Main paired native Thinking gain +7.20 pp (95% CI 5.67–9.08); Instruct evidence rescue 234/418 scored failures =55.98% (31 unresolved); post-evidence Thinking gain +14.69 pp (12.10–17.39). All three frozen criteria pass. Native and post-evidence gains remain positive in all three frozen confirmation seeds; this is decoding robustness, not untouched independent replication.

Validated native model recipes differ; this is not a causal mode toggle or equal-compute comparison. E* rescue does not isolate pure perception, and the post-evidence gain identifies no downstream mechanism. Source/gold defects, unresolved answers, same-agent review and dependence limits remain explicit.

MathVerse descriptive paired profile contrast is +9.28 pp (6.15–12.36), with +9.46 pp (4.73–14.18) in the source-clean layer. No outcome-dependent cohort, gold or recipe changes. All27,136 scientific calls preserved; 193.218 observed/proxy GPU-hours and all allocations released. Evidence: `outputs/stage14b/summaries/stage14b_final_summary.md`, `analysis/confirmatory_results.json` and `audit/completion_validation.json`. Exactly one recommendation: Review and authorize Stage14C task-selectivity testing, taking seed robustness and source limitations into account. NOT_LAUNCHED.


## D172 — 2026-10-08T15:10:53.901939+00:00: Stage14C concrete design prepared at mandatory G0 gate
User requested following Stage14C. Its explicit G0stop means prepare a concrete design before seeking release, not immediately launch a draft. Proposed MMStar officialval and authorBlindTestvalid, conservative family sampling, answer-safe two-pass E*, minimum100eligible per new task, frozenC1–C4 with unadjusted familybootstrap intervals, mandatory regressions/missingness, limitedD1, noD2/D3. Original plan and parent outcomes unchanged.13syntheticCPUtests pass; no new calls/GPUhours/payloaddownload. MMStar mixed-source/math composition, unspecified dataset-wide image license, BlindTest rendering repeats and pending actualfamily/E*counts are explicit. Evidence: outputs/stage14c/summaries/stage14c_g0_review_package.md and audit/g0_design_seal_v1.json. Await plan-required G0approval; no scientific continuation authorized at this boundary.


## D173 — 2026-10-09T03:27:04.386692+00:00: Stage14C source gate and technical release
Explicit user “proceed” approved G0. G1 source-only audit sealed MMStar1000/BlindTest714 native and280/300 final-QC E*, exceeding fixed100minimum each. BlindTest E* entirely line intersections: do not generalize eligible-stratum rescue to all fine-visual tasks. Original reviews/corrections preserved;172fixedrereads and everyacceptedsecondreview complete, same-agent limitation explicit.42preflightsciencecalls+4replay onfixedrecipes;4,588maincalls remain gated on technical pass. Evidence: outputs/stage14c/audit/g1_final_source_seal_v1.json and audit/g2_execution_seal_v1.json.


## D174 — 2026-10-09T03:55:12.922305+00:00: Stage14C G2 implementation repair and bounded release
All42scientific preflight calls produced committed finals,0caps/0strict repetition. Missingpyarrow was repaired locally before requests. Original changing-batch Thinking seed replay diverged at116thtoken despite identical input/seed/sampling; one frozen two-call fresh-engine replay matched128/128. Exact replay is conditional on matching numerical execution context; do not claim across-batch bitwise identity. Original failure immutable. G2release preserves sciencecases/recipes/thresholds; main4,588calls with42reuse, max8GPUs,120GPUhstagehard ceiling. Evidence: audit/preflight_validation_initial_v1.json, audit/g2_fixed_context_replay_result_v1.json, audit/preflight_validation.json underoutputs/stage14c.


### Stage14C — Preserve syntax before exact-answer normalization (2026-10-09)
Synthetic checks showed that unrestricted stripping of dollar signs/asterisks mapped malformed numeric expressions to valid integers. The versioned v4 guard accepts paired terminal formatting and sends ambiguous syntax to response-only review; no main outcomes were inspected or prompts/golds changed. Preserve this rule for later exact-answer adapters. Evidence: `outputs/stage14c/audit/terminal_normalization_repair_v4.json` (13passing synthetic checks; existingG2responses revalidated).


## D175 — 2026-10-09T07:49:33.170079+00:00: Stage14C cross-task bottleneck profile complete

Stage14C COMPLETE / STOP. All 4,588 unique main and 600 D1 calls completed; zero technical missingness. Primary, 89 source sensitivities, 1,200 D1 review records, five figures, accounting and final validation are sealed. All allocations released; 14.693634 observed/proxy GPU-hours. No follow-on launched.

Post-E* T−I: math +14.69 pp [12.10,17.39], MMStar +1.81 [−1.81,5.43], BlindTest lines +1.33 [−7.67,10.33]. BlindTest I net supply −21.67 pp: 104 regressions versus 39 rescues. D1 BlindTest elicitation is limited by mostly bare answers and strict spatial-unit matching; no internal-acquisition claim. One late MMStar source defect is disclosed, with original primary preserved and a negligible post-hoc exclusion effect.

Conditional rescue alone cannot establish overall evidence-supply benefit: report regressions on the paired population. Cross-task comparisons are observational and eligible-set restricted. Distinct model recipes/unequalcaps and same-agent/sourceQC limitations remain explicit. Probe-recovered facts do not establish original native solver knowledge. Evidence: `outputs/stage14c/summaries/stage14c_final_summary.md`, `analysis/optional_diagnostics.json`, `audit/final_validation.json`.

Exactly one recommendation: separately approve a bounded validation of the BlindTest textual evidence representation and evidence-probe output contract. NOT LAUNCHED.


## D176 — 2026-10-09T08:21:34.050969+00:00: Stage14C-V concrete G0 package, no generation

Follow the approved plan workflow through its explicit G0 STOP. Prepared source-equivalent R1/R2 and exact deletion-only C1 for both historical question variants; recovered original evidence-request-before-question order from raw input receipts, superseding schematic later/appended prose. C expansion uses source-ID hashes only; historical outputs/scores were verified as opaque hashes without inspecting per-item outcomes for design. Same five source subfacts and model-specific recipes retained. Estimation-only proposal avoids an undefined two-p-value family across the model/stratum C estimands. User approval must release the concrete package and tentative24 GPU-hour ceiling. Evidence: `outputs/stage14c_v_blindtest_validation/summaries/stage14c_v_g0_review_package.md`, `audit/parent_identity_audit_v1.json`. No model calls, download or job submitted.

## D177 — 2026-10-10T03:29:51.050956+00:00: Stage14C-V approved timeout recovery

User approved2,642physicalcalls and32GPUh to complete the existing stage after the6hR2allocation expired. Preserve1,742completed primary receipts and the interrupted wave. Rerun its18members for batching context, but retain the8already-completed responses as primary and store their replays separately; collect58missing primary responses overall. Additive worker checks the finite Slurm deadline before admitting each wave. Resource accounting includes lost attempts, context replays, preflights and expired scheduler records charged conservatively at the full requested limit. The science is unchanged and no follow-on is authorized. Evidence: `outputs/stage14c_v_blindtest_validation/spec/time_limit_recovery_approval_v1.json`; `audit/operational_repair_seal_v1.json`.

Repairpreflight passes the frozen128-token prefix criterion; Thinking full sequences differ (10,125/17,649tokens). Prefix replay validation must not be described as full-sequence bitwise reproducibility. This is an observed technical limitation, not an outcome-based protocol revision.


## Stage14D G0 prerequisite and prospective design — 2026-10-10T15:44:07.579363+00:00
The exactThinking-native/E* joins giveS1=306,S2=110,S3=574; the allocation100/100/100isviable.4000finalscoreidentities and1000sourceimagehashespass; no historical labelchanged. Proposed300/120selection usesformat×structurequotas, source-metadata balance and deterministichashseed20261011.249selectedstructuredfamilies require explicit source-definedsubfact/QC; do not treat technicalidentityas semanticvalidity.

Stage14C-V C has800rawresponses but no mode/fidelity/Cprimary/closureseal. Generationcompletion cannot satisfyStage14D'sclosureprerequisite. PlanG0/§9alsorequireexplicitnumericcomputeapproval; the requestedpre-mainbenchmarkhasno inheritedunlimitedbudget. Prepareconcrete2GPUh/24-callcalibrationproposal; fullstagehistoricalproxy42.54GPUh/stress92.65/proposedcap100remainsunapproved. Mainstillhelduntilsource/anchor/backendgates,measuredbudgetandclosure/explicitwaiver. Evidence: `outputs/stage14d/audit/g0_cpu_validation_v1.json`, `reports/stage14d_g0_review_package.md` underoutputs/stage14d. No experimentlaunched; this is agate decision, not anewmechanisticfinding.


## Stage14D completed preparation / main gate — 2026-10-11T12:06:20.261717+00:00

Preserve original300/120cohorts and2100slots; source/anchor review yields1674eligible continuations. Whole-prefix QC changed158records (4final states), demonstrating why first-explicit-statement timing alone misses earlier partial/distributed target information. All original versions and exact quotes retained; same-agent two-pass QC is not independent reliability. Two source/E* discrepancies remain explicit without historical repair. No certified CF inventory means nested assay0 and fresh-acquisition claims unavailable, not a scientific null.

24-call technical calibration passed,0.36305556allocatedGPUh including setup failures. Measured serial rates supersede historical batch proxy:178.20linear/362.76stress GPUh;375proposed total ceiling remains unapproved. No main generation; C-V closure/explicit-waiver gate still applies. Evidence: `outputs/stage14d/reports/stage14d_main_release_review_v1.md`, `audit/source_anchor_preparation_seal_v1.json`, `audit/native_second_pass_changes_v1.json`, `audit/main_resource_estimate_v2.json` under the stage namespace.


## Stage14D0 scope and reuse — 2026-10-11T15:13:10.712438+00:00
User approved the v2 retrospective audit. Preserve old preparation; no continuation/budget release. Exact1,000-family inventory confirms2,000nativeoutputs and4,000scoremetadatarecords. Earlier414target-specificreviews cannot replace whole-E* atom/subfact audit. Pilot32 prospective metadata/hash rule frozen; one main AI reviewer and prior exposure disclosed. Source-QC failures will not count as model errors; E*-arm raw reasoning remains unopened. Evidence:outputs/stage14d0/inventory/inventory_validation_v1.json and spec/prospective_selection_rules_v1.md.

## Stage14D0 completed retrospective audit — 2026-10-11T22:30:23.665674+00:00

Source-defined subfact comparison and full trace review are necessary: the older target-focused 414 reviews do not certify every required E* fact. D0 reviewed 300 paired families / 600 traces and withheld four source-invalid subfacts without rewriting historical E*. The source-selected paired T−I explicit-error contrast is −3.60 pp [−7.86, +0.40]; Thinking's longer trace and different recipe cannot support a causal perception claim. Fifteen I and 20 T wrong finals have all required reference facts last stated correctly, but minimal E* and other source mistakes prevent an automatic pure-downstream diagnosis.

Promoted lesson: preserve source-validity, statement coverage, premise use and answer outcome as separate units. Same-agent semantic labels and sparse event offsets require explicit uncertainty; deterministic span checks are not independent semantic review. Exactly one bounded verification-and-use proposal was written, not launched. Original main grid remains HOLD. Evidence: outputs/stage14d0/reports/stage14d0_native_trace_audit_results.md and audit/final_package_validation_v1.json.

## Stage14D1 — Preserve technical stop and grammar branch lesson (2026-10-19)

The user delegated prospective SAVA plan amendments and bounded execution without permission requests. The implemented chain separates current-prefix targetselection, model sourceaddressing, visualread and same-solver continuation; nooracle target/value entersruntime. Main R72 was notrun because exactreplay remains6/8 aftercache-disable diagnostic. Numerical/runtime cause unknown;do notpromote acache-causeclaim ormethodefficacynull. Allattemptspreserved;0.394722GPUh.

Supported engineering lesson: compilingJSONschema isinsufficient tovalidate intendedalternatives. Installedxgrammar rejectedtheQUERYexample's fieldorderwhileacceptingNONE; testingboth literalprompt examples reproducedthedefect. v3ordersQUERYfieldsconsistently andhasfourpassingregressiontests. Evidence:outputs/stage14d1_sava/audit/query_grammar_branch_diagnostic_v2.json andgrammar_v3_tests.txt. Exactlyonerecommendation:validaterestart/replayonfixed8beforeacquisitioncomparisons. Nofollow-onlaunched.

## Stage14D1 recovery — supported runtime and validation distinctions (2026-10-20T06:36:00.572618+00:00)

- Observed: pinnedvLLM0.11.0 default batched multiprocessing changed prefill schedules/logits despite identical inputs; instrumentedcase33diverged withmatching RNGstates. DisablingV1multiprocessing passed all8exactpairs and independentsecondseeds; batch1also passed. This supports runtime/scheduling-sensitive numerical execution, not a reconstruction or demonstrated RNG bug; no universal kernel/hardware guarantee.
- Keep structured-output syntax, branch selection, literal provenance acceptance and source-semantic validity distinct. Recoverycontrols12/12branch+JSON but10/12fullcontract; realqueries8/8JSONbut0/8fullcontract. Literal rejections do not prove8falsevisualfacts. No targetedlocatorwasattempted.
- Decision: retain all gates andSTOPtechnicaltask; no72familypilot. Evidence: `outputs/stage14d1_sava_recovery/v1/reports/technical_recovery_final.md` and `audit/final_result_verification.json`.

## 2026-10-20 — SAVA technical contracts versus scientific evidence

Source-reference IDs fix quotation transport without certifying target truth. v4literalimage-tag guardbugandv5LOCATEmode/cardinality mismatch are confirmed byregressions/actualreceipts; finalv6same8passesnumericgates. The officialnative0..1000coordinateadapter is supportedcompatibility practice, but noisolatedcausalproof thatcoordinateunitsalonecausedoldfailures. RomanQUERY-controlfalse-negative persistsandisnotprompt-tuned. Independentgrammarreachability isdistinctfromsemanticbranchaccuracy. AvalidringROI addresseswrongfinger: keepmethoderrorasdata. Evidence:outputs/stage14d1_sava_pilot/v1/reports/technical_validation_and_execution_status.md. Pendingallocationblockisexternalcapacity; no scientificSAVAefficacyconclusionyet.

## Stage14D-1 execution lesson — 2026-10-22

Confirmed:64/256-token technical throughput did not predict the full81,920-cap worker's long-context behavior. Rank1 admitted eight long requests with a201,152-token KV cache, showed prolonged token-progress starvation and reached its allocation deadline with2/175 physical solvers complete. Rank0 completed170/170 at141.475solver tokens/s, below the short-run265.009. Repeated preemption is suspected from the pinned scheduler and progress pattern; exact counts were not logged. Future recovery must account for live context/KV demand and validate long-context scheduling, without changing scientific caps or treating short replay success as a throughput guarantee. Evidence: outputs/stage14d1_sava_pilot/v1/reports/result_check_20261022.md. This is an execution lesson, not evidence against SAVA efficacy.

## Stage14D-1 completion — 2026-10-22

The fixed 72-family pilot completed after a capacity-admission repair and user-directed longer job limits. Primary QI−N was −4.17 pp (95% CI −12.50 to +4.17), with three rescues and six regressions. Technical validity did not imply method efficacy. Of 62 accepted queries, 22 were fully task-relevant; none of the three QI rescues contained a clearly new task-critical helper fact. Preserve the separation between provenance, relevance, readout correctness and final-answer changes. This supports target-selection development, not a universal claim that subgoal queries cannot work. No Stage14E was launched.

Replay traces show that identical seeds/inputs do not guarantee sampled bitwise identity across batch shapes in BF16. Validate the actual schedule, keep paired arms within one execution protocol per family, and reserve eventual KV demand to avoid long-context over-admission. GPU requests now default to 48 hours and end when work finishes; actual billing is tracked separately.

[Evidence](../outputs/stage14d1_sava_pilot/v1/reports/feasibility_main_v8.md).

## Stage14E development boundaries — 2026-10-23

Controlled source reading did not support dropping theprefix or assuming predictedcrops help: in24developmentcases, source-specifiedtargetcontext6useful vs3withoutprefix; global/local3. The source-specifiedtargets containqualitativehints, so modeltarget-vs-oracletarget is not a puretarget-identitycausalestimate. Preserve this limitation rather thanpromotinganoracleupperbound. Soleledgerrevisionselectedonpartialsourceevidence3/24vs0/24matchedA, not finalaccuracy; noheldoutefficacyconclusionyet. Evidence: outputs/stage14e_acquisition_development/v1/reports/diagnostic_interpretation_limits_v1.md anddevelopment_revision_v2.md.

Supportedengineeringlesson: prose dimensionseparators canbe misparsed asnegativevalues (`7-foot-by-7-foot`) whileLaTeXequivalentsarenot. Versionednormalizationpreservesarithmeticminus andunsupportedmagnitudes;48savedtargettransportsunchanged,5independentregressionspass. Provenanceacceptance remainsdistinctfromsemantictruth.

## Stage14E final source-evidence result — 2026-10-23T01:05:50.094588+00:00

The obligation-first ledger selected on3/24partial development reinspections produced0/32useful new/reinspected facts in the one-shot evaluation, versus1/32original SAVA-style reader. Seventeen targets were accepted,12ledgers rejected,3NONElegitimate; accepted targets were0fully relevant/9partial/8unhelpful. Technical provenance and exact-prefix/replay validity do not certify task relevance or evidence fidelity. Seven invalid ledgers had a valid first eligible entry but another invalid entry; no alternative execution was tested, so no claim that relaxation solves this. Keep helper evidence, later solver image use and final answers distinct. Final answers N 19/32, S 20/32, M 20/32; no accuracy result is relabeled as fresh helper acquisition. Recommendation: do not scale this implementation; establish reliable source binding before another efficacy study. No follow-on launched. [Evidence](../outputs/stage14e_acquisition_development/v1/reports/final_research_report_v1.md).

## Stage14E2 — matched reader diagnostic and user-requested pause (2026-10-23T02:50:35.340469+00:00)

The primary source-informed-target comparison gives4/24useful partial reads in both compact and reasoning modes; paired0pp,95%CI[-16.67,+12.50]. Extra helper deliberation alone did not establish improvement under this frozen protocol. Original-target gains are partial and development-only; correct no-image hexagon rows in487 do not demonstrate visual acquisition. Preserve source/format/novelty distinctions and all negative evidence. At the user’s explicit request, pause after this completed experiment; do not launch the frozen fresh32evaluation or select a new method now. Evidence: `outputs/stage14e_readout_mechanism/v1/reports/final_diagnostic_report_v1.md`.

## Thinking failure retrospective — source checks and verbal image-denial limits (2026-11-22)

The existing MathVerse checkbox frame is not a complete semantic certificate: family7 has `text_only_sufficient=PASS` while its detailed source review explicitly says sufficiency FAILS; several other records preserve separate key/unit conflicts despite literal cross-version gold consistency. Retain official scores and source flags, report these contradictions, and distinguish any note-exclusion sensitivity from the original cohort. Do not treat every archived WRONG as a verified model failure.

All884 image-present native outputs with a broad image-unavailability phrase have present/preprocessed-image input receipts matching their original result hashes. Such phrases are observable model text, not evidence that image transport failed or visual tokens were ignored. Broad lexical candidates include false positives; strict named-image sensitivity, length strata and exact quotes must remain separate from source-validated evidence errors. [Report](../reports/thinking_math_failure_audit/thinking_failure_analysis_20261122.md) · [Validation](../outputs/thinking_math_failure_audit/v1/independent_validation.json). No experiment resumed.
