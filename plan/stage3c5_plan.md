# Stage 3C.5 Plan — Behaviorally Necessary Visual Window and State Handoff

## 0. Purpose

Stage 3C.5 follows the Stage 3C.4 result:

> **Target-ROI evidence support is temporally redundant across immediately preceding reasoning queries, with the largest additional behavioral loss appearing when suppression expands from the current query to include the immediately preceding query.**

Stage 3C.4 found:

```text
all-layer target-ROI suppression

T0: current query only
median retention = 0.8436

T1: [t*-1, t*]
median retention = 0.6515

T2: [t*-2, t*]
median retention = 0.5952

T4: [t*-4, t*]
median retention = 0.5653

T8: [t*-8, t*]
median retention = 0.5588

T16: [t*-16, t*]
median retention = 0.5519
```

The largest incremental loss occurred at:

```text
T0 → T1
```

with median added unnormalized loss:

```text
1.3069
```

At the same time, Stage 3C.4 showed a significant layer-depth component, but even all-layer current-only removal retained substantial evidence.

The strongest bounded interpretation is therefore:

> **The current evidence decision is supported by target-ROI information acquired over more than one reasoning query, with the immediately preceding query carrying especially important behaviorally relevant visual support.**

Stage 3C.5 asks two ordered questions:

### WHERE within the immediately preceding query?

> **Which layer region at `t*-1` is behaviorally necessary for target-ROI visual evidence acquisition?**

### WHERE does that evidence go?

> **After entering at `t*-1`, which nonvisual/current-state carrier preserves the evidence into `t*` and supports the evidence decision?**

The target mechanistic chain is:

```text
target ROI at t*-1
        ↓
critical layer/window
        ↓
current reasoning state / previous reasoning state
        ↓
t* computation
        ↓
evidence decision
```

This stage does **not** manipulate attention sinks.

Sink causality remains deferred until the behaviorally necessary retrieval/handoff mechanism is clearer.

---

# 1. Scientific Handoff

## Stage 3B.2

Switching only future all-visual K/V semantic identity at `E_d-1` and `E_d` changed upcoming evidence identity strongly and bidirectionally.

Therefore:

> late visual-source identity is causally important.

## Stage 3B.7-R

The Stage 3A edited ROI was causally localized as the dominant visual source for the late W4 Value pathway.

## Stage 3C.3-R

Current-position W4 target-ROI contribution could be removed with almost no behavioral loss.

Therefore:

> the W4 target-ROI path is causally steerable but not individually necessary.

## Stage 3C.4

Same-time layer expansion increased behavioral loss, but even all-layer current-only removal retained median 0.8436.

Expanding one query earlier caused the largest additional loss:

```text
T0 0.8436
T1 0.6515
```

Target A was more sensitive:

```text
T0 0.7819
T1 0.4638
T16 0.3683
```

Target B was more robust:

```text
T0 0.8971
T1 0.8122
T16 0.7650
```

Therefore the next causal question is not “does late vision matter?” but:

> **What is special about the immediately preceding query, and how is its retrieved evidence handed forward?**

---

# 2. Frozen Targets

Reuse exactly the two historical targets.

## Target A

```text
decision coordinate: E_d
historical W4 target layer: 29
historical causal heads: [11, 6, 15, 12]
```

## Target B

```text
decision coordinate: E_d - 1
historical W4 target layer: 28
historical causal heads: [16, 0, 3, 6]
```

Define:

```text
t* = target retrieval/evidence coordinate
t_pre = t* - 1
```

Target ROI `T` remains the exact Stage 3B.7-R counterfactual edit ROI.

Do not redefine T using attention or Stage 3C.5 effects.

---

# 3. Primary Cohort

Reuse the exact:

```text
24 Stage 3C.3 / Stage 3C.3-R / Stage 3C.4 primary base_problem_ids
```

Primary statistical unit:

```text
base_problem_id
```

No exclusion may depend on Stage 3C.5 causal effects.

If a new mechanical audit excludes a base, record the reason before scientific scoring.

Minimum:

```text
20 valid bases
```

---

# 4. Stage Structure

Stage 3C.5 contains two primary phases.

## Phase A — Layer localization at `t_pre`

Hold temporal scope fixed to the immediately preceding query and localize where target-ROI contribution matters.

## Phase B — State-handoff localization

After identifying a behaviorally important `t_pre` layer/window, determine which state at `t*` carries the evidence forward.

