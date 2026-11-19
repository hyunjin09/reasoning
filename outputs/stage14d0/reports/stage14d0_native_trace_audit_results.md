# Stage14D-0 native trace audit — completed

Completed 2026-10-11T22:31:25.975640+00:00. Scope: approved v 2 retrospective audit, original E* versus Instruct-native versus Thinking-native. **No new inference or GPU use.** Old Stage14D: 1,674 continuations/375 GPU-hours remain HOLD; Stage14C-V closure unchanged. The bounded D1 proposal is a document only.

The audit supports an evidence-state verification problem that includes source binding, global structure and downstream use. It does **not** establish that Thinking causally perceives better or that reacquisition alone explains E* rescue. In the source-selected panel, the paired Thinking–Instruct error contrast among mutually explicit facts is **-3.60 pp [-7.86, +0.40] (n=131)**. The interval includes zero. The recommended future action is a small verification-and-use feasibility study, not the old exhaustive continuation grid.

## Coverage, provenance and review limitations

All **300 frozen family IDs / 300 images / 600 native r0 outputs** were reviewed, paired for every family. There are **437 historical E* parents and 1,887 source-defined subfacts**, producing 3,774 model/subfact rows. **1,883 subfacts are source-adjudicable**; four subfacts in three families are withheld. Both native finals are scoreable for 246 families; raw outputs are available even when finals are unscorable. Native I: 119 correct/128 wrong/53 unscorable; T: 143 correct/156 wrong/1 unscorable. These pooled discovery-cohort counts are not prevalence estimates.

The audited 300 overlap 190 of the old 300 source reviews and 71 I+186 T=257 of the old 414 target-focused native reviews. All 600 native strings were assessed for this broader source-atom audit; the old 414 are not an additional cohort. The inventory joins all 1,000 eligible families, 2,000 native raws and 4,000 score records. Exact seed, input, model/processor/template, raw hash, scorer receipt and answer status remain in the [inventory](../inventory/source_and_raw_output_manifest.jsonl). No E*-conditioned reasoning was opened; those arms contribute archived score metadata only.

**One main AI reviewer, zero independent human reviewers.** Semantic decisions were manually authored by this agent; deterministic programs validated spans and summarized records. No inter-reviewer agreement statistic is estimable. Source/E*/scores/other-arm displays were masked during Pass A, but prior exposure, trace-style model identification and same-agent memory prevent independent blinding. Exact source before/after display ordering is best-effort; persistence exceptions 2961 T, 2006,2714,2390 and 1841 T's final 732 characters are disclosed in the limitations ledger. They are not relabelled as pristine blinded review. A later source check corrected the Pass A suspicion that 2547's 1/3/9 labels were invented: those labels are printed.

Full native text coverage totals 24,514,716 Unicode characters. For repetitive cap tails, lossless paragraph/RLE receipts preserve all unique text, original order and exact reconstruction; no semantic truncation or keyword-only review. There are 2,061 selected claim excerpts, **not an exhaustive count of all repeated utterances**. Closure verified 2,945 exact quoted spans. Character offsets are authoritative; generated-token offsets are unfilled rather than fabricated by retokenization. Many excerpts cover several facts. Precise first-use, first-revision or first-divergence timing is not available for every row.

## Model and text boundaries

The archived models are Qwen3-VL-4B-Instruct revision`ebb281ec70b05090aa6165b016eac8ec08e71b17` and Qwen3-VL-4B-Thinking revision`1de27d8c51f12e819435303b9e84c4e25ba8401e`. Historical vLLM/BF16 execution is unchanged. I sampling: temperature 0.7/top-p 0.8/top-k 20/repetition 1/presence 1.5/cap 32,768; T: temperature 1/top-p 0.95/top-k 20/repetition 1/presence 0/cap 81,920. Per-family recorded seeds and runtime inputs are preserved.

Instruct's generated explanation is observable text, not an authenticated internal reasoning trace. Thinking's pre-`</think>` text is also a generated trace, not proof of a hidden computation or image retrieval. Both complete strings, including final exposition, were read. The primary last-state audit covers the whole output; it is **not a uniformly isolated pre-answer-only contrast**. Exact Thinking tag boundaries and manually quoted I answer regions are retained; capped uncommitted responses have no invented final boundary. A pre-answer-anchor sensitivity excludes rows with only final-exposition anchors, but cannot turn sparse excerpts into exhaustive pre-answer coding.

Median generated lengths: I 5,043 tokens (IQR 1,901–11,155.75), T 13,322.5 (6,925.25–22,591.75). Different checkpoints, recipes, caps and opportunities to verbalize facts confound a causal “Thinking” comparison. [Length/mention-opportunity strata](../analysis/length_and_mention_opportunity.csv) report this without claiming equal compute. A missing statement is never called absent acquisition.

