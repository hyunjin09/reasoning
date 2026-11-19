# Stage 14D — Causal Localization and Repair of Task-Critical Visual Evidence Acquisition

**Research execution plan — DRAFT FOR REVIEW / NOT AUTHORIZED TO RUN**  
**Paper emphasis:** C1 Functional evidence handoff → C2 Large evidence-supply-responsive bottleneck → **C3 Targeted visual evidence acquisition as a repair strategy (hypothesis).**  
**Primary domain:** MATH-Vision visual mathematical reasoning.  
**Primary checkpoint:** pinned Qwen3-VL-4B-Thinking.  
**Secondary checkpoint:** pinned Qwen3-VL-4B-Instruct, on a smaller fixed overlap panel.  
**Study type:** bounded *diagnostic* causal intervention, not a deployable controller or a new benchmark census.

> **Central question:** Can a VLM repair an incorrect answer by reacquiring a *specified missing task-critical visual fact from the original image*, without being told that fact's correct value? Is this more effective than generic rethinking or generic lookback?

---

## 0. Prior evidence, scientific motivation, and hard boundaries

### 0.1 What is already established

- **C1 — functional handoff.** Previous Stage 10 controlled fresh text-only replays yielded A0 **0/24**, A3 **19/24**, A4 **23/24** correct continuations. Counterfactual edits to emitted evidence text redirected downstream reasoning. This supports a *functional transition* from visual-access-dependent evidence resolution to text-sufficient continuation **in selected successful trajectories**, not universal disjoint computational phases or text as the unique internal carrier.
- **C2 — evidence-supply-responsive failures.** Sealed Stage 14B MATH-Vision `E*`-1,000: Instruct native-wrong → equal-evidence correct in **234/418 = 55.98%** of scored native-wrong follow-ups; 31 unresolved, identification bounds **52.12–59.02%** over 449 native-wrong families. Instruct net E*-supply effect on the eligible cohort was **+21.99 pp**. This shows *evidence supply is actionable*; it does **not** identify the fraction of failures due to pure visual misreading.
- **Post-evidence residual.** Paired Thinking–Instruct gap under the same image-free textual `Q + E*`: **+14.69 pp**, 95% CI **[+12.10,+17.39]**, with 926 complete pairs. Additional post-evidence difficulty remains. The Thinking/Instruct variants also differ in checkpoint and validated decoding recipe; do not claim a same-weights Thinking toggle.
- **Causal retrieval mechanism.** Prior controlled A→B→A experiments support reasoning-demand-conditioned *visual-semantic causal retargeting*; attention by itself is not retrieval. This is a motivation for an evidence-specific intervention, **not** proof that an inference-time prompt can cause new acquisition.
- **Task-selection boundary.** Stage 14C reproduced a math-versus-fine-grained-vision Thinking selectivity pattern already visible in Qwen3-VL reporting. BlindTest E* and R0/R1/R2 additionally showed large *text-interface sensitivity*. Do **not** treat those external-text interventions as established native acquisition or handoff failures. Stage 14D therefore stays on visual math, not BlindTest.

### 0.2 What must be established next

The Stage 14B oracle `E*` was **researcher/agent-authored textual evidence supplied in place of the image**. It is not the model's recovered evidence, hidden state, or Thinking trace. Consequently:

\[
\text{Native wrong}\to\text{correct under textual }E^*
\]

is an **evidence-supply-responsive** outcome, not a proven missing-acquisition event.

This stage must test a stronger sequence:

\[
\underbrace{\text{native failure}}_{\text{observed}}
\xrightarrow{\text{targeted image access; no fact value supplied}}
\underbrace{\text{correct task-critical evidence demonstrated}}_{\text{measured}}
\xrightarrow{\text{downstream continuation}}
\underbrace{\text{answer repair}}_{\text{measured}}.
\]

The key control is whether a targeted *image-directed* acquisition attempt improves evidence recovery/answers **beyond** more reasoning, generic visual prompting, and irrelevant target prompting. The stronger statement *fresh image evidence was causally accessed* additionally needs **source-specific visual-semantic intervention**, not merely a correct textual restatement.

