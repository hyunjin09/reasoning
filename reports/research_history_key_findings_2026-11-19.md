# Research history — key experiments and findings

**Updated: 19 November 2026.** This is the shorter scientific account of the project. It retains experiments that changed the conclusions, including consequential negative results. Routine instrumentation, scheduling, intermediate debugging and superseded execution plans are condensed. The [complete history](research_history_all_stages_2026-11-19.md) preserves those details and the original reports.

## Current scientific position

Our objective is to improve **task-critical visual evidence acquisition during reasoning**: identify the unresolved visual premise, retrieve it from the correct source in global context, and incorporate it into the solver's reasoning.

| Research question | What we have established | What remains unestablished |
|---|---|---|
| Does reasoning demand affect visual source use? | Controlled demand changes redirect causally relevant source use. | Attention shifts alone do not certify correct acquisition. |
| Can reasoning become text-sufficient after evidence resolution? | A functional handoff occurs in a controlled synthetic assay. | A universal handoff time or Thinking-specific late-access regime on MathVision. |
| Does supplying usable evidence rescue failures? | Yes, substantially in the source-eligible MathVision cohort. | That all rescued failures were purely perceptual, or that evidence supply always helps across tasks. |
| Does Thinking retain an advantage with the same evidence? | Yes, in the tested deployed-model comparisons. | A clean decomposition of that advantage into perception, state production, computation or utilization. |
| Have we developed a successful acquisition method? | We completed SAVA, a Source-Premise Ledger and a reader-mode diagnostic. | None demonstrated a reliable improvement in the primary acquisition objective. |

**Research is paused after Stage14E2.** The methodology objective remains open.

## 1. Establishing causal visual source use

**Principal stages: 3A, 3B.2, 3B.7-R, 3B.8–9, 3C.4, 4A.**

Early attention studies motivated the work but could not distinguish lexical alignment from acquisition. Counterfactual and intervention studies provided stronger evidence:

- **Visual content matters before explicit verbalization.** Stage3A found positive counterfactual content effects in all 49 bases, including sensitivity at all 46 eligible early pre-mention tests.
- **The source can control the evidence readout.** Stage3B.2 found bidirectional donor-source control in 49/49 bases at the two tested coordinates.
- **Value content carries a substantial part of the tested transfer.** Revalidated ROI experiments supported a Value-dominant path. A rank-eight representation failed to generalize; later rank-16/rank-24 tests supported more distributed representations.
- **Dependence is spread over depth and recent time.** In Stage3C.4, all-layer current-query suppression retained median evidence preference 0.8436. Including the previous query reduced retention to 0.6515. A single head, query or layer is not the whole mechanism.
- **Demand can redirect source use.** Stage4A used A→B→A demands: 36/48 W2 and 30/48 W8 comparisons showed dynamic behavior; all 24 semantic-challenge cases favored the demanded source over other/sham controls.

**Conclusion:** reasoning-conditioned source retrieval has causal support in these bounded assays. This does not establish that a model chooses the right target during an ordinary mathematical solution. Query/routing restoration also sometimes failed to restore the required evidence content.

Sources: [counterfactual content](../outputs/stage3a/summaries/stage3a_summary.md), [Value representation](../outputs/stage3b9/summaries/stage3b9_summary.md), [temporal redundancy](../outputs/stage3c4/summaries/stage3c4_summary.md), [demand switching](../outputs/stage4a/summaries/stage4a_summary.md).

## 2. Causally diagnosable natural failures were scarce

**Principal stages: 5A–7A and the reduced Stage7A-Bench sweep.**

These stages separated source-faithful reads, wrong-source reads, extraction errors, prior-filled claims and downstream errors. An important correction was that a wrong-versus-correct margin change does not necessarily show that a source caused the actual wrong token. High attention and no-image correctness were also inadequate substitutes for causal labels.

Stage7A scored 480 events and certified:

