# Phase 3B.2: Counterfactual visual-source switching

## Current Objective

Determine whether the identity of future visual K/V causally controls the upcoming discriminative evidence decision while the accumulated recipient history is held fixed.

## Active Constraints

- Use the exact frozen 49-base Stage 3A cohort; `base_problem_id` is the statistical unit.
- Freeze manual `E_d` annotations and all switch checkpoints before causal scoring.
- Run bidirectional O→C and C→O switches with self and sham controls across all 36 language layers.
- Selection and timing must not use attention; any Stage 2C comparison is secondary and post-freeze.
- Stop before layer/Q/R/module/head/path localization, ROI-specific switching, or any later-stage experiment.

## Current State

- Done: Stage 3B.1 technically passed on 49 bases and 489 checkpoints, with 0/49 reaching retention >=0.80 and median E0-1 retention 0.1114.
- Done: Stage 3B.2 technically passed all 16 acceptance criteria on 49 bases and 588 frozen checkpoints; all 144 secondary rollout checkpoints also completed.
- Blocked: None.
- Most recent useful observation: bidirectional donor-source control remained present for 49/49 bases at both E_d-1 and E_d, with median normalized BRI 0.9703 and 0.8022 and sham/target ratios 0.0107 and 0.0115.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Stage 3A localized visual CE was positive for 49/49 bases | `outputs/stage3a/analysis/primary_statistics.json` | Establishes a clean evidence-specific causal target | confirmed |
| Stage 3B.1 found 0/49 rho>=0.80 and median E0-1 retention 0.1114 | `outputs/stage3b1/analysis/prefill_vs_postprefill_gain.json` | Motivates replacing rather than removing future visual input | confirmed |
| Stage 3B.0 validated all-layer post-RoPE K/V cache replacement and GQA layout | `outputs/stage3b0/smoke/hook_transparency.json` | Supplies the technical basis for source switching | confirmed |
| Bidirectional source switching controlled the frozen evidence decision at E_d-1 and E_d for 49/49 bases | `outputs/stage3b2/analysis/bidirectional_retrieval_statistics.json` | Distinguishes evidence-specific visual-source control from a purely generic cutoff effect | confirmed |
| Fixed-seed source-switched rollouts usually changed the first discriminative identity | `outputs/stage3b2/scoring/rollout_summary.json` | Secondary behavioral validation of the teacher-forced preference result | confirmed with one-seed limitation |
| 37/49 E_d coordinates use semantic teacher-forced leads rather than exact baseline-trace continuations | `outputs/stage3b2/annotations/annotation_audit.md` | Limits exact natural-trajectory timing claims | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3B.1 all-visual cutoff | Strong damage but no evidence-identity specificity | supported limitation of the intervention, not a runtime failure | Preserve visual availability and switch only its identity | Do not interpret cutoff damage alone as target-evidence retrieval |
| Initial Stage 3B.2 custom attention-implementation name | Changed the model's causal-mask construction and broke no-switch score reproduction | supported by failed smoke comparison | Preserve the model's `eager` config and override only the eager operation locally | Do not introduce a new attention implementation name for this intervention |
| Full-cohort Stage 3A replay on base 126 | One of six divergent-tail log probabilities differed by 2.31e-7 | benign floating-point variance; token IDs and all other scores matched | Report bit-exact and tolerance results separately | Do not hide the 48/49 bit-exact count or treat 2.31e-7 as semantic divergence |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Persistent late evidence-specific retrieval | Direct vision remains necessary near E0 | Bidirectional source switching through `E_d` | supported at the frozen teacher-forced decision |
| Generic/distributed visual support as the sole explanation | All-V removal may be broadly off-manifold | Low BRI despite high Stage 3B.1 cutoff damage, or sham-comparable shifts | contradicted by strong target-specific switching; distributed support may still coexist |
| Earlier evidence commitment without late source control | The identity-specific effect may disappear before `E_d` | Frozen retrieval-timing curves | contradicted on the sampled grid |

## Next-Step Decision

- Current bottleneck: source identity and late timing are established, but the layer or carrier of visual-to-reasoning transfer remains unknown.
- Relevant memory item used: the frozen late-GO rule, reciprocal effects, sham controls, and the 37/49 semantic teacher-forced-coordinate limitation.
- Chosen next action: stop Stage 3B.2 and return **GO — Layer-wise visual-to-reasoning transfer analysis** for joint review; do not execute it.
- Why this action: both predeclared late checkpoints pass the GO rule, while the current all-layer/all-visual intervention cannot localize transfer.
- What not to repeat: do not infer a layer, ROI, Q/R carrier, attention pathway, or natural free-running decision time from the present aggregate intervention.
- Stop condition: satisfied. No follow-on experiment is authorized or started.

### Step Result

- Action taken: manually froze 49 E_d annotations and 588 checkpoints; validated and ran all-layer visual-source switching in both directions with self/sham controls; ran 576 secondary fixed-seed rollouts; aggregated cutoff, evidence-type, and attention comparisons.
- Result: technical PASS (16/16). Median unnormalized BRI was 12.0118 at E_d-1 and 9.0923 at E_d; 49/49 were bidirectionally source-consistent at both checkpoints; both late checkpoints pass the frozen GO rule.
- Evidence saved: `outputs/stage3b2/summaries/stage3b2_summary.md`, `outputs/stage3b2/summaries/stage3b2_acceptance.json`, and the complete `outputs/stage3b2/` tree.
- Failure or issue: the project-local `research-control` skill was absent; one invalid smoke implementation and the base-126 2.31e-7 replay exception are preserved and documented.
- Lesson learned: preserving visual availability while counterfactually changing its identity reveals strong late evidence-specific control that all-visual cutoff alone could not identify.
- Next implication: review the GO recommendation and the teacher-forced-coordinate limitation before authorizing any layerwise analysis.
