# Stage 3C.6 Plan — Suppression-to-Residual Rescue Scan

## 0. Purpose

Stage 3C.6 follows the Stage 3C.5 result:

> **The immediately preceding query `t_pre=t*-1` carries behaviorally relevant target-ROI visual support, but the necessary visual contribution is broad-depth and no clean Q/R token-cache carrier was identified.**

Stage 3C.5 found:

```text
t_pre target-ROI suppression

P0  layers 28–29: median evidence loss 0.0292
P1  layers 32–33: median evidence loss 0.0200
P2  layers 28–33: median evidence loss 0.0631
P3  layers 24–35: median evidence loss 0.2412
P4  layers 16–35: median evidence loss 0.5172
P5  layers 0–35:  median evidence loss 0.4979
```

The prospectively selected behaviorally important `t_pre` scope was:

```text
P4 = layers 16–35
```

State-carrier restoration at `t*` was partial:

```text
R_last1 median CRR = 0.0719
Q       median CRR = 0.0109
h_pre   median CRR = 0.1832
```

with strong target heterogeneity:

```text
Target A h_pre CRR = 0.3226
Target B h_pre CRR = 0.0205
```

The current strongest mechanistic lead is therefore not a sparse token-cache carrier, but an **integrated current-residual state**, especially for Target A.

Stage 3C.6 performs a more direct causal test than the prior O↔C `h_pre` semantic patch:

> **First create the actual behaviorally relevant deficit by suppressing target-ROI visual contribution at `t_pre`, then ask which current-position residual boundary at `t*` can rescue that exact deficit.**

The primary causal chain under test is:

```text
target ROI at t_pre
        ↓
broad P4 visual acquisition
        ↓
suppression-induced state deficit
        ↓
current-position residual at t*
        ↓
evidence decision
```

This is a **suppression → residual rescue** experiment.

Do not run token-type carrier analysis, sink causality, query routing, multi-evidence, or failure analysis in this stage.

---

## 1. Scientific Handoff

### Stage 3C.4

All-layer target-ROI suppression at only the current query retained substantial evidence:

```text
T0 median retention = 0.8436
```

Adding the immediately preceding query caused the largest incremental loss:

```text
T1 median retention = 0.6515
```

Therefore target evidence is temporally redundant and the immediately preceding query is behaviorally important.

### Stage 3C.5 Phase A

At `t_pre`, narrow W4/W5 suppression had little behavioral effect.

A much broader depth was needed:

```text
P4 = layers 16–35
```

Thus the relevant `t_pre` visual acquisition is broad-depth.

### Stage 3C.5 Phase B

Patching candidate nonvisual carriers from O↔C produced semantic transfer, but:

```text
R_last1: weak
Q: very weak
h_pre: strongest but heterogeneous
```

No clean universal carrier passed the frozen magnitude rule.

The strongest unresolved question is:

> **Does the causal consequence of `t_pre` visual acquisition become integrated into the current residual stream at `t*`, and if so, at which layer/boundary?**

---

## 2. Primary Targets

Reuse exactly the historical targets.

### Target A — primary mechanistic target

```text
target coordinate: E_d
historical W4 layer: 29
historical causal heads: [11, 6, 15, 12]
t_pre = E_d - 1
```

Target A is primary because Stage 3C.5 showed substantial `h_pre` semantic transfer:

```text
median h_pre CRR = 0.3226
```

### Target B — prespecified heterogeneity / robustness target

```text
target coordinate: E_d - 1
historical W4 layer: 28
historical causal heads: [16, 0, 3, 6]
t_pre = E_d - 2
```

Target B must remain separate because Stage 3C.5 showed:

```text
median h_pre CRR = 0.0205
```

Do not pool A and B into one carrier mechanism.

---

## 3. Primary Cohort

Reuse the exact:

```text
24 Stage 3C.3 / 3C.3-R / 3C.4 / 3C.5 primary base_problem_ids
```

Primary statistical unit:

```text
base_problem_id
```

No exclusion may depend on Stage 3C.6 rescue effect.

If a base fails a new mechanical audit, record the exclusion before primary rescue scoring.

Minimum:

```text
20 valid bases
```

---

## 4. Primary Deficit Condition

The recipient deficit is not an O↔C semantic mismatch.

It is the exact within-condition deficit caused by the behaviorally relevant Stage 3C.5 suppression:

```text
at t_pre only
layers 16–35 (P4)
all logical heads
target ROI T contribution
c_T(t_pre,l,h) → 0
```

Reuse the exact validated FP32 contribution-partition implementation.

Primary conditions:

```text
Native-O
Suppressed-O

Native-C
Suppressed-C
```

The primary analysis is within semantic condition:

```text
Native-O ↔ Suppressed-O
Native-C ↔ Suppressed-C
```

This avoids interpreting rescue from a donor with a different evidence identity.

O_sham / C_sham are optional secondary controls only.

---

## 5. Why Suppression→Rescue Is Stronger Than the Prior Semantic h_pre Patch

Stage 3C.5 patched:

```text
h_pre^O ↔ h_pre^C
```

This asked whether semantic image identity is present in a candidate state.

Stage 3C.6 instead asks:

```text
What state change specifically mediates the behavioral loss
caused by removing t_pre target-ROI visual contribution?
```

For each semantic condition, native and suppressed runs are identical in:

- image semantic identity;
- textual history;
- target decision;
- prompt;
- teacher-forced candidate;

and differ only by the frozen `t_pre` P4 target-contribution intervention and its downstream consequences.

Therefore rescue is anchored to an already demonstrated behavioral necessity effect.

---

## 6. Core Residual Rescue Intervention

At `t*`, let:

```text
h_native(l,b)
```

be the current-position residual state from the native run at layer `l` and boundary `b`.

Let:

```text
h_supp(l,b)
```

be the corresponding state after `t_pre` P4 suppression.

A rescue intervention is:

```text
h_supp(l,b) → h_native(l,b)
```

at the current position only.

Past-token K/V caches remain from the suppressed recipient run.

Visual K/V remain from the suppressed recipient run's native semantic image.

No donor visual cache is copied.

After the patch, all downstream computation recomputes naturally.

This tests:

> **Is the suppression-induced behavioral deficit already represented in the current residual at this boundary?**

---

## 7. Residual Boundaries

For every scanned layer `l`, define:

### B0 — `h_pre(l)`

Residual entering transformer block `l`.

### B1 — `h_post_attn(l)`

Residual after Attention output addition and before MLP.

### B2 — `h_post_block(l)`

Residual after MLP/block completion.

Because:

```text
h_post_block(l) == h_pre(l+1)
```

under the model implementation, exact equivalence must be audited.

Primary broad scan uses `h_pre`.

Boundary decomposition is gated and only run in a frozen candidate region after the broad scan.

---

## 8. Broad h_pre Rescue Scan

Primary scan:

```text
layers 0–35
```

At each layer `l`:

```text
Suppressed recipient
+
native current-position h_pre(l)
→ downstream natural recomputation
```

Do this separately for:

```text
Target A / O
Target A / C
Target B / O
Target B / C
```

Self controls:

```text
Native h_pre → Native
Suppressed h_pre → Suppressed
```

must be exact.

---

## 9. Primary Rescue Metric

For each base, semantic condition, target, and layer:

```text
D_native
D_supp
D_rescue(l)
```

Define suppression loss:

```text
L = D_native - D_supp
```

Define rescue gain:

```text
G(l) = D_rescue(l) - D_supp
```

Primary inference uses unnormalized `G(l)`.

Descriptive rescue ratio:

```text
RR(l) = G(l) / L
```

Do not clip.

Do not interpret RR as a unique causal information fraction.

Values above 1 or below 0 are allowed.

---

## 10. Signed Semantic Alignment

For O and C, align the evidence-preference sign so that:

```text
positive score = preference for the native semantic fact
```

Then aggregate O and C only after sign alignment.

Report O and C separately first.

Do not average raw unaligned scores.

---

## 11. Broad-Scan Questions

The broad `h_pre` scan asks:

1. At which layer does rescue first become reliably positive?
2. At which layer does rescue become behaviorally substantial?
3. Does rescue rise monotonically, plateau, or decay?
4. Is there a mid/late residual region that captures most of the `t_pre` suppression deficit?
5. Does Target A show a strong current-residual handoff while Target B remains weak?

---

## 12. Prospectively Frozen Rescue Thresholds

For descriptive localization define:

```text
first_20:
first layer with median RR >= 0.20

first_50:
first layer with median RR >= 0.50

first_80:
first layer with median RR >= 0.80
```

A threshold is reported only if:

- median criterion is met;
- bootstrap CI for unnormalized rescue gain excludes zero;
- at least 75% of bases have positive rescue gain.