A small Phase C may test natural handoff continuity only after A/B freeze.

Do not run sink causality.

---

# PHASE A — NECESSARY VISUAL WINDOW AT t_pre

## 5. Core Question

> **Which layer region at the immediately preceding query supplies the behaviorally necessary target-ROI support identified by Stage 3C.4 T1?**

Stage 3C.4 all-layer T1 was behaviorally important, but it did not localize the layer contribution of `t_pre` itself.

Stage 3C.5 isolates `t_pre`.

---

# 6. Intervention Semantics

Reuse the exact Stage 3C.4 target-contribution object:

```text
c_T(t,l,h)
=
sum_{j in T}
alpha(t,l,h,j) * V(l,h,j)
```

At `t_pre` only:

```text
c_T(t_pre,l,h) → 0
```

for frozen layer/head scopes.

Keep unchanged at the direct intervention site:

```text
Q
K
V vectors
attention probabilities
non-target source contributions
all queries outside t_pre
```

Downstream layers and the next query `t*` recompute naturally.

This is crucial:

> **Any effect measured at `t*` is caused by removing target-ROI visual contribution one reasoning step earlier, not by directly modifying the `t*` state.**

---

# 7. Frozen Layer Family at t_pre

Use prospectively fixed scopes.

## P0 — W4 only

```text
layers 28–29
all heads
t_pre only
```

## P1 — W5 only

```text
layers 32–33
all heads
t_pre only
```

## P2 — W4 + W5

```text
layers 28–33
all heads
t_pre only
```

## P3 — Late layers

```text
layers 24–35
all heads
t_pre only
```

## P4 — Mid + late

```text
layers 16–35
all heads
t_pre only
```

## P5 — All layers

```text
layers 0–35
all heads
t_pre only
```

Do not add or remove scopes after scoring.

---

# 8. Phase-A Baselines

Run:

```text
A0: native
A1: current-only all-layer target suppression at t*
A2: t_pre-only all-layer target suppression
A3: [t_pre, t*] all-layer suppression
```

A1 and A3 should reproduce Stage 3C.4 T0 and T1 respectively.

This allows comparison of:

```text
current-only effect
t_pre-only effect
joint two-query effect
```

without assuming additivity.

---

# 9. Phase-A Readouts

Primary behavioral readout:

```text
frozen evidence-preference score at the target decision
```

Also record at `t*`:

```text
h_pre evidence readout
h_post_attn evidence readout
final logits
```

These state readouts are descriptive in Phase A.

Do not patch them yet.

---

# 10. Phase-A Metrics

For each scope `Pk`:

```text
Loss_Pk = D_native - D_Pk
```

Descriptive retention:

```text
Ret_Pk = D_Pk / D_native
```

Do not clip.

Primary inference uses unnormalized loss.

Also report:

```text
incremental t_pre necessity
=
Loss_[t_pre,t*] - Loss_[t*,t*]
```

descriptively.

Do not interpret this difference as a unique causal fraction.

---

# 11. Phase-A Outcome Categories

## A1 — W4-local t_pre retrieval

If P0 causes most of the t_pre-only behavioral effect.

## A2 — W5-local t_pre retrieval

If P1 dominates.

## A3 — Late distributed t_pre retrieval

If P0/P1 are weak but P2/P3 are strong.

## A4 — Broad-depth t_pre retrieval

If P4/P5 are required.

## A5 — No localized t_pre layer

If even P5 t_pre-only is weak but joint `[t_pre,t*]` suppression is strong.

Interpretation:

> the T1 effect depends on interaction/recomputation across both queries rather than a simple isolated t_pre contribution.

Preserve this as a valid result.

---

# 12. Phase-A Gate to State Handoff

Proceed to Phase B if either:

1. a `t_pre` layer/window causes a robust behaviorally meaningful loss, or
2. the all-layer `t_pre` intervention causes a robust effect even if no narrow layer dominates.

If `t_pre`-only all-layer suppression is behaviorally null while joint T1 remains strong:

> redesign around two-query state interaction rather than forcing a single-query handoff.

STOP and review before Phase B.

---

# PHASE B — STATE HANDOFF LOCALIZATION

## 13. Core Question

> **After visual evidence is acquired at `t_pre`, which state at `t*` carries that evidence into the decision?**

Primary candidate carriers:

```text
Q/P = prompt/question-side cached states
R = previous generated reasoning states
h_pre(t*) = current-position residual before the target block
```

