# Stage 8B.1b — Block 1: Whole-Trajectory Success/Failure Analysis

## 0. Scope

This is the first analysis block for the completed 256-example MathVision bounded census.

It uses:
- Qwen3-VL-2B-Thinking
- 256 frozen MathVision examples
- canonical T=1.0 Stage 8B v2 protocol
- benchmark-faithful correct / wrong / unresolved scoring
- completion status stored separately
- frozen Stage 8A active-retrieval detector
- no detector refit
- no paired rollouts
- no causal intervention
- no local L+ / L− mechanistic analysis yet

This block asks only:

**How do final-correct and final-wrong reasoning trajectories differ globally?**

The next block will analyze retrieval-event-level L+ vs L− differences.

## 1. Why this block is necessary for the paper

Prior work such as vSTREAM reports that successful and failed multimodal reasoning trajectories differ in visual-attribution geometry.

We now have an independently calibrated retrieval detector that marks when the model actively re-engages visual information.

Before asking where retrieval itself fails, we should establish the broad outcome-level phenotype:

**Do correct and wrong reasoning trajectories differ in retrieval dynamics?**

This block provides:
1. a direct bridge to prior trajectory-level work;
2. a benchmark-scale success/failure phenotype;
3. context for the later retrieval-localized analysis;
4. a way to distinguish correctness effects from trivial confounds such as reasoning length or capping.

This block is descriptive but necessary. It should not be treated as the final mechanistic contribution.

## 2. Paper claim if positive

The strongest claim this block alone may support is:

> Correct and incorrect MathVision reasoning trajectories differ systematically in their visual-retrieval dynamics, even after controlling for completion status and reasoning length.

Possible specific forms include:
- wrong trajectories retrieve more frequently;
- wrong trajectories re-retrieve more often;
- wrong trajectories initiate retrieval later;
- wrong trajectories exhibit shorter or more irregular inter-retrieval intervals;
- wrong trajectories show larger retrieval-path length or tortuosity;
- correct and wrong trajectories differ mainly late in reasoning rather than early.

Do not claim from this block alone that any such difference is causal.

## 3. What a null does NOT rule out

A null correct-vs-wrong whole-trajectory difference does not imply that retrieval is unrelated to failure.

Possible explanations:
- final correctness is too coarse;
- many wrong answers contain locally correct visual retrieval followed by downstream reasoning errors;
- only specific L− local-read failures differ;
- source-routing differences are diluted in global trajectory summaries;
- same-item correct/wrong stochastic pairs are required;
- trajectory differences occur only after a local error event.

Therefore Block 2 must proceed regardless of whether Block 1 is positive or null.

## 4. Primary cohort

Use all 256 frozen Stage 8B.1a examples.

Each trajectory must have:
- benchmark outcome: correct / wrong / unresolved
- completion state: normal completed / capped / other abnormal stop
- total generated reasoning tokens
- frozen retrieval score time series
- thresholded active-retrieval events

Unresolved benchmark outcomes are excluded from the primary correct-vs-wrong test but retained for descriptive reporting.

## 5. Outcome labels

Primary outcome:

Y_i in {correct, wrong}

using the frozen Qwen-compatible MathVision scoring adapter.

Do not redefine:

cap = wrong.

Completion state is a separate variable.

## 6. Frozen retrieval event definition

For each reasoning token t, use the Stage 8A frozen retrieval score R_t.

Active retrieval:

R_t > tau_R

with frozen threshold:

tau_R = 0.5478025980771918

No threshold changes are allowed in Block 1.

## 7. Convert token-level hits into retrieval episodes

Token-level threshold crossings may form contiguous bursts.

Define a retrieval episode by merging active tokens separated by at most a small fixed gap.

Primary gap:
- g = 4 tokens

Secondary robustness:
- g in {0, 8}

Freeze the episode rule before looking at outcome differences.

For each episode record:
- start token
- end token
- duration
- peak retrieval score
- mean retrieval score
- area under retrieval score above threshold
- normalized trajectory position

This avoids counting one sustained retrieval burst as many independent events.

## 8. Primary whole-trajectory metrics

For each trajectory compute:

### M1 — Reasoning length
Generated reasoning tokens.

This is a confound/control variable, not a retrieval metric.

### M2 — Retrieval episode count
Number of retrieval episodes.

### M3 — Retrieval density
Retrieval episodes per 1,000 reasoning tokens.

### M4 — Active-token fraction
Fraction of reasoning tokens with R_t > tau_R.

This distinguishes frequent short episodes from long sustained episodes.

### M5 — First retrieval timing
Report:
- absolute token position
- normalized trajectory fraction

### M6 — Retrieval episode duration
Per trajectory:
- mean duration
- median duration
- max duration

Question:
> Do failed trajectories get stuck in longer retrieval episodes?

