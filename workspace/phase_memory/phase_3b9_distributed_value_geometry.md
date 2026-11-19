# Phase 3B.9: Distributed Value Geometry

## Current Objective

Execute the user-approved Stage 3B.9 action: distinguish shared higher-dimensional, locally compact/problem-specific, shared-plus-private, or globally/locally distributed causal Value geometry, then issue one recommendation and stop.

## Active Constraints

- Preserve Stage 3B.8 and all earlier artifacts unchanged.
- Freeze exactly Target A `E_d/W4/layer29/heads=[11,6,15,12]` and Target B-R `E_d-1/W4/layer28/heads=[16,0,3,6]`.
- Reuse only the audited Stage 3B.8 v3 512D pre-`W_O` exact eager-Attention recomposition effect vector.
- Treat the 57 Stage 3B.8 geometry bases as training/design only, never fresh confirmation.
- Obtain at least 24 fresh, protected-set-disjoint Phase-A bases and at least 12 separate Phase-B bases with one original plus four prospectively chosen semantic values.
- Freeze rank families, semantic/sham/random bases, cohorts, exclusions, and Phase-B values before their causal projection outcomes are read.
- Use `base_problem_id` as the statistical unit; aggregate leave-one-value-out folds within base first.
- Attention is secondary and post-freeze only.
- Do not start vision-encoder/projector, MLP-feature/neuron, Q/R lifecycle, multi-evidence refresh, failure analysis, or another geometry rescue stage.

## Current State

- Done: Stage 3B.8 completed with graded causal Value transport but no robust universal rank-8 compression on untouched confirmation.
- Done: `plan/stage3b9_plan.md`, machine-local access/GPU policies, active research state, and promoted Stage 3B.8 decision were reviewed.
- Done: the project-local `research-control` skill was searched for but is absent; the explicit user-approved plan is the fixed research action and no recursive action selection is allowed.
- Done: the existing two-A5000 Slurm allocation (job 106936, tmux 8) is alive and available through the project scheduler policy.
- Done: immutable history, the exact two targets, the 57-base historical SVD/sham bases, the full frozen rank family, and 100 random controls per target/rank were materialized before fresh scoring.
- Done: 51 initial candidates and a blinded edit-valid expansion were screened; all retained edits and ROI mappings were manually validated before generation.
- Done: locked-protocol prospective generation completed for 75 protected-set-disjoint bases: Phase A 29 correct/24 wrong and Phase B 15 correct/7 wrong, with no truncation or invalid output.
- Done: all 44 completed-correct candidates received a score-/fit-/attention-blind strict-E_d audit. One malformed Phase-A target was rejected, leaving 28 Phase-A and 15 Phase-B bases.
- Done: Phase-B full-V applicability retained 14/15 bases at each target (minimum 12); its leave-one-value-out bases and random seeds were frozen before projected scoring.
- Done: the seven-base blind Phase-A repair expansion produced five effective completed-correct traces; all five passed a score-/fit-/attention-blind strict-E_d audit, four entered the pre-registered N=32 ceiling by ascending base ID, and one is preserved as reserve.
- Done: expanded full-V applicability retained exactly 24/32 bases at both targets, satisfying the frozen Phase-A minimum before any rank projection outcome existed.
- Done: Phase-A learned/complement/sham/random rank scoring completed on the frozen N=24 confirmation cohort; all 24 bases are present exactly once and all shard-level mechanical controls pass.
- Done: Phase-B projected local/global/random leave-one-value-out scoring completed on all 15 frozen bases; all 15 bases are present exactly once and all shard-level mechanical controls pass.
- Done: the prewritten Phase-A and Phase-B aggregations, permitted post-freeze secondary diagnostics, and final Stage 3B.9 validation/reporting completed.
- Done: Phase A supports `Shared-Moderate-Dimensional` geometry at the smallest passing rank 24 for Target A and rank 16 for Target B-R on the fresh N=24 cohort.
- Done: Phase B does not support the strict local rank-1/2 criterion at either target; median Local SR is 0.365--0.470 and median Local CR is 0.419--0.613 across ranks 1--2.
- Done: Stage 3B.9 passes 20/20 technical criteria with joint outcome `G1 — Shared higher-dimensional` and the review-only recommendation `GO — Multi-Evidence Causal Refresh`.
- Blocked: none.
- Most recent useful observation: on fresh confirmation, shared causal recovery crosses the frozen 0.80/0.30 rule at rank 24 for Target A and rank 16 for Target B-R, while same-problem leave-one-value-out rank-1/2 recovery remains well below 0.80 despite exceeding random controls.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Graded late-W4 causal Value response at both frozen targets | `outputs/stage3b8/dose_response/dose_response_statistics.json` | Establishes that Stage 3B.9 studies geometry, not whether Value is causal | confirmed |
| Shared rank-8 primary compression failed despite random/sham specificity | `outputs/stage3b8/analysis/subspace_restoration_statistics.json`; `outputs/stage3b8/analysis/random_control_statistics.json` | Leaves shared higher-rank, local, and mixture hypotheses open | confirmed |
| Exact audited v3 endpoint has zero historical score error | `outputs/stage3b8/audit/reconstruction_validation.json` | Defines the only valid representation/intervention endpoint | confirmed |
| Stage 3B.8 has 57 unique geometry bases and protected Stage 3B.7/3B.7-R sets | `outputs/stage3b8/config/discovery_confirmation_split.json` | Defines training-only and exclusion sets | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3B.8 v1/v2 representation | Endpoint score errors 0.1196/0.1422 | supported BF16 reduction/round-trip mismatch | Use exact v3 recomposition and direct endpoint assignment | Do not revive ROI-only reduction or subtract/add endpoints |
| Stage 3B.8 universal rank 8 | Strong discovery fit but weak untouched transfer | unknown; alternative explanations remain open | Specificity against random/sham is not sufficient for compression | Do not reinterpret rank 8 as a positive universal result |
| Initial Stage 3B.9 expansion manifest | Fresh Phase-A candidate 751 overlapped the frozen 57-base historical fit set | supported cohort-construction oversight, detected by full protected-set re-audit before its generation | Recheck disjointness against the materialized cohort split, not only the nominal unseen range | Base 751 is versioned out in `config/generation_expansion_shards_v2`; do not count or generate it |
| Long-trace token serialization | Prefix-by-prefix decoding scaled quadratically on 20k+ tokens | supported by code inspection; GPU generation completed while CPU remained occupied in `_incremental_decode_pieces` | Use the regression-tested linear ByteLevel decoder; it exactly reproduced all 21,857 saved token pieces in 0.037 s | Do not restore quadratic prefix decoding for Qwen ByteLevel traces |
| First Phase-A full-V launch | Slurm workers exited before model scoring with `ModuleNotFoundError: scripts` | supported environment-path error; no causal artifact was created | Include both `code` and repository root in `PYTHONPATH`; the corrected identical run completed | Do not launch repository-namespace runners with `PYTHONPATH=code` alone |
| Phase-A prospective applicability | Only 22/28 strict-E_d bases passed the frozen both-target full-V gate | confirmed gate result; explanation was not needed for the repair choice | The score-blind expansion added two both-target-usable bases and reached the unchanged minimum at 24/32 | Do not lower the gate or start Phase-A projection scoring below N=24 |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Shared moderate/high-dimensional geometry | Rank 8 may simply be too small | Fresh causal rank curve at frozen ranks 1--48 | supported at rank 24 / 16 |
| Local low-dimensional/global heterogeneous geometry | Problems may use differently oriented compact codes | Four-way leave-one-value-out local subspaces at ranks 1--3 | not supported by frozen rank-1/2 rule |
| Shared plus private geometry | Learned rank 8 is non-arbitrary but incomplete | Compare fresh global curve, local held-out recovery, and complements | not selected by frozen outcome matrix |
| Broadly distributed local and global geometry | Complement effects remain large historically | Failure of both fresh shared and local rank-1/2 rules | not supported because Phase A passes |

