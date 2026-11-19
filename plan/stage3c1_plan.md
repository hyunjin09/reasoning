# Stage 3C.1 Plan — Causally Anchored Retrieval-Attention Phenotype

## 0. Purpose

Stage 3C.1 is a bridge stage between the completed single-evidence causal pathway analysis (Stage 3) and the planned dynamic multi-evidence retrieval analysis (Stage 4).

Stage 3 has already established the causal content pathway:

```text
edited visual evidence ROI
        ↓
small late W4 causal head ensemble
        ↓
Value-mediated semantic transport
        ↓
current reasoning residual
        ↓
evidence decision
```

The clean frozen retrieval targets are:

```text
Target A
E_d / W4 / layer 29
heads [11, 6, 15, 12]

Target B
E_d - 1 / W4 / layer 28
heads [16, 0, 3, 6]
```

Stage 3C.1 does not search for new heads, ROIs, layers, or timing coordinates from attention.

Instead it asks:

> **What does Attention actually look like at a visual retrieval event that has already been causally localized?**

The main decomposition is:

```text
QK routing
→ attention probability α
→ Value influx αV
→ post-W_O residual contribution
→ independently known causal effect
```

Primary questions:

1. Is target-evidence ROI attention actually elevated during causal retrieval?
2. Is the relevant ROI preferred over matched irrelevant/distractor regions?
3. If attention is high, is that driven by Q/K cosine alignment, Q norm, K norm, or softmax competition?
4. Can causal evidence transport be strong even when visual attention mass is small?
5. Where does the remaining attention mass go when visual attention is low?
6. Are there persistent high-attention positions that are plausible attention-sink candidates?
7. How do causal retrieval cells differ from nearby times, noncausal heads, and the upstream-state control?

Stage 3C.1 is a measurement/phenotype stage only.

Do not yet manipulate attention probabilities, force distractor routing, patch retrieval queries, or make causal attention-routing claims.

---

## 1. Scientific Handoff

### Stage 2C

Visual ROI attention was predominantly mention-centered and could reactivate with later semantic references.

Therefore:

> **High visual attention alone cannot distinguish semantic alignment from causal visual retrieval.**

### Stage 3B.5

Evidence-specific causal restoration increased across the post-Attention boundary in:

```text
E_d - 1 / W4
E_d - 1 / W5
E_d     / W4
```

while:

```text
E_d / W5
```

was upstream-state dominated.

### Stage 3B.6

Core finding:

> **Visual evidence retrieval is concentrated in a small, time-dependent subset of late attention heads.**

Clean W4 source decomposition showed strong visual-source dominance.

### Stage 3B.7-R

The causal source was localized to the actual Stage 3A edited evidence ROI.

K/V decomposition was Value-dominant:

```text
K-only ≈ 0
V-only ≈ full semantic effect
```

Therefore Stage 3C.1 can analyze attention around a known causal ROI→Value pathway rather than guessing retrieval from attention.

---

## 2. Frozen Primary Targets

Use exactly:

### Target A

```text
time: E_d
window: W4
layer: 29
heads: [11, 6, 15, 12]
```

### Target B

```text
time: E_d - 1
window: W4
layer: 28
heads: [16, 0, 3, 6]
```

Load exact definitions from frozen Stage 3B.7-R / Stage 3B.8 artifacts.

Do not infer missing implementation details from memory.

---

## 3. Core Characterization Cohort

Use the exact historical paired-semantic numeric cohort:

```text
37 unique base_problem_ids
```

with frozen:

- O/O_sham/C/C_sham;
- E_d;
- Stage 3A edit ROI;
- target/complement/irrelevant ROI token mappings;
- Target A/B head sets;
- Stage 3B.7-R causal ROI effects;
- Stage 3B.8 Value-path artifacts where compatible.

Primary statistical unit:

```text
base_problem_id
```

If the 13 fresh Stage 3B.7-R validation bases contain all required artifacts, use them only as an optional secondary replication set.

---

## 4. No Attention-Based Selection

Attention must not be used to select:

- examples;
- evidence events;
- ROIs;
- heads;
- layers;
- timing coordinates;
- distractors.

All primary coordinates are inherited from prior causal experiments.

---

## 5. Primary Temporal Grid

For each target layer/head set, reconstruct:

```text
E_d - 16
E_d - 8
E_d - 4
E_d - 2
E_d - 1
E_d
```

Use a checkpoint only when the required frozen history exists.

Do not invent missing checkpoints.

Do not use E_d+1 in the primary analysis because O/C token histories have diverged.

---

## 6. Control Families

### C1 — Nearby-time control

Same layer and same frozen causal heads at earlier pre-decision times.

### C2 — Noncausal-head control

