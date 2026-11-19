# Phase 3B.1: visual-sufficiency timing

## Current Objective

Determine when, strictly before E0, normal post-prefill reasoning makes the Stage 3A original-vs-counterfactual evidence distinction robust to removal of all future generated-query access to visual keys.

## Active Constraints

- Use all 49 frozen Stage 3A base problems; `base_problem_id` is the statistical unit.
- Use the exact Stage 3A strict pre-E0 token prefixes and evidence continuations.
- Freeze E0-relative and normalized-progress checkpoints before cohort scoring; deduplicate identical token indices without rescoring them.
- Use full-sequence eager scoring for no-cutoff and every timed-cutoff contrast so Stage 3A/3B.0 comparisons stay on one computation path.
- Attention is secondary and may be compared only after the causal timing results are frozen.
- Do not patch Q/R, localize layers/modules/heads/paths, or start Stage 3B.2.
- All GPU work must use the project scheduler and Slurm. Exclude node03 because its CUDA initialization failure remains unresolved.

## Current State

- Done: Stage 3B.0 established a small prefill residual (14.5% mean / 6.1% median raw retention) and Q carriage of that residual.
- Done: the frozen short/medium/long timing smoke passed 3/3 exact Stage 3A and Stage 3B.0 reproduction, edge-boundary auditing, no-op transparency, and finite-score checks on Slurm 106449 (node04 A5000).
- Done: all seven cohort shards (Slurm 106458--106464) completed on node04 A5000, covering 49/49 bases and 489/489 frozen checkpoints.
- Done: deterministic aggregation and reporting passed all 15 acceptance criteria. The frozen decision is **REDIRECT — Persistent direct-vision dependence**.
- In progress: none; Stage 3B.1 is complete and awaiting user review.
- Blocked: none.
- Most recent useful observation: the frozen cohort yields 489 unique problem-checkpoint pairs (6--12 per base) after deduplication.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| 49 strict pre-E0 bases with exact token hashes | `outputs/stage3a/cohort/primary_manifest.jsonl` | Fixes cohort, E0, prefixes, and evidence probes | confirmed |
| Stage 3A full-vision CE positive in 49/49 | `outputs/stage3a/scoring/fact_preference.jsonl` | Supplies the no-cutoff reference | confirmed |
| Generation-start cutoff retained 14.5% mean / 6.1% median | `outputs/stage3b0/cutoff/per_problem_cutoff_results.jsonl` | Supplies the 0% reference and motivates later checkpoints | confirmed |
| Full-sequence and cached BF16 paths differ deterministically | `outputs/stage3b0/smoke/cached_full_parity_diagnostic.json` | Requires one fixed full-sequence path throughout this stage | confirmed |
| Nine exact Stage 3A events overlap Stage 2C timing records | `outputs/stage3a/analysis/attention_moderator_analysis.json` | Bounds the post-freeze attention comparison | confirmed |
| No base reaches rho>=0.80; median E0-1 retention is 0.1114 | `outputs/stage3b1/analysis/prefill_vs_postprefill_gain.json` | Rejects the frozen GO and CONDITIONAL GO rules | confirmed |
| 15/15 technical criteria pass | `outputs/stage3b1/summaries/stage3b1_acceptance.json` | Establishes a valid negative timing result | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3A node03 execution | CUDA initialization failed despite visible devices | supported by saved diagnostic | Exclude node03 until administrator repair | Do not run Stage 3B.1 on node03 |
| Stage 3B.0 cached/full comparison | Up to 0.110 nats/token path-dependent difference | exact kernel cause unresolved; path difference directly observed | Keep all primary timing contrasts on full-sequence eager scoring | Do not mix cached and full scores within retention curves |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Early post-prefill sufficiency | Prefill retains a small residual that reasoning may rapidly amplify | Cut off at 25% and early E0-relative checkpoints | not supported cohort-wide |
| Gradual/late sufficiency | Continued visual access may accumulate evidence over many reasoning tokens | Compare continuous retention across all frozen checkpoints | limited: 6/49 reach rho>=0.50, none rho>=0.80 |
| Persistent direct-vision dependence | Even E0-1 cutoff may remove the fact distinction | Inspect late retention and no-threshold cases | supported under this intervention |
| Attention peak lags causal sufficiency | Stage 2C peaks were mostly mention-centered | Compare exact-overlap peak times only after causal results freeze | unresolved: only 2/9 overlaps reach rho>=0.50 |

## Next-Step Decision

- Current bottleneck: scientific review of the completed negative timing result before selecting any new action.
- Relevant memory item used: Stage 3B.0 shows that full/cached computation paths cannot be interchanged and that generation-start cutoff must reproduce exactly.
- Chosen next action: stop and return the complete Stage 3B.1 result for review; do not begin carrier localization or a redirected experiment.
- Why this action: the stage technically passes, but 0/49 reach rho>=0.80 and median maximum post-prefill gain is only 0.0313, so the frozen advancement rules require REDIRECT.
- What not to repeat: do not use attention to select checkpoints, do not submit to node03, and do not infer storage location from cutoff retention.
- Stop condition: after all 49 timing curves, threshold/monotonicity analyses, frozen secondary attention comparison, and one recommendation are written, stop before Stage 3B.2.

### Step Result

- Action taken: completed the smoke, all 49 timing curves, sham controls, threshold/monotonicity analyses, evidence strata, and frozen secondary Stage 2C comparison.
- Result: technical PASS (15/15); REDIRECT. First/stable rho>=0.80 is 0/49, E0-1 median retention is 0.1114, and median maximum post-prefill gain is 0.0313.
- Evidence saved: `outputs/stage3b1/scoring/`, `outputs/stage3b1/analysis/`, and `outputs/stage3b1/summaries/`.
- Failure or issue: the first secondary join dropped base 614 because two ROI events share E0. The corrected join reproduces Stage 3A's frozen density-based event selection and restores the expected 9-event overlap; primary causal results were unchanged.
- Lesson learned: post-prefill reasoning does not make the evidence distinction broadly independent of future direct visual access under the all-visual cutoff; small positive residuals must not be mistaken for high sufficiency.
- Next implication: immediate Stage 3B.2 carrier localization is not justified. Any redirected experiment requires separate review and authorization.
