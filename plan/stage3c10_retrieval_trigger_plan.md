# Stage 3C.10 Plan — Reasoning-State Retrieval Trigger
## What Makes the Model Look Again?

## 0. Purpose

Stages 3C.1–3C.9R establish a strong local visual-evidence lifecycle:

```text
task-conditioned retrieval
→ target QK sharpening / ROI-selective attention
→ Value-rich visual contribution
→ broad local integration
→ very recent reasoning-token K/V + current residual
→ downstream evidence use
```

Stage 3C.9R adds an important long-horizon constraint:

```text
10 isolated C2/C3 checkpoints
0 / 48 repeated-checkpoint bases
```

under the frozen W8/W16 sparse semantic-span assay.

Thus the current paper story should **not** assume that long reasoning is organized around repeatedly recurring sparse semantic-token checkpoints.

The main missing mechanistic question is now:

> **What in the ongoing reasoning state causes a later query to enter a visual-retrieval mode?**

Stage 3C.10 tests the causal chain:

```text
recent reasoning state
        ↓
current-query retrieval configuration
        ↓
target QK / routing
        ↓
behavioral dependence on target visual evidence
```

The key claim under test is:

> **Recent reasoning context causally configures the next query into a target-specific visual-retrieval state.**

This is a retrieval-trigger experiment, not a token-carrier or sink experiment.

---

## 1. Why This Experiment Is Necessary for the Paper

This stage is justified only because it closes a specific gap in the current causal story.

We already know:

### From Stage 3C.2

Natural retrieval demand is distinguishable from semantic mention alignment:

```text
mention state M
→ mention-aligned attention

retrieval state T
→ target-dominant QK / attention / alphaV
```

### From Stage 3C.3

Changing the **current query state** causally changes:

```text
QK
attention
alphaV
```

but query substitution alone did not reliably produce reciprocal behavioral evidence changes.

Therefore:

```text
current query state → routing
```

is established, but the upstream source of that query state is not.

### From Stages 3C.7–3C.8

Very recent reasoning-token state is a real functional carrier and is strongly recency-dominant.

### From Stage 3C.9R

Long reasoning does not generally show repeated sparse semantic checkpoints.

That leaves the important mechanistic gap:

```text
recent reasoning
    ?
    ↓
retrieval query
```

Stage 3C.10 directly tests that gap.

---

## 2. Paper-Level Claim If Positive

A strong positive result would support:

> **Visual retrieval is re-initiated by reasoning-dependent demand: recent reasoning state causally shapes the next query's target-specific routing geometry, thereby increasing its behavioral dependence on the relevant visual evidence.**

This would connect the current Stage 3C story into:

```text
reasoning demand
→ retrieval trigger
→ query-side routing
→ visual evidence retrieval
→ local reasoning-side carriage
```

This is substantially more informative than another attention correlation.

---

## 3. What a Null Would NOT Establish

A weak recent-reasoning trigger effect does **not** establish that retrieval is spontaneous or reasoning-independent.

Surviving alternatives include:

- trigger information lives farther back than the tested recent window;
- prompt/Q state supplies the control signal;
- trigger is distributed across residual state rather than recoverable from one source group;
- current lexical token identity contributes strongly;
- source-contribution deletion is too redundant to expose necessity;
- multiple recent-token paths compensate for one another.

A null therefore redirects the trigger mechanism; it does not erase the established retrieval phenomenon.

---

## 4. Main Competing Mechanisms

Stage 3C.10 distinguishes:

### H1 — Recent-reasoning trigger

```text
R_recent
→ current query state
→ target visual retrieval
```

Prediction:

- removing recent-reasoning contribution reduces target routing and target visual-source dependence;
- restoring native current-query Q geometry rescues them.

### H2 — Prompt/controller-dominant trigger

```text
Q_prompt
→ current query state
→ target visual retrieval
```

Prediction:

- prompt-source removal matters more than recent-R removal.

### H3 — Routing-only recent influence

Recent reasoning controls QK/attention but behavior remains visually dependent through redundant routes.

