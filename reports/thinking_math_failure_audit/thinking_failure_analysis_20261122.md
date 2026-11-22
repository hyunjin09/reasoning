# What Thinking fails on in MATH-Vision and MathVerse

**Completed 22 November 2026. Existing data only; zero model calls, zero GPUs, no changed scores.**

The strongest shared pattern is difficulty reconstructing usable visual structure: topology/connectivity, spatial configuration, counting, transformations and structured layouts. There is also observable replacement of unresolved images by verbal assumptions or familiar templates. These are not the only failure regimes: local scale reading, source/entity binding, downstream reasoning, completion and source/gold defects are distinct.

## Scope and what “all failures” means

All **13,568** Thinking generation records from the broad Stage14B main census and its fixed repeated-seed/equal-evidence followups were hash-checked and computationally screened. The primary native analysis is **7,768 r0 calls**: MATH-Vision 3,040 IDs and MathVerse 788 × six versions. It inventories every **2,303 scored native wrong output**, plus **26 unscorable MATH-Vision outputs**. Including repeated seeds, there are 3,417 native wrong and 35 native unscorable outputs; these are not additional independent questions.

**This is not a new exhaustive semantic/image audit of 2,303 cases.** Every failure is enumerated and its full text screened. Source-validated evidence diagnoses exist for 156 MATH-Vision wrong outputs in the prior 300-family audit, and detailed source difficulty for R=150. Others retain UNKNOWN mechanism rather than receiving invented cause labels. Question-type rates compare failures with successful cases; they are not simply shares of the failure pile.

Raw records: [all Thinking calls](../../outputs/thinking_math_failure_audit/v1/shared/README.md), [all main wrong/unscorable cases](../../outputs/thinking_math_failure_audit/v1/main_native_failure_cases.csv), [portable per-case results and lexical features](../../outputs/thinking_math_failure_audit/v1/shared/README.md).

## 1. Question types: MATH-Vision

Wrong/scored excludes unscorable answers; all are shown separately. Intervals are retrospective 95% conservative-family cluster bootstrap intervals, 4,000 draws, seed 20261122. Multiple native IDs can share a family; family-equal sensitivities and every category are in the CSV. No multiplicity-adjusted or causal claim.

| Native subject | Wrong / scored, rate [95% CI] | Unscorable | Family clusters |
|---|---|---:|---:|
| topology | 20/23 = 87.0% [75.0%, 100.0%] | 0 | 17 |
| descriptive geometry | 75/104 = 72.1% [54.7%, 80.3%] | 0 | 61 |
| counting | 41/66 = 62.1% [50.0%, 73.8%] | 1 | 64 |
| graph theory | 52/88 = 59.1% [47.8%, 69.8%] | 2 | 79 |
| combinatorial geometry | 177/305 = 58.0% [51.5%, 63.2%] | 3 | 205 |
| transformation geometry | 88/165 = 53.3% [40.8%, 62.9%] | 3 | 113 |
| solid geometry | 101/243 = 41.6% [34.6%, 49.2%] | 1 | 203 |
| statistics | 23/58 = 39.7% [26.7%, 52.5%] | 0 | 52 |
| combinatorics | 56/165 = 33.9% [26.7%, 41.2%] | 3 | 140 |
| analytic geometry | 25/83 = 30.1% [19.8%, 41.1%] | 1 | 68 |
| arithmetic | 42/140 = 30.0% [21.6%, 38.7%] | 0 | 122 |
| logic | 35/118 = 29.7% [20.2%, 39.6%] | 1 | 98 |
| metric geometry - area | 143/494 = 28.9% [25.1%, 33.4%] | 6 | 304 |
| algebra | 91/341 = 26.7% [21.0%, 32.4%] | 4 | 287 |
| metric geometry - angle | 37/173 = 21.4% [15.1%, 26.8%] | 0 | 122 |
| metric geometry - length | 91/448 = 20.3% [16.3%, 26.4%] | 1 | 308 |

