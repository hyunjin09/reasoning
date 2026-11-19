# Phase 3C.4: Spatiotemporal Redundancy Localization

## Current Objective

Execute the user-approved `plan/stage3c4_plan.md` as one bounded causal action: remove the frozen target-ROI Value contribution across prespecified layer and late-reasoning-time scopes, localize same-time versus temporal redundancy, compare the result descriptively with Stage 3B.2, produce exactly one next-stage recommendation, and stop.

## Active Constraints

- Preserve Stage 0--3C.3-R artifacts unchanged.
- Reuse the exact Stage 3C.3-R seven-base validation and 24-base primary cohorts, Target A/B coordinates, and attention-independent T/M/I ROIs.
- Reuse the validated FP32 pre-`W_O` source-contribution partition and remove only `c_T`; do not patch donor state, Q/K/V, attention probabilities, non-target sources, or earlier-than-window queries.
- Freeze L0--L4, T0/T1/T2/T4/T8/T16, C1--C4, the reduced M/I controls, and the 14-test Holm family before outcome scoring.
- Treat `base_problem_id` and unnormalized evidence change as primary; retained-evidence ratios are descriptive and unclipped.
- Do not run sink manipulation, Q/R/current-residual patching, windows earlier than `t*-16`, Stage 4, multi-evidence refresh, or failure analysis.

## Current State

- Done: Stage 3C.3-R passed 20/20 technical and artifact checks with O4 broad robustness beyond W4.
- Done: user explicitly authorized the complete Stage 3C.4 plan on 2026-09-04.
- Done: access/GPU policy, environment, the complete Stage 3C.4 plan, Stage 3C.3-R handoff, and reusable runtime were reviewed.
- Done: all 24 primary bases completed the frozen L0--L4, T0--T16, C1--C4, and M/I control families.
- Done: all 14 frozen tests survived Holm correction; technical acceptance and independent artifact validation pass 20/20.
- Blocked: none.
- Most recent useful observation: all-head W4 removal retained median evidence 0.9864/0.9910, while the existing Slurm allocation 106936 remains active on node04 with two A5000 GPUs.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Exact contribution semantics | `code/visual_reasoning/stage3c3r/runtime.py`; `outputs/stage3c3r/audit/` | Supplies the validated intervention object and FP32 partition | confirmed |
| Frozen cohorts and target states | `outputs/stage3c3r/cohort/`; `outputs/stage3c3r/config/frozen_targets.json` | Prevents outcome-driven reselection or coordinate drift | confirmed |
| Broad W4 robustness | `outputs/stage3c3r/analysis/redundancy_scope_analysis.json` | Motivates prespecified layer/time expansion | confirmed |
| Late source-identity sensitivity | `outputs/stage3b2/analysis/bidirectional_retrieval_statistics.json` | Provides a distinct semantic-switch reference for the final comparison | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3C.3-R v1 bookkeeping | BF16 partition and endpoint arithmetic drift | supported | retain FP32 source/rest arithmetic and exact endpoint audits | do not reintroduce BF16 contribution bookkeeping |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Same-time layer redundancy | W4-wide current suppression is weak | L0--L4 at the frozen current query | open |
| Earlier retrieval / temporal redundancy | late source identity matters but current W4 contribution is dispensable | all-layer T0--T16 suppression | open |
| Spatiotemporal redundancy | evidence may be refreshed across depth and several queries | frozen C1--C4 cells | open |
| Earlier nonvisual storage | even broad late visual suppression may be weak | persistence under all-layer T16 | open |

## Next-Step Decision

- Current bottleneck: evidence support that survives current-position W4 target-contribution removal is not localized across other layers or earlier late-reasoning queries.
- Relevant memory item used: Stage 3C.3-R R3 retained 0.9864/0.9910 median evidence and no nested W4 contrast survived Holm correction.
- Chosen next action: stop and return **GO — Behaviorally Necessary Visual Window Mechanism** for review only.
- Why this action: it is the smallest approved extension that separates same-time layer support, late temporal refresh, their interaction, and support already present before the tested window.
- What not to repeat: do not infer a carrier from persistence, select scopes from effects, use attention as the primary readout, or broaden beyond the frozen all-layer/16-token boundary.
- Stop condition: all 20 technical criteria are evaluated, one O1--O4 classification and exactly one recommendation are written, and no later experiment is started.

### Step Result

- Action taken: completed the frozen same-time layer, all-layer temporal, interaction, and control suppression families and independently rederived their mechanics/statistics.
- Result: technical PASS / O2 Temporal Redundancy. Base-aggregated retention fell from 0.8436 at all-layer T0 to 0.6515 at T1 and 0.5519 at T16; the target-specificity gate passed.
- Evidence saved: `outputs/stage3c4/`.
- Failure or issue: no technical failure; Target A is substantially more suppression-sensitive than Target B, and no tested base-aggregate `w_50` exists.
- Lesson learned: the W4 current-position robustness concealed support spread over other layers and immediately preceding reasoning queries; most added temporal loss appears by T1/T2, but sparse windows do not establish an exact acquisition boundary or carrier.
- Next implication: review a bounded mechanism study of the localized necessary late window; do not automatically patch Q/R/residual states or manipulate a sink.