At the same layer/time, use a prospectively fixed matched-size head set that did not enter the Stage 3B.6 causal Top-k sets.

Do not choose controls by low attention.

### C3 — Upstream-state control

Use the frozen E_d/W5 control from Stage 3B.5/3B.6.

Purpose:

> distinguish active evidence injection from a late Attention layer that already receives an evidence-rich h_pre.

### C4 — Visual-region controls

Use frozen Stage 3B.7-R regions:

```text
target ROI
matched irrelevant ROI
visual complement
all visual
```

An independently annotated second task-relevant ROI may be included only as a secondary distractor.

---

## 7. Exact Attention Audit

Audit the exact eager-Attention implementation:

1. residual input;
2. normalization;
3. Q projection;
4. K projection;
5. V projection;
6. GQA expansion;
7. RoPE;
8. scale;
9. mask;
10. softmax;
11. head concatenation;
12. W_O.

Create:

```text
outputs/stage3c1/audit/attention_equations.md
outputs/stage3c1/audit/gqa_mapping.json
outputs/stage3c1/audit/tensor_layout.json
outputs/stage3c1/audit/reconstruction_check.json
```

Reconstructed probabilities and head outputs must match eager Attention within a frozen tolerance.

---

## 8. Metric A — Attention Mass

For source set S:

```text
A_S = sum_j in S alpha_j
```

Compute for:

```text
target ROI
matched irrelevant ROI
visual complement
all visual
question/prompt
previous reasoning
special/control tokens
```

Also report token-count-normalized density.

Primary quantities:

- target ROI mass;
- target ROI density;
- target/irrelevant density ratio;
- target ROI share of all visual attention;
- total visual attention mass.

---

## 9. Metric B — QK Geometry

For the exact active post-RoPE Q/K vectors, store:

```text
||q||
||k_j||
cos(q,k_j)
q·k
scaled q·k
final masked logit
```

because:

```text
q·k = ||q|| ||k|| cos(q,k)
```

For each ROI/source class report:

- mean;
- median;
- maximum;
- attention-weighted mean;
- top-k token statistics.

Primary question:

> Is target ROI attention elevated because of cosine alignment, vector norms, or both?

---

## 10. Metric C — Softmax Competition

For source set S:

```text
LSE_S = logsumexp(final attention logits over S)
```

Compute:

```text
LSE_target
LSE_irrelevant
LSE_other_visual
LSE_Q
LSE_R
LSE_special
LSE_all_non_target
```

Define:

```text
target competition margin
= LSE_target - LSE_all_non_target
```

This distinguishes:

- target-logit increase;
- competitor-logit decrease;
- both.

Store top competing token classes as well.

---

## 11. Metric D — Entropy and Concentration

Compute:

- all-context attention entropy;
- visual-only renormalized entropy;
- target ROI share of visual attention;
- top-1 visual token share;
- top-5 visual token share;
- effective visual support = exp(visual entropy).

Question:

> Does retrieval sharpen attention spatially even when total visual mass is unchanged?

---

## 12. Metric E — Value Magnitude and Weighted Contribution

For each token/head store:

```text
||V_j||
```

For source S:

```text
C_V(S) = sum_j in S alpha_j V_j
```

Report:

```text
||C_V(target ROI)||
||C_V(irrelevant ROI)||
||C_V(visual complement)||
||C_V(all visual)||
||C_V(Q/P)||
||C_V(R)||
||C_V(special)||
```

Also compute the descriptive quantity:

```text
||C_V(S)|| / A_S
```

when A_S > 0.

This is not an information-per-attention measure; it is only for separating:

```text
low attention + large contribution
high attention + small contribution
```

phenotypes.

---

## 13. Metric F — Post-W_O Residual Contribution

For each logical query head, isolate the exact W_O slice.

For region S:

```text
C_res(h,S) = W_O^(h) C_V(h,S)
```

For frozen head set H:

```text
C_res(H,S) = sum_h in H C_res(h,S)
```

Report contribution norms for:

- target ROI;
- irrelevant ROI;
- all visual;
- R;
- special/control.

This is closer to the vector actually injected into the residual stream than attention probability alone.

---

## 14. Optional Alignment With the Known Causal Value Effect

Where tensor definitions are exactly compatible with Stage 3B.8, compute secondary:

- cosine similarity;
- signed projection;

between the natural target-ROI Value contribution and the frozen O↔C causal Value-effect direction.

Do not silently map incompatible coordinates.

---

## 15. Source-Mass Accounting

Verify:

```text
A_visual + A_prompt + A_reasoning + A_special/other = 1
```

within numerical tolerance.

Produce source-mass profiles.

Main question:

> If visual attention is small, where does the rest of the probability mass go?