### M7 — Retrieval episode intensity
Per trajectory:
- mean peak score
- max peak score
- mean episode AUC above threshold

Question:
> Are wrong trajectories weaker, stronger, or simply more repetitive in retrieval activation?

### M8 — Inter-retrieval interval
For consecutive episodes, measure the gap between episode end and next episode start.

Summarize:
- median interval
- minimum interval
- coefficient of variation
- short-interval fraction

### M9 — Retrieval recurrence
Measure:
- number of episodes after the first retrieval
- number of returns after gaps >32, 64, 128 tokens

Primary simple metric:
- recurrence count = max(number of retrieval episodes - 1, 0)

### M10 — Retrieval burstiness
Use a preregistered burstiness statistic based on inter-retrieval intervals.

For example:
B = (sigma_delta - mu_delta) / (sigma_delta + mu_delta)

when at least 3 intervals exist.

Trajectories with insufficient intervals are missing for this metric, not zero.

### M11 — Late retrieval fraction
For normalized reasoning positions:
- p = 0.5
- p = 0.75

Secondary:
- p = 0.25
- p = 0.9

Compute the fraction of episodes beginning after each threshold.

## 9. Retrieval-feature trajectory geometry

Construct a passive feature vector z_t from the frozen Stage 8A detector inputs.

Use only features already available in the frozen detector / passive measurements.

Do not introduce correctness-conditioned features.

Possible components:
- visual QK competitiveness
- visual attention mass
- visual concentration
- retrieval score

Standardization must be frozen globally without using outcome labels.

### M12 — Path length
Sum Euclidean movement in feature space across evaluated reasoning positions.

Report both raw and transition-normalized versions.

### M13 — Net displacement
Distance between first and last evaluated feature vector.

### M14 — Tortuosity
Path length divided by net displacement plus a frozen epsilon.

Also report sensitivity to excluding extremely small-displacement cases.

### M15 — Local curvature / directional instability
Optional secondary metric:
- mean angular change between consecutive feature-space steps

This is exploratory.

## 10. Primary analysis hierarchy

Block 1 should not become an unstructured scan.

Use three primary metric families.

### Primary family A — Retrieval amount
- retrieval episode count
- retrieval density
- active-token fraction

### Primary family B — Retrieval timing / recurrence
- first retrieval timing
- inter-retrieval interval
- recurrence
- late retrieval fraction

### Primary family C — Trajectory geometry
- normalized path length
- tortuosity

Episode duration/intensity and burstiness are secondary.

## 11. Primary comparisons

### Comparison 1 — All scorable correct vs wrong
Main descriptive result.

### Comparison 2 — Normal-completion correct vs wrong
Repeat all primary metric families among normal-completed trajectories only.

Purpose:
- remove cap/completion-status confounding

### Comparison 3 — Length-adjusted correct vs wrong
For each metric, estimate the correctness effect after controlling for reasoning length.

Preferred:
- regression with log reasoning length
- matched or weighted analysis as robustness

Do not rely only on raw group means.

### Comparison 4 — Completion- and length-adjusted
Jointly control:
- reasoning length
- completion status

This is the strongest broad cross-sectional comparison.

## 12. Secondary completion analysis

Separately compare:
- capped
- normal completed

on retrieval dynamics.

This asks:
> Are extremely long/nonterminating trajectories characterized by distinct retrieval recurrence or wandering?

Do not reinterpret this as correct-vs-wrong evidence.

Because the capped cohort may be small, emphasize effect sizes and uncertainty.

## 13. Reasoning-phase analysis

Split each trajectory into normalized phases:
- early: 0–25%
- early-mid: 25–50%
- late-mid: 50–75%
- late: 75–100%

Compute per phase:
- retrieval episode density
- active-token fraction
- mean retrieval score
- retrieval-feature movement

Question:
> At what stage of reasoning do correct/wrong trajectories begin to differ globally?

This is descriptive. Do not call the first significant phase a causal onset.

## 14. Trajectory-shape visualization

Produce:

### Figure 1 — Retrieval density over normalized reasoning time
Correct vs wrong with item-level uncertainty.

### Figure 2 — Cumulative retrieval episodes
Cumulative expected retrieval episodes over normalized trajectory fraction.

### Figure 3 — Inter-retrieval interval / recurrence
Correct vs wrong distributions.

### Figure 4 — Path length and tortuosity
Outcome-level distributions.

### Figure 5 — Completion-controlled summary
Effect sizes before and after length/completion control.

## 15. Matching and confound controls

At minimum control for:
- generated reasoning length
- completion status
- MathVision problem category/subtype where available
- answer format
- question length

Optional if reliable:
- image complexity
- number of visual entities

Do not control for variables that are themselves plausible consequences of retrieval dynamics unless clearly labeled as sensitivity analyses.

For example, retrieval count should not be controlled when retrieval count is the outcome being tested.

