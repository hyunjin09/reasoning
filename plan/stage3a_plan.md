# Stage 3A Plan: Counterfactual Visual-Content Sensitivity

## 0. Purpose

Stage 3A is the first causal stage after the Stage 2 measurement audit.

Stages 2A–2C showed that ROI attention is strongly associated with the language currently being generated, but does not reliably identify when visual evidence is first acquired.

Stage 3A therefore replaces raw attention magnitude with a more direct causal question:

> **If the visual content of one localized fact is changed while the textual reasoning prefix is held fixed before the fact is first mentioned, does the model's subsequent computation move toward the counterfactual visual fact?**

The goal is to establish **visual-content sensitivity before explicit textual leakage**.

Stage 3A does **not** yet determine where the information is stored (V/Q/R), nor does it establish handoff, memory, or refresh.

---

## 1. Stage 2A–2C Handoff

### Stage 2A

Some examples showed apparent evidence-specific ROI-attention shifts. This was descriptive only.

### Stage 2B

Generated-query -> ROI attention edges were blocked during frozen reasoning windows.

Result:

- 0/5 strong A/B crossovers,
- 1/5 partial-specificity case.

However, Stage 2C later showed that 8/10 target Stage 2B intervention windows began after the corresponding visual fact was already explicit in the generated CoT.

Therefore Stage 2B mainly tested **direct visual re-access after explicit fact formation**, not initial evidence acquisition.

### Stage 2C

50 completed-correct examples and 70 evidence events were audited.

Key findings:

- 58/70 events (82.9%) were mention-centered.
- Only 3/70 were classified as pre-mention leads.
- FACT-region ROI density was about 2.3x PRE density.
- Later semantic references had higher ROI density than nearby matched text.
- All 30 newly screened events were mention-centered.
- Non-T2 patterns came entirely from the previously reused Stage 2A subset.
- The counterfactual-ready pool contained 38 evidence items across 26 examples, but only 18 unique underlying problems.
- Only one counterfactual-ready item was also a clean T1 pre-mention-lead case.

Interpretation:

> **Existing ROI attention is much more consistent with semantic/text–vision alignment around fact expression than with systematic pre-mention evidence acquisition.**

Therefore Stage 3A must **not select examples based on pre-mention attention peaks**.

---

## 2. Three Constraints From the Measurement Audit

### Constraint 1 — Strictly pre-E0 textual context

A future causal prefix must end **strictly before E0**, where E0 is the first explicit generated mention of the relevant entity/referent.

Using merely `pre-E1` is too loose because the model may already have generated partial evidence-related language.

Primary Stage 3A analysis must therefore avoid feeding:

- the entity name,
- the value,
- the relation,
- or any partial fact wording that begins at E0.

### Constraint 2 — Do not use ROI attention as evidence acquisition

Attention may reflect semantic similarity between the current textual state and a matching visual region.

Attention may be retained as a secondary descriptive signal only.

### Constraint 3 — Visual information may already have multiple carriers

A counterfactual visual effect may later be mediated through:

- V: visual-token representations,
- Q: prompt/question representations,
- R: generated reasoning representations.

Stage 3A should establish visual-content causality first.

Carrier tracing belongs to Stage 3B.

---

## 3. Main Research Question

For an original image \(I_o\) containing visual fact \(f_o\), create a minimally edited counterfactual image \(I_c\) containing fact \(f_c\).

Examples:

\[
AB=3 \rightarrow AB=5
\]

or:

\[
\text{bar value}=12 \rightarrow 18
\]

while preserving all unrelated image content.

Given an identical evidence-neutral reasoning prefix \(c_t\) ending strictly before E0:

> **Does changing only the visual fact from \(f_o\) to \(f_c\) causally shift the model's prediction toward \(f_c\)?**

This is stronger than asking whether the model attends to the corresponding ROI.

---

## 4. Primary Statistical Unit

The primary independent unit is:

> **base_problem_id**

Do not treat multiple evidence events from the same underlying problem as independent samples.

For the main analysis:

- choose one primary evidence item per base problem prospectively,
- or use a hierarchical analysis if multiple evidence items must be retained.

Prefer one primary event per base problem for interpretability.

Secondary within-problem events may be analyzed separately.

---

## 5. Scale

Previous stages often used 5–20 examples. Stage 3A should be materially larger.

### Target

> **40 unique base problems**

### Desired upper range

> **40–50 unique base problems if sufficient clean edits are available**

### Minimum interpretable cohort

> **30 unique base problems**

Do not lower edit-quality standards merely to hit the target.

