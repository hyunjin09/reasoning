# Phase 3C.9R: Same-path validity repair

## Current Objective

Execute `plan/stage3c9r_plan.md` on the exact frozen Stage 3C.9 cohort, repair
numerical comparability, report one recommendation, and stop.

## Active Constraints

- Original 48 primary / eight validation bases and 144 primary events immutable.
- W8/W16, quartet images, ROI, neighbors, readouts, source/sham and C2/C3 rules fixed.
- A6000 BF16 P2 cached streaming, 2048 maximum chunk size, fixed shared barriers.
- Only existing tmux 9 / Slurm 108548 / node07 four-GPU allocation; no requests.
- No cohort expansion, new spans, retrieval-trigger, sink or Stage 4 experiment.

## Current State

- Done: read approved plan, policies, prior phase evidence and relevant code.
- Done: 86 focused/new plus inherited tests pass. All 15 mechanical gates passed
  across 8 bases, 24 events, 96 condition files and 192 window families. Self
  patches and replays are exact; all 16 inherited-path comparisons are exact.
- Done: all 576 quartet-condition files / 288 W8/W16 event-window families
  completed before classification. There are 33 source-sensitive events and
  10 isolated C2 candidates at 0.05, with zero repeated bases.
- Done: threshold counts at 0.025 / 0.05 / 0.10 / 0.15 are 12 / 10 / 6 / 3
  checkpoints and 0 / 0 / 0 / 0 repeated bases. Necessity is gated off with
  three robust-at-0.15 events versus four required; routes are gated off 0/16.
- Done: all nine lifetime tasks / 18 O/C condition files completed. Final
  classes are 111 C0, 23 C1, 9 C2 and 1 C3. Lifetime labels are five qualified
  L-Short, two L-Persistent and three RIGHT-CENSORED; no repeated pair exists.
- Done: all 15 figures (PNG/PDF), the regenerable summary, 20/20 acceptance,
  and the independent audit of all 576 primary / 18 lifetime execution traces.
- In progress: none; Stage 3C.9R is complete and stopped for review.
- Blocked: none for the explicit plan. Local research-control skill is absent.
- Most recent useful observation: repair source losses exactly reproduce all
  66 matched legacy Phase-B O/C cells, while same-path sham effects change four
  of its gates. Full-event scoring changes the isolated count to 10, but the
  repeated-checkpoint count remains zero at every frozen effect floor.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| 24/33 source gates changed across phases | `outputs/stage3c9/analysis/posthoc_score_stability.json` | Requires same-path scores for every arm/sham | confirmed |
| No repeated checkpoints at all four floors | `outputs/stage3c9/analysis/posthoc_score_stability.json` | Repair tests stability of this negative | confirmed |
| Calibrated P2 path passes 17/17 | `outputs/a6000_calibration_v2/summaries/a6000_calibration_v2_acceptance.json` | Reuse runtime, not new numerical tuning | confirmed |
| Complete same-path repair | `outputs/stage3c9r/analysis/primary_freeze.json` | All frozen events scored before gates | confirmed |
| 12/10/6/3 checkpoints, zero repeated bases at every floor | `outputs/stage3c9r/analysis/threshold_sensitivity.json` | Supports R1 without relying on an exact isolated count | confirmed |
| 66/66 Phase-B source losses exactly match; four gates change through sham repair | `outputs/stage3c9r/analysis/stage3c9_phase_comparison.json` | Controls must share execution semantics too | confirmed |
| 15/15 mechanics and 20/20 acceptance; original 4,751 hashes unchanged | `outputs/stage3c9r/audit/independent_artifact_validation.json` | Establishes validity and preserves legacy evidence | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3C.9 A/B comparison | Source/sham gate depends on partition | supported numerical path mismatch | Share all boundaries and recipient scores | No old denominators in new classification |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Sparse repeated checkpoints | Main approved hypothesis | Frozen full-event repair | not supported under this assay |
| Distributed/renewed visual support | 26/37 source-sensitive event windows fail span rescue | Continuous source vs rescue profile | surviving explanation, not diagnosed |

## Next-Step Decision

- Current bottleneck: repeated sparse semantic checkpoints are absent in this
  frozen assay; the reasoning-state trigger for renewed retrieval remains open.
- Relevant memory item used: zero repeated bases at all four floors after
  scoring every event on one path, despite 33 source-sensitive events.
- Chosen next action: none. Sole recommendation is **GO — Retrieval Trigger**,
  for joint review only; no trigger experiment is authorized by this result.
- Why stop: the complete approved repair and its gates are finished.
- What not to repeat: no pair-yield expansion by default, mixed-path sham or
  source denominators, artificial lifetime probes, or right-censored decay claims.
- Stop condition: satisfied; reports, acceptance and one recommendation complete.

### Step Result

- Action taken: froze 4,751 original artifact hashes, implemented actual shared
  suppressed cache forks, passed complete validation, and launched primary.
- Result: technical PASS 20/20; final 9 C2 + 1 C3 checkpoints on ten bases,
  0/48 repeated bases. Base 38 remains C2: local G=0.186937, next G=-0.031645
  at distance 2342, final G=-0.093745 at distance 4715; the decay interval
  between probes is unresolved. Base 149 no longer qualifies.
- Evidence saved: `outputs/stage3c9r/audit/mechanical_validation.json` and raw
  validations under `outputs/stage3c9r/audit/raw/`.
- Failure or issue: no experiment failure. Isolated counts remain threshold
  sensitive; unclipped RR can be large when one source denominator is tiny.
  The inherited prefill resets CUDA peak counters, so resource reporting uses
  the maximum of every saved condition-level peak (20.28/23.37 GiB allocated/reserved).
- Lesson learned: exact CPU cache forks reproduce the inherited eager streaming
  path, with exact measured cache selectivity and recipient replay.
- Next implication: review the Retrieval Trigger recommendation. Do not start
  it, expand the cohort, or run necessity/routes from failed feasibility gates.