### 0.3 Claim 3 remains a hypothesis

> **C3 candidate:** Targeting and verifying task-critical visual evidence can repair errors more effectively than indiscriminately extending reasoning or generic image lookback.

Stage 14D is **proof-of-principle / causal localization**. A practical, fully autonomous `identify → acquire → verify → handoff` method belongs to **Stage 14E**, and generalization/handoff integration belong to later stages.

---

## 1. Scope and cohort construction

### 1.1 Data source and immutable joins

Reuse only the **1,000 frozen MATH-Vision `E*` families** from Stage 14A, plus sealed Stage 14B native/equal-evidence outputs, IDs, original images, questions, golds, scoring outcomes, source annotations, alias groups, and raw reasoning traces.

Never rewrite original images, source evidence atoms, gold answers, native trajectories, parser decisions, or Stage 14B/14C estimates. Source and technical discrepancies discovered now must be recorded as **new audit findings** with versioned pointers; primary historical results stay intact.

Source evidence is an *evaluation reference*, not text to be injected into non-oracle intervention arms.

### 1.2 Primary bounded diagnostic cohort: 300 **families**, Thinking-defined

Freeze using sealed **Thinking** outcome strata (do not substitute Instruct rescue for Thinking rescue):

| Stratum | Condition on sealed Stage 14B Thinking outputs | Families | Role |
|---|---|---:|---|
| S1 — supply-responsive native failure | `T_img = wrong`, `T_E* = correct`, both scored | 100 | Main causal repair diagnostic |
| S2 — supply-resistant native failure | `T_img = wrong`, `T_E* = wrong`, both scored | 100 | Negative/mixed-bottleneck control |
| S3 — native-correct | `T_img = correct`, scored; record E* state separately | 100 | Harm/regression and unnecessary-relook control |
| **Total** | Distinct conservative families | **300** | Outcome-stratified diagnostic panel |

The sealed Stage 14C math transition table reports approximately **306** eligible Thinking wrong→E*-correct and **110** wrong→E*-wrong complete pairs, so the suggested 100/100/100 allocation appears viable. **Verify exact availability and sample identity in the original manifests before freezing.** If identity reconciliation changes eligible counts, stop and amend the proposed allocation **before new scientific model outcomes**; do not invent replacements.

Within each stratum:

1. Use a **frozen deterministic hash/seed** and source metadata balance for open-ended/MC, difficulty, subject, evidence type, evidence cardinality, and structured versus scalar atoms where feasible.
2. One family = one inferential unit. Do not sample conservative aliases as independent families.
3. Define a single **primary target fact/source object** per family by an explicit **source-only rule** before reading prospective intervention results. Example: first required atom by canonical frozen source order whose value is not already present in the nonvisual question. A structured atom may need a source-defined subfact (cell/edge/marked angle) and should be decomposed only with logged source-validity checks.
4. Carry forward *all* chosen families, including hard-to-anchor, ambiguous-readout, and intervention-inapplicable cases as explicit states. A source-invalidity exclusion may be made only under frozen objective rules and is **not silently replaced**.
5. Mark the cohort `OUTCOME_STRATIFIED_DIAGNOSTIC`; it is **not** a population-prevalence estimate or an independent confirmation of Stage 14B.

**Important:** Native Thinking has different failure modes from native Instruct. The headline **55.98%** is an **Instruct** conditional rescue rate, not the expected success rate or prevalence in this Thinking-selected 300.

### 1.3 Secondary Instruct overlap

Freeze **120 of the above 300 families**, exactly 40 from each S1/S2/S3 by the same deterministic selection procedure, for a matched-condition Instruct sensitivity. Keep their **Instruct-native and Instruct-E*** outcomes as separate recorded strata; do not imply Thinking-selected labels automatically characterize Instruct.

### 1.4 Future generalization panel — **not executed in 14D**

For a later claim of whole-benchmark *net* effect, a source-selected, outcome-unconditioned, prospectively frozen MATH-Vision sample will be needed (or new prospective intervention runs on all frozen E*-1,000). Reserve its selection rule in documentation now but **do not** run it or describe results from S1/S2/S3 as benchmark-wide improvement.

