# Phase 3B.5: Sequential residual-stream mediation and state-dependent recompute

## Current Objective

Determine where evidence identity becomes causally represented within the frozen late Qwen3-VL blocks, and whether source-state restoration followed by natural downstream recomputation explains the Stage 3B.4 block-versus-module gap.

## Active Constraints

- Reuse the exact 37 paired numeric primary bases and eight disjoint validation bases from Stage 3B.4.
- Reuse only frozen `E_d-1`/`E_d` and W4/F28_29 (layers 28--29) / W5/F32_33 (layers 32--33).
- Use paired O/O_sham/C/C_sham semantic restoration, exact current-position patches, self controls, and A5000 execution.
- Freeze all five block boundaries, the 40-test Holm family, validation gates, and decision rules before validation outcomes.
- The first-layer `h_pre` intervention is physically identical to the two-layer window-entry recompute arm; report it under both analyses without double-counting it as a separate hypothesis test.
- Do not use attention magnitude for selection and stop before head/path/ROI/Q-R/feature/neuron/multi-evidence/failure analysis.

## Current State

- Done: Stage 3B.4 passed its technical gate and found robust full-block restoration in 4/4 cells without a passing isolated Attention, MLP, or Joint attribution rule.
- Done: the user explicitly authorized `plan/stage3b5_plan.md` on 2026-09-01.
- Done: the installed Qwen3-VL decoder block was audited as pre-norm Attention, attention residual addition, pre-norm MLP, and MLP residual addition.
- Done: the five boundary hooks, exact 40-test Holm family, validation gates, and decision hierarchy were frozen before validation outcomes.
- Done: all eight disjoint A5000 validation bases passed exact baseline, state-capture, raw post-attention, current-position patch, downstream recompute, self, interface-equivalence, finite, deterministic, and paired-render controls.
- Done: the validation gate prospectively authorized the exact 37-base paired primary cohort.
- Done: all 37 bases, 1,480 paired boundary rows, 40 Holm-corrected tests, six analysis files, ten figures, acceptance report, and one recommendation are complete.
- Done: an independent persisted-artifact validator recomputed all 1,480 paired metrics and passed 20/20 checks.
- In progress: none.
- Blocked: none.
- Most recent useful observation: the frozen decision rule identifies qualifying post-Attention boundary gains in 3/4 cells, while W5 at `E_d` alone meets the upstream-state rule.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Full Block is robust in 4/4 cells while component rules fail | `outputs/stage3b4/analysis/decision_rule_evaluation.json` | Motivates state-boundary and recomputation tests | confirmed |
| Stage 3B.4 paired A5000 mechanics passed | `outputs/stage3b4/validation/validation_results.json` | Supplies the frozen bridge and validation cohort | confirmed |
| W4/F28_29 and W5/F32_33 are the retained fine windows | `outputs/stage3b4/config/stage3b4_config.json` | Fixes the only layers allowed in Stage 3B.5 | confirmed |
| Qwen block order is pre-norm Attention then pre-norm MLP with two residual additions | `.venv/lib/python3.12/site-packages/transformers/models/qwen3_vl/modeling_qwen3_vl.py` | Defines exact capture and patch boundaries | confirmed |
| A6000 numerical drift can be comparable to weak effects | `outputs/stage3b3_redesign/config/node03_drift_analysis.json` | Requires the established A5000 scientific path | confirmed |
| Stage 3B.5 independent method gate passed | `outputs/stage3b5/validation/validation_results.json` | Authorizes the frozen 37-base primary family | confirmed |
| Twenty-six of 40 boundary tests are robust; qualifying post-Attention gains occur in 3/4 fixed cells | `outputs/stage3b5/analysis/boundary_restoration_statistics.json`; `outputs/stage3b5/analysis/decision_rule_evaluation.json` | Selects the frozen Attention head/path recommendation | confirmed |
| All 1,480 paired metrics and the final decision independently recompute | `outputs/stage3b5/analysis/artifact_validation.json` | Validates the persisted result and report | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Original Stage 3B.3 unpaired restoration | Sham/target ratio exceeded the frozen gate | unknown | Keep paired semantic render controls | Do not substitute an uncontrolled patch contrast |
| Stage 3B.4 independent module-output patches | Full block was much stronger than isolated/precomputed module arms | unresolved by design | Test source-consistent state plus natural recomputation | Do not relabel the gap as a distributed representation without a sequential test |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Upstream residual origin | `h_pre` may already carry most block-restorable identity | Compare first-layer `h_pre` BMR with final `h_post_block` | partial: 1/4 cells; W5 `E_d-1` is borderline below threshold |
| Attention-boundary injection | Evidence may rise after Attention residual addition | Paired `h_post_attn - h_pre` boundary gain | supported by frozen rule in 3/4 cells |
| MLP/residual transformation | Evidence may rise after the MLP residual addition | Paired `h_post_block - h_post_attn` boundary gain | not identifiable from this difference because R3→R5 is structurally exact |
| State-dependent recomputation | Source-consistent state may outperform precomputed module-output patching | Compare R1/R3 with frozen Stage 3B.4 Joint/MLP | supported for R3 vs MLP in 4/4 and R1 vs Joint in W5 only |
| Cross-layer sequential mediation | Both layers may be needed to regenerate the full effect | Compare first-layer entry recompute, within-window boundaries, and final output | rejected by frozen rule |

## Next-Step Decision

- Current bottleneck: Stage 3B.5 is complete; the Attention head/path recommendation requires joint scientific review before any new plan or execution.
- Relevant memory item used: the frozen category counts are Attention 3/4, upstream 1/4, cross-layer 0/4, and MLP 0/4, with a structural R3/R5 equivalence caveat.
- Chosen next action: stop after reporting Stage 3B.5.
- Why this action: the authorized research action and all 17 acceptance criteria are complete, while the recommendation is not authorization for a head/path experiment.
- What not to repeat: do not use attention-selected targets, A6000/A5000 mixed scores, unpaired shams, or precomputed output restoration as the only mechanistic test.
- Stop condition: satisfied; no head/path/ROI/Q-R/feature/neuron/multi-evidence/failure analysis has started.

### Step Result

- Action taken: froze and validated the protocol, completed 37-base A5000 primary scoring, aggregated the 40-test family, audited the causal estimands, and independently validated all artifacts.
- Result: technical **PASS** (17/17) and **GO — Attention head/path localization** as a review-only recommendation. Post-Attention gains qualify in `E_d-1/W4`, `E_d-1/W5`, and `E_d/W4`; `E_d/W5` instead meets only the upstream-state rule.
- Evidence saved: `outputs/stage3b5/validation/validation_results.json`, `outputs/stage3b5/analysis/boundary_restoration_statistics.json`, `outputs/stage3b5/analysis/decision_rule_evaluation.json`, `outputs/stage3b5/analysis/artifact_validation.json`, and `outputs/stage3b5/summaries/stage3b5_summary.md`.
- Failure or issue: no technical failure. Interpretive limitation: R3 plus natural MLP recomputation and R5 are exactly equal by deterministic positionwise construction, so zero `G_mlp` is not a global MLP-null result.
- Lesson learned: source-consistent raw residual restoration can recover effects that precomputed module-output patches miss; normalized-input patches with recipient residual branches estimate a different, much weaker sufficiency quantity.
- Next implication: jointly review the heterogeneous Attention/upstream result and structural equivalence before defining any head/path plan. No next experiment is authorized.
