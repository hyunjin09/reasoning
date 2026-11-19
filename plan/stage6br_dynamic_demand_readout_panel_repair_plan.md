# Stage 6B-R Plan — Dynamic Demand / Readout Panel Repair
## Repairing Identification for Healthy Switching, Wandering, Fixation, and Stale Visual State

## 0. Purpose

Stage 6B completed all technical requirements, but the broad failure-mechanism claims were not established.

The main limitation was **not** a lack of controlled data, GPU execution, or successful source interventions.

The main limitation was **identification**:

```text
1. demand annotations were often too coarse or compound;
2. the exact causal panel contained too few valid source-transition pairs;
3. there were no matched stable-demand hold intervals;
4. numeric/value readouts could be correct even when source binding or geometric role was wrong;
5. therefore "source dominance" could not always be interpreted as causal error production.
```

Stage 6B-R is a **repair stage**.

It does not search for a new phenomenon.

It repairs the minimum parts of the existing C1 dynamic panel required to answer the paper-level question:

> **Is visual-state movement healthy when it follows reasoning demand, and pathological when it moves without demand or fails to move when demand changes?**

The central target comparison is:

```text
Demand stable   + visual state stable       → healthy hold
Demand changes  + visual state changes      → healthy switch
Demand stable   + visual state changes      → wandering
Demand changes  + old visual state persists → fixation / staleness
```

---

# 1. Why This Repair Is Necessary for the Paper

The paper already has strong evidence for:

```text
reasoning-conditioned visual retrieval
dynamic A → B → A source switching
local visual re-engagement / refresh
```

A generic trajectory claim such as:

```text
failed reasoning moves more in PCA space
```

would now be conceptually insufficient, because Stage 4A already showed that **large source changes can be correct and necessary**.

The stronger paper question is:

\[
\boxed{
\text{Does visual-state change occur when the reasoning demand says it should?}
}
\]

Stage 6B could not answer this cleanly because the exact dynamic panel had:

```text
20 bases
78 causal anchors
34 primary transitions
0 matched holds
19 selected refreshes
```

This made the "wandering" comparison structurally unidentifiable and fixation/staleness underpowered.

Stage 6B-R is therefore needed to turn the current qualitative trajectory idea into a causal, demand-conditioned comparison.

---

# 2. Paper Claim If Positive

A strong positive result would support:

> **Successful multimodal reasoning is characterized by demand-aligned changes in causal visual state. Visual-state movement becomes pathological when it occurs without a change in information demand, or when visual state fails to update after demand changes.**

Operationally:

\[
\boxed{
\text{healthy switch}
=
\text{demand change}
+
\text{matching source change}
}
\]

\[
\boxed{
\text{wandering}
=
\text{source change without demand change}
}
\]

\[
\boxed{
\text{fixation/staleness}
=
\text{demand change without source refresh}
}
\]

This would provide a mechanistic reinterpretation of trajectory "wandering" beyond path length/tortuosity alone.

---

# 3. What a Null Would NOT Rule Out

If Stage 6B-R still finds little wandering/fixation, do **not** conclude:

```text
retrieval-demand dynamics do not matter
```

Possible alternatives include:

```text
most model failures are downstream integration errors;
C1 numeric-source tasks genuinely contain little dynamic source pathology;
causal source identity is redundant across multiple equivalent ROIs;
the selected local readout still misses the true semantic decision;
some demand changes are carried through broader state rather than local direct source necessity;
failure occurs outside the first reviewed prefix scope.
```

A repaired null would mean:

> **The tested C1 dynamic failure mechanism is uncommon or weak under the repaired assay.**

It would not invalidate Stage 4A or Stage 3C.10.

---

# 4. Competing Mechanisms

Stage 6B-R distinguishes four models.

## H1 — Demand-aligned dynamic retrieval

```text
demand changes → causal source changes appropriately
demand stable  → causal source remains stable
```

## H2 — Wandering visual reassignment

```text
demand stable
but
causal visual source changes repeatedly
```

## H3 — Fixation / stale-source persistence

```text
demand changes
but
previous source remains causally active/dominant
```

## H4 — Mixed / distributed source support

```text
multiple sources remain simultaneously causal
```

