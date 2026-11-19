# Stage9A.5 — Qwen3-VL-4B native Thinking vs prompted CoT

Completed 2026-09-27T04:56:16.228479+00:00. **Outcome A; COMPLETE / STOP.**

Thinking and prompted CoT share coarse finite direct-access sufficiency at token128 under the frozen point-based5pp criterion. This is not an equivalence test. This preservation result is specific to standard masking: Thinking token128 does not preserve under null-sink. Robust shared sufficiency across the two interventions is not established.

Thinking-specific prolonged visual-access necessity is **not supported** under the preregistered claim gate. The primary Thinking-minus-CoT damage contrast at128 is 3.12pp,95% CI [0.00, 7.81]pp. 2/32 images have greater Thinking damage, 0/32 lower damage and30/32 tied.

## Fixed design and validity

Same32 frozen synthetic images, one color-count and one shape-count query each. All64 queries remain in every primary condition; missing final options receive no credit. The Stage9A.4 CoT reference, checkpoint files, questions, option permutations, images and preprocessing were hash-verified and reused without regeneration.

New arm: native Qwen3-VL-4B-Thinking, revision1de27d8c51f12e819435303b9e84c4e25ba8401e. The explicit CoT instruction was removed; the native template opens `<think>`. Literal option review applies only after native `</think>`, with scratchpad proposals excluded. FULL reasoning and final-answer reviews were sealed without gold before scoring.

Both matched-scale arms: greedy BF16, TF32 off,512-token cap, native EOS, eager language/SDPA vision, native DeepStack unchanged. All36 decoder layers are covered by generated-query→image-key restriction. Prefill and image-derived cache remain available. The prefill-predicted first output is native; query index t=absolute−prompt+1 is blocked when t>cutoff.

| FULL metric | CoT | Thinking |
|---|---:|---:|
| Correct | 45/64 | 58/64 |
| Substantive reasoning | 64/64 | 64/64 |
| Valid final option | 60/64 | 62/64 |
| Normal EOS | 60/64 | 61/64 |
| At512-token cap | 4/64 | 3/64 |
| Unscorable | 4/64 | 2/64 |

Thinking observed generated length mean/median: 196.17/174; native reasoning tokens: 190.38/168. All G1–G5 pass. Eight exact FULL no-op checks and eight actual-model V1–V6 checks pass, including unchanged prefill, cached continuation parity, exact zero image attention and64/128/256 boundaries.

## Absolute access results

Damage is FULL accuracy minus condition accuracy. Independent unit=image; each image has equal weight and its two queries remain paired. Intervals use4,000 paired image-cluster bootstrap draws, seed920260927. Preservation is the frozen point criterion damage≤5pp; interval uncertainty is reported separately.

| Condition | CoT accuracy | CoT damage,95% CI (pp) | Thinking accuracy | Thinking damage,95% CI (pp) |
|---|---:|---:|---:|---:|
| full | 70.31% | 0.00 [0.00, 0.00] | 90.62% | 0.00 [0.00, 0.00] |
| t0 | 43.75% | 26.56 [10.94, 42.19] | 64.06% | 26.56 [14.06, 39.06] |
| t64 | 57.81% | 12.50 [3.12, 21.88] | 71.88% | 18.75 [9.38, 28.12] |
| t128 | 71.88% | -1.56 [-4.69, 0.00] | 89.06% | 1.56 [0.00, 4.69] |

Selected Thinking cutoff: **128**. At128, 98.175% of bootstrap draws meet5pp. No token256 execution was triggered when128 preserved. No normalized50%/75% assay or precision reserve was triggered; frozen gate receipts record the reasons.

Literal final-channel and raw strict final-channel accuracy agree at FULL (90.62%). Full raw-sensitivity surfaces are retained in the machine-readable comparison. Whole-trajectory extraction is separately labeled and never substitutes scratchpad proposals for final answers.

## Relative exposure

The common descriptive horizon is observed FULL generated length, including final/EOS. Capped lengths are right-censored; cutoff/N is an upper bound on the complete-horizon fraction for those traces. Ratios above1 are reported as budget/horizon ratios, with clipped fractions also preserved. Actual exposure uses N−1>cutoff.

