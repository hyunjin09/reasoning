# Stage 3C.3 Plan — Relevant-vs-Distractor Routing Causality

## 0. Purpose

Stage 3C.3 follows Stage 3C.2, which found a descriptive **alignment-then-retrieval / retrieval-only mixture** at the two independently causal-localized late-W4 retrieval targets.

At retrieval:

- task-required ROI `T` exceeded distinct mention ROI `M` in attention density, QK cosine, αV norm, and post-`W_O` norm for all 62 target/base events;
- 40/62 events were alignment-then-retrieval;
- 22/62 were retrieval-only;
- target attention frequently rose while candidate-sink `<|im_start|>` mass fell.

Stage 3C.2 did not manipulate Q, K, attention probability, sink, `h_pre`, or source states.

Stage 3C.3 asks:

> **Does query-side routing toward the task-required ROI causally control target Value influx and evidence preference?**

The target control path is:

```text
reasoning state
→ causal-head query Q
→ relevant-vs-distractor QK routing
→ target attention
→ target αV
→ evidence decision
```

This stage focuses on **routing causality**.

Do not start sink causality here. Candidate-sink behavior is recorded observationally for the next stage.

---

## 1. Scientific Handoff

### Stage 2C

Mention-centered attention established that semantic alignment can produce high visual attention.

Therefore:

```text
high attention != proven retrieval
```

### Stage 3B.2

With prior reasoning history fixed, switching only future visual K/V identity changed upcoming evidence identity bidirectionally.

Therefore late evidence-specific visual-source control is causal.

### Stage 3B.5–3B.7-R

The causal path was localized to:

```text
task-required visual ROI T
→ late W4 causal query-head sets
→ Value-dominant transport
→ current reasoning state
→ evidence decision
```

K-only semantic replacement was near zero, while V-only semantic replacement reproduced the full ROI semantic effect.

Important distinction:

> `K-only semantic identity` being weak does **not** imply routing is unimportant. K/Q routing may choose *where* to read, while V carries *what* semantic content is read.

### Stage 3C.1–3C.2

Natural retrieval was characterized by:

```text
QK_T sharpening
→ target attention increase
→ target αV increase
```

and in many cases:

```text
earlier mention ROI dominance
→ later task-required ROI dominance
```

Stage 3C.3 now tests whether changing the query-side routing state causally changes retrieval and evidence use.

---

# 2. Frozen Causal Targets

Reuse exactly:

## Target A

```text
coordinate: E_d
window: W4
layer: 29
heads: [11, 6, 15, 12]
```

## Target B

```text
coordinate: E_d - 1
window: W4
layer: 28
heads: [16, 0, 3, 6]
```

Frozen noncausal controls from Stage 3C.2:

```text
A controls: [0,1,2,3]
B controls: [1,2,4,5]
```

No new head/layer may be selected using Stage 3C.3 outcomes.

---

# 3. Primary Hypotheses

## H1 — Query routing is causal

A retrieval-needed query applied to fixed visual K/V should increase:

```text
QK_T
attention_T
αV_T
post-W_O target contribution
evidence preference
```

relative to a mention-only query.

## H2 — Routing is selective

The effect should favor:

```text
T = causally required ROI
```

over:

```text
M = mention-matched ROI
I = irrelevant matched ROI
```

## H3 — Routing is necessary

Replacing the retrieval query with the mention-only query should reduce target retrieval and evidence use.

## H4 — Reasoning state controls routing through Q

If current-position `h_pre` patching affects retrieval and query-only patching reproduces most of that effect, then:

```text
h_pre → Q → visual retrieval
```

is supported.

---

# 4. Primary Cohort

Prefer the exact Stage 3C.2 retained cohort:

```text
31 unique base_problem_ids
```

Use the maximal prospective subset satisfying the state-pair requirements.

Minimum:

```text
24 unique bases
```

Primary statistical unit:

```text
base_problem_id
```

No exclusion may depend on query-patch outcome.

---

# 5. Frozen State Pair Per Base

Each base must provide:

## State M — mention-aligned / retrieval-light

A semantically annotated state where:

- current reasoning refers to mention ROI `M`;
- immediate subgoal does not yet require task ROI `T`;
- selected without attention.

## State R — retrieval-needed