| Strong state | Events |
|---|---:|
| Faithful read | 181 |
| Wrong-source read | 3 |
| Source-coupled extraction error | 1 |
| Downstream integration error | 2 |
| Prior-fill / stale-source read | 0 / 0 |

Most remaining events were unresolved. The zero counts mean **no certified cases under the assay**, not proof that these failures never occur. Monitor and intervention readiness gates remained closed.

The subsequent benchmark sweep retained Phantom, CharXiv, MathWild, MMMU-Pro and MMLongBench-Doc. Across 187 causal-pilot events, it found 17 strong faithful reads, 66 weaker faithful reads, three wrong-source reads and 101 unresolved events. Low benchmark accuracy did not reliably produce source-identifiable, causally diagnosable failures. The remaining overlapping benchmarks were deferred.

**Conclusion:** causal identifiability and correctly oriented readouts were more limiting than benchmark breadth. Broad failure-state or monitor claims were not justified.

Sources: [Stage7A](../outputs/stage7a/summaries/stage7a_summary.md), [benchmark comparison](../outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_summary.md).

## 3. Detecting visual retrieval did not yield an effective intervention

**Principal stages: 8A, 8B Blocks1–3, 8C v3.**

A retrieval proxy achieved held-out AUROC **0.9776**, but cheap transport predictors did not generalize. The natural MathVision studies also lacked enough clean matched local failures for the proposed causal routing test. Whole-trajectory success/failure signals became uncertain under full adjustment.

After a numerical decomposition repair, Stage8C v3 tested direct visual gain on 128 development cases. Correct counts at gains 1, 1.25, 1.5 and 2 were **61, 60, 59 and 57**. Promotion gates failed, so the held-out expansion was not launched.

**Conclusion:** observing retrieval, transporting Value information and increasing visual contribution are different achievements. Increasing visual contribution did not establish an accuracy improvement.

Sources: [proxy calibration](../outputs/stage8a/summaries/stage8a_summary.md), [gain experiment](../outputs/stage8c_v3/v1/stage8c_v3_summary.md).

## 4. Functional handoff is supported, but a broad late-access hypothesis failed

**Principal stages: 9A dynamics, 9A.3–5, 10A-R, 10B–C.**

Stage9A compared Direct, prompted CoT and native Thinking on 64 MathVision families, with 1,904 distinct masked continuations. The primary Thinking-minus-CoT damage contrasts were:

| Access intervention | Difference |
|---|---:|
| Cumulative cutoff at 512 tokens | −4.69 pp |
| Cumulative cutoff at 2,048 tokens | −3.13 pp |
| Final two local windows | −2.34 pp |
| Demand-aligned minus matched-control knockout | +10.71 pp |

All simultaneous intervals included zero. The demand contrast became zero when algebra was excluded. Thus the study did **not** establish greater late direct-image-access necessity in Thinking. Synthetic calibration also showed that baseline validity and attention-redistribution controls materially affect finite-access conclusions.

Stage10A-R subsequently supported a **functional perceptual-to-textual handoff** in a controlled synthetic assay: all four preregistered contrasts had adjusted intervals above zero. This is narrower than a universal visual-access boundary.

Stage10B found clean recurrent visual demands in **26/224 trajectories (11.6%)**. Stage10C's causal reopening study did not pass its full gate. Recurring visual language therefore cannot automatically be interpreted as causally necessary reacquisition.

Sources: [MathVision dynamics](../outputs/stage9a_dynamics/amendment_v1/stage9a_summary.md), [later control-queue closure](../outputs/stage9a_dynamics/amendment_v1/stage9a3_transition_addendum.md), [handoff](../outputs/stage10ar/v1/stage10ar_summary.md), [reopening](../outputs/stage10c/v1/stage10c_summary.md).

## 5. Evidence supply and downstream reasoning both matter

**Principal stages: 12B-S, 12T-S, 12U-S–12Y-S, 13A, 13D.**

