# Stage 3B.7-R Plan — Revalidated ROI-Specific Visual Path and K/V Decomposition

## 0. Purpose

Stage 3B.7 stopped **before any primary-cohort scoring** because one of the two frozen ROI-path validation targets failed the preregistered semantic-control gate.

That failure is scientifically meaningful and must remain immutable.

Stage 3B.7-R is a **new prospective redesign**. It does not reinterpret the failed Stage 3B.7 threshold, reuse the failed gate as a PASS, or retroactively rescue the original `E_d-1/W4/Top_2` target.

The goals are:

1. preserve the independently clean target;
2. replace the sham-sensitive target with a prospectively frozen, previously confirmed head set;
3. validate both targets on a **fresh disjoint cohort**;
4. use a more stable paired semantic-vs-control margin rather than a sham/semantic ratio whose denominator can approach zero;
5. only then score the untouched 37-base primary cohort;
6. run K-only / V-only / K+V decomposition only for targets that pass the new ROI-path gate.

The central research questions remain:

> **Which visual-token positions feed the causal late Attention heads?**

and, only after ROI localization:

> **Is evidence identity carried mainly by routing/selection through K, transmitted content through V, or their interaction?**

---

# 1. Immutable Stage 3B.7 Failure Record

The original Stage 3B.7 validation result must remain unchanged.

Completed before failure:

- exact 37-base primary cohort frozen and untouched;
- disjoint 8-base validation cohort scored;
- exact Stage 3A edited-pixel ROIs, complements, fixed rings, and matched irrelevant regions constructed;
- query-head-selective K-only, V-only, and K+V mechanics implemented and unit-tested;
- all mechanical, determinism, and source-isolation checks passed.

Semantic validation:

```text
E_d/W4/Top_4
median BPR = 0.8364
bidirectional fraction = 0.875
median sham/semantic = 0.1143
PASS

E_d-1/W4/Top_2
median BPR = 0.2138
bidirectional fraction = 0.750
median sham/semantic = 0.2699
FAIL under frozen <0.25 rule
```

The one permitted diagnostic found:

- modest absolute sham shift;
- near-zero semantic restoration on bases 83 and 101.

Interpretation:

> The failure was not mechanical. The `Top_2` target was not sufficiently robust relative to its sham behavior on the frozen validation set.

No threshold may be relaxed retrospectively.

No original Stage 3B.7 primary result exists.

---

# 2. Scientific Handoff From Stage 3B.6

Stage 3B.6 confirmed several head/head-set units before ROI analysis.

For:

```text
E_d/W4
```

confirmed units included:

```text
Top_4
Top_8
```

For:

```text
E_d-1/W4
```

confirmed units included:

```text
Top_2
Top_4
Top_8
```

Therefore replacing the failed `Top_2` ROI target with `Top_4` does **not** require a new head search.

`Top_4` was already a frozen, independently confirmed Stage 3B.6 unit.

However, choosing it as the replacement ROI-path target occurs after seeing the Stage 3B.7 validation failure.

Therefore it requires an entirely **fresh validation cohort** before any primary scoring.

---

# 3. Prospectively Frozen Targets

## Target A — retained clean target

```text
E_d / W4 / Top_4
```

Frozen heads:

```text
[11, 6, 15, 12]
```

This target passed the original Stage 3B.7 disjoint validation gate, but Stage 3B.7-R will still require fresh replication before primary inference.

---

## Target B-R — replacement target

```text
E_d - 1 / W4 / Top_4
```

Load the exact Stage 3B.6 frozen `Top_4` head list for this cell from Stage 3B.6 artifacts.

Do not infer the list from memory.

This replaces:

```text
E_d - 1 / W4 / Top_2
```

for Stage 3B.7-R primary ROI-path testing.

The failed `Top_2` target remains preserved as a historical negative validation result and must not be silently reclassified.

---

# 4. Primary Cohort Remains Untouched

Primary confirmatory cohort:

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

This cohort was not scored in Stage 3B.7 and must remain untouched until Stage 3B.7-R validation is complete.

Primary statistical unit:

```text
base_problem_id
```

Do not change this cohort after validation.

---

# 5. Fresh Validation Cohort

The original 8 Stage 3B.7 validation bases are now considered **diagnostic/history only**.

They cannot serve as the Stage 3B.7-R gate.

Construct a new disjoint validation cohort:

## Target size

```text
12–16 unique numeric-label bases
```

## Minimum

```text
12 valid bases
```

The fresh validation cohort must be disjoint from:

- the untouched 37-base primary cohort;
- the original 8 Stage 3B.7 validation bases;
- any Stage 3B.7-R target-selection diagnostic set.

Selection must not use attention or Stage 3B.7-R causal outcomes.

---

# 6. How to Obtain Fresh Validation Bases

First search existing previously generated completed-correct examples that satisfy:

1. unique base problem;
2. localized numeric visual fact;
3. valid strict counterfactual edit;
4. valid semantic-preserving sham;
5. exact source-token layout alignment;
6. valid Stage 3A-style evidence preference pair;
7. manual ROI mapping possible;
8. no overlap with prior validation or primary cohorts.

If fewer than 12 valid examples exist, prospectively collect additional MathVerse examples using the locked Stage 1 generation protocol.

For newly collected validation examples:

- do not use attention for inclusion;
- construct O/O_sham/C/C_sham before causal scoring;
- manually validate all images;
- freeze E_d and ROI definitions before Stage 3B.7-R scoring.

Do not expand the 37-base primary cohort with these new validation cases.

---

# 7. ROI Definitions

Reuse the same conceptual ROI definition as Stage 3B.7.

For every validation/primary base:

```text
V_target = visual-token positions overlapping the exact Stage 3A edited evidence region
V_other  = all visual tokens \ V_target
```

Also prospectively define:

```text
V_irrelevant
```

as a cardinality-matched, disjoint, task-irrelevant visual-token region where feasible.

Do not use raw attention to define any ROI.

---

# 8. ROI Mapping Audit

For every fresh validation base:

1. reproduce exact preprocessing;
2. map edited pixels to merged visual-token positions;
3. manually inspect overlays;
4. record target token count;
5. freeze complement;
6. freeze matched irrelevant region;
7. record ambiguity/rejection reason.

For the 37 primary bases, reuse the already frozen Stage 3B.7 ROI mappings unless a documented mechanical bug is discovered.

Do not revise primary mappings after seeing Stage 3B.7-R outcomes.

---

# 9. Why the Validation Statistic Is Redesigned

The original Stage 3B.7 validation used a ratio:

```text
|sham effect| / |semantic effect|
```

with a frozen threshold.

This ratio becomes unstable when the semantic denominator is near zero.

The failed `Top_2` target exposed exactly this issue on some validation cases.

Stage 3B.7-R therefore uses a **prospectively defined paired semantic-vs-control margin** as the primary semantic-validity gate.

This new statistic applies only to Stage 3B.7-R.

It must not be used to reinterpret the original Stage 3B.7 failure.

---

# 10. Primary Validation Metrics

For each base and target define source-oriented bidirectional effects.

Let:

```text
S_target_i
```

= bidirectional target-ROI semantic restoration effect.

Let:

```text
S_sham_i
```

= matched within-semantic sham restoration effect.

Let:

```text
S_irrelevant_i
```

= matched irrelevant-ROI restoration effect.

Define paired margins:

\[
M^{sham}_i
=
S^{target}_i
-
|S^{sham}_i|
\]

\[
M^{irr}_i
=
S^{target}_i
-
|S^{irrelevant}_i|
\]

These margins directly test whether the target semantic effect exceeds control perturbations.

Primary validation uses the distribution of these margins, not a ratio with a potentially tiny semantic denominator.

---

# 11. Fresh Validation Gate — Per Target

Each target is gated **independently**.

A target passes Stage 3B.7-R validation only if all conditions hold:

## Mechanical gates

1. self swap is transparent;
2. non-target heads remain recipient-native;
3. source-position isolation is exact;
4. bidirectional swap mechanics pass;
5. deterministic repetition passes;
6. finite scores only;
7. all-V source effect reproduces the Stage 3B.6 target tendency;
8. K/V mechanics remain valid under GQA.

## Semantic gates

9. median target semantic restoration is positive;
10. bootstrap 95% CI for median target semantic restoration excludes zero on the positive side;
11. bidirectional source-consistency fraction is at least 0.75;
12. median \(M^{sham}\) is positive;
13. bootstrap 95% CI for median \(M^{sham}\) excludes zero on the positive side;
14. median \(M^{irr}\) is positive;
15. bootstrap 95% CI for median \(M^{irr}\) excludes zero on the positive side.