In H4, hard winner-take-all source labels may be inappropriate.

The analysis must preserve:

```text
MIXED
NONE
UNRESOLVED
```

rather than forcing one source identity.

---

# 5. Scope

Stage 6B-R uses the **existing frozen C1 cohort and traces**.

It may:

```text
re-annotate compound demand states;
repair source/readout identity;
construct matched stable-demand holds;
score new exact causal anchor pairs on the existing cohort;
add error-oriented readouts;
recompute dynamic state labels;
reanalyze PCA/path metrics using repaired causal labels.
```

It must **not**:

```text
collect a new main cohort;
change the primary model;
change the primary dataset family;
run a failure-rescue intervention;
run sink causality;
run text↔visual representation substitution;
perform a new head/layer discovery search;
search until a positive failure class appears.
```

---

# 6. Existing C1 Resource Base

Use the frozen Stage 6A/6B C1 resources:

```text
109 retained bases
34 MathVerse
31 MathVision
44 MathVista

1,385 SOURCE_TO_SOURCE demand-transition annotations
3,683 matched-no-transition candidates
377 refresh candidates
97 reviewed wrong-claim anchors
1766 manually reviewed intact prefix spans
235 secondary numeric ROIs
```

Existing source masks, ROI maps, readouts, native traces, condition traces, and frozen discovery/confirmation split remain authoritative unless a documented annotation/readout error is repaired.

---

# 7. Canonical Execution

All new exact scoring uses the same canonical A6000 path:

```text
Qwen3-VL-4B-Thinking
BF16
fixed repaired cached/streaming path
2048 generated-token maximum chunk
fixed allocator handling
same tokenizer/model revision
same GQA/RoPE semantics
same candidate normalization
```

Do not mix absolute scores across incompatible execution shapes.

All within-contrast arms must share the same execution path.

---

# 8. Stage Structure

Stage 6B-R has five repair phases:

```text
Phase A — Set-Valued Demand Re-annotation
Phase B — Value / Binding / Error Readout Repair
Phase C — Transition ↔ Stable-Hold Panel Construction
Phase D — Exact Causal Dynamic Scoring
Phase E — Demand-Coupled Trajectory Reanalysis
```

A final gate determines whether any failure class is rescue-ready.

---

# PHASE A — SET-VALUED DEMAND RE-ANNOTATION

## 9. Why Set-Valued Demand Is Required

Stage 6B frequently encountered compound reasoning steps.

Examples:

```text
use A and B to compute C
compare A with B
combine radius r and angle θ
substitute two previously identified values
```

Forcing such spans into a single demanded source can create false:

```text
wandering
fixation
source switches
```

Stage 6B-R therefore represents demand as a set.

---

## 10. Demand State Ontology

For each reviewed span `s`, define:

\[
D_s \subseteq \mathcal{S}
\]

where `S` is the set of validated source identities in that base.

Allowed demand states:

```text
SINGLETON        = {A}
COMPOUND         = {A, B, ...}
NONE_VISUAL      = {}
UNRESOLVED       = unknown
```

Also record:

```text
primary source if one is semantically dominant
supporting sources
source roles
whether the source must be newly accessed
whether source content is already explicitly present in prior reasoning
```

Do not infer "new retrieval" solely from semantic demand.

---

## 11. Demand Transition Types

For adjacent reviewed spans:

```text
D_s → D_{s+1}
```

classify semantically as:

### T0 — Stable demand

```text
D_s = D_{s+1}
```

### T1 — Source replacement

```text
{A} → {B}
```

or non-overlapping set replacement.

### T2 — Demand expansion

```text
{A} → {A,B}
```

### T3 — Demand contraction

```text
{A,B} → {B}
```

### T4 — Partial replacement

```text
{A,B} → {B,C}
```

### T5 — Visual onset/offset

```text
{} → {A}
{A} → {}
```

Primary healthy-switch / wandering / fixation claims use T0/T1 first.

T2–T4 are secondary compound-demand analyses.

T5 is not used for the primary source-to-source failure classification.

---

## 12. Re-annotation Scope

Re-review existing C1 candidates in this priority order:

```text
all 1,385 existing SOURCE_TO_SOURCE candidates
all selected refresh candidates
enough NO_CHANGE candidates to build the hold panel
all 97 wrong-claim anchors
```

