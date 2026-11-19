# Stage 3B.7 Plan — ROI-Specific Visual Path and Routing-vs-Value Decomposition

## 0. Purpose

Stage 3B.7 follows the Stage 3B.6 result that a small causal Attention head/head-set can retrieve evidence identity predominantly from **visual-token source positions** near the discriminative evidence decision.

The strongest Stage 3B.6 visual-source results were:

### Primary clean targets

```text
E_d / W4 / Top_4
    median PRR_V ≈ 0.979
    P ≈ 0.009
    R ≈ 0

E_d - 1 / W4 / Top_2
    median PRR_V ≈ 0.885
    P ≈ 0
    R ≈ 0.038
```

These two targets passed the frozen robust visual-dominance rule.

### Secondary / exploratory target

```text
E_d - 1 / W5 / head_10
```

This target showed high median visual PRR but failed the frozen source-path robustness controls. It must not support the primary mechanism claim.

Stage 3B.7 asks two ordered questions:

1. **WHERE inside vision?**  
   Does the causal visual path originate primarily from the Stage 3A edited evidence ROI, from the rest of the visual-token field, or from a distributed combination?

2. **HOW inside Attention?**  
   For the localized visual path, is evidence identity carried mainly by routing/selection through Keys and attention patterns, by transmitted Value content, or by their interaction?

The target mechanistic chain is:

```text
target visual evidence tokens
        ↓
causal late Attention head/set
        ↓
current reasoning residual
        ↓
evidence decision
```

This must be established causally rather than inferred from raw attention.

---

## 1. Scientific Handoff

### Stage 2A–2C

Stage 2C showed that visual attention is predominantly aligned with evidence verbalization and can reactivate at later semantic references.

Therefore:

```text
high attention weight != evidence acquisition
```

Raw attention remains secondary.

### Stage 3A

Localized visual counterfactual edits established strong evidence-specific causal visual influence.

### Stage 3B.0–3B.1

A small prefill residual is carried by Q, but most evidence-specific effect remains dependent on direct vision during reasoning.

### Stage 3B.3-R–3B.5

Evidence-specific transfer was localized to narrow late-layer/current-position computation near E_d, with robust post-Attention boundary gains.

### Stage 3B.6

Head/source localization found:

- sparse/small-set causal query heads;
- two robust W4 head/head-set targets;
- visual-token source V strongly dominant over prefix P and previous reasoning R.

Stage 3B.7 now narrows the visual source and then decomposes K vs V.

---

## 2. Primary Cohort

Use the exact paired-semantic primary cohort from Stages 3B.4–3B.6:

- **37 unique numeric-label base_problem_ids**
- each with valid:
  - O
  - O_sham
  - C
  - C_sham

Primary statistical unit:

```text
base_problem_id
```

Do not add or remove examples based on Stage 3B.7 outcomes.

---

## 3. Frozen Primary Causal Targets

Primary targets:

```text
Target A:
E_d / W4 / Top_4

Target B:
E_d - 1 / W4 / Top_2
```

Secondary exploratory target:

```text
E_d - 1 / W5 / head_10
```

The exploratory W5 target may be scored only after primary results are frozen.

Do not include E_d/W5 as a primary visual-injection target; it remains an upstream-state control.

---

## 4. ROI Definition

The target ROI must come from the **counterfactual edit itself**, not from attention.

For every base:

```text
V_target = visual-token positions overlapping the Stage 3A edited evidence region
V_other  = V_all \ V_target
```

Do not redefine or enlarge V_target after seeing causal results.

---

## 5. Mandatory ROI-to-Token Audit

Before scoring:

1. load the exact Stage 3A edit mask/ROI;
2. reproduce image preprocessing;
3. map edited pixels to merged visual-token positions;
4. manually inspect token overlays;
5. record target token count;
6. record total visual token count;
7. freeze V_target and V_other;
8. prospectively define a matched irrelevant ROI when feasible.

Create:

```text
outputs/stage3b7/roi_audit/roi_token_mapping.jsonl
outputs/stage3b7/roi_audit/roi_mapping_report.md
outputs/stage3b7/roi_audit/irrelevant_roi_manifest.jsonl
outputs/stage3b7/roi_audit/overlays/
```

Important interpretation boundary:

> A pixel-local edit is not guaranteed to remain token-local after the vision encoder. ROI analysis localizes visual-token positions, not raw-pixel information itself.

---

## 6. Matched Irrelevant ROI

For each base, define a matched irrelevant visual-token region where feasible.

Criteria:

- disjoint from V_target;
- approximately matched target token count;
- does not overlap another obvious task-relevant label/mark;
- selected before causal scoring;
- valid under the same visual-token grid.

If exact matching is impossible, record the reason and closest feasible control.

---

# PHASE A — ROI-Specific Visual Source Localization

