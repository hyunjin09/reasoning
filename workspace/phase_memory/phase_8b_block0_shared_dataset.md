# Phase 8B.0: shared MathVision analysis dataset

## Current Objective

Construct the single frozen shared dataset from the completed 256 trajectories.

## Active Constraints

- Follow the approved Block 0 plan; four GPUs/node02 via scheduler and Slurm.
- No new generations, scientific comparisons, detector changes or interventions.
- Exact prior cohort; cap-independent scoring; outcome-independent membership.

## Current State

- Done: plan, policies, native evidence and frozen detector/adapter inspected.
- Done: all12 required artifacts frozen and independently verified; outcome extraction/provenance, completion, token/event/phase/geometry tables and456 review members complete.
- In progress: none. Slurm117930/node02/four GPUs completed in104s and released.
- Blocked: none; Block0 complete. Referenced separate Block 1 plan is not currently
  present among plan files; do not invent it.
- Most recent useful observation: all 256 native trajectories are verified,
  with 238 EOS completions and 18 caps; passive arrays already contain R/QK.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| 256 receipts / 1280 hashes verified | `outputs/stage8b1a/audit/native256_completion_verified_v1.json` | No regeneration needed | confirmed |
| Frozen threshold and detector | `outputs/stage8a/analysis/discovery_freeze_v1/freeze.json` | Load unchanged R | confirmed |
| Cap and scoring are independent | decision log D-073/074 | Preserve unresolved answers | confirmed |

## Failed Attempts and Lessons

None in this action. Historical gap=0 episode summaries remain preserved;
the newly approved primary rule is gap=4, implemented in a separate module.

## Open Candidates

None to select: the user approved the concrete construction plan.

## Next-Step Decision

- Current bottleneck: shared labels, episode definitions and reusable tables
  are not yet frozen for the complete cohort.
- Relevant memory item used: native completion proof and D-073/074.
- Chosen next action: execute Block 0 under its predeclared construction protocol.
- Why this action: prevent drift across subsequent analysis blocks.
- What not to repeat: no native reruns or outcome-selected event membership.
- Stop condition: monitor initial samples and report measured progress/ETA;
  batch stops once preprocessing finishes. Complete final integrity freeze when
  outputs and extraction provenance are ready. No invented Block 1 analysis.

### Step Result

- Action taken: completed the full authorized Block0 construction; monitored allfour workers.
- Result:256 trajectories,4,016,542 token rows,2358 primary episodes,456 review events; all12 artifacts pass hashing and acceptance checks.
- Evidence saved: `outputs/stage8b_block0/v1/stage8b_block0_freeze.json`, `audit/final_verification.json`, `audit/acceptance_checks.json`, `audit/resource_completion.json`.
- Failure or issue: preflight initially expected a nonexistent dtype config field; the actual frozen native runner enforces BF16. Corrected the check before submission, with no native change. No batch errors.
- Lesson learned: no new scientific inference.
- Next implication: later blocks must consume the frozen dataset unchanged. The separate Block1 plan referenced in the approved plan is absent; stop before inventing that analysis. Source-specific ROI feasibility awaits the later selected-event semantic review.