## Sampling and uncertainty

R contains 150 families selected by frozen source metadata strata from the 1,000 eligible frame; F contains 150 additional outcome-enriched families, including the 32 pilot cases where selected. Selection files preserve exact IDs, seed`stage14d0-v2-20261012`, hashes, quotas, inclusion probabilities and inverse-probability weights. R is retrospective and source-eligible-cohort conditional; it is not all MathVision or a new unobserved confirmation sample. F is discovery-only, never pooled as unweighted prevalence. The geometry-equivalent 751/1744 pair remains under its frozen IDs, with a merged-cluster sensitivity (299 clusters in the combined diagnostic).

Intervals use 4,000 paired family-cluster bootstrap draws, seed 20261012. R resamples within source strata and uses design weights; F gives families equal weight. Within-family fact rates prevent a large grid from acting as dozens of independent families. Intervals measure sampling variability, **not annotation error**. Tables/figures also show nested raw counts; nonexclusive evidence-type totals must not be added. No multiplicity-adjusted confirmatory claim is made.

## A. Evidence types and missingness

| Model, R | Required-fact explicit-correct coverage | Incorrect among explicitly correct/wrong facts | Families with ≥1 last explicit error |
|---|---|---|---|
| I | 55.85% [49.96, 61.70] (n=150 families) | 28.92% [23.60, 34.76] (n=140 families) | 49.91% [41.99, 57.87] (n=150 families) |
| T | 58.37% [52.12, 64.45] (n=150 families) | 26.85% [21.44, 32.44] (n=140 families) | 43.92% [36.04, 51.83] (n=150 families) |

R's family-weighted not-stated fractions are 4.51%I/3.59%T; vague/unmatchable 19.97%I/21.63%T. These are separate from incorrect claims. Raw R type counts include structured-layout errors 67/155 I and 47/137 T explicit subfacts; entity-binding 54/230 I and 52/223 T; topology 38/113 I and 38/108 T. Visual-convention 32/57 T versus 13/33 I shows that errors are not uniformly reduced in T. These are overlapping, nested descriptive type counts, not independently significant differences.

[Table A](../analysis/evidence_type_by_model.csv) carries parent/subfact/family and explicit-opportunity denominators, missingness and use states. [Figure1](../figures/figure1_evidence_taxonomy.png). Unsupported/nonrequired observations remain separate in the [verbatim supplemental ledger](../analysis/nonrequired_claims_and_downstream_observations.csv), rather than being silently added to the required E* denominator.

## B. Same-family, same-fact comparison

Of 1,887 paired subfacts: 739 both explicitly correct, 98 I-only wrong, 59 T-only wrong, 106 both wrong in the same way, 91 both wrong differently, 19 both wrong but identity unresolved, 203 one/both not stated, 568 ambiguous/unmatchable and 4 source-uncertain. The restricted both-explicit denominator is 1,112 subfacts, nested within 258 families across R/F. Wrong identity was compared manually from source bindings and actual statements; neither wrong final answers nor quote similarity supplied the labels.

The R paired error contrast is **-3.60 pp [-7.86, +0.40] (n=131)**; F **-2.45 pp [-7.09, +2.12] (n=127)**. R correct-required-coverage difference is **+2.51 pp [-1.91, +7.08] (n=150)**. F's coverage gain is **+6.98 pp [+2.70, +11.48] (n=150)**, but that panel is outcome-enriched. These are compatible with modest differences and substantial uncertainty, not a clean perception advantage.

Source-QC exclusion, both-scoreable, strict direct-visual, parent structure, first/last/used states, vague-as-error upper bound, pre-answer anchors and duplicate clusters are saved in [all bootstrap results](../analysis/cluster_bootstrap_and_sensitivity.json). R's strict-direct-visual paired error contrast is **-1.67 pp [-6.35, +3.37] (n=79)**. [Figure2](../figures/figure2_paired_error_matrix.png).

Examples: 2507 both ultimately fold Y above V instead of W despite I's intervening correct description; 2702 both insert checkerboard white cells into entirely dark rows; 2851 adopt different wrong grid sizes and coordinates. Shared errors and different errors both occur. None proves a common latent source or a causal visual-access mechanism.

## C. Observable propagation

The source-valid ledger contains 444 I/434 T subfacts with some explicitly wrong history. An incorrect premise is recorded as used for 389 I/391 T subfacts; these use counts also include assumptions whose source claim remains ambiguous and are **not a subset ratio of ever-wrong assertions**. Forty-one I and 86 T subfacts have a wrong-use plus later-revision record, not necessarily a successful repair. Sixty-four I/57 T ever-wrong facts lack observed wrong use; “claim only” means use unobserved, not proven absent.