Do not fully annotate all 140k+ reasoning spans.

The repair should be targeted to the causal comparison needed.

---

## 13. Annotation Blinding

Demand re-annotation must be blind to:

```text
attention
QK
alphaV
VSD
PCA position
correctness outcome where avoidable
prior Stage 6B dynamic label
```

Annotators may see:

```text
image
problem
reasoning text
source/ROI definitions
ground-truth semantics
```

They should not see causal results.

---

# PHASE B — VALUE / BINDING / ERROR READOUT REPAIR

## 14. Why Readout Repair Is Necessary

Stage 6B identified an important failure mode of the assay:

```text
numeric value can be correct
while
source/entity/geometric binding is wrong
```

Example:

```text
true:
CD = 5

model:
AB = 5
```

A numeric readout on `5` alone may appear correct even though the source binding is wrong.

Therefore Stage 6B-R separates at least three readout types.

---

## 15. Readout Type V — Value Readout

Measures:

> **What numeric/evidential content is being used?**

Example:

\[
D_V =
\log p(v_{\text{correct}})
-
\log p(v_{\text{foil}})
\]

Use when the source identity is not itself the disputed semantic variable.

---

## 16. Readout Type B — Binding / Role Readout

Measures:

> **Which visual source/entity is the evidence assigned to?**

Examples:

```text
AB = 5 vs CD = 5
radius = 5 vs diameter = 5
x-coordinate = 3 vs y-coordinate = 3
upper segment = 7 vs lower segment = 7
```

Preferred contrast:

\[
D_B =
\log p(b_{\text{correct}})
-
\log p(b_{\text{wrong}})
\]

where the contrasted candidates differ in source/entity role, not merely value.

If a clean token-level binding contrast is unavailable:

```text
mark binding readout unavailable
```

Do not invent one.

---

## 17. Readout Type E — Error-Oriented Readout

For an observed wrong claim/token `w_wrong`, measure directly:

\[
E_1 = \log p(w_{wrong})
\]

and:

\[
E_2 =
\log p(w_{wrong})
-
\log p(w_{correct})
\]

Under source suppression define:

\[
EP_R =
E_{native} - E_{suppress\,R}
\]

A source is:

```text
error-promoting
```

only if removing it reduces wrong-token/claim preference in the predicted direction.

This is mandatory before using a source anomaly as the basis for a future rescue intervention.

---

## 18. Readout Validity Classes

Each causal anchor receives:

```text
VALUE_VALID
BINDING_VALID
ERROR_VALID
MULTI_VALID
READOUT_INSUFFICIENT
```

Primary transition analysis requires at least one valid semantic readout on each side.

Failure-causation claims require:

```text
ERROR_VALID
or
a directly equivalent semantic wrong-binding contrast
```

---

## 19. Readout Freeze

All repaired readouts must be frozen before new exact causal scoring.

Store:

```text
anchor_id
source identities
candidate strings/tokens
candidate normalization
readout type
ground-truth direction
wrong direction if applicable
reason for validity
```

No candidate is changed after seeing intervention effects.

---

# PHASE C — TRANSITION ↔ STABLE-HOLD PANEL CONSTRUCTION

## 20. Core Identification Principle

The key comparison is paired:

```text
demand changes
vs
demand stays stable
```

under similar reasoning conditions.

Without a stable-demand comparison, "source movement" cannot be interpreted as wandering.

---

## 21. Primary Transition Panel

Retain T1 source-replacement transitions first.

Eligibility:

```text
single-source demand before
single-source demand after
distinct validated source identities
valid pre readout
valid post readout
both source ROIs available
semantic transition unambiguous
```

Target:

```text
>= 96 transitions
```

Minimum:

```text
>= 64
```

across:

```text
>= 48 bases
```

Preferred target:

```text
>= 64 bases
```

---

## 22. Stable-Hold Panel

For each transition or transition family, construct a matched T0 interval.

Eligibility:

```text
same demanded source across both endpoints
valid source ROI
valid readout at both endpoints
no newly introduced visual subgoal
```

Matching priority:

```text
same base
same source identity
similar reasoning progress
similar token/span gap
same readout type
same evidence class
```

