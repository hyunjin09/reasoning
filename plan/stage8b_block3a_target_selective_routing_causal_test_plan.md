# Stage 8B.3A — Confirm and Causally Test Reduced Target-Selective Routing

## 0. One-line objective

Test whether the **reduced target-selective routing phenotype** observed in Stage 8B Block 2 is:

1. reproducible,
2. present within the same item across successful vs failed local reads,
3. causally related to local visual-read quality, and
4. selectively correctable by routing intervention.

The central question is:

**When active visual retrieval succeeds or fails, does target-vs-confuser routing selectivity causally control local visual-read quality?**

This stage upgrades the Block 2 descriptive candidate into a falsifiable mechanistic hypothesis.

## 1. Why this experiment is necessary for the paper

Block 1 found no robust whole-trajectory retrieval phenotype from final correctness alone.

Block 2 then localized the earliest coherent descriptive candidate at the level of **source routing**:

- retrieval activation was similar between L+ and L−;
- failed local reads showed lower target-vs-confuser QK margin;
- failed reads showed lower target-vs-confuser attention-share margin;
- failed reads showed lower target visual share;
- source entropy was higher;
- top-two source margin was smaller;
- cross-head target consensus was lower.

However, Block 2 did **not** establish a confirmed mechanism because:

- only 17 L− events / 16 families were available;
- only 12 source-localizable L− events / 11 families were available;
- matched source-routing comparisons were based on only 8–9 pairs;
- the failure-yield gate was not met;
- source-routing measurements were observational, not causal;
- many failed reads still had the target as the top annotated source.

Therefore the next paper-critical question is:

**Does reduced target selectivity causally move the model toward failed local reading, and can restoring selectivity rescue it?**

If yes, the paper gains a clean mechanistic failure story:

retrieval activates normally  
→ target routing becomes insufficiently selective  
→ local visual read fails

and potentially a mechanism-guided intervention.

## 2. Main hypothesis

The primary hypothesis is:

**Local visual-read failure is associated with, and partly caused by, insufficient separation between the demanded target source and plausible visual confusers.**

Operationally:

- target-vs-confuser QK margin
- target-vs-confuser attention-share margin

should be lower in failed reads.

The stage must then test causality in both directions.

## 3. Bidirectional causal prediction

### Prediction A — Weakening routing should degrade correct reads

Starting from L+ events with strong target selectivity, reduce target-vs-confuser separation.

Desired result:

- lower correct-evidence preference,
- higher confuser/wrong-evidence preference,
- and where identifiable, L+ shifts toward L−.

### Prediction B — Sharpening routing should improve failed reads

Starting from L− events with target-top-1 but weak target-vs-confuser margin, increase selectivity.

Desired result:

- higher correct target-supported evidence preference,
- lower confuser-supported preference,
- and where possible, L− shifts toward L+.

## 4. What a positive result supports

The strongest claim would be:

> Visual-read failures can occur despite normal retrieval activation because the model insufficiently separates the demanded source from plausible visual confusers. Manipulating this routing selectivity causally changes local visual-read quality.

A stronger intervention-level claim is allowed only if rescue is selective:

> Restoring target-selective routing improves failed reads while minimally perturbing already selective correct reads.

## 5. What a null does NOT rule out

A null routing intervention does **not** establish that the Block 2 routing pattern was spurious.

Possible explanations:

- routing differences are consequences rather than causes;
- the intervention acts on the wrong layer/head window;
- causal routing is distributed across redundant heads/layers;
- source-specific semantics are already corrupted before routing;
- target and confuser representations overlap;
- local read failure arises in visual extraction after correct routing;
- the intervention changes attention weights without changing the relevant Value transport;
- routing selectivity matters only in a subset of failure types.

Therefore nulls must be interpreted mechanistically, not as global rejection of visual routing.

## 6. Competing mechanisms to distinguish

### H1 — Insufficient routing selectivity

Retrieval activation is intact, but target-vs-confuser separation is too weak.

Prediction:
- observational replication,
- causal weakening hurts,
- causal sharpening rescues.

### H2 — Mere correlational ambiguity

Routing margins differ descriptively but do not causally control local read quality.

Prediction:
- intervention changes QK/attention but not evidence preference.

### H3 — Wrong-source top-1 failure

The confuser is already top-1.

Prediction:
- generic sharpening of the current routing distribution may worsen failure.

These events require a different correction policy from target-top-1 / low-margin events.

### H4 — Correct routing, extraction/content failure

Target routing is adequate, but the extracted visual content is wrong.

Prediction:
- routing sharpening does not rescue.

### H5 — Distributed/redundant routing

