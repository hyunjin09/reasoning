# Stage 3C.7 Plan — Prior-Cache Rescue and Residual Joint Rescue

## 0. Purpose

Stage 3C.7 follows the Stage 3C.6 result:

> **The actual behavioral deficit created by suppressing target-ROI visual contribution at the immediately preceding query (`t_pre=t*-1`) is only partially recoverable from the current-position residual at `t*`.**

Stage 3C.6 produced:

```text
Scientific outcome:
O4 — Residual Insufficiency

Target A:
P4 suppression loss = 0.5528
peak h_pre RR = 0.6035 at L35
strongest confirmed detailed boundary:
L33 h_post_attn
median rescue gain = 0.2014
median RR = 0.4162

Target B:
P4 suppression loss = 0.3035
peak h_pre RR = 0.3410 at L35
no qualifying four-layer detailed region
```

The key causal constraint is:

> **Restoring only the current residual does not fully repair the deficit while the `t_pre` past-token cache remains in the suppressed state.**

Stage 3C.5 had also shown that cross-image `R_last1` K/V semantic transplantation was weak, but that intervention mixed different semantic/image states and may have suffered state mismatch.

Stage 3C.7 therefore uses a cleaner within-condition intervention:

```text
Native-O vs Suppressed-O
Native-C vs Suppressed-C
```

and asks two ordered questions.

### Q1 — Prior-cache rescue

> **Does restoring the native `t_pre` reasoning-token cache into the matching suppressed run rescue the actual visual-suppression deficit?**

### Q2 — Joint rescue

> **Do the native `t_pre` cache and the native current residual jointly rescue substantially more than either state alone?**

The target mechanism is:

```text
target ROI at t_pre
        ↓
broad visual acquisition
        ↓
t_pre reasoning-token cache
     + current residual at t*
        ↓
two-query interaction
        ↓
evidence decision
```

This stage does not run token-type carrier analysis or attention-sink causality.

---

# 1. Scientific Handoff

## Stage 3C.4

The largest incremental behavioral loss occurred when target-ROI suppression expanded from:

```text
current query only
```

to:

```text
[t_pre, t*]
```

Therefore the immediately preceding reasoning query is behaviorally important.

## Stage 3C.5

At `t_pre`, target evidence acquisition was broad-depth:

```text
P4 = layers 16–35
```

was the smallest frozen scope explaining at least 80% of all-layer `t_pre` loss.

Coarse semantic carrier patches were weak:

```text
R_last1 CRR = 0.0719
Q       CRR = 0.0109
h_pre   CRR = 0.1832
```

## Stage 3C.6

The real within-condition P4 suppression deficit was only partly rescued by current residual transplantation.

Therefore:

```text
current residual != complete carrier
```

A major unresolved possibility is:

> **The suppressed `t_pre` reasoning-token K/V cache remains behaviorally relevant at `t*`, and full handoff requires interaction between that cache and the evolving current residual.**

Stage 3C.7 directly tests this.

---

# 2. Frozen Targets

Reuse exactly the two historical targets.

## Target A

```text
target coordinate: E_d
t_pre: E_d - 1
historical target layer: 29
historical causal heads: [11, 6, 15, 12]
P4 suppression scope: layers 16–35
```

Frozen residual rescue boundary for the joint test:

```text
L33 h_post_attn
```

This is the strongest confirmed Stage 3C.6 detailed boundary.

## Target B

```text
target coordinate: E_d - 1
t_pre: E_d - 2
historical target layer: 28
historical causal heads: [16, 0, 3, 6]
P4 suppression scope: layers 16–35
```

Frozen residual rescue boundary for the joint test:

```text
L35 h_pre
```

This is the Stage 3C.6 peak broad-scan h_pre rescue layer.

Target A and B must remain separately interpreted.

---

# 3. Primary Cohort

Reuse the exact:

```text
24 Stage 3C.3–3C.6 primary base_problem_ids
```

Primary statistical unit:

```text
base_problem_id
```

No exclusion may depend on Stage 3C.7 rescue effects.

If a base fails a new cache-alignment/mechanical audit, record the exclusion before scientific scoring.

Minimum:

```text
20 valid bases
```

---

# 4. Primary Deficit

