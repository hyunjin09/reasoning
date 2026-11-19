# Stage14C — Cross-task evidence-supply bottlenecks

The completed study shows a large retained Thinking advantage under equal textual evidence in the math anchor, with smaller and uncertain gaps on the selected MMStar and BlindTest strata. Oracle evidence rescues many native failures in every panel, but it is not uniformly beneficial: the BlindTest line-intersection representation causes substantially more Instruct regressions than rescues. The bounded evidence probe has material elicitation and granularity limitations, so it cannot convert these behavioral results into a pure perception/reasoning decomposition.

All 4,588 unique new main calls and 600 frozen D1 calls are complete, with zero technical missingness. Main scoring, the primary-only summary, 89 source sensitivities, two-pass review of all D1 outputs, five figures and their provenance are preserved. The 42 scientific G2 calls are included in main, not additional calls; six synthetic replay calls are separately accounted. No new primary math output was generated or regraded.

## Scope, identities and source coverage

| Panel | Native items / conservative families | Frozen E* families | Coverage and limitation |
|---|---:|---:|---|
| MATH-Vision anchor | 3,040 / 2,104 | 1,000 | Sealed Stage14B reuse; not an independent new replication |
| MMStar | 1,000 / 1,000 | 280 | 28% eligible; mixed VQA including math; one late source-QC defect disclosed below |
| BlindTest | 714 / 714 | 300 | 42.02% eligible; all E* cases are line intersections, while native covers nine task labels |

The original plan's G0 hold was released by the user's “proceed”; the timestamped approval receipt supersedes the preserved draft status. Source cohorts and E* were frozen before generation, with two-pass same-agent review of all 580 accepted new E* records and a fixed 172-family reread. Source revisions and rejected candidates remain visible. MMStar's 250-family reserve was unused. Direct-answer tasks that could not support an answer-safe E* remain native-only. All 300 line-geometry derivations agree with native golds; this is not independent semantic certification of every benchmark gold.

The pinned Qwen3-VL-4B Instruct/Thinking checkpoints and validated Stage14B recipes are unchanged. Instruct uses temperature .7, top-p .8, top-k 20, repetition penalty 1, presence penalty 1.5 and 32,768 output tokens; Thinking uses 1/.95/20/1/0 and 81,920 output tokens. BF16 vLLM execution, image processing, family seeds, prompts, stopping and extraction identities are recorded in `spec/model_and_recipe_identity.json`. E* inputs are image-free with identical evidence content across variants. This compares distinct deployed models and recipes, not equal compute or a same-weights Thinking toggle.

## Primary results

All intervals below are unadjusted 95% family-bootstrap intervals: 10,000 draws, seed 120220260929, paired family-equal comparisons and independent task streams. No familywise-significance claim is made. Unscorable outputs are never collapsed into wrong answers.

| Eligible panel | Instruct rescue among scored native failures | Post-E* Thinking−Instruct pp | Instruct net E*−native pp | Thinking net E*−native pp |
|---|---|---|---|---|
| Math | 234/418 = 55.98% [51.20, 60.69] | +14.69 [12.10, 17.39], 926 pairs | +21.99 [18.60, 25.61] | +27.91 [24.67, 31.14] |
| MMStar | 25/37 = 67.57% [52.27, 82.50] | +1.81 [−1.81, 5.43], 276 pairs | +4.51 [0.00, 9.02] | +6.43 [2.14, 10.71] |
| BlindTest lines | 39/46 = 84.78% [73.58, 94.74] | +1.33 [−7.67, 10.33], 300 pairs | −21.67 [−29.33, −14.00] | −5.67 [−13.00, 1.67] |

Math has 31 unresolved follow-ups among 449 identified native-wrong Instruct cases: rescue bounds are 52.12–59.02%. MMStar has one among 38: bounds 65.79–68.42%. BlindTest has none. These conditional percentages do not identify the fraction of all benchmark failures caused by a visual misread.

The post-E* paired gaps have missingness bounds of 11.10–18.60 pp (math), 1.07–2.50 pp (MMStar) and 1.33 pp (BlindTest). These are missing-outcome identification bounds, not sampling uncertainty intervals. Marginal scored accuracies are math I 72.15%, T 85.63%; MMStar I 90.22%, T 91.43%; BlindTest I 63.00%, T 64.33%. Their denominators differ, so their naive subtraction is not the paired estimand.

