# Stage14D-0 visual evidence difficulty v2 — completed retrospective analysis

**COMPLETE / STOP.** All 150 representative R families were source-reviewed: 986 source subfacts, of which 979 enter the acquisition analysis. No new evaluated-model calls, inference jobs, source repairs or score changes occurred. F’s 150 outcome-enriched families remain inventoried but are not difficulty-annotated, as prospectively allowed by P2.3. This is a finished R analysis, not a 300-family difficulty estimate.

The clearest observed pattern is more explicit evidence errors for facts requiring global structure/context. This supports prioritizing **visual rereading tied to an entity or coordinate while retaining the full-image context** for a future test. It does not show that such an intervention works, that cropping causes errors, or that every missing statement reflects failed acquisition.

## Inventory, annotation and preservation

| Inventory | R | F | Total |
| --- | --- | --- | --- |
| Families / images | 150 | 150 | 300 |
| Native r0 outputs, I + T | 300 | 300 | 600 |
| Historical source subfacts | 986 | 901 | 1887 |
| Historically source-adjudicable | 986 | 897 | 1883 |
| Historically withheld | 0 | 4 | 4 |
| New source-feature annotation | 986 | Not performed | 986 |
| Primary acquisition-eligible source facts | 979 | Not estimated | 979 |

The historical 437 parent atoms and four withheld facts in 276, 604 and 2869 are unchanged. Earlier 414 reviews overlap these native outputs and are not extra cases. E* is a source reference, not a third model. Exact identities, image/native hashes, source strata, raw/input/config/scoring paths, checkpoint manifests, per-case seeds and preprocessing receipts are in [inventory](inventory_and_provenance.json) and [600 protocol records](audit/native_protocol_provenance.json). The [coverage ledger](annotation_coverage_ledger.json) accounts for every one of the 1,887 original facts.

One main AI reviewer inspected original images using a source-only packet (question, image, target source meaning). The deterministic source-stratified pilot included 32 families / 183 facts. The [rubric and pilot](pilot_annotation_and_adjudication.md) were frozen before the feature/outcome join. All 150 R families / 986 labels were then sealed at 2026-10-12T03:33:43Z; source-freeze SHA256 `0a381009c0f676f6941cc26bd8651f990386a5becadebedf28b6a7e4a2592749`. The reviewer had prior exposure to this research. Source-only presentation limits fresh exposure; it does not establish independent blindness. No independent human or second-reviewer reliability estimate exists.

The 979 eligible facts comprise 522 direct visual facts and 457 visual computations. Seven mixed/source-uncertain facts are excluded only in this extension: `436_E1_s1/s2/s4`, `760_E1_s4/s5/s6`, and `463_E1_s6`. They require hidden cube/brick layers or a partly occluded universal leg-course assertion. Their original wording and historical validity are preserved. Whole-family exclusion is a sensitivity. No exclusively math-derived class was assigned. Source confidence is 978 medium / 8 low; one low-confidence fact remains eligible. A documented pre-join serialization repair added each primary operation to its all-operations union for 27 records; it changed no minimal sequence, depth or primary operation.

## Estimands and uncertainty

R targets the existing E*-eligible 1,000-family frame, not all 3,040 MATH-Vision problems. The original source strata are answer format × structured-parent presence. For a source level, calculate each contributing family’s C/W/U fractions among eligible facts at that level, then average with its original inverse inclusion probability. Consequently, weighted percentages generally differ from raw numerator / subfact denominator. The CSVs also give raw rates, unweighted family-equal rates and source-stratum profiles. Families can contribute to several levels.

**C** = existing last-state `STATED_CORRECT`; **W** = `STATED_INCORRECT` or `MISBOUND`; **U** = every other state, including unstated, vague, unstable or unsupported assumptions. U is not a proven acquisition failure. Conditional explicit error is weighted mean W divided by weighted mean (C+W), shown only with coverage. Source facts from unscorable finals remain in observable-evidence analyses; unscorable final answers remain separate in answer analyses.

