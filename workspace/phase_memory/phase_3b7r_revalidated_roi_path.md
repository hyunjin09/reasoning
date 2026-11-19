# Phase 3B.7-R: Revalidated ROI-Specific Visual Path

## Current Objective

Stage 3B.7-R is complete. Preserve the frozen result and stop for review before any later experiment.

## Active Constraints

- Preserve all Stage 3B.7 artifacts and its failed `E_d-1/W4/Top_2` gate unchanged.
- Freeze selection, image controls, `E_d`, ROI maps, targets, thresholds, and analysis before reading Stage 3B.7-R causal outcomes.
- Fresh validation requires 12--16 unique numeric-label bases disjoint from the primary 37, old validation 8, and target-selection diagnostics.
- Target A is `E_d/W4/Top_4` heads `[11, 6, 15, 12]`; Target B-R is the previously Stage 3B.6-confirmed `E_d-1/W4/Top_4` heads `[16, 0, 3, 6]`.
- The locked Stage 1 official Thinking protocol and the two-A5000 allocation in tmux session 8 were used for all required generation/inference.
- Do not start any later vision-encoder, query/key subspace, MLP-feature, lifecycle, multi-evidence, or failure-analysis experiment.

## Current State

- Done: governing documents, Stage 3B.7 failure evidence, Stage 3B.6 frozen head lists, and the complete Stage 3B.7-R plan were reviewed.
- Done: primary 37 and historical validation 8 were enumerated and confirmed mutually protected.
- Done: outcome-blind screening covered 144 unseen Vision-Dominant bases across two frozen batches; 49 were prospectively mapped to a single-label counterfactual before generation.
- Done: 49 v1 four-image edit sets and one versioned 11-case ROI-undercoverage repair were automatically and manually audited before generation or causal scoring.
- Done: exactly 16 unique bases passed initial manual edit validation and were run under the locked protocol: `183,184,199,208,214,235,257,265,267,268,278,282,283,296,297,299`.
- Done: the generation outcome was `13 correct / 3 wrong / 0 truncated / 0 invalid`; every raw outcome is preserved.
- Done: all 13 completed-correct cases passed the score-blind strict-`E_d` audit and full ROI-overlay audit. The frozen fresh cohort is `183,184,199,208,214,257,268,278,282,283,296,297,299`.
- Done: a 60-base outcome-blind contingency screen produced 11 additional edit-valid candidates, but zero contingency generations were needed because the initial strict-valid yield exceeded the minimum.
- Done: both frozen targets passed fresh validation on 13 bases with all paired semantic-margin and mechanical conditions satisfied.
- Done: both targets passed the untouched 37-base primary ROI gate and were classified `ROI-Local`.
- Done: K/V mechanics passed on the fresh cohort; the 37-base primary decomposition classified both targets `Value-Dominant`, with K+V exactly reproducing the Phase-A target-ROI effect.
- Done: post-freeze attention triangulation uses 37 base-aggregated observations rather than pooling 74 target rows; it was not used for selection or causal inference.
- Done: all 20 acceptance criteria pass, and the sole recommendation is `GO — Value-content mechanism` for review. No later experiment was started.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Target A passed the original gate, whereas the old Target B failed its frozen sham-relative threshold | `outputs/stage3b7/validation/roi_path_validation.json` | Motivates fresh replication and target-specific gating without retroactive threshold changes | confirmed |
| Replacement Target B-R was independently frozen in Stage 3B.6 as `E_d-1/W4/Top_4=[16,0,3,6]` | `outputs/stage3b6/config/frozen_head_candidates.json` | Avoids a new post-failure head search | confirmed |
| The untouched primary cohort has 37 numeric bases and the old validation cohort has 8 bases | `outputs/stage3b7/config/primary_manifest.jsonl`; `outputs/stage3b7/config/validation_manifest.jsonl` | Defines disjointness and protects confirmatory inference | confirmed |
| Twelve additional completed-correct numeric cases failed edit validation because masks damage relevant geometry | `outputs/stage3a/cohort/expansion_manual_edit_exclusions.jsonl` | Rules out treating these as already valid fresh cases | confirmed |
| Twelve other disjoint edits passed manual validation but their locked-protocol generations were wrong | `outputs/stage3a/cohort_expansion/raw_outcome_manifest.jsonl`; `outputs/stage3a/cohort_expansion/round3/raw_outcome_manifest.jsonl` | They do not satisfy the completed-correct requirement | confirmed |
| Six batch-1, two batch-2-v1, and eight batch-2-v2 edits passed pre-generation manual validation | `outputs/stage3b7r/config/validation_edit_valid_freeze.json` | Supplies the maximum planned 16-case pool without outcome or attention selection | confirmed |
| Both frozen targets passed all fresh paired-margin and mechanical gates on 13 bases | `outputs/stage3b7r/validation/semantic_validation_statistics.json`; `outputs/stage3b7r/validation/mechanical_validation.json` | Prospectively authorizes both targets on the untouched primary cohort | confirmed |
| Both target ROIs are robust and localized on 37 bases | `outputs/stage3b7r/analysis/roi_path_statistics.json`; `outputs/stage3b7r/analysis/spatial_localization_analysis.json` | Exact edited-pixel visual positions account for most all-V restoration while controls remain small | confirmed |
| V-only, but not K-only, robustly restores evidence preference at both targets | `outputs/stage3b7r/analysis/kv_decomposition_statistics.json` | Supports the frozen Value-dominant classification under this intervention | confirmed |
| Base-aggregated pooled attention correlations are non-significant and differ by target | `outputs/stage3b7r/analysis/attention_secondary_analysis.json` | Reinforces that attention magnitude and causal transmitted content are distinct quantities | confirmed secondary |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Original Stage 3B.7 Target B validation | Median sham/semantic ratio `0.269893` exceeded frozen `<0.25` | supported semantic-strength/control failure, not a mechanical failure | Preserve the failure and use the prospectively defined paired-margin redesign | Do not relax the old threshold or reinterpret the failure |
| Reuse all existing disjoint completed-correct numeric examples | 12/12 have visible task-relevant geometry damage in their edits | supported by manual review records | Prospective collection is required | Do not promote previously rejected edits without a clean new design and audit |
| First-pass prospective edit construction | 41/49 v1 edits failed manual review, chiefly because the ROI missed part of a label or overlapped geometry | supported by review sheets and frozen manual manifests | Use exact component bounds only for isolated labels; preserve geometry-overlap failures | Do not perform another repair round after the one frozen v2 attempt |
| Initial aggregation metadata joins | Scorer results omitted duplicated evidence type, and Target B-R had no exact historical Stage 3B.6 V-source row | supported schema mismatch; not a scoring failure | Join evidence type from frozen annotations and require exact cell/unit/head-set historical matches; use same-run locked legacy equivalence where no historical V row exists | Do not fall back to a mismatched historical unit |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Prospectively screened unseen Vision-Dominant numeric-label problems | The initial 16-case pool yielded 13 strict-valid cases; the 11-case contingency remains unused | Preserve the contingency as unrun history | resolved |
| Target A replication | Previously passed, but new cohort prevents relying on the old result | Fresh validation and untouched primary scoring | resolved: ROI-Local, Value-Dominant |
| Target B-R replacement | Independently confirmed Top-4 source-path unit in Stage 3B.6 | Fresh validation and untouched primary scoring | resolved: ROI-Local, Value-Dominant |

