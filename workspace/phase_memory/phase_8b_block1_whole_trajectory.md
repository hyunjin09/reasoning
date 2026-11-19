# Phase 8B.1b: whole-trajectory success/failure

## Current Objective

Describe correct/wrong retrieval dynamics with length/completion/input controls
using the exact frozen Block0 cohort and objects; one recommendation for Block2.

## Active Constraints

- User-approved Block1 plan, two GPUs/node06 via project scheduler and Slurm.
- No detector changes, generation, causal work, local L labels or cohort growth.
- Unit=item;4000 bootstrap resamples; missing metrics remain missing.

## Current State

- Complete: all71 tasks,4000 resamples, five PNG/PDF figures and scientific report.
- Cohort:134 correct/105 wrong/17 unresolved; normal133 correct/105 wrong,
  capped1 correct/17 unresolved. Block0 hashes and event table preserved.
- Outcome D: no broad fully controlled retrieval difference established;
  all11 full primary pointwise and family intervals include zero.
- Contrary evidence retained: raw count/tortuosity differences; count and
  movement survive length/completion-only adjustment; secondary/gap0 effects.
- Resource completion: rank1 Slurm118035 preserved35 tasks; rank0 pending118034
  cancelled before execution, replacement118038/node06 completed36. Both
  released;40 allocated GPU-seconds. CPU assembly118039 complete; empty queue.
- No local L labels inspected and no Block2 action started.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Twelve frozen artifacts,256 unique families | `outputs/stage8b_block0/v1/audit/final_verification.json` | Reuse without drift | confirmed |
|238 normal,18 capped; cap independent of outcome | Block0 completion table; D-073/074 | Keep control axes separate | confirmed |
| Passive retrieval is not causal grounding | D-071 | Bound interpretation | confirmed |

## Failed Attempts and Lessons

No scientific runtime failure. Resource placement changed by explicit user steering:
118016 pending two-GPU/node06 request cancelled; then node03 pending118034
cancelled while completed node06 rank1 was preserved. Both final workers used
node06, with per-shard automatic release. No scientific definitions changed.

Confirmed limitations: normal/capped reasoning-length ranges have no overlap;
only one capped trajectory is scorable. Completion-adjusted cap coefficients
extrapolate, and normal-only outcome effects are not independent confirmation.
32 correct versus5 wrong trajectories have no detected episode, so timing
contrasts condition on different observed subsets. Causes remain unknown.

## Open Candidates

The approved Block1 action is complete. Exactly one handoff recommendation:
Block2 should emphasize L+ versus L− at active task-required retrieval events
across final-outcome groups, without changing frozen membership or eligibility.
No new analysis protocol or experiment is selected during this handoff.

## Next-Step Decision

- Current bottleneck: final correctness does not yield a robust fully controlled
  global phenotype; it cannot proxy for local-read correctness.
- Relevant evidence: D-076 immutable shared data; D-071 passive activation is
  not causal grounding; all11 adjusted primary family intervals include zero.
- Chosen action completed: bounded Block1 analysis and exactly one Block2 emphasis.
- Recommendation: local L+ versus L− at active task-required retrieval events,
  across both outcome groups with frozen event membership/eligibility retained.
- What not to repeat: no model generation, detector refit, outcome rescoring,
  episode changes, expansion or reinterpretation of cap as wrong.
- Stop condition reached: verified comparisons, figures, report, one interpretation
  and one recommendation. Await the separately specified Block2 execution.

### Step Result

- Action: two original logical shards completed on node06,4000 bootstrap samples;
  independent CPU assembly, hash checks and44 direct NumPy OLS point checks.
- Result: selected Outcome D, no broad outcome-level retrieval difference
  established under full controls. No equivalence or causal claim.
- Evidence: `outputs/stage8b_block1/v1/stage8b_block1_summary.md`, final freeze,
  `audit/analysis_acceptance_checks.json`, `audit/interpretation_freeze.json`,
  `audit/resource_completion_v3.json`.
- Contrary result: raw tortuosity attenuates after length adjustment, whereas
  count/movement need input controls to attenuate. Do not call all differences
  explained by length/completion or infer a specific causal explanation.
- Next implication: local-read correctness is the single recommended Block2
  emphasis. Block1 does not alter Block2 eligibility or authorize improvising
  its protocol. No local L inspection or Block2 execution occurred.
