# Stage 4A Plan — Dynamic Multi-Evidence Selection, Switch, and Refresh
## Does Reasoning Demand Dynamically Choose Which Visual Evidence Re-Enters Computation?

## 0. Purpose

Stage 3C established a local causal lifecycle for visual evidence:

```text
recent reasoning context
→ retrieval demand
→ target-specific visual dependence
→ QK / routing + Value-rich visual transport
→ broad local integration
→ very recent reasoning-token K/V + current residual
→ evidence use
```

Stage 3C.10 strengthened the upstream link:

```text
recent reasoning contribution
→ target-specific current-query visual-source dependence
```

at both frozen retrieval coordinates.

However, almost all of Stage 3C concerns one currently relevant visual fact at a time.

Stage 4A asks the larger question needed for the paper:

> **As reasoning demands evolve, does the model dynamically switch which visual evidence it causally depends on, and can it re-engage an earlier visual fact after attention/reasoning has moved to another fact?**

The central target pattern is:

```text
Reasoning demand:
A → B → A

Causal visual dependence:
A → B → A
```

This stage tests **selection**, **switching**, and **refresh/reinstatement**.

It does not yet attempt to improve performance. Mechanism-guided failure rescue is reserved for Stage 4B.

---

# 1. Why Stage 4A Is Necessary for the Paper

The current headline candidate is:

> **Thinking MLLMs perform reasoning-conditioned visual retrieval.**

Stage 3C shows that reasoning context causally determines whether a particular visual source becomes behaviorally relevant.

But a reviewer can still interpret this narrowly:

> "The model becomes more vision-dependent near one evidence decision."

Stage 4A must determine whether the mechanism is genuinely **dynamic**.

A strong result would upgrade the claim to:

> **Thinking MLLMs dynamically retrieve and refresh different visual evidence as reasoning demands change.**

This is a qualitatively stronger insight than showing an ROI attention peak near verbalization.

---

# 2. Paper-Level Claim If Positive

The strongest supported claim would be:

> **Visual evidence is not simply propagated forward after a one-time image read. As the reasoning state changes its information needs, the model causally switches which visual fact enters computation and can later refresh a previously used fact.**

Conceptually:

```text
Need A
  ↓
causal dependence on visual A
  ↓
reasoning evolves
  ↓
Need B
  ↓
causal dependence switches to visual B
  ↓
reasoning evolves
  ↓
Need A again
  ↓
causal dependence on visual A reappears
```

---

# 3. Competing Mechanisms

Stage 4A is designed to distinguish at least four pictures.

## H1 — Dynamic demand-conditioned retrieval

```text
Need A → retrieve A
Need B → retrieve B
Need A → retrieve/refresh A
```

Prediction:

```text
A > B
→
B > A
→
A > B
```

in causal visual-source dependence.

## H2 — Persistent broadcast / both-facts-always-available

Both A and B remain comparably causally available throughout reasoning.

Prediction:

```text
A ≈ B
```

across demand transitions.

## H3 — Sticky / stale retrieval

The model initially retrieves one fact and fails to switch or refresh.

Possible phenotype:

```text
A > B
→
A >= B despite Need B
```

or:

```text
A > B
→
B > A
→
B >= A despite Need A again
```

## H4 — Distributed nonlocal support

Both local ROI suppressions are weak even though the model uses the facts through earlier/broader state.

A null under the local assay does not establish that multi-evidence reasoning is nonvisual.

---

# 4. What a Null Does NOT Establish

If clean A→B→A causal switching is weak, do not conclude:

```text
retrieval demand is false
```

because Stage 3C.10 already establishes the single-evidence recent-reasoning trigger link.

Surviving explanations include:

- local source windows miss earlier acquisition;
- A/B evidence has already been integrated into broader reasoning state;
- multi-evidence tasks use persistent joint storage rather than refresh;
- A/B event annotation is semantically correct but not aligned to acquisition time;
- native reasoning uses mixed A+B support;
- refresh occurs through broader residual state rather than direct ROI access.

Stage 4A tests the **scope and dynamic generality** of the Stage 3C mechanism.