The old sham/semantic ratio is retained only as a **secondary diagnostic**.

Do not use it as the primary Stage 3B.7-R gate.

---

# 12. Target-Specific Gating Rule

Unlike the original Stage 3B.7 global stop, Stage 3B.7-R prospectively uses **target-specific eligibility**.

Possible outcomes:

### Both A and B-R pass

Proceed with both targets on the untouched 37-base primary cohort.

### A passes, B-R fails

Proceed with **Target A only** on the untouched primary cohort.

Record B-R as a failed fresh-validation target.

Do not try Top_8 or another replacement in the same stage.

### A fails, B-R passes

Proceed with **Target B-R only**.

The previous Stage 3B.7 A validation cannot override a fresh Stage 3B.7-R failure.

### Both fail

STOP.

Do not score the 37-base primary cohort.

REDIRECT away from ROI-specific localization.

This rule is frozen before fresh validation outcomes are read.

---

# 13. No Replacement Cascade

If Target B-R (`Top_4`) fails fresh validation:

- do not test Top_8 as another replacement;
- do not retune the head set;
- do not change ROI size;
- do not change semantic thresholds.

Any further replacement would be a new stage requiring separate review.

---

# 14. Phase A — Primary ROI-Path Scoring

Only for fresh-validation-eligible targets.

Score the untouched 37-base primary cohort.

Conditions:

```text
A0  all visual
A1  target ROI
A2  visual complement
A3  matched irrelevant ROI
A4  target + frozen surrounding ring (secondary)
```

All conditions:

- bidirectional O→C and C→O;
- self-controlled;
- paired-sham controlled;
- query-head selective;
- source-group isolated.

---

# 15. Primary ROI-Path Statistics

For source region \(S\):

\[
BPR_{H,S}
=
\frac{
\Delta_{H,S,O\rightarrow C}
+
\Delta_{H,S,C\rightarrow O}
}{2}
\]

Use unnormalized BPR as primary.

All-V reference:

\[
BPR_{H,all}
\]

Descriptive recovery:

\[
PRR_{H,S}
=
\frac{BPR_{H,S}}{BPR_{H,all}}
\]

Do not clip.

Do not treat PRR as a unique information fraction.

Report:

- median BPR;
- mean BPR;
- bootstrap 95% CI;
- bidirectional consistency;
- target-vs-sham paired margin;
- target-vs-irrelevant paired margin;
- PRR relative to all-V.

Use Holm correction across the fixed eligible-target ROI family.

---

# 16. Primary ROI Localization Rule

A target qualifies for K/V decomposition only if the 37-base primary ROI result satisfies:

1. target ROI BPR robustly positive;
2. target ROI bidirectional consistency >= 0.75;
3. target-vs-sham paired margin robustly positive;
4. target-vs-irrelevant paired margin robustly positive;
5. target ROI or target+ring explains a meaningful portion of all-V restoration;
6. all mechanical checks pass.

Do not require complement to be zero.

Complement magnitude determines whether the representation is local or distributed.

---

# 17. Spatial Outcome Categories

## ROI-Local

Target ROI accounts for most all-V restoration; complement and irrelevant are small.

## ROI-Local-Plus-Context

Target is strong, and target+ring materially improves recovery.

## Visual-Distributed

Target is real but complement is also substantial, or all-V greatly exceeds target-only.

Interpretation:

> localized pixel evidence has diffused across visual-token states.

## ROI-Inconclusive

Target does not reliably exceed sham/irrelevant.

No K/V decomposition for that target.

---

# 18. Gate to Phase B

Phase B is run only for targets passing the primary ROI-localization rule.

If no target qualifies:

STOP.

Do not run K/V decomposition.

Recommend visual-representation diffusion/localization or a broader visual-token representation study.

---

# 19. Phase B — K/V Routing-vs-Content Decomposition

For each ROI-qualified target:

### B0 — recipient-native

No target ROI semantic swap.

### B1 — K-only

```text
K_target = donor
V_target = recipient
```

### B2 — V-only

```text
K_target = recipient
V_target = donor
```

### B3 — K+V

```text
K_target = donor
V_target = donor
```

All interventions:

- use recipient current query;
- affect only the frozen causal head/head-set;
- preserve non-target query heads;
- preserve non-target source positions;
- allow downstream computation to recompute naturally;
- run bidirectionally;
- include self and paired-sham controls.

