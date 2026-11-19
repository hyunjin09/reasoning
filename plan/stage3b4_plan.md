# Stage 3B.4 Plan — Restoration-Controlled Module Localization

## 0. Purpose

Stage 3B.4 follows the successful Stage 3B.3-R result.

The goal is to determine:

> **Which transformer submodule implements the late evidence-specific visual transfer identified near the discriminative evidence decision?**

Stage 3B.3-R localized robust causal transfer to narrow late-layer windows near `E_d-1` and `E_d`, but did not identify whether the relevant computation is carried primarily by:

- self-attention,
- MLP/feed-forward computation,
- or their combined residual interaction.

The primary question is:

\[
oxed{	ext{Does evidence-specific restoration come from Attention, MLP, or both?}}
\]

This stage must preserve the **restoration-controlled causal design** introduced in Stage 3B.3-R.

Do not return to uncontrolled ablation-only interpretation.

Do not start head-level, ROI-path, Q/R-carrier, multi-evidence, or failure-analysis experiments automatically.

---

## 1. Scientific Handoff

### Stage 2A–2C

Evidence-aligned visual attention was observed during reasoning, but Stage 2C showed that most visual-attention peaks are mention-centered and often reappear at later semantic references.

Therefore:

> **attention magnitude alone cannot identify fresh visual acquisition.**

### Stage 3A

Localized original/counterfactual visual edits showed strong causal sensitivity:

- 49/49 independent bases in the expected CE direction;
- sham-controlled effects were large.

Visual content, not attention magnitude, became the causal handle.

### Stage 3B.0

Generation-start visual cutoff preserved only a small fraction of the full Stage 3A effect.

A small prefill residual was causally carried by Q-side cached states.

Therefore prefill visual-to-language transfer exists, but does not explain most evidence-specific reasoning.

### Stage 3B.1

Visual cutoff remained strongly damaging even immediately before explicit evidence mention.

Result:

> **persistent direct-vision dependence.**

### Stage 3B.3-R

The original Stage 3B.3 smoke design failed because its semantic-preserving original sham was not a valid zero-effect restoration control.

This failure is immutable and must remain documented.

Stage 3B.3-R prospectively redesigned the experiment using paired semantic classes:

```text
O / O_sham
C / C_sham
```

and passed independent validation before scoring the reserved primary cohort.

Primary results:

- 41 independent primary bases;
- largest median normalized selective sufficiency:
  - `0.6107` at `E_d-1 / W4`;
- largest median normalized paired-semantic restoration:
  - `0.6531` at `E_d-1 / W4`;
- largest median normalized current-position transfer:
  - `1.1614` after layer 35;
- fine localization retained:
  - `E_d-1 / W4`
  - `E_d-1 / W5`
  - `E_d / W4`
  - `E_d / W5`

Therefore:

> **Evidence-specific visual-source identity causally transfers into the current reasoning computation through narrow late-layer regions near the discriminative evidence decision.**

Stage 3B.4 decomposes that effect into transformer submodules.

---

## 2. Critical Methodological Rule

The Stage 3B.3 control failure must shape Stage 3B.4.

Mandatory rule:

> **A module effect is not considered evidence-specific merely because zeroing/removing that module hurts prediction.**

All primary claims must be supported by **paired semantic restoration**, comparing matched original and counterfactual semantic classes with validated shams.

Necessity/ablation results may be reported only as secondary context.

---

## 3. Primary Cohort

Reuse the Stage 3B.3-R primary cohort.

- 41 independent base problems;
- 37 numeric-label bases with valid paired semantic restoration controls;
- 4 structural bases with the restricted arms already allowed by Stage 3B.3-R.

Primary statistical unit:

```text
base_problem_id
```

For paired restoration, the primary inferential cohort is the 37 bases with:

```text
O
O_sham
C
C_sham
```

Do not expand or alter the cohort based on module-level outcomes.

---

## 4. Frozen Coordinates and Layer Targets

Use only the narrow candidates already authorized by Stage 3B.3-R:

```text
E_d - 1 / W4
E_d - 1 / W5
E_d     / W4
E_d     / W5
```

Load the exact retained two-layer windows from the frozen Stage 3B.3-R artifacts.

Do not redefine W4/W5 from memory.

No new layer search should occur in Stage 3B.4.

The purpose is **module decomposition inside already-localized windows**.

---

## 5. Transformer Decomposition

For each target layer, identify the exact Qwen3-VL decoder block computation.

At minimum distinguish:

- input residual before self-attention;
- self-attention contribution after output projection and before residual addition;
- post-attention residual;
- MLP contribution before residual addition;
- final block residual.

Account for the actual pre-norm / RMSNorm implementation.

Do not assume textbook ordering without auditing the model code.

Save:

```text
outputs/stage3b4/audit/block_decomposition.md
outputs/stage3b4/audit/hook_locations.json
```

Freeze hook definitions before primary scoring.

---

## 6. Primary Causal Design

Use the same paired semantic restoration framework as Stage 3B.3-R.

Semantic classes:

```text
Original:
O
O_sham

Counterfactual:
C
C_sham
```

Primary intervention target:

> **current-position module contribution at the frozen evidence-decision coordinate and frozen layer window.**

Do not patch arbitrary full-sequence module outputs.

---

## 7. Core Conditions

At every authorized coordinate/window run:

### M0 — Baseline semantic conditions

```text
O
O_sham
C
C_sham
```

Must reproduce frozen Stage 3B.3-R evidence scores within tolerance.

### M1 — Attention-output semantic restoration

Restore the current-position self-attention contribution from one semantic class into the other.

Example:

```text
source: O
recipient: C
```

Patch:

\[
a_\ell^{O} ightarrow a_\ell^{C}
\]

for the target two-layer window.

Run reciprocal:

\[
a_\ell^{C} ightarrow a_\ell^{O}
\]

Use paired semantic-class contrast, not a single raw patch.

### M2 — MLP-output semantic restoration

Restore:

\[
m_\ell^{O} ightarrow m_\ell^{C}
\]

and reciprocal:

\[
m_\ell^{C} ightarrow m_\ell^{O}
\]

at the current position.

### M3 — Attention + MLP joint restoration

Restore both module contributions from the same source semantic class.

This tests whether:

- effects are additive,
- one module dominates,
- or both are jointly required.

### M4 — Full block-output restoration

Restore the current-position full block output.

This bridges the module decomposition back to the already observed residual-transfer effect.

---

## 8. Optional Necessity Arms — Secondary Only

Only after restoration validation, optionally run:

```text
Attention contribution knockout
MLP contribution knockout
```

within the same narrow windows.

These are secondary.

Do not use `zeroing hurts` as the main evidence that a module carries visual identity.

---

## 9. Paired Semantic Restoration Metric

For module `M`, compute source-oriented evidence shifts in both directions:

- `O -> C`
- `C -> O`

Define:

\[
BMR_M =
rac{
\Delta_{M,Oightarrow C}
+
\Delta_{M,Cightarrow O}
}{2}
\]

Use unnormalized effect as primary.

Also report the same normalized paired-restoration quantity used in Stage 3B.3-R for direct comparability.

Do not clip normalized scores.

---

## 10. Sham-Controlled Semantic Contrast

For every module restoration, compute the semantic restoration contrast against paired sham restoration.

Conceptually:

```text
true semantic restoration
minus
within-semantic sham restoration
```

Use the exact paired formulation already validated in Stage 3B.3-R.

Do not invent a new sham definition after observing module results.

The goal is to ensure the effect tracks **semantic visual-source identity**, not generic restoration perturbation.

---

## 11. Module Attribution Ratios

For descriptive decomposition compare each module restoration with full block restoration.

For example:

\[
R_{attn} = BMR_{attn}/BMR_{block}
\]

\[
R_{mlp} = BMR_{mlp}/BMR_{block}
\]

\[
R_{joint} = BMR_{attn+mlp}/BMR_{block}
\]

Do not interpret these as unique additive fractions.

Attention and MLP may be nonlinear and interdependent.

