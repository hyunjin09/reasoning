# Stage 6A cohort summary

Status: **CONTROLLED_PASS_NATURAL_ATLAS_INSUFFICIENT**. Recommended next stage: **GO — Natural Failure Extension**.

All acquisition used BF16 Qwen3-VL-4B-Thinking, the fixed official sampling settings, natural EOS and the 40,960-token cap. Existing allocation 109385 on node03 in tmux session 9 supplied four A6000 GPUs; no additional allocation or dataset download was made.

Retained bases: C1=109, C2=31, C3=136, C4=1000. Native incompletes remain in raw evidence and condition accounting. C1 completion exclusions follow its frozen eligibility rule.

Physical acquisition saved 3182 terminal records and 13 replay generations, totaling 117.42 measured GPU device-hours. Reused mechanics records are counted once; this is not elapsed wall time.

C4 prevalence uses all 1,000 fixed images. The separate matched atlas does not estimate prevalence. The frozen conservative COCO80 presence protocol is CHAIR-compatible; it is not unmodified official CHAIR and does not exhaustively score attributes, counts, relations or non-COCO objects.

Semantic demand/refresh states and anchors are prospective annotations. They do not establish causal grounding, mirage, wandering or fixation. Controlled exact-source roles and natural category-set roles must remain separate. Correct numeric readouts can coexist with wrong geometric bindings or wrong final answers.

C1 validated evidence-availability conditions average 4.00 per base; 109 bases have both counterfactual and full-mask assets. Natural EOS averages 3.94 availability conditions per base, with 104 counterfactual/mask pairs both reaching EOS. Construction coverage and native-completion feasibility are distinct; capped variants remain in the release and limit completed-trajectory analyses.

C4 confirmed object errors occur in 1.0% of the fixed sample. Including unresolved cases gives a 1.0%–6.0% identification range under this annotation protocol. This is not a statistical confidence interval or a universal upper bound on hallucination. Whole-trace and final-caption labels are distinct; see c4_natural_failure/unbiased_prevalence.json.

For the fixed 63 present-object C3 families, reviewed yes responses are intact=61, strong=50, mask=41, sham=60, and sham_strong=61. These are paired response frequencies, not estimates of causal grounding or hallucination. See audit/c3_paired_native_response_review.json for review scope and sham-shape limits.

C3 unrelated-image responses are 133 no and 3 yes. Reviewed positive cases include one lamp-to-potted-plant error and two unresolved category boundaries. All 136 no-image finals answer no with explicit missing-image acknowledgement. They contain 47 unique prompts; identical prompts yield identical raw responses and are shared controls. These observations do not establish causal prior collapse. See audit/c3_unrelated_native_response_review.json and audit/c3_no_image_native_response_review.json.

## 1. Dataset availability and inventory

| Dataset | Usable | Local evidence |
| --- | --- | --- |
| MathVerse | True | testmini: 3940 rows, 788 bases, 2364 referenced images |
| MathVision | True | test: 3040 locally verified Arrow rows |
| MathVista | True | testmini: 1000 locally verified Arrow rows |
| DocVQA | True | validation: 5349 locally verified Arrow rows |
| POPE | True | test: 9000 locally verified Arrow rows |
| COCO2014 | True | val2014: 40504 images, 291875 instances |
| COCO2017 | True | val2017: 5000 images, 36781 instances |
| GQA | Located fallback; not validated for this stage | secondary fallback located; not needed with POPE/COCO usable |

## 2. Downloaded versus reused assets

| Action | Count | Evidence |
| --- | --- | --- |
| Downloads | 0 | Ordered local lookup found core datasets |
| Locally reused dataset entries | 8 | Includes located unused fallbacks; no external writes |
| Reused mechanics-v1 condition results | 59 | Hash-validated reuse; not additional physical generations |

## 3. Per-dataset retained base counts

| Cohort | Dataset | Bases |
| --- | --- | --- |
| C1 | MathVerse | 34 |
| C1 | MathVision | 31 |
| C1 | MathVista | 44 |
| C2 | DocVQA | 31 |
| C3 | POPE_COCO2014 | 136 |
| C4 | COCO2014 | 1000 |

## 4. C1 saved-pixel manipulation validity

