# Phase8B Block3B: post-read recovery, evidence persistence and wandering

## Current Objective

Completed the approved observational lifecycle analysis on frozen Stage8B data;
stopped at the plan's sparse-coverage / inconclusive-result boundary.

## Active Constraints

- Preserved all256 items/456 original reviews/148 T anchors and prior stages.
- Semantic judgments sealed before new outcome/passive joins; no post-outcome relabeling.
- Four frozen primary endpoints/windows/controls; conservative family clustering.
- No generation, detector refit, intervention, replay, download or cohort expansion.
- No next experiment authorized by completion of this action.

## Current State

- Done: 148 masked reviews, quote/provenance validation, passive extraction,
  4000-family-bootstrap contrasts/sensitivities, 11 artifacts and six figures.
- Annotation coverage:16 full remainders /132 source-reference-window reviews.
  Missingness is a performed-review limitation, not proof of inherent unannotatability.
- Three correction witnesses / two mutation witnesses; unknowns remain unknown.
- GPU-hours0; two CPU-only Slurm jobs119818/119819 completed on node02.
- All seven tests and final provenance/accounting checks passed; resources released.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| 120L+ retrieval-within128 contrast: adjusted−.02149,98.75% CI[−.24131,.19315] | outputs/stage8b_block3b/v1/stage8b_block3b_primary_effects.csv | No reliable final-outcome separation | confirmed |
| 16L+ mutation labels;104 unknown;871/4000 valid adjusted resamples | outputs/stage8b_block3b/v1/stage8b_block3b_mutation_Lplus.json | Cohort mutation incidence not established | confirmed |
| Only27L+ anchors have full symmetric256 exposure;2477/4000 valid adjusted resamples | outputs/stage8b_block3b/v1/stage8b_block3b_pre_post_wandering.json | Nominal120-anchor power does not transfer to symmetric geometry | confirmed |
| 3L− corrections,2 persistent errors,12 unknown | outputs/stage8b_block3b/v1/stage8b_block3b_recovery_Lminus.json | Existence cases only; final correctness is not recovery | confirmed |
| One identifiable refresh-compliance anchor; continuous sources and first-failure taxonomy unresolved | outputs/stage8b_block3b/v1/stage8b_block3b_summary.md | Refresh/stale and causal mechanism claims unsupported | confirmed |

## Failed Attempts and Lessons

The first analysis selected first family events before metric eligibility and
counted verbal refresh without detector support as stale. Mechanical repairs
corrected these two rules and added frozen tF extraction spans. Initial artifacts
are preserved under audit/initial_analysis_before_mechanical_repairs. Primary
results and semantic labels are unchanged. No search for positive effects.

D-080 remains relevant: early coarse claims and sparse source inventories limit
later source attribution. D-093 records the observed loss of symmetric exposure.
Seven exposed L− events show a raw negative delta, but adjustment is imprecise;
no failure-precursor/consequence explanation is supported.

## Open Candidates

Preservation failure, refresh failure, arithmetic/integration and failed correction
remain competing unresolved explanations. No candidate promoted to causal mechanism.

## Next-Step Decision

- Bottleneck: insufficient semantic coverage and symmetric pre-read exposure.
- Relevant evidence: original anchors yield27 rather than120 L+ geometry observations;
  adjusted primary intervals are either wide or unavailable.
- Selected action result: approved Block3B completed at plan§28 stop condition.
- Single paper recommendation: see audit/paper_recommendation.json; emphasize the
  local-evidence/final-answer dissociation with illustrative cases and inconclusive
  controlled post-read comparisons.
- Stop: no additional windows, taxonomy, replay, generation or next study.

### Step Result

outputs/stage8b_block3b/v1/stage8b_block3b_summary.md is the final report.
audit/final_validation.json records seven tests, all input/review checks and outputs.
CPU jobs exited0; no active allocation. Await a new user-selected research action.