| Frozen contrast, math minus comparison | Estimate pp | Unadjusted 95% interval |
|---|---:|---|
| C1: Instruct rescue minus MMStar | −11.59 | [−27.27, 4.44] |
| C2: Instruct rescue minus BlindTest | −28.80 | [−39.71, −16.65] |
| C3: post-evidence gap minus MMStar | +12.88 | [8.42, 17.35] |
| C4: post-evidence gap minus BlindTest | +13.35 | [4.17, 22.53] |

The math post-evidence gap is larger in these eligible cohorts. Rescue is not uniquely large in math. Small uncertain gaps in other panels do not establish equivalence, and cross-task differences remain confounded by eligibility, source format, difficulty, ceiling/headroom and benchmark composition.

## Regressions and residual failures

| Panel/model | Correct→correct | Correct→wrong | Wrong→correct | Wrong→wrong | Complete pairs |
|---|---:|---:|---:|---:|---:|
| Math/I | 391 | 46 | 234 | 184 | 855/1,000 |
| Math/T | 543 | 30 | 306 | 110 | 989/1,000 |
| MMStar/I | 216 | 13 | 25 | 12 | 266/280 |
| MMStar/T | 226 | 12 | 30 | 12 | 280/280 |
| BlindTest/I | 150 | 104 | 39 | 7 | 300/300 |
| BlindTest/T | 137 | 73 | 56 | 34 | 300/300 |

The BlindTest 84.78% conditional rescue rate coexists with a −21.67 pp overall Instruct supply effect. Both results must be reported together. The cause of these regressions is unresolved; a representation/interface explanation is plausible, not established.

E* correct/wrong/unscorable/technical-missing counts are math I 671/259/70/0, T 852/143/5/0; MMStar I 249/27/4/0, T 256/24/0/0; BlindTest I 189/111/0/0, T 193/107/0/0. Residual scored-error rates are respectively 27.85%/14.37%, 9.78%/8.57%, and 37.00%/35.67% for I/T. Call these supply-resistant outcomes, not automatically pure reasoning failures. Full four-way transitions and uncertainty are in the sealed primary artifacts.

## Secondary native selectivity and source sensitivities

Family-equal native T−I is math +8.50 pp [6.57, 10.46] on 2,738 scored item pairs/1,922 families; MMStar +0.82 [−1.65, 3.19] on 972 pairs; BlindTest −5.49 [−9.00, −1.83] on 711 pairs. Native marginal correct/wrong/unscorable counts are math I 1,612/1,143/285 and T 1,917/1,097/26; MMStar I 713/260/27 and T 737/262/1; BlindTest I 538/173/3 and T 499/215/0. All have zero technical missingness.

The math item-weighted +7.1950 pp exactly matches Stage14B's +7.20 pp headline; the +8.5010 pp family-equal value exactly matches its family sensitivity. These are distinct estimands on unchanged outcomes. On each eligible native stratum, T−I is math +8.98 pp, MMStar −0.37 pp and BlindTest −14.67 pp. Do not substitute eligible-stratum results for full native results.

The 89 prespecified source strata cover categories, format, structured evidence volume, source flags and repeats. MMStar's non-math sensitivity retains 834 native/164 eligible families, with post-E* T−I +1.86 pp [−3.11, 6.83]. The small overall MMStar gap is therefore not simply due to including its math category. These are descriptive mixture sensitivities, not new confirmatory hypotheses. MathVerse remains the sealed Stage14B contextual modality analysis, not another fresh Stage14C task replication. Unknown historical exposure remains unknown.

## Bounded D1 evidence elicitation

| Task/model | Scored / 100 | Full E* recovery | Family-mean exact atom recall | Family-mean subfact recall |
|---|---:|---:|---:|---:|
| Math/I | 97 | 20 | 24.48% | 35.11% |
| Math/T | 100 | 31 | 34.83% | 45.86% |
| MMStar/I | 96 | 38 | 39.58% | 46.90% |
| MMStar/T | 99 | 53 | 53.54% | 63.55% |
| BlindTest/I | 100 | 0 | 0% | 0% |
| BlindTest/T | 100 | 0 | 0% | 0% |

Thinking demonstrates more complete evidence in the math/MMStar probe, descriptively. This separately prompted behavior does not establish evidence acquired by the original native solver. The [D1 report](stage14c_D1_summary.md) retains micro denominators, structured-object fidelity, targeted precision, all recovery/answer-transition crosstabs and unresolved bounds.

