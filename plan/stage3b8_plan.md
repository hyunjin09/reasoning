# Stage 3B.8 Plan — Causal Value Representation and Low-Dimensional Evidence Subspace

## 0. Purpose

Stage 3B.8 follows the successful Stage 3B.7-R result.

Stage 3B.7-R established, under fresh validation and paired semantic controls, that two late W4 causal head/head-set targets have:

1. a robust **ROI-local visual source path**, and
2. a robust **Value-dominant K/V decomposition**.

Primary Stage 3B.7-R results:

```text
Target A:
E_d / W4 / Top_4
ROI-local
median PRR_target ≈ 0.886
median PRR_complement ≈ 0.047
median PRR_irrelevant ≈ 0.001

KVR:
K  ≈ -0.009
V  ≈ 1.154
KV = 1.0
```

```text
Target B:
E_d - 1 / W4 / Top_4
ROI-local
median PRR_target ≈ 0.848
median PRR_complement ≈ 0.115
median PRR_irrelevant ≈ 0.005

KVR:
K  ≈ 0.005
V  ≈ 1.044
KV = 1.0
```

Thus the current best-supported chain is:

```text
edited visual evidence ROI
        ↓
late causal Attention head set
        ↓
Value-mediated semantic content
        ↓
current reasoning state
        ↓
discriminative evidence decision
```

Stage 3B.8 asks:

> **What structure inside the causal Value-mediated representation carries the evidence identity?**

The stage has two ordered goals:

### Goal A — Causal dose-response
Does continuously interpolating donor–recipient Value content continuously control the model's evidence preference?

### Goal B — Causal low-dimensional subspace
Can a low-dimensional subspace of the ROI-derived Value-content difference reproduce most of the full causal semantic effect?

Do not yet start multi-evidence A/B refresh, failure analysis, vision-encoder localization, MLP feature/neuron analysis, or Q/R lifecycle analysis automatically.

---

## 1. Scientific Handoff

### Stage 2A–2C

Stage 2C showed that visual attention is predominantly mention/verbalization-centered and can reactivate with later semantic references.

Therefore:

```text
attention magnitude != causal evidence acquisition
```

### Stage 3A

Visual counterfactuals established strong causal evidence identity across 49 independent bases.

### Stage 3B.0–3B.1

A small prefill Q-side residual exists, but most evidence-specific influence remains dependent on direct vision throughout reasoning.

### Stage 3B.3-R–3B.6

The causal transfer was progressively localized to:

```text
late W4/W5 layers
→ current-position residual
→ post-Attention boundary
→ small causal query-head sets
→ visual-token source V
```

### Stage 3B.7-R

The two clean W4 targets were further localized to:

```text
Stage 3A edited ROI
```

and K/V decomposition showed:

```text
K-only ≈ 0
V-only ≈ K+V
```

Interpretation:

> **The semantic identity of the visual evidence is transmitted primarily through the Value-content pathway of the localized causal heads.**

Stage 3B.8 now characterizes that causal Value representation.

---

## 2. Primary Causal Targets

Freeze exactly the two Stage 3B.7-R primary targets:

```text
Target A:
E_d / W4 / Top_4
heads = [11, 6, 15, 12]
```

```text
Target B:
E_d - 1 / W4 / Top_4
```

Load Target B's exact frozen Top_4 head list from Stage 3B.7-R / Stage 3B.6 artifacts.

Do not infer it from memory.

Do not introduce W5/head_10 into the primary mechanism analysis.

---

## 3. Primary Confirmation Cohort

Use the exact:

```text
37 unique numeric-label base_problem_ids
```

with valid:

```text
O
O_sham
C
C_sham
```

from Stages 3B.4–3B.7-R.

Primary statistical unit:

```text
base_problem_id
```

This cohort is for final confirmation only, not shared-subspace fitting.

---

## 4. Fresh Subspace-Discovery Cohort

