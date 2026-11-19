# Stage 3C.3-R Plan — Target-ROI Signal Gain: Saturation vs Redundancy

## 0. Purpose

Stage 3C.3 produced a clear dissociation:

> **Query-side intervention strongly and bidirectionally changed T-vs-M routing and target αV influx, but did not reciprocally control evidence preference.**

Technical result:

```text
routing causality: YES
behavioral evidence control: NO
```

Stage 3C.3-R asks why.

The two primary hypotheses are:

### H1 — Saturation / plateau

The selected causal target-ROI signal is genuinely behaviorally relevant, but the native signal is already above the amount required for the evidence decision. Large routing reductions may therefore leave enough signal to preserve the output.

### H2 — Redundancy

The selected target-ROI path is only one of several parallel routes. Even if its contribution is strongly reduced or eliminated, other heads/layers/states may preserve the evidence decision.

Primary question:

> **How much target-ROI Value contribution is actually required for the evidence decision?**

Gated secondary question:

> **If the selected path can be zeroed without behavioral loss, where is the redundant support within the already-localized W4 region?**

Do not manipulate the candidate attention sink in this stage.

---

## 1. Scientific Handoff

### Stage 3B.7-R

For the two frozen W4 targets:

```text
K-only semantic swap ≈ 0
V-only semantic swap ≈ full semantic effect
```

Thus evidence identity is carried primarily through the target-ROI Value path.

### Stage 3B.8

Interpolating semantic Value identity produced graded evidence changes.

Therefore:

> the semantic content encoded in the Value path is causally meaningful.

### Stage 3C.3

Changing selected-head query routing caused:

```text
QK_T changes
attention_T changes
αV_T changes
```

but not reciprocal evidence-preference changes.

This creates a crucial distinction:

```text
semantic identity of Value
vs
magnitude of routed Value contribution
```

Stage 3C.3-R directly tests that distinction.

---

## 2. Frozen Causal Targets

Reuse exactly:

### Target A

```text
coordinate: E_d
layer: 29
heads: [11, 6, 15, 12]
ROI: frozen task-required target ROI T
```

### Target B

```text
coordinate: E_d - 1
layer: 28
heads: [16, 0, 3, 6]
ROI: frozen task-required target ROI T
```

Do not add new heads or layers based on Stage 3C.3-R outcomes.

---

## 3. Primary Cohort

Prefer the exact Stage 3C.3 primary cohort:

```text
24 independent base_problem_ids
```

If a small number fail the new contribution-decomposition audit, use the maximal frozen valid subset.

Minimum primary N:

```text
20
```

No exclusion may depend on signal-gain or evidence outcome.

Primary statistical unit:

```text
base_problem_id
```

---

## 4. Core Representation

For causal head `h` at the frozen coordinate:

```text
z_h = c_T,h + c_rest,h
```

where:

```text
c_T,h = sum_{j in target ROI T} alpha_hj * V_hj
c_rest,h = sum_{j not in T} alpha_hj * V_hj
```

The intervention changes only the target-ROI contribution:

```text
z_h(lambda) = lambda * c_T,h + c_rest,h
```

Keep unchanged:

```text
Q
K
V vectors
attention probabilities
non-target source contributions
all non-target heads
```

Primary λ grid:

```text
1.00
0.75
0.50
0.25
0.10
0.00
```

Optional strengthening, secondary only after primary results freeze:

```text
1.25
1.50
```

---

## 5. Why This Is Different From Prior Stages

Stage 3B.8 changed semantic identity:

```text
V_C + lambda * (V_O - V_C)
```

Stage 3C.3-R instead changes the strength of the same semantic contribution:

```text
lambda * c_T
```

Thus:

```text
Stage 3B.8:
what content is carried?

Stage 3C.3-R:
how much of that same content is required?
```

This distinction is central to interpreting attention magnitude.

---

## 6. Mandatory Mechanical Audit

Before primary scoring verify:

1. exact target ROI token set;
2. exact selected causal heads;
3. exact pre-`W_O` head-output decomposition;
4. exact reconstruction:
   ```text
   c_T + c_rest = native head output
   ```
5. `lambda=1` reproduces native logits exactly or within frozen BF16 tolerance;
6. `lambda=0` removes only target-ROI contribution;
7. non-target visual contribution is unchanged;
8. mention ROI M contribution is unchanged;
9. irrelevant ROI I contribution is unchanged;
10. all other heads are unchanged;
11. Q/K/V and attention probabilities remain unchanged;
12. deterministic repeatability passes;
13. all outputs are finite.

Create:

```text
outputs/stage3c3r/audit/
  contribution_partition.json
  lambda_endpoint_validation.json
  head_selectivity.json
  source_invariance.json
  attention_invariance.json
  reproducibility.json
```

---

## 7. Validation Cohort

Use:

```text
6–8 disjoint validation bases
```

if available.

Validation must cover:

- λ endpoints;
- monotonic contribution scaling;
- no attention drift;
- exact source isolation;
- self/native reconstruction;
- deterministic repeatability.

Do not tune the λ grid using validation effect magnitude.

---

# PHASE A — SELECTED-HEAD TARGET-SIGNAL DOSE RESPONSE

## 8. Primary Intervention

For each frozen target/base:

```text
selected causal heads only
target ROI contribution only
```

scale by λ.

All downstream computation recomputes naturally:

```text
W_O
→ residual
→ MLP
→ later layers
```

---

## 9. Phase-A Readouts

For each λ collect:

### Direct signal

```text
target contribution norm
post-W_O target contribution norm
```

### Behavioral evidence

Use the frozen evidence-preference score.

### Optional downstream state

```text
h_post_attn readout
final evidence logits
```

Attention/QK need not be reinterpreted because they are fixed by construction, but exact invariance must be audited.

---

## 10. Primary Dose-Response Quantity

For each base:

```text
E(lambda) = evidence-preference score under target-signal gain lambda
```

Descriptive normalization:

```text
ER(lambda) = E(lambda) / E(1.0)
```

Do not clip.

Do not interpret ER as an additive causal fraction.

Primary analysis uses unnormalized evidence scores.

---

## 11. Saturation / Threshold Signatures

### S1 — Strong saturation / plateau

Evidence remains near-native over substantial attenuation:

```text
1.0 → 0.75 → 0.5 → 0.25
```

and collapses only near:

```text
0.10 or 0
```

Interpretation:

> native target signal exceeds the amount behaviorally required.

### S2 — Smooth gain dependence

Evidence degrades progressively with λ.

Interpretation:

> target contribution magnitude continuously controls evidence strength.

### S3 — No selected-path necessity

Even:

```text
lambda = 0
```

leaves evidence substantially intact.

Interpretation:

> selected-head target contribution is not behaviorally necessary by itself; redundancy is likely.

---

## 12. Threshold Descriptives

For bases with monotonic or approximately monotonic curves define:

```text
lambda_80
```

= smallest tested λ retaining at least 80% of native evidence preference.

```text
lambda_50
```

= smallest tested λ retaining at least 50%.

These are descriptive.

Do not interpolate aggressively between sparse λ points.

---

## 13. Direct Comparison to Stage 3C.3 Query Patch

For each base recover the Stage 3C.3 query-patched target contribution:

```text
c_T_query_patch
```

Compute descriptive effective gain:

```text
lambda_query_norm =
||c_T_query_patch|| / ||c_T_native||
```

Also compute a direction-aware projection if stored vectors permit:

```text
lambda_query_proj =
<c_T_query_patch, c_T_native> / ||c_T_native||^2
```

Prefer projection-aware interpretation where direction changes.

Overlay these operating points on the new dose-response curves.

Key question:

> Did the Stage 3C.3 query intervention reduce the target signal below the empirically observed behavioral transition region?

---

## 14. Saturation Explanation Rule

Stage 3C.3 behavioral null is considered **consistent with saturation** if:

1. selected-path dose curve shows a clear plateau;
2. evidence changes only below a lower λ region;
3. most Stage 3C.3 query-patch operating points remain above that transition;
4. `lambda=0` causes substantial behavioral loss in at least one or both targets.

Use the phrase:

```text
saturation / plateau-like robustness
```

unless a genuinely sharp threshold is observed.

---

## 15. Target-Specificity Controls

Run the same contribution scaling for:

```text
M = mention ROI
I = matched irrelevant ROI
```

at the selected causal heads.

Frozen control λ levels:

```text
1.0
0.5
0.0
```

Expected:

```text
attenuating T affects evidence more than attenuating M or I
```

Do not redefine T from these outcomes.

---

## 16. Frozen Noncausal-Head Control

At the same target ROI T, run:

```text
lambda = 1.0
lambda = 0.5
lambda = 0.0
```

for the frozen Stage 3C.3 noncausal-head sets.

This tests whether simple removal of any large ROI contribution perturbs behavior.

---

## 17. Gate to Redundancy Analysis

Proceed to Phase B only if selected-head:

```text
lambda = 0
```

leaves substantial evidence preference intact.

Prospective gate:

- median retained evidence >= 0.50 of native, OR
- at least 40% of bases retain >= 0.80 of native.

If the gate fails:

**STOP after Phase A.**

Do not run redundancy expansion unnecessarily.

---

# PHASE B — PROSPECTIVE NESTED REDUNDANCY LOCALIZATION

## 18. Purpose

If selected-head target contribution can be removed with limited behavioral loss, determine whether nearby parallel pathways preserve evidence.

The full nested family must be frozen before Phase-A primary scoring.