---

# 5. Stage Structure

Stage 4A has four scientific phases.

## Phase A — Dedicated A→B→A cohort construction

Build a fresh cohort containing two independently localizable visual facts and three prospectively annotated demand events.

## Phase B — Dynamic causal source-selectivity

At A1, B, and A2, measure causal dependence on ROI A and ROI B under the same local source-suppression assay.

## Phase C — Retrieval-trigger continuity

Test whether the Stage 3C.10 recent-reasoning trigger mechanism also switches with the currently demanded evidence.

## Phase D — Counterfactual refresh challenge

On a frozen subset, test whether visual A can reassert causal semantic control at A2 even after earlier reasoning has already verbalized/used A.

Stage 4B failure rescue is not run in Stage 4A.

---

# 6. Cohort Size

## 6.1 Mechanical validation

Target:

```text
8 disjoint bases
```

## 6.2 Fresh primary cohort

Target:

```text
48 valid bases
```

Minimum:

```text
36
```

The cohort must be constructed prospectively and remain disjoint from prior mechanistic validation/discovery cohorts where feasible.

If fewer than 36 valid bases are obtained after the frozen screening budget:

```text
STOP as cohort-feasibility outcome
```

Do not relax event or ROI criteria to manufacture A→B→A cases.

---

# 7. Screening Budget

Recommended initial generation screen:

```text
800 trajectories
```

with prospective extension to:

```text
1200
```

only if needed to reach the frozen cohort target.

Record:

```text
attempted
completed
correct
multi-evidence candidate
two-ROI valid
A→B→A semantic sequence valid
counterfactual edit valid
retained
```

Selection must not use attention, QK, causal source effects, or Stage 4A intervention results.

---

# 8. Required Visual Structure

Each retained base must contain two distinct visual evidence sources:

```text
ROI A
ROI B
```

with all of the following:

1. spatially distinguishable source regions;
2. independently interpretable facts;
3. independently editable or suppressible;
4. no overlap in frozen visual-token ROI mapping;
5. both facts are genuinely relevant somewhere in the frozen reasoning trajectory.

Preferred evidence classes:

```text
localized length labels
angle labels
radius labels
formula labels
other clean localized numeric facts
```

Do not require identical evidence type for A and B.

---

# 9. Required Reasoning Structure

Each retained trajectory must contain three attention-blind semantic demand events in this order:

## A1 — Initial A use

The first frozen reasoning event where fact A is required for the annotated local inference.

## B — B use after A1

A later event where fact B is required.

## A2 — Re-use / refresh of A after B

A later event where fact A is again required.

Required ordering:

```text
A1 < B < A2
```

Required separation:

```text
B - A1 >= 12 generated reasoning tokens
A2 - B >= 12 generated reasoning tokens
```

Preferred:

```text
>= 24 tokens
```

where available.

The event order is semantic, not attention-derived.

---

# 10. Local Readouts

For every event:

```text
A1
B
A2
```

freeze a local evidence-use readout before causal scoring.

The readout must reflect the currently demanded fact.

Examples:

```text
candidate value for A
candidate value for B
downstream expression whose next discriminative token depends on A/B
```

Primary readout is local.

Final-answer correctness is secondary.

---

# 11. Independent A/B Counterfactual Assets

For every primary base, construct or retain independent semantic image variants:

```text
OO = native A, native B
AO = counterfactual A, native B
OB = native A, counterfactual B
AB = counterfactual A, counterfactual B
```

Names may be changed in implementation, but the 2×2 semantic structure is fixed.

Also retain same-pipeline sham edits when mechanically feasible:

```text
A_sham
B_sham
```

Counterfactual values must be independently valid and non-overlapping with the other fact.

No image may change both ROIs unless it is the explicit double-counterfactual condition.

---

# PHASE A — MECHANICAL VALIDATION

## 12. Canonical Platform

Use the frozen A6000 execution protocol:

```text
A6000 only
BF16
fixed repaired cached path
2048 generated-token maximum chunk
fixed allocator release
same model/tokenizer
same GQA/RoPE semantics
```