| Condition | Status | Events |
| --- | --- | --- |
| counterfactual | PASS | 109 |
| counterfactual_render_sham | PASS | 109 |
| mask | PASS | 109 |
| mild | PASS | 109 |
| sham_mask | PASS | 109 |
| sham_mild | PASS | 109 |
| sham_strong | PASS | 109 |
| strong | PASS | 109 |

## 5. C1 counterfactual, mask and sham coverage

| Condition | Assets | Natural EOS |
| --- | --- | --- |
| counterfactual | 109 | 109 |
| counterfactual_render_sham | 109 | 109 |
| intact | 109 | 109 |
| mask | 109 | 104 |
| mild | 109 | 108 |
| no_image | 109 | 107 |
| sham_mask | 109 | 106 |
| sham_mild | 109 | 109 |
| sham_strong | 109 | 109 |
| strong | 109 | 108 |
| unrelated | 109 | 107 |

## 6. C2 alignment-by-retrieval cells

| Cell | Events | Natural EOS | Correct | Incorrect | Other/unknown |
| --- | --- | --- | --- | --- | --- |
| AR | 31 | 31 | 30 | 1 | 0 |
| A_only | 31 | 31 | 30 | 1 | 0 |
| R_only | 31 | 31 | 29 | 2 | 0 |
| Neither | 31 | 31 | 30 | 1 | 0 |

## 7. C2 within-base pairing

| Property | Families |
| --- | --- |
| All four prompts and the same source image | 31 |
| All four native traces reach EOS | 31 |

## 8. C3 present and absent object families

| Stratum | Source-valid bases | Intact EOS | Full-mask EOS |
| --- | --- | --- | --- |
| Present | 63 | 63 | 63 |
| Absent | 73 | 73 | Not applicable; no fabricated target ROI |

## 9. C3 source ROI quality

| Measure | Value |
| --- | --- |
| Reviewed polygon-mask present families | 63 |
| Reviewed natural-negative families | 73 |
| Geometry counts | {"C3:COCO_polygon": 1079, "C3:COCO_RLE": 8} |
| Opaque target pixels imply zero category information | False |

## 10. C4 unbiased whole-trace object-error yield

| Label | Images | Fraction of fixed sample |
| --- | --- | --- |
| UNRESOLVED | 50 | 0.05 |
| hallucination | 10 | 0.01 |
| no_detected_object_hallucination | 940 | 0.94 |

## 11. C4 separate matched atlas composition

| Role | Split | Bases |
| --- | --- | --- |
| hallucination_case | confirmation | 5 |
| hallucination_case | discovery | 5 |
| no_detected_control | confirmation | 5 |
| no_detected_control | discovery | 5 |

## 12. Native span counts

| Cohort | Section | Spans |
| --- | --- | --- |
| C1 | final | 48190 |
| C1 | reasoning | 140122 |
| C2 | final | 489 |
| C2 | reasoning | 1289 |
| C3 | final | 833 |
| C3 | reasoning | 13097 |
| C4 | final | 5067 |
| C4 | reasoning | 13516 |

## 13. Demand-transition annotations

| Cohort | Kind | Spans |
| --- | --- | --- |
| C1 | DEMAND_ONSET_OR_OFFSET | 566 |
| C1 | NO_CHANGE | 3982 |
| C1 | SOURCE_TO_SOURCE | 1385 |
| C1 | UNRESOLVED | 134189 |
| C2 | NO_CHANGE | 28 |
| C2 | SOURCE_TO_SOURCE | 14 |
| C2 | UNRESOLVED | 1247 |
| C3 | DEMAND_ONSET_OR_OFFSET | 5 |
| C3 | NO_CHANGE | 287 |
| C3 | UNRESOLVED | 12805 |
| C4 | COARSE_OBJECT_SET_CHANGE | 2157 |
| C4 | DEMAND_ONSET_OR_OFFSET | 5352 |
| C4 | NO_CHANGE | 4780 |
| C4 | UNRESOLVED | 1227 |

## 14. First-use, reuse and refresh annotations