Do not add scopes after seeing `lambda=0`.

---

## 19. Frozen Nested Scopes

### R0 — Selected causal head set, current layer

Already tested in Phase A.

### R1 — All heads, same layer, target ROI contribution

Scale/remove target ROI contribution from all logical query heads at the same frozen layer.

### R2 — Frozen causal head identities across W4

Remove target ROI contribution from the frozen causal head identities across:

```text
layers 28–29
```

where mechanically meaningful.

Audit head identity separately per layer.

### R3 — All heads across W4, target ROI contribution

Remove target ROI contribution from all heads across:

```text
layers 28–29
```

This is the broadest allowed scope in Stage 3C.3-R.

Do not expand beyond W4.

---

## 20. Redundancy Gain Levels

For R1–R3 use:

```text
lambda = 1.0
lambda = 0.5
lambda = 0.0
```

Do not automatically run the full six-point curve for every broad scope.

---

## 21. Redundancy Interpretation

### R-Head-Parallel

If:

```text
R0 lambda=0 weak effect
R1 lambda=0 strong effect
```

then other same-layer heads compensate.

### R-Cross-Layer

If:

```text
R1 weak
R2 or R3 strong
```

then nearby W4 layers provide redundant support.

### R-Broad-Robustness

If even:

```text
R3 lambda=0
```

leaves evidence largely intact, redundancy likely lies outside the tested current-W4 target-ROI contribution family.

Possible sources include:

- earlier visual retrieval;
- language-side residual state;
- other layers;
- downstream robustness.

Do not chase these automatically.

---

## 22. Behavioral Readout for Redundancy

Use the same frozen evidence-preference score.

Secondary matched-seed rollout may be run only for:

```text
R0 lambda=0
R3 lambda=0
```

if primary teacher-forced results are stable.

Do not interpret one-seed proportions as repeated-sampling probabilities.

---

## 23. Optional Evidence-Direction Projection

As a secondary audit, if the frozen Stage 3B.8/3B.9 evidence-relevant Value geometry can be reused without learning from this cohort, measure:

```text
projection of c_T(lambda)
onto the frozen evidence-relevant direction/subspace
```

This may distinguish:

```text
large vector norm
vs
evidence-relevant component
```

Do not fit a new subspace on the Stage 3C.3-R primary cohort.

---

# 24. Primary Statistical Family

Primary unit:

```text
base_problem_id
```

Frozen tests:

### Phase A

1. T λ=.75 vs λ=1 evidence change
2. T λ=.50 vs λ=1
3. T λ=.25 vs λ=1
4. T λ=.10 vs λ=1
5. T λ=0 vs λ=1
6. monotonic trend
7. T vs M attenuation specificity
8. T vs I attenuation specificity
9. causal-head vs noncausal-head attenuation specificity
10. Stage 3C.3 query-patch operating-point consistency with dose curve

### Phase B, gated

11. R1 λ=0 vs R0 λ=0
12. R2 λ=0 vs R0 λ=0
13. R3 λ=0 vs R0 λ=0

Use Holm correction across the frozen confirmatory family where applicable.

Report:

- mean;
- median;
- bootstrap 95% CI;
- positive-direction fraction;
- unnormalized evidence effects.

---

# 25. Primary Scientific Outcomes

## O1 — Saturated Target-Signal Use

If target signal can be attenuated substantially before behavior changes, but λ=0 eventually causes strong evidence loss:

> **The evidence decision is robust to large changes in target-ROI contribution magnitude and operates in a saturated/plateau-like regime.**

This would explain why Stage 3C.3 strongly changed routing and αV without changing evidence preference.

## O2 — Continuous Gain Control

If evidence degrades smoothly with target signal:

> **Target-ROI contribution magnitude continuously controls evidence strength.**

Then Stage 3C.3 null requires another explanation, such as state/direction mismatch.

## O3 — Redundant Parallel Support

If selected-head λ=0 is weak but broader same-layer/W4 removal is strong:

> **The localized visual evidence pathway is behaviorally redundant across nearby heads/layers.**

## O4 — Broad Robustness Beyond W4

If even all-head W4 target contribution removal has little effect:

> **The evidence decision is supported by pathways or stored states outside the currently localized W4 target-contribution family.**

Do not infer which path without a new stage.

---

# 26. Relation to Attention Magnitude

If saturation is supported:

> **Attention/Value magnitude above a sufficiency regime need not scale with behavioral importance.**

If redundancy is supported:

> **Attention to one causal path may vary substantially while parallel routes preserve the same evidence decision.**

Either result helps explain why raw attention magnitude is not a universal quantitative proxy for causal influence.

---

# 27. Candidate Sink Boundary

Do not manipulate:

```text
<|im_start|>
```

or any sink-like position.

Stage 3C.4 sink causality remains deferred until Stage 3C.3-R is interpreted.