BlindTest I returned bare answers in 100/100 cases; T in 91/100. The nine T prose responses contain 11 accurate partial observations and 13 contradictory assertions, with no complete frozen source unit. The native answer-only instruction remains after the evidence-probe instruction. This is an observable output-contract conflict and possible contributor, not a tested causal explanation. No outcome-dependent prompt repair occurred. Zero demonstrated complete-unit recall is not zero visual knowledge. Counts without source locations, partial object descriptions, and approximate chart readings below the frozen precision also limit recovery interpretation. Targeted precision measures complete required units among all asserted visual facts, so it penalizes accurate unmatched facts; it is not ordinary factual correctness.

Six I probes hit the cap (three math, three MMStar) and remain unresolved. No T probe hit its cap; all T responses closed their Thinking block. A seventh I unresolved and the sole T unresolved probe arise from the source defect below. Two-pass review was by the same agent and does not establish independent inter-rater reliability.

## Late source-QC finding, preserved transparently

The original image for MMStar:997 has a plant→horse arrow, while its frozen E* reverses that edge. This was confirmed on repeated source-image inspection during D1 review, after main outcomes existed. Both D1 counterparts are unresolved. Original E*, cohort membership, raw outputs and primary results remain immutable; no item was replaced or rerun.

An explicitly post-hoc, point-estimate-only check excluding this one source-defective family changes MMStar post-E* T−I from +1.8116 to +1.8182 pp (276 to 275 scored pairs). Instruct rescue and net supply remain exactly unchanged; T net supply changes from +6.4286 to +6.4516 pp. This does not replace the primary analysis or its intervals. It shows the disclosed defect does not explain the main pattern. Frozen final-QC coverage is a historical gate result, not a claim that all sources are now known error-free. See `analysis/late_source_QC_exclusion_sensitivity_v1.json` and the two source-conflict audit records.

## Technical evidence and resources

Main generation used 12,077,889 output tokens; D1 used 1,371,651. Main cap hits: I 36, T 1; D1: I 6, T 0. Cap hits and strict repetition flags are retained separately from answer scorable status. No main/D1 OOM or final technical failure occurred. All GPUs were released when their finite queues finished.

Observed/proxy allocation cost is **14.693634 GPU-hours**, including **1.421389 D1 GPU-hours**, below the 120/12 GPU-hour ceilings. The 75 gross requested GPU-hours include unspent reservation time and cancelled pending work; they are not consumption. Retained Slurm intervals are used where available; expired job 139215 uses its explicit worker-lifetime proxy. `sacct` is unavailable, so startup/release precision for that job is limited. Concurrent request latencies are not summed as GPU-hours. GPU memory measurements from the frontend do not capture vLLM child peak VRAM; engine logs are retained.

G2's missing local pyarrow dependency was repaired before scientific requests. Its changing-batch Thinking seed replay diverged; a fixed-context fresh-engine 128-token replay matched exactly. The original failure remains preserved. This validates the bounded matched execution context, not universal bitwise determinism. Later parser repairs preserved ambiguous syntax for response-only review; no prompt, source, seed, recipe or correctness criterion was selected by accuracy. Main I/T scoring includes 437/669 response reviews and 673/866 fixed QC records. MMStar uses committed-final adjudication rather than the upstream first-character matcher; this is not an official leaderboard replication.

## Artifacts and stopping boundary

The approved figure versions are [eligibility](../figures/figure1_eligibility_map.png), [rescue and net effects](../figures/figure2_rescue_profile_v2.png), [post-evidence profile](../figures/figure3_post_evidence_profile_v3.png), [native selectivity](../figures/figure4_native_selectivity_v3.png), and [descriptive task map](../figures/figure5_task_map_v3.png). Display revisions preserve numerical data and original figures. Each must be read with the eligibility and late-QC qualifications above.

The [primary-only report](stage14c_primary_summary.md) and its seal precede all subgroup/D1 interpretation. [Source sensitivities](stage14c_sensitivity_summary.md), [D1 diagnostics](stage14c_D1_summary.md), raw outputs, annotation versions, source/code hashes, final validation and resource accounting are linked from [the report index](../../../reports/stage14c/index.md). Final hash validation verifies execution/provenance, not perfect semantic source accuracy.

**Exactly one recommendation:** prepare a bounded prospective validation of the BlindTest textual evidence representation and evidence-probe output contract for separate approval; see [recommendation and rationale](next_stage_recommendation.md). It has not been launched. No Stage14D/E/F, new model, new benchmark, method, D2/D3 or reserve experiment follows automatically. **STOP at Stage14C.**