---

## 2. Critical scientific validation gates

**G0 — User approval / prerequisites:** Require explicit approval of the frozen 14D specification, scientific-call ceiling, GPU-hour hard ceiling, and outputs. Stage 14C-V's separate C panel/final closure must be documented as completed or explicitly waived by the user before launching a new main stage. Creating this plan does not authorize compute.

**G1 — Source/fact validity:** Before evaluating interventions, validate each selected original image, question, target identity/ROI, answer-safe `E*` provenance and gold relationship. Independent image/source reroutes are preferable for a small expert QC sample. Preserve ambiguity and answer-leakage flags; a source-derived fact that gives away the answer cannot be used in a targeted prompt as an oracle. Use the frozen `E*` values for **scoring only**, not for choosing favorable text after looking at outputs.

**G2 — Native trace and anchor feasibility:** Read/annotate original native trajectories. Confirm exact model/processor/config identity, output/token boundaries and whether there is a **pre-explicit-evidence**, source-neutral intervention prefix. Freeze anchors *before* new intervention results. A wrong answer without explicit evidence cannot be labeled a proven visual misread.

**G3 — Technical preflight:** Up to **24 tiny technical calls** to validate prefix continuation identity, image availability, attention-mask backend behavior if used, prompt rendering, generation output contracts, raw trace preservation, scoring, and deterministic replay in a fixed context. Use a non-primary technical set. Preflight is not a tuning phase. If backend or prompt identity differs from specified conditions, **STOP**.

**G4 — Preregistered scientific launch:** Lock cohort, target selectors, anchors, interventions, analysis code, review rules, call and GPU ceilings, seeds, and hashes. Scientific output inspection cannot change the specification.

**G5 — Main and causal control completion:** Finish fixed primary conditions and, if technically valid, bounded source-specific interventions. If matched visual semantic edits fail validity, report them as **not executed/invalid**, not a negative result.

**G6 — Primary-only sealing:** Seal primary outcomes, uncertainty, missingness, and paired transitions **before** narrative subgroup/trace interpretation and qualitative examples. Then run secondary/causal diagnostics, produce a final report and STOP.

---

## 3. How to locate evidence events in the native trace

For each family, record for the **primary task-critical source unit**:

- `E0`: first naming/identification of the target visual entity (if any);
- `E1`: first position where the full task-critical fact is explicit in generated text (if any);
- `E2`: first downstream reasoning step that uses the fact (if any);
- repeated/contradictory mentions;
- `PRE-E1`, `E0–E1`, `POST-E1`, and `USE` regions;
- whether target evidence is **correct, incorrect, contradictory/unstable, partial, not demonstrated, or unreadable/unscorable** in the *observable generated trace*.

**Do not equate:**

- `not stated` with `not internally acquired`;
- a wrong final answer with an evidence misread;
- a fact mentioned after E1 with *fresh* image acquisition;
- high ROI attention with semantic retrieval.

### 3.1 Anchor selection and timing

The primary anchor should be the **latest source-neutral prefix just before the first evidence-bearing commitment for the selected target**. This allows an intervention before a suspected misread propagates into arithmetic. The exact token index, original prefix bytes/hash, original semantics, and E0/E1/E2 timing must be logged.

If no explicit mention exists, use a preregistered **early evidence-neutral anchor** (e.g., immediately before generation or first pre-evidence reasoning block) under a deterministic fallback policy; mark the fallback. Do not select a later prefix based on the success of a new intervention. Exclude from *pre-acquisition causal timing* analyses if the prefix already contains the answer-critical fact, but preserve in the overall diagnostic cohort.

A separate **post-incorrect-fact correction** analysis may be run on clearly wrong-fact examples as secondary only. It tests *repairing a committed text state* rather than initial acquisition and must not be pooled with the pre-fact assay.

### 3.2 Structured evidence limitation

Many Stage 14A E* families contain one or more structured atoms. A vague instruction such as “recheck the whole grid” and a specific instruction “read cell (row r, column c)” are not equivalent. Require exact target identity, image localization and a non-answer-leaking request. If a coherent object cannot be reduced to one defensible target fact, mark `STRUCTURED_COMPLEX` and report separately, not as a wrong scalar fact.