All intervals are percentile 95% intervals from 4,000 shared family-cluster draws, seed 20261012, resampling within original source strata. The same sampled families support paired model differences and level contrasts. There is no subfact bootstrap, finite-population correction, independent annotation-error model, multiplicity correction or confirmatory p-value. F is not pooled. Cells with fewer than 10 families are sparse. Zero denominators are NA; finite draw counts are recorded. Correlated source dimensions are not independently causal. No multivariable model was fit, as fixed before joining outcomes.

| Original source stratum | Frame N | Sample n | Weight N/n |
| --- | --- | --- | --- |
| multiple_choice / structured=False | 81 | 12 | 6.75 |
| multiple_choice / structured=True | 269 | 41 | 6.560975609756097 |
| open_ended / structured=False | 122 | 18 | 6.777777777777778 |
| open_ended / structured=True | 528 | 79 | 6.6835443037974684 |

## Overall observable evidence

| Model | Raw C/W/U; denominator | Weighted C % | Weighted W % | Weighted U % | Conditional error % |
| --- | --- | --- | --- | --- | --- |
| I | 430/165/384 / 979 | 55.88 [49.57, 61.81] | 19.62 [15.57, 24.12] | 24.51 [19.31, 29.94] | 25.98 [20.74, 31.88] |
| T | 447/165/367 / 979 | 58.99 [52.84, 65.03] | 15.69 [12.03, 19.52] | 25.32 [19.83, 30.98] | 21.01 [16.20, 26.11] |

Both models have 165/979 raw explicitly wrong/misbound facts. The family-weighted T−I W difference is −3.92 percentage points [−8.38, +0.19]; there is **no established overall Thinking advantage in expressed evidence correctness**. Different family distributions explain the unequal weighted W estimates despite identical raw wrong counts. Native final-answer accuracy is a separate outcome.

## All seven source dimensions

Each row below gives complete C/W/U counts and eligible fact denominators. Weighted W intervals summarize explicit errors, not hidden acquisition. The full [per-axis CSV](difficulty_by_model_error.csv) also contains C/U and conditional-error intervals, unweighted family-equal estimates and source-stratum results. Multi-label visibility and operations overlap.

### A — Granularity and clarity

| Source label | Families | Facts / model | I raw C/W/U | T raw C/W/U | I weighted W %, 95% CI | T weighted W %, 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| na | 102 | 612 | 177/84/351 | 193/105/314 | 20.27 [14.74, 26.54] | 18.95 [13.43, 25.08] |
| readable_normal | 92 | 360 | 250/81/29 | 251/60/49 | 19.23 [13.25, 25.59] | 14.86 [9.77, 20.48] |
| unknown | 2 | 7 | 3/0/4 | 3/0/4 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |

| Source label | Families | Facts / model | I raw C/W/U | T raw C/W/U | I weighted W %, 95% CI | T weighted W %, 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| blur | 3 | 22 | 15/3/4 | 19/1/2 | 19.91 [0.00, 60.00] | 8.41 [0.00, 25.00] |
| dense_clutter | 2 | 19 | 4/3/12 | 4/3/12 | 9.29 [0.00, 18.75] | 9.29 [0.00, 18.75] |
| none | 139 | 848 | 376/148/324 | 391/153/304 | 19.48 [15.23, 23.99] | 17.22 [13.08, 21.63] |
| occlusion | 3 | 4 | 0/3/1 | 1/2/1 | 83.62 [50.00, 100.00] | 49.76 [0.00, 100.00] |
| overlap | 23 | 103 | 37/12/54 | 35/9/59 | 21.34 [7.21, 38.66] | 7.20 [0.84, 17.13] |

Across all 986 annotations, source size is normal 360, NA 619 and unknown 7. No small/fine or extremely-small eligible facts were labeled under the frozen pixel rubric; the within-feature tiny-text contrast is **not estimable**, not a demonstrated null effect. Exact glyph heights were calibrated only on the bounded pilot examples; most per-fact dimensions were not measured. These are original-raster judgments, not model patch resolution. Archived processed-image dimensions/hashes are retained, but no processed-view glyph measurement is claimed. Blur, clutter and occlusion cells are sparse. Overlap profiles differ across models and coexist with other features; they do not establish an overlap mechanism.