## Next-Step Decision

- Current bottleneck: user review of the completed Stage 3B.9 result before any later plan is selected or authorized.
- Relevant memory item used: fresh shared-rank confirmation passes only at moderate ranks, while local rank-1/2 held-out recovery fails the frozen compression criterion.
- Chosen next action: stop after reporting the completed Stage 3B.9 result.
- Why this action: the authorized research action and its final validation are complete; the GO label is a recommendation, not authorization to run the next experiment.
- What not to repeat: do not fit on fresh confirmation, choose Phase-B values after vector inspection, add ranks after outcomes, use attention for selection, or launch another rescue stage.
- Stop condition: after shared-rank confirmation, local leave-one-value-out geometry, frozen secondary diagnostics, one geometry classification, and one GO/REDIRECT recommendation; no later experiment starts.

### Step Result

- Action taken: completed and mechanically validated all frozen scoring, then ran the prewritten primary aggregations, post-freeze secondary diagnostics, and finalizer.
- Result: 20/20 technical PASS; shared rank 24 (Target A) and rank 16 (Target B-R) pass prospectively, local rank 1--2 does not; joint outcome `G1 — Shared higher-dimensional`.
- Evidence saved: `outputs/stage3b9/phase_a_shared/analysis/`, `outputs/stage3b9/phase_b_local/analysis/`, `outputs/stage3b9/phase_c_secondary/`, `outputs/stage3b9/analysis/`, and `outputs/stage3b9/summaries/`.
- Failure or issue: none in final scoring or aggregation. The earlier base-751 exclusion and serialization/runtime repairs remain preserved historical implementation lessons.
- Lesson learned: the causal Value geometry contains reproducible shared structure, but the smallest prospectively passing shared code is moderate-dimensional rather than rank 8; within-problem rank-1/2 structure is specific versus random yet insufficient for most held-out causal recovery.
- Next implication: return `GO — Multi-Evidence Causal Refresh` for review and stop; do not begin that experiment without a new approved plan.