Before these comparisons, Stage11–12 technical work exposed severe Direct completion and output-contract problems. Reproducing a historical recipe did not validate it: even the official Qwen MathVision sanity recipe produced only **7/12 committed Direct finals**, versus **12/12 Thinking finals** on the fixed test cases. Later studies used their separately validated, pathology-aware protocols. These are distinct checkpoints/recipes, not an equal-compute thinking toggle.

The 61-family Stage12B-S study found 29 scored native failures; 26 had complete profiles. Supplying E* rescued **12/26**. The failure profiles included incomplete evidence recovery, context-use issues, downstream failures and mixed cases; incomplete evidence was not relabelled as a proven misread.

Stage12T-S showed a Thinking rescue signal, including **5/11 mixed B4 failures**. Only one B1 rescue was fully evidence-linked. The result pointed toward downstream benefits without establishing better visual acquisition.

Selected prefix-transfer studies showed that Instruct could use some Thinking-produced textual states. However, single-step localization was inconsistent, distributed-state tests remained unresolved, and a 96-family held-out replication yielded only two eligible transfer candidates. The selected-case portability result did not become a broad confirmed mechanism.

Stage13A provided stronger evidence for the phenomenon itself: on 84 complete families over three seeds, **Thinking's equal-evidence advantage was +11.11 pp [5.56,17.06]**. The source families had been used earlier; fresh generations were not a new independent source cohort. Stage13D's derived-state priming and immediate-buffer contrasts did not confirm either proposed explanation.

**Conclusion:** Thinking can retain an advantage after evidence is supplied. We have not isolated a general explanation for that advantage.

Sources: [official-protocol audit](../outputs/qwen3vl_official_eval/v1/qwen3vl_official_sanity_summary.md), [failure profiles](../outputs/stage12bs/v1/stage12bs_summary.md), [Thinking rescue](../outputs/stage12ts/v1/stage12ts_summary.md), [held-out transfer](../outputs/stage12xs/v2/stage12xs_summary.md), [equal-evidence confirmation](../outputs/stage13a/v1/stage13a_summary.md), [mechanism tests](../outputs/stage13d/v1/stage13d_summary.md).

## 6. Large-scale MathVision confirmed the evidence-supply phenomenon

**Principal stages: 14A–14B.**

Source-only cohort construction produced 1,000 eligible E* records from the 3,040-item MathVision census. Structured visual objects retained internal subfact counts rather than being treated as uniformly simple scalar evidence.

Stage14B completed 17,536 main and 9,600 fresh confirmation calls, plus technical validation. Its central results were:

| Endpoint | Result | Denominator |
|---|---|---|
| Native Thinking−Instruct | **+7.20 pp [5.67,9.08]** | 2,738 common scored item pairs |
| Instruct E* rescue | **55.98% [51.08,60.80]** | 234/418 scored native-wrong followups |
| Equal-E* Thinking−Instruct | **+14.69 pp [12.10,17.39]** | 926 common scored pairs |

Thirty-one native-wrong E* followups were unresolved and excluded from the scored rescue denominator. MathVerse also showed a larger Thinking advantage in the more visual modality profile: **+9.28 pp [6.15,12.36]** for the preregistered visual-relative contrast. Multi-seed repetitions retained the main directions.

**Conclusion:** supplying usable source evidence rescues many failures, while substantial post-evidence differences remain. E* changes representation and reasoning context as well as access; this is not proof that 55.98% of failures are purely perceptual.

Source: [Stage14B final report](../outputs/stage14b/summaries/stage14b_final_summary.md).

## 7. BlindTest demonstrated that “correct evidence” can still harm performance

**Principal stages: 14C and 14C-V.**

Cross-task results differed sharply. MMStar Instruct E* rescue was **25/37 (67.57%)**, but its post-evidence Thinking gap was small and uncertain. On BlindTest's 300 eligible line-intersection families, Instruct had **39 rescues but 104 regressions** under the original E* representation: net **−21.67 pp [−29.33,−14.00]**.