---

# 28. What Stage 3C.3-R May Establish

If supported:

- whether target visual signal magnitude is behaviorally saturated;
- whether Stage 3C.3 query-patch null is explained by insufficient attenuation;
- whether selected-head target paths are redundant with same-layer/W4 paths;
- why attention magnitude can change dramatically without proportional evidence change.

---

# 29. What Stage 3C.3-R Cannot Establish

Do not claim:

- sink is causally useless;
- exact upstream retrieval trigger;
- long-term Q/R memory role;
- vision-encoder origin;
- multi-evidence refresh;
- failure mechanism;
- universal hard thresholds across tasks/models.

---

# 30. Decision After Stage 3C.3-R

Recommend exactly one next direction.

## GO — Stage 3C.4 Attention Sink Causality

Use if saturation or local redundancy sufficiently explains the Stage 3C.3 behavioral null and sink dynamics remain scientifically interesting.

## GO — Broader Retrieval-Control State Analysis

Use if selected-path attenuation behaves unexpectedly and broader state control remains unresolved.

## GO — Redundancy Localization Beyond W4

Use only if R3 remains behaviorally robust and this question is more important than sink analysis.

Do not automatically continue single-evidence localization indefinitely.

---

# 31. Output Structure

```text
outputs/stage3c3r/
  config/
    stage3c3r_config.json
    frozen_targets.json
    lambda_grid.json
    nested_scope_family.json
    primary_family.json

  cohort/
    validation_manifest.jsonl
    primary_manifest.jsonl
    exclusions.jsonl

  audit/
    contribution_partition.json
    lambda_endpoint_validation.json
    head_selectivity.json
    source_invariance.json
    attention_invariance.json
    reproducibility.json

  phase_a_gain/
    per_problem_lambda_results.jsonl
    target_gain_results.jsonl
    mention_control_results.jsonl
    irrelevant_control_results.jsonl
    noncausal_head_controls.jsonl
    query_patch_operating_points.jsonl

  phase_b_redundancy/
    scope_r1_results.jsonl
    scope_r2_results.jsonl
    scope_r3_results.jsonl
    redundancy_gate.json

  analysis/
    dose_response_statistics.json
    threshold_descriptives.json
    saturation_analysis.json
    query_patch_curve_comparison.json
    target_specificity_analysis.json
    redundancy_scope_analysis.json
    figures/

  summaries/
    stage3c3r_summary.md
    stage3c3r_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3C.3 or earlier artifacts.

---

# 32. Required Figures

At minimum:

1. target evidence preference vs λ for Target A;
2. same for Target B;
3. per-base λ curves;
4. retained target contribution vs evidence preference;
5. Stage 3C.3 query-patch operating points overlaid on λ curves;
6. target vs mention attenuation control;
7. target vs irrelevant attenuation control;
8. causal vs noncausal head attenuation;
9. λ=0 retained-evidence distribution;
10. redundancy nested-scope comparison, if gated;
11. same-layer vs W4-wide λ=0 effects;
12. saturation/redundancy phenotype summary.

---

# 33. Acceptance Criteria

Stage 3C.3-R technically passes if:

1. exact frozen targets and ROI definitions are reused;
2. primary cohort is independent at `base_problem_id` level;
3. contribution decomposition reconstructs native output;
4. λ=1 reproduces native computation;
5. λ=0 removes only target-ROI contribution;
6. attention/Q/K/V are unchanged by construction;
7. non-target heads remain unchanged in Phase A;
8. λ grid is frozen before scoring;
9. target/mention/irrelevant controls are frozen;
10. frozen noncausal-head controls are run;
11. Stage 3C.3 query-patch operating points are compared prospectively;
12. Phase-B redundancy scopes are frozen before Phase-A results;
13. Phase B runs only if the redundancy gate passes;
14. no scope broader than W4 is introduced;
15. `base_problem_id` remains the statistical unit;
16. unnormalized evidence effects are primary;
17. no sink intervention is run;
18. no h_pre/query intervention is added;
19. no Stage 4/failure experiment is started;
20. exactly one next-stage recommendation is written.

Technical PASS does not require saturation or redundancy.

---

# 34. Stop Condition

After:

- contribution-decomposition audit;
- selected-head target-signal dose curve;
- Stage 3C.3 operating-point comparison;
- target/mention/irrelevant controls;
- gated nested redundancy analysis;
- final saturation/redundancy classification;
- exactly one next recommendation;

**STOP.**

Do not start:

- sink knockout or redistribution;
- broader-than-W4 redundancy search;
- h_pre retrieval-control experiments;
- Stage 4 multi-evidence refresh;
- failure analysis.

Return the complete Stage 3C.3-R results for review.

The next stage must be chosen only after jointly considering Stage 3C.3-R with all prior Stage 2A–3C.3 evidence.