Topology has only 23 questions and is a sparse extreme. Descriptive geometry, counting, graph theory, combinatorial geometry and transformations form a broader, less sparse difficulty pattern. Subject names are benchmark metadata, not verified global/local labels. Area problems contribute many failures because there are 500 of them; their per-question error rate is lower than several structural categories.

Native difficulty labels do not produce a monotonic error curve: difficulty 1 has 112/236 scored wrong (47.5%), versus 35–36% at levels 2–5. This is an unadjusted task-mixture observation. Open-ended and multiple-choice scored errors are similar (36.6% versus 36.2%); completion missingness differs. Full topic-cue, difficulty and answer-format tables are supplied in `question_type_failure_rates.csv`. Lexical topic cues are nonexclusive retrieval tags and do not certify source complexity.

## 2. Beyond global/local: structured information burden

The frozen source-only E*-eligible subset contains 1,000 families. These rates are final-answer errors, not visual-acquisition errors. They describe this selected subset, not the complete benchmark.

| Frozen source feature | Value | Wrong / scored, rate [95% CI] |
|---|---|---|
| requires_spatial_relation | False | 25/128 = 19.5% [13.3%, 26.6%] |
| requires_spatial_relation | True | 395/866 = 45.6% [42.4%, 48.9%] |
| requires_diagram_label_reading | False | 281/583 = 48.2% [44.2%, 52.2%] |
| requires_diagram_label_reading | True | 139/411 = 33.8% [29.1%, 38.6%] |
| requires_graph_table_reading | False | 153/457 = 33.5% [29.3%, 37.7%] |
| requires_graph_table_reading | True | 267/537 = 49.7% [45.7%, 54.0%] |
| structured_layout | False | 51/202 = 25.2% [19.4%, 31.5%] |
| structured_layout | True | 369/792 = 46.6% [43.3%, 50.1%] |
| structured_subfacts | 1-4 | 73/223 = 32.7% [26.9%, 39.0%] |
| structured_subfacts | 10-19 | 93/145 = 64.1% [56.0%, 72.0%] |
| structured_subfacts | 20+ | 57/86 = 66.3% [55.8%, 76.5%] |
| structured_subfacts | 5-9 | 146/338 = 43.2% [37.9%, 48.5%] |
| structured_subfacts | none | 51/202 = 25.2% [19.4%, 31.5%] |

**A useful additional pattern is the amount of structure to preserve.** Scored errors rise from 32.7% for structured objects with 1–4 recorded internal subfacts, to 43.2% for 5–9, 64.1% for 10–19 and 66.3% for 20+. Counting a whole grid/table/chain as one primary E* atom does not make it one simple datum. Primary atom count itself has no comparable monotonic curve.

Internal subfact sizes are heterogeneous annotation units, not standardized information bits. Size, subject, topology and source eligibility are correlated; the gradient is unadjusted and does not prove a memory-capacity mechanism. `structured_size_by_subject.csv` exposes the subject composition. Requiring label reading alone is not uniformly harder: its final-error rate is lower than the complementary group. Do not infer that tiny text is the dominant problem.

## 3. What the existing source audit actually establishes

R is a source-selected 150-family panel; F is an additional outcome-enriched 150-family panel. Source-valid required E* facts are compared with explicit native statements. Missing, vague and unstable statements are unobservable/ambiguous, never proven acquisition failures.

| Panel; Thinking native wrong | All required facts explicitly correct | At least one explicit required-source error | No explicit error, incomplete/ambiguous |
|---|---:|---:|---:|
| R: 69 wrong | 5 (7.2%) | 50 (72.5%) | 14 (20.3%) |
| F: 87 wrong | 15 (17.2%) | 50 (57.5%) | 22 (25.3%) |
| Combined, descriptive only: 156 wrong | 20 (12.8%) | 100 (64.1%) | 36 (23.1%) |

R weighted explicit-error share among wrong answers is 72.4% [61.7, 82.5]; all-correct 7.3% [1.6, 13.8]; incomplete/ambiguous 20.3% [11.3, 30.3]. Combined counts cannot be extrapolated as census prevalence. The source audit also contains explicit errors in 27 correct Thinking outputs, so a correct final is not a certificate of faithful source statements.