Stage14C-V then tested the same source content in three formats:

| Format | Instruct accuracy | Thinking accuracy |
|---|---:|---:|
| R0: original text | 190/300 | 191/300 |
| R1: typed structured fields | 123/300 | 177/300 |
| R2: entity-explicit prose | 245/298 | 277/300 |

The predicted structured-format benefit failed: Instruct R1−R0 was **−22.33 pp**. Prespecified prose helped: R2−R0 was **+18.46 pp** for Instruct and **+28.67 pp** for Thinking. Instruct R2 nevertheless retained 46 regressions versus 39 rescues, with two unscorable outputs.

The historical 104 regressions and fresh R0's 103 are distinct runs. R2 also changed response behavior, so its benefit is a format-package effect rather than proof of one naming or reasoning mechanism. Separately elicited D1 records do not establish what the native solver used.

**Conclusion:** source faithfulness, task sufficiency, answer safety and textual usability are separate requirements. The representation panel is complete; the wider Stage14C-V contract review/final closure remains unfinished.

Sources: [cross-task results](../outputs/stage14c/summaries/stage14c_final_summary.md), [representation experiment](../outputs/stage14c_v_blindtest_validation/summaries/stage14c_v_R_primary_summary.md).

## 8. Native trace audits identified errors and global-context difficulty

**Principal stages: 14D-0, answer/evidence supplement, visual-difficulty v2.**

The retrospective audit reviewed **300 families and 600 native outputs**, with 1,883 source-adjudicable subfacts. It separated a 150-family source-selected R panel from a 150-family outcome-enriched F panel.

In R, wrong native answers contained at least one explicit required-source error in **52/73 Instruct** and **50/69 Thinking** cases. Errors also occurred in **13/63** and **15/80** correct answers. Evidence correctness strongly associated with final correctness, but was neither necessary nor sufficient.

The paired Thinking−Instruct explicit-error contrast was **−3.60 pp [−7.86,+0.40]**: no clean perception advantage was established. Some wrong finals had every required reference fact explicitly correct, although this does not rule out errors in other visual claims or downstream binding.

The source-difficulty analysis found higher explicit-error coverage for **global-required versus local-sufficient evidence**:

- Instruct: **+12.33 pp [2.49,21.99]**.
- Thinking: **+14.72 pp [7.94,21.76]**.

Operation depth had no reliable monotonic effect. Tiny-text difficulty was not adequately represented; counting and competitor patterns remained exploratory.

**Conclusion:** global structure and contextual binding are plausible intervention targets. This is retrospective, single-AI-reviewed association, not evidence that adding a crop or rereading will fix the problem. Unmentioned or ambiguous facts remain unobservable, not acquisition failures.

Sources: [native audit](../outputs/stage14d0/reports/stage14d0_native_trace_audit_results.md), [answer/evidence tables](../outputs/stage14d0_answer_evidence_supplement_v1/supplementary_report.md), [difficulty analysis](../outputs/stage14d0_visual_difficulty/v2/report.md).

## 9. SAVA did not establish a benefit

**Principal stage: 14D-1 full 72-family pilot.**

The method was: **reasoning subgoal → value-free query → predicted source address → visual readout → resume solver**. Technical replay, grammar and provenance problems were repaired before the completed pilot; those early invalid outputs were not scientific evidence.

| Arm | Correct /72 |
|---|---:|
| Native continuation | 39 |
| Generic lookback | 41 |
| Query without fresh helper image | 39 |
| Query + full-image readout | 36 |
| Query + address + full image | 37, with one unscorable |
| Query + address + global/local images | 36 |

Primary full-image SAVA minus native was **−4.17 pp [−12.50,+4.17]**, with three rescues and six regressions.

The acquisition records explain why accuracy alone was insufficient:

- Only **22/62 accepted queries** were fully task-relevant.
- **47/72 query reviews** concerned given or tentatively mentioned information; a tentative mention is not necessarily redundant.
- Only **14/49 local views** correctly localized the requested source.
- In the frozen 24-family acquisition panel, SAVA supplied new correct information in **3/24**, versus **2/24** generic lookback.
- None of the three primary rescues supplied a clearly new task-critical fact in the standardized helper readout.

**Conclusion:** the tested pipeline did not demonstrate improvement. Target selection, localization, reading and checkpoint timing remain separate possible bottlenecks; the result does not disprove all subgoal-addressed methods.

Source: [completed SAVA report](../outputs/stage14d1_sava_pilot/v1/reports/feasibility_main_v8.md).

## 10. The Source-Premise Ledger did not generalize

**Principal stage: 14E.**

The completed cycle combined a 72-family SAVA postmortem, a 24-family diagnostic, one 24-family development revision and a disjoint 32-family evaluation.

The revised method enumerated source obligations, classified them as known/tentative/unresolved, selected an unresolved obligation, and requested a full-image readout. It used no E*, gold or human ROI at deployment. Development produced three partial useful reinspections, but the final evaluation found:

| Condition | Useful acquisition /32 | Correct final /32 |
|---|---:|---:|
| Native | Not separately elicited | 19 |
| Original SAVA-style reader | 1 | 20 |
| Source-Premise Ledger | 0 | 20 |

The acquisition difference was **−3.125 pp [−9.375,0]**. Both treatments rescued the same single family, and both helpers merely repeated already-known information. The ledger had 17 accepted queries, 12 invalid fallbacks and three NONE decisions; none of its accepted targets was fully task-relevant.

Source-informed diagnostic targets sometimes contained qualitative hints, so they cannot be treated as a clean value-free oracle upper bound. They were kept separate from deployable evaluation.

**Conclusion:** source provenance and a structured demand interface were insufficient. Producing and reading the precise relational binding remained an actionable obstacle. The small final-answer change did not demonstrate improved acquisition.

Source: [Stage14E report](../outputs/stage14e_acquisition_development/v1/reports/final_research_report_v1.md).

## 11. Allowing the reader to reason did not fix the primary acquisition deficit

**Principal stage: 14E2.**

On 24 previously observed development families, matched compact and reasoning readers used the same diagnostic targets and images. Useful reads were **4/24 in both modes**, difference **0 pp [−16.67,+12.50]**, with two gains and two losses.

Original model-selected targets gave 3/24 compact versus 5/24 reasoning. The diagnostic-target no-image condition produced one source-correct response; that is not visual acquisition. No condition recovered a new or validly reinspected **complete task-source representation**.

Reasoning was much more expensive: **114,501 tokens** versus **2,340** for the matched compact condition, with five reasoning cap hits. No downstream solver-accuracy experiment was run.

**Conclusion:** extra helper deliberation alone did not improve the primary acquisition endpoint. The experiment is complete; the fresh 32-family evaluation remains unused and research is paused.

Source: [Stage14E2 report](../outputs/stage14e_readout_mechanism/v1/reports/final_diagnostic_report_v1.md).

## What was condensed from the complete history

The early PIQD/Stage0–2 instrumentation, most intermediate Stage3 localization variants, hardware calibration, dataset plumbing, job migrations, repeated technical repairs and cancelled proposal details are retained only where they change interpretation above. Their omission is editorial, not deletion of evidence or a claim that they had no engineering value.

Consequential negative results remain included. The old Stage14D 1,674-continuation/375-GPU-hour proposal remains **HOLD**; Stage14C-V remains unfinished overall. No experiment is resumed or selected by this summary.

For exact protocols, secondary contrasts, case-level provenance, uncertainty definitions and the complete stage index, use the [full archived history](research_history_all_stages_2026-11-19.md).