If same-base matching fails, use cross-base matching within:

```text
dataset
evidence type
readout type
reasoning-progress bucket
```

No matching variable may use attention or causal effect.

---

## 23. Matching Targets

Target:

```text
>= 96 matched hold intervals
```

Minimum:

```text
>= 64
```

Primary paired analysis prefers:

```text
1 transition : 1 hold
```

If more holds exist, freeze one primary hold and retain extras as sensitivity.

---

## 24. Refresh Panel

Use existing reviewed refresh candidates.

Eligibility:

```text
A previously demanded
intervening non-A demand
A demanded again
valid returning-source readout
valid prior-source/intervening-source identities
```

Target:

```text
>= 32 refresh events
```

Minimum descriptive:

```text
>= 20
```

---

## 25. Failure-Enriched Panel

Separately retain:

```text
wrong local claim
wrong binding
wrong downstream step
```

events only after the primary panel is frozen.

This panel is case-control and not used for prevalence.

Target:

```text
>= 24 error-valid events
```

if available.

Do not extend the cohort merely to hit this number during Stage 6B-R.

---

# PHASE D — EXACT CAUSAL DYNAMIC SCORING

## 26. Primary Source Assay

Use:

```text
W2 = [t-1, t]
all 36 layers
all 32 heads
selected source contribution → 0
no attention renormalization
```

Score for each endpoint:

```text
currently demanded source(s)
previous source
plausible alternative source
irrelevant control where available
```

W8 sensitivity:

```text
demanded + previous source
```

on a frozen subset.

---

## 27. Set-Valued Causal Support

For each anchor `s` and source `R`:

\[
C_s(R) = VSD_R(s)
\]

For demand set `D_s`, define:

\[
Support(D_s)
=
\sum_{R\in D_s} \max(C_s(R),0)
\]

for descriptive purposes only.

Do not interpret this sum as unique information.

Primary source-state reporting remains per-source.

---

## 28. Causal Active-Source Set

Use discovery-only data to freeze:

```text
minimum effect floor
dominance margin
mixed-support rule
```

Initial default:

```text
VSD > 0.05 nats/candidate-token
```

as the source-activity floor unless readout scale materially differs.

Define:

```text
A_s = set of causally active sources
```

not necessarily one source.

---

## 29. Set-Valued Demand Coupling

For single-source demand:

\[
DCM_s =
VSD_{demanded}
-
\max_{R\notin D_s} VSD_R
\]

For multi-source demand, use:

```text
coverage = fraction of demanded sources that are causally active
intrusion = substantial causal support from non-demanded sources
```

Possible state labels:

```text
ALIGNED
PARTIAL
MIXED
INTRUSIVE
NONE
UNRESOLVED
```

Primary healthy-switch/wandering/fixation claims use single-source T0/T1 first.

---

## 30. Healthy Hold

For T0 stable-demand interval:

```text
D_pre = D_post = {A}
```

a strict healthy hold requires:

```text
A causally aligned pre
A causally aligned post
no non-demanded source becomes dominant
```

---

## 31. Healthy Switch

For T1:

```text
{A} → {B}
```

a strict healthy switch requires:

```text
pre: A aligned/dominant
post: B aligned/dominant
```

Report:

```text
switch success
source-margin change
new-source gain
old-source decay
```

---

## 32. Wandering

For T0:

```text
{A} → {A}
```

a strict wandering event requires:

1. A is aligned pre;
2. post causal source state changes materially;
3. a non-demanded source becomes dominant or substantially intrusive;
4. no semantic demand change explains the source change;
5. both endpoint readouts are valid.

Separate:

```text
WANDERING_BENIGN
WANDERING_ERROR_ASSOCIATED
```

after correctness labels are applied.

---

## 33. Fixation / Staleness

For T1:

```text
{A} → {B}
```

a strict fixation event requires:

1. A is aligned pre;
2. post demand is B;
3. old source A remains substantial/dominant;
4. B fails to become adequately aligned within the frozen post window.

Subclasses:

```text
PURE_FIXATION
MIXED_STALE
DELAYED_SWITCH
NO_VISUAL_SUPPORT
UNRESOLVED
```

Do not collapse delayed switch into fixation.