Every Stage 4A condition uses the same path.

---

# 13. Validation Requirements

Before primary scoring, pass on the 8-base validation set:

1. exact A/B ROI token maps;
2. no A/B visual-token overlap;
3. exact A1/B/A2 event indices;
4. exact local-readout indices;
5. all four semantic image variants have matched token layout;
6. ROI-A suppression changes only A contribution;
7. ROI-B suppression changes only B contribution;
8. joint A+B suppression changes exactly the union;
9. self/no-op suppression is exact;
10. deterministic replay;
11. counterfactual image scoring is finite;
12. sham rendering/token layouts valid;
13. recent-R trigger intervention isolation;
14. all passive telemetry reconstruction checks pass;
15. no attention-based selection enters any manifest.

---

# PHASE B — DYNAMIC CAUSAL SOURCE SELECTIVITY

## 14. Primary Source-Dependence Assay

At every event `e ∈ {A1, B, A2}`, compute causal dependence on both ROIs.

Use a frozen two-query local source window:

```text
W2(e) = [t_e - 1, t_e]
```

At every query in W2:

```text
all 36 language layers
all 32 logical heads
selected ROI contribution c_X → 0
```

where:

```text
X = A or B
```

This inherits the Stage 3C.4 result that the immediately preceding query is often behaviorally important.

No renormalization of attention probabilities.

Downstream computation recomputes naturally.

---

# 15. Secondary Wider Source Window

Also score, as a predeclared sensitivity assay:

```text
W8(e) = [t_e - 7, ..., t_e]
```

for ROI A and ROI B.

W2 remains primary.

W8 is used to determine whether a local null is plausibly due to slightly earlier acquisition.

Do not choose W2/W8 per example based on effect size.

---

# 16. Visual Source Dependence

For event `e` and ROI `X`:

```text
VSD_X(e)
=
D_native(e) - D_suppress_X(e)
```

using sign-aligned local evidence preference.

Compute separately for O/C semantic directions where relevant.

Unnormalized VSD is primary.

Do not treat any ratio as a unique information fraction.

---

# 17. Selection Indices

Define:

## A1 selection

```text
S_A1
=
VSD_A(A1) - VSD_B(A1)
```

## B selection

```text
S_B
=
VSD_B(B) - VSD_A(B)
```

## A2 refresh selection

```text
S_A2
=
VSD_A(A2) - VSD_B(A2)
```

The ideal dynamic phenotype is:

```text
S_A1 > 0
S_B  > 0
S_A2 > 0
```

---

# 18. Switch and Refresh Contrasts

In addition to within-event selectivity, compute:

## A→B switch

```text
Switch_AB
=
[VSD_B(B) - VSD_A(B)]
-
[VSD_B(A1) - VSD_A(A1)]
```

## B→A refresh

```text
Refresh_BA
=
[VSD_A(A2) - VSD_B(A2)]
-
[VSD_A(B) - VSD_B(B)]
```

Positive values indicate dynamic reversal of which visual source is causally more important.

---

# 19. Native Dynamic-Switch Base Classification

A base is classified as:

```text
DYNAMIC_A_B_A
```

only if:

1. `S_A1 > 0`;
2. `S_B > 0`;
3. `S_A2 > 0`;
4. demanded-ROI VSD exceeds the frozen minimum effect floor at all three events;
5. the two switch contrasts have the expected sign.

Freeze the minimum effect floor before primary scoring.

Recommended:

```text
0.05 nats / candidate token
```

Report continuous values regardless of class.

---

# 20. Primary Cohort-Level Claim

A strong dynamic retrieval claim requires:

```text
median S_A1 > 0
median S_B  > 0
median S_A2 > 0
```

plus robust positive:

```text
Switch_AB
Refresh_BA
```

with:

```text
>= 75% expected-direction bases
positive bootstrap mean CI
multiple-comparison-corrected paired significance
```

The base-level all-three-pass rate is secondary but important.

---

# 21. Joint A+B Suppression

As a secondary mechanistic control, suppress both A and B in W2:

```text
A+B → 0
```

