# Stage 3B.5 Plan — Sequential Residual-Stream Mediation and State-Dependent Recompute

## 0. Purpose

Stage 3B.5 follows the Stage 3B.4 result:

> **Full-block restoration is robust, but isolated Attention, isolated MLP, and even Attention+MLP output restoration do not explain enough of the block-level semantic effect under the frozen attribution rules.**

Stage 3B.4 therefore redirected away from a simple Attention-dominant / MLP-dominant / Attention→MLP-cascade interpretation.

Stage 3B.5 asks:

> **At which within-block residual boundary does evidence identity become causally represented, and is the Stage 3B.4 block-vs-module gap explained by state-dependent sequential recomputation rather than by a generic “distributed” mechanism?**

The central distinction is between:

1. patching a precomputed module output into a mismatched recipient state, and
2. patching the source semantic state at a residual boundary and allowing downstream modules to recompute naturally.

Do not start head-level, ROI-specific, Q/R-carrier, multi-evidence, or failure-analysis experiments automatically.

---

## 1. Scientific Handoff

### Stage 3B.3-R

Restoration-controlled layer localization established robust evidence-specific transfer near:

```text
E_d - 1 / W4
E_d - 1 / W5
E_d     / W4
E_d     / W5
```

with strong current-position residual transfer.

### Stage 3B.4

Primary paired semantic restoration cohort:

- 37 independent numeric-label bases with valid O/O_sham/C/C_sham controls.

Median unnormalized restoration:

| Coordinate | Window | Attention | MLP | Joint | Block |
|---|---:|---:|---:|---:|---:|
| E_d-1 | W4/F28_29 | 0.467 | 0.071 | 0.551 | 0.997 |
| E_d-1 | W5/F32_33 | 0.141 | 0.191 | 0.381 | 1.372 |
| E_d | W4/F28_29 | 1.967 | 0.211 | 3.063 | 6.064 |
| E_d | W5/F32_33 | 1.314 | 1.406 | 4.059 | 9.173 |

Key observation:

> **Full-block restoration is consistently stronger than isolated module-output restoration, and even Attention+MLP output restoration remains substantially below full-block restoration.**

This does not prove a uniquely distributed mechanism.

Live alternatives include:

- source/recipient incoming residual mismatch,
- RMSNorm-conditioned computation,
- nonlinearity of downstream recomputation,
- cross-layer sequential dependence,
- residual-state composition,
- restoration-surface non-additivity.

Stage 3B.5 is designed to distinguish these.

---

## 2. Core Mechanistic Hypotheses

### H1 — Incoming residual already carries most evidence identity

If pre-block residual patching followed by natural recomputation restores nearly the full block effect, then evidence identity is already present before the target block.

### H2 — Attention creates the evidence-specific state

If post-attention residual restoration is much stronger than pre-block residual restoration, Attention is where evidence identity becomes strongly represented at the current position.

### H3 — MLP creates/transforms the decision-ready state

If pre-block and post-attention restoration are similar but post-block restoration rises sharply, MLP computation is the major within-block transformation.

### H4 — State-dependent recomputation explains the Stage 3B.4 gap

If source-state patching followed by natural recomputation is much stronger than precomputed module-output patching, then the block effect depends on downstream modules being evaluated on a source-consistent state.

### H5 — Normalization-conditioned state is critical

If normalized-state transfer explains substantially more than raw additive module-output transfer, the effective computation may depend on the RMS-normalized representation presented to Attention/MLP.

### H6 — Cross-layer interaction dominates

If within-layer residual-boundary patches remain weaker than two-layer/window restoration, evidence transfer may require sequential computation across the retained two-layer window.

---

## 3. Primary Cohort

Reuse the frozen Stage 3B.4 paired-semantic primary cohort:

- 37 unique numeric-label base_problem_ids
- each with valid:
  - O
  - O_sham
  - C
  - C_sham

Primary statistical unit:

```text
base_problem_id
```

Do not add/remove problems based on Stage 3B.5 outcomes.

The 4 structural examples without complete paired semantic controls remain excluded from the primary restoration inference.

---

## 4. Frozen Coordinates and Layers

Use only:

```text
E_d - 1 / W4
E_d - 1 / W5
E_d     / W4
E_d     / W5
```

Load exact layer indices from frozen Stage 3B.3-R / Stage 3B.4 artifacts.

Known labels from Stage 3B.4:

```text
W4 = F28_29
W5 = F32_33
```

but implementation must read exact indices from artifacts rather than hard-code from this plan.

Do not reopen a global layer sweep.

---

## 5. Mandatory Architecture Audit

Audit exact Qwen3-VL decoder-block computation at target layers.

At minimum identify:

```text
h_pre
  ↓
input RMSNorm
  ↓
Self-Attention
  ↓
attention output projection
  ↓
residual add
  ↓
h_post_attn
  ↓
post-attention RMSNorm
  ↓
MLP
  ↓
residual add
  ↓
h_post_block
```

Confirm exact implementation from model code.

Document:

1. input residual location;
2. pre-attention RMSNorm output;
3. Attention output before residual add;
4. post-attention residual;
5. pre-MLP RMSNorm output;
6. MLP output before residual add;
7. post-block residual;
8. dtype;
9. tensor shape;
10. current-position index;
11. cache/recompute behavior;
12. any fused-kernel behavior affecting hook semantics.

Create:

```text
outputs/stage3b5/audit/block_state_map.md
outputs/stage3b5/audit/hook_locations.json
outputs/stage3b5/audit/tensor_shape_diagnostics.json
```

Freeze hook definitions before primary scoring.

---

## 6. Main Experimental Principle

Stage 3B.4 mainly patched precomputed module outputs.

Stage 3B.5 should instead patch states at residual/norm boundaries and let downstream computation recompute naturally.

### Previous style

```text
recipient residual from C
+
source Attention output from O
```

This can create a mismatched hybrid state.

### Stage 3B.5 style

```text
replace recipient h_pre with source h_pre
then run recipient Attention + MLP normally from that source-consistent state
```

This asks whether downstream block computation can regenerate the source semantic effect from the restored state.

---

## 7. Core Restoration Arms

At each frozen coordinate/window perform all arms bidirectionally:

```text
O -> C
C -> O
```

and with paired sham controls.

### R0 — Baseline

```text
O
O_sham
C
C_sham
```

Must reproduce Stage 3B.4 baselines within tolerance.

### R1 — Pre-block residual patch + natural recomputation

Patch current-position h_pre from source semantic class into recipient, then allow all downstream block computation to recompute naturally.

### R2 — Pre-attention normalized-state patch + downstream recomputation

Patch the RMS-normalized state presented to Attention from source into recipient while keeping the recipient raw residual path intact.

Implementation must be audited carefully.

### R3 — Post-attention residual patch + natural MLP recomputation

Patch source h_post_attn into recipient, then run pre-MLP RMSNorm, MLP, and final residual addition naturally.

### R4 — Pre-MLP normalized-state patch + natural MLP recomputation

Patch the normalized state presented to MLP from source into recipient, then let MLP recompute.

### R5 — Post-block residual patch

Patch source h_post_block into recipient.

This acts as the upper/reference restoration condition.

---

## 8. Window-Level Sequential Patching

Because W4/W5 are two-layer windows, perform both:

### Single-layer boundary patches

Within each window patch each layer individually.

### Two-layer sequential state restoration

Patch the state entering the first layer of the window and allow both layers to recompute naturally.

Do not expand outside W4/W5.

---

## 9. Recompute-vs-Precomputed Comparison

Compare Stage 3B.5 state+recompute arms with frozen Stage 3B.4 module-output arms.

Key comparisons:

```text
h_pre -> natural Attention+MLP recompute
vs
precomputed Attention+MLP output patch
```

and:

```text
h_post_attn -> natural MLP recompute
vs
precomputed MLP output patch
```

Define:

\[
Gain_{recompute}
=
BMR_{state+recompute}
-
BMR_{precomputed\ output}
\]

A large positive gain supports state-dependent sequential computation.

---

## 10. Primary Restoration Metric

Reuse paired semantic restoration from Stage 3B.3-R / Stage 3B.4.

For restoration arm X:

\[
BMR_X
=
rac{
\Delta_{X,Oightarrow C}
+
\Delta_{X,Cightarrow O}
}{2}
\]

Use unnormalized BMR as primary.

Also report normalized restoration relative to the paired semantic gap.

Never clip normalized values.

---

## 11. Paired Sham Controls

For every state-restoration arm, run within-semantic sham restoration at the same location.

Examples:

```text
O_sham -> O
O -> O_sham

C_sham -> C
C -> C_sham
```

Use the exact Stage 3B.3-R paired semantic control logic.

A restoration effect is considered semantic only if true O↔C restoration clearly exceeds within-semantic sham restoration.

---

## 12. Self-Patch Controls

For every state type:

```text
O -> O
C -> C
```

must be transparent within frozen numerical tolerance.

If not, stop and debug before primary inference.

---

## 13. Validation Gate

Before the 37-base primary cohort, use an independent 8–10 base validation set if available.

Validation must include:

1. baseline reproduction;
2. self-patch transparency;
3. paired sham effect small relative to true semantic restoration;
4. exact bidirectional source consistency;
5. exact current-position targeting;
6. no unintended all-sequence patching;
7. correct downstream recomputation after the patched boundary;
8. downstream modules actually re-execute;
9. deterministic replication;
10. finite outputs;
11. post-block patch reproduces Stage 3B.4 block tendency.