---

## 34. Transition Latency

For a frozen subset with enough adjacent valid anchors:

```text
pre-2
pre-1
transition
post-1
post-2
```

measure when the new demanded source first becomes causally aligned.

Define:

```text
latency = first valid post-transition anchor with B aligned
```

If never observed:

```text
right-censored
```

This provides:

```text
immediate switch
delayed switch
persistent stale source
```

without assuming acquisition timing from a single VSD window.

---

## 35. Refresh Classification

For:

```text
A → B → A
```

or equivalent re-demand:

```text
SUCCESSFUL_REFRESH
DELAYED_REFRESH
MIXED_REFRESH
FAILED_REFRESH_STALE_B
NO_LOCAL_VISUAL_SUPPORT
UNRESOLVED
```

A successful refresh requires the returning source to re-enter the causal active set and recover positive demanded-source margin.

---

## 36. Error-Causation Classification

For a wrong anchor, combine:

```text
demand state
causal source state
value readout
binding readout
error-oriented readout
```

Possible labels:

```text
WRONG_SOURCE_ERROR_PROMOTING
STALE_SOURCE_ERROR_PROMOTING
VALUE_EXTRACTION_ERROR
BINDING_ERROR
DOWNSTREAM_INTEGRATION_ERROR
CAUSAL_SOURCE_ANOMALY_NOT_ERROR_PROMOTING
UNRESOLVED
```

This replaces any simplistic:

```text
alternative source dominates correct-vs-wrong margin
→ misretrieval caused the error
```

interpretation.

---

## 37. Primary Statistical Contrasts

### Contrast 1 — Demand-change source motion

Compare:

```text
causal source-state change across T1 transitions
vs
causal source-state change across matched T0 holds
```

Primary quantity:

```text
change in demanded-source identity/margin
```

### Contrast 2 — Demand alignment

Compare post-event:

```text
new-demand source margin in T1
vs
same-demand source margin in T0
```

### Contrast 3 — Unnecessary switching

Measure:

```text
non-demanded source intrusion/change under stable demand
```

### Contrast 4 — Failed switching

Measure:

```text
old-source persistence under changed demand
```

### Contrast 5 — Refresh

Measure:

```text
returning-source causal re-engagement
```

---

## 38. Robustness Rule

For a directional cohort-level contrast to be called robust:

```text
expected-direction median
bootstrap 95% mean CI excludes zero
>= 75% expected-direction bases where meaningful
Holm-corrected p < .05
```

Use:

```text
10,000 base bootstrap resamples
paired Wilcoxon where appropriate
base as independent unit
```

Do not treat anchors as independent observations.

---

## 39. Primary Dynamic Panel Gate

Confirmatory dynamic inference requires:

```text
>= 48 bases
>= 64 valid T1 transitions
>= 64 valid matched T0 holds
```

Preferred:

```text
>= 64 bases
>= 96 transitions
>= 96 holds
```

If this gate fails:

```text
STOP as repair-insufficient
```

Do not run a broad wandering/fixation claim analysis on an underidentified panel.

---

# PHASE E — DEMAND-COUPLED TRAJECTORY REANALYSIS

## 40. Why Reanalyze PCA Only After Repair

Stage 6B already showed that PCA/path geometry exists, but sparse causal coverage prevented a strong claim that demand coupling is more mechanistically informative than path length.

Stage 6B-R uses repaired causal labels to test that claim.

PCA remains descriptive.

---

## 41. Preserve Existing PCA Basis

Do not refit the primary passive PCA if the existing discovery fit is valid.

Use the frozen discovery PCA basis for confirmation projection.

If repaired readout features add dimensions not present in the existing PCA:

```text
analyze them outside the old PCA space
```

Do not silently refit and compare as if unchanged.

A new "repair PCA" may be created only as secondary descriptive analysis, fit on discovery only and named separately.

---

## 42. Trajectory State Categories

For reviewed intervals assign:

```text
HEALTHY_HOLD
HEALTHY_SWITCH
WANDERING
FIXATION
DELAYED_SWITCH
MIXED
UNRESOLVED
```

Then compare path geometry.

The critical quadrants are:

| Demand | Causal state | Interpretation |
|---|---|---|
| stable | stable/aligned | healthy hold |
| changes | changes appropriately | healthy switch |
| stable | changes/intrudes | wandering |
| changes | remains old | fixation/staleness |

---

## 43. Path Metrics

Reuse:

```text
path length
tortuosity
```

and report them by repaired dynamic state.

Also report:

```text
demand coupling
unnecessary switching
failed switching
transition latency
```

Primary mechanistic question:

> **Does demand coupling distinguish healthy/failure states more directly than path length alone?**

---

## 44. Required vSTREAM-Style Comparison

Replicate descriptively:

```text
correct vs wrong path length/tortuosity
```

but then stratify by repaired dynamic state.

Key comparisons:

```text
correct + high movement + healthy switch
wrong + high movement + wandering
wrong + low movement + fixation
correct + low movement + healthy hold
```

A successful result should demonstrate that:

```text
movement magnitude is ambiguous without demand context
```

---

## 45. Failure Association

After dynamic labels freeze, compare with:

```text
local value correctness
local binding correctness
downstream reasoning correctness
final correctness
```

Do not define the state classes using these outcomes.

Primary association questions:

```text
Is wandering enriched in local/binding errors?
Is fixation enriched after demand switches?
Are integration errors often demand-aligned despite final failure?
```

---

## 46. Dataset Robustness

Report separately:

```text
MathVerse
MathVision
MathVista
```

for all primary dynamic contrasts where sample size permits.

Also report:

```text
leave-one-dataset-out
```

A pooled effect driven entirely by one dataset is not a cross-dataset dynamic claim.

---

## 47. Readout-Type Robustness

Report primary results separately for:

```text
value-valid anchors
binding-valid anchors
multi-valid anchors
```

If the dynamic conclusion appears only under numeric value readouts but disappears under binding readouts:

```text
do not claim source-tracking mechanism broadly
```

That would indicate readout dependence.

---

## 48. Error-Oriented Robustness

Any future rescue-ready failure class must satisfy:

```text
source anomaly
+
error-oriented readout in the predicted direction
```

Recommended minimum:

```text
>= 24 fresh Tier-1/strong Tier-2 events
```

for one coherent class.

If fewer than 24:

```text
do not run full rescue
```

A small bounded pilot may only be recommended if the causal direction is exceptionally clean and fresh confirmation is predeclared afterward.

---

## 49. Mirage Boundary During Repair

Do not rerun the broad C1 mirage discovery/confirmation as the main objective.

Preserve existing Stage 6B findings:

```text
9 strict candidates
8/62 bases
7 source groups
continuous divergence not broadly robust
```

Use mirage only as a secondary state in trajectory synthesis if a repaired demand/readout label exists.

Do not optimize mirage thresholds during Stage 6B-R.

---

## 50. Sink Boundary

Sink remains descriptive only.

Do not run sink intervention.

Existing strict-candidate sink association may be reported as background, but Stage 6B-R does not reopen the sink gate unless the repaired dynamic classes produce a new, replicated, behavior-linked sink prediction.

---

## 51. Natural Validation Boundary

Do not extend C4 in this repair stage.

The missing evidence is not natural sample size.

The missing evidence is the repaired exact demand/readout causal panel.

Natural extension may be reconsidered only after Stage 6B-R establishes a specific failure signature worth validating.

---

## 52. Discovery / Confirmation Discipline

Use the existing C1 discovery/confirmation split.

Discovery may be used only to freeze:

```text
set-demand edge cases
source activity floor if adjustment is necessary
dominance margin
binding/error readout conventions
matching tolerances
```

Confirmation receives the frozen rules unchanged.

Do not move cases across splits.

---

## 53. Mechanical Validation

Before full rescoring, validate on:

```text
8–12 representative bases
```

covering:

```text
single-source transition
compound demand
stable hold
binding-error candidate
refresh
wrong-claim/error-oriented readout
```

Checks:

1. source identities reproduce;
2. W2 suppression isolates selected source;
3. candidate tokens/readouts are exact;
4. binding candidate orientation is correct;
5. wrong-token orientation is correct;
6. pre/post anchor indices are exact;
7. set-valued demand annotations serialize correctly;
8. matched hold does not contain a hidden subgoal change;
9. no-op replay exact;
10. canonical execution path exact.