First-use offsets are missing for 1,735 I/1,739 T of 1,883 valid subfacts. Many positive use judgments are qualitative, supported by arithmetic/geometry snippets but without a certified earliest time. The table's earliest wrong snippet is an **earliest annotated text event**, not a certified first internal error. Do not estimate an acquisition-to-integration latency from these sparse timestamps. [Timeline table](../analysis/first_error_and_propagation.csv), [event ledger](../annotations/event_chronology_and_self_correction.jsonl), [Figure3](../figures/figure3_observable_propagation.png).

## D. Self-revision with the right denominator

Among initially explicit wrong facts, I has 378 opportunities and T 262. Seventeen I and 9 T have a recorded wrong→source-consistent correction with ordered span anchors; 15 I/9 T are recorded as subsequently used, 2 I as not used. Three further T correction candidates lack a sufficient ordered span pair and remain unconfirmed in this count. These are conservative **annotation counts**, not independently validated rates of true visual retrieval. Partial correction and correct→wrong→correct instability are not forced into a successful-correction label.

Family-weighted R correction fractions are I 9.39% [3.74, 16.23] (n=80 families) and T 7.60% [1.52, 15.18] (n=66 families). The raw 17/378 versus 9/262 and these family-equal estimates answer different aggregation questions. No claim of higher Thinking visual self-correction is warranted. “Look again” language does not verify new image access. [Denominator table](../analysis/self_correction_initial_error_denominators.csv), [Figure4](../figures/figure4_self_correction.png).

## E. Correct stated reference facts do not ensure a correct solution

Fifteen I and 20 T wrong native finals have all required source-valid E* subfacts last stated correctly. This is a full-required-reference coverage flag, **not automatic proof of a purely downstream error**, because E* can be minimal and other native source claims can still be wrong.

- **1118 T: ** the tile's four triangular sectors are explicitly correct. The trace later swaps row/column adjacency, verifies inconsistent constructions and lists 5+5+2+2 light border triangles while claiming 12. This is concrete downstream construction/use evidence; repeated source restatement alone would not fix it.
- **2078 I: ** cube vertex identities are source-consistent, then the cut-solid construction invents edgeEGand miscomputes the volume. Correct initial binding does not prevent later geometric state corruption.
- **2045 T: ** source geometry is eventually restated correctly, but formulas and an absolute-value repair do not produce a valid derivation. A source correction is not equivalent to a corrected answer.
- **2239 T: ** minimal E* steps 1→2 right and 2→3 down are correct, but the cropped spiral's displayed row is misbound to full-grid row 2. This is a counterexample to diagnosing every all-required-correct failure as arithmetic-only.

These examples have exact native/source links in the [viewer](../viewer/index.html), Pass A/B files and [E table](../analysis/correct_evidence_wrong_reasoning.csv). They motivate premise-use verification and retention of incomplete/uncertain classifications. No absent statement or wrong final answer was reverse-engineered into an invented visual error.

## F. Association with archived textual E* outcomes

Among source-QC-passed R native-wrong families, a last explicit source error appears in 37/43 I rescued cases versus 15/28 I unrescued; T 41/53 rescued versus 8/15 unrescued. Regressions have 1/6 Iand 2/4 Tsuch errors. F differs: 20/25 versus 15/24 I; 27/40 versus 22/45 T. These raw conditional counts are descriptive and sparse, particularly regressions; weighted family intervals and all missing/scoreability strata are retained. [Table F](../analysis/error_by_Estar_rescue_outcome.csv), [Figure5](../figures/figure5_errors_and_Estar_outcome.png).

E* supply changes the input interface, representation, binding and reasoning context. Association with rescue cannot identify mediation or a percentage of pure acquisition failures. Original Stage14B/14C/14C-Vheadline scores and adjudications remain untouched.

## Source validity and conclusion boundary

Families 604,2869 and 276 have four withheld reference subfacts: an occlusion relation, incomplete dot occupancy, and a supplied numeral where the source has a question mark. Original references remain immutable. Some remaining references make structure explicit or expose task-relevant counts; source faithfulness is not a proof of answer-safety or unchanged task difficulty. No human source-validation reliability was established here.

The audit is complete as a **single-AI retrospective, human-checkable analysis**, with important semantic and timing uncertainty. It supports a future design that identifies the needed entity/structure, verifies it against full/local image context and checks incorporation into subsequent reasoning. It does not validate a decoder, certify fresh acquisition, or establish a causal advantage of one checkpoint/recipe.

**One recommendation: ** the [bounded Stage14D-1 verification-and-use feasibility study](stage14d1_bounded_feasibility_proposal.md), requiring a separate release. **STOP. No follow-on experiment launched.**