Local head/layer edits are insufficient because routing is redundantly represented.

Prediction:
- narrow intervention null;
- broader coordinated intervention may be required.

## 7. Stage structure

Stage 8B.3A has four parts:

1. **3A.0 — Freeze routing-failure subtype taxonomy and cohorts**
2. **3A.1 — Replicate routing phenotype on a same-item mixed-outcome cohort**
3. **3A.2 — Causal routing weakening on successful reads**
4. **3A.3 — Causal routing sharpening/rescue on failed reads**

Do not begin with intervention before cohort/subtype definitions are frozen.

## 8. Source-routing failure subtypes

Before intervention, classify source-localizable events using native routing only.

### R1 — Target-top-1 / low-margin

Target remains top-1, but target-vs-confuser separation is small.

This is the primary candidate for generic routing sharpening.

### R2 — Confuser-top-1

A plausible confuser outranks the demanded target.

Generic sharpening may amplify the wrong source and must not be used blindly.

### R3 — Target-top-1 / high-margin but wrong read

Routing appears selective, yet local read is wrong.

Treat as extraction/content-error candidate.

### R4 — Unresolved multi-source

Source inventory or demanded target cannot be identified reliably.

Exclude from source-specific intervention.

## 9. Primary cohort

Start from the frozen Block 2 reviewed events.

Preserve all original Block 2 labels and source geometries.

Do not modify:
- T/M/U labels,
- L+/L−/L? labels,
- demanded source,
- confuser source,
- ROI geometry,
- Block 2 replay measurements.

Block 2 source-localizable counts:
- L+: 101 events / 90 families
- L−: 12 events / 11 families

These are insufficient for strong confirmation alone.

Therefore same-item mixed-outcome expansion is permitted under the rules below.

## 10. Same-item mixed-outcome confirmation cohort

The strongest confirmation uses:

**same MathVision image + same question**

with different stochastic rollouts producing:
- at least one L+ local read,
- at least one L− local read,

for the **same semantic visual subgoal**.

This controls:
- image difficulty,
- target/confuser layout,
- demanded source identity,
- question semantics,
- visual ambiguity.

## 11. Same-item generation policy

Use the same canonical model/protocol:

- Qwen3-VL-2B-Thinking
- BF16
- temperature = 1.0
- top-p = 0.95
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 0.0
- max_new_tokens = 40960
- frozen preprocessing

Suggested:
- 4–8 seeds per selected item.

Selection of base items must be frozen before new rollouts.

Prefer items with:
- a source-localizable T event,
- a plausible confuser,
- at least one existing L− or ambiguous-routing event.

Do not select items based on intervention response.

## 12. Same-item confirmation target

Preferred target:

- **at least 32 same-item L+/L− event pairs**
- from **at least 24 unique items**

Minimum exploratory target:
- 20 pairs / 16 unique items.

If the minimum cannot be reached without excessive compute, stop and report the yield.

Do not weaken semantic event matching.

## 13. Same-subgoal event matching

Within each item:

1. identify the same demanded visual subgoal;
2. identify the corresponding active retrieval episode in each rollout;
3. verify demanded source T;
4. verify plausible confuser X;
5. classify local read as L+ or L−;
6. measure routing on the same functional layer/head window.

Do not compare unrelated retrieval episodes.

## 14. Observational replication metrics

Primary:
- target-vs-confuser QK margin
- target-vs-confuser attention-share margin

Secondary:
- target visual share
- target rank
- source entropy
- top-two source margin
- cross-head target consensus
- layer-wise target consensus

The key paired test is:

**routing selectivity in L+ > routing selectivity in L−**

within the same item/subgoal.

## 15. Replication success gate

Proceed to causal routing intervention only if at least one of the two primary routing metrics:

- target-vs-confuser QK margin,
- target-vs-confuser attention-share margin,

shows:

1. same direction as Block 2;
2. positive paired median L+ − L−;
3. bootstrap 95% CI excluding zero in the paired cohort;
4. effect present across more than one problem/source subtype.

If this gate fails, do not claim routing as the leading mechanism and do not proceed automatically to a large intervention sweep.

## 16. Causal intervention window

Use the previously localized **2B functional late retrieval window**:

- layers 19–22

Use only verified causal/replay-compatible heads within this window.

Do not assume every head contributes equally.

Interventions should be applied at the active retrieval event immediately before / during local evidence use.

## 17. Causal intervention family A — Routing weakening

Purpose:

**Does reducing target selectivity cause degradation?**

Apply only to strong L+ source-localizable events.

### A1 — Target QK attenuation

Reduce target-source QK logits in selected causal heads/layers:

s_T' = s_T - delta

while preserving other sources.

Use a small frozen dose curve.

### A2 — Target/confuser equalization

Move target and confuser logits toward equal preference while preserving overall visual mass.

Goal:
- target-vs-confuser QK margin approaches zero.

### A3 — Confuser-biased routing

For a small bounded causal test only, make the confuser exceed the target.

Use cautiously.

## 18. Weakening readout

Measure:
- correct local-evidence span CE,
- wrong/confuser evidence span CE,
- correct-vs-wrong local margin,
- next-token distribution shift,
- source-conditioned semantic followability.

Primary outcome:

**change in correct-evidence preference**

relative to self/no-op and matched sham.

A successful causal weakening effect should be dose-responsive.

## 19. Weakening controls

Required:
- no-op/self patch
- equal-norm irrelevant-source routing perturbation
- nonvisual-logit perturbation if feasible
- same magnitude at non-retrieval timing
- matched random visual-source perturbation

Purpose:
> show that degradation is specific to target-routing selectivity, not generic hidden-state disturbance.

## 20. Causal intervention family B — Routing sharpening / rescue

Purpose:

**Can increasing target selectivity rescue failed local reads?**

Primary rescue cohort:

**L− ∩ R1**

that is:
- target is already top-1,
- but target-vs-confuser margin is weak.

This is the cleanest cohort for generic sharpening.

## 21. Routing sharpening methods

### B1 — Visual routing temperature sharpening

Within the candidate visual source set:

a_j' = softmax(s_j / tau_V)

with tau_V < 1.

Suggested frozen dose curve:
- 1.0
- 0.85
- 0.70
- 0.55

This method does not require externally specifying the target if the target is already top-1.

### B2 — Target-margin boost

For mechanistic confirmation where target ROI is known:

- increase target QK logit, or
- decrease confuser QK logit,

to increase target-vs-confuser separation.

This is an oracle/source-aware causal test, not the final deployable controller.

## 22. Rescue readouts

Measure:
- correct local-evidence preference,
- wrong/confuser evidence preference,
- evidence-span CE,
- semantic counterfactual followability,
- next-token distribution shift.

Primary rescue criterion:

**correct-evidence preference under intervention > native**

with matched sham control.

Behavioral local-read correction is secondary but high-value.

## 23. Rescue selectivity

Test separately:

### Target-top-1 low-margin L−
Expected:
- correct-evidence preference improves.

### Target-top-1 high-margin L+
Expected:
- minimal change or saturation.

### Confuser-top-1 L−
Generic sharpening may worsen.

This is a critical negative control.

### Non-retrieval / mention-only events
Expected:
- little or no systematic benefit.

## 24. Critical subtype split

Do not pool:

- target-top-1 low-margin
- confuser-top-1

because the same sharpening intervention has opposite predictions.

For target-top-1 low-margin:
- sharpening may help.

For confuser-top-1:
- sharpening may reinforce the error.

This split is central to causal interpretation.

## 25. Causal success criteria

### Gate C1 — Weakening

On strong L+ events:
- target-routing weakening reduces correct-evidence preference;
- family-level median effect has expected sign;
- bootstrap 95% CI excludes zero;
- effect exceeds matched sham;
- dose response is monotonic or approximately monotonic.

### Gate C2 — Rescue

On target-top-1 / low-margin L− events:
- sharpening increases correct-evidence preference;
- effect exceeds matched sham;
- family-level median positive;
- bootstrap 95% CI excludes zero.

### Gate C3 — Selectivity

At least one of:
- already-selective L+ cases change substantially less than low-margin L−;
- non-retrieval controls show smaller effect;
- confuser-top-1 cases behave differently as predicted.

This prevents a generic “sharpen everything” interpretation.

## 26. Strongest paper claim gate

Only if:

1. observational routing replication passes;
2. weakening passes;
3. rescue passes;
4. selectivity passes;

may the paper claim:

**Target-selective visual routing is a causal control point for local visual-read quality.**

If only replication + weakening pass:
- routing contributes causally to successful reading, but rescue is not established.

If only observational replication passes:
- reduced routing selectivity remains a descriptive failure phenotype.

## 27. Null interpretation discipline

### Null in same-item replication

Does not prove Block 2 was false.

Possible:
- small original-sample fluctuation,
- source geometry mismatch,
- stochastic local errors differ in mechanism,
- subtype composition changed.

But routing should no longer be elevated as the primary failure mechanism.

### Weakening works, rescue fails

Possible:
- routing is necessary but not sufficient,
- failed reads also contain corrupted visual content,
- target sharpening cannot repair extraction errors,
- intervention timing is too late.