---

## 12. Interaction Analysis

Define descriptive interaction:

\[
I =
BMR_{attn+mlp}
-
BMR_{attn}
-
BMR_{mlp}
\]

Possible patterns:

### A — Attention-dominant

Attention restoration approaches full block restoration while MLP restoration is small.

Interpretation:

> evidence-specific visual transfer is primarily routed through self-attention.

### B — MLP-dominant

MLP restoration approaches full block restoration.

Interpretation:

> evidence identity is mainly transformed/constructed through MLP computation.

### C — Attention then MLP

Attention and MLP both contribute, and joint restoration approaches full block restoration.

Interpretation:

> attention routes evidence-specific visual content and MLP transforms/consolidates it.

### D — Distributed block effect

Attention and MLP individually weak but full block restoration strong.

Interpretation:

> the causal representation depends on module interaction, normalization, or residual-state composition.

Do not force a simple module story.

---

## 13. Temporal Comparison: E_d-1 vs E_d

Compare the same module effects at:

```text
E_d - 1
E_d
```

Questions:

- Is module-specific transfer already present one decision before the discriminative token?
- Does it strengthen at the actual evidence decision?
- Does Attention dominate earlier and MLP later?
- Is the same mechanism active at both coordinates?

Report within-problem paired differences.

---

## 14. W4 vs W5 Comparison

Compare the two frozen late windows.

Questions:

- Is transfer concentrated in W4?
- Does W5 add refinement?
- Are W4 and W5 redundant?
- Does combined W4+W5 restoration exceed either alone?

A combined W4+W5 condition may be added only as a prospectively frozen secondary condition.

Do not reopen a broad layer sweep.

---

## 15. Current-Position Scope

Primary Stage 3B.4 intervention remains at the **current evidence-decision position**.

Do not yet patch:

- all previous reasoning positions;
- Q states;
- all sequence positions;
- individual visual positions.

The narrow question is:

> **Which submodule builds the evidence-specific current-position state?**

---

## 16. Validation Cohort

Before scoring all primary bases, use an independent validation set if reserved examples remain.

Target:

```text
8–10 validation bases
```

Prefer numeric-label examples with valid `O/O_sham/C/C_sham` controls.

Validation gates:

1. baseline reproduction;
2. self-restoration transparency;
3. sham restoration near-zero semantic effect;
4. exact module hook placement;
5. reciprocal source-direction behavior;
6. full block restoration recovers the expected residual tendency;
7. finite outputs;
8. deterministic replication.

Only after all validation gates pass should the primary cohort be scored.

If no independent reserved cohort exists, document this and use a frozen non-primary smoke set without changing primary hypotheses.

---

## 17. Primary Statistics

For each coordinate/window/module report:

- N;
- median unnormalized bidirectional restoration;
- mean;
- bootstrap 95% CI over `base_problem_id`;
- normalized paired restoration;
- proportion source-consistent in both directions;
- sham semantic shift;
- self-restoration error.

Emphasize medians because prior normalized effects were heterogeneous.

Use a predeclared multiple-testing correction across the fixed family, e.g. Holm.

---

## 18. Frozen Primary Test Family

Primary hypothesis family:

```text
Coordinates:
E_d - 1
E_d

Windows:
W4
W5

Modules:
Attention
MLP
Attention + MLP
Block
```

Do not add more layers/modules after seeing primary results.

---

## 19. Secondary Relation to Attention Magnitude

Do not use Stage 2 attention for selection.

After module results are frozen, optionally test:

- whether high ROI attention predicts attention-module restoration;
- whether mention-centered attention remains high when Attention-module causal restoration is weak;
- whether MLP-mediated evidence construction can occur despite strong visual attention.

This can sharpen the methodological contribution:

> **attention magnitude is not equivalent to attention-module causal contribution.**

Secondary only.

---

## 20. What Stage 3B.4 May Establish

If supported, Stage 3B.4 may support one of:

### Attention-mediated retrieval

> Evidence-specific visual content is causally routed into the current reasoning state through self-attention in narrow late layers near the discriminative evidence decision.