---

## 4. Main intervention panel — same image, same checkpoint, same prefix

For every eligible 14D family, **fork from the exact same frozen native prefix and the same original image** into the following **five preregistered** arms. All arms are fresh controlled continuations; original sealed native output is a contextual reference rather than a perfectly matched replay control.

| Code | Arm | Action | Purpose |
|---|---|---|---|
| `B0` | No intervention | Continue from exact frozen prefix without new directive | Matched-prefix baseline / natural replay variability |
| `THINK_MORE` | Generic reasoning / verification | Prompt to reconsider/check the solution without naming a visual fact | Extra deliberation control |
| `LOOK_GENERIC` | Generic image lookback | Ask to inspect the original image again for relevant details | Is generic reinspection enough? |
| `LOOK_TARGET` | **Target-specific lookback** | Identify which visual entity/quantity/relation to re-read; **do not supply its value** | Main causal repair candidate |
| `LOOK_IRRELEVANT` | Irrelevant source control | Direct inspection to an available, irrelevant source object matched as closely as possible for salience/format | Specificity and prompt-content control |

**Illustrative prompt only, not a frozen literal template:** “Re-examine the segment labeled AB in the original figure. Read its marked length directly from the image; do not assume or infer a value from your previous answer. Then continue solving.” The instruction **cannot contain `AB = 3`** if `3` is the frozen ground-truth visual value.

### 4.1 Fairness rules

- Use the **same pinned checkpoint** for within-model causal comparisons. Thinking is primary; the exact same panel is run on the 120 Instruct overlap families.
- Use the identical original image and target problem, unchanged native question/options, output format, tokenizer, BF16, model revision, backend and existing validated native decoding recipe *within each checkpoint*. Do not make Instruct-vs-Thinking causality claims.
- Keep prompt packaging as similar as possible across `THINK_MORE`, `LOOK_GENERIC`, `LOOK_TARGET`, `LOOK_IRRELEVANT`; preregister exact strings, target fields, insertion timing, and text lengths. Report differences in prompt specificity and token counts. The five arms cannot be described as strictly equal-compute merely because max-token caps match.
- Use matched seed families, fixed generation ceilings, fixed stop handling, and retain both actual output tokens and timing/GPU information.
- No oracle evidence value, inferred answer, mathematically derived step, alternative solution, or true intersection/length/angle count may enter **any** non-oracle intervention input.
- If no defensible irrelevant ROI/source is present, mark `IRRELEVANT_CONTROL_INAPPLICABLE`; do not invent a new image feature or quietly substitute random text.
- Long reasoning, repetition, parser ambiguity, normal-stop refusal and cap hits must be distinguished. Preserve every raw completion before scoring.
- A prompting effect can alter reasoning without acquiring information from the image; final-answer rescue alone is not proof of image re-access.

### 4.2 Oracle positive control — contextual, not a method

Existing `T_E*` and `I_E*` full-problem runs are an **oracle supply reference**, not a matched-prefix acquisition arm. Optionally propose a *small, separately approved* same-prefix oracle-value injection as a diagnostic positive control, with a new fixed evidence interface and all resultant representation confounds explicitly disclosed. Do **not** include it in the main `LOOK_TARGET` estimator or count it as model-acquired evidence.

### 4.3 Handoff claim reserved

Successful final answers after `LOOK_TARGET` are **not yet evidence** that a new image-free text-sufficient handoff occurred. Replaying the resulting prefix without image/hidden states is a later Stage 14F mechanistic integration, except for a tiny separately approved technical demonstration clearly labeled exploratory.

---

## 5. Causal visual-content validation (nested, bounded)

A target-specific prompt and a correct stated fact do not establish *fresh image retrieval*. For stronger evidence, select up to **48 source-valid, localizable families** by a preregistered **source-only** rule from the 300 before looking at new arm outcomes. Preserve all eligibility failures and screening receipts.

At the **same frozen prefix** (before first explicit fact), probe:

1. **`IMG_ON`:** unmodified image, targeted continuation or fixed next-evidence readout.
2. **`IMG_OFF_FUTURE`:** block only *future generated-query → image-token* access after the fixed prefix using the validated backend; multimodal prefill/prior K/V remain, so this is **not** a no-visual-information condition.
3. **`IMG_CF_SEMANTIC`:** where feasible, alter only the target visual **semantic fact** in a matched image (e.g., marked AB length 3↔5) while holding other layout/source identities constant; validate target directional answer/readout expectations independently. Prefer preexisting carefully validated same-layout counterfactuals over ad hoc uncontrolled image edits.
4. **`IRRELEVANT_SOURCE_CF`:** matched edit or masking of a task-irrelevant source if a valid control exists.

**High-confidence local indicator:** target-specific upcoming evidence/readout tracks `IMG_CF_SEMANTIC` *directionally*, while irrelevant edits do not, with access/timing validity. Global next-token perplexity or attention changes alone are not adequate evidence of semantic retrieval.

**Interpretation limits:** This establishes source-specific semantic *causal influence / steerability*. To claim *fresh acquisition after the anchor*, also account for prior prefill/hidden carriers, first explicit fact timing and control placement. Semantic sensitivity does not automatically imply native-path necessity or full answer-level causal mediation.

If no trustworthy semantic edit can be made without changing other relevant facts or leaking the answer, **do not fabricate one**. Report smaller achieved valid N and describe the mechanism claim as limited accordingly.

---

## 6. Readouts: evidence recovery must be measured separately from final accuracy

### 6.1 Primary observable answer endpoint

For each arm/family, score **final-answer correctness** under the frozen Stage 14B numerical equivalence/terminal-answer review policy. Preserve `CORRECT`, `WRONG`, `UNSCORABLE`, `TECHNICAL_MISSING` separately. Record pair completeness and the full N→C, C→N, C→C, N→N transition table.

### 6.2 Observable evidence-state endpoint

Blind to downstream gold success wherever operationally possible, annotate for the preregistered target visual fact:

- `EXPLICIT_CORRECT`
- `EXPLICIT_INCORRECT`
- `PARTIAL_OR_APPROXIMATE`
- `CONTRADICTORY`
- `NOT_DEMONSTRATED`
- `UNSCORABLE`

Label *what is written*, not what the model invisibly knows. Only source-validated factual units count as exact evidence. Report the raw snippets and E0/E1/E2 locations, including failure to verbalize a fact.

A standardized, **separate evidence-elicitation readout** may be used on matched frozen states in a strictly limited diagnostic branch; it must be labeled `ELICITED`, not conflated with native generated evidence or automatically called recovered from the current image. Ensure answer-only system instructions do not silently nullify the elicitation command (the Stage 14C-V BlindTest D1 issue).

### 6.3 Stronger local semantic endpoint

For the ≤48 nested source-validated counterfactual families, measure the **direction and magnitude** of evidence-token/logit/readout change as the single target visual fact changes. Include same-prefix, same-template and irrelevant-source controls. This is the primary mechanistic assay, not high aggregate attention.

### 6.4 Do not infer mediation from association

If a repaired fact and correct answer co-occur, that does not by itself prove evidence correction mediated the improvement. A later matched **fact-edit / carrier intervention** can establish whether a specifically changed fact causally changes downstream reasoning; if added, freeze it as a separate optional assay rather than retroactively calling the co-occurrence proof of mediation.

---

## 7. Preregistered hypotheses and estimands

### P1 — Target-specific answer repair among S1 (primary)

\[
\Delta_{\rm repair}^{S1}
= Acc(\mathrm{LOOK\_TARGET}\mid S1)
-Acc(\mathrm{LOOK\_GENERIC}\mid S1).
\]

Use **paired same-family complete scored continuations** as the main estimate; also report missingness bounds on all 100 planned S1 families. Compare to `THINK_MORE` and `B0` as prespecified **secondary** contrasts. A positive P1 shows a target-specific prompt advantage *in a diagnostic, supply-responsive stratum*, not a general deployed gain.

### P2 — Observable target-evidence correction (co-primary mechanism endpoint)