Prediction:

- routing readouts move;
- behavioral visual-source dependence does not.

### H4 — Distributed / unresolved trigger

No tested source group cleanly controls retrieval.

Prediction:

- neither recent-R nor prompt-source intervention gives a robust behavioral effect.

---

## 5. Primary Cohort

Reuse the exact Stage 3C.2 / 3C.3 retrieval-demand cohort:

```text
31 bases total
7 frozen validation bases
24 frozen primary bases
```

These bases already provide the key natural contrast:

```text
M = mention / retrieval-light state
T = task-required retrieval state
```

and the independently frozen target coordinates:

```text
Target A
Target B
```

No base is selected by Stage 3C.10 effect size.

The primary independent unit remains:

```text
base_problem_id
```

Target A and Target B remain separately visible.

---

## 6. Why Reuse This Cohort

This is preferable to constructing a new retrieval cohort because:

1. M and T were defined independently of the new intervention;
2. Stage 3C.2 already demonstrated a clean natural retrieval-vs-alignment contrast;
3. Stage 3C.3 already validated query-side causal routing at the same coordinates;
4. Stage 3C.4–3C.8 established causal visual dependence and local carrier behavior on the same mechanistic family.

Stage 3C.10 therefore tests a genuinely new **upstream causal link**, not the same effect again.

---

## 7. Frozen Retrieval Coordinates

Reuse the exact historical targets.

### Target A

```text
retrieval coordinate: E_d
routing layer: 29
historical causal heads: [11, 6, 15, 12]
```

### Target B

```text
retrieval coordinate: E_d - 1
routing layer: 28
historical causal heads: [16, 0, 3, 6]
```

The exact M and T positions from Stage 3C.2/3C.3 must be loaded from frozen artifacts.

Do not reannotate them using Stage 3C.10 results.

---

## 8. Canonical Hardware / Execution

Use the frozen A6000 canonical path validated before Stage 3C.9:

```text
A6000 only
BF16
fixed repaired cached execution
maximum generated-token chunk = 2048
same attention implementation
same GQA / RoPE semantics
same model/tokenizer
```

All native, trigger-knockdown, source-suppression, rescue, and controls must use this path.

---

## 9. Primary Trigger Object

At the current query `t`, define the contribution from the most recent generated reasoning positions:

```text
R16(t) = generated reasoning positions [t-16, t-1]
```

At layer `l`, logical head `h`:

```text
c_R16(t,l,h)
=
Σ_{j in R16} alpha(t,l,h,j) V(l,h,j)
```

The Stage 3C.10 trigger knockdown removes this contribution:

```text
c_R16(t,l,h) → 0
```

after Attention source decomposition and before `W_O`.

Important:

- current query Q/K/V at that layer are left native before the intervention;
- attention probabilities are not recomputed at the intervention layer;
- visual contribution is untouched;
- prompt/Q contribution is untouched;
- non-R16 reasoning positions are untouched;
- downstream layers recompute naturally.

This asks:

> **Does information arriving from recent reasoning tokens into the current query causally create the later retrieval state?**

---

## 10. Upstream Layer Scope

The primary trigger intervention must occur strictly upstream of the frozen routing readout.

### Target A

Routing readout:

```text
layer 29
```

Primary trigger layers:

```text
0–28
```

### Target B

Routing readout:

```text
layer 28
```

Primary trigger layers:

```text
0–27
```

This prevents intervention after the routing quantity has already been computed.

---

## 11. Primary Conditions

For both M and T states:

### N — Native

No trigger intervention.

### R16-KD — Recent reasoning trigger knockdown

Remove R16 current-query contribution over the frozen upstream layer scope.

### E16-KD — Earlier-reasoning temporal control

Remove an equal-width earlier reasoning window:

```text
[t-32, t-17]
```

when available.

If fewer than 32 generated reasoning tokens exist:

```text
mark temporal control unavailable
```

Do not shift the control window post hoc.

### Q-KD — Prompt/question source control

Remove current-query attention-output contribution from the frozen nonvisual prompt/question positions over the same upstream layer scope.