### MLP-mediated construction

> Late MLP computation is required to construct/transform the evidence-specific current-position representation.

### Attention-to-MLP cascade

> Self-attention routes visual evidence into the current token state and subsequent MLP computation transforms/consolidates that evidence.

### Distributed module interaction

> The localized transfer cannot be assigned cleanly to either module alone and depends on combined block computation.

All claims must be restoration-controlled.

---

## 21. What Stage 3B.4 Cannot Yet Establish

Do not claim:

- which attention heads implement transfer;
- which visual ROI/path is used;
- which visual token carries the fact;
- Q/R long-term storage;
- path-specific V→R circuits;
- LOOK/THINK states;
- multi-evidence refresh;
- failure mechanisms.

---

## 22. Decision After Stage 3B.4

### GO — Attention-head/path localization

Use if Attention restoration explains a substantial, robust, bidirectional, sham-controlled fraction of block restoration.

### GO — MLP mechanism localization

Use if MLP restoration dominates or is required for block restoration.

### GO — Attention→MLP cascade analysis

Use if both modules contribute and joint restoration is strongest.

### REDIRECT — Distributed block computation

Use if neither module alone is stable but full block restoration remains strong.

---

## 23. Output Structure

Create:

```text
outputs/stage3b4/
  config/
    stage3b4_config.json
    primary_family.json
    cohort_manifest.jsonl

  audit/
    block_decomposition.md
    hook_locations.json
    tensor_shape_diagnostics.json

  validation/
    validation_manifest.jsonl
    validation_results.json
    validation_report.md

  scoring/
    attention_restoration.jsonl
    mlp_restoration.jsonl
    joint_restoration.jsonl
    block_restoration.jsonl
    optional_necessity_results.jsonl

  analysis/
    module_restoration_statistics.json
    module_interaction_statistics.json
    coordinate_comparison.json
    window_comparison.json
    attention_secondary_analysis.json
    figures/

  summaries/
    stage3b4_summary.md
    stage3b4_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3B.3-R or earlier artifacts.

---

## 24. Required Figures

At minimum:

1. Attention vs MLP vs joint vs block restoration at `E_d-1/W4`;
2. same at `E_d-1/W5`;
3. same at `E_d/W4`;
4. same at `E_d/W5`;
5. per-problem Attention vs MLP restoration scatter;
6. paired `E_d-1` vs `E_d` module effects;
7. W4 vs W5 comparison;
8. sham semantic restoration vs true semantic restoration;
9. representative successful bidirectional restoration examples.

---

## 25. Acceptance Criteria

Stage 3B.4 technically passes if:

1. the original Stage 3B.3 failed control remains documented;
2. Stage 3B.3-R paired semantic control logic is reused;
3. W4/W5 exact layers are loaded from frozen artifacts;
4. `E_d-1` and `E_d` are frozen;
5. model block ordering and hook locations are audited;
6. independent validation/smoke gate passes before primary scoring;
7. Attention restoration is bidirectional;
8. MLP restoration is bidirectional;
9. Attention+MLP and block restoration controls are included;
10. self restoration is transparent;
11. paired sham semantic restoration is included;
12. `base_problem_id` remains the statistical unit;
13. primary test family is frozen;
14. attention magnitude is not used for selection;
15. no head/path/ROI/Q/R experiment is started;
16. an explicit GO / REDIRECT recommendation is written.

Technical PASS does not require one module to dominate.

---

## 26. Stop Condition

After:

- implementation audit;
- validation;
- full restoration-controlled module decomposition;
- sham/self controls;
- interaction analysis;
- coordinate/window comparison;
- final recommendation;

**STOP.**

Do not start:

- head-level attention analysis;
- ROI-specific attention-path analysis;
- Q/R carrier patching;
- path patching;
- multi-evidence A/B analysis;
- correct-vs-wrong failure analysis.

Return the complete Stage 3B.4 results for review.

The next plan must be determined only after reviewing Stage 3B.4 together with all prior Stage 2A–3B.3-R evidence.
