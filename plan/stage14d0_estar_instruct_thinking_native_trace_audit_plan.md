# Stage 14D-0 — E*-Anchored Instruct vs Thinking Native Reasoning Trace Audit

**Revision:** v2, 2026-10-11  
**Status:** **PROPOSED RETROSPECTIVE AUDIT ONLY — ORIGINAL STAGE14D MAIN RUN ON HOLD**  
**Supersedes for Stage14D-0 scope:** `stage14d_revised_evidence_trace_audit_plan.md` (the previous four-generation comparative audit specification); **does not modify** the archived Stage14D intervention plan or historical results.  
**Primary benchmark:** frozen MATH-Vision Stage14A/14B **1,000 `E*`-eligible source families**.  
**Evaluated models:** pinned **Qwen3-VL-4B-Instruct** and **Qwen3-VL-4B-Thinking**, preserving each checkpoint's recorded native decoding recipe.  
**Primary research comparison:** **source-derived `E*` vs Instruct native trace vs Thinking native trace**.  
**Goal:** discover *which observable task-critical visual claims are wrong, misbound, unstated, contradictory, self-revised, or correctly stated but misused*, and use the resulting taxonomy to design a **future** evidence-recovery decoder.  
**New inference authorized:** **none**. Do not start or approve the old **375 GPU-hour** run.

> **한국어 요약:** 같은 MATH-Vision 문제를 `E*`(기준 시각 정보), Instruct native reasoning, Thinking native reasoning의 **3열**로 비교한다. 모델은 **2개**, `E*`는 모델 출력이 아니다. 약 **300 families × 최대 2 native traces = 최대 600 traces**가 primary 분석 단위다(정확한 수는 manifest 대조 후 확정). 기존 **414개 two-pass-reviewed native traces**는 이미 검토한 기록이지 `414 × 3`개의 새 trace가 아니다. 기존 `I_E*`/`T_E*`는 **정답/오답 및 scoreability metadata에 한해서만** 쓰고 reasoning text는 main audit에서 읽지 않는다. 먼저 30–50개 pilot → annotation rubric freeze → 약 300개 audit → 작은 후속 intervention 별도 제안. **1,674 sealed continuations 실행 금지, 375 GPU-hour 승인 보류, Stage14C-V closure waiver 금지.**

---

## 0. Research framing and questions

### Three paper claims (current standing framing)

- **C1 — Evidence Handoff (existing mechanistic finding):** On selected successful trajectories, visual-access-dependent evidence resolution can transition to text-prefix-sufficient downstream computation. This is a **functional** handoff, not a universal disjoint two-phase architecture, and text sufficiency does not establish a unique text carrier.
- **C2 — Evidence Bottleneck (existing large-N result):** Supplying source-derived task-critical `E*` as **text instead of an image** rescues many native errors. In Stage14B, MATH-Vision Instruct scored native-wrong → `E*`-correct was **234/418 = 55.98%**, with **+21.99 percentage-point** native-to-evidence net gain for Instruct in the eligible cohort. Under equal textual `E*`, Thinking–Instruct paired accuracy difference was **+14.69 pp** (926 scored pairs). `E*` changes visual access, format, evidence binding, and interface; the rescue proportion is **not** the percentage of pure visual-acquisition failures.
- **C3 — Evidence Recovery Methodology (future hypothesis):** Develop a decoding-time policy that **identifies unresolved task-critical evidence, reacquires it from the image, verifies it, and then uses it** to improve answer accuracy. Whether this beats additional thinking is a **later evaluation comparison**, not the central design objective.

**Immediate D0 questions:**

1. For the same image/question, **which individual source-derived evidence atoms or subfacts are explicitly correct, incorrect, misbound, unmentioned, or contradicted** in Instruct vs Thinking native reasoning?
2. **Which error classes overlap** across I and T, and which are model-specific? Are *the same incorrect values/relations* shared, or are errors different?
3. **When** is each evidence demand, claim, downstream use, and revision first observable in the response? Is a wrong visual premise **propagated into calculation**, ignored, or corrected?
4. Does Thinking exhibit **observable self-correction** of initially wrong visual facts? If yes, what text-visible event precedes correction and is the corrected evidence actually used?
5. How often is relevant source evidence **already correctly stated but misused** (binding, integration, deduction, arithmetic), suggesting acquisition-only repair would be insufficient?
6. How do these patterns relate **descriptively** to the **already scored native→`E*` correctness transitions**, without rereading `E*`-conditioned reasoning text or inferring mediation?

**Explicit non-goal:** This retrospective trace audit **cannot** show that a visual fact was absent from a hidden state, that a self-reported “look again” involved new image retrieval, or that correcting a text-visible fact *causally* fixes a final answer. Those are prospective Stage14D-1 questions.

