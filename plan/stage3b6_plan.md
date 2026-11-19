# Stage 3B.6 Plan — Restoration-Controlled Attention-Head and Source-Path Localization

## 0. Purpose

Stage 3B.6 follows the Stage 3B.5 result:

> **Evidence-specific causal restoration rises across the post-Attention residual boundary in three frozen late-layer cells, supporting Attention-mediated evidence injection into the current reasoning state.**

The qualifying cells were:

```text
E_d - 1 / W4
E_d - 1 / W5
E_d     / W4
```

while:

```text
E_d / W5
```

met the frozen upstream-state rule and should remain an important control rather than being merged into the same mechanism.

Stage 3B.6 asks two ordered questions:

### WHICH HEAD?
Which query-head computations account for the evidence-specific post-Attention gain?

### WHICH SOURCE PATH?
For those causal heads, is the semantic evidence retrieved from visual tokens, non-visual prompt/question states, previous reasoning states, or a combination?

This stage must preserve the project’s restoration-controlled causal framework.

Do not select heads using raw attention magnitude.

Do not start ROI-specific path decomposition, pattern-vs-value decomposition, MLP feature analysis, Q/R long-term carrier analysis, multi-evidence refresh, or failure analysis automatically.

---

## 1. Scientific Handoff

### Stage 2A–2C

Raw visual attention was initially used as a descriptive signal.

Stage 2C showed:

- 58/70 evidence events were mention-centered;
- matching ROI attention can reactivate at later semantic references;
- high visual attention therefore cannot by itself distinguish semantic alignment from causal retrieval.

This remains a core methodological result.

### Stage 3A

Localized visual counterfactual edits established that visual evidence identity is genuinely causal:

- 49/49 independent bases in the expected CE direction;
- strong sham-controlled effects.

Visual-content interventions, not attention weights, became the causal handle.

### Stage 3B.0

Generation-start visual cutoff preserved only a small part of the full Stage 3A effect.

A small prefill residual was causally carried by Q-side cached states.

Therefore prefill visual-to-language transfer exists but is insufficient for most evidence-specific reasoning.

### Stage 3B.1

Most problems remained strongly dependent on future direct visual access even very late before the evidence decision.

Therefore long-form reasoning shows persistent direct-vision dependence.

### Stage 3B.3-R

Restoration-controlled layer localization found evidence-specific transfer in narrow late-layer windows near the discriminative decision.

### Stage 3B.4

Isolated precomputed Attention/MLP output restoration did not fully explain robust block restoration.

This prevented a premature module-level claim.

### Stage 3B.5

Residual-boundary restoration with natural downstream recomputation showed robust post-Attention gains in 3/4 frozen cells.

Primary boundary profiles:

| Coordinate/window | first h_pre | first h_post_attn | second h_post_attn | frozen Block | Category |
|---|---:|---:|---:|---:|---|
| `E_d-1/W4` | 0.3461 | 0.6001 | 1.0024 | 0.9969 | Attention (first) |
| `E_d-1/W5` | 1.0880 | 1.2912 | 0.7188 | 1.3718 | Attention (first) |
| `E_d/W4` | 2.0076 | 3.2813 | 6.0621 | 6.0635 | Attention (second) |
| `E_d/W5` | 7.5592 | 8.6712 | 9.1677 | 9.1730 | upstream |

The frozen decision hierarchy selected:

> **GO — Attention head/path localization**

Stage 3B.6 implements that recommendation.

---

## 2. Critical Interpretation Constraint

Stage 3B.5 does not imply that all four W4/W5 cells share one mechanism.

Primary head localization must preserve the heterogeneity:

```text
Qualifying Attention-gain cells:
1. E_d - 1 / W4
2. E_d - 1 / W5
3. E_d     / W4

Upstream-state control:
4. E_d     / W5
```

Do not pool all four cells into one mechanism.

---

## 3. Exact Target Attention Layers

Do not infer the target Attention layer from window names alone.

Load the exact qualifying boundary/layer from the frozen Stage 3B.5 artifacts.

Expected from the frozen categories:

- `E_d-1/W4`: first Attention transition in W4
- `E_d-1/W5`: first Attention transition in W5
- `E_d/W4`: second Attention transition in W4