Reuse exactly the Stage 3C.5 / Stage 3C.6 within-condition P4 suppression:

```text
at t_pre only
layers 16–35
all 32 logical heads
target ROI T contribution
c_T(t_pre,l,h) → 0
```

Primary semantic conditions:

```text
Native-O
Suppressed-O
Native-C
Suppressed-C
```

All primary rescue comparisons are within condition:

```text
Native-O ↔ Suppressed-O
Native-C ↔ Suppressed-C
```

No cross-image semantic donor is used in the primary rescue.

---

# 5. Why This Is Cleaner Than Stage 3C.5 R_last1 Patching

Stage 3C.5 asked:

```text
Does O's prior-reasoning cache transfer O-vs-C semantic identity into C?
```

That is a cross-image state transplant.

Stage 3C.7 asks:

```text
Within the same image semantics,
does restoring the native cache repair the exact deficit
created by removing t_pre target-ROI visual contribution?
```

Thus donor and recipient share:

- image identity;
- prompt;
- token history;
- evidence fact;
- candidate continuation;
- positional structure.

They differ only because one run experienced the frozen P4 target-ROI suppression at `t_pre`.

This sharply reduces semantic-state mismatch.

---

# 6. Prior-Cache Object

For the immediately preceding generated reasoning token `t_pre`, at language layer `l` define its cached:

```text
K_pre(l)
V_pre(l)
```

using the exact model-native cache representation:

- post-RoPE K;
- projected V;
- exact KV-head layout before query-head expansion.

Because Qwen3-VL uses GQA, the cache is defined in native KV-head space.

Do not construct per-query-head fake caches.

---

# 7. Native vs Suppressed Cache Difference

For each layer:

```text
Delta K_pre(l) = K_pre_native(l) - K_pre_supp(l)
Delta V_pre(l) = V_pre_native(l) - V_pre_supp(l)
```

Note:

- at layers before suppression-induced divergence, native/suppressed cache entries may be identical;
- after the `t_pre` visual contribution alters the residual, later-layer cache entries may diverge.

Record these deltas descriptively before rescue analysis.

Do not use their magnitude to select layers.

---

# 8. Mandatory Cache Audit

Before primary scoring verify:

1. exact `t_pre` token index;
2. exact token identity;
3. exact cache position;
4. exact post-RoPE K semantics;
5. exact projected V semantics;
6. exact KV-head count/layout;
7. native and suppressed image/prompt caches are otherwise identical where expected;
8. visual prompt K/V are never patched;
9. current-query K/V are never patched in cache-only arms;
10. cache replacement affects only the `t_pre` token entry;
11. all other previous-reasoning cache entries remain suppressed-recipient native;
12. self native→native cache patches are exact;
13. self suppressed→suppressed patches are exact;
14. deterministic repeatability;
15. finite scores.

Create:

```text
outputs/stage3c7/audit/
  tpre_cache_layout.json
  cache_position_alignment.json
  native_suppressed_cache_deltas.json
  cache_patch_selectivity.json
  visual_cache_invariance.json
  current_query_invariance.json
  self_patch_validation.json
  reproducibility.json
```

---

# 9. Validation Cohort

Use the exact seven disjoint Stage 3C.6 validation bases if mechanically valid.

Validation must cover:

- K-only patch;
- V-only patch;
- K+V patch;
- residual-only rescue reproduction;
- joint rescue;
- exact cache-position isolation;
- exact visual-cache invariance;
- deterministic repeatability.

Do not tune rescue scopes using validation effect size.

---

# PHASE A — PRIOR-CACHE RESCUE

## 10. Primary Cache Scope

Primary cache rescue uses the same broad layer family implicated by `t_pre` visual acquisition:

```text
layers 16–35
```

For every layer in P4, replace only the `t_pre` cache entry.

Primary K+V rescue:

```text
K_pre_supp(l) → K_pre_native(l)
V_pre_supp(l) → V_pre_native(l)
```

for `l = 16…35`.

All other cached positions remain suppressed-recipient native.

The current-position residual at `t*` remains suppressed-recipient native.

---

# 11. Phase-A Arms

For each target and semantic condition run:

## C0 — Native

No suppression.

## C1 — Suppressed

P4 target-ROI suppression at `t_pre`.