\[
\Delta_{\rm evidence}^{S1}
= P(\texttt{EXPLICIT\_CORRECT}\mid\mathrm{LOOK\_TARGET},S1)
-P(\texttt{EXPLICIT\_CORRECT}\mid\mathrm{LOOK\_GENERIC},S1).
\]

Always accompany this with `NOT_DEMONSTRATED` and contradiction rates. Elicitation differences may partially reflect prompting style, so **P2 alone does not prove fresh image acquisition**. The nested controlled visual-semantic probe supplies complementary source-specific evidence.

### P3 — Correctness regression / harm among S3 (safety)

\[
H_{S3}=P(\mathrm{wrong}\mid\mathrm{LOOK\_TARGET},S3)
-P(\mathrm{wrong}\mid\mathrm{B0},S3).
\]

Report target versus generic lookback as a further planned control. Do not call the method beneficial if rescue is accompanied by large harm to already-correct cases.

### P4 — Specificity and source-semantic dependence (bounded mechanistic assay)

Among valid counterfactual cases, measure directional target-semantic response versus irrelevant edit, plus any matching direct-visual-access knockout contrast. **Declare a source-specific retrieval result only if semantic controls and timing validity pass**; otherwise report descriptive prompting effects.

### Secondary analyses

- S1/S2/S3 full outcome and evidence-state transition matrices, with denominators and unresolved bounds;
- model-specific comparison on the fixed 120 Instruct overlap;
- scalar versus structured evidence, difficulty, question format, subject, first versus repeated evidence mentions, source alias groups;
- total output tokens, latency, prefill/decode metrics, estimated compute usage (report only instrumented quantities; do not invent peak device VRAM);
- extent to which generic thinking / generic lookback repairs evidence relative to `LOOK_TARGET`;
- correct evidence but wrong answer, and wrong evidence but correct answer;
- anchor position / fallback / post-fact status, with prespecified strata labels.

---

## 8. Statistical design and success/failure logic

- **Inference unit:** conservative family. Never treat repeated conditions, steps, ROI pixels, answers or token readouts as independent families.
- **Uncertainty:** 10,000 paired family-bootstrap draws under a newly frozen Stage 14D seed; report unadjusted 95% CIs explicitly. Before execution choose a prespecified correction for the **two primary P1/P2 claims** (e.g., Holm control for corresponding tests) if making a familywise-significance statement. Do not invent familywise significance from unadjusted CIs.
- **Missingness:** distinguish scoreable wrong, unscorable, cap before outcome and genuine technical failure. Report complete-pair denominators and worst/best bounds over planned families. Technical-incomplete cases are never silently counted wrong.
- **Power:** 100 S1 families are a *bounded mechanism/feasibility pilot*, not guaranteed power for small effects. Estimate minimum detectable effect from **frozen baseline paired disagreement assumptions** in a planning memo before execution; do not interpret inconclusive CI as proof of no effect.
- **Randomization/ordering:** use frozen per-family seeds, balanced condition order, and job-independent output identities. Do not choose a best seed, decoding temperature or prompt after seeing outcomes.
- **Multiplicity/selection:** observational patterns from previous Stage 14B strata are **not** fresh held-out confirmation; the new causal intervention assignment/conditions, once frozen, are prospective. Report preselected and achieved N separately.
- **Reviews:** blinded response-only reviews to the extent feasible (at minimum hide condition IDs, gold and downstream outcomes for evidence annotations). If review is performed by the same agent, disclose lack of independent inter-rater reliability. A small human-audited subset would strengthen source fidelity if available, but do not claim it occurred unless documented.

### Decision matrix

| Observed result | What it would support | What it would **not** support |
|---|---|---|
| Targeted lookback improves both correct evidence statements and answers; relevant semantic CF changes readout directionally | Target-specific source information contributes to repair in tested cases | Universal acquisition mechanism, complete mediation, benchmark-wide method gain |
| Targeted prompting improves answers but not evidence recovery / no content-specific sensitivity | Reasoning-path/prompt effect possible | `Improved visual acquisition` as the cause |
| Correct evidence recovery increases but answers do not improve | Downstream limitation is material | Acquisition alone sufficient |
| Generic lookback ≈ targeted lookback | Targeting has no demonstrated extra advantage under this assay | Targeting impossible or useless universally |
| S3 previously-correct cases regress markedly | Overuse of reacquisition is harmful; need selective activation | Evidence-first is safe without a controller |
| Source-semantic edit/control invalid or backend fails | Mechanistic assay invalid / technically blocked | Scientific null |

