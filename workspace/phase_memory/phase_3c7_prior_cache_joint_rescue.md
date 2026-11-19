# Phase 3C.7: Prior-Cache and Residual Joint Rescue

## Current Objective

Execute the user-approved `plan/stage3c7_plan.md` as one bounded causal action: test within-condition native `t_pre` K/V cache rescue of the exact P4 deficit, test frozen residual-plus-downstream-cache joint rescue, issue one recommendation, and stop.

## Active Constraints

- Preserve all earlier artifacts and reuse the exact seven validation and 24 primary bases, Target A/B definitions, T ROI, P4 layers 16--35, all logical heads, seed 1234, and A5000 runtime.
- Use native post-RoPE K and projected V in the model's 8-KV-head GQA layout; patch only `t_pre`, never visual or current-query K/V.
- Keep O/C within-condition donors, report conditions separately, then sign-align and average within `base_problem_id`.
- Freeze Target-A `L33 h_post_attn` with downstream cache layers 34--35 and Target-B `L35 h_pre` with downstream cache layer 35 before scoring.
- Run joint downstream K/V decomposition only if J4 is substantial. Optional rollouts are prospectively omitted.
- Do not run token-type, sink, residual-feature, R_last2/4, Stage 4, multi-evidence, or failure experiments.

## Current State

- Done: Stage 3C.6 completed with O4 Residual Insufficiency and exact P4 reproduction.
- Done: Stage 3C.7 completed on the frozen seven-base validation and 24-base primary cohorts; all required mechanics, primary analyses, the Target-A-gated decomposition, reports, and independent validation are complete.
- In progress: none; the phase is stopped at its required boundary.
- Blocked: project-local `research-control` skill is not installed; the explicit user-approved plan and repository research-action boundary govern this action directly.
- Most recent useful observation: native `t_pre` K+V cache rescue exactly reaches the native endpoint for both targets, with robust V-dominant effects; Target A additionally shows near-complete residual/downstream-cache complementarity, while Target B does not reach the frozen substantial-joint threshold.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Exact P4 deficit and cohort | `outputs/stage3c6/config/`; `outputs/stage3c6/cohort/` | Defines the recipient and independent sample units | confirmed |
| Late incomplete residual rescue | `outputs/stage3c6/analysis/current_residual_classification.json` | Motivates testing prior cache and joint rescue | confirmed |
| Frozen residual points | `outputs/stage3c6/phase_b_boundary/boundary_statistics.json`; `outputs/stage3c6/phase_a_hpre_scan/layer_statistics.json` | Fixes A L33 post-attention and B L35 pre-attention without Stage 3C.7 outcome selection | confirmed |
| Native token-cache implementation | `code/visual_reasoning/stage3c5/carriers.py` | Provides validated post-RoPE K/projected-V capture semantics | confirmed |
| Suppression mechanics | `code/visual_reasoning/stage3c4/runtime.py` | Recreates the exact target-ROI P4 deficit | confirmed |
| Stage 3C.7 independent validation | `outputs/stage3c7/audit/artifact_validation.json` | Recomputes raw metrics and passes all 28 artifact/mechanics checks | confirmed |
| Cache and joint classification | `outputs/stage3c7/analysis/two_query_classification.json` | Records C-KV for both targets, O2 for Target A, and O1 for Target B | confirmed |
| Frozen acceptance result | `outputs/stage3c7/summaries/stage3c7_acceptance.json` | Records 20/20 PASS and confirms that no follow-on was started | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3C.5 cross-image R_last1 | weak pooled semantic recovery | state mismatch remains plausible but unproven | test cleaner within-condition native/suppressed cache rescue | do not infer cache irrelevance from cross-image transplantation |
| Stage 3C.6 current residual | neither target reached robust RR 0.50 | confirmed incomplete rescue | retain suppressed cache when testing residual alone and combine only at frozen downstream scope | do not treat current residual as complete mediation |
| Earlier candidate-state assumption | candidate-specific states were not always bit-identical | supported by saved validation | preserve candidate-specific donors | do not collapse candidate donors |
| Stage 3C.7 first smoke launch | the overlapping step inherited two tasks and both targeted one output path | supported by duplicate model loads/progress lines in the preserved log | set `--ntasks=1` explicitly for a one-GPU smoke | do not rely on the allocation's inherited task count |
| Unscoped repository pytest collection | pytest entered vendored code and `workspace/uv_cache` and collided on repeated test basenames | supported by 1,549 collection errors before any Stage 3C.7 failure | scope repository regression checks to `tests/` and use `--import-mode=importlib` | do not treat third-party/cache collection failures as product-test failures |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Prior-cache carrier | P4 suppression changes the prior token's later-layer K/V | within-condition C2/C3/C4 rescue | open |
| Residual-cache complementarity | current residual alone is incomplete while prior cache stays suppressed | J1/J3/J4 frozen comparison | open |
| Distributed recent-state support | single cache plus current residual may remain insufficient | J4/J5 under frozen thresholds | open |

## Next-Step Decision

- Current bottleneck: Stage 3C.7 is resolved; selecting or authorizing a new research action requires review of the completed evidence and a new explicit user instruction.
- Relevant memory item used: Stage 3C.7 found complete tested `t_pre` K+V rescue for both targets, but target-heterogeneous residual/downstream-cache complementarity.
- Chosen next action: none. Preserve the single review-only recommendation, **GO — Token-Type Carrier Atlas**, and stop.
- Why this action: the authorized research action and all acceptance checks are complete; the recommendation is not authorization to execute it.
- What not to repeat: no cross-image donor as the primary test, no cache-layer selection by delta magnitude, and no interpretation of RR as an information fraction.
- Stop condition: satisfied. No token-type, sink, residual-feature, Stage 4, multi-evidence, or failure experiment was started.

### Step Result

- Action taken: implemented and mechanically validated native-GQA `t_pre` K/V rescue, scored the frozen 24-base cohort, tested frozen residual/downstream-cache combinations, and ran the prospectively gated Target-A joint K/V decomposition.
- Result: 20/20 acceptance PASS and 28/28 independent artifact-validation PASS. Both targets classify as C-KV. Target A is O2 residual-cache complementarity (joint median RR 1.0006); Target B is O1 prior-cache carrier (joint median RR 0.4611, below the 0.50 substantial threshold). The Target-A joint effect is Value-dominant with an additional K+V interaction.
- Evidence saved: `outputs/stage3c7/`, especially `analysis/two_query_classification.json`, `analysis/exact_endpoint_analysis.json`, `audit/artifact_validation.json`, and `summaries/stage3c7_summary.md`.
- Failure or issue: the first one-base smoke inherited two Slurm tasks and was excluded; the corrected smoke and every subsequent run explicitly used one task per GPU. The unscoped pytest command also collected vendored/cache tests, while the correctly scoped repository suite passed 258 tests.
- Lesson learned: the prior token's native K+V cache is a sufficient tested carrier of the exact P4 deficit at both queries, with V carrying the dominant isolated effect; a late current residual and narrow downstream cache are complementary at Target A but insufficiently joint at Target B.
- Next implication: review **GO — Token-Type Carrier Atlas** as the sole proposed next action. It has not been started or authorized by this result alone.
