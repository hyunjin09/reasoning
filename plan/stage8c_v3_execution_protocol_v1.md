# Stage8C v3 execution protocol

The user approved `stage8c_v3_fp32_direct_retrieval_gain_plan.md` on 2026-09-20
KST, with two node02 GPUs via the project scheduler and Slurm. This is a new
scientific execution regime; the BF16 stop and all historical evidence remain
preserved. The v3 plan takes precedence over previous Stage8C technical gates.

## Frozen execution

- Directly load the pinned Qwen3-VL-2B-Thinking checkpoint in FP32, including
  vision/language weights, activations, cache and logits. Disable TF32 matmul
  and cuDNN, use no autocast and no BF16 fallback. Record actual dtypes during
  ordinary development inference; do not run an extra validation cohort.
- Preserve vision SDPA / language eager attention implementations, prompts,
  image processing, sampling and scoring from the established runner.
- The frozen Stage8A detector is a fixed policy, without FP32 transfer claims.
  Threshold .5478025980771918, gap4, onset only, layers19–22 and all existing
  heads. Prefill R is unavailable; output index t measures the prefix predicting
  token t. Apply the policy throughout generation, as in the previous protocol.
- Reuse the existing visual-contribution formula and two-pass wrapper: probe
  without sampling; crop its appended cache token at an onset; rerun that token
  with postprojection gain and commit its cache; sample once in the native loop.
- No BF16 repair, transfer cohort, detector audit/recalibration, pre-dose semantic
  review, or pre-efficacy V1–V6 bundle. CPU implementation checks are not a new
  scientific gate. OOM/crash is an execution barrier; retain logs and stop, with
  no precision fallback or outcome-conditioned item replacement.
- Copy frozen dev128/test512 manifests byte-for-byte under the v3 filenames.
  Preserve timing256/local-read128, visual families and original item seeds.
  Dev has 512 trajectories (four doses/item); one worker per GPU. Baseline
  g=1.0 is FP32 with transparent gain and passive frozen-policy measurement.

## Decisions frozen before outcomes

- Primary accuracy is correct/all frozen items. Unresolved extraction is
  reported separately and receives no correct credit. Use the unchanged local
  scorer and inherited blind-extraction/equivalence workflow before dose choice.
  No test execution while decision-relevant extraction remains pending.
- Apply no-go guards, then rank eligible non-native doses by exactly:
  highest accuracy, greatest W→C−C→W, lowest cap-rate increase, lowest median
  reasoning-length increase, then smallest gain. No extra harm tie-breaker.
- Retain the previous prespecified operational meanings: a major subject has
  >=15 dev items; severe harm is >10pp loss; meaningful dev gain for the length
  exception is >=2pp; clearly substantial held-out gain is >=5pp. Multiple means
  >=2 major subjects. Preserve all subject effects and reasons in the report.
- Test512 is conditional on dev go/no-go and a sealed dose. Use paired item and
  visual-family bootstraps (20,000 draws, seed820260921) plus exact McNemar.
  All comparisons are within FP32. Do not treat events as accuracy samples.
- Timing schedules use the frozen subset and baseline trajectories only,
  matching baseline onset counts, excluding episode±16 and matching trajectory
  quartiles where possible. Preserve placement/early-termination mismatches.
- Local-read review remains downstream interpretive work. Preserve unresolved
  claims and collateral damage. Optional extension requires every plan §28
  condition and an explicit recorded decision before additional item selection.
- A stopped branch yields a report and one recommendation. Block3B is not
  launched automatically; it is a separately specified research action.

## Resource estimate before ordinary FP32 runs

The dev queue is 512 trajectories, with two GPU workers. Prior BF16 lengths
provide only a planning range: roughly 20–80 wall hours for dev, subject to FP32
throughput, caps and intervention recurrence. Request a five-day finite Slurm
ceiling and release on queue completion or error. Replace this range using
ordinary completed FP32 examples, never a separate timing/transfer cohort.
Conditional initial total:512 dev +1024 held-out +256 timing trajectories;
semantic review follows. No total ETA until dev throughput and gate are known.
