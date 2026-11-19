# Stage 0: Visual–Reasoning Instrumentation Memory

## Current Objective

Define and validate an instrumentation pipeline for continuous, evidence-specific visual dependence and reasoning-side support on approximately 30–50 MathVerse examples using Qwen3-VL-4B-Thinking.

## Active Constraints

- Treat `plan/overview.md` as the scientific source of truth.
- Analyze current-model behavior before designing a method.
- Do not use raw attention magnitude or prior FastV pruning as a causal-usage measure.
- Separate local teacher-forced effects from downstream free-rollout effects.
- Separate direct visual dependence, explicit generated-text memory, and latent hidden/KV carriers.
- Use the project GPU scheduler for model execution.
- Execute only Stage 0; do not begin Stage 1 automatically.
- The project-local `research-control` skill referenced by `AGENTS.md` is currently absent; this state transition used the repository protocol directly as a conservative fallback.

## Current State

- Done: Recorded the approved pivot, implemented the new non-PIQD pipeline, passed the paired smoke gate, completed and independently validated the 30-example full run, and preserved prior PIQD work only as historical smoke evidence.
- In progress: None; Stage 0 is complete and stopped before Stage 1.
- Blocked: None currently.
- Most recent useful observation: The fixed full run passed all instrumentation criteria and independent validation, but only 4/30 trajectories terminated correctly while 26/30 reached the 2,048-token safety cap.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| The active goal is analysis of when, what, why, how, and failure dynamics of visual reliance. | `plan/overview.md` | Defines the new research target. | confirmed |
| Qwen3-VL-4B-Thinking and MathVerse are the primary model and benchmark. | `plan/overview.md` | Prior 8B/FastV assumptions cannot be carried forward silently. | confirmed |
| Prior Phase 2 artifacts passed mechanical checks but are hook-smoke-only. | `workspace/phase_memory/phase_2b_phase2_audit.md` | Prevents overclaiming from pruning/attention proxies. | confirmed |
| MathVerse is recorded locally. | `workspace/dataset_inventory.md` | A dataset download should not be the first Stage 0 action. | confirmed |
| The project-local environment and A5000 runtime were verified with Qwen3-VL-4B-Thinking. | `workspace/env_state.md`, `outputs/stage0/environment.md` | Confirms the recorded Stage 0 artifacts were produced with the intended model and attention backends. | confirmed |
| The full 30-example pipeline passes all eight Stage 0 acceptance criteria. | `outputs/stage0/summaries/stage0_summary.json` | Establishes that the non-invasive instrumentation is ready for later planned analyses. | confirmed |
| All saved full-run token, span, attention, mapping, and boundary artifacts validate independently. | `outputs/stage0/summaries/validation.json` | Prevents relying only on the runner's completion claim. | confirmed |
| 26/30 fixed-budget trajectories are truncated; 4/30 are correct. | `outputs/stage0/summaries/stage0_summary.json` | Strongly constrains later eligibility and generation-protocol decisions. | confirmed |
| Five representative spatial overlays align with their source diagrams. | `outputs/stage0/summaries/visual_sanity_check.md` | Confirms qualitative inspectability without claiming causal use. | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Prior PIQD Phase 2 scientific interpretation | Mechanically valid tensors could not support final evidence claims. | supported: approximate static input-level FastV pruning, documented by Phase 2b audit | Validate causal meaning, not only tensor mechanics. | Do not promote a proxy because its implementation checks pass. |
| First new Stage 0 smoke run at 1,024 generated tokens | Sample 3 was truncated immediately after `</think>` while beginning its final response. | supported: saved response tail and `generated_token_count: 1024` in `outputs/stage0_smoke/examples/3/generation.json` | Increase the limit to 2,048 so normally terminating traces can finish, then distinguish an insufficient cap from repetitive non-termination. | Do not reuse the 1,024-token limit for this Thinking checkpoint. |
| Repaired smoke at 2,048 generated tokens | Sample 8 remained in a repetitive `Wait, maybe...` trajectory at the cap; samples 3 and 4 terminated at 1,486 and 1,343 tokens. | supported: saved response tail and results under `outputs/stage0_smoke_2048/examples/` | Keep 2,048 as a bounded safety cap and report repetitive non-termination as `truncated`, as required by the filtering report. | Do not keep raising the cap to chase termination of a repetitive trajectory. |
| Initial full-run summary | Nine examples failed `incremental_decode_alignment` even though IDs, scores, attention steps, and span ranges matched. | supported: Qwen prefix diagnostics showed incomplete multibyte symbols decode as `�` before being rewritten to `⊥` or `∠` | Build token display pieces against stable boundaries in the completed decode and verify exact reconstruction. | Do not assume decoded tokenizer prefixes are monotonically extending strings. |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Matched ROI knockout and counterfactual effects can measure evidence-specific direct dependence. | The overview identifies them as complementary causal tools. | Specify matched interventions, irrelevant-ROI controls, local effects, and free-rollout effects. | open |
| Reasoning-side states may carry acquired visual information. | The overview distinguishes prompt, generated-state, and explicit-text carriers. | Specify same-text/different-image cache interventions after direct-dependence instrumentation is valid. | deferred |
| Evidence demand, rather than elapsed time or uncertainty alone, drives visual access. | This is the overview's leading but non-exclusive hypothesis. | Design controlled order and evidence-availability comparisons in a later stage. | deferred |

## Next-Step Decision

- Current bottleneck: No further Stage 0 action remains; Stage 1 scope must explicitly address the small completed-trajectory pool before execution.
- Relevant memory item used: All 30 instrumentation bundles validate, but 26 trajectories are truncated at the fixed cap and only 4 terminate correctly.
- Chosen next action: Stop at the Stage 0 boundary and present the evidence without beginning Stage 1.
- Why this action: The authorized research action is complete, and generation-protocol or eligibility changes belong in a separately reviewed next-stage plan.
- What not to repeat: Do not reuse approximate FastV pruning as the operational definition of direct visual dependence.
- Stop condition: Every Stage 0 deliverable and acceptance criterion has an evidence-backed pass/fail status, and no Stage 1 work has begun.

### Step Result

- Action taken: Completed the paired smoke gate, ran the fixed 30-example full instrumentation subset, repaired a Unicode decode-validation false positive without rerunning the model, and independently validated every artifact.
- Result: Stage 0 passes all eight acceptance criteria; 30/30 bundles validate and Stage 1 was not started.
- Evidence saved: `outputs/stage0/summaries/stage0_summary.json`, `outputs/stage0/summaries/validation.json`, `outputs/stage0/summaries/decode_alignment_repair.json`, and `outputs/stage0/summaries/visual_sanity_check.md`.
- Failure or issue: 26/30 trajectories reached the 2,048-token safety cap; this is retained as a filtering limitation rather than hidden or retried.
- Lesson learned: Instrumentation validity and trajectory eligibility are separate gates; valid instrumentation does not make a truncated trace suitable for every later causal analysis.
- Next implication: Design and approve Stage 1 separately, explicitly accounting for the four completed correct trajectories and the high truncation rate.