A shared subspace must not be learned and evaluated on the same 37 primary bases.

Construct a fresh, disjoint discovery cohort.

### Target size

```text
16–20 unique numeric-label bases
```

### Minimum

```text
16 valid bases
```

Disjoint from:

- the 37-base primary cohort;
- the 13 Stage 3B.7-R validation bases;
- the original Stage 3B.7 8-base validation cohort.

Selection must not use:

- raw attention;
- Stage 3B.8 causal outcomes;
- subspace fit quality.

Prefer existing completed-correct, edit-valid examples first. If insufficient, prospectively collect more MathVerse numeric-label examples using the locked generation/edit protocol.

---

## 5. Discovery-Example Requirements

Each discovery base must have:

1. correct completed baseline reasoning;
2. clean O/O_sham/C/C_sham visual conditions;
3. localized numeric-label counterfactual edit;
4. strict evidence decision `E_d`;
5. valid Stage 3A-style original/counterfactual fact pair;
6. manually validated ROI-to-token mapping;
7. visual-token count/layout alignment across semantic conditions;
8. mechanically valid Stage 3B.7-R-style V-only intervention.

Reject ambiguous or layout-incompatible examples before fitting.

---

## 6. Primary Representation Definition

The primary Stage 3B.8 representation is the **ROI-derived Value-content contribution** at the current reasoning position.

For frozen target head set H and target ROI R, under recipient routing/context r:

```text
z^V_H,R(r; I)
=
concatenate over h in H of
sum over j in ROI of alpha_h,j^(r) * V_h,j^(I)
```

where:

- `alpha^(r)` is recipient-native routing;
- `V^(I)` is visual Value content from image condition I;
- only target ROI positions are included;
- representation is taken before shared `W_O`, unless an audited equivalent representation is prospectively required.

This fixed-dimensional vector is called:

```text
ROI-derived causal Value-content vector
```

It directly corresponds to the validated Stage 3B.7-R V-only mechanism.

---

## 7. Symmetric Semantic Delta Per Base

Because recipient routing can differ between O and C, define a symmetric original-minus-counterfactual delta.

For base i:

```text
d_i =
0.5 * [
  z^V(r=O; I=O) - z^V(r=O; I=C)
  +
  z^V(r=C; I=O) - z^V(r=C; I=C)
]
```

This preserves a consistent semantic direction:

```text
counterfactual → original
```

while averaging across the two recipient routing contexts.

Freeze this definition before subspace fitting.

---

## 8. Mandatory Representation Audit

Before Stage 3B.8 experiments, verify:

1. exact target query heads;
2. exact associated GQA K/V groups;
3. head dimension;
4. ROI token indices;
5. recipient attention probabilities;
6. ROI-derived vector dimension;
7. pre-W_O vs post-W_O location;
8. O/C/sham tensor alignment;
9. reconstruction of full Stage 3B.7-R V-only effect from the chosen representation;
10. self-condition exactness.

Create:

```text
outputs/stage3b8/audit/value_representation_definition.md
outputs/stage3b8/audit/tensor_layout.json
outputs/stage3b8/audit/reconstruction_validation.json
```

If the representation cannot reproduce the Stage 3B.7-R V-only effect within tolerance, stop and redesign.

---

# PHASE A — Causal Value Dose-Response

## 9. Intervention

For recipient C and donor O:

```text
V_lambda = V_C + lambda * (V_O - V_C)
```

within:

- target ROI only;
- frozen causal head/head-set only.

Use:

```text
lambda = 0.00
lambda = 0.25
lambda = 0.50
lambda = 0.75
lambda = 1.00
```

Run reciprocal O-recipient / C-donor interpolation with semantically aligned direction.

Keep all other K, routing, heads, visual positions, prefix states, and reasoning states recipient-native.

---

## 10. Dose-Response Controls

### Endpoints

```text
lambda=0 → recipient-native
lambda=1 → full Stage 3B.7-R V-only semantic restoration
```