### B — Spatial scope

| Source label | Families | Facts / model | I raw C/W/U | T raw C/W/U | I weighted W %, 95% CI | T weighted W %, 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| global_configuration | 88 | 521 | 164/94/263 | 169/102/250 | 23.90 [17.65, 31.24] | 19.89 [14.00, 26.71] |
| one_local | 103 | 417 | 247/60/110 | 258/60/99 | 13.31 [8.59, 18.52] | 11.30 [7.41, 15.65] |
| three_plus_separated | 2 | 3 | 3/0/0 | 3/0/0 | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] |
| two_separated | 15 | 38 | 16/11/11 | 17/3/18 | 28.83 [11.99, 48.36] | 10.03 [0.00, 26.97] |

Global versus one-local explicit-error coverage differs by +10.59 pp [2.27, 19.15] for I and +8.58 [0.98, 16.33] for T. However, separated-ROI versus one-local contrasts are uncertain: I +12.13 [−3.85, 30.56], T −2.45 [−13.32, 13.02]. The three-plus-separated cell has only two families and three facts. A generic claim that more separated ROIs cause more errors is unsupported.

### C — Entity/relational complexity

| Source label | Families | Facts / model | I raw C/W/U | T raw C/W/U | I weighted W %, 95% CI | T weighted W %, 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| direct_attribute | 29 | 63 | 34/25/4 | 37/19/7 | 36.63 [22.71, 52.22] | 23.65 [9.92, 38.44] |
| multi_relation_or_correspondence | 84 | 313 | 117/61/135 | 130/45/138 | 24.51 [16.95, 32.91] | 18.20 [11.65, 25.46] |
| single_entity_binding | 77 | 393 | 212/58/123 | 213/79/101 | 13.38 [8.44, 18.83] | 15.80 [9.94, 22.41] |
| two_entity_relation | 41 | 210 | 67/21/122 | 67/22/121 | 17.17 [8.58, 27.21] | 16.94 [8.63, 26.47] |

There is no monotonic progression from direct attribute to multi-relation error rate. Direct attributes include source-constrained counts and string readings and are not necessarily easy. This source taxonomy does not justify ranking relational complexity as a universal difficulty scale.

### D — Minimal visual-operation depth

| Source label | Families | Facts / model | I raw C/W/U | T raw C/W/U | I weighted W %, 95% CI | T weighted W %, 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| one_visual_operation | 46 | 111 | 63/26/22 | 69/20/22 | 21.53 [12.02, 32.28] | 14.63 [6.22, 24.50] |
| three_plus_visual_operations | 62 | 458 | 137/77/244 | 143/77/238 | 25.23 [17.49, 33.35] | 19.89 [12.27, 28.16] |
| two_visual_operations | 113 | 410 | 230/62/118 | 235/68/107 | 14.98 [9.86, 20.64] | 16.00 [10.86, 21.48] |
| unknown | 0 | 0 | 0/0/0 | 0/0/0 | NA [NA, NA] | NA [NA, NA] |

Three-plus versus one operation gives I +3.70 pp [−9.84, 16.98] and T +5.27 [−7.55, 17.44]. Two-operation facts are not uniformly harder than one-operation facts. The evidence does not support a monotonic depth effect or prioritize sequential rereading solely from this proxy. These steps exclude mathematical deduction.

### E — Operation type