This tests whether retrieval control is more prompt-driven than recent-reasoning-driven.

---

## 12. Why Contribution Deletion Instead of Attention Knockout

The primary trigger intervention removes:

```text
alpha V source contribution
```

rather than renormalizing attention probabilities.

This preserves:

- the native Q/K compatibility at the intervention layer;
- the native attention distribution at that layer;
- all non-target source contributions.

It asks whether the **state transmitted from recent reasoning positions** is needed to construct the later query state.

Do not interpret a null as proof that recent reasoning is irrelevant; compensation can occur downstream.

---

## 13. Primary Routing Readout

Reuse the exact Stage 3C.3 routing implementation.

Primary routing quantity:

```text
Stage 3C.3 frozen RDS
```

at the frozen target coordinate/layer.

If the historical RDS implementation cannot be recovered exactly:

```text
STOP
```

and reconstruct it from Stage 3C.3 artifacts before scientific scoring.

Do not invent a new composite score after seeing Stage 3C.10 results.

Also retain primitive readouts:

```text
target QK cosine
scaled target logit
target ROI attention density
target alphaV norm
post-W_O selected-head norm
```

These are secondary mechanistic readouts.

---

## 14. Primary Behavioral Readout — Current-Query Visual Source Dependence

Routing movement alone is not enough.

The key behavioral quantity is the current query's dependence on target visual evidence.

Reuse the exact Stage 3C.4 `T0` intervention:

```text
current query only
all 36 language layers
all 32 logical heads
target ROI T contribution → 0
```

Define:

```text
VSD_native
=
D_native - D_targetROI_suppressed
```

and under trigger knockdown:

```text
VSD_R16KD
=
D_R16KD - D_R16KD_plus_targetROI_suppressed
```

The primary trigger effect on behavioral visual dependence is:

```text
TE_VSD
=
VSD_native - VSD_R16KD
```

Positive `TE_VSD` means:

> removing recent-reasoning input makes the current query less behaviorally dependent on target visual evidence.

This is the most important Stage 3C.10 readout.

---

## 15. Difference-in-Differences With Mention State

The trigger claim should not rely only on damage at T.

For M and T separately compute:

```text
TE_VSD(T)
TE_VSD(M)
```

Primary retrieval-specific contrast:

```text
DiD_trigger
=
TE_VSD(T) - TE_VSD(M)
```

A positive result means recent reasoning contribution is more important for visual dependence during task-required retrieval than during mention-only alignment.

---

## 16. Irrelevant-ROI Behavioral Control

Repeat the T0-style source suppression with the frozen irrelevant ROI I.

Define:

```text
VSD_I_native
VSD_I_R16KD
```

The recent-R trigger should preferentially affect:

```text
target ROI dependence
```

rather than generic sensitivity to any visual source.

Primary control contrast:

```text
target trigger effect
>
irrelevant-ROI trigger effect
```

---

## 17. Generic Language-Damage Controls

Recent-R knockdown may simply damage computation.

Record:

```text
candidate NLL
current-query residual norm
attention-output norm
entropy
noncausal-head routing readouts
```

Also compare:

```text
R16-KD
vs
E16-KD
vs
Q-KD
```

A retrieval-trigger claim requires target-specific routing/source-dependence effects beyond generic degradation.

---

# PHASE A — MECHANICAL VALIDATION

## 18. Validation Cohort

Use the exact frozen:

```text
7 Stage 3C.3 validation bases
```

Validation covers both targets.

Do not use effect sizes to change the primary R16 or layer scopes.

---

## 19. Validation Requirements

Before primary scoring verify:

1. exact M/T token coordinates;
2. exact Target A/B routing layers;
3. exact Stage 3C.3 RDS reconstruction;
4. exact R16 positions;
5. exact E16 positions;
6. exact prompt/Q positions;
7. source contribution partition reconstructs native attention output within frozen FP32 tolerance;
8. only current-query source contribution is altered;
9. past-token caches are unchanged;
10. visual K/V are unchanged in trigger-only arms;
11. target T0 suppression reproduces Stage 3C.4 semantics;
12. irrelevant-ROI suppression is isolated;
13. deterministic replay;
14. self/no-op intervention exactness;
15. all outputs finite.