## 7. Phase A Question

Within the already-confirmed causal visual head/head-set:

> **Which visual-token positions carry the evidence-specific semantic effect?**

Use the same state-consistent head semantic-swap implementation validated in Stage 3B.6.

Keep:

- recipient current query/state unchanged;
- non-target heads recipient-native;
- downstream residual/MLP/later layers recomputing naturally.

Only source positions exposed to the selected causal head/set are semantically swapped.

---

## 8. Phase A Conditions

All conditions must be bidirectional O→C and C→O with self/sham controls.

### A0 — All visual source swap

Swap semantic visual K/V for all visual positions.

This must reproduce the Stage 3B.6 V-only source-path effect.

### A1 — Target ROI-only swap

Swap only V_target.

All other visual positions remain recipient-native.

### A2 — Visual complement-only swap

Swap only V_other.

V_target remains recipient-native.

### A3 — Matched irrelevant ROI swap

Swap only V_irrelevant.

### A4 — Target + fixed surrounding ring

Prospectively define a small token ring around V_target where grid geometry permits.

This is secondary and must use a fixed rule frozen before scoring.

---

## 9. ROI Path Metric

For source region S:

```text
BPR_H,S = bidirectional semantic restoration for causal head/set H using source region S
```

All-V reference:

```text
BPR_H,all
```

Descriptive recovery ratio:

```text
PRR_H,S = BPR_H,S / BPR_H,all
```

Use unnormalized BPR as primary.

Do not clip PRR and do not interpret it as a unique information fraction.

---

## 10. Phase A Controls

For every ROI arm verify:

- self swap transparency;
- paired within-semantic sham swap;
- reciprocal O↔C direction;
- exact visual-token group isolation;
- non-target heads unchanged;
- non-target source positions unchanged.

Target semantic effect must exceed sham and matched-irrelevant effects.

---

## 11. Phase A Outcome Categories

### ROI-Local

```text
target ROI ≈ all visual
other visual ≈ 0
irrelevant ≈ 0
```

Interpretation:

> The edited evidence ROI is the dominant visual-token source for the causal head pathway.

### ROI-Local-Plus-Context

Target is strong, but target+ring recovers substantially more and approaches all-V.

Interpretation:

> Evidence representation is locally distributed around the edited region.

### Visual-Distributed

Complement-only is substantial or target-only explains little despite strong all-V effect.

Interpretation:

> Pixel-local evidence has become spatially distributed across visual-token representations.

### ROI-Inconclusive

Target and matched irrelevant are similar.

Do not proceed to primary target-ROI K/V decomposition.

---

## 12. Gate From Phase A to Phase B

Proceed to primary K/V decomposition only for target/cell combinations satisfying all:

1. robust bidirectional target ROI restoration;
2. target effect clearly exceeds sham;
3. target effect clearly exceeds matched irrelevant;
4. target or target+ring explains a meaningful portion of the all-V causal path.

If no primary target passes:

```text
STOP
REDIRECT → visual-representation diffusion/localization
```

Do not force K/V decomposition on an unlocalized ROI.

---

# PHASE B — Routing-vs-Value Decomposition

## 13. Phase B Question

For each Phase-A-qualified causal target:

> **Is evidence identity carried mainly by routing/selection through Keys, by transmitted visual Value content, or by their interaction?**

Recipient query remains recipient-native.

All non-target positions remain recipient-native.

Downstream computation recomputes naturally.

---

## 14. Phase B Conditions

All conditions are bidirectional with self/sham controls.

### B0 — No semantic ROI swap

Recipient-native K and V.

### B1 — K-only semantic swap

```text
K_target = donor
V_target = recipient
```

Interpretation:

> Routing/selection-side semantic manipulation.

Do not call this a perfect pattern-only intervention.

### B2 — V-only semantic swap

```text
K_target = recipient
V_target = donor
```

Interpretation:

> Recipient routing geometry is retained while transmitted visual content changes.

### B3 — K+V semantic swap

```text
K_target = donor
V_target = donor
```

This must reproduce the Phase A target-ROI semantic path effect within tolerance.

---

## 15. Optional Alpha / Attention-Pattern Swap

Only after B1–B3 are validated.

A secondary arm may patch the normalized attention-probability pattern while keeping recipient visual values.

Requirements:

- exact self transparency;
- normalization audit;
- paired sham controls;
- clear mechanical definition.

This is secondary because alpha-patching can be off-manifold.

---

## 16. K/V Causal Metric

For mechanism arm M ∈ {K, V, KV}:

```text
BKV_M = bidirectional semantic restoration
```

Compare with K+V:

```text
KVR_M = BKV_M / BKV_KV
```

Use BKV as primary.

Do not clip ratios or interpret them as additive fractions.

Descriptive interaction:

```text
I_KV = BKV_KV - BKV_K - BKV_V
```

---

## 17. Phase B Mechanistic Outcomes

### Value-Dominant

```text
V-only ≈ K+V
K-only small
```

Interpretation:

> Evidence identity is transmitted primarily through visual Value content.

This would strongly explain why raw attention magnitude is an incomplete causal measurement.

### Routing-Dominant

K-only is large and approaches K+V.

Interpretation:

> Semantic routing toward visual positions is strongly causal for evidence identity.

### Routing + Value Interaction

Both K and V contribute; joint K+V is stronger.

Interpretation:

> Visual retrieval requires both where-to-read routing and what-is-read content.

### Distributed / Nonlocal

Target ROI K/V effects remain weak while all-V is strong.

Interpretation:

> Evidence is not localized to the edited ROI at the LM visual-token interface.

---

## 18. GQA-Specific Constraint

Qwen3-VL uses grouped-query attention.

Stage 3B.7 must preserve the Stage 3B.6 query-head-selective semantics.

Do not globally patch a shared KV group if doing so changes non-target logical query heads.

K/V decomposition must occur inside the already-validated hybrid target-head/head-set computation.

Document exactly how donor K/V affect only the intended query heads.

---

## 19. Validation Gate

Before the 37-base primary run, validate on the disjoint 8-base validation/discovery set if available.

Verify:

1. all-V path reproduces Stage 3B.6;
2. ROI mapping/source isolation is exact;
3. target/complement/irrelevant groups are non-overlapping;
4. target ROI self swap is transparent;
5. K-only changes only intended K inputs for intended query heads;
6. V-only changes only intended V inputs for intended query heads;
7. K+V reproduces target-ROI source swap;
8. non-target query heads remain recipient-native;
9. GQA shared-KV semantics are handled correctly;
10. bidirectional semantic direction is correct;
11. sham effects are small;
12. no NaNs/infs occur;
13. deterministic replication passes.

Do not score the primary cohort until this gate passes.

---

## 20. Primary Statistical Family

Primary family is frozen to:

```text
Targets:
E_d / W4 / Top_4
E_d - 1 / W4 / Top_2

Phase A:
all visual
target ROI
visual complement
matched irrelevant ROI

Secondary Phase A:
target + fixed ring

Phase B, gated:
K-only
V-only
K+V
```

Use `base_problem_id` as the statistical unit.

Report:

- median and mean unnormalized restoration;
- bootstrap 95% CIs;
- bidirectional consistency;
- sham/render effect;
- self error;
- recovery relative to all-V or K+V reference.

Use Holm correction across the fixed confirmatory family.

---

## 21. Secondary W5 Exploratory Analysis

Only after all primary results are frozen, optionally evaluate:

```text
E_d - 1 / W5 / head_10
```

with the same ROI/KV framework.

All W5/head_10 results must be labeled exploratory and not pooled into primary mechanism estimates.

---

# SECONDARY TRIANGULATION

## 22. Attention Triangulation

After ROI/KV causal results are frozen, compare:

1. raw Stage 2C ROI attention;
2. selected causal head's ROI attention;
3. ROI-specific causal restoration;
4. K-only restoration;
5. V-only restoration.

These are different measurements:

```text
attention magnitude
routing-side causal contribution
value-content causal contribution
```

Possible findings:

### High attention, low K, high V

Supports:

> attention may reflect alignment/selection while evidence identity is transmitted mainly through values.

### High attention, high K, high V

Attention coincides with genuine routing and content retrieval.

### Low attention, high causal effect

Important evidence transfer can occur without a large raw attention signal.

This analysis is secondary only.

---

## 23. Stage 3B.1/3B.6 Triangulation

For each primary target, compare:

```text
Stage 3B.1 all-V cutoff damage
Stage 3B.6 V-source head restoration
Stage 3B.7 target-ROI restoration
Stage 3B.7 K/V decomposition
```

A particularly strong mechanistic chain would be:

```text
future vision cutoff is damaging
+
causal head reads from V
+
target ROI explains V effect
+
V-only carries semantic identity
```

This would provide multi-stage causal evidence from behavioral dependence down to a specific visual-value path.

---

# SCIENTIFIC BOUNDARIES

## 24. What Stage 3B.7 May Establish

If supported:

### ROI-specific causal visual path

> A localized visual-token region corresponding to the edited evidence causally feeds a small set of late reasoning Attention heads.

### Distributed visual representation

Alternatively:

> Although the causal source is visual, evidence identity is spatially distributed beyond the pixel-local edited ROI at the visual-token interface.

### Value-mediated evidence transport

If V-only dominates:

> Evidence identity is transmitted primarily through the Value stream, while attention/routing magnitude is not itself the main carrier of semantic identity.

### Routing-mediated retrieval