---

## 1. Hard execution boundaries and preservation

### 1.1 Previous Stage14D preparation — preserve and reconcile

| Operator-reported preparation | Reported figure | Required D0 action |
|---|---:|---|
| Source-image review | **300 images** | Match to stable family IDs, QC findings, and `E*` version; reuse if applicable |
| Native trace two-pass checks | **414 applicable native traces** | Establish **family × model × seed × condition × trace ID** exactly; trace count ≠ family count |
| Technical preflight | **24 calls passed** | Preserve receipts; do not repeat GPU preflight |
| CPU/input checks | **29 CPU tests**, **1,674 inputs passed** | Preserve checks and provenance |
| Sealed intervention continuations | **1,674** (**1,196 T**, **478 I**) | Keep immutable and **do not execute** |
| Valid semantic counterfactuals | **None** | Record assay as **not executed / unavailable**, not a null experimental result |
| Historical preparation compute | **0.363 GPU-hours** | Preserve original operator report/receipt; **no new budget** |
| Old proposed main budget | Estimated **178 GPU-hours**, doubled-length ~**363**, ceiling **375** | **HOLD; never interpret as approved** |

Reported old repository documents (relative paths to verify in the operator's environment):

- `outputs/stage14d/reports/stage14d_main_release_review_v1.md`
- `plan/stage14d_causal_evidence_acquisition_localization_plan.md`

Do **not** fabricate their contents or paths if absent. Compare manifest IDs and SHA256 for all reusable artifacts. If a joined output is missing, **report it**; do not regenerate it.

### 1.2 Approval status

- The old **Stage14D targeted-continuation main run remains ON HOLD**. Prior approval covered **source/anchor preparation and bounded calibration only**.
- Do **not** waive the unfinished **Stage14C-V closure prerequisite**. D0 is a separable CPU/read-only retrospective analysis; it does not close 14C-V or authorize new causal intervention runs.
- **No** scientific GPU calls, new model generations, fresh continuation forks, LLM judge calls, external annotation services, extra checkpoint probes, or new semantic-image perturbations are authorized.
- Allowed: existing-output inventory, reproducible CPU text parsing, local audit viewer/report generation, SHA256 receipts, and **in-team human annotation/source review** consistent with approvals. Automation that suggests a label must not be misrepresented as validated annotation.
- Archive past plans/results unchanged; write all new files under **`outputs/stage14d0/`** or a separately versioned folder.

---

## 2. Exact units, inputs, and output counts

### 2.1 Three-column **primary** audit

| Column | Material | Count for a complete family | Role |
|---|---|---:|---|
| **`REF_ESTAR`** | Original image/question, source-derived `E*` text and evidence-atom ledger | 1 reference | Anchor for task-critical facts, **not** a reasoning trace |
| **`I_IMG`** | Qwen3-VL-4B-Instruct output from **original image + question**, including pre-answer reasoning-like text and final answer | 1 native trace | Observable visual evidence and downstream use |
| **`T_IMG`** | Qwen3-VL-4B-Thinking output from **original image + question**, including recorded reasoning and final answer | 1 native trace | Observable visual evidence and downstream use |

**Target primary audit:** approximately **300 distinct families**; at most **300 `I_IMG` + 300 `T_IMG` = 600 native traces**, assuming exactly one selected native output of each model per family. The actual paired/full-coverage denominator is **TBD until inventory**. Multiple seeds/runs are **not** silently counted as different families; choose a prespecified primary seed/recipe or report repeat runs as nested sensitivity analysis.

**`I_ESTAR` and `T_ESTAR`: outcome metadata only.** Link existing **correct/wrong/unscorable/technical-missing** statuses from Stage14B for descriptive rescue strata, including model-specific `native wrong → E* correct` and `native correct → E* wrong`. **Do not require or annotate their reasoning text in D0**, and do not include them in native-trace count. A few preselected examples could be inspected in a **separately approved follow-up**, not by default.

### 2.2 What the original 414 trace checks mean

- **414 is the number of applicable native trace checks previously reported** for the old 300-image intervention preparation. It is not an extra 414 new samples, and **not** `414 × 3` or `414 × 4`.
- Some prechecked families may have only I or only T, or multiple eligible anchors; the **manifest**, not arithmetic inference, determines coverage.
- There may be raw archived native generations that were **not** among the 414 preflight-eligible traces. Their use is allowed **only as existing outputs** after exact provenance matching.
- For every proposed family report: `has_Estar`, `has_I_IMG`, `has_T_IMG`, `I_trace_readable`, `T_trace_readable`, `both_scored`, `prior_review_coverage`, and exact output hashes.

### 2.3 Join keys and no-lookahead safeguards

Use stable conservative **family ID**; source image hash; question/version; Stage14A `E*` record ID/version; model/checkpoint hash; processor/template; run/seed; native prompt; validated decoding parameters; raw output path/hash; extraction boundary; existing score and scorer version. Verify input is **native image-conditioned** (no accidental `E*` text) and that referenced evidence is not merely already present in the question text.

- Never replace `E*` or question text after reading model trace. Flag later source QC discoveries prospectively in a separate ledger.
- If evidence reference is wrong, insufficient, ambiguous, trivially answer-leaking, or relies on image information not actually source-valid, mark `SOURCE_QC_FAIL`/`SOURCE_UNCERTAIN` and **do not score the model as wrong against it**.
- Preserve `WRONG`, `CORRECT`, `UNSCORABLE`, `TECHNICAL_MISSING` and `NO_TRACE` separately.
- If a model explicitly correctly infers a fact absent from `E*`, do not mark it hallucinated just because it was not listed: `E*` is **source-derived task-critical evidence, not necessarily exhaustive visual truth**.

---

## 3. Sampling: pilot first, freeze the approximately 300-family main set

**Source frame:** Stage14A/14B frozen **1,000 MATH-Vision `E*`-eligible families**; source metadata reports **1,448 primary evidence atoms** (985 structured-layout, 463 scalar-relation), with structured evidence in **797 families**. These are the **1,000-family source-corpus totals**, not necessarily the atom counts in the selected 300. Structured atoms can encompass multiple separately checkable subfacts.

### 3.1 D0-P: 30–50-family deep annotation pilot

From the **already prepared 300 families first**, select **30–50 distinct** cases **with available source, `E*`, and both native traces where possible**. Deliberately cover a mix of source evidence types and existing outcome patterns:

- `I_IMG wrong / T_IMG correct`;
- both native wrong;
- `I_IMG correct / T_IMG wrong`;
- both native correct;
- `native wrong / E* correct` and `native wrong / E* wrong` strata for each model (overlapping with preceding groups).

These are **sampling strata for discovery**, not mutually additive quotas. Keep a pilot receipt with exact IDs, outcome labels, source types, model outputs, provenance, and explicit selection reasons. All **30–50** count toward the ~300 target if ultimately selected; the initial sample is not itself representative.

Pilot tasks: test a source-blind pass for visual-claim extraction; adjudicate atom/subfact matching, direct visual observation vs derived math, entity binding, unsupported assumptions, errors later corrected, and trace length differences. Freeze the coding book **before** broad annotation.

### 3.2 D0-M: approximately 300 distinct families (recommendation, not a guaranteed availability count)

| Panel | Proposed target | Selection and interpretation |
|---|---:|---|
| **R — Source-selected representative panel** | **150 families** | Predefine source-stratified/random selection from the **1,000** before inspecting I/T traces; use for prevalence **only for the eligible frame and with documented selection probabilities, coverage and missingness** |
| **F — Outcome-enriched discovery panel** | **150 additional families** | Oversample I/T disagreement, both wrong, supply-responsive failures, supply-resistant failures, self-correction candidates, and rare evidence types; **not** for overall prevalence |
| **Total** | **~300 distinct families** | Deduplicate R/F and pilot by family ID; any nontrivial missingness/shortfall reported |

**Reuse economics:** An old set of 300 already source-reviewed families is **not necessarily a new representative sample**. In inventory, calculate R/F overlap and reuse as many as valid. If source-selected R cannot be assembled without prohibited new work, do **not** silently relabel a biased old sample representative: report an **exploratory prepared-300 cohort**, with a separate user decision whether additional CPU source review is worthwhile. No new evaluated-model inference to fill gaps.

Freeze: RNG seed, deterministic selection algorithm, strata, inclusion probabilities (if relevant), available paired-arm coverage, exclusion/QC rules, and selection file hashes. Raw traces should remain untouched.

### 3.3 Analysis denominators

Report at minimum: eligible source families; selected families; source-QC pass/fail; I native available; T native available; I/T pair available; both scoreable; required evidence atoms/subfacts; model-claim opportunity; explicit visual claims; explicit claims actually used; initial incorrect claims available for correction. Do not divide an atom-level event count by number of families without declaring aggregation, and do not treat multiple atoms in one family as independent samples.

---

## 4. Annotation workflow and schema

### 4.1 Pass A — **extract native claims before revealing `E*` and outcome**

For each archived `I_IMG` and `T_IMG` output, show **question + original image + raw trace** to in-team annotators, but **mask `E*`, final-answer gold/correctness, and the other model trace** until claims are extracted. Record exactly what the model *asserts about the image*, including spans and claim timing; separate from text-based deduction and unsupported geometrical assumptions. Mask model identity where practical, but do not assert blinding if answer/trace format reveals it.

Examples of claimed fact types:

- directly read value/label/angle/coordinate;
- which entity that value is attached to (binding);
- visual spatial/metric relation: perpendicular, parallel, tangent, collinear, congruent, intersection, ordering;
- diagram/topology/global structure, table/chart/grid composition;
- interpretation of a visual convention (tick mark, right-angle mark, arrow, legend);
- unsupported assumption or over-read of a not-explicitly-marked property;
- **mathematically derived** relation/value (must be tagged separately, **not** mistaken for directly retrieved evidence).

Record claim `span_start/end` (prefer raw token offsets plus quoted text and char offsets), `claim_text`, `canonicalized_fact`, `entity_ids`, `evidence_type`, `direct_visual|derived_math|assumption|ambiguous`, `assertion_polarity`, confidence expressed in trace (not treated as actual calibrated confidence), and `occurrence_index`.

### 4.2 Pass B — **source-first match against validated `E*`**

Only after Pass A, expose the original image/source QC and structured `E*` atoms. Match candidate claims to each *source-supported required atom/subfact*, without forcing every trace utterance to correspond to `E*`.

**For each model × evidence atom/subfact, record:**

| Category / field | Meaning | Reporting discipline |
|---|---|---|
| `STATED_CORRECT` | Explicit source-supported equivalent statement | Semantics/entity binding matter, not string match |
| `STATED_INCORRECT` | Explicit contradiction of source-validated fact | Preserve exact wrong value/relation |
| `MISBOUND` | Potentially correct value assigned to incorrect entity | Track as special incorrect class, not simultaneous correct |
| `NOT_STATED` | No sufficiently explicit identifiable trace statement | **Never label “not acquired”** |
| `VAGUE_OR_UNMATCHABLE` | Ambiguous claim; cannot adjudicate source relation | Report separately from correctness |
| `CONTRADICTED_OR_UNSTABLE` | Multiple incompatible claims over time | Preserve chronological events and final-use state |
| `CORRECTED_LATER` | Initially wrong visual claim later replaced by source-consistent one | Requires explicit before-and-after spans; final downstream use separate |
| `DERIVED_FACT_ERROR` | Mathematical inference/calculation error using identified premises | Do not count as visual readout error by default |
| `UNSUPPORTED_VISUAL_ASSUMPTION` | Confident claim beyond source markings/available info | May be recorded outside required `E*` atoms |
| `SOURCE_UNCERTAIN` | No source-grounded adjudication possible | Withhold from correctness denominator |

Each row must additionally carry: `first_claim_state`, `last_claim_state`, `used_premise_state`, `is_ever_correct`, `is_ever_wrong`, `first_use_offset`, `is_self_revised`, `revision_direction`, `final_answer_outcome_metadata`, `evidence_source_QC`, `annotator_id`, and `adjudication_status`.

**Do not collapse all history into one correctness bit.** A Thinking trace that says `AB=5` then corrects to `AB=3` differs from a trace that never made the initial error; likewise a correction that is **not subsequently used** differs from a successful handoff.

### 4.3 Evidence-type taxonomy: freeze after pilot

Suggested nonexclusive domains: `scalar_label`, `entity_binding`, `spatial_relation`, `diagram_topology`, `diagram_convention`, `structured_layout`, `table_or_graph`, `unsupported_assumption`; retain original Stage14A primary atom family (`structured` vs `scalar`) for traceability. A structured atom may be split into independently meaningful, source-checkable **subfacts** by a rubric established **from source**, not selectively split because a model made a mistake. Maintain parent/child IDs to prevent double counting.

### 4.4 Trace event chronology

For each focal evidence atom/subfact, identify **observable text offsets**:

- `t_demand`: first explicit statement of needing the fact for a subgoal (can be absent);
- `t_claim`: first explicit statement about that visual fact;
- `t_use`: first identifiable **deduction/calculation relying on** that fact;
- `t_revision`: first later explicit change (if any);
- `t_use_after_revision`: whether the corrected fact was actually incorporated into downstream reasoning;
- `t_answer`: final answer boundary.

`first evidence divergence` means **first source-inconsistent *observable* visual claim or its first source-inconsistent use**, not necessarily the model's true first internal error. A missing explicit claim is `NOT_STATED` and does not have a fabricated timestamp. Distinguish self-described reinspection (`"look again"`) from verified image-conditioned retrieval (not established in D0).

### 4.5 Minimal machine-readable records (schematic, NOT observed data)

```json
{
  "family_id": "EXAMPLE_ONLY",
  "source_image_sha256": "<existing_hash>",
  "e_star_version": "<frozen_version>",
  "atom_id": "E7",
  "subfact_id": "E7.entity_AB_length",
  "source_fact": {"entity": "AB", "relation": "length", "value": "3"},
  "source_validity": "source_checked",
  "model": "Thinking",
  "condition": "T_IMG",
  "first_claim": {"value": "5", "state": "STATED_INCORRECT", "start": 104},
  "revision": {"value": "3", "state": "CORRECTED_LATER", "start": 311},
  "used_premise": {"value": "3", "state": "STATED_CORRECT", "start": 400},
  "native_outcome": "CORRECT",
  "e_star_outcome_metadata": "CORRECT",
  "trace_text_span_ids": ["raw-104-121", "raw-311-331", "raw-400-421"],
  "annotator_id": "reviewer_A",
  "annotation_status": "ADJUDICATED"
}
```

Examples in this document are invented **schema examples**, not Stage14B observed cases. Raw text never needs to be embedded in summary tables if provenance pointers can retrieve it.

### 4.6 Annotation reliability and source fidelity

- Pilot: **double-annotate** all or a prespecified meaningful subset with independent human reviewers where available; explicitly report number of reviewers and independence. If one reviewer or AI-assisted annotation is used, say so; do not imply independent validation.
- Report agreement for *claims identified*, *atom matching*, *incorrect vs correct*, *misbinding*, *not-stated*, and *self-correction*, plus adjudication examples; keep raw disagreement ledger. No agreement statistic can compensate for unreliable `E*` or biased model-output sampling.
- Source QA: validate referenced `E*` item against image/question before judging model errors. Mark model statements that contradict a questionable `E*` as `SOURCE_UNCERTAIN` pending review; never silently rewrite historical source evidence.
- Audit all quoted illustrative cases by independent source review where feasible. Preserve source/provenance for eventual reproduction and human-checkable viewer.

---

## 5. Six prespecified core analyses (A–F)

### A — Evidence-type error taxonomy: **what is visibly wrong?**

**Question:** Are most explicitly incorrect source facts scalar values, entity bindings, spatial relations, structural/topological facts, visual convention interpretations, or unsupported visual assumptions?

**Outputs:** per-type `STATED_CORRECT`, `STATED_INCORRECT`, `MISBOUND`, `NOT_STATED`, `VAGUE`, `SOURCE_UNCERTAIN`, `CORRECT_AND_USED`, `WRONG_AND_USED` rates for I and T; counts and denominators at both required-atom and source-checkable-subfact levels. Record unsupported claims separately even when not one of the predefined `E*` atoms. Include per-family aggregates and confidence intervals that cluster by family. **Do not equate prevalence among explicitly asserted facts with prevalence among all required facts.**

**C3 implication:** scalar errors → local high-resolution reading; binding errors → entity-aware grounding; global structure → full+local view; unsupported assumptions → visual claim verification.

### B — Paired I/T overlap: **do they get the same evidence wrong?**

**Question:** For the **same family/atom**, are I and T both explicitly correct, I wrong / T correct, I correct / T wrong, or both explicitly wrong? When both wrong, do they assert the **same incorrect value/relation** or different ones?

**Outputs:** paired matrix with **`NOT_STATED`, `VAGUE`, and `SOURCE_UNCERTAIN` as explicit non-error categories**; model gap in explicitly incorrect-claim rate *among both-asserted atoms*; all-required-atom explicit-correct coverage as a **separate estimand**. Control for unequal I/T trace lengths using opportunity/mention-rate measures and report model-specific missingness. Family-cluster paired uncertainty.

**C3 implication:** shared failure class vs variant-specific error correction; do not conclude Thinking “perceives better” merely because its trace is longer.

### C — First incorrect visual claim and propagation: **where does observable failure start?**

**Question:** Relative to each trace's written subgoals, when does it first assert a wrong source fact, **first use** that wrong fact in reasoning, and optionally revise it? Is a wrong visual premise actually connected to final error, or is it abandoned?

**Outputs:** trace timelines and counts of `incorrect_claim_only`, `incorrect_claim_used`, `used_then_revised`, `corrected_and_used`, `corrected_but_not_used`, `explicit_facts_correct_but_math_wrong`, and `no_identifiable_visual_premise_error`. Events ordered by raw offsets; missing events treated as unobserved, not time zero. Use length-normalized offsets **only as supplementary display**, not a shared cognitive time scale.

**C3 implication:** intervention trigger *at evidence-demand*, *before premise use*, or *at conflict/failed verification*; select based on observed propagation points.

### D — Thinking and Instruct self-correction: **which wrong facts become correct?**

**Question:** For an **initially explicitly wrong** visual claim, what fraction is later accurately revised, and is the corrected value used in downstream reasoning? What text-visible statements precede revision (contradiction, uncertainty, new subgoal, arithmetic check, self-declared reinspection)?

**Outputs:** model-specific `P(corrected later | initially incorrect explicit claim)`, `P(corrected and used | initially incorrect claim)` by evidence type; distinguish `wrong→correct`, `wrong→different wrong`, `correct→wrong`, `correct→correct reaffirmed`. Report raw spans and whether direct visual reaccess is **unverified**. Use family-cluster uncertainty and avoid comparing absolute counts without error-opportunity denominators.

**C3 implication:** determine whether targeted evidence-state revision, selective rollback, or explicit verification seems feasible. A text claim of “checking the image again” is **not** retrieval proof.

### E — Correct evidence but incorrect use: **what would reacquisition fail to fix?**

**Question:** How often does a failing model explicitly state the relevant `E*` fact accurately and still misbind, contradict, misuse, misderive, or miscalculate? Are required facts only partially explicit, making inference impossible?

**Outputs:** `correct_and_used`, `correct_but_misused`, `correct_but_unused`, `evidence_correct_and_math_error`, `missing_or_unobservable_fact`, `unsupported_assumption`, `cannot_assign_stage`. Keep direct observed evidence distinct from **math-derived** values. Show selected negative cases to prevent an acquisition-only post hoc narrative.

**C3 implication:** decide whether method must include **evidence integration, state revision, or downstream premise-use verification** instead of only crop/zoom.

### F — Evidence-error association with archived `E*` rescue: **which error patterns co-occur with supply responsiveness?**

**Question:** Among native wrong outputs, are explicit source-evidence errors more frequent in **native wrong → `E*` correct** than in **native wrong → `E*` wrong**, for I and T separately? What about **native correct → `E*` wrong regressions**?

**Outputs:** conditional, *descriptive* family-level tables using **score metadata only** from E* arms; stratify by source evidence type, native model, panel, source-QC status, answer-scoreability; report complete scored denominators and missingness. Use paired/family-cluster CIs and **do not infer mediation from trace comparisons**. Note that evidence rescue can arise through textual format/binding/attention/representation as well as genuine acquisition.

**C3 implication:** identify enriched candidates for **future causal repair** rather than claim demonstrated pure visual acquisition failure.

---

## 6. Prespecified tables, figures, and statistical protocol

### Figure/table package (five main analysis displays)

1. **Figure 1 — Evidence error taxonomy (I/T):** by scalar, binding, relation, topology, conventions, structured vs scalar parent; report per-type source-atom denominator, explicit-claim denominator, and `NOT_STATED` separately. **No invented plots or illustrative values in final research report.**
2. **Figure 2 — Paired I/T error matrix:** `both correct`, `I-only wrong`, `T-only wrong`, `both wrong same`, `both wrong different`, `one/both unstated`, `ambiguous/source uncertain`; show raw n and restricted pair denominator.
3. **Figure 3 — First evidence divergence and propagation:** event trajectories `demand → first claim → first use → revision → final` for annotated evidence, with unsuccessful/successful case snippets anchored to raw spans.
4. **Figure 4 — Self-correction:** initial wrong fact → source-consistent revision → incorporation into downstream work; I/T contrasted **among initial errors**, with type and token-length context.
5. **Figure 5 — Evidence errors × `E*` outcome:** model-specific `native-wrong/E*-correct` vs `native-wrong/E*-wrong` vs regression strata with clear sample selection and scoreable denominators.

### Calculation rules

- **Family** is the sampling/uncertainty unit. Multiple atoms/subfacts per family are **nested**, not independent replications. Use family-cluster bootstrap (paired IDs) for descriptive intervals; raw count/rate tables alongside CIs.
- **Panel R** may support source-eligible-cohort prevalence estimates **only if selection probabilities and native trace availability are documented**. Apply design weights if unequal source sampling is known; otherwise report cohort-conditional estimates. **Panel F** is outcome-enriched and **never** used as unweighted prevalence evidence for the source cohort.
- Avoid treating one model's silent evidence state as an error when the other model verbalizes an explicit source fact. Report (a) explicit-correct among required facts, (b) incorrect among assertable/explicit facts, (c) unobserved/unstated, **separately**.
- Correct/wrong answer statuses are carried from existing Stage14B archived scoring; preserve different scored denominators and explicit `UNSCORABLE`/missingness.
- If multiple evidence errors occur in one family, report both **per-atom counts** and **fraction of families with ≥1 explicit incorrect source fact**. `first` chronology must be trace text order, not a claim that the underlying internal error happened at that step.
- Sensitivity: exclude source-QC uncertain records; restrict to I/T both native scoreable; restrict to direct visual atoms only; structured vs scalar; R-only vs F-only; first/last/used-premise states; alternative treatment of `VAGUE_OR_UNMATCHABLE`. All comparisons described as retrospective/exploratory unless registered and frozen before annotation.

---

## 7. Concrete run plan, stops, and review gates

| Phase | Permitted work | Deliverable | STOP / gate |
|---|---|---|---|
| **D0-A: Inventory** | Read-only discover Stage14A/14B & old D prep, hash artifacts, exact joins, quantify 414 coverage and raw 2-arm availability | `input_inventory.md`, full `family_arm_manifest`, preservation receipts | STOP for missing critical refs, silent model/seed mismatch, or unresolved provenance |
| **D0-B: Pilot 30–50** | In-team manual Pass A/Pass B, source-QC check, hard-case adjudication, renderer prototype | `pilot_casebook`, disagreement ledger, frozen atom/event rubric | Freeze before broadened analysis; if claims not reliably extractable, revise rubric before continuing |
| **D0-C: Cohort freeze** | Reuse prior 300 where valid; construct R/F if feasible, record actual source selection/coverage and exact IDs | `sampling_manifest`, no duplicate IDs, exclusion reasons | STOP if representative label unsupportable; proceed exploratory with accurate description only |
| **D0-D: ~300 audit** | Human source checks and native trace-to-atom alignment; only CPU deterministic tooling; produce paired matrices | `atom_annotations`, `event_ledger`, `I_T_pair_table` | Escalate source mismatch; no new model or GPU calls |
| **D0-E: Results** | Analyses A–F, five figures, case viewer, uncertainty/missingness report, method-action map | `trace_audit_results.md` + machine-readable outputs | Separate results from speculation; no causal repair claims |
| **D0-F: Formal review** | Propose **small Stage14D-1** targeted retrieval based on observed dominant errors | `stage14d1_bounded_feasibility_proposal.md` | **STOP before experiment execution; new explicit user approval required** |

**Future D1 proposal only, not executed here:** nominate top one or two source-supported error classes, specify *fact-targeting prompts without oracle fact values*, targeted/global-plus-crop versus generic lookback versus matched rethinking and irrelevant/no-image controls, evidence-correctness and answer-correctness separately, model-regression risk, precise cost, and **new approval**. Valid semantic counterfactual evidence is required to run semantic-counterfactual assays; since none is currently available, those assays stay absent unless independently validated later. Do not reuse the old 1,674 continuations by default.

---

## 8. Required artifacts in the operator repository

**Do not create files in the operator's repository merely by reading this document.** Recommended **new namespace**, with old artifacts preserved:

```text
plan/
  stage14d_causal_evidence_acquisition_localization_plan.md     # archived old plan; unchanged
  stage14d0_estar_instruct_thinking_native_trace_audit_plan.md # this v2 scope

outputs/stage14d0/
  spec/
    scope_and_hold_status.md
    annotation_rubric_frozen.md
    analysis_estimands_and_denominators.md
  inventory/
    source_and_raw_output_manifest.jsonl
    old_300_414_1674_reuse_map.csv
    source_QC_and_Estar_version_ledger.jsonl
    provenance_sha256.json
    availability_missingness_report.md
  samples/
    pilot_30_50_families.jsonl
    panel_R_source_selected.jsonl
    panel_F_outcome_enriched.jsonl
    selected_300_distinct_ids_and_seed.json
  annotations/
    passA_native_claims_blinded.jsonl
    passB_Estar_atom_alignment.jsonl
    event_chronology_and_self_correction.jsonl
    adjudication_and_disagreement_ledger.jsonl
  analysis/
    evidence_type_by_model.csv
    paired_atom_I_T_error_matrix.csv
    same_wrong_vs_different_wrong.csv
    first_error_and_propagation.csv
    self_correction_initial_error_denominators.csv
    correct_evidence_wrong_reasoning.csv
    error_by_Estar_rescue_outcome.csv
    cluster_bootstrap_and_sensitivity.json
  viewer/
    index.html                              # local, source-linked; no external upload
  reports/
    stage14d0_inventory_and_reuse_review.md
    stage14d0_pilot_rubric_review.md
    stage14d0_native_trace_audit_results.md
    stage14d1_bounded_feasibility_proposal.md
    decision_and_unresolved_limitations.md
```

### Side-by-side viewer requirements

For each **family** show source image/question (authorized local path), canonical `E*` parent atom/subfact tree with source validity, **Instruct native reasoning**, **Thinking native reasoning**, and answer-status metadata. Color/underline source-supported matches, explicit mismatches, misbindings, missing-explicit claims, initial error/revision spans, and first use. Do not display `I_ESTAR` or `T_ESTAR` reasoning text in the default view or annotate them as primary traces. A collapsible metadata area can show archived native and `E*` correctness flags, without revealing the E* source answer inside Pass A extraction view. Support filters by evidence type, model error overlap, rescue stratum, initial wrong→revision, and source-QC state. Every assertion must link back to exact raw span and reviewer/adjudication provenance.

### Final audit report must explicitly state

1. **Count audited:** distinct images/families, native I/T trace coverage, actual paired n, reference atoms/subfacts, old 414 reuse counts, and missingness.
2. What the **pre-answer Instruct text** and **Thinking reasoning text** do and do not reveal, with model/recipe differences.
3. Evidence-type errors, shared-vs-specific errors, wrong-fact first use, self-corrections, correct-fact-but-wrong-use cases, and overlap with archived `E*` rescue.
4. Source `E*` fidelity/ambiguity; exact choice and limitations of population frame and sampling weights.
5. Competing explanations (visual readout error, binding/state formatting, downstream reasoning) and **why none is automatically causal from trace text**.
6. C3 decoding-method design requirements derived from verified patterns, and a small, separately approvable Stage14D-1 causal feasibility experiment.

---

## 9. Claim discipline / interpretation bounds

**The retrospective audit CAN support:**

- Source-anchored comparisons of **observable** native visual assertions at matched family/evidence-atom level in the two recorded variants.
- Evidence type and error classes; common/specific wrong claims; *observable* self-revision and downstream premise use.
- Descriptive association between native trace features and **archived `E*` supply responsiveness**.
- Evidence-driven priorities for C3 visual reacquisition / binding / verification / state-revision methods.

**It CANNOT by itself demonstrate:**

- `NOT_STATED` = no internal acquisition; no visible self-correction = no internal verification.
- A correct visual claim was read causally from the image rather than inferred from text/world knowledge.
- Two different pinned checkpoints/decoding recipes isolate the causal effect of “Thinking” at equal compute.
- An utterance such as “I will look again” means actual source-specific visual retrieval.
- Providing textual `E*` and successful rescue isolates visual readout from textual interface/representation/binding changes.
- Evidence-correction mediates outcome-correction, a universal C1 handoff, or a working C3 policy.
- The existing unexecuted semantic counterfactual assay found a null effect.

**Stop-and-revise conditions:** unreliable source `E*`; absent/mismatched raw traces; taxonomy fails to disambiguate visual source fact from calculated fact; annotation agreement too low to support mechanistic statements; I/T difference dominated by output contract rather than source fact fidelity; insufficient matched family coverage to estimate claimed paired statistic; high prevalence of source-correct-but-misused cases undermining an acquisition-only method. Report the problem plainly rather than force the prior hypothesis.

---

## 10. Operator-ready instruction (paste into Codex)

> **Stage14D main scientific continuations remain ON HOLD; do not approve 375 GPU-hours, do not launch any of the 1,674 sealed continuation inputs, and do not waive pending Stage14C-V closure.** Execute Stage14D-0 as an **existing-output/CPU/manual** retrospective **E* vs Instruct-native vs Thinking-native** trace audit, using frozen MATH-Vision 1,000 eligible source families. E* is the **source evidence reference, not a third model or trace**. For up to ~300 selected distinct families, compare at most **two primary native outputs per family** (max **~600 native traces**, actual n manifest-verified). Existing **414 two-pass-reviewed traces** are historical prep checks, not 414×3 outputs. Use already scored I_ESTAR and T_ESTAR **correctness/scoreability metadata only**; do not reread their reasoning in the primary audit. First inventory all joins/hashes and reuse old 300 source reviews; run a 30–50-family blinded-claim-extraction pilot; freeze a source-validated evidence-atom/subfact taxonomy; then annotate an approximately 150-family source-selected panel plus 150-family outcome-enriched panel **if actually feasible**. Carry out analyses A–F: evidence-type errors, paired I/T shared vs specific errors, first wrong fact and propagation, self-correction, correct evidence but wrong downstream use, and observable evidence error versus archived E* rescue. Preserve trace spans, model/seed/checkpoint provenance, source validity, missingness, true denominators, and annotator review. Produce five result displays, a local side-by-side viewer, and a **small** evidence-type-driven Stage14D-1 intervention proposal. **STOP before any scientific inference/GPU/LLM judge calls or causal continuations; separate user approval required.**

**This file is a research plan, not a budget or experiment-execution approval.**
