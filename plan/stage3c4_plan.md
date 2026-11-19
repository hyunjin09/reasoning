# Stage 3C.4 Plan — Spatiotemporal Redundancy Localization of Visual Evidence

## 0. Purpose

Stage 3C.4 follows the Stage 3C.3-R result:

> **Removing the current-position target-ROI contribution from the selected causal heads, from all heads at the target layer, and even from all heads across W4 (layers 28–29) leaves the evidence preference almost unchanged.**

Stage 3C.3-R therefore rejected a simple saturation explanation and produced:

```text
O4 — Broad Robustness Beyond W4
```

Key observations:

```text
selected-head target contribution removed:
median retained evidence ≈ 0.997

all heads across W4 target contribution removed:
Target A retained ≈ 0.986
Target B retained ≈ 0.991
```

The Stage 3C.3 query intervention also drove the selected-head target contribution close to zero:

```text
Target A projected effective gain ≈ 0.0014
Target B projected effective gain ≈ 0.0059
```

yet evidence preference remained stable.

Therefore the next scientific question is:

\[
\boxed{
\text{Where is the redundant evidence support distributed across layer depth and reasoning time?}
}
\]

Stage 3C.4 distinguishes:

1. **same-time layer redundancy**
2. **earlier-time retrieval / temporal redundancy**
3. **broad spatiotemporal redundancy**
4. **evidence already carried by nonvisual state before the tested window**

This stage does not analyze sink causality yet.

The planned sink stage is deferred until the behaviorally necessary visual support window is better localized.

---

## 1. Scientific Handoff

### Stage 3B.2

With prior reasoning history fixed, switching future all-visual K/V identity at `E_d-1` or `E_d` strongly changed upcoming evidence identity.

Therefore:

> **late visual-source identity remains causally important.**

This rules out the trivial story that all evidence was fully stored long before the late decision and late vision was irrelevant.

### Stage 3B.7-R

The Stage 3A edited ROI was shown to be the dominant visual source for the localized W4 Value pathway.

### Stage 3C.3

Query-side substitution strongly changed:

```text
QK_T
attention_T
alphaV_T
```

but not reciprocal evidence preference.

### Stage 3C.3-R

Directly scaling/removing the same target-ROI contribution showed:

```text
selected-path removal ≠ behavioral collapse
W4-wide removal ≠ behavioral collapse
```

Thus the local W4 target-ROI pathway is:

```text
causally steerable
but not uniquely necessary
```

The unresolved question is:

> **Is evidence redundantly available in other layers at the same reasoning time, or was it already retrieved at earlier reasoning steps and carried forward?**

---

## 2. Core Hypotheses

### H1 — Same-time layer redundancy

At the current evidence-decision query, other language layers outside W4 directly retrieve enough target-ROI signal to preserve the evidence decision.

Prediction:

```text
W4 removal: little effect
broader layer removal at same time: increasing evidence loss
```

### H2 — Temporal redundancy / earlier retrieval

The model retrieved the evidence at one or more earlier reasoning queries.

Prediction:

```text
current-time all-layer removal: weak effect
backward-expanding temporal removal: increasing evidence loss
```

### H3 — Spatiotemporal redundancy

Evidence is repeatedly retrieved through multiple layers across several reasoning steps.

Prediction:

> substantial behavioral loss appears only when both layer scope and temporal scope become broad.

### H4 — Earlier nonvisual storage dominates

Even broad late target-ROI suppression leaves evidence intact.

Prediction:

> evidence has already been carried into Q/R/current residual before the tested visual-suppression window.

---

## 3. Frozen Targets

Reuse the exact two targets:

### Target A

```text
decision coordinate: E_d
W4 target layer: 29
historical causal heads: [11, 6, 15, 12]
```

### Target B

```text
decision coordinate: E_d - 1
W4 target layer: 28
historical causal heads: [16, 0, 3, 6]
```

