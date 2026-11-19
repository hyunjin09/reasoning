# Stage 3B.9 Plan — Distributed Value Geometry: Shared vs Local vs Mixture

## 0. Purpose

Stage 3B.9 follows Stage 3B.8:

> **Graded causal Value transport is robust, but a discovery-learned shared rank-8 subspace does not recover most of the causal effect on the historical 37-base confirmation cohort.**

Stage 3B.8 established:

- smooth donor-Value dose response at both frozen late-W4 targets;
- discovery-only rank-8 compression that looked strong on 20 discovery bases;
- weak rank-8 transfer to the 37 historical confirmation bases;
- substantial orthogonal-complement causal signal;
- learned rank-8 subspaces that still beat random and sham-derived controls;
- negligible cross-target transfer under the frozen ordinal head-coordinate mapping.

Therefore Stage 3B.9 does **not** ask whether Value is causal. It asks:

> **What kind of geometry does the causal Value representation have if one robust shared rank-8 code is insufficient?**

Three live hypotheses:

### H1 — Shared but higher-dimensional
A shared causal geometry exists across problems, but rank 8 was too small.

### H2 — Locally low-dimensional but globally heterogeneous
Within one problem, several possible visual evidence values lie in a compact causal subspace, but that subspace differs across problems.

### H3 — Mixture / clustered geometry
Problems reuse several recurring causal subspaces rather than one universal geometry.

Primary goals:

1. obtain a **fresh-confirmed shared-rank generalization curve**;
2. test **within-problem local dimensionality using multiple counterfactual values per problem**;
3. compare local and global subspaces without using attention for selection.

This should be the final single-evidence representation-geometry stage before returning to multi-evidence reasoning, unless the mechanics fail.

---

## 1. Immutable Stage 3B.8 Result

The Stage 3B.8 conclusion remains unchanged.

### Frozen targets

```text
Target A:
E_d / W4 / layer 29 / heads [11, 6, 15, 12]

Target B:
E_d - 1 / W4 / layer 28 / heads [16, 0, 3, 6]
```

### Frozen representation

```text
512-dimensional selected-head pre-W_O exact eager-Attention recomposition effect vector
recipient-native q/k/routing
donor target-ROI Value content
```

Reuse the validated v3 endpoint.

Do not return to the failed v1 ROI-only reduction or failed v2 BF16 subtract/add formulation.

### Stage 3B.8 low-rank result

```text
Target A:
discovery rank-8 projected/full ≈ 0.899
historical confirmation SR ≈ 0.368
historical confirmation CR ≈ 0.472

Target B:
discovery rank-8 projected/full ≈ 0.837
historical confirmation SR ≈ 0.532
historical confirmation CR ≈ 0.348
```

Therefore:

> **A robust universal rank-8 causal Value subspace is not supported.**

Stage 3B.9 must not reinterpret this as a positive rank-8 result.

---

## 2. Frozen Causal Targets

Use exactly the two Stage 3B.8 targets.

Do not add:

- W5/head_10;
- other heads;
- other layers;
- attention-selected targets.

All geometry questions are conditional on the already-localized ROI→Value→head mechanism.

---

## 3. Stage Structure

### Phase A — Shared-rank generalization
Ask:

> Does a larger shared subspace generalize causally across previously unseen problems?

### Phase B — Within-problem local geometry
Ask:

> Within the same problem, do several alternative evidence values occupy a low-dimensional causal Value subspace even if the global shared subspace is weak?

### Phase C — Mixture diagnostics
Secondary only, after A and B freeze.

---

# PHASE A — SHARED-RANK GENERALIZATION

## 4. Historical Geometry-Training Pool

For Stage 3B.9, prior Stage 3B.8 data become **training/design only**.

Use:

```text
20 Stage 3B.8 discovery bases
+
37 Stage 3B.8 historical confirmation bases
=
57 unique bases
```

All 57 already influenced prior conclusions.

They may be used to fit frozen shared subspaces, but they are not fresh confirmation evidence.

---

## 5. Fresh Phase-A Confirmation Cohort

