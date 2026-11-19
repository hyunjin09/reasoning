# Phase 3C.3-R: Target-ROI Signal Gain

## Current Objective

Execute the user-approved `plan/stage3c3r_plan.md` as one bounded causal action: measure selected-head target-ROI contribution dose response, compare the Stage 3C.3 query-patch operating point, run the prospectively frozen W4 redundancy scopes only if the Phase-A gate passes, write exactly one review-only recommendation, and stop.

## Active Constraints

- Preserve Stage 0--3C.3 artifacts unchanged.
- Reuse the exact Stage 3C.3 seven-base validation and 24-base primary cohorts, Target A/B coordinates, T/M/I ROIs, causal heads, and noncausal controls.
- Scale only a frozen source contribution after Attention and before `W_O`; keep the locally computed Q/K/V, attention probabilities, non-target source contribution, and untargeted heads unchanged.
- Freeze the lambda grid, controls, R0--R3 scope family, gate aggregation, and 13-test family before new outcome scoring.
- Treat unnormalized evidence preference as primary and retained-evidence ratios as descriptive and unclipped.
- Do not manipulate the candidate sink, add query/`h_pre` interventions, expand beyond layers 28--29, or start Stage 3C.4, Stage 4, multi-evidence, or failure analysis.

## Current State

- Done: Stage 3C.3 completed with technical PASS and a failed reciprocal evidence-preference gate despite strong routing/alpha-V changes.
- Done: the Stage 3C.3-R plan, access/GPU policy, environment, promoted lessons, prior cohort/configuration, and reusable exact-attention runtime were reviewed.
- Done: the project-local `research-control` skill is absent; the explicit user-approved plan and repository controls govern this action.
- Done: a v1 smoke exposed avoidable BF16 partition-bookkeeping error; FP32 contribution partitioning was fixed and the failed smoke preserved before primary scoring.
- Done: corrected smoke and seven disjoint validation bases passed exact endpoints, native reproduction, source/head isolation, Q/K/V/attention invariance, finite-output, and repeatability checks.
- Done: all 24 primary bases completed Phase A; the prospective redundancy gate passed with median base-aggregated `E(0)/E(1)=0.996591` and 24/24 bases at least 0.80.
- Done: gated R1--R3 scoring completed on all 24 bases; all-head, both-layer R3 retained median evidence 0.9864/0.9910 for Targets A/B.
- Done: 20/20 acceptance and 20/20 independent artifact checks passed; exactly one recommendation was written.
- Blocked: none.
- Most recent useful observation: the Stage 3C.3 query necessity patch already drove the median projected target contribution to 0.0014/0.0059 of native, while direct lambda-zero and even R3 retained about 99% of evidence preference.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Stage 3C.3 routing/behavior dissociation | `outputs/stage3c3/analysis/query_causality_statistics.json` | Motivates testing contribution magnitude rather than changing routing again | confirmed |
| Frozen cohorts and state coordinates | `outputs/stage3c3/cohort/` | Supplies disjoint 7/24 validation-primary split without outcome reselection | confirmed |
| Frozen T/M/I and head targets | `outputs/stage3c2/annotations/`; `outputs/stage3c3/config/stage3c3_config.json` | Defines source and head interventions prospectively | confirmed |
| Exact full-shape eager Attention path | `code/visual_reasoning/stage3c3/runtime.py`; `outputs/stage3c1/audit/reconstruction_check.json` | Avoids known BF16 row-shape drift | confirmed |
| Native evidence scores positive | `outputs/stage3c3/phase_a_query/raw/` | Makes `E(lambda)/E(1)` defined without clipping on the frozen primary cohort | confirmed |
| Phase-A dose and gate | `outputs/stage3c3r/analysis/dose_response_statistics.json`; `outputs/stage3c3r/phase_b_redundancy/redundancy_gate.json` | Rejects an insufficient-attenuation explanation and authorizes the frozen nested scopes | confirmed |
| Nested W4 result | `outputs/stage3c3r/analysis/redundancy_scope_analysis.json` | Shows broad robustness without localizing same-layer or W4 cross-layer compensation | confirmed |
| Independent validation | `outputs/stage3c3r/summaries/artifact_validation.json` | Recomputes raw cohorts, rows, gate, mechanics, Holm family, figures, and stop boundary | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3C.1 row-only reconstruction | BF16 numerical drift | supported | preserve the installed full tensor shape | do not compute a smaller attention row as a substitute |
| Stage 3C.3 prefix-only donor capture | exact self control failed across different matrix shapes | supported | measure/intervene inside each exact candidate-scoring pass | do not reuse low-precision states from a different sequence shape |
| Stage 3C.3 query routing | large routing/alpha-V changes without reciprocal evidence control | supported observation; explanation unknown | distinguish signal identity, signal magnitude, and redundant paths | do not treat intermediate routing change as behavioral control |
| Stage 3C.3-R smoke v1 | BF16 `c_rest` subtraction/addition produced 0.0078125 partition and 0.03125 endpoint arithmetic error | supported by preserved smoke artifact | do partition bookkeeping in FP32 and cast only the patched head output | do not accept avoidable BF16 decomposition error |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Saturation / plateau | query patch may leave target signal above a sufficiency regime | selected-head T contribution lambda curve plus query operating point | rejected under tested range; query patch was already near zero and no collapse occurred at zero |
| Local redundancy | selected path may be unnecessary while nearby heads/layers preserve evidence | gated R1--R3 nested W4 removal | not localized; no R1--R3 incremental contrast survived Holm correction |
| Continuous gain control | prior semantic Value interpolation was graded | unnormalized evidence preference across the frozen lambda grid | supported only for a small Target-B effect; unsupported for Target A |
| Support beyond W4 | even broad W4 target removal may leave evidence intact | R3 all-head layers 28--29 target removal | supported as broad robustness, carrier/location unresolved |

## Next-Step Decision

- Current bottleneck: Stage 3C.3-R is complete; the support preserving evidence after all-head W4 target-contribution removal is not localized.
- Relevant memory item used: R3 retains median evidence 0.9864/0.9910 and no nested-scope contrast versus R0 survives Holm correction.
- Chosen next action: stop and return **GO — Redundancy Localization Beyond W4** for review only.
- Why this action: R3 broad robustness meets the plan's specific recommendation condition, while saturation and local W4 redundancy do not explain the result.
- What not to repeat: do not infer a particular carrier or automatically expand beyond W4 from persistence alone.
- Stop condition: met; no broader-than-W4, sink, query, `h_pre`, Stage 3C.4, Stage 4, multi-evidence, or failure intervention was started.

### Step Result

- Action taken: completed the frozen selected-head dose curve, controls, Stage 3C.3 operating-point comparison, gated R1--R3 family, statistics, figures, and artifact validation.
- Result: technical PASS / O4 Broad Robustness Beyond W4. Target A shows no gain dependence; Target B shows a small target-specific graded effect, but both targets retain about 99% evidence at lambda zero and under R3.
- Evidence saved: `outputs/stage3c3r/`.
- Failure or issue: local redundancy is not localized; the preserving carrier/path remains unknown.
- Lesson learned: semantic Value identity can be causal while the magnitude of the current-position W4 target contribution is highly robust/redundant; attention/alpha-V magnitude is not a quantitative behavioral-importance fraction.
- Next implication: review a bounded beyond-W4 redundancy design before any further experiment.