**Explicit continuation/kill gates:** If P1 is nonpositive or P2 lacks interpretable evidence correction, do **not** automatically advance to Stage 14E as a claimed evidence-acquisition method. Audit technical/prompt issues, report the negative finding, and seek separate approval for a revised hypothesis. If source-specific image-semantic sensitivity fails despite clean controls, downgrade to a behavioral prompt-repair interpretation.

---

## 9. Call inventory, resource gates, and execution order

This is a **proposed** bound, not authorization or a GPU-hour estimate.

| Scientific block | Approximate fresh calls |
|---|---:|
| Thinking main, 300 families × 5 matched arms | 1,500 continuations |
| Instruct secondary, 120 families × 5 arms | 600 continuations |
| Nested mechanism, ≤48 families, limited ON/OFF/CF matched continuations | ≤144 continuations |
| **Proposed max new scientific continuations** | **2,244** |
| Technical preflight | ≤24 additional calls |

Controlled short teacher-forced readouts, if necessary, must be separately counted and hard-capped **before** approval (proposed ceiling: **≤150 short readouts**). Do not double-count reused native baselines and do not execute optional full-problem oracle repeat runs under this inventory.

**Before G0 launch approval**, run a CPU-only planning dry run and obtain a GPU cost projection from a tiny technical benchmark; obtain explicit user approval for a **numeric GPU-hour hard ceiling** and concurrency. No guessed GPU-hour limit is encoded here. If the allocated ceiling would be exceeded, **STOP** rather than truncate scientific conditions after seeing outcomes.

Suggested execution:

1. **Source/identity and prerequisite closure:** Verify Stage 14C-V closure or explicit waiver; enumerate E* manifests; check exact family, alias and source ties.
2. **Cohort freeze:** 100 S1 + 100 S2 + 100 S3, plus 120 Instruct-overlap, deterministic primary target and source-only mechanism subset. Hash and sign receipts.
3. **Evidence annotation / anchor freeze:** Annotate native traces and E0/E1/E2; source-audit targets; freeze prefix byte/token indices; report anchor feasibility.
4. **G3 technical preflight:** Exact cache/backend/attention-mask validation and raw/scoring contracts; freeze cost ceiling; request user approval as specified.
5. **Five-arm main run:** Randomized/balanced condition order, saved raw outputs and immutable hashes; no primary-result-led reallocation.
6. **Scoring and primary-only seal:** Freeze response adjudication, evidence-state annotations, P1/P2/P3 and all denominators and uncertainty.
7. **Nested mechanism probe:** Run only the prospectively frozen valid images/ROIs; preserve exact original and CF sources; separately report achieved N and directional sensitivity.
8. **Secondary analysis and figure package:** Source QC, structured/scalar, model overlap, timing, cap/missingness, resource logs.
9. **Final gate/STOP:** Conclude what is established and what remains unknown; **do not automatically launch Stage 14E or 14F**.

If the user prefers to separate the mechanism assay from the main study for compute/risk reasons, label the ≤48-family block **14D-M**, freeze it upfront, and require a second explicit approval; do not use main effect sizes to select those cases.

---

## 10. Artifact and provenance requirements

Create an isolated, immutable namespace (do not overwrite Stages 10, 12, 13, 14A/B/C/C-V):