Target ROI `T` is the exact frozen Stage 3B.7-R causal edit ROI.

Do not redefine T from attention or Stage 3C.4 effects.

---

## 4. Primary Cohort

Reuse the exact:

```text
24 Stage 3C.3 / Stage 3C.3-R primary base_problem_ids
```

unless a base fails a new mechanical audit unrelated to scientific outcome.

Minimum:

```text
20 valid base_problem_ids
```

Primary statistical unit:

```text
base_problem_id
```

No exclusion may depend on layer/window suppression results.

---

## 5. Core Intervention Object

For query time `t`, language layer `l`, and logical head `h`:

```text
c_T(t,l,h)
=
sum_{j in target ROI T}
alpha(t,l,h,j) * V(l,h,j)
```

The intervention removes only this target-ROI contribution:

```text
c_T → 0
```

Keep fixed at the directly intervened computation:

```text
Q
K
V source vectors
attention probabilities
all non-target source contributions
```

Then allow downstream computation to recompute naturally.

This is the exact Stage 3C.3-R causal object extended across layer and time.

---

## 6. Mandatory Mechanical Audit

Reuse the validated Stage 3C.3-R:

```text
pre-W_O contribution partition
FP32 partition arithmetic
source-isolation semantics
```

Before primary scoring verify:

1. exact target ROI token indices;
2. exact temporal query indices;
3. exact layer scope;
4. exact all-head enumeration;
5. exact native reconstruction;
6. `c_T=0` removes only target contribution;
7. attention/Q/K/V unchanged at the direct intervention site;
8. non-target source contributions unchanged;
9. multi-layer composition is correct;
10. multi-query composition is correct;
11. no earlier-than-window query is altered;
12. deterministic repeatability;
13. finite scores;
14. no donor hidden/KV state is patched.

Create:

```text
outputs/stage3c4/audit/
  contribution_definition.json
  layer_scope_audit.json
  temporal_scope_audit.json
  source_isolation.json
  reconstruction_validation.json
  reproducibility.json
```

---

## 7. Validation Cohort

Use:

```text
6–8 disjoint validation bases
```

if available.

Validate:

- single-layer removal;
- multi-layer removal;
- current-only removal;
- multi-query removal;
- exact temporal boundary;
- exact non-window invariance;
- deterministic repeats.

Do not tune scopes based on behavioral effects.

---

# PHASE A — SAME-TIME LAYER REDUNDANCY

## 8. Question

> **At the current retrieval/evidence query, how broadly across layer depth is target-ROI support distributed?**

Temporal scope is fixed to:

```text
current query only
```

No earlier query is altered.

---

## 9. Frozen Layer Scopes

Use nested scopes:

### L0 — W4

```text
layers 28–29
```

Historical Stage 3C.3-R reference.

### L1 — W4 + W5

```text
layers 28–33
```

### L2 — Late layers

```text
layers 24–35
```

### L3 — Mid + late

```text
layers 16–35
```

### L4 — All language layers

```text
layers 0–35
```

At every included layer:

```text
all logical query heads
target ROI contribution only
c_T = 0
```

Do not change the scope family after scoring.

---

## 10. Phase-A Readout

Primary behavioral readout:

```text
frozen evidence-preference score
```

For each scope `Lk`:

```text
E_Lk
```

Descriptive retention:

```text
LR_k = E_Lk / E_native
```

Do not clip.

Primary inference uses unnormalized evidence changes.

---

## 11. Phase-A Outcome Categories

### A1 — W5 compensation

If:

```text
L0 robust
L1 strongly degrades
```

then W5 provides major same-time redundancy.

### A2 — Distributed late-layer redundancy

If:

```text
L1 robust
L2 strongly degrades
```

then target support is distributed across a wider late-layer set.

### A3 — Broad layer redundancy

If only:

```text
L3 or L4
```

causes major loss.

### A4 — Same-time target retrieval not necessary