## 16. Statistical unit

The independent unit is the MathVision item / trajectory.

Do not treat retrieval tokens or episodes as independent samples for correct-vs-wrong inference.

For episode-level descriptive plots, cluster uncertainty by item.

## 17. Statistical reporting

For every primary metric report:
- correct group median / mean
- wrong group median / mean
- standardized effect size
- item-level bootstrap 95% CI
- adjusted correctness effect
- robustness in normal-completion subset

Use 4,000 bootstrap resamples with fixed seed unless computationally prohibitive.

Do not base conclusions on p-values alone.

## 18. Multiplicity discipline

Primary metric families are frozen before opening results:
1. retrieval amount
2. retrieval timing/recurrence
3. trajectory geometry

Within-family metrics should be interpreted jointly.

Do not promote a single isolated significant metric if neighboring metrics disagree.

Secondary metrics:
- episode duration
- episode intensity
- burstiness
- phase-specific effects
- curvature

must remain secondary/exploratory unless later confirmed.

## 19. Primary hypotheses

### H1 — Outcome-level retrieval dynamics differ
At least one primary metric family shows a robust correct/wrong difference after length and completion controls.

### H2 — Wrong reasoning is not explained only by longer trajectories
Any key retrieval effect should remain directionally consistent after reasoning-length adjustment.

### H3 — Geometry difference is retrieval-related
If wrong trajectories show greater path length/tortuosity, the effect should co-occur with a meaningful difference in retrieval timing, recurrence, or episode structure rather than being only a trivial consequence of longer generation.

## 20. Interpretive outcome matrix

### Outcome A — More/repeated retrieval in wrong trajectories
Interpretation:
> failed reasoning may engage in repeated visual re-query or unstable evidence acquisition.

This motivates later analysis of whether local read failures precede recurrence.

### Outcome B — Less/delayed retrieval in wrong trajectories
Interpretation:
> some failures may arise because visual retrieval is not activated sufficiently or is activated too late.

Block 2 should test whether this remains true specifically for L− events.

### Outcome C — Similar retrieval amount, different tortuosity
Interpretation:
> failure may reflect instability in retrieval state/source rather than retrieval frequency.

Block 2 should inspect routing/source selectivity.

### Outcome D — No broad correct/wrong difference
Interpretation:
> final correctness is too coarse to localize visual retrieval failure.

This makes Block 2 more important, not less.

### Outcome E — Raw difference disappears after length/completion control
Interpretation:
> the apparent trajectory effect is largely a long-reasoning / cap phenotype rather than correctness-specific retrieval dynamics.

Do not use the raw effect as a paper claim.

## 21. Relation to vSTREAM

This block may replicate a high-level success/failure trajectory distinction.

Its paper role is:

vSTREAM-style global phenotype
→ our retrieval-specific decomposition in later blocks.

Do not claim novelty from path length/tortuosity alone.

The novelty must come from later linking these global effects to:
- retrieval activation
- local read success/failure
- routing
- re-retrieval
- recovery/wandering

## 22. Required outputs

Produce:
1. `stage8b_block1_outcome_census.json`
2. `stage8b_block1_retrieval_episode_table.parquet`
3. `stage8b_block1_trajectory_metrics.csv`
4. `stage8b_block1_correct_wrong_raw.json`
5. `stage8b_block1_correct_wrong_adjusted.json`
6. `stage8b_block1_completion_analysis.json`
7. `stage8b_block1_phase_analysis.json`
8. five figures:
   - retrieval density over reasoning time
   - cumulative retrieval episodes
   - recurrence/inter-retrieval intervals
   - path length/tortuosity
   - adjusted effect summary
9. `stage8b_block1_summary.md`
10. exactly one scientific recommendation for Block 2 emphasis

## 23. No-go actions during Block 1

Do not:
- refit the retrieval detector
- change tau_R
- run source-specific causal interventions
- run Value patching
- run reinjection
- launch paired rollouts
- extend beyond the 256 bounded cohort
- inspect L+/L− results before Block 1 analysis is frozen and completed

Block 1 is outcome-level trajectory analysis only.

## 24. Block 1 completion criterion

Block 1 is complete when we can answer:

> **How do final-correct and final-wrong MathVision reasoning trajectories differ in visual-retrieval dynamics, after controlling for trajectory length and completion status?**

The answer may be positive or null.

Either way, proceed to **Block 2 — Retrieval-Event / Local-Read Success-Failure Analysis**.

## 25. Decision passed to Block 2

After Block 1, freeze one high-level interpretation:
- more/repeated retrieval in wrong
- less/delayed retrieval in wrong
- similar amount but greater instability
- difference explained by length/completion
- no broad outcome-level retrieval difference

This interpretation determines emphasis, but not eligibility, for Block 2.

Block 2 must still test:

L+ vs L−

at active task-required retrieval events.