A state where:

- immediate reasoning requires causal target ROI `T`;
- corresponds to the frozen retrieval coordinate or prospectively matched retrieval-needed coordinate;
- selected without attention.

Where possible, preserve a stronger subset with similar lexical material across M and R.

---

# 6. Strong Lexical-Matching Subset

Prospectively flag cases where M and R contain the same entity phrase or close paraphrase but differ in retrieval need.

Example:

```text
M: "We already know AB; now compute CD."
R: "We now need to determine AB."
```

This is secondary but important for reducing simple lexical-alignment explanations.

---

# 7. Core Intervention Principle

In the primary routing test:

```text
visual K = recipient-native
visual V = recipient-native
nonvisual K/V = recipient-native
```

Only the **current selected-head query** is changed.

Thus Stage 3C.3 does not change the visual fact.

It asks whether changing the retrieval-control query changes access to the already-present visual evidence.

---

# PHASE A — QUERY-ONLY ROUTING CAUSALITY

## 8. Query Representation Audit

Audit the exact query used by eager Attention:

- layer;
- logical query head;
- head dimension;
- pre-RoPE vs post-RoPE tensor;
- recipient position;
- GQA mapping.

Because M and R occur at different positions, RoPE semantics must be handled explicitly.

Smoke-test two formulations:

### Form A — direct post-RoPE query patch

Patch the exact donor attention query vector.

### Form B — content-space query patch

Take donor pre-RoPE query content and apply the **recipient position's RoPE**.

Prefer the prospectively validated formulation that best isolates semantic query content from positional phase.

Freeze one formulation before primary scoring.

Preserve the rejected formulation in the audit.

---

## 9. Query-Only Intervention

At the frozen causal layer and current position:

- selected causal heads receive donor state query;
- all visual K/V remain recipient-native;
- all nonvisual K/V remain recipient-native;
- non-target query heads remain recipient-native;
- downstream Attention, `W_O`, residual, MLP, and later layers recompute naturally.

---

## 10. Phase-A Arms

### Q0 — Native retrieval

```text
State R + Q_R
```

### Q1 — Retrieval query replaced by mention query

```text
State R
selected causal-head Q_R → Q_M
```

Tests necessity.

Expected under routing causality:

```text
QK_T ↓
T-vs-M routing ↓
attention_T ↓
αV_T ↓
evidence preference ↓
```

### Q2 — Mention query replaced by retrieval query

```text
State M
selected causal-head Q_M → Q_R
```

Tests sufficiency.

Expected:

```text
QK_T ↑
T-vs-M routing ↑
attention_T ↑
αV_T ↑
target evidence preference ↑
```

### Q3 — Self-query reconstruction

```text
Q_R → Q_R
Q_M → Q_M
```

Must be transparent.

### Q4 — Frozen noncausal-head query patch

Run the same M↔R query intervention on the frozen noncausal heads.

Expected effect should be weaker if routing is specific to the prior causal head set.

---

# 11. Primary Readouts

For `T`, `M`, and `I`:

## Routing

```text
QK cosine
raw QK dot product
scaled pre-softmax logit
attention mass
attention density
attention entropy
```

## Value influx

```text
αV vector
αV norm
post-W_O contribution
frozen-head-set post-W_O sum
```

## Evidence

Reuse the frozen teacher-forced evidence-preference metric.

Matched-seed rollout is secondary only.

---

# 12. Relevant-vs-Distractor Metrics

Primary distractor:

```text
D = M
```

Secondary distractor:

```text
D = I
```

Define:

```text
RDS = mean scaled-logit(T) - mean scaled-logit(D)
ADG = attention_density(T) - attention_density(D)
```

Use unnormalized changes as primary.

Do not treat these as information fractions.

---

# 13. Phase-A Causal Chain

For each intervention measure:

```text
ΔRDS
Δattention_T
ΔαV_T
ΔpostWO_T
Δevidence
```

The desired sequence is:

```text
query intervention
→ T-vs-M routing changes
→ target Value influx changes
→ evidence preference changes
```

After primary causal effects are established, correlations among these changes may be reported descriptively.

Do not claim formal causal mediation fractions from correlation.

---

# 14. Phase-A Gate

