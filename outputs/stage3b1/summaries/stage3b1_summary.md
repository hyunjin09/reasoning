# Stage 3B.1 summary — Visual-sufficiency timing

## Outcome

**Technical status: PASS (15/15 acceptance criteria).**

**Recommendation: REDIRECT — Persistent direct-vision dependence.**

Across 49 frozen base problems, 0/49 (0.0%) reached a first raw retention crossing at rho>=0.80, and 0/49 (0.0%) remained above that threshold at every later sampled checkpoint. Median generation-start retention was 0.0607; median maximum strict-pre-E0 retention was 0.1253; the median maximum post-prefill gain was 0.0313.

These quantities measure preservation of the Stage 3A evidence-specific counterfactual effect after future visual access is removed. Retention is not a unique information fraction and does not identify a carrier.

## Cohort and intervention

- Primary unit: 49 frozen unique Stage 3A `base_problem_id` values (45 local numeric-label edits; 4 structural edits).
- Schedule: 489 unique problem-checkpoint pairs after exact-index deduplication (6–12 per base).
- Coordinates: E0-relative offsets -128, -64, -32, -16, -8, -4, -1 where available, plus normalized progress 0%, 25%, 50%, 75%, and 90%.
- Cutoff semantics: cutoff `c` permits normal vision for generated queries `y_0...y_(c-1)` and blocks all generated-query→all-visual-key edges from `y_c` onward in all 36 language layers. Prefill is unchanged.
- Scoring: identical Stage 3A strict pre-E0 prefix, evidence candidates, original/counterfactual/sham images, and full-sequence eager path at every checkpoint.
- Selection and checkpoint placement used no attention measurements.

## Validation

The three-base short/medium/long smoke gate was **PASS**. No-cutoff scores exactly reproduced Stage 3A for 49/49 bases; generation-start cutoff scores exactly reproduced Stage 3B.0 for 49/49. All 489 cutoff audits verified the frozen visual-key list, first modified query, all-layer coverage, and zero prefill or pre-cutoff modification.

Seven A5000 cohort shards completed. Maximum reported allocated GPU memory was 9.09 GiB. Median synchronized candidate-forward time per base was 14.67 seconds. Eight required figures were produced (8 observed).

## Primary timing results

- First rho>=0.80 crossing: 0/49 (0.0%).
- Stable rho>=0.80 crossing: 0/49 (0.0%).
- First/stable rho>=0.50 crossing: 6/49 and 6/49.
- E0-1 retention: mean 0.1794, median 0.1114 (N=49).
- Maximum post-prefill gain: mean 0.0450, median 0.0313.
- Material non-monotonic curves (>0.20 downward step): 0/49 (0.0%).
- Frozen descriptive timing categories: S3_gradual_accumulation=6, S5_persistent_direct_vision_dependence=43.

The raw unsmoothed curves are primary. Discrete threshold crossings are summaries of the sampled grid, not exact continuous acquisition times.

## Controls and strata

Sham-controlled CE was computed at every checkpoint. At E0-1 it remained positive in 45/49 bases, while the mean original-vs-sham shift was 0.0027. Numeric-label examples (N=45) had median maximum gain 0.0175; structural examples (N=4) had 0.0950. Structural N=4 is too small for a strong comparison.

## Secondary Stage 2C attention comparison

Exact event matching yielded 9 overlapping problems; 40 cohort problems had no unique exact Stage 2C event match. This analysis was performed only after the primary cohort and timing definitions were frozen.

Only 2/9 overlap problems reached a rho>=0.50 crossing, and 0/9 reached rho>=0.80. Thus the exact-overlap subset is insufficient for a reliable high-sufficiency-versus-attention timing comparison.

ROI attention remains descriptive. Agreement or disagreement between an ROI-attention peak and a causal sufficiency crossing does not establish where evidence is stored, when it was first acquired, or which mechanism carried it.

## Limitations

- Retention ratios can be heterogeneous and non-monotonic because the intervention can interact nonlinearly with distributed/redundant computation.
- The checkpoint grid bounds rather than exactly localizes transitions; threshold times are discrete.
- Teacher-forced evidence-specific preference is the primary behavioral readout. Optional short rollouts were omitted prospectively because the Stage 3B.0 128-token rollouts rarely reached the target fact.
- The exact Stage 2C overlap is small, and the structural stratum contains only four bases.
- This stage does not locate evidence in Q, R, a layer, module, head, or path.

## Scientific boundary

Stage 3B.1 tests when future direct visual access becomes dispensable for preserving an evidence-specific counterfactual effect. It does not claim that the retained effect is stored in any particular state, that attention marks acquisition, or that a LOOK/THINK mode exists. Stage 3B.2 and all carrier-localization experiments remain unstarted.

## Key artifacts

- `config/checkpoint_schedule.jsonl` and `smoke/cutoff_timing_validation.json`
- `scoring/per_problem_timing_results.jsonl` and `scoring/per_checkpoint_statistics.json`
- `analysis/retention_curves.json`, `analysis/sufficiency_times.jsonl`, and `analysis/monotonicity_audit.jsonl`
- `analysis/prefill_vs_postprefill_gain.json` and `analysis/attention_timing_comparison.json`
- `summaries/stage3b1_acceptance.json` and `summaries/stage3b2_recommendation.md`