This asks whether the demanded fact's effect is embedded in broader mixed visual support.

Do not interpret:

```text
joint - single
```

as a unique causal fraction.

Useful outcomes include:

```text
demanded ROI dominates
joint substantially exceeds demanded-only
non-demanded ROI contributes redundantly
```

---

# 22. Irrelevant ROI Control

Where a validated irrelevant ROI I exists, score:

```text
VSD_I(e)
```

on a frozen subset.

Demanded ROI dependence should exceed irrelevant ROI dependence.

This is a generic-visual-damage control.

---

# PHASE C — RETRIEVAL-TRIGGER CONTINUITY

## 23. Why This Phase Matters

Stage 4A should not merely show that different ROIs matter at different times.

To connect Stage 4A to the Stage 3C mechanism, ask:

> **Does recent reasoning control whichever visual source is currently demanded?**

Stage 3C.10 found a robust recent-reasoning trigger effect concentrated in layers 16–23.

Use that discovery as a frozen mechanistic bridge.

---

# 24. Trigger Intervention

At each A1/B/A2 current query, define:

```text
R16 = last up to 16 generated reasoning positions
```

Remove the R16 source contribution only in:

```text
layers 16–23
all 32 logical heads
current query
```

leaving visual K/V and current-query Q/K/V otherwise native at the local intervention boundary.

Downstream recomputes naturally.

---

# 25. Demand-Specific Trigger Effect

For event `e` and ROI `X`:

```text
TE_X(e)
=
VSD_X_native(e)
-
VSD_X_R16KD(e)
```

The demanded source should show the larger trigger effect.

Expected pattern:

```text
A1: TE_A > TE_B
B:  TE_B > TE_A
A2: TE_A > TE_B
```

This is the dynamic generalization of Stage 3C.10.

---

# 26. Trigger-Switch Metrics

Define:

```text
TS_A1 = TE_A(A1) - TE_B(A1)
TS_B  = TE_B(B)  - TE_A(B)
TS_A2 = TE_A(A2) - TE_B(A2)
```

A strong result supports:

> **The same recent-reasoning trigger mechanism dynamically retargets visual dependence as reasoning demand changes.**

---

# 27. Trigger Phase Gate

Phase C is confirmatory only if Phase B demonstrates at least:

```text
robust cohort-level Switch_AB
or
robust cohort-level Refresh_BA
```

If dynamic source switching itself is absent:

```text
do not force a trigger-switch interpretation
```

Still preserve passive trigger telemetry if already computed mechanically.

---

# PHASE D — COUNTERFACTUAL REFRESH CHALLENGE

## 28. Motivation

The strongest form of "refresh" is not merely:

```text
A dependence > B dependence at A2
```

It is:

> **A later visual update can regain causal semantic control even after A was already used earlier in the reasoning history.**

This tests whether vision can re-enter computation rather than the model relying only on stale textualized A information.

---

# 29. Phase-D Subset

Freeze a subset before counterfactual scoring:

```text
24 bases target
minimum 16
```

Requirements:

1. clean A/B independent edits;
2. A1 explicitly uses or verbalizes A;
3. B occurs after A1;
4. A2 later requires A again;
5. local A2 candidate readout is valid.

Selection must not depend on Stage 4A causal effect size.

---

# 30. Fixed-History Counterfactual A Refresh

At the frozen A2 readout:

- keep the recipient textual reasoning history fixed;
- compare native-A vs counterfactual-A visual conditions;
- keep B semantic state fixed.

Primary contrast:

```text
CE_A2
=
A-semantic preference under native-A image
-
A-semantic preference under counterfactual-A image
```

with sign aligned to the semantic change.

The purpose is not to produce a natural free rollout.

The purpose is:

> **Can the later computation still become causally controlled by current visual A despite earlier reasoning already containing A-related textual state?**

---

# 31. B Edit Control at A2

At A2, independently change only B.

Expected:

```text
A edit effect >> B edit effect
```

if A is selectively refreshed.

Likewise at B:

```text
B edit effect >> A edit effect
```

This gives a factorial semantic-control check.

---

# 32. Sham Controls