Do not infer an exact biological-style boundary from one layer crossing.

---

## 13. Broad-Scan Outcome Categories

### R1 — Early current-residual integration

Substantial rescue appears by early/middle layers.

### R2 — Mid/late current-residual integration

Rescue emerges primarily in middle/late layers.

### R3 — Late-only rescue

Only very late residual boundaries rescue behavior.

### R4 — Transient rescue / decay

A residual patch rescues at one depth but the effect falls again downstream.

Interpretation:

> suppressed past caches or later computation reintroduce the deficit; current residual alone is not a stable carrier.

### R5 — No substantial residual rescue

Even late `h_pre` patching fails to recover the suppression loss.

Interpretation:

> the necessary handoff cannot be explained by current residual state alone.

---

## 14. Candidate Region Freeze

Freeze the detailed-region rule before examining within-block outcomes:

> Select the smallest contiguous 4-layer region containing the largest positive median slope in `h_pre` rescue, subject to at least two adjacent layers having Holm-significant positive rescue.

If no region satisfies the rule:

```text
do not run detailed boundary decomposition
```

Do not manually choose a prettier region.

---

# PHASE B — WITHIN-BLOCK RESCUE DECOMPOSITION

## 15. Gate

Run Phase B only if at least one target has:

```text
median RR >= 0.20
```

at one or more `h_pre` layers with robust positive rescue.

Target A and B are gated independently.

---

## 16. Boundary Scan in Frozen Region

For each layer in the frozen candidate region test:

```text
h_pre
h_post_attn
h_post_block
```

using the same suppression→native rescue logic.

Downstream computation recomputes naturally.

Primary question:

> Does the suppression-induced deficit become recoverable across a specific current-token block transition?

---

## 17. Boundary Gains

For layer `l` define:

```text
G_pre(l)
G_post_attn(l)
G_post_block(l)
```

Descriptive transition gains:

```text
Attention_gain(l) =
G_post_attn(l) - G_pre(l)

MLP_gain(l) =
G_post_block(l) - G_post_attn(l)
```

Do not interpret these differences as unique causal fractions.

They are state-boundary rescue increments.

---

## 18. Boundary Outcome Categories

### B-Attention integration

Robust rescue increase from:

```text
h_pre → h_post_attn
```

### B-MLP integration

Robust increase from:

```text
h_post_attn → h_post_block
```

### B-Upstream-state

Most rescue is already present at `h_pre`.

### B-Distributed / nonmonotonic

No one transition dominates.

Important:

Stage 3B.5 previously identified Attention-boundary evidence transfer under O/C semantic restoration.

Stage 3C.6 asks a different question:

> **where the actual t_pre-suppression deficit becomes rescuable inside t* current-residual computation.**

Do not assume the same boundary must dominate.

---

## 19. Residual-Delta Dose Test

For the single strongest confirmed rescue boundary per target, optionally run:

```text
delta_h = h_native - h_supp
```

and:

```text
h(lambda) =
h_supp + lambda * delta_h
```

with:

```text
lambda = 0.00
0.25
0.50
0.75
1.00
```

Question:

> Does gradually restoring the actual suppression-induced residual delta gradually rescue evidence preference?

This is secondary but provides a strong causal continuity check.

Do not extrapolate beyond 1.

---

## 20. Important Cache-Control Interpretation

When current-position residual is rescued:

```text
past t_pre K/V cache remains suppressed
```

Therefore strong rescue means:

> the current residual is sufficient to recover behavior even though the directly altered previous-token cache remains deficient.

Weak or transient rescue means:

> continued access to suppressed past-token state/caches may still matter.

---

## 21. Target-Specificity Controls

For a reduced scope, create analogous deficits using:

```text
mention ROI M suppression at t_pre/P4
irrelevant ROI I suppression at t_pre/P4
```

Then apply the strongest native residual rescue boundary.

Because M/I suppression historically caused little behavioral deficit, expected rescue gain is also small.

This verifies that large rescue is tied to the target-specific deficit rather than generic residual transplantation.

Do not use M/I to select the rescue layer.

---

## 22. Self Controls

At every tested boundary:

```text
native state → native run
suppressed state → suppressed run
```

must reproduce the unpatched result exactly or within frozen tolerance.

---

## 23. Optional Sham Control

If compute permits, repeat the strongest rescue boundary on:

```text
O_sham
C_sham
```