In the existing R difficulty extension, Thinking weighted explicit wrong/misbound evidence coverage is **18.88% for global-required** source facts, **14.93% for local-plus-global**, and **4.16% for local-sufficient**. Global-required minus local-sufficient is **+14.72 pp [7.94, 21.76]**. These are family-weighted subfact outcomes, not final-answer error rates. The extension uses 979 eligible facts after seven additional uncertainty exclusions; the table above retains the original source-valid audit definition. Do not merge their denominators.

Other supported distinctions include scale/quantity reading, entity-to-value binding, topology/connectivity and coordinate-frame use. Counting and operation-specific point estimates are exploratory; visual-operation depth did not have a reliable monotonic effect, and tiny-text difficulty was not adequately represented. The current source annotations do not support a census claim about tiny text, distractor attention or pure perception.

Pre-answer sensitivity is retained in `historical_thinking_evidence_crosstabs.csv`: it uses the first anchored statement before the existing answer boundary, not the last pre-answer evidence state. Many facts become unobservable in that view. Whole-output last-state evidence may include final exposition, so it does not certify acquisition timing.

## 4. Text reliance, imagined diagrams and the Math Blind hypothesis

The external [Math Blind / MATHEMETRIC project](https://vi-ocean.github.io/projects/MATHEMETRIC/) reports weaknesses in diagram perception and textual shortcuts. It motivates checking our traces; it is not evidence about these Qwen3-VL-4B generations. It is distinct from our BlindTest line-intersection representation experiment.

We searched exact full-output text for image-unavailability claims, description/text references, explicit assumption language and familiar-template language. Each match preserves Unicode character offsets and context. These are lexical candidates, not semantic verdicts: assumptions can be legitimate, a description can be correct, and a model can claim blindness despite having image tokens.

| Image-present native outputs | Image-unavailability phrase in wrong | Same phrase in correct |
|---|---:|---:|
| MATH-Vision | 379/1097 (34.5%) | 288/1917 (15.0%) |
| MathVerse | 88/969 (9.1%) | 119/2971 (4.0%) |

Every one of the **884** image-present main denial candidates has a saved image-present input receipt: **True**. Exact preprocessing sizes/hashes are preserved in the archived `image_denial_input_receipt_check.json`; the compact validation outcome and candidate excerpts are published. This rules out absent image transport in those saved receipts; it does not demonstrate visual-token use or exclude other runtime issues. Text Only is excluded from this image-present table because no-image statements are legitimate there.

MATH-Vision wrong traces also contain template phrases in 603/1,097 and assumption phrases in 957/1,097. Neither is an error label. Wrong traces are much longer, giving more opportunities for these phrases; length-stratified and early-first-quarter counts are retained. These associations do not isolate a causal effect of text reliance.

The broad search includes pronoun-only “I cannot see it” and occasional false positives such as a diagram “missing a segment.” A stricter named-image sensitivity retains only explicit I/we inability statements naming image/diagram/picture/figure: MATH-Vision **178/1,097 wrong (16.2%) versus 119/1,917 correct (6.2%)**; image-present MathVerse **33/969 wrong (3.4%) versus 55/2,971 correct (1.9%)**. These remain self-reported text, not certified image-neglect diagnoses. The broader screen and strict subset are both preserved.

**Three different phenomena must remain separate:** (1) a textual premise supplied by the user; (2) a model-generated textual surrogate for an unresolved picture; (3) valid algebra after correct visual facts. Cases 9 and 32 explicitly appeal to typical/standard diagrams despite image input. Case 2997 substitutes a rectangle for the source trapezoid. These support an observable template-substitution hypothesis; they do not prove that attention never reached the image. There is no controlled text–image conflict experiment here that could identify a universal preference for prompt text over pixels.

## 5. MathVerse: text availability matters, but source validity changes the comparison

| Version | Thinking wrong / 788 | Error rate |
|---|---:|---:|
| Text Dominant | 134 | 17.0% |
| Text Lite | 181 | 23.0% |
| Text Only | 237 | 30.1% |
| Vision Intensive | 210 | 26.6% |
| Vision Dominant | 219 | 27.8% |
| Vision Only | 225 | 28.6% |

Subject-wise Vision Only errors are Plane Geometry 131/510 (25.7%), Functions 49/159 (30.8%), and Solid Geometry 45/119 (37.8%). Within these categories, angle/length binding, graph/function interpretation and 3D geometry are useful review targets; broad subject metadata do not establish which operation caused each error.

| Paired comparison | Families | Left correct → right wrong | Left wrong → right correct | Right-minus-left error, pp [95% CI] |
|---|---:|---:|---:|---|
| Census; Text Dominant → Vision Only | 788 | 126 | 35 | +11.55 [+8.63, +14.47] |
| Census; Text Only → Vision Only | 788 | 104 | 116 | -1.52 [-5.08, +2.16] |
| Recorded checks pass; Text Dominant → Vision Only | 350 | 57 | 4 | +15.14 [+11.14, +19.43] |
| Recorded checks pass; Text Only → Vision Only | 350 | 58 | 8 | +14.29 [+10.29, +18.57] |

On all 788 families, Text Only is not better than Vision Only; in the 350-family recorded-checks-pass subset, Text Only is 330/350 correct versus Vision Only 280/350. Thus valid text-supplied geometry can be substantially easier than extracting it from images. That supports an evidence-interface bottleneck, not the claim that every image-present failure ignored the image. Vision Only also contains the question/choices in the raster, so it adds reading/formatting demands beyond diagram perception.

The recorded clean checks have limits: visual sufficiency review specifically targeted VD/VO, not a guarantee that every intermediate version preserves all constraints. For example, family 59 Vision Intensive drops parallelism/bisection without visual replacement. More seriously, family 7 has `text_only_sufficient=PASS` but its detailed review says “Text-only sufficiency FAILS.” Family 90 passes literal gold consistency despite a separately documented geometric key conflict; family 629 has the unrelated native gold “Bugs Bunny.” Thus the 350-family checkbox subset is not a new certification of full semantic validity. The source-note exclusion sensitivity retains the main direction without overwriting historical labels; only explicitly identified note issues are excluded, not an exhaustive new source audit.

Across six versions, 381 families are all-correct, 75 all-wrong and 332 mixed. All-wrong is not proof of a downstream mathematical bottleneck: family 90 is a counterexample with a documented gold conflict. Source-repeat clustering reduces the 788 family identifiers to 772 clusters; this changes uncertainty modestly and does not create new observations.

## 6. Evidence-supply followups distinguish opportunity from persistent failure

Within the 1,000-family source-eligible MATH-Vision cohort, Thinking has 420 native wrong answers. Of these, **306 become correct with E***, **110 remain wrong**, and **4 are unscorable with E***. The scored-followup rescue is **306/416 = 73.6%**; over all 420 native-wrong cases, observed rescue is 72.9%. There are also 30 native-correct → evidence-wrong regressions and one evidence-unscorable followup among native-correct cases.

This is strong evidence that usable source-derived textual evidence often helps this subset. It changes representation, binding and reasoning context, so it cannot identify a pure acquisition-failure fraction. Persistent E* failures require examining reasoning, source validity and output behavior; they are not automatically arithmetic errors. Repeated seeds preserve 88/120 and 89/119 scored-followup rescue, without adding independent families.

## 7. Completion and downstream behavior

| Image-present dataset | Native status | n | Median tokens | IQR | Cap hits |
|---|---|---:|---:|---|---:|
| MATH-Vision | CORRECT | 1917 | 9,731 | 4,898–16,470 | 0 |
| MATH-Vision | WRONG | 1097 | 15,103 | 8,993–24,941 | 0 |
| MATH-Vision | UNSCORABLE | 26 | 81,920 | 81,920–81,920 | 26 |
| MathVerse | CORRECT | 2971 | 1,897 | 864–4,447 | 0 |
| MathVerse | WRONG | 969 | 4,564 | 1,759–9,147 | 0 |

Long uncertain deliberation is common, but duration and “wait” counts are not causal diagnoses. An exact repeated-window screen finds no ≥10% verbatim 32-word-window duplication in wrong main outputs; this does not exclude semantic loops such as case 32, where the wording varies while the same alternatives recur.

Some wrong outputs have all minimal required source facts correct. Existing audit examples distinguish downstream construction/use mistakes (1118), formula/repair failure after source restatement (2045), and an extra full-grid coordinate error outside minimal E* (2239). These must not all be labelled missing visual evidence. Conversely, a correct minimal E* reference does not certify every other visual statement in the trace.

## 8. Source/gold and measurement failures

Known MathVerse review notes describe key conflicts in 90, 91, 144, 145, 622, 629, 720 and 728, plus unit conflicts in 681, 709 and 727. Original raw scores remain unchanged. A newly inspected MATH-Vision example, 2925, derives 45 from the stated right triangle and midpoints, but the archived gold is literal `45^2`, producing WRONG under the frozen scorer. This is flagged for human source/gold review, not silently repaired. No census-wide corrected accuracy is claimed.

A wrong benchmark label is therefore not automatically a model acquisition failure. Existing source annotations and E* can also be incomplete or imperfect. The analysis keeps these measurement issues visible rather than forcing all cases into perceptual or reasoning categories.

## 9. Failure taxonomy and conclusion

| Regime | What supports it here | What remains unknown |
|---|---|---|
| Global topology / structural reconstruction | High topology, graph, spatial/transformation errors; R global-context evidence contrast | Whether a particular crop/global intervention would repair it |
| Structured information burden | Strong internal-size gradient in the frozen source subset | Standardized information volume and subject-adjusted mechanism |
| Local source reading / entity binding | Exact source-audited wrong scales, endpoints, labels and source bindings | Census-wide frequency outside reviewed source families |
| Template or verbal-surrogate substitution | Exact traces replace unresolved diagrams with familiar configurations, sometimes denying image access despite transport | Causal attention/use, genuine text–image conflict preference |
| Incomplete/ambiguous evidence | Existing source audit retains unmentioned/uncertain facts | Latent acquisition; absence of mention is not failure |
| Downstream state/construction/computation | Wrong finals with correct minimal evidence and detailed trace case notes | Pure downstream prevalence; E* may omit other source facts |
| Uncertainty / completion | Long varying reconsideration, cap/unscorable records | Whether additional tokens or source rereading would improve it |
| Source/gold/representation defects | Existing source notes and the 2925 gold discrepancy candidate | Full human-validated corrected benchmark labels |

**Assessment:** the data support a compound problem—forming the right visual structure, preserving/binding its details, and preventing an unresolved picture from being replaced by a convenient verbal template. “The model just needs more reasoning” and “it always ignores images” are both too broad. The most informative next research question is whether a source-verified structural representation prevents these substitutions while preserving correct local facts. This analysis does not launch that experiment or resume the paused method-development work.

## Artifacts and limits

The [14-case source/output casebook](casebook_20261122.md) supplies exact references, quoted spans and limits, with complete raw traces linked. CSV/JSON artifacts preserve all main failures, repeated-seed followups, source flags, family clustering, ambiguity and lexical screens. Existing global/local numbers and source evidence judgments are single-AI retrospective annotations with prior exposure and no independent human reliability. New tables are exploratory; intervals include family resampling only. Full coverage means complete artifact inventory/screening, not 2,303 new manually certified causes.

[Analysis plan](../../plan/thinking_math_failure_retrospective_20261122.md) · [Data validation](../../outputs/thinking_math_failure_audit/v1/validation.json) · [Source audit supplement](../../outputs/stage14d0_answer_evidence_supplement_v1/supplementary_report.md) · [Prior source difficulty](../../outputs/stage14d0_visual_difficulty/v2/report.md) · [Math Blind official repository](https://github.com/Vi-Ocean/MATHEMETRIC_Benchmark).

**STOP. No follow-on experiment was run.**