## Next-Step Decision

- Current bottleneck: scientific review of the completed Stage 3B.7-R result; no additional research action is authorized.
- Relevant memory item used: the old Top-2 failure remains valid, while the prospectively revalidated Top-4 path succeeds without threshold relaxation or replacement cascading.
- Chosen next action: stop and return the complete result for review.
- Why this action: the plan's validation, primary ROI, conditional K/V, reporting, and acceptance boundaries are complete.
- What not to repeat: do not reinterpret KVR as an additive information fraction, treat attention as causal evidence, or start query/key-subspace, vision-encoder, Q/R, lifecycle, multi-evidence, or failure work without a separately reviewed plan.
- Stop condition: satisfied after final reports and acceptance verification.

### Step Result

- Action taken: completed fresh validation, primary spatial scoring, gated K/V mechanics and primary decomposition, post-freeze attention triangulation, figures, and final acceptance reporting.
- Result: Target A and Target B-R are both `ROI-Local` and `Value-Dominant`; all 20 technical criteria pass.
- Evidence saved: `outputs/stage3b7r/validation/`; `outputs/stage3b7r/analysis/`; `outputs/stage3b7r/scoring/`; `outputs/stage3b7r/summaries/`.
- Failure or issue: two aggregation-only schema joins required strict repairs; raw scorer outputs and frozen tests were unchanged. Secondary attention pooling was corrected from target-row N=74 to base-level N=37 before finalization.
- Lesson learned: exact evidence metadata and historical-unit matching must be explicit, and repeated target rows must be aggregated before any pooled inferential statistic.
- Next implication: Stage 3B.7-R stops with `GO — Value-content mechanism` as a recommendation for review, not authorization for a follow-on experiment.