### Sham interpolation

Interpolate semantic-preserving:

```text
O ↔ O_sham
C ↔ C_sham
```

using the same lambda grid.

### Optional extrapolation — secondary only

After primary validation only:

```text
lambda = 1.25
```

Do not include extrapolation in the primary claim.

---

## 11. Dose-Response Readout

Reuse the frozen evidence-preference score.

For each lambda compute bidirectional semantic restoration:

```text
BVR(lambda)
```

Report:

- median;
- mean;
- bootstrap 95% CI;
- bidirectional fraction;
- sham interpolation effect.

Primary question:

> Does increasing donor Value-content dose systematically move evidence preference toward donor semantics?

---

## 12. Dose-Response Analysis

Prospectively test:

1. endpoint reproduction;
2. cohort-level monotonic ordering;
3. within-base rank monotonicity;
4. linear vs saturating descriptive fits;
5. sham dose-response magnitude.

Perfect linearity is not required.

Possible outcomes:

- smooth graded response;
- threshold/saturation;
- non-monotonic interaction.

If dose-response is mechanically or semantically unstable, stop before Phase B.

---

# PHASE B — Shared Causal Value Subspace

## 13. Discovery-Only Subspace Fitting

Run Phase B only if Phase A passes.

For each target separately:

1. compute one symmetric delta `d_i` per discovery base;
2. stack into a discovery matrix;
3. perform SVD/PCA on discovery data only.

The 37 primary bases must not affect subspace learning or rank selection.

---

## 14. Frozen Candidate Ranks

Use:

```text
k = 1
k = 2
k = 4
k = 8
k = 16
```

subject to discovery rank and representation dimension.

Do not add ranks after viewing primary results.

---

## 15. Discovery Rank Selection

For each k, evaluate on discovery only:

- explained semantic-delta energy;
- causal projected restoration;
- orthogonal-complement restoration;
- sham projected restoration.

Freeze one:

```text
k_primary
```

using the rule:

> smallest k whose median projected causal restoration reaches at least 80% of full V-only restoration while the orthogonal complement median is at most 30%.

If no rank satisfies the rule:

- freeze the best discovery tradeoff rank;
- label the low-dimensional hypothesis partial/exploratory;
- do not change the rule using primary data.

---

## 16. Projected-Delta Causal Intervention

For a primary base with full ROI-derived semantic delta:

```text
Delta z_i
```

and discovery-learned projector:

```text
Pi_k
```

define:

```text
Delta z_parallel = Pi_k * Delta z_i
Delta z_perp     = (I - Pi_k) * Delta z_i
```

Apply only the selected component to the recipient ROI-derived Value-content representation.

Allow:

- `W_O`;
- residual addition;
- MLP;
- later layers

to recompute naturally.

---

## 17. Primary Confirmation Conditions

On all 37 primary bases, for each target run:

```text
C0  recipient-native
C1  full V-only semantic restoration
C2  projected k_primary subspace restoration
C3  orthogonal-complement restoration
```

Secondary frozen rank controls may also be stored, but must not redefine `k_primary`.

All conditions are:

- bidirectional O↔C;
- paired-sham controlled;
- self controlled.

---

## 18. Primary Subspace Metrics

Let:

```text
B_full       = full V-only restoration
B_parallel   = learned-subspace restoration
B_perp       = orthogonal-complement restoration
```

Descriptive ratios:

```text
SR = B_parallel / B_full
CR = B_perp / B_full
```

Do not clip.

Do not interpret as additive information fractions.

Use unnormalized effects as primary.

---

## 19. Random-Subspace Controls

The learned subspace must outperform arbitrary same-dimensional subspaces.

For selected `k_primary`:

```text
100 random orthonormal subspaces
```

Evaluate on the 37-base primary cohort.

Compare learned-subspace restoration with the random-subspace distribution.

For non-primary ranks, random controls may remain discovery-only if compute is excessive.

