# Phase 3C.5: Visual Window and State Handoff

## Current Objective

Stage 3C.5 is complete. Preserve the frozen result, return it for review, and do not start the recommended follow-on without a new approved plan.

## Active Constraints

- Preserve Stage 0--3C.4 artifacts unchanged and reuse the exact 7/24 validation/primary split, target coordinates, and attention-independent T/M/I ROIs.
- Reuse the exact Stage 3C.4 FP32 pre-`W_O` target-contribution intervention at `t_pre` only; all other queries remain native and downstream computation recomputes naturally.
- Freeze P0--P5, A0--A3, carrier representations, quantitative gates, and the 15-test primary family before their corresponding scientific scores are inspected.
- Phase B is gated by isolated all-layer `t_pre` necessity. Keep R, Q, and `h_pre` interpretations separate and never patch visual K/V in Phase B.
- Use `base_problem_id` and unnormalized loss/restoration as primary. Do not manipulate sinks, search earlier history, run Stage 4, multi-evidence refresh, or failure analysis.

## Current State

- Done: Stage 3C.4 passed 20/20 and localized the largest added loss to T0→T1, with O2 temporal redundancy.
- Done: user explicitly authorized the complete Stage 3C.5 plan on 2026-09-04.
- Done: access/GPU policy, environment, the complete plan, Stage 3C.4 handoff, and reusable runtimes were reviewed.
- Done: all 24 primary bases completed P0--P5, A0--A3, gated R/Q/`h_pre`, R_last2/R_last4, and reduced T/M/I control scoring.
- Done: technical acceptance and independent raw-artifact validation pass 20/20; all 13 figures and required reports are complete.
- Blocked: none.
- Most recent useful observation: Stage 3C.4 median base-aggregated retention fell from 0.8436 at T0 to 0.6515 at T1; target loss exceeded M/I loss on all 24 bases.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Exact contribution semantics | `code/visual_reasoning/stage3c4/runtime.py`; `outputs/stage3c4/audit/` | Supplies the validated `c_T` intervention at one query | confirmed |
| Frozen cohort/targets | `outputs/stage3c4/cohort/`; `outputs/stage3c4/config/frozen_targets.json` | Prevents coordinate and cohort drift | confirmed |
| Immediate temporal increment | `outputs/stage3c4/analysis/spatiotemporal_classification.json` | Motivates isolation of `t_pre` | confirmed |
| Q cache mechanics | `code/visual_reasoning/stage3b0/cache.py` | Supplies validated all-layer token-position K/V patching | confirmed |
| Current residual mechanics | `code/visual_reasoning/stage3b5/boundaries.py` | Supplies exact `h_pre` replacement with natural recomputation | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3C.3-R v1 bookkeeping | BF16 partition and endpoint drift | supported | retain FP32 contribution/rest arithmetic and exact endpoint audits | do not reintroduce BF16 contribution bookkeeping |
| Stage 3C.3 routing intervention | routing changed but evidence preference did not reciprocally follow | confirmed | use evidence preference, not routing/attention, as the behavioral gate | do not infer handoff from attention or alpha-V alone |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| W4/W5-local `t_pre` retrieval | prior W4 causal paths and W5 descriptive phenotype | frozen P0/P1/P2 scopes at `t_pre` | evaluated; effect small |
| Distributed late/broad `t_pre` retrieval | Stage 3C.4 showed depth interaction | P3/P4/P5 at `t_pre` | supported; P4 selected |
| Immediate R carrier | `t_pre` becomes the nearest reasoning-cache source at `t*` | bidirectional R_last1 K/V patch | partial; below CRR gate |
| Q carrier | Stage 3B.0 showed Q carriage of a small prefill residual | bidirectional Q K/V patch | weak; below CRR gate |
| Current residual carrier | evidence may already be integrated before the historical target layer | bidirectional `h_pre(t*)` patch | strongest lead; pooled CRR below gate |

## Next-Step Decision

- Current bottleneck: Stage 3C.5 found broad `t_pre` necessity but no tested carrier met the frozen pooled CRR threshold; Target A and Target B differ sharply.
- Relevant memory item used: P4/P5 median loss 0.5172/0.4979 and `h_pre` Target-A/Target-B median CRR 0.3226/0.0205.
- Chosen next action: stop and return **GO — Current-Residual Mechanism** for review only.
- Why this action: `h_pre` is the strongest tested lead, while the pooled no-clean-carrier result and target heterogeneity require a separately reviewed design.
- What not to repeat: do not select layers from attention, infer causality from descriptive state readouts, patch visual donor K/V in Phase B, or expand to sinks/whole history.
- Stop condition: all 20 technical criteria are evaluated, one handoff classification and exactly one recommendation are written, and no later experiment is started.

### Prospective Quantitative Rules

- Phase-B gate: P5 loss is positive on at least 18/24 bases, Holm-significant, and median loss is at least 20% of the historical T0→T1 median added loss (`0.26138`).
- Necessary window: smallest P-scope with at least 80% of P5 median loss plus the same direction/significance requirements; otherwise P5.
- R expansion: run R_last2/R_last4 only if R_last1 is Holm-significant and positive on at least 18/24 bases but median normalized recovery is below 0.80.
- Carrier robustness: positive on at least 18/24 bases, Holm-significant, median normalized recovery at least 0.20, and median semantic restoration at least twice the paired-sham absolute shift.

### Step Result

- Action taken: completed the frozen broad-depth `t_pre` necessity family, gated carrier patches, short-R extension, target-specificity controls, and descriptive continuity/phenotype overlap.
- Result: technical PASS / **O5 — No Clean Carrier**. P4/P5 median loss was 0.5172/0.4979; h_pre was strongest (BCR 2.4347, CRR 0.1832) but no pooled carrier reached the frozen 0.20 CRR rule.
- Evidence saved: `outputs/stage3c5/`.
- Failure or issue: no technical failure; Target A h_pre recovery was 0.3226 while Target B was 0.0205, and R_last4 added only 0.0091 median CRR over R_last1.
- Lesson learned: the immediately preceding visual contribution is broad-depth and causally necessary, but its handoff is target-dependent and not cleanly readable from the tested R/Q/current-state candidates.
- Next implication: review a bounded current-residual mechanism design; do not automatically start it or manipulate a sink.