using within-condition native-vs-suppressed runs.

Secondary only.

---

## 24. Relationship to Stage 3C.5 h_pre Semantic Patch

After all Stage 3C.6 causal results freeze, compare:

```text
Stage 3C.5 O↔C h_pre semantic restoration
vs
Stage 3C.6 suppression→native residual rescue
```

Possible interpretations:

### Semantic patch weak, suppression rescue strong

> h_pre may robustly carry the actual acquired-evidence consequence even if cross-image semantic transplantation is state-mismatched.

### Both strong

> strong support for current residual as an evidence carrier.

### Both weak

> current residual is unlikely to be the main carrier.

This comparison is secondary.

---

## 25. Relationship to Retrieval Phenotype

After primary results freeze, compare the localized rescue region with Stage 3C.2/3C.3:

```text
QK_T
target attention
target alphaV
candidate sink release
```

at `t_pre` and `t*`.

Descriptive triangulation only.

Do not infer attention or sink causality.

---

## 26. Primary Statistical Family

Primary unit:

```text
base_problem_id
```

Analyze Target A and Target B separately.

### Phase A

For each of 36 `h_pre` layers:

```text
G(l) > 0
```

Use Holm correction across the fixed 36-layer family per target.

Also report:

```text
first_20
first_50
first_80
peak RR
peak unnormalized rescue
```

descriptively.

### Phase B, gated

For the frozen candidate region:

```text
h_pre
h_post_attn
h_post_block
```

with Holm correction across the fixed boundary family.

Do not pool A/B p-values into one mechanism.

---

## 27. Primary Scientific Outcomes

### O1 — Current-Residual Mediation

If native residual rescue at `t*` recovers a large portion of the actual `t_pre` suppression deficit:

> **The behaviorally necessary consequence of preceding-query visual acquisition is carried forward substantially in the current-position residual stream.**

### O2 — Progressive Residual Integration

If rescue rises across depth:

> **The preceding visual-acquisition consequence is progressively integrated into the current residual during the next reasoning step.**

### O3 — Boundary-Specific Integration

If one block transition sharply increases rescue:

> **A specific current-token block operation converts the inherited deficit into a behaviorally usable residual state.**

### O4 — Residual Insufficiency

If residual rescue remains weak:

> **The necessary handoff cannot be explained by current residual state alone; prior-token caches or distributed two-query interaction remain important.**

### O5 — Target-Heterogeneous Mechanism

Expected possibility:

```text
Target A: strong residual rescue
Target B: weak residual rescue
```

Do not force one shared mechanism.

---

## 28. Scientific Boundary

Stage 3C.6 may establish:

- whether the actual causal deficit created at `t_pre` is represented in `t*` current residual;
- where across layer depth that deficit becomes rescuable;
- whether Attention/MLP/current-block transitions contribute to residual integration;
- whether Target A and Target B use different handoff mechanisms.

Stage 3C.6 does **not** establish:

- which text token type stores evidence;
- sink causal function;
- the upstream retrieval-trigger feature;
- whole-history Q/R lifecycle;
- vision-encoder origin;
- multi-evidence refresh;
- failure mechanisms.

---

## 29. Explicitly Deferred Token-Type Carrier Analysis

Do not run the proposed token-type carrier scan in Stage 3C.6.

That separate question is:

> **Does visual residual preferentially reside in entity tokens, interrogatives, relation words, function words, punctuation/boundaries, or special tokens?**

First determine whether the current residual can genuinely rescue the actual behaviorally necessary visual deficit.

---

## 30. Sink Deferral

Do not manipulate `<|im_start|>`.

Sink causality should be revisited only after determining whether the behaviorally necessary visual deficit is carried by current residual or remains dependent on prior caches.

---

## 31. Decision After Stage 3C.6

Recommend exactly one next direction.

### GO — Token-Type Carrier Atlas

Use if:

- current residual rescue is strong;
- token-cache carrier effects from Stage 3C.5 remain weak;
- the next question becomes whether a sparse token-local state feeds the integrated residual.

### GO — Residual Feature / Subspace Mechanism

Use if:

- current residual rescue is strong and broad;
- no sparse carrier is suggested.

### GO — Prior-Cache / Two-Query Interaction

Use if:

- current residual rescue is weak or transient;
- the suppressed `t_pre` cache remains necessary downstream.

### GO — Attention Sink Causality

Use only if:

- the behaviorally necessary residual/retrieval window is sufficiently characterized;
- sink-release overlaps it;
- no more fundamental handoff ambiguity remains.

Do not start any follow-on automatically.

---

## 32. Output Structure

```text
outputs/stage3c6/
  config/
    stage3c6_config.json
    frozen_targets.json
    suppression_definition.json
    residual_boundaries.json
    primary_family.json

  cohort/
    validation_manifest.jsonl
    primary_manifest.jsonl
    exclusions.jsonl

  audit/
    suppression_reproduction.json
    residual_tensor_layout.json
    boundary_equivalence.json
    current_position_selectivity.json
    past_cache_invariance.json
    self_patch_validation.json
    reproducibility.json

  phase_a_hpre_scan/
    per_problem_layer_rescue.jsonl
    target_a_layer_statistics.json
    target_b_layer_statistics.json
    threshold_crossings.json
    candidate_region_freeze.json

  phase_b_boundary/
    per_problem_boundary_rescue.jsonl
    attention_boundary_gain.json
    mlp_boundary_gain.json
    boundary_statistics.json

  phase_c_optional_dose/
    residual_delta_dose_results.jsonl
    dose_statistics.json

  controls/
    mention_deficit_rescue.jsonl
    irrelevant_deficit_rescue.jsonl
    optional_sham_rescue.jsonl

  secondary/
    stage3c5_semantic_patch_comparison.json
    retrieval_phenotype_overlap.json

  analysis/
    suppression_deficit_analysis.json
    residual_rescue_analysis.json
    target_heterogeneity.json
    current_residual_classification.json
    figures/

  summaries/
    stage3c6_summary.md
    stage3c6_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3C.5 or earlier artifacts.

---

## 33. Required Figures

At minimum:

1. Target A `h_pre` rescue ratio vs layer;
2. Target B `h_pre` rescue ratio vs layer;
3. unnormalized rescue gain vs layer for A;
4. same for B;
5. native / suppressed / peak-rescued evidence scores;
6. per-base rescue curves for A;
7. per-base rescue curves for B;
8. suppression-induced residual-delta norm vs layer;
9. rescue gain vs residual-delta norm;
10. detailed `h_pre / h_post_attn / h_post_block` rescue in the frozen region;
11. Target A vs Target B rescue profile;
12. target-deficit vs mention/irrelevant-deficit rescue control;
13. optional residual-delta dose curve;
14. Stage 3C.5 semantic h_pre patch vs Stage 3C.6 suppression-rescue comparison.

---

## 34. Acceptance Criteria

Stage 3C.6 technically passes if:

1. exact Stage 3C.5 target definitions are reused;
2. exact P4 `t_pre` suppression semantics are reused;
3. Stage 3C.5 P4 suppression loss is reproduced before rescue analysis;
4. native and suppressed runs use the same semantic image condition;
5. rescue patches only the current-position residual;
6. past-token K/V caches remain suppressed-recipient native;
7. visual K/V are never donor-patched;
8. all 36 `h_pre` layers are scanned prospectively;
9. `h_post_block(l) == h_pre(l+1)` equivalence is audited;
10. native→native and suppressed→suppressed self patches are exact;
11. Target A and B remain separately interpreted;
12. unnormalized rescue gain is primary;
13. rescue ratios are unclipped and not treated as unique fractions;
14. Phase B runs only if the `h_pre` gate passes;
15. the detailed boundary region is selected by the frozen rule;
16. target-specificity controls do not select the rescue region;
17. no token-type carrier scan is run;
18. no sink intervention is run;
19. no Stage 4/failure experiment is started;
20. exactly one next-stage recommendation is written.

Technical PASS does not require strong residual rescue.

---

## 35. Stop Condition

After:

- suppression reproduction;
- exact 36-layer `h_pre` rescue scan;
- gated within-block boundary decomposition;
- optional frozen residual-delta dose test;
- target-specificity controls;
- A/B heterogeneity analysis;
- final residual-mechanism classification;
- exactly one next-stage recommendation;

**STOP.**

Do not start:

- token-type carrier analysis;
- sink knockout or redistribution;
- earlier-history carrier search;
- residual feature/subspace learning;
- Stage 4 multi-evidence refresh;
- failure analysis.

Return the complete Stage 3C.6 results for review.

The next stage must be chosen only after jointly considering Stage 3C.6 with all prior Stage 2A–3C.5 evidence.