If K-only dominates:

> Evidence identity depends strongly on semantic routing toward the relevant visual positions.

### Routing-content interaction

If both matter:

> Late visual retrieval combines where-to-read routing with what-is-read visual content.

---

## 25. What Stage 3B.7 Cannot Establish

Do not claim:

- exact vision-encoder feature responsible;
- causal vision-encoder layer;
- MLP feature/neuron mechanism;
- long-term Q/R lifecycle;
- evidence A→B refresh cycles;
- correct-vs-wrong failure mechanisms;
- discrete LOOK/THINK states.

---

# 26. Decision After Stage 3B.7

Recommend exactly one next direction.

## GO — Fine visual path / vision-encoder localization

Use if target ROI path is robust and the K/V mechanism is clear.

## GO — Attention routing mechanism

Use if K/routing dominates.

Next:
- query/key feature analysis;
- routing-specific causal circuit;
- validated pattern-level intervention.

## GO — Value-content mechanism

Use if V dominates.

Next:
- characterize visual value representation;
- causal value-subspace/feature patching;
- descriptive probe/lens readout only after causal localization.

## REDIRECT — Distributed visual representation

Use if all-V is strong but target ROI path is weak.

Next:
- map how localized image evidence diffuses across visual-token representations before the late causal head reads it.

---

# 27. Output Structure

Create:

```text
outputs/stage3b7/
  config/
    stage3b7_config.json
    primary_family.json
    cohort_manifest.jsonl

  roi_audit/
    roi_token_mapping.jsonl
    roi_mapping_report.md
    irrelevant_roi_manifest.jsonl
    overlays/

  validation/
    validation_manifest.jsonl
    roi_path_validation.json
    kv_decomposition_validation.json
    validation_report.md

  scoring/
    all_visual_path_results.jsonl
    target_roi_results.jsonl
    visual_complement_results.jsonl
    irrelevant_roi_results.jsonl
    target_ring_results.jsonl
    k_only_results.jsonl
    v_only_results.jsonl
    kv_results.jsonl
    optional_alpha_results.jsonl

  analysis/
    roi_path_statistics.json
    spatial_localization_analysis.json
    kv_decomposition_statistics.json
    kv_interaction_analysis.json
    attention_secondary_analysis.json
    exploratory_w5_analysis.json
    figures/

  summaries/
    stage3b7_summary.md
    stage3b7_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3B.6 or earlier artifacts.

---

# 28. Required Figures

At minimum:

1. all-V vs target ROI vs complement vs irrelevant restoration for Target A;
2. same for Target B;
3. target ROI / all-V recovery distribution;
4. complement / all-V recovery distribution;
5. K-only vs V-only vs K+V for Target A;
6. same for Target B;
7. per-problem K vs V scatter;
8. target ROI causal effect vs raw ROI attention as secondary analysis;
9. selected-head attention vs K/V causal effect;
10. representative bidirectional ROI semantic flips;
11. visual-token overlays for strong-local and distributed cases.

---

# 29. Acceptance Criteria

Stage 3B.7 technically passes if:

1. the two robust W4 primary targets are frozen exactly;
2. W5/head_10 remains exploratory only;
3. the exact Stage 3A edit ROI is used rather than an attention-selected ROI;
4. ROI-to-token mappings are manually validated;
5. target/complement/matched irrelevant groups are frozen before scoring;
6. all-V source effect reproduces Stage 3B.6;
7. ROI source swaps are bidirectional;
8. self and paired sham controls are implemented;
9. source-group isolation is mechanically audited;
10. Phase B occurs only if the ROI gate passes;
11. K-only, V-only, and K+V interventions remain query-head-selective under GQA;
12. K+V reproduces target-ROI path restoration within tolerance;
13. non-target query heads remain recipient-native;
14. base_problem_id remains the statistical unit;
15. raw attention is secondary only;
16. no vision-encoder/MLP/Q-R/multi-evidence/failure experiment is started;
17. an explicit GO / REDIRECT recommendation is written.

Technical PASS does not require ROI localization or one dominant K/V mechanism.

---

# 30. Stop Condition

After:

- ROI mapping audit;
- validation;
- 37-base ROI-specific causal path analysis;
- complement and matched-irrelevant controls;
- gated K/V decomposition;
- sham/self controls;
- secondary attention triangulation;
- final recommendation;

**STOP.**

Do not start:

- vision-encoder feature localization;
- query/key feature analysis;
- value-subspace analysis;
- MLP feature/neuron analysis;
- Q/R memory lifecycle analysis;
- multi-evidence A/B refresh;
- correct-vs-wrong failure analysis.

Return the complete Stage 3B.7 results for review.

The next plan must be determined only after jointly considering Stage 3B.7 with all prior Stage 2A–3B.6 evidence.