K+V must reproduce the primary target-ROI path effect within tolerance.

---

# 20. K/V Metrics

For \(M \in \{K,V,KV\}\):

\[
BKV_M
=
\frac{
\Delta_{M,O\rightarrow C}
+
\Delta_{M,C\rightarrow O}
}{2}
\]

Use unnormalized BKV as primary.

Descriptive ratios:

\[
KVR_K = BKV_K / BKV_{KV}
\]

\[
KVR_V = BKV_V / BKV_{KV}
\]

Do not clip.

Do not interpret as additive information fractions.

Descriptive interaction:

\[
I_{KV}
=
BKV_{KV}
-
BKV_K
-
BKV_V
\]

---

# 21. K/V Outcome Categories

## Value-Dominant

V-only robustly approaches K+V while K-only is small.

Interpretation:

> semantic evidence identity is transmitted mainly through visual Value content.

## Routing-Dominant

K-only robustly approaches K+V.

Interpretation:

> semantic routing/selection toward visual positions is a major causal mechanism.

## Routing + Value

Both are robust; K+V remains stronger.

Interpretation:

> retrieval depends jointly on where-to-read routing and what-is-read content.

## Nonlocal / Distributed

ROI K/V effects remain weak despite strong all-V visual-source restoration.

Interpretation:

> semantic evidence is not confined to the edited ROI at the LM visual-token interface.

---

# 22. Optional Attention-Probability Analysis

Do not run an alpha/pattern-only intervention unless B1–B3 are fully validated.

If run, it is secondary.

Requirements:

- exact self transparency;
- probability normalization audit;
- paired sham controls;
- frozen target/head/ROI;
- no redefinition based on K/V outcomes.

Raw attention magnitude remains descriptive.

---

# 23. Secondary Attention Triangulation

Only after causal ROI/KV results are frozen, compare:

1. raw Stage 2C ROI attention;
2. causal head ROI attention;
3. ROI BPR;
4. K-only BKV;
5. V-only BKV.

This comparison may sharpen the existing methodological finding:

> **attention magnitude, causal routing, and causal transmitted content are distinct quantities.**

Do not use attention to define the causal result.

---

# 24. Interpretation of the Original Top_2 Failure

The failed Stage 3B.7 `E_d-1/W4/Top_2` target should remain visible in the final Stage 3B.7-R report.

Possible interpretation if B-R Top_4 passes:

> a broader confirmed head set is required for stable ROI-level semantic restoration one step before the discriminative decision.

This would be consistent with a more distributed head mechanism at `E_d-1`.

However, this is a **post-stage interpretation only**.

Do not define the new experiment as proving why Top_2 failed.

If B-R also fails, retain the stronger conclusion:

> ROI-level localization at `E_d-1/W4` is not robust under current controls.

---

# 25. What Stage 3B.7-R May Establish

If supported:

## ROI-specific causal path

> A visual-token region defined independently by the counterfactual evidence edit causally feeds the previously localized late Attention head/set.

## Temporal concentration difference

If A passes but B-R remains weaker or fails:

> ROI-specific evidence retrieval may become more causally concentrated at the discriminative decision than one step earlier.

This requires appropriate evidence and must not be inferred from validation failure alone.

## Value-mediated evidence transport

If V-only dominates:

> evidence identity is carried mainly by transmitted visual Value content rather than attention weight magnitude itself.

## Routing-mediated retrieval

If K-only dominates:

> semantic routing to the relevant visual positions is causally important.

## Distributed visual representation

If all-V remains strong but target ROI is incomplete:

> localized image evidence is represented across a broader visual-token field before retrieval.

---

# 26. What Stage 3B.7-R Cannot Establish

Do not claim:

- exact vision-encoder feature;
- causal vision-encoder layer;
- MLP feature/neuron mechanism;
- long-term Q/R memory lifecycle;
- multi-evidence A→B refresh;
- correct-vs-wrong failure mechanism;
- discrete LOOK/THINK state.

---

# 27. Decision After Stage 3B.7-R

Recommend exactly one next direction.

## GO — Value-content mechanism

Use if ROI localization is robust and V-only dominates.

## GO — Attention routing mechanism

Use if ROI localization is robust and K-only/routing dominates.

## GO — Routing + Value mechanism