---

# PHASE B — PRIMARY TRIGGER NECESSITY

## 20. Primary Questions

On the 24 frozen primary bases:

### Q1

Does `R16-KD` reduce retrieval-state routing at T?

### Q2

Is that routing reduction larger at T than M?

### Q3

Does `R16-KD` reduce behavioral dependence on the target ROI?

### Q4

Is that behavioral reduction larger than:

```text
mention-state effect
earlier-R control
irrelevant-ROI effect
```

A strong trigger claim requires Q3/Q4, not Q1 alone.

---

## 21. Primary Trigger Gate

Classify:

```text
RECENT-REASONING TRIGGER SUPPORTED
```

for a target only if all of the following hold:

1. median T-state RDS decreases under R16-KD;
2. at least 18/24 bases show the expected T-state RDS direction;
3. median `TE_VSD(T) > 0`;
4. at least 18/24 bases show positive `TE_VSD(T)`;
5. `TE_VSD(T) > TE_VSD(M)` robustly;
6. target-ROI trigger effect exceeds irrelevant-ROI trigger effect;
7. effect exceeds E16 temporal control;
8. primary family survives frozen multiple-comparison correction.

Do not declare a behavioral trigger from routing movement alone.

---

## 22. Prompt-Dominant Alternative

If:

```text
Q-KD
```

has a substantially stronger and more robust effect than `R16-KD`, classify:

```text
PROMPT/QUESTION-DOMINANT CONTROL
```

rather than forcing a recent-reasoning trigger story.

---

# PHASE C — TEMPORAL LOCALIZATION

## 23. Gate

Run only if R16-KD shows a robust T-state routing effect or behavioral VSD effect for at least one target.

---

## 24. Frozen Recent Windows

Evaluate cumulative source windows:

```text
R1  = [t-1]
R2  = [t-2, t-1]
R4
R8
R16
```

using the full frozen upstream layer scope.

Primary localization readout:

```text
TE_VSD(T)
```

Secondary:

```text
RDS drop
alphaV drop
```

---

## 25. Temporal Trigger Profile

Report:

```text
R1
R2
R4
R8
R16
```

without forcing monotonicity.

Define descriptively:

```text
k80
=
smallest k whose median TE_VSD
reaches >= 80% of the R16 median effect
```

Only report `k80` if:

- R16 is robust;
- the candidate window has >=75% expected-direction bases.

This is a localization descriptor, not a unique information span.

---

## 26. Relation to Stage 3C.8

Stage 3C.8 found:

```text
late carrier strength is strongly recency-dominant
```

Stage 3C.10 asks whether **retrieval control** is similarly local.

Possible outcomes:

```text
carrier recency and trigger recency match
or
trigger is broader than carrier
```

Either result is informative.

---

# PHASE D — LAYER LOCALIZATION

## 27. Gate

Run if at least one target passes the recent-reasoning trigger gate.

Use the frozen `k80` window if available; otherwise use R16.

---

## 28. Frozen Upstream Layer Bins

Target B-compatible common bins:

```text
L0 = layers 0–7
L1 = layers 8–15
L2 = layers 16–23
L3 = layers 24–27
```

For Target A only, optional:

```text
L4A = layer 28
```

because layer 28 remains upstream of the layer-29 routing readout.

Do not redefine bins after results.

---

## 29. Layer Questions

Determine whether recent reasoning influences retrieval primarily through:

```text
early contextualization
mid-layer reasoning integration
late pre-routing state formation
or distributed depth
```

Primary readout remains:

```text
TE_VSD(T)
```

with RDS as mechanistic support.

---

# PHASE E — QUERY-GEOMETRY MEDIATION

## 30. Why This Phase Matters

A strong recent-R knockdown effect would show:

```text
recent reasoning → retrieval
```