| Source label | Families | Facts / model | I raw C/W/U | T raw C/W/U | I weighted W %, 95% CI | T weighted W %, 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| compare | 16 | 31 | 16/5/10 | 18/7/6 | 16.34 [0.00, 34.22] | 13.77 [0.00, 29.50] |
| count | 35 | 101 | 54/31/16 | 64/16/21 | 39.38 [25.96, 53.60] | 21.77 [9.79, 34.58] |
| match_bind | 64 | 328 | 182/53/93 | 173/61/94 | 16.69 [10.50, 23.80] | 14.25 [8.22, 21.16] |
| pattern_structure | 21 | 95 | 26/13/56 | 26/18/51 | 17.16 [5.93, 29.73] | 23.08 [9.55, 38.77] |
| read | 10 | 38 | 24/14/0 | 26/11/1 | 23.75 [3.14, 49.64] | 13.87 [0.00, 35.18] |
| relation_decode | 44 | 117 | 50/18/49 | 50/31/36 | 16.22 [7.56, 26.23] | 20.27 [10.98, 30.84] |
| spatial_transform | 4 | 12 | 1/2/9 | 1/4/7 | 18.78 [0.00, 50.00] | 31.04 [0.00, 75.00] |
| trace_follow | 50 | 257 | 77/29/151 | 89/17/151 | 18.66 [10.17, 28.73] | 9.43 [4.11, 16.14] |

All primary operation-versus-read explicit-error contrast intervals include zero. Counting has a relatively high I point estimate, but count−read is +15.63 pp [−14.14, 40.27] for I and +7.90 [−17.14, 28.31] for T. The read comparator contains only 10 families / 38 facts. Spatial transforms have only four families. Trace-follow facts have 151/257 U in each model; lower explicit-error coverage cannot be read as successful latent tracing. [Operation/depth profiles](operation_type_and_depth.csv) retain the single primary label and overlapping all-operations views; no ranking by operation is sufficiently stable to establish a specialized remedy.

### F — Competitors and ambiguity

| Source label | Families | Facts / model | I raw C/W/U | T raw C/W/U | I weighted W %, 95% CI | T weighted W %, 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| any_competitor | 148 | 958 | 413/164/381 | 428/164/366 | 20.63 [16.32, 25.24] | 16.64 [12.83, 20.73] |
| none | 17 | 21 | 17/1/3 | 19/1/1 | 1.97 [0.00, 6.68] | 1.97 [0.00, 6.68] |

Any-competitor versus none differs by I +18.66 pp [11.97, 24.43] and T +14.67 [8.54, 20.10]. Repeated/similar competitor contrasts have similar direction. However, the broad competitor category covers 958/979 facts and 148/150 families; the no-competitor reference has only 21 facts in 17 families. The groups overlap in families and correlate with scope, context and operation. This is a source association, not a causal distractor effect or evidence that the model attended to a competitor.

Six predetermined hash-selected post-outcome examples form a bounded source-location diagnostic. In 2354, the wrong column’s first value appears in an adjacent column; in 2852, blue belongs to another digit. The other four are no exact signed/pattern match, unchanged-value misbinding, or unresolved topology. These are not a 2/6 prevalence estimate or causal WRONG_SOURCE_READ certification. Exact quotes, source boxes and uncertainty are separate from source-only predictors in [diagnostic records](audit/wrong_value_elsewhere_diagnostics.json) and [combined typed export](distractor_and_wrong_source_location.csv).

### G — Predicted need for global context

| Source label | Families | Facts / model | I raw C/W/U | T raw C/W/U | I weighted W %, 95% CI | T weighted W %, 95% CI |
| --- | --- | --- | --- | --- | --- | --- |
| global_required | 94 | 534 | 168/98/268 | 171/102/261 | 23.27 [17.41, 30.23] | 18.88 [13.37, 25.16] |
| local_plus_global | 66 | 304 | 155/51/98 | 155/56/93 | 14.73 [8.85, 21.62] | 14.93 [9.15, 21.26] |
| local_sufficient | 49 | 141 | 107/16/18 | 121/7/13 | 10.94 [4.26, 18.62] | 4.16 [1.06, 8.14] |
| uncertain | 0 | 0 | 0/0/0 | 0/0/0 | NA [NA, NA] | NA [NA, NA] |