Construct a completely fresh disjoint cohort.

Target:

```text
24–32 unique numeric-label bases
```

Minimum:

```text
24 valid bases
```

Disjoint from:

- the 57 Stage 3B.8 geometry bases;
- the 13 Stage 3B.7-R validation bases;
- the original 8 Stage 3B.7 validation bases;
- the Phase-B multi-counterfactual cohort.

Selection must not use:

- attention;
- Stage 3B.9 subspace recovery;
- rank-fit quality;
- causal projection outcome.

Use the locked generation, edit, ROI, evaluator, and v3 endpoint protocols.

---

## 6. Phase-A Example Requirements

Every fresh base must have:

1. completed-correct baseline reasoning;
2. valid O/O_sham/C/C_sham images;
3. localized numeric evidence edit;
4. strict `E_d`;
5. manually validated ROI mapping;
6. aligned visual-token layout;
7. valid v3 Value endpoint reconstruction;
8. usable full V-only semantic effect for the target being evaluated.

The full-V applicability check must occur before rank-projection outcomes are inspected.

Freeze all exclusions first.

---

## 7. Shared Subspace Training

For each target separately:

1. compute the exact Stage 3B.8 symmetric semantic delta `d_i` on the 57 historical bases;
2. fit SVD/PCA on those 57 only;
3. freeze all basis files before fresh scoring.

Frozen candidate ranks:

```text
k = 1
k = 2
k = 4
k = 8
k = 16
k = 24
k = 32
k = 48
```

Only use mathematically identifiable ranks.

Do not add ranks after fresh results are read.

---

## 8. Frozen Phase-A Controls

For every rank k materialize before fresh scoring:

### Semantic learned basis
From historical O↔C deltas.

### Sham-derived basis
From historical:

```text
O ↔ O_sham
C ↔ C_sham
```

differences.

### Random bases

```text
100 Haar-random orthonormal subspaces per rank
```

with frozen seeds.

Store hashes and seeds before scoring the fresh cohort.

---

## 9. Phase-A Causal Conditions

For each fresh base and target:

```text
A0  recipient-native
A1  full V-only semantic restoration
A2  learned semantic subspace projection at each frozen k
A3  orthogonal complement at each frozen k
A4  sham-derived same-rank projection
A5  random same-rank projection controls
```

All interventions:

- recipient-native q/k/routing;
- target ROI Value path only;
- frozen target heads only;
- non-target heads/positions unchanged;
- bidirectional O↔C;
- self controlled.

---

## 10. Phase-A Metrics

For each rank k:

```text
B_full
B_parallel(k)
B_perp(k)

SR(k) = B_parallel(k) / B_full
CR(k) = B_perp(k) / B_full
```

Do not clip ratios.

Do not interpret them as additive information fractions.

Report:

- median and mean unnormalized restoration;
- bootstrap 95% CI;
- median SR;
- median CR;
- bidirectional consistency;
- learned-vs-sham margin;
- learned percentile among random controls.

Primary unit:

```text
base_problem_id
```

---

## 11. Shared-Geometry Decision Rule

A fresh-confirmed rank k supports a shared causal geometry only if all hold:

1. median SR(k) >= 0.80;
2. median CR(k) <= 0.30;
3. learned effect robustly positive;
4. learned effect exceeds sham-derived same-rank effect;
5. learned effect exceeds the 95th percentile of random same-rank controls;
6. bidirectional consistency >= 0.75.

Freeze `k_shared` as the smallest passing rank.

Outcome labels:

```text
Shared-Moderate-Dimensional
    passing k = 16–24

Shared-High-Dimensional
    passing k = 32–48

No-Robust-Shared-Compression
    no tested rank passes
```

Do not change the 0.80/0.30 rule after inspecting the curve.

If rank 32 or 48 is required, do not call the representation low-dimensional.

---

# PHASE B — WITHIN-PROBLEM LOCAL GEOMETRY

## 12. Fresh Multi-Counterfactual Cohort

Use a separate fresh cohort.

Target:

```text
12–16 unique base problems
```

Minimum:

```text
12 valid bases
```

Each base must support:

```text
1 original semantic value
+
4 distinct counterfactual semantic values
=
at least 5 valid semantic image variants
```

All variants modify the same evidence ROI.

Statistical unit remains:

```text
base_problem_id
```

---

## 13. Counterfactual-Value Requirements

Choose all four alternative numeric values **before any Value-vector analysis**.

Requirements:

1. same edited object/label/ROI;
2. visually plausible edit;
3. non-target image content preserved;
4. no overlap with other task-relevant marks;
5. aligned image preprocessing and visual-token layout;
6. unambiguous evidence-choice readout;
7. candidate tokenization prospectively audited;
8. formatting ambiguity avoided;
9. manual inspection passes;
10. attention is not used for selection.

Prefer single-token numeric decisions where feasible.

Record every rejected value and reason.

---

## 14. Recipient-State Rule

For each semantic pair:

```text
Original O ↔ Counterfactual C_m
```

use the exact validated recipient-native causal coordinate and v3 V-only intervention.

All variants need not produce identical free-running reasoning prefixes.

However:

- `E_d` scoring must be aligned;
- recipient-state provenance must be recorded;
- one frozen common-prefix / teacher-forcing rule must be used across variants;
- exact natural-common-lead cases, when available, are reported as a stronger subset.

Do not silently mix natural and teacher-forced states.

---

## 15. Full-V Applicability Gate

Before local subspace fitting, each base must show usable full V-only causal transfer for at least:

```text
3 of 4 alternative values
```

at the target being evaluated.

This gate is frozen before local rank outcomes.

---

## 16. Local Delta Construction

For each base and target:

```text
Delta_m = z(C_m) - z(O)
```

using the exact v3 ROI-derived causal Value representation.

Do not pool across bases for the primary local test.

Each problem defines its own local semantic geometry.

---

## 17. Leave-One-Value-Out Test

For each base:

1. hold out one counterfactual value `C_m`;
2. learn the local subspace from the other three counterfactual deltas;
3. causally test the held-out O↔C_m semantic delta;
4. rotate across all four held-out values.

Frozen local ranks:

```text
k_local = 1
k_local = 2
k_local = 3
```

No higher rank is permitted because each training fold has only three alternative deltas.

---

## 18. Local Causal Conditions

For every held-out value:

```text
L0  recipient-native
L1  full V-only held-out restoration
L2  local rank-1 projection
L3  local rank-2 projection
L4  local rank-3 projection
L5  corresponding orthogonal complements
L6  historical global shared-basis projection at matched rank
L7  random same-rank local controls
```

All interventions are bidirectional and preserve recipient-native q/k/routing.

---

## 19. Local Geometry Metrics

Aggregate leave-one-value-out folds within each base first.

Then aggregate across base problems.

Report:

```text
Local_SR(k)
Local_CR(k)
GlobalMatched_SR(k)
```

plus unnormalized causal effects.

Primary question:

> Can a small subspace learned from other semantic values of the same problem causally control an unseen held-out value?

---

## 20. Local-Low-Dimensional Rule

Support `Local-Low-Dimensional` if rank 1 or rank 2 satisfies:

1. median held-out Local_SR >= 0.80;
2. median held-out Local_CR <= 0.30;
3. learned local projection robustly exceeds random controls;
4. bidirectional consistency >= 0.75;
5. effect generalizes to held-out semantic values.

Rank 3 is reported but does not count as strong evidence for a very compact local code.

---

## 21. Global-vs-Local Comparison

At matched rank compare:

```text
same-problem local subspace
vs
historical global shared subspace
```

Key result:

```text
Local_SR >> GlobalMatched_SR
```

would support:

> **The causal Value code is compact within a problem but poorly aligned across problems.**

Do not compare unmatched ranks as if equivalent.

---

# JOINT GEOMETRY INTERPRETATION

## 22. Outcome Matrix

### G1 — Shared higher-dimensional

Phase A passes at a larger k and local geometry gives little additional advantage.