Use same-pipeline A/B sham edits where available.

Require semantic edit effects to exceed sham-rendering effects for confirmatory interpretation.

Do not require exact zero sham effect.

---

# 33. Counterfactual Dynamic Pattern

The strongest semantic-source identity result is:

```text
A1:
A edit controls local A evidence
B edit weak

B:
B edit controls local B evidence
A edit weak

A2:
A edit controls local A evidence again
B edit weak
```

This is a direct counterfactual analogue of:

```text
A → B → A
```

---

# 34. Important Interpretation Boundary for Phase D

A2 fixed-history counterfactual scoring may create tension with earlier teacher-forced A-related text.

Therefore:

- a strong A2 effect is compelling evidence of re-engaged visual control;
- a weak A2 effect does **not** prove absence of refresh;
- prior textual state may compete with the changed image.

Phase B native causal source dependence remains the primary Stage 4A result.

---

# PHASE E — PASSIVE TELEMETRY FOR STAGE 4B / FAILURE TAXONOMY

## 35. Why Save Telemetry Now

Stage 4B will ask whether failed switch/refresh can be rescued.

Post-Stage-4 analyses will ask:

```text
alignment
retrieval
verification
misretrieval
failed refresh
mirage
hallucination
integration failure
```

Therefore Stage 4A should save the relevant internal signals **without using them for cohort selection or primary classification**.

---

# 36. Passive Signals to Save

At A1/B/A2 save:

```text
A ROI attention density
B ROI attention density
A/B QK cosine
A/B scaled logits
A/B alphaV norm
A/B post-W_O contribution norm
candidate sink <|im_start|> mass
entropy
recent-R trigger quantities
current residual norms
A/B source-dependence scores
local correctness
final correctness
```

Where feasible also save:

```text
selected-head and all-head summaries
```

No passive signal may retroactively redefine demand events.

---

# 37. Failure Phenotypes to Freeze After Primary Results

After causal source results freeze, classify descriptively:

## Successful switch

```text
A1 selects A
B selects B
```

## Successful refresh

```text
B selects B
A2 selects A
```

## Failed switch

```text
B event remains A-dominant
```

## Failed refresh / stale B

```text
A2 remains B-dominant
```

## Mixed retrieval

A and B causal dependence both remain high.

## Local visual-insensitivity

Neither A nor B has substantial local VSD.

These labels are intended to seed Stage 4B and later failure taxonomy.

---

# 38. Stage 4B Boundary

Do not perform corrective interventions in Stage 4A.

After Stage 4A, review native failures and decide whether a mechanism-guided rescue is justified.

Potential Stage 4B interventions may include:

```text
demand-triggered refresh
stale-carrier suppression
demand-consistent rerouting
```

but none are pre-authorized here.

---

# 39. Statistical Unit

Primary independent unit:

```text
base_problem_id
```

A1/B/A2 are repeated within-base events.

Use paired within-base contrasts.

Do not treat:

```text
48 × 3 events
```

as 144 independent samples.

---

# 40. Primary Statistical Family

Primary family:

1. `S_A1 > 0`
2. `S_B > 0`
3. `S_A2 > 0`
4. `Switch_AB > 0`
5. `Refresh_BA > 0`
6. demanded ROI > irrelevant ROI
7. Phase-C `TS_A1 > 0` if gated
8. Phase-C `TS_B > 0` if gated
9. Phase-C `TS_A2 > 0` if gated

Use the project's frozen paired multiple-comparison procedure.

Report:

```text
median
mean
bootstrap 95% CI
positive fraction
paired p / corrected p
```

---

# 41. Main Scientific Outcomes

## O1 — Dynamic Multi-Evidence Retrieval

If causal source selectivity follows:

```text
A > B
→
B > A
→
A > B
```

then:

> **Visual dependence dynamically follows reasoning demand across multiple evidence sources.**

## O2 — Visual Refresh / Reinstatement

If A becomes selectively causal again at A2 after B dominated the middle event:

> **A previously used visual fact can be causally re-engaged after reasoning has moved to a different source.**

## O3 — Trigger-Retargeting