---

## 16. Attention-Sink Candidate Analysis

Stage 3C.1 may identify candidate sinks but cannot make a causal sink claim.

Prospectively define token classes from the exact tokenizer/template, such as:

- BOS/start token;
- image delimiters/control tokens;
- assistant/control markers;
- formatting/newline tokens where applicable.

A sink candidate should show:

1. persistently high attention;
2. low semantic specificity between O and C;
3. weak temporal coupling to known retrieval events.

Store:

- mass;
- frequency as top-attended position;
- O/C difference;
- Value-contribution norm.

Do not call any token a causal sink in Stage 3C.1.

---

## 17. Per-Head Analysis

Do not report only Top-4 averages.

Analyze:

```text
Target A: heads 11, 6, 15, 12
Target B: heads 16, 0, 3, 6
```

Questions:

- Do all causal heads show ROI selectivity?
- Is one head carrying most natural ROI attention?
- Does shared head 6 show a persistent phenotype across E_d-1 and E_d?
- Are other heads specialized for different source classes?

Head-set aggregate remains primary.

Individual-head interpretation is secondary unless robust.

---

## 18. Secondary W5 Comparator

Use `E_d-1/W5/head_10` only as a secondary comparator.

It had robust head-level causal restoration but inconclusive clean visual-source attribution because its Stage 3B.6 sham robustness failed.

Do not upgrade its source claim here.

---

## 19. Primary Contrasts

### Contrast 1 — Retrieval time vs earlier time

For the same causal heads compare the retrieval coordinate with E_d-2, -4, -8, -16 on:

- target ROI attention;
- target QK cosine/logit;
- competition margin;
- target alpha-V norm;
- target post-W_O contribution.

### Contrast 2 — Target ROI vs irrelevant ROI

At the causal coordinate compare:

- attention density;
- QK geometry;
- Value norm;
- weighted Value contribution;
- post-W_O contribution.

### Contrast 3 — Causal vs noncausal heads

Same time/layer, matched number of heads.

### Contrast 4 — Retrieval cell vs upstream-state control

Compare:

```text
E_d/W4 retrieval
vs
E_d/W5 upstream-state control
```

using frozen prior definitions.

---

## 20. Relationship With Existing Causal Effects

After phenotype metrics are frozen, relate natural measurements to existing per-base causal measurements:

```text
ROI causal BPR
V-only restoration
full V-only BVR
```

Use Spearman correlations and scatter plots.

These are descriptive associations only.

---

## 21. Possible Phenotype Outcomes

### P1 — High-attention causal retrieval

```text
target ROI attention ↑
target QK compatibility ↑
target Value/residual contribution ↑
```

near the causal coordinate.

### P2 — Low-mass / high-content retrieval

```text
target ROI attention modest
but
alpha-V / W_O contribution strong
and
known causal ROI effect strong
```

### P3 — High attention without causal specificity

Attention is high in retrieval and controls or weakly related to known causal effect.

### P4 — Competition-driven attention

Target QK changes little, but competitor logits fall and target probability rises.

### P5 — Candidate sink-heavy phenotype

Most mass goes to special/control positions while a small ROI mass carries strong known causal influence.

Sink remains descriptive only.

---

## 22. Statistical Treatment

Primary unit:

```text
base_problem_id
```

Aggregate repeated heads/times within base before cohort-level significance tests.

Report:

- medians;
- means;
- bootstrap 95% CIs;
- paired within-base differences;
- effect sizes;
- Holm correction over the small frozen family of primary contrasts.

Do not run large uncorrected metric/head fishing analyses.

---

## 23. Validation Requirements

Before full extraction verify:

1. eager Attention reconstruction;
2. source-token partition;
3. frozen ROI mappings;
4. head indices;
5. Q/K/V tensor shapes;
6. attention sums to one;
7. source-mass accounting closes;
8. sum(alpha*V) reconstructs head output;
9. per-head W_O contributions reconstruct selected-head output;
10. instrumentation preserves model logits within tolerance;
11. deterministic repeated extraction;
12. no NaN/Inf.

Use a small smoke set first.

---

## 24. What Stage 3C.1 May Establish

It may establish:

- whether causally localized retrieval has a distinct attention phenotype;
- whether the actual evidence ROI receives elevated/selective attention;
- whether high attention is driven by cosine, norm, or competition;
- whether small attention mass can accompany strong causal Value transport;
- where nonvisual attention mass goes;
- which positions are plausible sink candidates;
- how retrieval heads differ from controls.

---

## 25. What Stage 3C.1 Cannot Establish

Do not claim:

- attention magnitude itself causes retrieval;
- increasing distractor attention will switch the fact;
- candidate sinks are causally useless;
- Q/K routing is the retrieval trigger;
- reasoning state causally controls query formation;
- dynamic A→B retrieval;
- hallucination/failure mechanisms.

---

## 26. Decision After Stage 3C.1

Do not automatically start Stage 3C.2.

Write exactly one review-only recommendation after inspecting the results.

Possible next directions:

```text
GO — Retrieval-control signal intervention
```

if a clear query/QK phenotype emerges.

```text
GO — Relevant-vs-distractor routing causality
```

if ROI-selective routing is strong enough for a controlled rerouting experiment.

```text
GO — Attention-sink causal test
```

if a strong persistent high-mass/low-specificity sink candidate emerges.

```text
REDIRECT — Attention magnitude weakly informative
```

if causal Value retrieval has little distinctive attention phenotype.

The next stage must be chosen only after reviewing Stage 3C.1.

---

## 27. Output Structure

Create:

```text
outputs/stage3c1/
  config/
    stage3c1_config.json
    frozen_targets.json
    temporal_grid.json
    control_heads.json
    source_classes.json

  audit/
    attention_equations.md
    gqa_mapping.json
    tensor_layout.json
    reconstruction_check.json
    instrumentation_faithfulness.json

  extraction/
    per_head_per_time_metrics.jsonl
    source_attention_mass.jsonl
    qk_geometry.jsonl
    softmax_competition.jsonl
    entropy_metrics.jsonl
    value_contributions.jsonl
    wo_residual_contributions.jsonl

  controls/
    irrelevant_roi_comparison.jsonl
    noncausal_head_comparison.jsonl
    upstream_state_control.jsonl
    w5_head10_secondary.jsonl
    sink_candidate_metrics.jsonl

  analysis/
    retrieval_time_contrasts.json
    roi_selectivity_statistics.json
    qk_decomposition_statistics.json
    softmax_competition_statistics.json
    attention_vs_value_statistics.json
    source_mass_profiles.json
    sink_candidate_summary.json
    causal_effect_correlations.json
    per_head_phenotypes.json
    figures/

  summaries/
    stage3c1_summary.md
    stage3c1_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite any Stage 3 artifacts.

---

## 28. Required Figures

At minimum:

1. target ROI attention over E_d-16…E_d for Target A;
2. same for Target B;
3. target vs irrelevant ROI attention density;
4. QK cosine / Q norm / K norm / logit decomposition;
5. target competition margin over time;
6. all-token and visual-only entropy over time;
7. target ROI attention mass vs alpha-V contribution;
8. target ROI attention vs post-W_O residual contribution;
9. source-mass composition for causal heads;
10. causal vs noncausal head phenotype;
11. E_d/W4 retrieval vs E_d/W5 upstream-state control;
12. per-head profile highlighting head 6;
13. candidate sink mass over time;
14. natural attention metric vs existing causal ROI/V effect.

---

## 29. Acceptance Criteria

Stage 3C.1 technically passes if:

1. no new ROI/head/time is selected from attention;
2. exact Target A/B definitions are reused;
3. exact Stage 3B.7-R ROI mappings are reused;
4. eager-Attention reconstruction passes;
5. GQA mapping is audited;
6. source attention mass sums to one within tolerance;
7. Q/K cosine, norm, dot-product, and scaled-logit terms come from the actual Attention tensors;
8. softmax competition terms are computed;
9. alpha*V reconstructs per-head output;
10. post-W_O contributions reconstruct correctly;
11. nearby-time controls are included;
12. noncausal-head controls are frozen prospectively;
13. E_d/W5 stays an upstream-state control;
14. E_d-1/W5/head_10 stays secondary;
15. sink analysis remains descriptive;
16. attention is not manipulated;
17. existing causal effects are used only for post-freeze triangulation;
18. base_problem_id is the statistical unit;
19. no Stage 4/failure experiment is started;
20. exactly one next-stage recommendation is written.

Technical PASS does not require a high-attention retrieval phenotype.

---

## 30. Stop Condition

After:

- instrumentation audit;
- 37-base phenotype extraction;
- temporal contrasts;
- ROI vs irrelevant comparison;
- Q/K norm-cosine-logit decomposition;
- softmax competition analysis;
- Value and post-W_O contribution analysis;
- source-mass accounting;
- candidate sink analysis;
- causal-effect triangulation;
- summary and one recommendation;

**STOP.**

Do not start:

- h_pre/query patching;
- forced relevant→distractor routing;
- direct alpha manipulation;
- causal sink knockout;
- Stage 4 multi-evidence refresh;
- hallucination/failure analysis.

Return the full Stage 3C.1 results for review.

The next experiment must be determined only after jointly considering Stage 3C.1 with all prior Stage 2–3 evidence.