---

## 54. Output Structure

```text
outputs/stage6br/
  config/
    stage6br_config.json
    demand_ontology.json
    readout_rules.json
    transition_rules.json
    hold_matching_rules.json
    source_activity_rules.json
    statistical_families.json

  annotation_repair/
    demand_states.jsonl
    compound_demand_review.jsonl
    transition_types.jsonl
    source_roles.jsonl
    value_readouts.jsonl
    binding_readouts.jsonl
    error_readouts.jsonl
    readout_validity.jsonl
    annotation_exclusions.jsonl

  panel/
    transition_candidates.jsonl
    transition_primary.jsonl
    hold_candidates.jsonl
    hold_primary.jsonl
    transition_hold_pairs.jsonl
    refresh_panel.jsonl
    failure_enriched_panel.jsonl
    panel_accounting.json

  audit/
    mechanical_validation.json
    canonical_path_audit.json
    anchor_index_audit.json
    source_mask_audit.json
    readout_orientation_audit.json
    hold_semantic_match_audit.json
    split_integrity.json
    causal_replay.json
    resource_summary.json

  causal/
    pre_post_source_scores.jsonl
    w2_scores.jsonl
    w8_sensitivity.jsonl
    source_active_sets.jsonl
    demand_coupling.jsonl
    healthy_hold.jsonl
    healthy_switch.jsonl
    wandering.jsonl
    fixation_staleness.jsonl
    refresh.jsonl
    transition_latency.jsonl
    error_causation.jsonl

  trajectory/
    repaired_state_labels.jsonl
    frozen_pca_projection.jsonl
    path_metrics_by_state.json
    demand_vs_path_comparison.json
    correctness_association.json
    dataset_stratification.json
    readout_type_stratification.json

  analysis/
    primary_statistics.json
    paper_claim_assessment.json
    panel_identification_assessment.json
    rescue_readiness.json
    next_stage_decision.json
    figures/

  summaries/
    stage6br_summary.md
    stage6br_acceptance.json
    next_stage_recommendation.md
```

---

## 55. Required Figures

At minimum:

1. repaired demand-state ontology;
2. single vs compound demand examples;
3. value vs binding vs error readout examples;
4. transition/hold panel construction;
5. source-state change in T1 transitions vs T0 holds;
6. demanded-source causal margin pre/post;
7. healthy hold examples;
8. healthy switch examples;
9. wandering examples;
10. fixation/stale examples;
11. delayed-switch / latency examples;
12. refresh classifications;
13. error-oriented source effects;
14. numeric-correct / binding-wrong examples;
15. dynamic-state frequencies in the repaired panel;
16. dynamic state vs local/final correctness;
17. path length by dynamic class;
18. tortuosity by dynamic class;
19. demand coupling vs path length;
20. vSTREAM-style correct/wrong path plot with dynamic-state overlay;
21. per-dataset dynamic contrasts;
22. value-readout vs binding-readout sensitivity;
23. rescue-readiness by failure class;
24. final conceptual figure:

```text
                    DEMAND
               stable       changes
                 │             │
                 │             │
VISUAL      stable/aligned   changes correctly
STATE        healthy hold     healthy switch

VISUAL      changes/intrudes stays old
STATE         wandering       fixation/staleness
```

---

## 56. Primary Scientific Outcomes

### O1 — Demand-Aligned Dynamic Retrieval

If changed demand causes matched source changes while stable demand predicts source stability:

> **Causal visual-state movement is aligned with reasoning demand.**

### O2 — Wandering

If stable-demand holds show unnecessary source switching in a reproducible subset, especially with downstream errors:

> **Some multimodal reasoning failures involve visual-source wandering without a change in information demand.**

### O3 — Fixation / Staleness

If old sources remain causal after demand changes and error-oriented readouts support harmful persistence:

> **Some failures arise from stale visual-state fixation after subgoal transitions.**

### O4 — Readout Separation

If value readouts remain correct while binding readouts fail:

> **Visual-content extraction and visual-source binding are separable failure points.**

This would be a valuable mechanistic result even if wandering/fixation are rare.

### O5 — Path-Length Reinterpretation