Global-required versus local-sufficient gives I +12.33 pp [2.49, 21.99] and T +14.72 [7.94, 21.76]. Local-plus-global versus local-sufficient gives I +3.79 [−5.79, 12.85] and T +10.77 [3.76, 17.88]. This is the clearest shared source-level contrast alongside B. The label predicts what information a crop might lose; no actual crop was tested. [B × G tables](roi_scope_vs_context_need.csv) retain the distinction between spatial extent and interpreting a local detail using the scene.

## Paired I/T facts and shared failures

| Paired state | Count / 979 | Explicit-comparable subset | Weighted full % [95% CI] |
| --- | --- | --- | --- |
| both_correct | 373 | 373/527 | 48.54 [42.17, 54.73] |
| I_wrong_T_correct | 39 | 39/527 | 6.83 [3.90, 10.24] |
| I_correct_T_wrong | 17 | 17/527 | 2.78 [1.26, 4.51] |
| both_wrong_same | 56 | 56/527 | 6.03 [3.91, 8.42] |
| both_wrong_different | 33 | 33/527 | 3.07 [1.37, 5.16] |
| both_wrong_unknown | 9 | 9/527 | 0.89 [0.31, 1.57] |
| I_correct_T_unobservable | 40 | 0/527 | 4.56 [2.56, 6.89] |
| I_wrong_T_unobservable | 28 | 0/527 | 2.80 [1.34, 4.58] |
| I_unobservable_T_correct | 35 | 0/527 | 3.62 [1.93, 5.45] |
| I_unobservable_T_wrong | 50 | 0/527 | 2.92 [1.35, 4.81] |
| both_unobservable | 299 | 0/527 | 17.96 [13.49, 22.76] |

Only 527 facts are explicitly comparable in both models. Full-denominator results retain 452 facts where at least one output is unobservable/ambiguous. Of 98 both-wrong facts, existing annotations identify 56 same wrong, 33 different wrong and nine unresolved. This is shared expressed error, not shared hidden visual state. Detailed per-axis and explicit-comparable weighted intervals are in [paired results](paired_I_T_shared_failure.csv).

## Native answers, family burden and archived rescue

| Model | Native final | Families | Any eligible explicit error | All eligible facts explicitly correct |
| --- | --- | --- | --- | --- |
| I | CORRECT | 63 | 13 | 38 |
| I | WRONG | 73 | 52 | 9 |
| I | UNSCORABLE | 14 | 10 | 1 |
| T | CORRECT | 80 | 15 | 50 |
| T | WRONG | 69 | 49 | 6 |
| T | UNSCORABLE | 1 | 1 | 0 |

Families without an explicit error need not have complete correct evidence. The all-correct column uses the 979 eligible facts; seven extension-excluded source assertions do not silently become correct. Any-error and all-correct counts are separate outcomes, not an exhaustive binary partition.

| Model | E* correct / native-wrong with E* scoreable | Weighted rescue %, 95% CI |
| --- | --- | --- |
| I | 43/71 | 60.54 [49.37, 71.58] |
| T | 53/68 | 77.95 [67.98, 87.51] |

Rescue denominators exclude two I and one T E*-unscorable cases among native-wrong families. These are archived status metadata, not newly read oracle traces. E* changes representation/binding as well as access, so rescue is not a pure acquisition-failure measure. [Difficulty/answer/rescue CSV](difficulty_by_answer_and_rescue.csv) reports all-family burden conditional on having a feature opportunity, with native correct/wrong/unscorable strata; its overlapping groups must not be summed. [Archived R/F inventory](archived_answer_rescue_inventory.csv) preserves F status counts separately without assigning F difficulty or population weights.

## Sensitivities and temporal limits

