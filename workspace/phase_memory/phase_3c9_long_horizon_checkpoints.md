# Phase 3C.9: Dedicated Long-Horizon Causal Checkpoints

## Current Objective

Execute `plan/stage3c9_plan.md` as one bounded action: prospectively construct a dedicated long-horizon cohort, test event-local source sensitivity and causal checkpoint rescue, characterize lifetime/repeated formation, run route decomposition only if gated, issue one recommendation, and stop.

## Active Constraints

- Preserve Stage 3C.8 and all earlier artifacts.
- Freeze cohort, events, spans, local-use readouts, neighboring controls, and intervention families before causal scoring.
- Target 48 / minimum 40 unique primary bases plus eight disjoint validation bases; stop primary inference below 40 after at most 1,000 screened trajectories.
- Select using no attention or prior causal outcomes; aggregate inference by `base_problem_id`.
- Use both W8 and W16 source windows, event-local readout as primary, and final-use as secondary.
- A checkpoint claim requires source sensitivity plus native span K+V rescue; necessity is supporting only.
- Use only the four A6000 GPUs already assigned to tmux session 9 / Slurm job 108085; request no additional GPUs and do not mix preserved A5000 outcomes into primary inference.
- Do not start sink causality, residual-feature learning, unconstrained history search, Stage 4, multi-evidence refresh, or failure analysis.

## Current State

- Done: Stage 3C.8 passed 25/25 and established strongly recency-dominant, phase-specific token-cache carriage.
- Done: Stage 3C.8 long-horizon Phase D was gated off with 15 eligible fresh bases versus 28 minimum; this is cohort infeasibility, not a causal null.
- Done: Stage 3C.9 plan read completely; implementation and stopping rules frozen in `workspace/stage3c9_implementation_plan.md`.
- Done: deterministic attention-blind screening, annotation, edit/ROI, causal-runtime, analysis, and validation code is implemented and covered by the Stage 3C9 regression suite.
- Done: the pre-score coordinate amendment freezes zero-based generated-token coordinates, strict downstream bridges, control eligibility, and the C3 distinct-final-readout rule before any causal score exists.
- Done: the pre-score runtime amendment preserves native eager attention while using a `DynamicCache` and bounded 128-query chunks, with exact cached-versus-full parity as a prospective validation gate; this avoids materializing full long-prefix attention tensors on an A5000.
- Done: calibration v2 passed 17/17 and froze one fixed A6000 streaming-cached path (2,048-token chunks with allocator-cache release) for every Stage 3C.9 causal condition.
- Done: the clean A6000 prospective screen completed 600/600 unique Vision Dominant trajectories: 391 correct, 207 wrong, two 40,960-token cap hits, and zero invalid. All 600 per-example bundles are complete and the four A5000 provenance shards remain excluded.
- Done: score-blind semantic, edit, and ROI review yielded 57 fully valid unique bases; eight disjoint validation bases and 48 primary bases were frozen, with one valid reserve and no attention or causal-score selection.
- Done: the disjoint mechanics cohort passed all 16/16 validation checks, including exact coordinates/hashes, source-suppression isolation, cache-patch selectivity, route ordering, deterministic replay, and finite scores.
- Done: all 48 primary bases completed source sensitivity, checkpoint rescue, and lifetime scoring; Phase D was correctly gated off, all required reports/13 figures were created, independent output validation passed 16/16, and the Stage 3C.9 suite passed 72/72.
- Done: a post-hoc read-only stability audit found that the exact two-event C2 count is cross-path/threshold sensitive, while zero repeated-checkpoint bases is unchanged across every reported sensitivity check.
- Blocked: project-local `research-control` skill is absent; the explicit user-approved plan governs this bounded action directly.
- Most recent useful observation: the missing evidence is repeated checkpoint formation over long trajectories; another late-coordinate token atlas would not resolve it.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Immediate carrier recency | `outputs/stage3c8/analysis/position_vs_type_analysis.json` | Motivates repeated short-lived checkpoints over persistent distant-token storage | confirmed |
| Phase-specific carrier taxonomy | `outputs/stage3c8/analysis/phase_specificity_analysis.json` | Prevents assuming one universal event-token class | confirmed |
| Long-horizon cohort shortfall | `outputs/stage3c8/phase_d_anchor/gate.json` | Requires a dedicated prospective cohort rather than interpreting a null | confirmed |
| Exact cache-rescue mechanics | `outputs/stage3c7/audit/artifact_validation.json` | Supplies validated within-condition native-GQA K/V patch semantics | confirmed |
| Exact target-ROI suppression | `outputs/stage3c4/audit/artifact_validation.json` | Supplies validated all-layer/all-head contribution suppression | confirmed |
| Prospective screen result | `outputs/stage3c9/prospective_generation/raw/`; `outputs/stage3c9/cohort/screening_accounting.json` | Supplies the completed attention-blind A6000 screen for score-blind cohort qualification | 600/600 complete; 391 correct, 207 wrong, 2 truncated, 0 invalid |
| Pre-score protocol amendments | `outputs/stage3c9/config/prescore_coordinate_amendment.json`; `outputs/stage3c9/config/prescore_runtime_amendment.json` | Freezes coordinate semantics and the memory-bounded execution path before causal scoring | confirmed before scores |
| Stage 3C9 regression suite | `tests/stage3c9/`; `tests/stage3c4/`; related Stage 3C5/3C7/3C8 suites | Checks candidate rules, exact controls, cached coordinates, streaming mechanics, outputs, and inherited suppression behavior | 132 passed with related suites |
| Stage 3C.9 primary result | `outputs/stage3c9/analysis/long_horizon_checkpoint_summary.json`; `outputs/stage3c9/analysis/repeated_checkpoint_analysis.json` | Directly evaluates repeated sparse checkpoints on the frozen long-horizon cohort | 2 nominal C2 events; 0/48 repeated bases |
| Cross-phase score stability | `outputs/stage3c9/analysis/posthoc_score_stability.json` | Qualifies the precision of the nominal checkpoint count without changing the frozen result | 24/33 source gates changed; repeated count remained 0 |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3C.8 Phase-D cohort | 15 eligible versus 28 minimum | supported cohort-feasibility failure | construct a cohort prospectively for multi-event long reasoning | do not filter the Stage 3C.8 atlas by its effects |
| Prior multi-rank generation | overlapping Slurm steps used the same GPU | supported launch-layout error | use one three-rank process launch with rank-disjoint shards | do not launch overlapping one-task steps |
| Prior config launch | stale model snapshot path | supported launch configuration error | read checkpoint from frozen config | do not hand-copy snapshot hashes |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Repeated dynamic checkpoints | immediate cache carriage is strong but decays by distance 4--16 | W8/W16 source deficit plus separated event-span rescue | open |
| Persistent reasoning-side memory | some earlier states may survive beyond the atlas window | local versus 65+/final rescue | open |
| Direct visual refresh | later events may reacquire target evidence locally | gated direct W8 versus prior-route perturbation | open |
| Distributed state | source matters but no 1--8-token span rescues | compare source-sensitive C1 events with span and neighbor rescue | open |