| Arm | Median observed tokens | Median64/N | Median128/N | Reaches64 mask | Reaches128 mask |
|---|---:|---:|---:|---:|---:|
| cot | 149 | 0.430 | 0.859 | 98.44% | 67.19% |
| thinking | 174 | 0.368 | 0.736 | 98.44% | 64.06% |

Observed lengths differ, but the same absolute128 cutoff preserves both arms. These descriptions do not establish equality of relative-phase causal necessity.

## Bounded redistribution control

The null-sink intervention zeros image attention contributions without renormalizing non-image probabilities. It uses only primary32 FULL/ZERO/selected128; exact FULL and normal-ended non-exposed rows are reused.

| Arm/condition | Accuracy | Damage (pp) | 95% CI (pp) |
|---|---:|---:|---:|
| CoT/full | 70.31% | 0.00 | [0.00, 0.00] |
| CoT/t0 | 32.81% | 37.50 | [21.88, 53.12] |
| CoT/t128 | 67.19% | 3.12 | [0.00, 7.81] |
| Thinking/full | 90.62% | 0.00 | [0.00, 0.00] |
| Thinking/t0 | 60.94% | 29.69 | [17.19, 42.19] |
| Thinking/t128 | 79.69% | 10.94 | [3.12, 21.88] |

Qualitative control support: **False**. Thinking selected-cutoff preservation fraction across bootstrap draws: 12.575%. The frozen CoT control128 interval crosses5pp, so its point preservation is not high-precision evidence. Interpret the Thinking control with its displayed interval as well.

**Thinking128 preservation fails this control.** The paired null-sink Thinking-minus-CoT damage contrast is 7.81pp,95% CI [-1.56, 18.75]pp (secondary robustness comparison). Of7 FULL-correct queries lost at null-sink128, 7 have no final answer and0 have valid wrong answers; 0 queries improve. These observed counts do not identify the cause of changed completion. The512 cap, scoring rule and selected condition were retained. No cap repair,256 search or reserve was launched after the failed control. [Diagnostic receipt](audit/control_completion_diagnostic.json).

Completion also matters in the primary panel: all12 FULL-correct losses at standard64 and the1 loss at standard128 lack final answers. The measured necessity endpoint is performance within the frozen512-token budget, including completion. These losses do not establish that an emitted local visual value became wrong. The reason the interventions delay or prevent completion remains unknown.

## Native use and claim limits

[Stage4A](../../stage4a/summaries/stage4a_summary.md) established demand-aligned A→B→A source dependence and later A re-engagement in a frozen MathVerse local-read assay:36/48 bases met its dynamic definition. Its trigger-retargeting O3 claim was not established. That prior local source-use evidence and this synthetic access-removal assay answer different questions; the present result does not invalidate native dynamic retrieval.

This is a bounded32-image mechanistic comparison, not a benchmark-population estimate or equivalence test. Checkpoint/training specialization remains confounded. No effect is causally attributed to thinking, DeepStack, or a particular objective. Persistent visual representations are not ruled out, and FULL access is not proven strictly necessary.

## Verification and resources

11 focused tests pass. Final independent audit passes8 groups, including unchanged input/reference hashes, all receipts and exact aliases, native answer-channel boundaries, and independently reconstructed damage/paired-contrast bootstraps.

337 new scientific generations ({'full': 64, 't1': 168, 'sink': 105}); 0.682 allocated GPU-hours, 0.567 measured generation GPU-hours. Peak reserved VRAM8.54GiB. At most4 GPUs concurrently; all GPU jobs completed and released. Existing local checkpoints/data and project .venv reused; no download, package install, tmux allocation or keepalive.

Figures: [FULL validity](figures/figure1_full_validity.png), [absolute access](figures/figure2_absolute_access.png), [token128 contrast](figures/figure3_token128_contrast.png), [relative exposure](figures/figure4_relative_exposure.png), [native use vs necessity](figures/figure5_native_use_vs_necessity.png). Each also has a PDF.

## Exactly one recommendation

Retain dynamic visual re-access as the main Thinking mechanism and emphasize the dissociation between native causal use and ablation necessity rather than a Thinking-specific VAB claim.

**STOP.** The recommendation has not been executed. No new experiment or later stage was launched.