---

## 20. Sham-Derived Subspace Control

Using discovery data only, build a same-rank subspace from semantic-preserving sham differences:

```text
O ↔ O_sham
C ↔ C_sham
```

Evaluate this sham-derived subspace on the 37-base semantic O↔C deltas.

A semantic causal subspace should substantially outperform the render/artifact subspace.

---

## 21. Cross-Target Transfer — Secondary

After both primary target results are frozen:

- apply Target-A learned subspace to Target-B deltas;
- apply Target-B learned subspace to Target-A deltas.

Questions:

- is there shared evidence-content geometry?
- or are the two reasoning coordinates represented differently?

Secondary only.

---

## 22. Optional Raw Visual-V Subspace

Primary analysis is in the effective ROI-derived Value-content representation.

Only if the primary subspace is robust, optionally test a raw visual V-vector subspace.

This requires a separate audit because:

- ROI token counts vary;
- GQA query heads share K/V groups.

Do not mix this optional analysis with the primary claim.

---

## 23. Optional Decodability Analysis — Secondary Only

Only after causal subspace results are frozen, test evidence decodability from:

- full ROI-derived Value vector;
- learned subspace coordinates;
- orthogonal complement.

Possible methods:

- linear probe;
- ridge classifier/regressor;
- simple evidence-choice decoder.

Use train/test separation.

Do not infer causality from probe accuracy.

---

# PRIMARY OUTCOME INTERPRETATION

## 24. Low-Dimensional Causal Value Subspace

If a small discovery-learned k:

- recovers most primary V-only effect;
- substantially beats random subspaces;
- substantially beats sham-derived subspace;
- leaves little orthogonal-complement effect;

then:

> **Evidence identity is concentrated in a low-dimensional causal subspace of the late ROI-derived Value-content representation.**

---

## 25. Moderately Distributed Representation

If restoration rises gradually and requires a larger k:

> evidence identity is distributed across a broader Value representation.

---

## 26. Dose-Response Without Low-Rank Compression

If lambda interpolation is robust but no small shared subspace captures the effect:

> Value content is causally graded but high-dimensional/distributed.

This is a valid result.

---

## 27. Shared vs Target-Specific Geometry

If cross-target transfer is high:

> a shared causal Value geometry may represent visual evidence identity across nearby reasoning coordinates.

If cross-transfer is weak:

> the causal Value representation is target/time-specific.

---

# SECONDARY TRIANGULATION

## 28. Attention Comparison

Only after causal results are frozen, compare:

```text
raw ROI attention
selected-head ROI attention
full V-only causal effect
causal subspace restoration
```

Potential methodological contribution:

> **Attention weights indicate neither the magnitude nor the semantic dimensionality of causal visual information being transmitted.**

Secondary only.

---

# SCIENTIFIC BOUNDARY

## 29. What Stage 3B.8 May Establish

If supported:

- graded causal Value geometry;
- a low-dimensional or distributed causal Value representation;
- whether the same subspace generalizes across two nearby reasoning targets;
- causal-vs-decodable differences if secondary probes are run.

---

## 30. What Stage 3B.8 Cannot Establish

Do not claim:

- where the Value subspace originates in the vision encoder;
- a specific visual-encoder layer or feature;
- MLP neuron/feature mechanism;
- long-term Q/R memory;
- evidence A→B refresh cycle;
- failure mechanisms;
- discrete LOOK/THINK states.

---

# 31. Decision After Stage 3B.8

Recommend exactly one next direction.

## GO — Vision-encoder/projector origin

Use if a robust causal Value subspace is identified.

Next question:

> Where upstream does this causal Value subspace emerge?

## GO — Multi-evidence causal refresh

Use if the single-evidence Value mechanism is sufficiently characterized and additional single-path compression gives diminishing returns.

Next:

> Does reasoning retrieve A and later B through distinct ROI→Value→head episodes?