but not yet establish that the effect is mediated through the query geometry that Stage 3C.3 showed can control routing.

Stage 3C.10 therefore performs a same-state mediation rescue.

---

## 31. Native-Q Rescue

Starting from:

```text
R16-KD
```

at the T retrieval state, restore the native current-query Q vectors at the frozen routing layer.

Primary rescue uses:

```text
all 32 logical query heads
```

Recipient:

```text
K/V remain from the R16-KD run
visual source remains native
token history remains identical
```

No donor cache positions are copied.

This is same-token, same-image, same-position mediation.

---

## 32. Native-Q Rescue Readouts

Measure:

```text
RDS
target QK
target ROI attention
alphaV
VSD
evidence score
```

Define:

```text
Q_mediation_VSD
=
VSD_Qrescue - VSD_R16KD
```

A strong result supports:

```text
recent reasoning
→ current-query Q geometry
→ visual retrieval
```

---

## 33. Selected-Head Q Rescue

Secondary only.

Repeat native-Q rescue for the frozen historical causal heads:

### Target A

```text
[11, 6, 15, 12]
```

### Target B

```text
[16, 0, 3, 6]
```

This tests whether the known late causal heads are sufficient to mediate the trigger effect.

Do not require selected-head rescue for the primary trigger claim.

---

## 34. Optional h_pre Upper-Bound Rescue

Run only if:

```text
R16-KD strongly reduces VSD
but
all-head Q rescue restores routing without restoring VSD
```

Then patch the native current-query:

```text
h_pre at the frozen routing layer
```

into the R16-KD run.

This is an upper-bound state rescue.

Interpret cautiously because `h_pre` can contain more than routing information, including prior visual contributions.

Do not use `h_pre` rescue as the primary mediation claim.

---

## 35. Mediation Outcomes

### M1 — Q-mediated trigger

```text
R16-KD lowers routing and VSD
native-Q rescue restores both
```

Strongest result.

### M2 — Routing mediation only

```text
R16-KD lowers routing and VSD
native-Q rescue restores routing
but not VSD
```

Interpretation:

> query geometry is one trigger component, but broader state is behaviorally required.

### M3 — Broad-state mediation

```text
Q rescue weak
h_pre rescue strong
```

Interpretation:

> trigger is integrated in broader current-query state rather than Q alone.

### M4 — No clean mediation

Recent-R knockdown has an effect, but neither Q nor h_pre cleanly rescues it.

Do not force a single mediator.

---

# PHASE F — SECONDARY TRIGGER-CONTENT ANALYSIS

## 36. Gate

Run only after primary trigger results freeze.

This phase is descriptive/secondary.

---

## 37. Recent-Reasoning Token Annotation

For the last 16 reasoning positions before M and T, freeze the Stage 3C.8-compatible labels:

```text
VISUAL_ENTITY
TARGET_ALIGNED
RELATION_OPERATOR
MATH_OPERATOR
NUMERIC_LITERAL
FUNCTION_WORD
DISCOURSE_MARKER
PUNCTUATION
BOUNDARY
OTHER_CONTENT
```

Also record:

```text
distance to current query
reasoning role
```

No attention-based annotation.

---

## 38. Causal Position Scan

For:

```text
last 8 positions
```

individually remove each token position's current-query source contribution over the frozen full upstream layer scope.

Do not scan arbitrary earlier history.

Primary purpose:

> determine whether the trigger effect is sparse or distributed within the recent window.

Because Stage 3C.8 found strong recency effects, position is analyzed before token type.

---

## 39. Token-Type Interpretation

Only after position effects freeze, test whether effect-bearing positions are enriched for:

```text
target-aligned/entity
operator/subgoal
function/discourse
boundary
other
```

Control for distance to current query.

Do not claim a universal trigger token type from raw counts.

---

## 40. Statistical Plan

Primary independent unit:

```text
base_problem_id
```

Analyze Target A and B separately.

Primary family per target:

1. T-state RDS effect of R16-KD;
2. T-state `TE_VSD`;
3. T-vs-M `DiD_trigger`;
4. R16 vs E16 trigger effect;
5. target-ROI vs irrelevant-ROI trigger effect;
6. R16 vs Q-source trigger effect;
7. all-head Q rescue of RDS;
8. all-head Q rescue of VSD.

Use the project's frozen multiple-comparison procedure.

Report:

```text
median
mean
bootstrap 95% CI
positive fraction
paired effect
```

Do not treat M/T events within a base as independent samples.

---

## 41. Main Scientific Outcomes

### O1 — Reasoning-State Retrieval Trigger

If recent-R knockdown reduces target routing and behavioral visual dependence specifically at T:

> **Recent reasoning state causally initiates target-specific visual retrieval.**

### O2 — Query-Mediated Retrieval Trigger

If native Q rescue restores the knockdown effect:

> **Recent reasoning state triggers retrieval by configuring current-query routing geometry.**

This is the strongest Stage 3C.10 outcome.

### O3 — Prompt-Dominant Trigger

If Q/prompt contribution is stronger than recent-R contribution:

> **Retrieval control is driven primarily by persistent prompt/question state rather than immediately preceding reasoning.**

### O4 — Routing-Only Trigger

If routing moves but behavioral visual dependence does not:

> **Recent reasoning causally steers routing, but the tested routing change is behaviorally redundant.**

Do not claim retrieval initiation.

### O5 — Distributed / No Clean Trigger

If no tested source group robustly controls VSD:

> **The retrieval trigger is not cleanly localized to the tested recent-R or prompt contribution pathways.**

This is a valid outcome and should redirect, not terminate, the broader question.

---

## 42. Importance Check After Results

Do not automatically run another trigger experiment.

After Stage 3C.10, ask:

1. Did we establish a new causal link needed by the paper?
2. Does the result materially strengthen the lifecycle story?
3. Is any remaining ambiguity central enough to justify more Stage 3C work?
4. Would sink causality add explanatory value, or merely another side mechanism?
5. Is the paper now better served by moving to Stage 4 multi-evidence experiments?

---

## 43. Decision Branches After Stage 3C.10

### If O1/O2

The Stage 3C causal lifecycle is close to complete:

```text
reasoning demand
→ retrieval trigger
→ query routing
→ visual Value transport
→ local reasoning-side carrier
```

Next review should choose between:

```text
A. Stage 4 multi-evidence retrieval/refresh
B. one final sink-causality experiment
```

Sink should run only if it is necessary for the central mechanism story.

### If O4

Do not overinterpret.

The result would replicate a Stage 3C.3-like distinction:

```text
routing causality != behavioral retrieval necessity
```

Next priority should be broader current-state mediation, not sink.

### If O5

Reconsider whether trigger control is:

```text
longer-history
prompt-state
broad residual
or distributed
```

Do not abandon the retrieval-trigger direction based on one null intervention.

---

## 44. Sink Boundary

Do not manipulate `<|im_start|>` in Stage 3C.10.

After primary results freeze, it is acceptable to overlay the previously measured candidate sink release descriptively.

A sink-causality experiment is justified only if:

```text
confirmed trigger events
systematically show sink release
and
a causal sink mechanism would materially improve the paper's explanation of retrieval routing
```

---

## 45. Relationship to Stage 3C.9R

Stage 3C.9R found:

```text
isolated local checkpoints exist
but
repeated sparse semantic checkpoints are absent in 0/48 bases
```

Stage 3C.10 therefore does **not** assume a prior semantic checkpoint as the trigger.

Instead it tests a broader mechanism:

```text
recent distributed reasoning state
→ next-query retrieval configuration
```

This is deliberately consistent with the Stage 3C.9R negative result.

---

## 46. Output Structure