But implementation must use the exact frozen layer IDs from Stage 3B.5 outputs.

For `E_d/W5`, use only a prospectively defined control layer/boundary loaded from the upstream-state result.

Do not reopen a layer search.

---

## 4. GQA Head Semantics Audit

Qwen3-VL uses grouped-query attention.

Before head intervention, audit:

- number of logical query heads;
- number of K/V heads;
- query-head to KV-group mapping;
- head dimension;
- output-projection layout;
- exact tensor axis order;
- whether fused attention kernels expose per-query-head outputs;
- how to reconstruct a single logical query-head contribution before `W_O`.

Expected logical query heads:

```text
32
```

Expected K/V heads from previous cache audits:

```text
8
```

but these values must be re-verified from the exact model implementation.

Create:

```text
outputs/stage3b6/audit/gqa_head_map.md
outputs/stage3b6/audit/head_tensor_layout.json
outputs/stage3b6/audit/output_projection_slices.json
```

Never treat one shared KV head as equivalent to one query head.

---

## 5. Why Raw KV Replacement Is Not Enough for Head Localization

Because multiple query heads share K/V groups under GQA, directly replacing one cached K/V head could alter several logical query heads at once.

Therefore primary query-head localization must operate on:

> **the per-query-head attention computation or per-query-head projected contribution at the current position**

rather than globally modifying a shared KV cache slot.

The implementation must explicitly verify query-head selectivity.

---

## 6. Discovery / Confirmation Split

Use two fixed sets.

### Head-discovery set

Reuse the 8 disjoint Stage 3B.5 validation bases.

These were not used for head-level selection previously.

Use them only to:

- validate mechanics;
- rank candidate heads;
- freeze candidate single heads and head sets.

They are not part of the primary confirmatory statistics.

### Primary confirmation set

Use the exact 37 paired-semantic numeric bases from Stages 3B.4–3B.5.

Primary statistical unit:

```text
base_problem_id
```

Do not change the 37-base cohort after head discovery.

---

## 7. Semantic Conditions

Preserve the paired restoration classes:

```text
Original semantic class:
O
O_sham

Counterfactual semantic class:
C
C_sham
```

All head-level and source-path claims must be based on:

- bidirectional O↔C semantic transfer;
- within-semantic sham controls;
- self controls.

Do not return to ablation-only attribution.

---

# 8. Phase A — Query-Head Localization

## 8.1 Primary intervention concept

At a frozen qualifying Attention layer and current evidence-decision position, use the recipient current state/query but semantically swap the context computation for only one logical query head.

For a recipient `C` run and source `O` run:

```text
recipient current h_pre/query:
    C

all non-target query heads:
    C computation

target query head h:
    source-conditioned semantic attention computation from O
```

Then allow:

- head concatenation;
- output projection;
- residual addition;
- MLP;
- all later layers

to recompute naturally.

Run reciprocal:

```text
O recipient + C semantic head computation
```

The exact implementation can use one of two validated approaches.

### Preferred A — Hybrid per-head recomputation

Keep recipient query `Q_h`.

Use source/recipient K/V according to the semantic-swap condition for the target head, recompute its attention, and keep all other query heads recipient-native.

### Fallback B — Per-head contribution restoration

Patch only the selected query head’s pre-`W_O` or projected additive contribution at the current position.

If fallback B is required, explicitly acknowledge that it is closer to the precomputed-output intervention family and compare it with state-consistent validation controls.

Preferred A should be used if technically feasible.

---

## 9. Phase A Head Family

For each qualifying cell, screen all 32 logical query heads on the 8-base discovery set.

Do not use raw attention to rank them.

For each head compute:

- bidirectional semantic head-restoration effect;
- paired sham effect;
- self error;
- source consistency;
- restoration relative to the frozen post-Attention boundary gain.

Freeze the discovery ranking before primary scoring.

---

## 10. Candidate-Head Freeze

From the 8-base discovery set, freeze:

1. all heads passing the discovery robustness rule;
2. fixed cumulative head sets by effect ranking:

```text
Top-1
Top-2
Top-4
Top-8
```

within each qualifying cell.

If fewer than 8 valid heads exist, freeze the available set and document it.

Do not alter the ranking after inspecting the 37-base primary results.

The purpose of cumulative sets is to distinguish:

- sparse head mechanism;
- small head ensemble;
- distributed multi-head Attention effect.

---

## 11. Head Restoration Metric

For head `h`, define bidirectional semantic restoration:

\[
BHR_h
=
rac{
\Delta_{h,Oightarrow C}
+
\Delta_{h,Cightarrow O}
}{2}
\]

Use an unnormalized evidence-preference shift as primary.

Also compute:

\[
HRR_h
=
rac{BHR_h}{G_{attn}}
\]

where `G_attn` is the frozen Stage 3B.5 post-Attention boundary gain for that exact cell.

Do not clip ratios.

Do not interpret `HRR` as a unique information fraction.

---

## 12. Head-Level Controls

Every tested head/set must include:

### H0 — No intervention

Frozen recipient computation.

### H1 — Self semantic head reconstruction

```text
O -> O
C -> C
```

Must be transparent.

### H2 — O→C semantic restoration

Source O, recipient C.

### H3 — C→O semantic restoration

Source C, recipient O.

### H4 — Within-semantic sham restoration

Use matched:

```text
O_sham / O
C_sham / C
```

with the exact same head intervention.

True O↔C semantic shift must clearly exceed sham/render shift.

---

## 13. Primary Confirmation of Heads

On the 37-base primary cohort, evaluate only the frozen candidate single heads and frozen Top-k sets.

Report:

- median BHR;
- mean BHR;
- bootstrap 95% CI;
- bidirectional consistency;
- sham semantic effect;
- self error;
- boundary-gain-relative restoration.

Use Holm correction across the frozen confirmatory head family.

Exploratory all-head results may be stored separately but must not redefine primary claims.

---

## 14. Sparse vs Distributed Head Mechanism

Compare cumulative restoration:

```text
Top-1
Top-2
Top-4
Top-8
All robust discovery heads
```

to the Stage 3B.5 post-Attention boundary gain.

Possible patterns:

### H-Sparse
Top-1 or Top-2 explains most causal gain.

### H-Small-Ensemble
Top-4 explains most gain.

### H-Distributed
Restoration grows gradually and requires many heads.

### H-No-Head-Recovery
No head/set reproduces substantial gain despite robust post-Attention boundary restoration.

This would require a methodological redirect rather than forced head attribution.

---

## 15. Upstream-State Control Cell

After candidate heads are frozen from the 3 qualifying cells, evaluate those same heads/sets in:

```text
E_d / W5
```

as a control.

Because Stage 3B.5 classified this cell as upstream-state dominated, do not expect the same head-level injection mechanism automatically.

Preserve whatever heterogeneity appears.

---

## 16. Gate From Phase A to Phase B

Proceed to source-path decomposition only if at least one qualifying cell has:

- one confirmed head or frozen head set with robust bidirectional semantic restoration;
- true semantic effect clearly exceeding sham effect;
- meaningful recovery of the Stage 3B.5 post-Attention gain.

If no head/set passes:

**STOP and REDIRECT.**

Do not proceed to source-path analysis merely because raw attention looks interpretable.

---

# 17. Phase B — Source-Path Decomposition

For each confirmed causal head or minimal confirmed head set, decompose preceding token positions into source groups.

Primary source groups:

\[
V = 	ext{all visual-token positions}
\]

\[
P = 	ext{all eligible non-visual prefix positions}
\]

\[
R = 	ext{previous generated reasoning-token positions}
\]

The exact prefix partition must be loaded from the Stage 3B.0 token-layout audit.

If useful as a frozen secondary split:

```text
P = Q + T
```

where:

- `Q` = actual user question/content tokens;
- `T` = trailing assistant/control/post-question prefix tokens.

Do not define groups from attention patterns.

---

## 18. Source-Path Semantic Swap

For a confirmed target query head `h` and source group `S`, use recipient query state and swap semantic K/V only for token positions in `S`.

Example:

```text
recipient:
C

target head:
recipient Q_h

visual positions V:
K/V from O

prefix P:
K/V from C

reasoning R:
K/V from C
```

This is a V-only semantic source swap into the target head.

Run reciprocal.

Similarly test:

- P-only swap
- R-only swap

All other heads remain recipient-native.

Allow downstream output projection, residual, MLP, and later layers to recompute naturally.