Do not score the primary cohort until the validation gate passes.

---

## 14. Primary Analysis A — Where Does Evidence Identity First Appear Within the Block?

For each frozen coordinate/window compare:

```text
R1  h_pre
R2  pre-attn normalized state
R3  h_post_attn
R4  pre-MLP normalized state
R5  h_post_block
```

Report:

- median BMR;
- mean BMR;
- bootstrap 95% CI;
- bidirectional source consistency;
- sham-controlled effect;
- normalized restoration.

The main object is the incremental restoration profile across block boundaries.

---

## 15. Primary Analysis B — Incremental Boundary Gains

Define descriptive causal increments:

\[
G_{attn}
=
BMR_{post-attn}
-
BMR_{pre}
\]

\[
G_{mlp}
=
BMR_{post-block}
-
BMR_{post-attn}
\]

Also compare norm-boundary gains where technically valid.

Use bootstrap CIs over base_problem_id.

Do not interpret these as unique information fractions.

---

## 16. Primary Analysis C — State-Dependent Recompute Test

Compare:

```text
BMR(h_pre -> recompute)
```

with frozen Stage 3B.4:

```text
BMR(Attention+MLP precomputed outputs)
```

and compare:

```text
BMR(h_post_attn -> recompute)
```

with:

```text
BMR(MLP precomputed output)
```

If recompute variants are substantially stronger, this supports:

> **The block effect depends on downstream computation being evaluated on a source-consistent state, not merely on transplanting precomputed module outputs.**

---

## 17. Primary Analysis D — Cross-Layer Sequential Dependence

Within W4 and W5 compare:

- first-layer state restoration;
- second-layer state restoration;
- first-layer entry restoration followed by full two-layer recomputation;
- final two-layer block-output restoration.

Possible patterns:

### L1 — First-layer entry already sufficient
Evidence identity predates the window.

### L2 — First layer creates most of the signal
Strong gain after first layer.

### L3 — Second layer creates/refines the signal
Signal rises mainly after second layer.

### L4 — Two-layer synergy
Neither individual layer reproduces the full effect, but sequential two-layer recomputation does.

---

## 18. E_d-1 vs E_d Comparison

Repeat the same boundary analysis at:

```text
E_d - 1
E_d
```

Questions:

- Does evidence identity enter the current residual earlier at E_d?
- Does the Attention boundary gain increase sharply at E_d?
- Does MLP become more important only at the actual decision?
- Is state-dependent recomputation especially strong at E_d?

Use within-problem paired comparisons.

---

## 19. W4 vs W5 Comparison

Determine whether:

- W4 creates an intermediate evidence state;
- W5 converts it into a stronger decision-ready state;
- or both redundantly transform the same state.

Do not reopen layers outside W4/W5.

---

## 20. Frozen Primary Hypothesis Family

Primary family:

```text
Coordinates:
E_d - 1
E_d

Windows:
W4
W5

Residual/state boundaries:
h_pre
pre-attn norm
h_post_attn
pre-MLP norm
h_post_block

Sequential recompute:
single-layer
two-layer window
```

Freeze all conditions before primary scoring.

Use a predeclared multiple-testing correction such as Holm.

---

## 21. Secondary Readout Analysis

Only after causal results are frozen, optionally inspect semantic content of residual states using:

- logit lens;
- tuned lens if available and validated;
- Patchscope-like readout.

Questions:

- At which boundary does original-vs-counterfactual fact become decodable?
- Does decodability precede causal restoration?
- Does causal restoration rise before target content is linearly decodable?

These are descriptive only.

---

## 22. Attention Magnitude Is Secondary

Do not select windows/examples using attention.

After causal results are frozen, optionally compare:

- Stage 2C ROI attention;
- Stage 3B.4 Attention-output restoration;
- Stage 3B.5 post-attention residual gain.

Potential methodological contribution:

> **attention weight magnitude, Attention-module causal contribution, and evidence representation in the residual stream are distinct quantities.**

---

## 23. Scientific Outcomes

### Outcome A — Evidence already present at h_pre

If pre-block residual restoration is nearly as strong as post-block restoration:

> the target block is not the origin of evidence transfer.

Next step: upstream residual-origin search.

### Outcome B — Strong post-attention jump

If post-attention restoration is much stronger than pre-block:

> Attention causally injects evidence identity into the current-position residual.

Next step: head/path localization.

### Outcome C — Strong post-block jump

If post-attention is weak but post-block is strong:

> MLP-side transformation is critical.

Next step: MLP/residual mechanism localization.

### Outcome D — State patch + recomputation closes Stage 3B.4 gap

If source-state recomputation approaches full block restoration while precomputed module-output restoration remains weaker:

> **state-dependent sequential computation** explains the previous apparent distributed-block effect.

### Outcome E — Two-layer recomputation required

If individual within-layer patches remain weak but two-layer recomputation is strong:

> evidence transfer depends on cross-layer sequential processing.

### Outcome F — Gap remains unexplained

Consider:

- wider cross-layer interaction;
- normalization/residual coupling;
- cache-state dependence;
- off-manifold patching limitations.

Do not prematurely label it “distributed representation.”

---

## 24. What Stage 3B.5 May Establish

If supported, Stage 3B.5 may establish:

> **where inside a late transformer block evidence identity becomes causally represented at the current reasoning position.**

and potentially:

> **the Stage 3B.4 block-vs-module gap is explained by state-dependent sequential recomputation rather than independent additive module contributions.**

---

## 25. What Stage 3B.5 Cannot Yet Establish

Do not claim:

- specific attention heads;
- specific ROI-to-token paths;
- exact visual-token source;
- Q/R long-term carriers;
- multi-evidence refresh;
- failure mechanisms;
- general LOOK/THINK states.

---

## 26. Decision After Stage 3B.5

Recommend exactly one:

### GO — Attention head/path localization
Use if a strong causal jump appears at post-attention boundary.

### GO — MLP/residual mechanism localization
Use if post-block gain dominates.

### GO — Upstream residual-origin search
Use if h_pre restoration is already close to block restoration.

### GO — Cross-layer sequential mediation
Use if two-layer recomputation is necessary.

### REDIRECT — Broader residual/norm interaction
Use if no boundary/recompute arm explains block-level effect.

---

## 27. Output Structure

Create:

```text
outputs/stage3b5/
  config/
    stage3b5_config.json
    primary_family.json
    cohort_manifest.jsonl

  audit/
    block_state_map.md
    hook_locations.json
    tensor_shape_diagnostics.json

  validation/
    validation_manifest.jsonl
    validation_results.json
    validation_report.md

  scoring/
    pre_block_state_restoration.jsonl
    pre_attn_norm_restoration.jsonl
    post_attn_state_restoration.jsonl
    pre_mlp_norm_restoration.jsonl
    post_block_restoration.jsonl
    two_layer_recompute_restoration.jsonl

  analysis/
    boundary_restoration_statistics.json
    incremental_gain_statistics.json
    recompute_vs_precomputed.json
    cross_layer_sequential_analysis.json
    coordinate_comparison.json
    window_comparison.json
    optional_readout_analysis.json
    figures/

  summaries/
    stage3b5_summary.md
    stage3b5_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3B.4 or earlier artifacts.

---

## 28. Required Figures

At minimum:

1. restoration across h_pre -> post_attn -> post_block at E_d-1/W4;
2. same at E_d-1/W5;
3. same at E_d/W4;
4. same at E_d/W5;
5. raw-state vs normalized-state restoration;
6. recompute-state restoration vs Stage 3B.4 precomputed module-output restoration;
7. single-layer vs two-layer sequential recomputation;
8. E_d-1 vs E_d boundary gains;
9. W4 vs W5 comparison;
10. representative bidirectional restoration trajectories.

---

## 29. Acceptance Criteria

Stage 3B.5 technically passes if:

1. Stage 3B.4 redirect remains preserved;
2. paired semantic O/O_sham/C/C_sham logic is retained;
3. same 37 primary bases are used;
4. W4/W5 and E_d-1/E_d remain frozen;
5. exact Qwen3-VL block ordering is audited;
6. all residual/norm boundaries are prospectively defined;
7. validation passes before primary scoring;
8. state patches are bidirectional;
9. self patches are transparent;
10. paired sham controls are implemented;
11. downstream recomputation after state patch is verified;
12. single-layer and two-layer recompute arms are implemented;
13. Stage 3B.4 module-output results are used only as frozen comparison;
14. base_problem_id remains the statistical unit;
15. attention magnitude is not used for selection;
16. no head/ROI/Q/R/multi-evidence experiment is started;
17. an explicit next-stage decision is written.

Technical PASS does not require a simple within-block mechanism.

---

## 30. Stop Condition

After:

- architecture audit;
- validation;
- residual-boundary restoration;
- natural recomputation tests;
- sham/self controls;
- cross-layer sequential analysis;
- comparison with Stage 3B.4;
- final recommendation;

**STOP.**

Do not start:

- head-level attention analysis;
- ROI-specific path patching;
- Q/R carrier patching;
- MLP feature/neuron analysis;
- multi-evidence A/B analysis;
- correct-vs-wrong failure analysis.

Return the complete Stage 3B.5 results for review.

The next plan must be determined only after jointly considering Stage 3B.5 with all prior Stage 2A–3B.4 evidence.