```text
outputs/stage3c10/
  config/
    stage3c10_config.json
    frozen_targets.json
    frozen_mt_states.json
    trigger_source_groups.json
    routing_readout.json
    vsd_definition.json
    primary_family.json

  cohort/
    validation_manifest.jsonl
    primary_manifest.jsonl

  annotations/
    optional_recent_token_annotations.jsonl

  audit/
    mt_coordinate_audit.json
    rds_reconstruction.json
    source_partition_audit.json
    r16_position_audit.json
    e16_position_audit.json
    prompt_source_audit.json
    current_query_selectivity.json
    t0_target_suppression_audit.json
    irrelevant_roi_audit.json
    q_patch_audit.json
    self_patch_validation.json
    deterministic_replay.json

  phase_b_primary/
    native_scores.jsonl
    r16_knockdown.jsonl
    e16_control.jsonl
    q_source_control.jsonl
    target_vsd.jsonl
    irrelevant_vsd.jsonl
    primary_statistics.json

  phase_c_temporal/
    r1.jsonl
    r2.jsonl
    r4.jsonl
    r8.jsonl
    r16.jsonl
    temporal_profile.json
    k80.json

  phase_d_layers/
    layer_bin_results.jsonl
    layer_profile.json

  phase_e_mediation/
    all_head_q_rescue.jsonl
    selected_head_q_rescue.jsonl
    optional_hpre_rescue.jsonl
    mediation_statistics.json

  phase_f_secondary/
    recent_position_scan.jsonl
    token_type_analysis.json
    sink_overlay_descriptive.json

  analysis/
    retrieval_trigger_summary.json
    routing_vs_behavior.json
    target_heterogeneity.json
    paper_claim_assessment.json
    figures/

  summaries/
    stage3c10_summary.md
    stage3c10_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite prior Stage 3C artifacts.

---

## 47. Required Figures

At minimum:

1. native M vs T RDS replication;
2. R16-KD effect on T-state RDS;
3. R16-KD effect on target visual-source dependence;
4. T-vs-M trigger difference-in-differences;
5. target-ROI vs irrelevant-ROI trigger effect;
6. R16 vs E16 temporal control;
7. R16 vs Q-source control;
8. R1/R2/R4/R8/R16 temporal trigger profile;
9. layer-bin trigger profile;
10. RDS drop vs VSD drop;
11. all-head Q rescue of routing;
12. all-head Q rescue of VSD;
13. selected-head vs all-head Q rescue;
14. Target A vs Target B mechanism;
15. optional recent-token position effects;
16. final causal-chain diagram with supported/unsupported arrows.

---

## 48. Acceptance Criteria

Stage 3C.10 technically passes if:

1. exact 31-base historical M/T cohort is reused;
2. exact 7 validation / 24 primary split is preserved;
3. exact M/T coordinates are loaded from frozen artifacts;
4. exact Stage 3C.3 RDS implementation is reused;
5. R16/E16/Q source groups are frozen before primary scoring;
6. trigger intervention alters only current-query source contribution;
7. upstream layer scopes are frozen before scoring;
8. current-query target VSD uses the exact Stage 3C.4 T0 semantics;
9. irrelevant-ROI control is included;
10. M-state control is included;
11. generic language-damage controls are included;
12. routing-only change cannot satisfy the behavioral trigger claim;
13. temporal localization runs only after its gate;
14. layer localization runs only after its gate;
15. native-Q rescue uses same-token/same-image state;
16. h_pre rescue, if run, is labeled upper-bound/secondary;
17. Target A and B remain separately interpreted;
18. no attention-based cohort or token selection occurs;
19. no sink intervention or Stage 4 experiment is started;
20. exactly one next-stage recommendation is produced.

Technical PASS does not require a positive retrieval-trigger result.

---

## 49. Stop Condition

After:

```text
mechanical validation
→ primary R16 trigger test
→ M / earlier-R / irrelevant-ROI / Q controls
→ gated temporal localization
→ gated layer localization
→ Q-geometry mediation
→ secondary recent-token analysis if eligible
→ paper-level claim assessment
→ exactly one recommendation
```

**STOP.**

Do not start:

```text
sink causality
broader-history trigger search
new trigger cohort construction
Stage 4
failure analysis
```

Return the complete Stage 3C.10 result for review.

The next step must be chosen by the paper-level value of the result, not by a precommitted desire to continue Stage 3C.