## C2 — K-only prior-cache rescue

```text
K_pre: suppressed → native
V_pre: suppressed
```

across layers 16–35.

## C3 — V-only prior-cache rescue

```text
K_pre: suppressed
V_pre: suppressed → native
```

across layers 16–35.

## C4 — K+V prior-cache rescue

```text
K_pre: suppressed → native
V_pre: suppressed → native
```

across layers 16–35.

Downstream current-query computation recomputes naturally.

---

# 12. Why K vs V Is Informative Here

This is **not** the earlier visual-token K/V experiment.

Here K/V belong to the **previous reasoning token**.

Possible interpretations:

### Prior-cache K rescue

The previous reasoning token's addressability/routing relation to the current query matters.

### Prior-cache V rescue

The previous reasoning token carries behaviorally useful content.

### K+V-only rescue

Routing and content of the previous reasoning token interact.

Do not assume the same Value-dominant pattern as the visual ROI.

---

# 13. Cache Rescue Metric

For each base and condition:

```text
D_native
D_supp
D_cache
```

Suppression loss:

```text
L = D_native - D_supp
```

Cache rescue gain:

```text
G_cache = D_cache - D_supp
```

Descriptive rescue ratio:

```text
RR_cache = G_cache / L
```

Do not clip.

Use unnormalized rescue gain as primary.

O and C are sign-aligned before within-base aggregation.

---

# 14. Phase-A Questions

1. Does native `t_pre` cache rescue the real suppression deficit?
2. Is rescue stronger through K, V, or K+V?
3. Is Target A more cache-dependent than Target B?
4. Does cache rescue complement the partial current-residual rescue from Stage 3C.6?
5. Does the cache carry enough information to justify a token-local carrier analysis later?

---

# 15. Phase-A Outcome Categories

## C-Value

V-only rescue is robust and approaches K+V.

## C-Key

K-only rescue is robust and approaches K+V.

## C-KV

K+V is substantially stronger than either alone.

## C-Weak

K+V prior-cache rescue is small.

Interpretation:

> the single `t_pre` cache entry is not a sufficient carrier by itself.

This does not end the stage because joint rescue may still be strong.

---

# PHASE B — RESIDUAL + PRIOR-CACHE JOINT RESCUE

## 16. Core Question

> **Does the prior `t_pre` cache explain the portion of the suppression deficit that current-residual rescue could not recover?**

The primary comparison is:

```text
cache-only
residual-only
cache + residual
```

under the exact same suppressed recipient.

---

# 17. Frozen Residual Boundaries

## Target A

```text
L33 h_post_attn
```

from Stage 3C.6.

## Target B

```text
L35 h_pre
```

from Stage 3C.6.

Do not reselect boundaries using Stage 3C.7 cache results.

---

# 18. Residual-Only Reproduction

Before the joint intervention, reproduce:

```text
Suppressed current residual
→ Native current residual
```

at the frozen target-specific boundary.

Past `t_pre` cache remains suppressed.

This must reproduce the Stage 3C.6 rescue score within frozen tolerance.

Call this:

```text
G_resid
```

---

# 19. Why Joint Rescue Needs a Downstream-Cache Definition

A residual patch at a late boundary overwrites the upstream current-position consequences of earlier cache access.

Therefore a clean joint test must distinguish:

```text
cache effects before the residual boundary
```

from:

```text
cache access that remains available after the residual boundary
```

For the primary joint intervention:

> patch the native residual at the frozen boundary **and** restore native `t_pre` cache only in Attention layers that occur at or after the next usable Attention operation downstream of that boundary.

This asks:

> **Once the current residual is repaired, does continued access to the native previous-token cache provide additional behavioral rescue?**

---

# 20. Target-A Joint Cache Scope

Target A residual boundary:

```text
L33 h_post_attn
```

After this boundary:

- layer 33 Attention has already executed;
- layer 33 MLP remains;
- future Attention operations are layers 34–35.

Therefore primary downstream cache scope:

```text
Target A:
t_pre K/V cache at layers 34–35
```

Joint arm:

```text
native L33 h_post_attn
+
native t_pre K/V at layers 34–35
```

inside the suppressed run.

---

# 21. Target-B Joint Cache Scope

Target B residual boundary:

```text
L35 h_pre
```

The next Attention operation is layer 35.

Therefore primary downstream cache scope:

```text
Target B:
t_pre K/V cache at layer 35
```

Joint arm:

```text
native L35 h_pre
+
native t_pre K/V at layer 35
```

inside the suppressed run.

---

# 22. Primary Joint Arms

For each target:

## J0 — Suppressed

No rescue.

## J1 — Residual only

Frozen Stage 3C.6 residual rescue.

## J2 — Full prior-cache only

Native `t_pre` K+V across P4 layers 16–35.

## J3 — Downstream prior-cache only

Native `t_pre` K+V only in the frozen downstream cache scope defined above.

## J4 — Residual + downstream prior-cache

Native residual at frozen boundary plus native downstream `t_pre` K+V.

This is the primary clean joint-rescue condition.

---

# 23. Optional Full-Cache + Residual Arm

As a secondary operational intervention, also run:

```text
native t_pre K+V across P4
+
native residual at frozen boundary
```

Label:

```text
J5 — full-cache + residual
```

Interpret cautiously:

> cache effects occurring before the residual boundary may be overwritten by the residual transplant.

Therefore J5 is a practical total rescue condition, not an additive decomposition.

Primary mechanistic interpretation uses J4.

---

# 24. Joint Rescue Metrics

Define:

```text
G_cache_full
G_cache_down
G_resid
G_joint
```

Descriptive ratios:

```text
RR_cache
RR_resid
RR_joint
```

Do not clip.

Primary joint increment:

```text
Delta_joint_over_resid
=
G_joint - G_resid
```

This asks whether downstream native prior-cache access adds rescue after current residual restoration.

Secondary descriptive interaction:

```text
I_joint
=
G_joint - G_resid - G_cache_down
```

Do not interpret `I_joint` as a unique causal interaction fraction.

---

# 25. Joint Outcome Categories

## J-Residual-Dominant

```text
G_resid large
G_joint ≈ G_resid
```

## J-Cache-Dominant

```text
G_cache_full large
G_resid weak
```

## J-Complementary

```text
G_resid partial
G_cache partial
G_joint substantially larger than both
```

## J-Synergistic-Two-Query

```text
joint rescue approaches full deficit recovery
while both single rescues remain modest
```

## J-Insufficient

Even joint rescue remains weak.

Interpretation:

> evidence support is distributed beyond the single `t_pre` cache and current residual pair.

---

# 26. Prospectively Frozen Joint Rescue Thresholds

Call a joint rescue behaviorally substantial if:

```text
median RR_joint >= 0.50
```

and:

- bootstrap CI for unnormalized `G_joint` excludes zero;
- at least 75% of bases have positive rescue.

Call it near-complete if:

```text
median RR_joint >= 0.80
```

under the same robustness conditions.

These are descriptive sufficiency thresholds, not information fractions.

---

# 27. K/V Decomposition Gate

K-only and V-only are primary Phase-A arms.

For the joint downstream cache component, run K-only/V-only decomposition only if:

```text
J4 joint rescue is substantial
```

for that target.

Then compare:

```text
residual + downstream K
residual + downstream V
residual + downstream K+V
```

Do not run this gated decomposition if J4 is weak.

---

# 28. Negative Controls

Run exact self controls:

```text
native cache → native
suppressed cache → suppressed
native residual → native
suppressed residual → suppressed
```

All must reproduce baselines.

Also run a reduced mechanical negative control:

> replace Q/prompt cache entries in the suppressed run with matching native-run Q/prompt cache entries.

Because the P4 suppression occurs during generation after prefill, these caches should be identical or nearly identical.

Expected rescue:

```text
~0
```

This is not a new Stage 3B.0 carrier test.

---

# 29. State Integrity

During cache-only rescue:

- current residual stays suppressed;
- current query stays suppressed;
- visual K/V remain unpatched.

During residual-only rescue:

- all past caches stay suppressed.

During joint rescue:

- only the frozen residual boundary and frozen `t_pre` cache entries are restored.

Audit these cases separately.

---

# 30. Optional Rollout

Only after primary teacher-forced results freeze, optionally run matched-seed rollouts for:

```text
Suppressed
Residual only
Cache only
Joint
```

at the strongest target.