Use if both are required.

## GO — Visual representation diffusion

Use if a causal visual source exists but target ROI is insufficient and complement/all-V effects indicate spatially distributed encoding.

## REDIRECT — ROI localization not robust

Use if no prospectively eligible target yields a robust primary ROI effect.

---

# 28. Output Structure

Create:

```text
outputs/stage3b7r/
  history/
    immutable_stage3b7_failure.md

  config/
    stage3b7r_config.json
    target_definitions.json
    validation_primary_split.json
    primary_family.json

  validation_cohort/
    candidate_screening.jsonl
    fresh_validation_manifest.jsonl
    exclusion_log.jsonl
    edit_validation/
    roi_overlays/

  roi_audit/
    roi_token_mapping.jsonl
    irrelevant_roi_manifest.jsonl
    roi_mapping_report.md

  validation/
    mechanical_validation.json
    semantic_validation_results.jsonl
    semantic_validation_statistics.json
    validation_report.md
    eligible_targets.json

  scoring/
    all_visual_results.jsonl
    target_roi_results.jsonl
    complement_results.jsonl
    irrelevant_roi_results.jsonl
    ring_results.jsonl
    k_only_results.jsonl
    v_only_results.jsonl
    kv_results.jsonl

  analysis/
    roi_path_statistics.json
    paired_margin_statistics.json
    spatial_localization_analysis.json
    kv_decomposition_statistics.json
    kv_interaction_analysis.json
    attention_secondary_analysis.json
    figures/

  summaries/
    stage3b7r_summary.md
    stage3b7r_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3B.7 or earlier artifacts.

---

# 29. Required Figures

At minimum:

1. fresh validation target BPR vs sham for Target A;
2. same for replacement Target B-R;
3. paired semantic-vs-sham margin distributions;
4. paired semantic-vs-irrelevant margin distributions;
5. primary all-V / target / complement / irrelevant comparison for each eligible target;
6. target/all-V recovery distribution;
7. K-only / V-only / K+V for each ROI-qualified target;
8. per-problem K vs V scatter;
9. old failed Top_2 validation shown separately from new Top_4 validation;
10. representative ROI overlays and semantic flips.

---

# 30. Acceptance Criteria

Stage 3B.7-R technically passes if:

1. the original Stage 3B.7 failure remains immutable and explicitly documented;
2. no original threshold is relaxed retrospectively;
3. Target A and replacement Target B-R are prospectively frozen;
4. Target B-R uses a Stage 3B.6-confirmed head set rather than a new head search;
5. at least 12 fresh validation bases are disjoint from both old validation and primary cohorts;
6. fresh validation selection does not use attention or causal outcomes;
7. O/O_sham/C/C_sham edits are manually validated;
8. ROI mappings and irrelevant controls are frozen before scoring;
9. self/source/head-isolation mechanics pass;
10. target-specific validation eligibility is decided using the new paired-margin gate;
11. the old sham/semantic ratio is secondary only;
12. no replacement cascade occurs if B-R fails;
13. the 37-base primary cohort is scored only for fresh-validation-eligible targets;
14. Phase B occurs only for targets passing the primary ROI gate;
15. K-only/V-only/K+V remain query-head selective under GQA;
16. K+V reproduces target-ROI restoration;
17. `base_problem_id` remains the statistical unit;
18. attention remains secondary only;
19. no vision-encoder/Q-R/multi-evidence/failure experiment is started;
20. an explicit GO / REDIRECT recommendation is produced.

Technical PASS does not require both targets to pass or one K/V mechanism to dominate.

---

# 31. Stop Condition

After:

- fresh validation cohort construction;
- immutable failure documentation;
- Target A / Target B-R fresh validation;
- target-specific eligibility freeze;
- eligible-target primary ROI scoring;
- gated K/V decomposition;
- sham/irrelevant/self controls;
- secondary attention triangulation;
- final recommendation;

**STOP.**

Do not start:

- additional target replacement;
- Top_8 rescue;
- vision-encoder localization;
- K/Q feature analysis;
- Value-subspace feature analysis;
- Q/R lifecycle analysis;
- multi-evidence A/B refresh;
- correct-vs-wrong failure analysis.

Return the complete Stage 3B.7-R results for review.

The next plan must be determined only after jointly considering Stage 3B.7-R with all prior Stage 2A–3B.7 evidence.