Because Stage 3B.0 already showed a small Q-side prefill visual residual, Q must be tested but should not be assumed dominant.

Because `t_pre` is itself a previous reasoning token by `t*`, the most direct live candidate is:

```text
R_pre = state/cache associated with the immediately preceding reasoning token
```

---

# 14. Donor/Recipient Semantic Conditions

Use the frozen paired semantic image classes:

```text
O
O_sham
C
C_sham
```

Primary handoff logic is bidirectional:

```text
O → C
C → O
```

with paired within-semantic sham controls.

The key is to transfer only the candidate nonvisual carrier while holding the recipient image condition and other states fixed.

---

# 15. Primary State-Handoff Arms

At `t*`, define candidate carrier groups.

## H0 — Native recipient

No patch.

## H1 — Immediate previous reasoning token carrier

Patch the state/cache associated with the `t_pre` reasoning token from donor semantic condition into recipient.

Prospectively freeze one exact representation before scoring:

```text
preferred:
t_pre reasoning-token K/V entry at a frozen layer family

alternative if mechanics are cleaner:
t_pre residual state at a frozen boundary
```

Do not combine the two definitions post hoc.

## H2 — Short recent reasoning window

Only if H1 is partial but nonzero, test:

```text
R_last2
R_last4
```

as a nested family.

## H3 — Question/prompt carrier

Patch Q-side cached K/V using the Stage 3B.0-compatible definition.

## H4 — Current-position h_pre(t*)

Patch donor-semantic `h_pre` at the frozen target layer into recipient and allow downstream computation to recompute naturally.

This is the strongest current-state carrier test.

---

# 16. Carrier Interpretation

These arms answer different questions.

### R-token K/V patch

> Is evidence accessible from prior generated reasoning states as a source to the current query?

### Q patch

> Is evidence carried by image-conditioned prompt/question cache?

### h_pre patch

> Is evidence already integrated into the current reasoning residual before the local target computation?

Do not collapse them into one “text memory” category.

---

# 17. Gated Carrier Order

### Step 1

Test:

```text
R_last1
Q
h_pre
```

### Step 2

Only if `R_last1` is partial but nonzero, test:

```text
R_last2
R_last4
```

Do not automatically expand to the whole reasoning history.

---

# 18. State-Patch Controls

Every carrier patch must include:

```text
self O→O
self C→C
semantic O→C
semantic C→O
O↔O_sham
C↔C_sham
```

Verify:

- exact token identity alignment;
- exact cache-position alignment;
- no visual K/V replacement;
- no unintended current-query patch;
- finite outputs;
- deterministic repeatability.

---

# 19. Carrier Metric

Reuse the evidence-preference score.

For carrier `S` define bidirectional semantic restoration:

```text
BCR_S
=
0.5 * (
  donor-O shift into C recipient
  +
  donor-C shift into O recipient
)
```

Use unnormalized BCR as primary.

Descriptive normalized recovery:

```text
CRR_S = BCR_S / reference_gap
```

Do not clip.

Do not interpret as a unique information fraction.

---

# 20. Reference Gap

Primary handoff reference:

```text
full semantic O↔C evidence-preference gap at t*
```

Secondary reference:

```text
Stage 3B.2 all-visual source-switch effect
```

Do not change the reference after seeing results.

---

# 21. Handoff Outcome Categories

## H1 — Immediate R carrier

If `R_last1` robustly transfers evidence identity.

Conclusion:

> **Visual evidence acquired at t_pre is carried forward in the immediately preceding reasoning-token state/cache.**

## H2 — Short R accumulation

If `R_last1` is partial but `R_last2`/`R_last4` recover more.

Conclusion:

> evidence is distributed across a short recent reasoning history.

## H3 — Q carrier

If Q patch is strong.

Conclusion:

> image-conditioned prompt/question states remain a meaningful late carrier.

## H4 — Current residual carrier

If h_pre patch is strong while Q/R source patches are weak.

Conclusion:

> evidence has already been integrated into the current residual state before the target local computation.

## H5 — Mixed carrier

Multiple sources transfer semantic identity.

Preserve mixed/redundant interpretation.

---

# 22. Link Between Phase A and Phase B

The strongest combined test is:

```text
t_pre target-ROI suppression
→ loss of evidence at t*
```

together with:

```text
donor t_pre/R/current-state patch
→ restoration of evidence at t*
```