Secondary only.

---

# 31. Relationship to Stage 3C.5 R_last1

After Stage 3C.7 freezes, compare:

```text
Stage 3C.5 cross-image semantic R_last1 patch
vs
Stage 3C.7 within-condition native/suppressed cache rescue
```

Possible outcomes:

### Cross-image weak, within-condition strong

> prior cache is behaviorally useful, but cross-semantic cache transplantation was state-mismatched.

### Both weak

> single-token cache is unlikely to be the main carrier.

### Both strong

> strong evidence for prior reasoning-token cache as a carrier.

---

# 32. Relationship to Stage 3C.6 Residual Rescue

The central comparison is:

```text
G_cache
G_resid
G_joint
```

Target A and Target B remain separate.

Do not pool away heterogeneity.

---

# 33. Token-Type Carrier Atlas Deferral

Do not run exhaustive token-type scans in Stage 3C.7.

If native `t_pre` cache rescue is strong:

> the next token-local question becomes meaningful.

If native `t_pre` cache rescue is weak:

> sparse token-local carrier analysis becomes lower priority.

---

# 34. Sink-Causality Deferral

Do not manipulate `<|im_start|>` or any sink-like position.

Sink causality remains deferred until the state handoff mechanism is sufficiently understood.

---

# 35. Primary Statistical Family

Primary unit:

```text
base_problem_id
```

Analyze Target A and B separately.

## Phase A

1. K-only cache rescue > 0
2. V-only cache rescue > 0
3. K+V cache rescue > 0
4. K+V vs K
5. K+V vs V

## Phase B

6. residual-only rescue reproduction > 0
7. downstream-cache-only rescue > 0
8. residual + downstream-cache rescue > 0
9. joint vs residual-only
10. joint vs downstream-cache-only
11. full-cache-only vs residual-only
12. full-cache + residual secondary total rescue

Apply Holm correction within the fixed target-specific family.

Use unnormalized rescue gains as primary.

---

# 36. Main Scientific Outcomes

## O1 — Prior-Cache Carrier

If within-condition native `t_pre` cache strongly rescues the suppression deficit:

> **The immediately preceding reasoning token's cache carries behaviorally useful consequences of visual evidence acquisition.**

## O2 — Residual-Cache Complementarity

If both cache and current residual are partial, but joint rescue is substantially stronger:

> **Visual evidence handoff is jointly maintained by prior-token cache and current residual state.**

## O3 — Two-Query Synergy

If joint rescue approaches full recovery while each single rescue remains weak:

> **The behaviorally necessary handoff is an interaction across consecutive reasoning queries rather than a single-state memory trace.**

## O4 — Residual-Dominant

If prior cache adds little beyond residual rescue:

> **The current residual is the primary tested carrier; cache differences are secondary.**

## O5 — Distributed Beyond Last-Token Cache + Residual

If joint rescue remains weak:

> **The handoff requires broader recent-history caches, other residual states, or a distributed multi-state mechanism.**

---

# 37. Scientific Boundary

Stage 3C.7 may establish:

- whether the native `t_pre` prior cache rescues the actual suppression deficit;
- whether K, V, or K+V of the prior reasoning token matters;
- whether prior cache and current residual are complementary;
- whether a two-query interaction explains more than either carrier alone.

Stage 3C.7 does **not** establish:

- universal token-type carrier roles;
- whole-history memory lifecycle;
- sink function;
- upstream retrieval-trigger features;
- vision-encoder origin;
- multi-evidence refresh;
- failure mechanisms.

---

# 38. Decision After Stage 3C.7

Recommend exactly one next direction.

## GO — Token-Type Carrier Atlas

Use if prior-cache rescue is strong enough to justify token-local carrier analysis.

## GO — Broader Recent-Cache Interaction

Use if last-token cache + residual joint rescue is still insufficient but cache contribution is nonzero.

## GO — Residual Feature Mechanism

Use if residual dominates and cache adds little.

## GO — Attention Sink Causality

Use only if the handoff ambiguity is sufficiently resolved and sink-release overlaps the behaviorally necessary retrieval window.

Do not start follow-on work automatically.

---

# 39. Output Structure

