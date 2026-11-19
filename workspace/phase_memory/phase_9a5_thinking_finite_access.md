# Phase9A.5: matched4B Thinking vs CoT finite access

## Current Objective
Completed the approved Stage9A.5 comparison. COMPLETE / STOP.

## Active Constraints
Original plan and frozen execution protocol remain unchanged. Same32 primary
images/64 queries; BF16, native Thinking template,512 cap, all36 decoder layers.
Immutable Stage9A.4 CoT reference. No new images, prompt tuning or cap repair.
No automatic next experiment.

## Current State
- Done: input freeze;64 FULL baselines; gold-free sealed reviews; all G1-G5;
  eight exact no-op and eight V1-V6 checks; ZERO/64/128; bounded null-sink;
  relative descriptions, paired statistics, five PNG/PDF figures and final audit.
- Outcome A under standard masking only. Thinking128 damage1.5625pp
  [0,4.6875]; CoT128 damage−1.5625pp. Neither arm preserves64.
- Control caveat: Thinking null-sink128 damage10.9375pp [3.125,21.875];
  preservation does not replicate. Robust shared sufficiency is not established.
- Optional256, normalized50/75 and reserve gates closed; none executed.
- All23 scheduler jobs succeeded;14 GPU jobs released.337 new generations,
  0.682222 allocated GPU-hours, max4 concurrent GPUs, node07. Live queue empty.
- No unfinished approved action. No follow-on launched.

## Evidence That Matters
| Evidence | Source under outputs/stage9a5/v1 | Relevance | Status |
|---|---|---|---|
| FULL58/64;64 reasoning;62 valid final;3 capped | stage9a5_thinking_full_baseline.json | All G1-G5 pass | confirmed |
| ZERO26.5625pp;64 18.75pp;128 1.5625pp | stage9a5_absolute_access_comparison.json | First preserving tested cutoff128 | confirmed |
| Paired Thinking−CoT128 3.125pp [0,7.8125] | same comparison | No supported prolonged claim; not equivalence | confirmed |
| Null-sink128 10.9375pp [3.125,21.875] | stage9a5_null_sink_control.json | Standard preservation not robust to this control | confirmed |
| All12 standard64 losses,1 standard128 loss,7 sink128 losses lack finals | audit/control_completion_diagnostic.json | Bounded completion endpoint; no emitted local-value error established by these losses | confirmed |
| Null-sink cross-arm128 7.8125pp [−1.5625,18.75] | same diagnostic | Secondary contrast also uncertain | confirmed |
| Eight independent audit groups;9 closeout checks | audit/final_validation.json; audit/closeout_verification.json | Provenance/statistical/resource closure | passed |

## Failed Attempts and Lessons
Scientific: null-sink did not replicate Thinking128 preservation. Cause unknown;
completion counts locate the losses but do not explain the changed completion.
Technical: no GPU/model failure. A local CPU presentation command stopped at its
Slurm guard before doing work; resubmitted correctly as CPU-only. Initial
presentation artifacts are archived with hashes; revised interpretation gives
prominence to the failed control. Raw generations and statistical results did
not change.11 focused tests pass.

## Open Candidates
None selected. Any follow-on requires user authorization.

## Next-Step Decision
- Bottleneck resolved: bounded stage result is known, including failed robustness.
- Evidence: shared standard cutoff128, uncertain paired difference and control failure.
- Chosen action: STOP. No256 search, reserve rescue, cap repair or normalized assay.
- Exactly one recommendation: retain dynamic visual re-access as the main Thinking
  mechanism and emphasize the distinction between native causal use and ablation
  necessity rather than a Thinking-specific VAB claim.
- Recommendation has not been executed.

### Step Result
Final report: outputs/stage9a5/v1/stage9a5_summary.md.
Current result does not invalidate Stage4A native causal source retargeting, which
used a distinct local MathVerse assay. No training/DeepStack causal attribution.