---

## 19. Primary Source-Path Arms

For each confirmed head/set run:

```text
All-source semantic swap
V-only semantic swap
P-only semantic swap
R-only semantic swap
```

If `P` is substantial, optionally and prospectively split:

```text
Q-only
T-only
```

after the coarse P result is frozen.

Do not begin ROI localization in Stage 3B.6.

---

## 20. Source-Path Metric

For source group `S` in head/set `H`, define:

\[
BPR_{H,S}
=
rac{
\Delta_{H,S,Oightarrow C}
+
\Delta_{H,S,Cightarrow O}
}{2}
\]

Use unnormalized bidirectional path restoration as primary.

Compare with all-source swap using:

\[
PRR_{H,S}
=
rac{BPR_{H,S}}{BPR_{H,all}}
\]

Do not interpret as unique additive information fractions.

---

## 21. Source-Path Controls

For every source group:

- self semantic swap;
- within-semantic sham swap;
- bidirectional O↔C;
- exact token-position alignment;
- exact source-group isolation audit.

Verify that:

- V-only changes only visual K/V for the target head/set;
- P-only changes only prefix positions;
- R-only changes only prior reasoning positions;
- other heads remain recipient-native.

---

## 22. Source-Path Scientific Outcomes

### P1 — Visual-dominant path

If:

\[
BPR_{H,V}
pprox
BPR_{H,all}
\]

and P/R effects are much smaller:

> **The causal head retrieves evidence identity primarily through direct visual-token input.**

This would strongly support active visual retrieval during reasoning.

### P2 — Prefix-mediated path

If P dominates:

> the head’s current evidence state is primarily retrieved from image-conditioned prefix representations rather than direct visual tokens.

### P3 — Reasoning-mediated path

If R dominates:

> the current head retrieves evidence identity mainly from previously generated reasoning states.

### P4 — Mixed / redundant source paths

Multiple source groups have robust effects or only joint all-source swap explains the head effect.

Do not force a single-source mechanism.

---

## 23. Stage 3B.1 Cutoff Connection

For each confirmed visual-path head/set, compare source-path strength with the frozen Stage 3B.1 persistent direct-vision dependence.

A strong triangulation would be:

```text
high all-V cutoff damage
+
high V-only causal head restoration
```

This would support the claim that continued direct visual access matters because specific visual evidence is transferred through a localized Attention pathway.

---

## 24. Stage 2C Attention Connection — Secondary Only

After all causal head/path results are frozen, compare:

1. raw ROI attention magnitude;
2. selected head’s visual attention mass;
3. selected head’s causal semantic restoration;
4. V-only source-path restoration.

Possible findings:

### Attention-high but causal-low
Semantic alignment without major causal transfer.

### Attention-high and causal-high
Attention coincides with genuine retrieval in that specific causal head.

### Attention-low but causal-high
Important evidence transfer without a large raw attention signal.

This can sharpen the paper’s methodological claim:

> **attention weight magnitude, causal Attention-module contribution, and evidence-specific source-path transfer are distinct measurements.**

---

## 25. ROI and Pattern-vs-Value Are Deferred

Even if a strong V-only head/path is found, Stage 3B.6 must stop before testing:

```text
target ROI vs other visual tokens
K-only vs V-only vs KV swap
attention-pattern vs value-content
```

Those should be the next gated stage.

First establish WHICH HEAD and WHICH SOURCE CLASS without adding ROI-level assumptions.

---

## 26. What Stage 3B.6 May Establish

If supported:

### Head localization
A small set of query heads accounts for a substantial part of the evidence-specific post-Attention gain near the discriminative evidence decision.

### Direct visual source path
Those causal heads retrieve evidence identity primarily from visual-token states rather than from prefix or previous-reasoning states.

### Language-mediated source path
Alternatively, the causal Attention head may be driven mainly by language-side image-conditioned states.

### Distributed head/source mechanism
Or the post-Attention gain may be distributed across multiple heads and/or source groups.

All claims must remain restoration-controlled and sham-controlled.

---

## 27. What Stage 3B.6 Cannot Yet Establish

Do not claim:

- target ROI is the exact source;
- a specific attention pattern itself carries the fact;
- K vs V mechanism;
- MLP feature/neuron mechanism;
- long-term Q/R memory lifecycle;
- multi-evidence refresh;
- correct-vs-wrong failure mechanisms;
- discrete LOOK/THINK states.

---

## 28. Decision After Stage 3B.6

Recommend exactly one next direction.

### GO — ROI-specific visual path + pattern/value decomposition

Use if:

- confirmed head/set exists;
- V-only path explains substantial semantic restoration;
- sham/self controls pass.

### GO — Language-side source-path localization

Use if P or R dominates.

### GO — Multi-head distributed circuit analysis

Use if many heads are needed to recover the post-Attention boundary gain.

### REDIRECT — Head-localization failure

Use if the post-Attention boundary gain is robust but no single/frozen head set transfers semantic identity under validated intervention.

---

## 29. Output Structure

Create:

```text
outputs/stage3b6/
  config/
    stage3b6_config.json
    qualifying_cells.json
    discovery_primary_split.json
    frozen_head_candidates.json

  audit/
    gqa_head_map.md
    head_tensor_layout.json
    output_projection_slices.json
    source_token_groups.json
    hook_validation.md

  discovery/
    per_head_discovery_results.jsonl
    head_rankings.json
    candidate_freeze_report.md

  validation/
    head_intervention_validation.json
    source_path_validation.json
    validation_report.md

  scoring/
    primary_head_results.jsonl
    cumulative_headset_results.jsonl
    upstream_control_results.jsonl
    source_path_results.jsonl

  analysis/
    head_restoration_statistics.json
    sparse_vs_distributed_heads.json
    source_path_statistics.json
    cutoff_triangulation.json
    attention_secondary_analysis.json
    figures/

  summaries/
    stage3b6_summary.md
    stage3b6_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3B.5 or earlier artifacts.

---

## 30. Required Figures

At minimum:

1. discovery-set effect across all 32 query heads for each qualifying cell;
2. confirmatory restoration for frozen candidate heads;
3. Top-1/2/4/8 cumulative recovery vs Stage 3B.5 post-Attention gain;
4. head effects across the 3 qualifying cells;
5. qualifying heads evaluated in the `E_d/W5` upstream control cell;
6. V vs P vs R source-path restoration;
7. per-problem visual-path restoration scatter;
8. Stage 3B.1 cutoff damage vs V-path restoration;
9. raw attention magnitude vs causal head restoration as secondary analysis;
10. representative bidirectional head/path semantic flips.

---

## 31. Acceptance Criteria

Stage 3B.6 technically passes if:

1. Stage 3B.5 qualifying cells and upstream control are preserved exactly;
2. exact target Attention layers are loaded from frozen artifacts;
3. GQA query-head/KV-group mapping is audited;
4. query-head-selective intervention is mechanically validated;
5. 8 discovery bases are used before 37-base primary confirmation;
6. head rankings/candidate sets are frozen before primary scoring;
7. no attention-based head selection is used;
8. O↔C head interventions are bidirectional;
9. self and paired sham controls are implemented;
10. cumulative Top-k head sets are tested;
11. the upstream `E_d/W5` control is evaluated only after head candidates are frozen;
12. source-path decomposition occurs only after a head-level gate passes;
13. V/P/R source groups are prospectively frozen;
14. source-path semantic swaps are bidirectional and group-selective;
15. `base_problem_id` remains the statistical unit;
16. ROI/K-vs-V/pattern-value analysis is not started;
17. an explicit GO / REDIRECT recommendation is written.

Technical PASS does not require a sparse head mechanism or a visual-dominant path.

---

## 32. Stop Condition

After:

- GQA/head audit;
- discovery head screen;
- candidate freeze;
- 37-base head confirmation;
- cumulative head-set analysis;
- upstream-control analysis;
- gated V/P/R source-path decomposition;
- secondary attention/cutoff triangulation;
- final recommendation;

**STOP.**

Do not start:

- ROI-specific path patching;
- K-only/V-only/pattern-value decomposition;
- MLP feature/neuron analysis;
- Q/R long-term memory tracing;
- multi-evidence A/B refresh;
- correct-vs-wrong failure analysis.

Return the complete Stage 3B.6 results for review.

The next plan must be determined only after jointly considering Stage 3B.6 with all prior Stage 2A–3B.5 evidence.