If:

```text
L4 current-only removal
```

still preserves evidence substantially.

Then the explanation shifts toward temporal redundancy / earlier storage.

---

# PHASE B — TEMPORAL REDUNDANCY

## 12. Question

> **How far back in reasoning time must direct target-ROI contribution be removed before evidence preference fails?**

Primary layer scope:

```text
all language layers 0–35
```

This prevents same-time compensation across layers.

---

## 13. Frozen Temporal Windows

For current retrieval coordinate `t*`:

```text
T0: [t*, t*]
T1: [t*-1, t*]
T2: [t*-2, t*]
T4: [t*-4, t*]
T8: [t*-8, t*]
T16: [t*-16, t*]
```

Use only windows supported by available history.

Do not substitute normalized positions for missing exact history.

Record N per window.

---

## 14. Temporal Intervention

For every query `t` in the window:

```text
all 36 language layers
all logical heads
target ROI T contribution
c_T(t,l,h) = 0
```

All queries before the window remain native.

Teacher-forced token identities remain frozen.

Downstream states inside the window may change naturally as a consequence of the intervention.

---

## 15. Interpretation of This Intervention

This is not:

```text
visual K/V deletion
```

and not:

```text
full visual attention knockout
```

It removes only the **target ROI Value contribution** across all layers for the specified reasoning-time window.

Thus it asks:

> can the evidence decision survive when the model receives no target-ROI contribution during the final N reasoning queries?

---

## 16. Phase-B Readout

For each window:

```text
E_Tw
```

Primary effect:

```text
D_native - D_suppressed
```

Descriptive retention:

```text
TR_w = E_Tw / E_native
```

Report:

- median;
- mean;
- bootstrap 95% CI;
- fraction retaining >=80%;
- fraction retaining >=50%.

---

## 17. Temporal Necessity Descriptives

Define:

```text
w_80
```

= shortest tested backward window whose median retained evidence falls below 0.80.

```text
w_50
```

= shortest tested backward window whose median retained evidence falls below 0.50.

Do not infer an exact token boundary from sparse windows.

---

## 18. Phase-B Outcome Categories

### B1 — Very-late temporal redundancy

If:

```text
T0 robust
T1/T2 strongly degrade
```

then evidence is redundantly supplied over the last few steps.

### B2 — Multi-step retrieval accumulation

If:

```text
T0/T1/T2 robust
T4/T8 strongly degrade
```

then evidence is accumulated or repeatedly refreshed over several tokens.

### B3 — Long late-history support

If only:

```text
T16
```

causes major loss.

### B4 — Pre-window storage

If even:

```text
T16 all-layer target suppression
```

preserves evidence.

Then evidence was likely retrieved before `t*-16` or carried by nonvisual state.

This should motivate later Q/R/current-state carrier analysis.

---

# PHASE C — SPATIOTEMPORAL INTERACTION

## 19. Purpose

If both layer and temporal redundancy appear, test a small fixed interaction family.

Run only after Phase A/B primary results freeze.

---

## 20. Frozen Interaction Cells

```text
C1: layers 24–35 × last 4 queries
C2: layers 24–35 × last 8 queries
C3: layers 0–35 × last 4 queries
C4: layers 0–35 × last 8 queries
```

If history is unavailable, record the cell as unavailable.

Do not add cells post hoc.

---

## 21. Interaction Interpretation

### C-Layer-Dominant

Broad same-time layer removal causes collapse; temporal expansion adds little.

### C-Time-Dominant

All-layer current removal is weak, but backward expansion causes collapse.

### C-Spatiotemporal

Only broad layer × multi-token suppression causes strong evidence loss.

Interpretation:

> target evidence is redundantly refreshed across both layer depth and reasoning time.

---

# 22. Target-Specificity Controls

For reduced scopes only, run:

```text
all layers × current query
all layers × last 4 queries
```