| Variant | Families | Facts / model | I weighted W %, 95% CI | T weighted W %, 95% CI |
| --- | --- | --- | --- | --- |
| primary_last | 150 | 979 | 19.62 [15.57, 24.12] | 15.69 [12.03, 19.52] |
| direct_visual_only | 118 | 522 | 15.53 [11.00, 20.45] | 14.11 [10.11, 18.52] |
| exclude_uncertain_families | 147 | 968 | 18.79 [14.75, 23.27] | 15.60 [11.96, 19.50] |
| drop_1744_alias | 149 | 971 | 19.74 [15.68, 24.20] | 15.55 [11.95, 19.37] |
| first_state | 150 | 979 | 20.37 [16.38, 24.80] | 16.01 [12.36, 19.82] |
| ever_error | 150 | 979 | 23.40 [19.20, 28.07] | 22.17 [17.86, 26.64] |
| anchored_full_first | 150 | 979 | 20.23 [16.22, 24.66] | 15.34 [11.71, 19.11] |
| pre_answer_anchored_first | 150 | 979 | 19.01 [15.08, 23.46] | 10.35 [7.22, 13.78] |

The direct-visual-only analysis separates source reading from visual computation. The source-uncertain-family sensitivity drops 436, 760 and 463 entirely. The known duplicate-construction sensitivity drops 1744 while retaining 751; the original conservative family IDs remain immutable. First-state and ever-error analyses use existing annotations, not a new trace review. Ever-error gives priority to any historical wrong statement and therefore estimates a different quantity.

Anchored whole-output first-state support is available for 567/979 I facts and 569/979 T facts; the existing pre-answer rule retains only 536 I and 487 T. Pre-answer U rises to 31.37% I and 41.98% T (weighted), compared with 27.99% and 32.26% in the matched anchored-whole-output view. A lower pre-answer wrong rate cannot by itself prove correction or better acquisition. This sensitivity describes the first anchored statement, **not the last pre-answer state or first latent use**. Thinking’s think boundary and Instruct’s final exposition boundary are not equivalent measurements. All variants and per-axis profiles are preserved in [bootstrap/sensitivity metadata](cluster_bootstrap_and_sensitivities.json) and [CSV](sensitivity_axis_profiles.csv).

## Casebook, limitations and paper-safe conclusion

[Three explicit-error / matched-success pairs](casebook_source_images.md) contain original images, source rationale, immutable raw paths/hashes and exact Unicode-offset quotations. Matches share model, primary operation, depth and predicted context; they do not equalize all other attributes. Success is subfact-level, not whole-answer success. Some original linked quotations express a broader premise rather than literally stating the disputed value; those limitations are retained.

Critical limitations: retrospective, previously outcome-observed families; one AI reviewer with prior exposure and no independent reliability; selected verbalization and missing timing; correlated broad source labels; 150 R families in an E*-eligible frame; source-raster rather than model-view size labels; seven new local exclusions; sparse comparators; different I/T checkpoints, decoding and output lengths; unchanged original source/evidence imperfections. The confidence intervals include family sampling variation only. No absence/ambiguity is relabeled as acquisition failure.

Native protocols remain Qwen3-VL-4B-Instruct revision `ebb281ec70b05090aa6165b016eac8ec08e71b17` (temperature .7, top-p .8, top-k 20, repetition 1, presence 1.5, cap 32,768) and Qwen3-VL-4B-Thinking revision `1de27d8c51f12e819435303b9e84c4e25ba8401e` (temperature 1, top-p .95, top-k 20, repetition 1, presence 0, cap 81,920). The 300 per-family seeds, shared across model pair members, and original prompt/input/config/scorer provenance are retained individually; none was regenerated.

Paper-safe statement: in the representative source-eligible panel, global structure/context labels are associated with more explicitly incorrect or misbound native evidence, while operation depth and operation-specific contrasts do not establish a reliable ordering. These observations motivate a bounded future test of entity/coordinate-anchored rereading with global context. They do not validate a remedy or establish a pure perceptual cause. C1 remains a functional handoff observation; C2 remains a representation-changing evidence intervention; C3 visual acquisition remains a future test.

Exactly one priority is developed in [method design implications](method_design_implications.md). No Stage14D-1/14E experiment, tool use by evaluated models, training or continuation was launched. The old 1,674-continuation / 375-GPU-hour Stage14D main proposal remains HOLD and Stage14C-V closure is unchanged. **STOP.**