If Stage 3C.10-style recent-reasoning trigger effects also switch A→B→A:

> **Reasoning demand dynamically retargets which visual source enters computation.**

This is the strongest mechanistic generalization.

## O4 — Persistent Joint Availability

If A/B dependence remains broadly high across events without clear crossover:

> **Multi-evidence reasoning relies more on jointly available visual state than selective refresh.**

Do not force a switching story.

## O5 — Sticky / Failed Refresh

If the model often fails B→A reinstatement:

> **Visual retrieval can become stale across subgoal transitions.**

This becomes a high-value Stage 4B intervention target.

## O6 — Local Assay Insufficient

If both W2 and W8 local source effects are weak:

> **The multi-evidence mechanism is not captured by the tested local ROI-dependence assay.**

This does not invalidate Stage 3C.

---

# 42. What Would Make Stage 4A Insightful?

The experiment is worth the compute only if it can distinguish a new conceptual picture.

The strongest result is not:

```text
attention to A is high when talking about A
```

The strong result is:

```text
reasoning demand changes
→ causal source dependence reverses
→ the earlier source later becomes causal again
```

That would support:

> **Vision repeatedly re-enters reasoning under evolving information demand.**

This is the primary reason to run Stage 4A.

---

# 43. What Would Not Be Enough

Do not elevate the following to the headline:

```text
A ROI attention > B ROI attention at A1
B ROI attention > A ROI attention at B
```

without causal source-dependence switching.

Attention-only crossover is supporting evidence only.

Likewise, one illustrative A→B→A trajectory is not sufficient for the main claim.

---

# 44. No Overinterpretation of Failures

If A2 refresh is weak, distinguish:

```text
stale B dependence
joint A/B dependence
local visual-insensitivity
prior textual A dominance
annotation/acquisition mismatch
```

before labeling "failed refresh."

One negative intervention must not be used to abandon multi-evidence reasoning as a direction.

---

# 45. Paper Story After Stage 4A

If O1/O2/O3 are supported, the core narrative becomes:

```text
Reasoning does not merely consume a static visual representation.

Recent reasoning creates visual retrieval demand.
As that demand changes, the model dynamically selects different visual evidence.
Retrieved evidence is integrated into short-lived local reasoning state.
Previously used evidence can be re-engaged when reasoning needs it again.
```

This is the main conceptual contribution Stage 4A is designed to test.

---

# 46. Decision After Stage 4A

Recommend exactly one next step.

## GO — Stage 4B Mechanism-Guided Failure Rescue

Use if:

- dynamic switching/refresh is supported;
- there are enough native failed-switch / failed-refresh cases;
- failures have a mechanistically interpretable causal signature.

## GO — Multi-Evidence Storage / Joint-State Mechanism

Use if O4 dominates.

## GO — Broader Window / State-Level Multi-Evidence Assay

Use if O6 dominates.

Do not automatically proceed to Stage 4B because it was planned in advance.

---

# 47. Relationship to Post-Stage-4 Program

After Stage 4 is complete, retain the planned sequence:

```text
Failure / Attention-State Taxonomy
→ Causal Meaning of Visual Attention
→ Sink Causality if justified
```

Stage 4A telemetry should be preserved to support:

```text
alignment
retrieval
verification
misretrieval
failed refresh
mirage
hallucination
integration failure
```

analysis later.

---

# 48. Output Structure