for:

```text
M = mention ROI
I = irrelevant matched ROI
```

Expected:

```text
T suppression >> M/I suppression
```

if the effect is evidence-specific.

Do not run the full layer/time grid for controls unless compute is trivial.

---

# 23. Stage 3B.2 Comparison

Compare descriptively with Stage 3B.2 future visual-source switching.

Important distinction:

```text
Stage 3B.2:
replace future visual semantic identity

Stage 3C.4:
remove only target-ROI Value contribution
```

If broad target suppression reproduces late sensitivity, the results converge.

If broad suppression remains weak while semantic switching is strong:

> semantic opposition is more powerful than deletion because redundant native evidence remains elsewhere.

---

# 24. Optional Nonvisual-State Readout

Only after primary suppression results freeze, optionally record at the final coordinate:

```text
h_pre
h_post_attn
final evidence logits
```

under each window.

Question:

> does evidence information remain present in nonvisual state after target visual contribution has been blocked for several queries?

Do not patch these states in Stage 3C.4.

---

# 25. Primary Statistical Family

Primary unit:

```text
base_problem_id
```

Frozen tests:

### Phase A

1. L1 vs L0
2. L2 vs L0
3. L3 vs L0
4. L4 vs L0
5. monotonic layer-scope trend

### Phase B

6. T1 vs T0
7. T2 vs T0
8. T4 vs T0
9. T8 vs T0
10. T16 vs T0
11. monotonic temporal-window trend

### Controls

12. T vs M suppression
13. T vs I suppression

### Phase C

14. frozen layer × time interaction summary

Use Holm correction across the frozen confirmatory family.

Unnormalized evidence effects are primary.

---

# 26. Main Scientific Outcomes

## O1 — Layer Redundancy

Evidence fails once enough same-time layers lose target contribution.

Conclusion:

> **The evidence is redundantly retrievable across layer depth at the same reasoning step.**

## O2 — Temporal Redundancy

Current all-layer suppression is weak, but backward-expanding suppression causes evidence failure.

Conclusion:

> **The model has already acquired evidence in one or more earlier reasoning steps.**

## O3 — Spatiotemporal Redundancy

Only broad layer and temporal suppression causes collapse.

Conclusion:

> **Evidence is repeatedly and redundantly supplied across both depth and reasoning time.**

## O4 — Earlier Nonvisual Storage

Even broad all-layer late-window target suppression preserves evidence.

Conclusion:

> **The decisive evidence state is already available before the tested window or stored in nonvisual carriers.**

This should trigger Q/R/current-state carrier analysis.

---

# 27. Scientific Boundary

Stage 3C.4 does not establish:

- which Q/R token stores evidence;
- one exact earlier retrieval token;
- retrieval-trigger state;
- sink causal function;
- vision-encoder origin;
- multi-evidence refresh;
- failure mechanisms.

It localizes **necessity across layer and reasoning time**, not a unique memory trace.

---

# 28. Sink-Causality Deferral

Do not manipulate `<|im_start|>` or any sink-like position.

The candidate-sink question should be revisited only after identifying the behaviorally necessary visual-support regime.

Provisionally reserve:

```text
Stage 3C.5 — Attention Sink Causality
```

Questions for that later stage:

- does sink release feed a behaviorally necessary retrieval window?
- does reducing sink mass help only when correct routing is active?
- where does sink probability redistribute?

---

# 29. Decision After Stage 3C.4

Recommend exactly one next direction.

## GO — Nonvisual Carrier Localization

Use if broad temporal suppression indicates evidence is already stored before the tested window.

Next:

```text
Q vs previous reasoning R vs current residual
```

## GO — Behaviorally Necessary Visual Window Mechanism

Use if a clear layer/time necessity window is found.

## GO — Stage 3C.5 Attention Sink Causality

Use only if the necessary retrieval regime is sufficiently localized and sink-release dynamics overlap it.

