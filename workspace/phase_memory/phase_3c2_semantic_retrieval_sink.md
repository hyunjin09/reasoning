# Phase 3C.2: Semantic Alignment, Retrieval Demand, and Sink Dynamics

## Current Objective

Execute the user-approved `plan/stage3c2_plan.md` as one bounded, primarily descriptive action: construct a manually validated `M != T` cohort, characterize mention alignment versus independently causal task-required retrieval and attention-budget/sink dynamics, write exactly one review-only recommendation, and stop.

## Active Constraints

- Preserve Stage 0--3C.1 artifacts unchanged.
- Reuse exact Target A `E_d/W4/layer29/heads=[11,6,15,12]`, Target B `E_d-1/W4/layer28/heads=[16,0,3,6]`, and Stage 3C.1 noncausal controls.
- Define mention ROI `M`, task-required ROI `T`, irrelevant ROI `I`, and all semantic state labels without attention.
- Require `M != T`, manual semantic/ROI validation, exact token mapping, and at least 24 unique bases before primary extraction.
- Prefer the existing 37 causal-valid numeric bases; collect new examples only if the valid existing cohort is below 24.
- Use exact full-shape eager-Attention reconstruction and passive measurement only.
- Use `base_problem_id` as the statistical unit and Holm-correct the frozen primary family.
- Do not manipulate Q, K, alpha, sink, `h_pre`, source states, or routing.
- Do not start Stage 4, multi-evidence refresh, failure analysis, or any recommended causal experiment.

## Current State

- Done: Stage 3C.1 completed with 20/20 technical PASS and independent artifact validation.
- Done: access policy, GPU policy, environment state, Stage 3C.2 plan, prior phase memory, and promoted decisions were reviewed.
- Done: the project-local `research-control` skill is absent; the fully specified user-approved plan is the sole research action and repository rules supply fallback discipline.
- Done: 37 bases were screened without attention; 31 unique bases passed the manual `M != T`/T/M/I/state audit and six exclusions were preserved.
- Done: the two-A5000 smoke and full four-condition passive extraction completed in allocation `106936` through tmux session `8`.
- Done: 11,904 per-head rows, 2,976 head-set rows, 248 raw tensor archives, seven Holm-corrected contrasts, 14 figures, and all reports were persisted.
- Done: independent validation passed 12/12 artifact/invariant checks and Stage 3C.2 passed 20/20 acceptance criteria.
- Current status: Stage 3C.2 complete and stopped; recommendation awaits review.
- Blocked: none.
- Most recent useful observation: Stage 3C.1 found strong target-ROI routing at causal coordinates but target/head-dependent attention-to-causal-effect coupling, motivating semantic-alignment dissociation rather than treating attention as causal.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Stage 3C.1 exact reconstruction | `outputs/stage3c1/audit/reconstruction_check.json` | Supplies the validated passive measurement path | confirmed |
| Frozen causal targets and controls | `outputs/stage3c1/config/frozen_targets.json`; `outputs/stage3c1/config/control_heads.json` | Prevents Stage 3C.2 attention-based selection | confirmed |
| Independently causal task ROI | `outputs/stage3b7/roi_audit/roi_token_mapping.jsonl`; `outputs/stage3b7r/analysis/roi_path_statistics.json` | Defines `T` independently of current attention | confirmed |
| Exact histories and decisions | `outputs/stage3b2/annotations/discriminative_event_annotations.jsonl` | Supports blinded semantic-state and mention annotation | confirmed |
| Candidate sink phenotype | `outputs/stage3c1/analysis/sink_candidate_summary.json` | Freezes `<|im_start|>` as a descriptive candidate before Stage 3C.2 | confirmed/descriptive |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 2 attention-only timing | Mention-centered ROI attention did not identify acquisition timing | supported | Semantic alignment and causal retrieval must be separated by independent annotation | Do not define `M`, `T`, or states from attention |
| Stage 3C.1 row-only reconstruction | BF16 drift under changed tensor shape | supported | Reuse installed full tensor shapes exactly | Do not substitute mathematically equivalent row-shaped recomputation |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Task-conditioned retrieval | T exceeded M at retrieval in all 62 target/base events across density, QK, alpha-V, and post-`W_O` | Future routing intervention only if separately approved | supported/descriptive |
| Alignment-dominant routing | Stage 2C attention was mostly mention-centered | M dominated earlier in 40/62 events but not at retrieval | not supported as the sole phenotype |
| Alignment-then-retrieval | Stage 2 and Stage 3 findings may reflect different times | 40/62 events crossed from M>T early to T>M at retrieval | supported/descriptive |
| Sink release versus persistence | `<|im_start|>` carries large natural mass | 46/62 sink-release, 13/62 persistent, 3/62 non-sink under the exploratory rule | heterogeneous/descriptive |

## Next-Step Decision

- Current bottleneck: review whether the descriptive T-over-M sharpening is strong and specific enough to justify a separately designed routing-causality experiment.
- Relevant result: 31/31 base-aggregated temporal crossovers were positive and causal-vs-noncausal enrichment was positive on 31/31 bases, but Target-B head 6 stayed near-zero and sham image variation is measurable.
- Chosen next action: none. Stage 3C.2 stops with one review-only recommendation.
- Why stop: the authorized research action is complete, and testing the recommendation would manipulate routing beyond this plan's scope.
- What not to infer: QK sharpening does not prove causal retrieval; sink loss does not show dispensability; attention mass is not an information fraction.
- Stop condition: satisfied with 20/20 technical PASS and no later intervention started.

### Step Result

- Action taken: completed the attention-blind cohort freeze, exact passive extraction, descriptive analysis, controls, audits, figures, and reports.
- Result: 31-base technical PASS; 40/62 alignment-then-retrieval and 22/62 retrieval-only events; candidate-sink release is common but heterogeneous.
- Evidence saved: `outputs/stage3c2/` and `runs/stage3c2_passive_{smoke,full}/tmux.log`.
- Failure or issue: no technical failure; limitations include teacher-forced retrieval coordinates, no A0 state, inexact lexical matching across paired states, variable M area, and measurable O/O_sham attention variation.
- Lesson learned: semantic mention alignment and task-conditioned target sharpening are temporally separable at these causal anchors, but raw attention still cannot identify causal acquisition or sink function.
- Next implication: review the sole relevant-vs-distractor routing-causality recommendation; do not execute it without a new approved plan.