The existing Stage 2C pool contains only 18 unique base problems, so additional curation is required.

---

## 6. Cohort Expansion

First screen all remaining completed-correct Stage 1B trajectories that were not already used in the Stage 2C counterfactual-ready pool.

Selection must be independent of ROI-attention timing category.

Select on:

1. localized visual fact,
2. correct completed reasoning,
3. strict pre-E0 evidence-neutral prefix exists,
4. fact can be counterfactually edited without changing unrelated content,
5. counterfactual remains semantically valid,
6. edit can be visually verified,
7. problem identity is unique for the primary cohort.

If the existing Stage 1B correct pool cannot provide at least 30 unique base problems, prospectively collect additional completed-correct MathVerse problems using the **same locked Stage 1 Thinking generation protocol**.

If additional inference is needed for cohort expansion:

- use previously unseen underlying MathVerse problems,
- preserve the same generation protocol,
- do not inspect attention to decide inclusion,
- stop collection once the target number of unique counterfactual-ready problems is reached.

---

## 7. Preferred Counterfactual Types

Prioritize edits that make a clean causal comparison possible.

### Tier 1 — Local numeric/text label changes

Examples:

- `3 -> 5`
- `12 -> 18`
- category label A -> B
- local chart/diagram text value change

These are preferred because the rest of the visual scene can remain identical.

### Tier 2 — Local symbolic relation changes

Examples:

- angle/marker/symbol edits,
- discrete annotation changes,

only when the edit is localized and unambiguous.

### Tier 3 — Structural visual edits

Examples:

- changing geometry,
- moving objects,
- changing topology.

Avoid these in the primary cohort unless a strong matched-control procedure is available, because they may alter many visual tokens and introduce large off-target effects.

---

## 8. Counterfactual Construction

For every primary problem produce:

- original image \(I_o\),
- counterfactual image \(I_c\),
- target evidence ROI,
- original fact \(f_o\),
- counterfactual fact \(f_c\),
- exact edit description.

Keep fixed:

- image dimensions,
- image crop,
- unrelated visual content,
- question text,
- prompt formatting,
- preprocessing settings.

Do not modify multiple task-relevant facts in the same primary edit.

---

## 9. Mandatory Edit Controls

Each counterfactual item should include at least:

### C0 — Original image

Unmodified source.

### C1 — Counterfactual target edit

Only the target fact changes from \(f_o\) to \(f_c\).

### C2 — Sham target-region edit

Re-render or reconstruct the same original fact \(f_o\) using the same edit pipeline used for C1, while preserving its semantics.

Purpose:

> control for visual artifacts caused merely by editing the ROI.

### C3 — Matched irrelevant edit

When feasible, perform a similarly sized local edit in a task-irrelevant region that does not change the target evidence.

Purpose:

> control for generic local image perturbation.

If C3 cannot be defined cleanly, document the reason.

C2 is strongly preferred and should not be omitted silently.

---

## 10. Manual Edit Validation

Every edited image must be manually inspected before inference.

For each item verify:

1. target fact has changed exactly as intended,
2. sham retains the original fact,
3. unrelated task-relevant content is unchanged,
4. text/number is legible,
5. no accidental occlusion was introduced,
6. image dimensions/preprocessing are unchanged,
7. counterfactual problem remains logically interpretable.

Use two-pass validation if practical:

- construction pass,
- independent review pass.

Reject ambiguous edits.

Do not repair failed examples after observing model outcomes without logging the failure and treating the repair as a new version.

---

## 11. Strict Prefix Definition

For each primary evidence event use the Stage 2C E0 annotation.

Define the primary prefix:

\[
c_{pre}=y_{<E0}
\]

That is:

> **all generated reasoning tokens strictly before E0, and no E0 token itself.**

The same exact token prefix must be used for:

- original image,
- counterfactual image,
- sham image,
- irrelevant-edit image.

Do not regenerate a different prefix for each image condition.

This preserves the causal comparison.

---

## 12. Primary Counterfactual Fact Pair

For each item define two minimally different candidate evidence continuations:

\[
s_o
\]

representing the original fact, and:

\[
s_c
\]

representing the counterfactual fact.

Example:

```text
s_o: "AB is 3"
s_c: "AB is 5"
```

Whenever possible, the two sequences should differ only in the evidence content.

Use the same surrounding grammatical structure.

Do not compare arbitrary unrelated continuations.

---

## 13. Primary Metric — Evidence Preference Shift

At the strict pre-E0 prefix, score both candidate fact continuations under both images.

Define:

\[
L_o(I)=\frac{1}{|s_o|}\log P(s_o\mid c_{pre},I)
\]