Conclusion:

> **The causal Value code is shared across problems but distributed over a larger subspace than rank 8.**

### G2 — Local low-dimensional / global heterogeneous

Phase A fails or needs very high rank, while Phase B rank 1–2 strongly transfers to held-out values.

Conclusion:

> **Each problem instantiates a compact causal Value code whose orientation varies across problems.**

### G3 — Shared + private geometry

Phase A reveals a meaningful shared component but does not recover most effect, while local subspaces recover substantially more.

Conclusion:

> **The causal representation contains shared semantic structure plus substantial problem-specific private directions.**

### G4 — Distributed globally and locally

Neither moderate shared rank nor local rank 1–2 captures most held-out effect.

Conclusion:

> **The causal Value code is broadly distributed even within individual problems.**

---

# PHASE C — MIXTURE DIAGNOSTICS, SECONDARY ONLY

## 23. Mixture / Cluster Diagnostics

Run only after Phase A and B primary results freeze.

Possible frozen descriptors:

- MathVerse problem category;
- evidence type;
- numeric-label morphology;
- ROI size;
- number of selected visual tokens;
- output tokenization class.

For base-level local subspaces:

- compute pairwise principal angles;
- compute projector similarity;
- visualize geometry.

Unsupervised clustering is exploratory only.

Do not claim a causal mixture-of-subspaces architecture from clustering alone.

A true cluster-specific causal confirmation would require another fresh cohort and a separate reviewed stage.

---

# 24. Distribution-Mismatch Analysis

Stage 3B.8 mixed historical choice and fresh free-response numeric discovery examples.

For Phase A, record:

- question format;
- answer format;
- problem category;
- edit type;
- tokenization;
- ROI token count.

After primary results freeze, run secondary stratified analysis.

Do not modify the cohort or basis to optimize subgroup performance.

---

# 25. Attention Analysis

Raw attention remains secondary only.

After geometry results freeze, optional descriptive comparisons may include:

```text
ROI attention
full V-only effect
global-subspace recovery
local-subspace recovery
```

Do not use attention for:

- cohort selection;
- rank selection;
- semantic-value selection;
- primary cluster definition.

---

# 26. Scientific Claims Allowed

Stage 3B.9 may establish:

- shared higher-dimensional causal Value geometry;
- within-problem low-dimensional causal Value codes;
- shared + problem-specific private geometry;
- globally and locally distributed Value geometry.

---

# 27. Scientific Claims Not Allowed

Do not claim:

- vision-encoder origin;
- projector feature origin;
- MLP neuron/feature mechanism;
- Q/R long-term memory;
- evidence A→B refresh;
- correct-vs-wrong failure mechanisms;
- discrete LOOK/THINK states.

---

# 28. Decision After Stage 3B.9

The default scientific transition after a technically valid Stage 3B.9 is:

## GO — Multi-Evidence Causal Refresh

Use if Phase A/B produce any coherent geometry outcome:

- shared higher-dimensional;
- local low-dimensional;
- shared + private;
- broadly distributed.

Rationale:

> The single-evidence ROI→Value→head pathway has been characterized sufficiently. The next central Thinking-MLLM question is whether different evidence items are causally retrieved at different reasoning times.

Next high-level question:

```text
Evidence A ROI → Value path → A-dependent reasoning
then later
Evidence B ROI → Value path → B-dependent reasoning
```

This returns to the project's original long-form reasoning question using causal mechanisms rather than raw attention.

## REDIRECT — Geometry mechanics invalid

Use only if:

- v3 endpoint reconstruction fails;
- multi-counterfactual variants cannot be made semantically valid;
- held-out local interventions are technically uninterpretable.

Do not continue indefinitely searching for a prettier single-evidence geometry.

---

# 29. Output Structure

Create:

```text
outputs/stage3b9/
  history/
    immutable_stage3b8_result.md

  config/
    stage3b9_config.json
    frozen_targets.json
    frozen_rank_family.json
    cohort_split.json
    decision_rules.json

  phase_a_shared/
    historical_training_manifest.jsonl
    fresh_confirmation_manifest.jsonl
    exclusions.jsonl
    basis/
      target_a_rank_bases.npz
      target_b_rank_bases.npz
      sham_bases.npz
      random_basis_seeds.json
    scoring/
      full_v_results.jsonl
      learned_rank_results.jsonl
      complement_results.jsonl
      sham_rank_results.jsonl
      random_rank_results.jsonl
    analysis/
      rank_curve_statistics.json
      shared_geometry_decision.json

  phase_b_local/
    cohort_manifest.jsonl
    value_variant_manifest.jsonl
    edit_validation/
    roi_overlays/
    applicability_gate.json
    local_deltas/
    scoring/
      leave_one_value_out_full.jsonl
      local_rank_results.jsonl
      local_complement_results.jsonl
      global_matched_results.jsonl
      random_local_results.jsonl
    analysis/
      local_rank_statistics.json
      local_vs_global_statistics.json
      local_geometry_decision.json

  phase_c_secondary/
    metadata_manifest.jsonl
    principal_angles.json
    projector_similarity.json
    exploratory_clusters.json

  analysis/
    geometry_outcome_matrix.json
    format_stratification.json
    attention_secondary.json
    figures/

  summaries/
    stage3b9_summary.md
    stage3b9_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3B.8 or earlier artifacts.

---

# 30. Required Figures

At minimum:

1. fresh-confirmed shared recovery vs rank for Target A;
2. same for Target B;
3. shared orthogonal-complement recovery vs rank;
4. learned vs random vs sham subspace curves;
5. representative per-base shared-rank curves;
6. within-problem multi-value causal geometry examples;
7. leave-one-value-out local recovery vs local rank;
8. local vs matched-global recovery;
9. local-subspace principal-angle distribution;
10. global-vs-local outcome summary;
11. secondary format stratification;
12. secondary attention-vs-geometry comparison.

---

# 31. Acceptance Criteria

Stage 3B.9 technically passes if:

1. Stage 3B.8 result remains immutable;
2. exact Stage 3B.8 v3 representation is reused;
3. exact two causal targets remain frozen;
4. the 57 historical Stage 3B.8 bases are training/design only;
5. at least 24 fresh Phase-A confirmation bases are disjoint from prior geometry cohorts;
6. shared candidate ranks are frozen before fresh scoring;
7. semantic, sham-derived, and random bases are materialized before fresh scoring;
8. Phase-A scoring is bidirectional and self-controlled;
9. no fresh-confirmation example influences shared-basis fitting;
10. at least 12 separate Phase-B bases support five valid semantic image values each;
11. Phase-B values are chosen before Value-vector analysis;
12. local testing uses leave-one-value-out semantic generalization;
13. local rank is limited to 1–3;
14. global-vs-local comparison uses matched ranks where possible;
15. `base_problem_id` remains the statistical unit;
16. raw attention remains secondary only;
17. mixture analysis is explicitly secondary;
18. no vision-encoder/MLP/Q-R/failure experiment is started;
19. no further single-evidence rescue stage is automatically launched;
20. an explicit `GO — Multi-Evidence Causal Refresh` or `REDIRECT` recommendation is written.

Technical PASS does not require any particular geometry hypothesis to win.

---

# 32. Stop Condition

After:

- historical shared-basis construction;
- fresh Phase-A rank-curve confirmation;
- fresh multi-counterfactual Phase-B construction;
- leave-one-value-out local geometry;
- global-vs-local comparison;
- optional frozen secondary mixture diagnostics;
- final geometry classification;
- final recommendation;

**STOP.**

Do not start:

- another shared-rank rescue;
- another local-rank rescue;
- cluster-specific confirmatory training;
- vision-encoder localization;
- projector-feature analysis;
- Q/R lifecycle analysis;
- multi-evidence A/B causal refresh;
- correct-vs-wrong failure analysis.

Return the complete Stage 3B.9 results for review.

The next plan must be determined only after jointly considering Stage 3B.9 with all prior Stage 2A–3B.8 evidence.