```text
outputs/stage14d/
  spec/
    stage14d_plan.md
    approved_scope_and_gates.json
    condition_templates_frozen.json
    pinned_model_revisions_and_recipes.json
    scoring_and_evidence_annotation_protocol.md
    statistical_analysis_spec.md
  cohorts/
    thinking_strata_300.jsonl
    instruct_overlap_120.jsonl
    target_source_annotations.jsonl
    mechanism_source_valid_48.jsonl
    exclusion_and_inapplicability_log.jsonl
  anchors/
    evidence_events_E0_E1_E2.jsonl
    prefix_identity_and_timing.jsonl
    source_ROI_identity.jsonl
  raw/
    continuations/
    readouts/
    controlled_visual_semantic_interventions/
  annotation/
    evidence_state_reviews.jsonl
    answer_extraction_reviews.jsonl
    source_fidelity_QC.jsonl
  analysis/
    prereg_primary_results.json
    paired_transitions.json
    evidence_recovery_outcomes.json
    source_specific_causal_sensitivity.json
    bootstrap_and_missingness_bounds.json
    secondary_sensitivities.json
  figures/
    figure1_design_and_evidence_timing.png
    figure2_answer_repair_by_arm.png
    figure3_target_evidence_recovery.png
    figure4_source_semantic_counterfactual.png
    figure5_native_correct_regression.png
  audit/
    immutable_source_hashes.json
    condition_identity_receipts.json
    technical_preflight_validation.json
    execution_completion_validation.json
    review_provenance.json
    gpu_resource_accounting.json
    artifact_catalog.json
  reports/
    stage14d_primary_only_summary.md
    stage14d_final_report.md
    next_stage_recommendation.md
```

Minimum figure contents:

1. Timing and controlled-prefix intervention schematic (distinguish prefix/image/supplied targets/true values).
2. Paired `LOOK_TARGET` vs `LOOK_GENERIC` and `THINK_MORE` answer repair in S1, plus S2 controls.
3. Observable correct-evidence vs wrong/unstated transitions, including counts (not only cherry-picked examples).
4. Directional target-versus-irrelevant source-semantic intervention, with achieved valid N.
5. S3 harmful regressions and net effects, separately from conditional rescue.

Every figure/table must identify whether it concerns Thinking or Instruct, source stratum, reused or fresh outputs, source validity, scoreable denominator, paired estimand, CI definition and model/recipe identity.

---

## 11. Interpretation discipline / paper-language gate

### If successful, supported (with relevant qualifiers)

> On a frozen, outcome-stratified visual-math diagnostic cohort, directing a model to reacquire a specific task-critical visual fact **from the original image**, without supplying its value, improves demonstrated evidence recovery and can repair downstream answers more often than generic lookback or generic additional reasoning. Local matched visual-semantic interventions provide source-specific causal support where validated.

### Not established by Stage 14D alone

- That every `E*`-rescued failure was caused by missing visual acquisition rather than representation/binding/other prompt changes.
- That correct self-generated evidence necessarily mediated every answer correction.
- That more image attention or a statement “I looked” proves fresh retrieval.
- That text is the sole/unique downstream representation.
- That arbitrary visual-math tasks or other checkpoints benefit without an autonomous target selector and verifier.
- That an adaptive policy is superior in equal compute without measured budget-matched comparisons.
- That Thinking's native/equal-evidence checkpoint difference is a same-weights reasoning-mode causal effect.
- That this targeted diagnostic sample yields a population-level intervention improvement.

### 14D → 14E/14F conditional bridge

- **14E (if positive):** Prospectively design and validate a **deployable** policy that predicts the missing target and checks whether it was resolved, without any oracle `E*` identity or value at inference. Compare against calibrated generic/uncertainty lookback and longer-thinking controls under measured compute budgets on a **fresh source-selected evaluation cohort**.
- **14F (if positive):** Examine whether successful reacquisition produces a verifiable `visual-dependent → fresh text-sufficient continuation` handoff, including text-prefix counterfactual edits and image-independent replay. This links repair directly to C1.
- **Generalization (later):** replicate across model sizes, external families and additional reasoning tasks. BlindTest text-geometry remains a separate source/interface stress case, not a causal stand-in for math evidence acquisition.

---

## 12. One-sentence objective and stopping rule

\[
\boxed{
\textbf{Determine whether targeted, source-specific reacquisition of visual evidence}
\textbf{ can causally repair native visual-math failures beyond generic thinking/lookback.}
}
\]

**Plan status: DRAFT ONLY. No models have been run, no cohort newly frozen, no GPU resources allocated. STOP pending user review and explicit authorization.**