## GO — Distributed Value geometry

Use if V is strongly causal but not low-dimensional.

## REDIRECT — Value-geometry instability

Use if interpolation or learned-subspace effects fail random/sham controls.

---

# 32. Output Structure

Create:

```text
outputs/stage3b8/
  config/
    stage3b8_config.json
    primary_targets.json
    primary_family.json
    discovery_confirmation_split.json

  discovery_cohort/
    candidate_screening.jsonl
    discovery_manifest.jsonl
    exclusion_log.jsonl
    edit_validation/
    roi_validation/

  audit/
    value_representation_definition.md
    tensor_layout.json
    reconstruction_validation.json

  dose_response/
    per_problem_interpolation_results.jsonl
    dose_response_statistics.json
    sham_interpolation_results.jsonl

  subspace/
    discovery_delta_matrix/
    svd_statistics.json
    frozen_subspace_definition.npz
    rank_selection_report.md
    primary_projected_results.jsonl
    complement_results.jsonl
    random_subspace_results.jsonl
    sham_subspace_results.jsonl
    cross_target_results.jsonl

  secondary/
    optional_raw_v_subspace/
    optional_decodability/
    attention_comparison.json

  analysis/
    dose_response_analysis.json
    subspace_restoration_statistics.json
    random_control_statistics.json
    sham_subspace_statistics.json
    cross_target_analysis.json
    figures/

  summaries/
    stage3b8_summary.md
    stage3b8_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3B.7-R or earlier artifacts.

---

# 33. Required Figures

At minimum:

1. Value dose-response curve for Target A;
2. dose-response curve for Target B;
3. per-problem lambda-response trajectories;
4. discovery singular-value spectrum for Target A;
5. same for Target B;
6. causal restoration vs subspace rank;
7. learned vs random-subspace restoration;
8. learned semantic vs sham-derived subspace;
9. in-subspace vs orthogonal-complement restoration;
10. cross-target subspace transfer;
11. optional causal-restoration vs decodability;
12. raw attention vs causal Value/subspace effect as secondary analysis.

---

# 34. Acceptance Criteria

Stage 3B.8 technically passes if:

1. the two Stage 3B.7-R primary targets remain frozen exactly;
2. the 37-base cohort is used only for confirmation, not subspace fitting;
3. at least 16 fresh disjoint discovery bases are obtained;
4. discovery selection does not use attention or subspace outcomes;
5. ROI-derived Value-content representation is prospectively defined;
6. the representation reconstructs Stage 3B.7-R V-only effect within tolerance;
7. dose-response endpoints reproduce native and full V-only conditions;
8. sham dose-response controls are run;
9. discovery-only SVD/PCA is used;
10. candidate ranks are frozen before primary evaluation;
11. primary rank is selected using discovery data only;
12. primary 37-base projected-subspace testing is bidirectional;
13. orthogonal complement is tested;
14. random same-rank subspaces are tested;
15. sham-derived same-rank subspace is tested;
16. base_problem_id remains the statistical unit;
17. raw attention remains secondary only;
18. optional probes/readouts are separated from causal claims;
19. no vision-encoder/multi-evidence/failure experiment is started;
20. an explicit GO / REDIRECT recommendation is written.

Technical PASS does not require a low-dimensional subspace.

---

# 35. Stop Condition

After:

- fresh discovery cohort construction;
- representation audit;
- causal dose-response;
- discovery-only subspace fitting;
- untouched 37-base confirmation;
- orthogonal/random/sham controls;
- optional frozen secondary analyses;
- final recommendation;

**STOP.**

Do not start:

- vision-encoder causal localization;
- projector-feature localization;
- multi-evidence A/B refresh;
- Q/R lifecycle analysis;
- correct-vs-wrong failure analysis.

Return the complete Stage 3B.8 results for review.

The next plan must be determined only after jointly considering Stage 3B.8 with all prior Stage 2A–3B.7-R evidence.