Proceed to Phase B only if at least one frozen target satisfies all:

1. `Q_R→Q_M` reduces T-over-M routing;
2. `Q_M→Q_R` increases T-over-M routing;
3. reciprocal effects are directionally consistent;
4. target αV changes in the expected direction;
5. evidence preference changes in the expected direction;
6. causal-head effects exceed frozen noncausal-head controls;
7. self-query reconstruction is exact.

If neither target passes:

**STOP and REDIRECT.**

Do not use Phase B or alpha manipulation to rescue a null query result.

---

# PHASE B — CURRENT-STATE (`h_pre`) ROUTING CAUSALITY

## 15. Purpose

Phase A tests whether Q itself controls retrieval.

Phase B asks the higher-level question:

> **Does the current reasoning state causally create that retrieval routing?**

---

## 16. h_pre Intervention

At the frozen target layer:

### H1 — Retrieval state → mention state

```text
State R recipient
current-position h_pre_R → h_pre_M
```

### H2 — Mention state → retrieval state

```text
State M recipient
current-position h_pre_M → h_pre_R
```

### H3 — Self patch

Must be transparent.

Only the current-position `h_pre` is directly patched.

Past K/V remain recipient-native.

Visual K/V remain recipient-native.

Then naturally recompute:

```text
norm
→ Q/K/V projections
→ Attention
→ W_O
→ residual
→ MLP
→ later layers
```

---

# 17. h_pre Readouts

Measure the same chain:

```text
Q direction
QK_T / QK_M
attention_T / attention_M
αV_T
post-W_O target contribution
evidence preference
```

This directly tests whether the reasoning state controls subsequent visual routing.

---

# 18. Query-vs-h_pre Comparison

For each base compare query-only and h_pre effects.

Define descriptive:

```text
QRR_routing  = query-only routing effect / h_pre routing effect
QRR_evidence = query-only evidence effect / h_pre evidence effect
```

Do not clip.

Do not interpret as a unique mediation fraction.

---

# 19. Phase-B Outcome Categories

## C1 — Query-Mediated Retrieval Control

If h_pre patch strongly changes retrieval and query-only patch reproduces most of the direction/magnitude:

> **The current reasoning state controls visual retrieval substantially through the causal-head query vectors.**

## C2 — Broader State-Dependent Control

If h_pre is strong but query-only is weak:

> retrieval control depends on broader current-state computation beyond a frozen Q substitution.

Possible contributors:

- normalization;
- current-token K/V;
- multiple-head interaction;
- residual state geometry.

Do not automatically localize further here.

## C3 — Target-Specific

A and B differ.

Preserve heterogeneity.

---

# OPTIONAL PHASE C — DIRECT ROUTING-PROBABILITY CAUSALITY

## 20. When to Run

Only if Phase A establishes query-dependent routing but a direct probability-allocation test would materially clarify interpretation.

This phase is secondary.

---

## 21. Alpha Reallocation Intervention

Keep recipient:

```text
Q
K
V
```

fixed.

Modify only normalized attention probabilities between:

```text
T
and
M
```

or secondarily:

```text
T
and
I
```

Preserve within-region relative distributions and renormalize all probabilities exactly.

Frozen dose levels:

```text
25%
50%
100%
```

of the native T-vs-distractor probability gap.

Run both:

```text
D → T
T → D
```

Do **not** borrow probability from the candidate sink in this stage.

---

## 22. Alpha Boundary

Alpha manipulation is off-manifold relative to natural QK computation.

It can test whether relevant-vs-distractor probability allocation changes Value influx/evidence use, but does not identify the natural upstream trigger.

Phase A/B remain primary.

---

# 23. Candidate Sink Tracking — Observational Only

Continue recording:

```text
sink mass
sink QK
sink αV
sink post-W_O contribution
```

during query and h_pre interventions.

Key descriptive question:

> If routing is causally redirected toward T, does candidate-sink mass fall automatically?

This will guide Stage 3C.4.

Do not:

- patch sink;
- ablate sink;
- force sink mass redistribution.

---

# 24. Condition Controls

Where mechanically feasible, retain:

```text
O
O_sham
C
C_sham
```

Primary routing inference is within a fixed recipient image condition.

Sham conditions detect:

- rendering-sensitive routing;
- query/image mismatch;
- ROI instability.

Do not define routing causality from O-vs-C attention differences alone.

---

# 25. Validation Cohort

Before primary scoring, use:

```text
6–8 disjoint validation bases
```

if available.

Validation must cover:

1. self-query exactness;
2. self-h_pre exactness;
3. query-head selectivity;
4. non-target-head invariance;
5. exact visual K/V invariance in Phase A;
6. exact past-cache invariance;
7. RoPE formulation;
8. deterministic repeatability;
9. finite scores;
10. expected T-vs-M routing direction in a majority of smoke cases.

Do not debug on the primary cohort.

---

# 26. Frozen Primary Statistical Family

Primary unit:

```text
base_problem_id
```

### Phase A

1. Q_R→Q_M effect on T-vs-M scaled-logit gap
2. Q_R→Q_M effect on target attention density
3. Q_R→Q_M effect on target αV
4. Q_R→Q_M effect on evidence preference
5. Q_M→Q_R effect on T-vs-M scaled-logit gap
6. Q_M→Q_R effect on target attention density
7. Q_M→Q_R effect on target αV
8. Q_M→Q_R effect on evidence preference
9. causal-vs-noncausal query-patch difference

### Phase B, gated

10. h_pre R→M effect on target routing
11. h_pre M→R effect on target routing
12. h_pre effect on evidence preference
13. query-only vs h_pre recovery

Use Holm correction across the frozen family.

Report:

- mean;
- median;
- bootstrap 95% CI;
- positive-direction fraction;
- unnormalized effects.

---

# 27. Primary Scientific Outcomes

## R1 — Routing-Causal Retrieval

If retrieval query causes T-over-M routing, target αV, and evidence preference to rise, while reciprocal query suppresses them:

> **Task-conditioned query routing causally controls access to the independently causal visual evidence ROI.**

## R2 — Reasoning→Query→Vision Control

If h_pre changes retrieval and Q-only reproduces most of it:

```text
reasoning state
→ query
→ visual retrieval
```

is supported.

Combined with prior stages:

```text
reasoning state
→ query routing
→ target ROI Value
→ current reasoning
```

would form a causal reasoning→vision→reasoning loop.

## R3 — Broader Retrieval-Control State

If h_pre is causal but query-only is insufficient:

> retrieval control exists at the current reasoning state but cannot be reduced to a frozen query vector alone.

## R4 — Routing Without Behavioral Control

If query patch changes QK/attention but not evidence preference:

> routing redistribution is computationally real but insufficient to control evidence use under the tested intervention.

---

# 28. Relation to Stage 3B.7-R K/V Result

Do not confuse:

```text
K-only semantic identity swap
```

with:

```text
Q/K routing causality
```

The earlier K-only null asked:

> does changing K semantic content transfer `3 vs 5` identity?

Stage 3C.3 asks:

> does changing the query-side routing state alter which visual Value source is read?

Thus the coherent mechanism may be:

```text
Q/K:
where to read

V:
what content is read
```

---

# 29. Handoff to Sink Causality

If Stage 3C.3 establishes routing causality, the planned next stage is:

```text
Stage 3C.4 — Attention Sink Causality
```

Questions for Stage 3C.4:

- Is `<|im_start|>` mass dispensable?
- If sink mass is reduced, where does it go?
- Does it improve target retrieval only when the correct routing query is present?
- Is sink a probability reservoir, stabilizer, or active information source?

Do not execute these experiments here.

---

# 30. What Stage 3C.3 May Establish

If supported:

- relevant-vs-mention routing is causal;
- current reasoning state causally controls visual retrieval;
- causal-head query vectors mediate that control;
- routing changes target Value influx and evidence use.

---

# 31. What Stage 3C.3 Cannot Establish

Do not claim:

- sink is useless;
- sink is safe to remove;
- attention mass is an information fraction;
- all retrieval is query-mediated;
- a universal mechanism across every head/problem;
- vision-encoder origin;
- Q/R long-term memory lifecycle;
- multi-evidence refresh;
- failure mechanisms;
- discrete LOOK/THINK states.

---

# 32. Decision After Stage 3C.3

Recommend exactly one direction.

## GO — Stage 3C.4 Attention Sink Causality