A positive pair would support:

```text
target ROI at t_pre
→ nonvisual state carrier
→ t* evidence decision
```

This is the desired handoff mechanism.

---

# PHASE C — HANDOFF CONTINUITY, SECONDARY ONLY

## 23. Optional Continuity Analysis

After Phase A/B freeze, track evidence-state continuity across:

```text
t_pre
→ t*
```

using only frozen/descriptive quantities:

- donor/recipient residual-difference norms;
- frozen evidence-direction projection if available from prior stages;
- state-patch effect sizes.

Do not fit a new probe/subspace on the primary cohort.

---

# 24. Target Heterogeneity

Preserve Target A and Target B separately.

Given Stage 3C.4:

```text
Target A:
strong T1 sensitivity

Target B:
greater robustness through T16
```

it is plausible that:

- Target A has a stronger immediate handoff;
- Target B relies on broader/earlier accumulated support.

Do not pool away this difference.

---

# 25. Target-Specificity Controls

For the strongest Phase-A `t_pre` layer/window, run reduced controls:

```text
mention ROI M suppression
irrelevant ROI I suppression
```

at `t_pre`.

Expected:

```text
T effect > M/I effect
```

Do not run the full Phase-A layer family for controls unless compute is trivial.

---

# 26. Stage 3C.2 / 3C.3 Connection

After primary results freeze, compare the behaviorally necessary `t_pre` window with:

```text
QK_T sharpening
target attention
target alphaV
candidate sink release
```

from Stage 3C.2/3C.3.

Question:

> Does the previously observed retrieval phenotype overlap the newly localized necessary visual-acquisition window?

This is descriptive triangulation only.

Do not infer sink causality.

---

# 27. Sink Deferral

Do not manipulate `<|im_start|>` or any candidate sink.

If Phase A localizes a behaviorally necessary retrieval window and Stage 3C.2 sink release overlaps that window, then a later stage may test sink causality.

Provisional name:

```text
Stage 3C.6 — Attention Sink Causality
```

---

# 28. Primary Statistical Family

Primary unit:

```text
base_problem_id
```

Frozen family:

## Phase A

1. t_pre P0 vs native
2. t_pre P1 vs native
3. t_pre P2 vs native
4. t_pre P3 vs native
5. t_pre P4 vs native
6. t_pre P5 vs native
7. t_pre-only vs current-only
8. joint [t_pre,t*] vs current-only
9. monotonic layer-scope trend

## Phase B, gated

10. R_last1 semantic restoration
11. Q semantic restoration
12. h_pre semantic restoration
13. R_last1 vs Q
14. R_last1 vs h_pre
15. Q vs h_pre

Secondary, only if R_last1 partial:

16. R_last2
17. R_last4

Apply Holm correction where appropriate.

Use unnormalized evidence effects as primary.

---

# 29. Main Scientific Outcomes

## O1 — Immediate Visual-to-R Handoff

If:

```text
t_pre target suppression hurts
+
R_last1 patch restores semantic identity
```

then:

> **The model acquires target visual evidence at the immediately preceding reasoning query and carries it forward through the prior-reasoning state/cache.**

## O2 — Immediate Visual-to-Current-Residual Handoff

If:

```text
t_pre target suppression hurts
+
h_pre(t*) patch restores
+
R/Q patches weak
```

then:

> evidence is integrated into the current residual state rather than stored in a directly readable token-source cache.

## O3 — Mixed Short-History Handoff

If multiple recent R states are needed.

## O4 — Q-Side Carry

If Q remains unexpectedly strong.

## O5 — No Clean Carrier

If Phase A shows a necessary visual window but no candidate state patch transfers evidence robustly.

Then the handoff is distributed/nonlinear and requires a new design.

---

# 30. Scientific Boundary

Stage 3C.5 may establish:

- which layer region at `t_pre` carries behaviorally necessary target evidence;
- whether evidence is handed into R/Q/current residual;
- whether the immediately preceding query supports the next decision through a nonvisual carrier.

Stage 3C.5 does **not** establish:

- sink causal function;
- exact retrieval-trigger feature;
- whole-history memory lifecycle;
- vision-encoder origin;
- multi-evidence refresh;
- failure mechanisms;
- discrete LOOK/THINK states.

---

# 31. Decision After Stage 3C.5

Recommend exactly one next direction.

## GO — Attention Sink Causality

Use if:

- a behaviorally necessary retrieval window is localized;
- Stage 3C.2 sink release overlaps that window;
- state handoff is sufficiently understood.

## GO — Recent-Reasoning Carrier Refinement

Use if R_last1/R_last2/R_last4 show a clear but distributed handoff.

## GO — Current-Residual Mechanism

Use if h_pre is the dominant carrier.

## REDIRECT — Two-Query Interaction Mechanism

Use if t_pre-only is weak but joint `[t_pre,t*]` suppression is strong.

Do not automatically start any next stage.

---

# 32. Output Structure

```text
outputs/stage3c5/
  config/
    stage3c5_config.json
    frozen_targets.json
    tpre_layer_scopes.json
    carrier_family.json
    primary_family.json

  cohort/
    validation_manifest.jsonl
    primary_manifest.jsonl
    exclusions.jsonl

  audit/
    tpre_query_index_audit.json
    contribution_definition.json
    layer_scope_audit.json
    state_patch_alignment.json
    cache_position_audit.json
    reconstruction_validation.json
    reproducibility.json

  phase_a_tpre_layer/
    per_problem_tpre_scope_results.jsonl
    baseline_reproduction.json
    tpre_layer_statistics.json

  phase_b_handoff/
    r_last1_results.jsonl
    r_last2_results.jsonl
    r_last4_results.jsonl
    q_results.jsonl
    hpre_results.jsonl
    sham_controls.jsonl
    handoff_statistics.json

  controls/
    mention_tpre_suppression.jsonl
    irrelevant_tpre_suppression.jsonl

  secondary/
    retrieval_phenotype_overlap.json
    continuity_analysis.json

  analysis/
    necessary_window_analysis.json
    carrier_comparison.json
    target_heterogeneity.json
    handoff_classification.json
    figures/

  summaries/
    stage3c5_summary.md
    stage3c5_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3C.4 or earlier artifacts.

---

# 33. Required Figures

At minimum:

1. t_pre evidence loss vs layer scope for Target A;
2. same for Target B;
3. t_pre-only vs current-only vs joint two-query suppression;
4. per-base t_pre layer-scope curves;
5. R_last1 semantic restoration;
6. Q semantic restoration;
7. h_pre semantic restoration;
8. carrier comparison across bases;
9. R_last1/R_last2/R_last4 nested recovery if gated;
10. Target A vs Target B handoff profile;
11. target vs mention/irrelevant t_pre suppression;
12. overlap with Stage 3C.2 QK/attention/alphaV phenotype;
13. final handoff-mechanism summary.

---

# 34. Acceptance Criteria

Stage 3C.5 technically passes if:

1. exact Stage 3C.4 target ROI and contribution semantics are reused;
2. exact two target coordinates remain frozen;
3. `t_pre=t*-1` is computed exactly for every base;
4. at least 20 primary bases remain valid;
5. t_pre layer scopes are frozen before scoring;
6. current-only and joint T1 baselines reproduce Stage 3C.4;
7. t_pre suppression changes only target-ROI contribution at t_pre;
8. queries outside t_pre remain native in Phase A;
9. downstream propagation is allowed naturally;
10. Phase B runs only if the t_pre handoff gate passes;
11. carrier representations are frozen before Phase-B scoring;
12. state/cache positions are aligned exactly;
13. no visual K/V donor patch occurs in the handoff experiment;
14. self semantic patches are transparent;
15. paired sham controls are implemented;
16. R/Q/h_pre remain separately interpreted;
17. `base_problem_id` remains the statistical unit;
18. no sink manipulation is run;
19. no Stage 4/failure experiment is started;
20. exactly one next-stage recommendation is written.

Technical PASS does not require a clean carrier.

---

# 35. Stop Condition

After:

- mechanical validation;
- t_pre layer localization;
- current-only/t_pre-only/joint comparison;
- gated R/Q/h_pre handoff localization;
- reduced target-specificity controls;
- descriptive overlap with prior retrieval phenotype;
- final handoff classification;
- exactly one recommendation;

**STOP.**

Do not start:

- sink knockout or redistribution;
- whole-history Q/R search;
- earlier-than-t_pre handoff rescue;
- vision-encoder localization;
- Stage 4 multi-evidence refresh;
- failure analysis.

Return the complete Stage 3C.5 results for review.

The next stage must be chosen only after jointly considering Stage 3C.5 with all prior Stage 2A–3C.4 evidence.