```text
outputs/stage3c7/
  config/
    stage3c7_config.json
    frozen_targets.json
    suppression_definition.json
    cache_scope.json
    residual_boundaries.json
    joint_intervention_definition.json
    primary_family.json

  cohort/
    validation_manifest.jsonl
    primary_manifest.jsonl
    exclusions.jsonl

  audit/
    tpre_cache_layout.json
    cache_position_alignment.json
    native_suppressed_cache_deltas.json
    cache_patch_selectivity.json
    visual_cache_invariance.json
    current_state_invariance.json
    residual_reproduction.json
    joint_patch_order.json
    self_patch_validation.json
    reproducibility.json

  phase_a_cache/
    k_only_results.jsonl
    v_only_results.jsonl
    kv_results.jsonl
    cache_rescue_statistics.json
    cache_delta_statistics.json

  phase_b_joint/
    residual_only_results.jsonl
    downstream_cache_only_results.jsonl
    joint_results.jsonl
    full_cache_plus_residual_results.jsonl
    joint_statistics.json
    optional_joint_kv_decomposition.jsonl

  controls/
    q_prompt_negative_control.jsonl
    self_controls.jsonl

  secondary/
    optional_rollouts.jsonl
    stage3c5_r_last1_comparison.json
    stage3c6_residual_comparison.json

  analysis/
    prior_cache_mechanism.json
    residual_cache_complementarity.json
    target_heterogeneity.json
    two_query_classification.json
    figures/

  summaries/
    stage3c7_summary.md
    stage3c7_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3C.6 or earlier artifacts.

---

# 40. Required Figures

At minimum:

1. K-only / V-only / K+V cache rescue for Target A;
2. same for Target B;
3. per-base cache rescue distributions;
4. native / suppressed / cache-rescued evidence scores;
5. residual-only vs cache-only vs joint rescue for A;
6. same for B;
7. joint rescue ratio distribution;
8. joint-over-residual incremental rescue;
9. joint-over-cache incremental rescue;
10. full-cache vs downstream-cache rescue;
11. Target A vs Target B mechanism comparison;
12. cache-delta norm vs rescue gain;
13. Stage 3C.5 cross-image R_last1 vs within-condition cache rescue;
14. Stage 3C.6 residual rescue vs Stage 3C.7 joint rescue.

---

# 41. Acceptance Criteria

Stage 3C.7 technically passes if:

1. exact Stage 3C.6 target definitions are reused;
2. exact P4 `t_pre` suppression is reproduced;
3. native/suppressed runs remain within the same semantic image condition;
4. exact `t_pre` cache position is frozen;
5. cache patches use native GQA KV-head representation;
6. visual prompt K/V are never patched;
7. current-query K/V are never patched in cache-only arms;
8. all non-`t_pre` past cache positions remain suppressed-recipient native;
9. K-only, V-only, and K+V cache rescues are mechanically isolated;
10. Stage 3C.6 residual-only rescue is reproduced;
11. target-specific residual boundaries are frozen before Stage 3C.7 scoring;
12. downstream-cache scopes are frozen from boundary semantics, not effect size;
13. joint patch order is explicitly audited;
14. self native→native and suppressed→suppressed patches are exact;
15. Target A and B remain separately interpreted;
16. unnormalized rescue gain is primary;
17. rescue ratios are unclipped and not treated as unique fractions;
18. no token-type carrier scan or sink intervention is run;
19. no Stage 4/failure experiment is started;
20. exactly one next-stage recommendation is written.

Technical PASS does not require strong cache or joint rescue.

---

# 42. Stop Condition

After:

- cache-layout validation;
- K/V/K+V prior-cache rescue;
- exact Stage 3C.6 residual-rescue reproduction;
- downstream-cache-only rescue;
- residual + downstream-cache joint rescue;
- optional gated joint K/V decomposition;
- target heterogeneity analysis;
- final two-query mechanism classification;
- exactly one recommendation;

**STOP.**

Do not start:

- exhaustive token-type carrier analysis;
- R_last2/R_last4 rescue;
- sink knockout or redistribution;
- residual feature learning;
- Stage 4 multi-evidence refresh;
- failure analysis.

Return the complete Stage 3C.7 results for review.

The next stage must be chosen only after jointly considering Stage 3C.7 with all prior Stage 2A–3C.6 evidence.