\[
L_c(I)=\frac{1}{|s_c|}\log P(s_c\mid c_{pre},I)
\]

Define fact preference:

\[
D(I)=L_o(I)-L_c(I)
\]

Then define the primary counterfactual effect:

\[
CE=D(I_o)-D(I_c)
\]

A positive \(CE\) means changing the image from original fact to counterfactual fact shifts the model's preference in the expected direction.

Report per-token normalized values.

---

## 14. Sham-Controlled Effect

Compute:

\[
D(I_{sham})
\]

and compare it with \(D(I_o)\).

The sham edit should produce little change relative to the true counterfactual edit.

A useful controlled quantity is:

\[
CE_{controlled}=[D(I_o)-D(I_c)]-[D(I_o)-D(I_{sham})]
\]

Equivalent formulations are acceptable if documented prospectively.

The point is to distinguish:

> semantic content change

from:

> edit artifact.

---

## 15. Secondary Metric — Next-Token Distribution Sensitivity

At the same strict pre-E0 prefix, compute a distribution-level change:

\[
U(t)=JS(p(\cdot\mid c_t,I_o),p(\cdot\mid c_t,I_c))
\]

or another symmetric divergence.

This is secondary because general distribution shift does not prove that the target fact specifically changed.

Interpret it together with the evidence-preference metric.

---

## 16. Pre-E0 Temporal Sensitivity Curve

Stage 3A should not inspect only one point.

For each problem define several **strictly pre-E0** checkpoints, for example:

- earliest valid reasoning checkpoint,
- E0-64,
- E0-32,
- E0-16,
- E0-8,
- immediately before E0,

subject to trajectory length.

All checkpoints must remain before E0.

At each checkpoint compute:

- distribution-level counterfactual sensitivity,
- evidence-specific preference where meaningful.

This creates:

\[
U_A(t),\quad t<E0
\]

The purpose is to ask:

> **When does visual content begin to have a causal effect on the reasoning state before the model explicitly talks about it?**

Do not use post-E0 points in the primary acquisition analysis.

Post-E0 analyses may be reported separately as semantic-expression controls.

---

## 17. Post-E0 Control Analysis

For a subset or all examples, evaluate the same counterfactual effect:

- during the fact-verbalization span,
- after E1,
- at first downstream use E2.

This is a control, not the primary acquisition result.

It helps determine whether visual-content sensitivity is:

- already present pre-E0,
- strongest only during semantic expression,
- retained after explicit scratchpad formation,
- or absent after textualization.

Do not confuse post-E1 sensitivity with initial acquisition.

---

## 18. Short Free Rollout From Pre-E0

In addition to teacher-forced scoring, perform a short free rollout from the exact same strict pre-E0 prefix under:

- original image,
- counterfactual image,
- sham image.

Use matched random seeds under the locked Thinking protocol.

Record:

- first entity/fact statement,
- whether original or counterfactual evidence is expressed,
- first semantic divergence,
- short continuation.

Primary purpose:

> behavioral validation that the counterfactual content can alter what the model says next.

Do not use one stochastic rollout per condition as a frequency estimate.

If compute permits, use several matched seeds per problem as a secondary robustness analysis.

---

## 19. Do Not Select on Attention

The primary cohort must not be restricted to:

- T1 pre-mention attention leads,
- Stage 2A A->B attention patterns,
- high ROI-attention examples.

Stage 2C showed that these patterns are rare and cohort-sensitive.

Attention timing category should be used only as a **post hoc moderator variable**.

For example, after the causal analysis ask:

> Do T1/T2/T4 attention patterns predict counterfactual sensitivity?

This tests whether attention contains any useful information about causal visual use without defining the cohort by attention.

---

## 20. Primary Statistical Analysis

Use base_problem_id as the independent unit.

Report:

- number of unique problems,
- median and mean CE,
- bootstrap confidence interval over base problems,
- proportion with CE in the expected direction,
- sham-controlled CE,
- effect distribution,
- evidence-type breakdown.

If multiple events from one base problem are retained secondarily, use:

- per-problem aggregation,
- or hierarchical/mixed-effects analysis.

Do not count correlated events as independent observations.

---

## 21. Key Scientific Outcomes

### Outcome A — Strong pre-E0 content sensitivity

Changing only the visual fact systematically shifts evidence preference before the fact is mentioned.

Interpretation:

> Visual evidence causally influences the reasoning state before explicit verbalization.

This justifies Stage 3B carrier tracing.

### Outcome B — Sensitivity emerges only near/after E0

Interpretation:

> Visual content becomes causally influential mainly around explicit semantic expression, consistent with Stage 2C's mention-centered picture.

This is still informative but changes the handoff hypothesis.

### Outcome C — Counterfactual target edit behaves like sham edit

Interpretation:

> The apparent effect is likely dominated by edit artifacts or the intervention is insufficiently valid.

Redesign the edit procedure.

### Outcome D — Little evidence-specific sensitivity anywhere

Interpretation:

> The current MathVerse evidence events may not provide a clean causal handle, or the model may rely on redundant/global visual representations.

Do not proceed directly to carrier patching.

---

## 22. GO / CONDITIONAL GO / REDESIGN

### GO — Carrier tracing

Proceed to Stage 3B if:

1. the counterfactual edit pipeline passes validation,
2. the primary cohort contains at least 30 unique base problems,
3. evidence-specific CE is directionally consistent across a substantial majority of problems,
4. the median effect clearly exceeds sham-edit effects,
5. at least a meaningful subset shows clear **pre-E0** sensitivity.

Do not require attention peaks to predict the effect.

### CONDITIONAL GO

Use if:

- content sensitivity is real but concentrated in one evidence type,
- pre-E0 sensitivity exists only in a subset,
- or edit quality limits the usable cohort.

Then narrow Stage 3B to the validated subset.

### REDESIGN

Do not start carrier tracing if:

- counterfactual and sham effects are similar,
- edits introduce uncontrolled artifacts,
- fewer than ~30 unique problems remain,
- or visual-content changes do not reliably affect evidence-specific predictions.

---

## 23. What Stage 3A Must Not Claim

Stage 3A may establish:

> visual content causally changes pre-mention reasoning predictions.

It must not yet claim:

- evidence is stored in question tokens,
- evidence is stored in reasoning tokens,
- V->Q->R handoff occurred,
- visual memory exists,
- direct visual access became unnecessary,
- re-grounding occurs,
- LOOK/THINK states exist.

Those require Stage 3B/3C.

---

## 24. Planned Stage 3B — Do Not Execute

If Stage 3A passes, Stage 3B will compare causal carriers using same-text/different-image runs.

Candidate carriers:

\[
V=\text{visual states}
\]

\[
Q=\text{prompt/question states}
\]

\[
R=\text{previous reasoning states}
\]

The goal will be to determine whether the evidence-bearing causal state changes over:

\[
\text{layer depth}\times\text{reasoning time}
\]

This stage should be designed only after reviewing Stage 3A results.

---

## 25. Output Structure

Create:

```text
outputs/stage3a/
  cohort/
    candidate_screening.jsonl
    primary_manifest.jsonl
    exclusion_log.jsonl

  counterfactuals/
    <base_problem_id>/
      original/
      counterfactual/
      sham/
      irrelevant_control/
      edit_metadata.json
      validation.md

  scoring/
    fact_preference.jsonl
    temporal_sensitivity.jsonl
    rollout_results.jsonl

  analysis/
    primary_statistics.json
    evidence_type_statistics.json
    attention_moderator_analysis.json
    figures/

  summaries/
    stage3a_summary.md
    stage3a_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 1/2 artifacts.

---

## 26. Required Figures

At minimum:

1. distribution of per-problem counterfactual effects,
2. original vs counterfactual vs sham fact preference,
3. pre-E0 temporal sensitivity curve,
4. effect by evidence type,
5. proportion of expected-direction effects,
6. representative successful and failed counterfactuals,
7. Stage 2C attention category vs Stage 3A causal effect as a secondary analysis.

---

## 27. Acceptance Criteria

Stage 3A technically passes if:

1. base_problem_id is treated as the primary independent unit,
2. 40 unique base problems are targeted,
3. at least 30 valid unique base problems remain,
4. selection is not based on ROI attention,
5. every primary edit is manually validated,
6. sham controls are implemented,
7. the primary prefix ends strictly before E0,
8. the exact same prefix is used across image conditions,
9. original and counterfactual fact continuations are prospectively defined,
10. evidence-preference CE is computed,
11. pre-E0 temporal sensitivity is measured,
12. free-rollout validation is performed,
13. Stage 2C attention timing is used only as a moderator,
14. no carrier patching is started,
15. an explicit GO / CONDITIONAL GO / REDESIGN decision is written.

Technical PASS does not require a positive causal result.

---

## 28. Stop Condition

After Stage 3A analysis and recommendation:

> **STOP.**

Do not start V/Q/R patching.
Do not run cutoff/reveal.
Do not return to A/B refresh experiments.

Review Stage 3A first and design the next stage using the full accumulated evidence.