| Cohort | Unit | Role | Count |
| --- | --- | --- | --- |
| C1 | individual source | FIRST_USE | 571 |
| C1 | individual source | REFRESH | 493 |
| C1 | individual source | REUSE | 1626 |
| C1 | individual source | UNRESOLVED | 12627 |
| C1 | span | FIRST_USE | 389 |
| C1 | span | MIXED | 158 |
| C1 | span | NONE | 784 |
| C1 | span | REFRESH | 234 |
| C1 | span | REUSE | 775 |
| C1 | span | UNRESOLVED | 137782 |
| C2 | individual source | FIRST_USE | 20 |
| C2 | individual source | REUSE | 15 |
| C2 | individual source | UNRESOLVED | 203 |
| C2 | span | FIRST_USE | 18 |
| C2 | span | MIXED | 1 |
| C2 | span | REUSE | 14 |
| C2 | span | UNRESOLVED | 1256 |
| C3 | individual source | FIRST_USE | 138 |
| C3 | individual source | REUSE | 21 |
| C3 | individual source | UNRESOLVED | 2266 |
| C3 | span | FIRST_USE | 138 |
| C3 | span | NONE | 6 |
| C3 | span | REUSE | 21 |
| C3 | span | UNRESOLVED | 12932 |
| C4 | individual source | FIRST_USE | 2345 |
| C4 | individual source | REFRESH | 2651 |
| C4 | individual source | REUSE | 6804 |
| C4 | individual source | UNRESOLVED | 608 |
| C4 | span | FIRST_USE | 1181 |
| C4 | span | MIXED | 1256 |
| C4 | span | NONE | 5873 |
| C4 | span | REFRESH | 999 |
| C4 | span | REUSE | 3977 |
| C4 | span | UNRESOLVED | 230 |

## 15. Local visual versus final correctness

| Cohort | Local visual label | Final label | Reasoning spans |
| --- | --- | --- | --- |
| C1 | CORRECT | CORRECT | 382 |
| C1 | CORRECT | INCORRECT | 95 |
| C1 | INCORRECT | CORRECT | 34 |
| C1 | INCORRECT | INCORRECT | 63 |
| C1 | UNRESOLVED | ABSTAINED | 62 |
| C1 | UNRESOLVED | CORRECT | 28021 |
| C1 | UNRESOLVED | INCOMPLETE | 15271 |
| C1 | UNRESOLVED | INCORRECT | 54841 |
| C1 | UNRESOLVED | UNRESOLVED | 41353 |
| C2 | CORRECT | CORRECT | 132 |
| C2 | CORRECT | INCORRECT | 1 |
| C2 | INCORRECT | CORRECT | 3 |
| C2 | INCORRECT | INCORRECT | 6 |
| C2 | UNRESOLVED | CORRECT | 1098 |
| C2 | UNRESOLVED | INCORRECT | 49 |
| C3 | CORRECT | CORRECT | 386 |
| C3 | INCORRECT | INCORRECT | 1 |
| C3 | UNRESOLVED | CORRECT | 2036 |
| C3 | UNRESOLVED | INCORRECT | 339 |
| C3 | UNRESOLVED | UNRESOLVED | 10335 |
| C4 | INCORRECT_OBJECT_PRESENCE | INCORRECT_OBJECT_PRESENCE | 39 |
| C4 | NOT_APPLICABLE_TO_NORMALIZED_OBJECT_PRESENCE | INCORRECT_OBJECT_PRESENCE | 54 |
| C4 | NOT_APPLICABLE_TO_NORMALIZED_OBJECT_PRESENCE | UNRESOLVED_FULL_CAPTION_TRUTH | 5819 |
| C4 | NO_OBJECT_ERROR_DETECTED | INCORRECT_OBJECT_PRESENCE | 60 |
| C4 | NO_OBJECT_ERROR_DETECTED | UNRESOLVED_FULL_CAPTION_TRUTH | 7394 |
| C4 | UNRESOLVED | UNRESOLVED_FULL_CAPTION_TRUTH | 150 |

## 16. Discovery and confirmation composition

| Cohort | Split | Bases |
| --- | --- | --- |
| C1 | confirmation | 62 |
| C1 | discovery | 47 |
| C2 | confirmation | 19 |
| C2 | discovery | 12 |
| C3 | confirmation | 90 |
| C3 | discovery | 46 |
| C4 | confirmation | 674 |
| C4 | discovery | 326 |

## 17. Template and stimulus duplication audit

| Measure | Value |
| --- | --- |
| status | PASS |
| reviewed_identity_records | 1891 |
| flagged_perceptual_pairs | 54 |
| primary_exact_pixel_groups | 17 |
| declared_template_families | 772 |
| errors | [] |

## 18. Future semantic causal-anchor candidates