If high path movement contains both healthy switching and wandering, and low movement contains both healthy holds and fixation:

> **Trajectory movement alone is not a sufficient failure signal; demand alignment is the mechanistically relevant variable.**

### O6 — Mostly Integration Failure

If dynamic source states are usually demand-aligned even in wrong outcomes:

> **Many failures occur after successful visual retrieval dynamics rather than through source-tracking failure.**

This is also a valid and useful paper result.

---

## 57. What Would Make This Repair Worthwhile?

The strongest result is not:

```text
more correct cases switch appropriately
```

The stronger result is a mechanistic decomposition:

```text
correct high-motion → healthy demand-aligned switch
wrong high-motion   → wandering
wrong low-motion    → fixation
wrong but aligned   → downstream integration failure
```

This would explain why raw PCA/path length is insufficient and connect the paper's earlier retrieval-demand result directly to failure behavior.

---

## 58. What Would Not Be Enough

Do not headline:

```text
correct trajectories are shorter
```

Do not call:

```text
any source change = wandering
```

Do not call:

```text
any no-switch = fixation
```

Do not call:

```text
numeric value correct = source binding correct
```

Do not call:

```text
alternative-source VSD effect = wrong-source causation
```

without error-oriented support.

Do not change the panel until a desired failure count appears.

---

## 59. Technical Acceptance Criteria

Stage 6B-R technically passes if:

1. existing C1 cohort and discovery/confirmation split remain unchanged;
2. set-valued demand ontology is frozen before causal rescoring;
3. all primary T1/T0 annotations are attention-blind;
4. value/binding/error readout types are explicitly separated;
5. all repaired readouts are frozen before intervention effects;
6. primary transition panel reaches the minimum gate or stops as insufficient;
7. primary stable-hold panel reaches the minimum gate or stops as insufficient;
8. matching uses no causal/attention feature;
9. W2 remains the primary source assay;
10. W8 remains predeclared sensitivity;
11. source activity/dominance rules are frozen on discovery;
12. MIXED/NONE/UNRESOLVED remain allowed;
13. wandering requires stable demand;
14. fixation requires changed demand;
15. delayed switching is not merged into fixation;
16. error-promoting claims use error-oriented readouts;
17. PCA does not define causal states;
18. key path metrics are interpreted with demand labels;
19. no new main cohort is collected;
20. no rescue/sink/representation intervention is run;
21. exactly one next-stage recommendation is produced.

---

## 60. Next-Stage Decision

Produce exactly one recommendation.

### GO — Mechanism-Guided Failure Rescue

Use only if one repaired failure class satisfies:

```text
>= 24 coherent fresh confirmation events
clear causal direction
error-oriented readout supports harmful source contribution
specific intervention with a falsifiable prediction
matched non-failure controls predict little/opposite effect
```

### GO — Targeted Natural Failure Validation

Use if:

```text
a coherent dynamic failure signature is established
but natural ecological validation is the main missing evidence
```

Target the discovered signature rather than generic COCO hallucination.

### GO — Causal Meaning of Text↔Visual Alignment

Use if:

```text
dynamic failures remain rare
and
the strongest unresolved mechanistic question is alignment/routing semantics
```

### STOP / REPORT BOUNDARY

Use if:

```text
the repaired panel is sufficient
but healthy demand-aligned retrieval dominates and failure classes remain too rare
```

This is a scientifically valid result.

Do not manufacture a rescue target.

---

## 61. Stop Condition

After:

```text
set-valued demand repair
→ value/binding/error readout repair
→ transition panel freeze
→ matched-hold panel freeze
→ exact W2/W8 causal scoring
→ healthy-switch/hold classification
→ wandering/fixation/refresh classification
→ error-causation diagnostics
→ repaired trajectory/PCA interpretation
→ rescue-readiness assessment
→ paper-claim assessment
→ exactly one next-stage recommendation
```

**STOP.**

Do not start the recommended next experiment automatically.

---

## 62. Final Research Principle

Stage 6B-R should answer one question cleanly:

\[
\boxed{
\text{Does the model's causal visual state change when its reasoning demand changes — and only when it should?}
\]

The repair is successful if it makes that question identifiable, regardless of whether wandering or fixation turn out to be common.