## REDIRECT — Suppression Semantics Inconclusive

Use if broad suppression causes mechanical/off-manifold failure or target-specificity controls fail.

Do not automatically broaden beyond all layers / 16-token scope.

---

# 30. Output Structure

```text
outputs/stage3c4/
  config/
    stage3c4_config.json
    frozen_targets.json
    layer_scopes.json
    temporal_windows.json
    interaction_cells.json
    primary_family.json

  cohort/
    validation_manifest.jsonl
    primary_manifest.jsonl
    exclusions.jsonl
    temporal_availability.jsonl

  audit/
    contribution_definition.json
    layer_scope_audit.json
    temporal_scope_audit.json
    source_isolation.json
    reconstruction_validation.json
    reproducibility.json

  phase_a_layer/
    per_problem_layer_scope_results.jsonl
    layer_scope_statistics.json

  phase_b_time/
    per_problem_temporal_results.jsonl
    temporal_statistics.json
    temporal_necessity_summary.json

  phase_c_interaction/
    interaction_results.jsonl
    interaction_statistics.json

  controls/
    mention_suppression_results.jsonl
    irrelevant_suppression_results.jsonl

  secondary/
    stage3b2_comparison.json
    optional_state_readout.jsonl

  analysis/
    layer_redundancy_analysis.json
    temporal_redundancy_analysis.json
    spatiotemporal_classification.json
    target_specificity_analysis.json
    figures/

  summaries/
    stage3c4_summary.md
    stage3c4_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3C.3-R or earlier artifacts.

---

# 31. Required Figures

At minimum:

1. evidence retention vs layer scope for Target A;
2. same for Target B;
3. per-base layer-scope curves;
4. evidence retention vs temporal window for Target A;
5. same for Target B;
6. per-base temporal curves;
7. layer × time suppression heatmap;
8. W4-only vs all-layer current suppression;
9. target vs mention/irrelevant suppression;
10. Stage 3B.2 source-switch vs Stage 3C.4 suppression timing comparison;
11. `w_80` summary;
12. `w_50` summary;
13. final spatiotemporal phenotype summary.

---

# 32. Acceptance Criteria

Stage 3C.4 technically passes if:

1. exact Stage 3C.3-R contribution semantics are reused;
2. exact target ROI definitions remain frozen;
3. exact two target coordinates remain frozen;
4. at least 20 primary bases remain valid;
5. layer scopes are frozen before scoring;
6. temporal windows are frozen before scoring;
7. all-layer enumeration is exact;
8. only target ROI contribution is removed;
9. Q/K/V and attention are unchanged at the direct intervention site;
10. queries before the temporal window remain untouched;
11. downstream propagation is allowed naturally;
12. target/mention/irrelevant control scopes are frozen;
13. current-only W4 result reproduces Stage 3C.3-R;
14. all current-only layer scopes are completed;
15. all available temporal windows are completed;
16. `base_problem_id` remains the statistical unit;
17. unnormalized evidence effects are primary;
18. no state patching or sink manipulation is run;
19. no broader-than-all-layer / earlier-than-16-token rescue is automatically started;
20. exactly one next-stage recommendation is produced.

Technical PASS does not require evidence collapse.

---

# 33. Stop Condition

After:

- mechanical validation;
- same-time nested layer suppression;
- all-layer backward temporal suppression;
- frozen interaction cells;
- target-specificity controls;
- Stage 3B.2 comparison;
- final spatiotemporal classification;
- exactly one recommendation;

**STOP.**

Do not start:

- Q/R carrier patching;
- h_pre intervention;
- sink knockout or redistribution;
- temporal windows earlier than `t*-16`;
- Stage 4 multi-evidence refresh;
- failure analysis.

Return the complete Stage 3C.4 results for review.

The next stage must be chosen only after jointly considering Stage 3C.4 with all prior Stage 2A–3C.3-R evidence.