| Cohort | Kind | Anchors |
| --- | --- | --- |
| C1 | demand_transition | 1385 |
| C1 | matched_no_transition_candidate | 3683 |
| C1 | refresh | 377 |
| C1 | stress_high_risk | 6060 |
| C1 | wrong_claim | 97 |
| C2 | demand_transition | 14 |
| C2 | matched_no_transition_candidate | 28 |
| C2 | wrong_claim | 9 |
| C3 | matched_no_transition_candidate | 287 |
| C3 | stress_high_risk | 2054 |
| C3 | wrong_claim | 1 |
| C4 | coarse_demand_transition | 2157 |
| C4 | coarse_refresh | 2026 |
| C4 | matched_no_transition_candidate | 1998 |
| C4 | wrong_claim | 45 |

## Interpretation and limits

C1 uses a subset of source-editable diagrams/tables, with all 114 intact candidates reviewed independently of correctness. The target of 120 was attempted using 155 source candidates. Source editability and long-response completion are selection limits; excluded raw evidence is preserved.

C2 pairs the same image and reviewed T/X fields. A source-only revalidation during acquisition supersedes the original crop-pass metadata; whole families with prompt/ROI mismatches are excluded while raw traces are retained. Retrieval-only prompts retain spatial/ordinal cues. Task wording and expected answer lengths are not perfectly matched; this is not a claim of zero semantic alignment.

C3 opaque polygon masks remove annotated target pixels but may preserve silhouettes, context and boundary fragments. Masked yes responses are not automatically hallucinations. Translated sham shapes can also be described as additional silhouettes: target pixels are preserved, but the sham is not guaranteed neutral for object counts or shape semantics. No-image and unrelated-image final labels distinguish original source-answer consistency from presented-image truth. An explicit no combined with missing-image acknowledgement is recorded separately from verified absence; repeated no-image question text is a shared control, not independent visual evidence.

C3 final scoring uses the fixed POPE/COCO category reference. The reviewed truck/van, cup/glass, chair/stool, mattress/bed, and unrelated-image car/pickup and bowl/bucket disagreements retain unresolved local visual truth: benchmark disagreement alone does not establish an objective perception failure. These source families and their raw responses remain included.

C1 complete numeric-source prefix review covers 1766 spans across all 109 frozen eligible bases, with 235 secondary numeric ROIs. The fixed scope is the first 20 native reasoning spans, or the whole reasoning if shorter. Remaining whole-trajectory geometry is not fully annotated. Most remaining long trajectories retain unknown local truth/demand. Reviewed local claims are a limited annotation subset, so their correctness counts are not a representative accuracy estimate. Temporal prior access means an earlier reviewed source-linked utterance; it does not prove causal use.

C1 numeric regions have mixed granularity: some are coordinate or expression components, others whole expressions or table values. Numeric table keys identify data cells rather than adding separate value regions. Repeated values retain separate source identities, while ambiguous attribution remains unresolved. Region and source-claim counts therefore are not counts of independent facts. The review does not cover every glyph, geometric property or causal dependency.

Atlas matching balances count/length/edge-complexity features and dominant object categories approximately. All eligible confirmed cases are retained, including weak matches; imbalance is recorded in matching_diagnostics.json.

All matched C4 controls have original-image and complete native-text reviews under the frozen positive COCO80 presence protocol. Known out-of-scope caption errors include calling a sink a bathtub and reading Crisco as Riso. These controls are not globally error-free; see c4_natural_failure/matched_control_review.json.

Source/template folds were assigned prospectively and inherited by every condition. Exact/flagged perceptual matches stay grouped, including C3/C4 shared COCO images. Generic task instructions are shared across folds; no unseen-task-template or exhaustive historical semantic-template claim is made.

Resource totals count actual generation and replay work once, including failed mechanics and capped responses. Referenced mechanics reuse adds no compute. Device-hours exclude CPU annotation, loading and dependency waits; they are not elapsed wall time or measured utilization.

Evidence: [acceptance](stage6a_acceptance.json), [screening](../cohort/screening_accounting.json), [release integrity](../audit/release_integrity.json), [resources](../audit/resource_summary.json), [atlas matching](../c4_natural_failure/matching_diagnostics.json), [annotation integrity](../audit/controlled_annotation_integrity.json).

Stage 6A stops here. No PCA, exact causal trajectory scoring, mirage confirmation, rescue or subsequent stage is executed.
