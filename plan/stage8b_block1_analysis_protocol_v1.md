# Block 1 execution and statistical protocol v1

2026-09-19. Implements the explicitly approved whole-trajectory plan. Freeze
this protocol and code before opening outcome-level contrasts. Reuse Block0 v1;
never rewrite its cohort, labels, features, episodes, scaling or geometry.

## Estimands and metric hierarchy

All effects are **wrong minus correct**. The independent unit is one unique
MathVision item/image family. Unresolved outcomes remain in census/completion
reporting and are excluded from correct/wrong contrasts. Missing timing and
interval metrics remain missing, with group denominators reported: first timing
requires an episode, intervals require two, burstiness requires four episodes.

Primary families, frozen together:

- A amount: episode count, episodes/1000 reasoning tokens, active-token fraction.
- B timing/recurrence: first absolute and normalized retrieval position, median
  inter-episode gap, episodes after first, late-episode fractions after .5/.75.
  Absolute/normalized first timing form one related construct; .5/.75 form one
  late-timing construct; recurrence and episode count are algebraically related.
- C geometry: standardized-feature transition-normalized path length and
  standardized-feature tortuosity. Use Block0 values unchanged.

Secondary: mean/median/max duration; mean/max peak R and mean AUC; mean/min gap,
gap CV, short-gap fraction (gap <=32), returns after gaps >32/64/128; burstiness
(population SD - mean)/(population SD + mean) for >=3 intervals; late fractions
after .25/.9; unnormalized standardized path length and net displacement; raw
feature-space geometry. Curvature is optional and omitted. Reasoning length is
described as a confound, never adjusted for itself as a retrieval outcome.

## Comparisons and inference

1. Raw all-scorable correct/wrong group mean/median, difference and Hedges g.
2. Raw normal-completion subset, all primary metrics (also cache secondary).
3. OLS wrong coefficient with intercept and log reasoning length.
4. OLS with log reasoning length and completion indicators.
5. Primary fully adjusted OLS adds pre-input subject/subtype, answer format,
   log(1 + question whitespace-word count), and MathVision difficulty level.
6. Repeat fully adjusted OLS in normal completions (constant columns redundant).

Use original metric units, plus coefficients divided by the original finite
correct/wrong pooled within-group SD for that analysis. Use an intercept,
centered/scaled continuous covariates (scaling pooled across all256, outcome-blind),
fixed categorical references and indicators. Subject labels occurring <8 times
in the full cohort are pooled into OTHER, determined without labels; preserve
the original subject in the analysis table. Difficulty is categorical. Use the
question exactly as stored, including any option text; MCQ/open is separate.
Completion and length controls are descriptive: they can themselves reflect
reasoning dynamics and do not identify causal correctness effects.

Bootstrap 4,000 times, fixed base seed1234, resampling items with replacement
within comparison groups and preserving group sizes. Shared resampling weights
across metrics within each comparison retain their dependence. Normal-completion
bootstrap uses that subset. Missing-metric values are omitted after resampling.
OLS uses float64 Frisch-Waugh-Lovell residualization; nuisance Gram pseudoinverse
relative cutoff1e-10; unidentified wrong coefficients are null. Report valid
replicate counts; with <95% valid replicates do not report a bootstrap interval.
Raw Hedges correction is 1-3/(4*(n_correct+n_wrong-2)-1). Bootstrap its mean,
median, mean difference and g; percentile95% intervals. OLS intervals are
percentile95%, with pooled SD held at the observed analysis sample value.

Within each primary family also give joint95% max-standardized-deviation
bootstrap intervals for raw mean differences and fully adjusted coefficients.
These guard against selecting one isolated metric; report all three families.
No p-value-only claim and no causal inference.

## Prespecified robustness

- Reuse Block0 gap0/gap8 episode tables. Derive the same episode metrics and
  repeat all primary comparisons; active-token and geometry quantities stay fixed.
- Tortuosity sensitivity excludes displacement at/below the pooled full-cohort
  fifth percentile of standardized net displacement, frozen without outcomes.
  This is a low-displacement-tail check; the actual minimum is nonzero, so it
  need not represent numerical degeneracy.
- Deterministic 1:1 matching without replacement: exact completion, pooled
  subject and answer format; maximum log-length difference .5. Within strata,
  minimum-cost maximum-cardinality assignment uses absolute log-length difference
  plus .25 times absolute log-question-length difference. Ties resolve in cohort
  order. Fix pairs for all metrics. Bootstrap4000 paired blocks; report balance,
  coverage and paired differences. Fewer than20 pairs is limited robustness.

## Completion, phases and figures

Completion analysis compares capped minus normal among all256, including
unresolved answers, with bootstrap uncertainty and separate length/covariate
adjustment; never interpret it as correctness evidence. Other abnormal stops
are described separately. Report overlap/imbalance and sparse cells.

Phase comparisons use the four frozen phases and per-item density, active
fraction, mean R, standardized mean movement. Bootstrap raw and fully adjusted
contrasts per phase; cache late-minus-early within-item differences. All phase
inference is secondary, with no claim about causal onset.

Five figures (PNG and PDF):20-bin per-item retrieval density means with item
bootstrap bands; cumulative episode means on21 grid points; per-item median
gap and recurrence distributions; standardized path length/tortuosity
distributions; raw/length/completion/full-adjusted standardized effect summary.
Density divides each item's bin count by exact zero-based token-bin exposure;
cumulative count uses onset <= grid position. Episode plots never treat events
as independent replicates.

## Interpretation and stop

Judge families jointly. A positive broad phenotype needs more than one
substantively related primary construct, not duplicate transforms/count versus
count-minus-one, with joint adjusted intervals, normal-subset direction, and
available gap/matching robustness considered. H3 additionally needs retrieval
amount/timing context; geometry alone is not causal/source evidence. Preserve
mixed or null outcomes; lost precision alone is not proof of mediation or
confound explanation. Select exactly one of the approved high-level outcomes
and exactly one Block2 emphasis, with limits and contrary evidence stated.

Stop after Block1 artifacts, five figures, interpretation and recommendation.
The next block is required irrespective of the result, but do not improvise
its separate protocol or inspect local L labels during this action.

## Implementation and resources

1. Validate Block0 hashes; freeze covariates, definitions and analysis code.
2. Test bootstrap/regression on known synthetic effects, missingness and rank
   deficiency; check matching and episode-derived additions.
3. Submit two independent Slurm workers on node06 (2GPU/8CPU/48G,2h limit).
   GPU bootstrap/regression uses existing cached tables; no model loading.
4. Verify real-device CPU/GPU parity and progress; assemble results/figures.
5. Verify inputs unchanged, required outputs complete, resource release and state.

Initial compute estimate: minutes rather than native-generation hours; measure
after startup. Release allocation immediately at batch exit. No downloads or
environment changes are expected. No tmux allocation or added GPUs.