## Next-Step Decision

- Current bottleneck: Stage 3C.9 produced no repeated checkpoint pairs and the exact isolated-checkpoint count is sensitive to cross-phase BF16 score-path drift.
- Relevant memory item used: 0/48 bases satisfy the frozen repeated-checkpoint criterion; only base 38 has a nominal C2 that survives the 0.15 effect floor and a distinct distal readout.
- Chosen next action: none. Stage 3C.9 is complete and stopped for review.
- Why stop: the Phase-D gate failed prospectively (0 versus 16 required), and resolving score-path stability or expanding pair yield would be a separately reviewed action.
- What not to repeat: do not treat the nominal two-event C2 count as precise, interpret base 149's right-censored lifetime as demonstrated decay, or run route decomposition from a failed gate.
- Stop condition: satisfied; all Stage 3C.9 reports, validation, and exactly one qualified recommendation are complete.

### Step Result

- Action taken: completed the clean four-rank A6000 prospective screen under the locked official Thinking protocol.
- Result: 600/600 raw outcomes were preserved: 391 correct, 207 wrong, two safety-cap truncations, and zero invalid; 598/600 terminated normally at EOS.
- Evidence saved: raw rank-disjoint bundles and shard summaries under `outputs/stage3c9/prospective_generation/raw/`; protocol/provenance freezes under `outputs/stage3c9/config/`.
- Failure or issue: bases 351 and 676 reached the 40,960 safety cap. This 0.33% cap-hit rate does not indicate systematic protocol failure and both remain excluded from completed-correct qualification.
- Lesson learned: the A6000 screen is operationally feasible and supplies substantially more completed-correct candidates than the minimum cohort size, but semantic/edit/ROI eligibility remains unknown until blinded review.
- Next implication: run deterministic collection and score-blind candidate drafting, then manually audit before cohort freeze; do not start causal scoring or inspect causal effects early.

### Final Result

- Action taken: froze 8 validation plus 48 primary bases after score-blind semantic/edit/ROI review, passed 16/16 mechanics checks, and completed the full gated Stage 3C.9 pipeline on the canonical A6000 path.
- Result: 29/144 events were Phase-A source-sensitive under W8/W16, but only two nominal event spans classified C2, none C3; 0/48 bases had two separated checkpoints, and Phase D did not run.
- Lifetime: both automated labels are `L-Short`; base 38 has direct distal evidence for decay, while base 149 is right-censored because local and final readouts coincide.
- Validity qualification: Phase-A-versus-Phase-B source-loss recomputation differs materially for small effects, changing 24/33 source gates. The exact checkpoint count is provisional, but the zero repeated-checkpoint result is invariant across reported sensitivity analyses.
- Evidence saved: `outputs/stage3c9/`; the main report is `outputs/stage3c9/summaries/stage3c9_summary.md` and the validity diagnostic is `outputs/stage3c9/analysis/posthoc_score_stability.md`.
- Decision: technical PASS; no support for recurrent sparse checkpoints under the tested assay; stop before route or later experiments.