Use if routing causality is established and sink behavior remains systematic.

## GO — Broader Retrieval-Control State Analysis

Use if h_pre is strongly causal but Q-only mediation is weak.

## REDIRECT — Routing Intervention Not Behavioral

Use if Q changes routing but not evidence use.

Do not start the next experiment automatically.

---

# 33. Output Structure

```text
outputs/stage3c3/
  config/
    stage3c3_config.json
    frozen_targets.json
    state_pair_rules.json
    primary_family.json
    rope_query_formulation.json

  cohort/
    validation_manifest.jsonl
    primary_manifest.jsonl
    exclusions.jsonl
    lexical_match_subset.jsonl

  audit/
    query_tensor_layout.json
    rope_alignment_audit.json
    q_patch_selectivity.json
    hpre_patch_selectivity.json
    visual_kv_invariance.json
    non_target_head_invariance.json
    reproducibility.json

  phase_a_query/
    per_problem_query_patch_results.jsonl
    routing_metrics.jsonl
    value_influx_metrics.jsonl
    evidence_results.jsonl
    noncausal_head_controls.jsonl

  phase_b_hpre/
    per_problem_hpre_patch_results.jsonl
    query_mediation_results.jsonl

  phase_c_optional_alpha/
    alpha_intervention_results.jsonl
    alpha_validation.json

  observational_sink/
    sink_under_query_intervention.jsonl
    sink_under_hpre_intervention.jsonl

  analysis/
    relevant_vs_mention_routing_statistics.json
    query_causality_statistics.json
    hpre_causality_statistics.json
    query_mediation_statistics.json
    causal_vs_noncausal_comparison.json
    lexical_match_subset_analysis.json
    sink_secondary_analysis.json
    figures/

  summaries/
    stage3c3_summary.md
    stage3c3_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3C.2 or earlier artifacts.

---

# 34. Required Figures

At minimum:

1. Q_R→Q_M effect on T-vs-M QK/logit gap;
2. Q_M→Q_R reciprocal effect;
3. query-patch effect on target attention;
4. query-patch effect on target αV;
5. query-patch effect on evidence preference;
6. per-base routing-change vs evidence-change;
7. causal-vs-noncausal head-set query effects;
8. h_pre vs query-only routing effects;
9. h_pre vs query-only evidence effects;
10. query-recovery ratio distributions;
11. strong lexical-match subset;
12. T-vs-I secondary controls;
13. candidate-sink mass under query intervention;
14. head-level heterogeneity, especially Target-B head 6.

---

# 35. Acceptance Criteria

Stage 3C.3 technically passes if:

1. Stage 3C.2 target/head/ROI definitions remain frozen;
2. no attention-based cohort/state selection occurs;
3. at least 24 valid primary bases remain;
4. State M and State R are frozen semantically before intervention;
5. visual K/V remain recipient-native in Phase A;
6. query patch is logical-query-head selective;
7. non-target heads remain recipient-native;
8. RoPE semantics are explicitly audited;
9. one query formulation is frozen before primary scoring;
10. self-query reconstruction is exact;
11. frozen noncausal-head controls are run;
12. QK/attention/αV/evidence readouts are all collected;
13. Phase B occurs only if Phase A gate passes;
14. h_pre patch is current-position selective;
15. visual K/V remain recipient-native in Phase B;
16. query-vs-h_pre comparison avoids mediation-fraction overclaim;
17. candidate sink is observed but never manipulated;
18. optional alpha intervention is secondary and mechanically audited;
19. `base_problem_id` remains the statistical unit;
20. exactly one GO / REDIRECT recommendation is written.

Technical PASS does not require routing causality.

---

# 36. Stop Condition

After:

- state-pair validation;
- query/RoPE formulation audit;
- Phase-A query intervention;
- gated Phase-B h_pre intervention;
- optional validated alpha analysis;
- observational sink tracking;
- final routing classification;
- exactly one recommendation;

**STOP.**

Do not start:

- sink knockout;
- sink mass redistribution;
- Stage 4 multi-evidence refresh;
- failure analysis.

Return the complete Stage 3C.3 results for review.

The next stage must be chosen only after jointly considering Stage 3C.3 with all prior Stage 2A–3C.2 evidence.