Do not conclude routing is irrelevant.

### Rescue works only with oracle target boost

Interpretation:
> routing is a causal handle, but a deployable target-free controller is not yet established.

### Generic sharpening worsens confuser-top-1 cases

This is expected and informative.

It establishes the need for source-state-aware intervention rather than unconditional sharpening.

## 28. Relation to prior stages

This stage directly links:

- Stage 3/4: reasoning-conditioned dynamic visual retrieval
- Stage 8A: active retrieval is passively observable online
- Block 1: final correctness alone does not yield a robust global retrieval phenotype
- Block 2: earliest coherent descriptive local-failure candidate is reduced target-selective routing
- Block 3A: test whether that routing candidate is reproducible and causal

The intended arc is:

retrieval detection  
→ local failure localization  
→ causal routing test  
→ possible mechanism-guided correction

## 29. Statistical unit

Use item/image family as the independent unit.

For same-item pairs:
- paired bootstrap over items
- sign test / Wilcoxon robustness
- paired effect sizes

For causal interventions:
- family-level paired intervention-minus-native effects
- family bootstrap
- no token-level pseudoreplication

## 30. Multiplicity discipline

Primary families:
1. same-item routing replication
2. causal weakening
3. causal rescue

Secondary:
- head/layer consensus
- attention-share decomposition
- transport changes induced by routing
- final-answer effects

Do not elevate a secondary metric if primary routing/readout effects fail.

## 31. Required controls

At minimum:
- self/no-op
- matched sham perturbation
- irrelevant visual-source perturbation
- non-retrieval timing control
- strong L+ saturation control
- confuser-top-1 negative-control subtype

Where feasible:
- matched nonvisual perturbation
- random source perturbation

## 32. Compute-efficient execution order

1. Freeze source-routing subtype definitions.
2. Reuse all Block 2 source-localizable events.
3. Generate same-item mixed-outcome rollouts only for frozen base items.
4. Seal L+/L− and source annotations.
5. Measure same-item routing replication.
6. Freeze causal intervention doses and windows.
7. Run weakening assay on strong L+ events.
8. Run sharpening/rescue assay on target-top-1 low-margin L− events.
9. Run negative controls:
   - strong L+
   - confuser-top-1 L−
   - non-retrieval timing
10. Decide whether routing becomes a confirmed causal mechanism.
11. Only then decide whether a larger intervention / Block 3B is justified.

## 33. Stop conditions

Stop this routing branch if:
- same-item replication fails;
- source-localizable L− yield is too low;
- causal weakening is null across reasonable doses/windows;
- intervention only produces generic distributional disturbance;
- rescue effects are not stronger than sham;
- apparent rescue depends on post-hoc subtype/threshold changes.

Do not expand sample size indefinitely to recover significance.

## 34. Required outputs

Produce:

1. `stage8b_block3a_routing_subtypes.json`
2. `stage8b_block3a_same_item_pairs.parquet`
3. `stage8b_block3a_routing_replication.json`
4. `stage8b_block3a_weakening_results.json`
5. `stage8b_block3a_rescue_results.json`
6. `stage8b_block3a_selectivity_controls.json`
7. `stage8b_block3a_intervention_manifest.json`
8. `stage8b_block3a_summary.md`
9. exactly one recommendation:
   - promote routing to causal mechanism,
   - retain as descriptive candidate,
   - or stop routing branch.

## 35. Key figures

### Figure 1 — Same-item L+ vs L− routing
Paired target-vs-confuser QK and attention margins.

### Figure 2 — Routing subtype map
Show:
- target-top-1 low-margin
- confuser-top-1
- target-top-1 high-margin wrong
- unresolved

### Figure 3 — Causal weakening dose response
Routing selectivity vs correct-evidence preference.

### Figure 4 — Causal rescue dose response
Native vs sharpened routing in low-margin L− events.

### Figure 5 — Selectivity controls
Compare intervention effect across:
- low-margin L−
- high-margin L+
- confuser-top-1 L−
- non-retrieval controls

## 36. Final decision criterion

Block 3A succeeds only if it moves the claim from:

**failed reads are descriptively less target-selective**

to:

**target-selective routing causally controls local visual-read quality**

with evidence from:
- within-item replication,
- causal degradation,
- causal rescue,
- selective controls.

If this fails, the routing pattern remains useful as a descriptive clue but should not anchor the intervention story.

If it succeeds, the next stage can ask whether routing correction changes:

recovery  
→ re-retrieval  
→ wandering  
→ final outcome.

That becomes **Block 3B — Post-Read Recovery / Wandering Dynamics**.