```text
outputs/stage4a/
  config/
    stage4a_config.json
    cohort_rules.json
    event_rules.json
    roi_rules.json
    source_windows.json
    trigger_definition.json
    primary_family.json

  cohort/
    screening_accounting.json
    validation_manifest.jsonl
    primary_manifest.jsonl
    exclusions.jsonl

  annotations/
    roi_a_b.jsonl
    event_a1_b_a2.jsonl
    local_readouts.jsonl
    semantic_roles.jsonl

  counterfactuals/
    image_manifest.jsonl
    edit_validation.json
    sham_manifest.jsonl

  audit/
    canonical_path_audit.json
    roi_nonoverlap.json
    event_index_audit.json
    readout_index_audit.json
    source_suppression_selectivity.json
    joint_suppression_audit.json
    trigger_intervention_audit.json
    deterministic_replay.json
    self_patch_validation.json

  phase_b_source_switch/
    w2_roi_a.jsonl
    w2_roi_b.jsonl
    w8_roi_a.jsonl
    w8_roi_b.jsonl
    joint_ab.jsonl
    irrelevant_controls.jsonl
    dynamic_selectivity.json

  phase_c_trigger/
    r16_l16_23.jsonl
    trigger_selectivity.json
    trigger_statistics.json

  phase_d_counterfactual_refresh/
    subset_manifest.jsonl
    a_edit_results.jsonl
    b_edit_results.jsonl
    double_edit_results.jsonl
    sham_results.jsonl
    counterfactual_refresh_statistics.json

  telemetry/
    attention_qk_alphav.jsonl
    sink_mass.jsonl
    entropy.jsonl
    residual_norms.jsonl
    correctness.jsonl

  analysis/
    selection_switch_refresh.json
    base_level_dynamic_classes.json
    native_failure_phenotypes.json
    target_heterogeneity.json
    paper_claim_assessment.json
    figures/

  summaries/
    stage4a_summary.md
    stage4a_acceptance.json
    next_stage_recommendation.md
```

---

# 49. Required Figures

At minimum:

1. A/B causal VSD across A1→B→A2;
2. median causal selectivity trajectory;
3. per-base A→B switch scatter;
4. per-base B→A refresh scatter;
5. A1/B/A2 demanded-vs-nondemanded ROI effects;
6. W2 vs W8 comparison;
7. joint A+B suppression;
8. dynamic base-class proportions;
9. recent-R trigger selectivity A→B→A;
10. trigger effect vs causal VSD switch;
11. counterfactual A/B semantic-control trajectory;
12. A2 counterfactual refresh under fixed history;
13. successful vs failed-switch examples;
14. successful vs failed-refresh examples;
15. passive attention/QK trajectory as supporting evidence;
16. final conceptual diagram:
    ```text
    reasoning demand A → B → A
    visual dependence A → B → A
    ```

---

# 50. Acceptance Criteria

Stage 4A technically passes if:

1. cohort rules are frozen before causal scoring;
2. at least 36 valid primary bases are retained;
3. every retained base has two non-overlapping validated ROIs A/B;
4. every retained base has frozen A1/B/A2 semantic demand events;
5. event selection uses no attention or causal effect;
6. local readouts are frozen before intervention scoring;
7. all conditions use the canonical A6000 path;
8. ROI-A and ROI-B suppressions are mechanically isolated;
9. W2 is primary and W8 is predeclared sensitivity;
10. both A and B are scored at all three events;
11. dynamic claims use causal source dependence, not attention alone;
12. joint A+B suppression is secondary and not treated additively;
13. Stage 3C.10 trigger continuity runs only under its gate;
14. trigger effect uses frozen layers 16–23;
15. counterfactual A/B edits are independent;
16. fixed-history counterfactual refresh remains secondary to native VSD;
17. passive telemetry never changes cohort/event definitions;
18. no corrective Stage 4B intervention is run;
19. no post-Stage-4 attention/failure/sink experiment is started;
20. exactly one next-stage recommendation is produced.

Technical PASS does not require dynamic A→B→A switching.

---

# 51. Stop Condition

After:

```text
dedicated cohort construction
→ mechanical validation
→ W2/W8 A/B causal source dependence
→ A→B switch analysis
→ B→A refresh analysis
→ gated retrieval-trigger continuity
→ counterfactual refresh challenge
→ native failure phenotype freeze
→ paper-level claim assessment
→ exactly one recommendation
```

**STOP.**

Do not start:

```text
Stage 4B rescue
Failure / Attention-State Taxonomy
Causal Meaning of Visual Attention
Sink Causality
failure-mechanism deep dives
```

Return the complete Stage 4A result for review.

The next experiment must be selected by whether Stage 4A materially supports the paper's dynamic retrieval story, not by a precommitted desire to continue the planned roadmap.
