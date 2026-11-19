# Stage 2B Plan: Evidence-Specific Causal Dependence Pilot

## 1. Purpose

Stage 2B is the first **causal intervention stage**.

Stage 2A found descriptive evidence that, in a subset of multi-evidence MathVerse trajectories, visual focus appears to shift from an earlier evidence item \(A\) to a later evidence item \(B\).

Stage 2B asks:

> **Are those visually attended evidence items actually causally required at the reasoning stages where they appear relevant?**

The target result is an **evidence-specific temporal crossover**:

\[
\begin{array}{c|cc}
 & A\text{-window} & B\text{-window}\\
\hline
A\text{-ROI knockout} & \text{large effect} & \text{small effect}\\
B\text{-ROI knockout} & \text{small effect} & \text{large effect}
\end{array}
\]

This is a **five-example feasibility pilot only**.

Do not expand automatically.

---

## 2. Stage 2A Handoff

Stage 2A ended with a **CONDITIONAL GO**.

Use only these five high-confidence pilot examples:

```text
699
739
2799
3044
3764
```

For each example, Stage 2A already froze:

- Evidence A
- Evidence B
- ROI_A
- ROI_B
- A-related reasoning window
- B-related reasoning window
- candidate future intervention windows

Do not change these annotations after observing Stage 2B outcomes.

Read before running:

```text
overview.md

outputs/stage2a/summaries/stage2a_summary.md
outputs/stage2a/summaries/stage2a_acceptance.json
outputs/stage2a/summaries/stage2b_recommendation.md

outputs/stage2a/evidence_subset/evidence_annotations.jsonl
outputs/stage2a/evidence_subset/evidence_subset_report.md
outputs/stage2a/evidence_subset/examples/<example_id>/
```

---

## 3. Main Scientific Question

For each sample:

> **Does removing the currently required visual evidence disrupt reasoning more than removing the other evidence or a matched irrelevant region?**

Expected pattern:

### A window

\[
\Delta(A\text{-ROI}) >
\Delta(B\text{-ROI})
\]

and:

\[
\Delta(A\text{-ROI}) >
\Delta(\text{irrelevant ROI})
\]

### B window

\[
\Delta(B\text{-ROI}) >
\Delta(A\text{-ROI})
\]

and:

\[
\Delta(B\text{-ROI}) >
\Delta(\text{irrelevant ROI})
\]

The strongest result is a within-example A/B crossover.

---

## 4. Scope

Stage 2B does **not** test:

- why the switch happens,
- uncertainty as a LOOK trigger,
- visual-memory handoff,
- hidden/KV storage,
- re-grounding failures,
- benchmark-wide performance improvement.

Those belong to later stages.

---

## 5. Primary Intervention

Implement **region-specific visual access knockout**.

During a predefined generated reasoning window, prevent the current generated-token queries from attending to the visual-token positions corresponding to one ROI.

Conceptually:

\[
q_t \not\rightarrow K_{ROI}
\]

for:

\[
t \in [t_{start}, t_{end}]
\]

The intervention should change only the selected generated-query → visual-ROI attention edges.

Do not change:

- model weights,
- vision encoder output,
- non-target visual tokens,
- prompt tokens,
- previous reasoning tokens,
- MLPs,
- decoding configuration,
- image preprocessing.

For the initial pilot, apply the ROI mask across **all language-model layers** during the frozen reasoning window unless a technical limitation requires otherwise.

Document the exact implementation.

---

## 6. Required Conditions

For both the A-related window and B-related window, evaluate:

### C0 — Baseline
No intervention.

### C1 — Target-evidence ROI knockout
- A ROI in the A window
- B ROI in the B window

### C2 — Wrong-evidence ROI knockout
- B ROI in the A window
- A ROI in the B window

### C3 — Same-size irrelevant ROI knockout
Choose a region that:
- approximately matches the target ROI token count,
- does not overlap A or B,
- does not contain an obviously task-critical visual fact.

Freeze this irrelevant ROI before inspecting causal outputs.

### Optional C4 — Correct ROI at wrong timing
If cheap to implement:
- B ROI in a clearly earlier non-B window,
- or A ROI after its expected use.

Do not delay the core pilot for C4.

---

## 7. ROI-Size Control

ROI size is a major confound.

Record:

```text
ROI_A token count
ROI_B token count
irrelevant ROI token count
```

Use same-size or closely matched irrelevant controls.

If A and B differ substantially in size, do not interpret raw effect magnitude as pure evidence importance.

Prioritize:

> target ROI versus matched irrelevant ROI within the same reasoning window.

---

## 8. Intervention Smoke Test

Before running all five samples, validate the implementation on one example.

Verify:

1. baseline hooked inference reproduces the original baseline,
2. ROI token indices match frozen Stage 2A mappings,
3. only intended attention-mask entries are modified,
4. target masking does not remove all visual access,
5. wrong/irrelevant conditions preserve target-evidence access,
6. tensors remain finite,
7. KV-cache generation remains functional.

If baseline hooked inference is not faithful, stop and debug.

---

## 9. Local Causal Evaluation — Primary Metric

Local effects are the main Stage 2B measurement.

Use the clean reasoning trajectory and teacher forcing to evaluate the immediate continuation after intervention.

Do not use long-horizon teacher forcing as evidence of behavioral recovery because later clean CoT tokens may reintroduce visual facts.

### Evaluation horizon

Prefer:

> **the next semantic reasoning span**

If this is impractical, use one prospectively fixed token horizon, e.g.:

```text
next 16 tokens
```

or:

```text
next 32 tokens
```

Do not choose the horizon after seeing results.

### Metrics

Compute at least:

#### Clean-token NLL increase

\[
\Delta NLL
=
NLL_{\mathrm{intervention}}
-
NLL_{\mathrm{baseline}}
\]

#### Clean-token log-probability loss

\[
\Delta \log p
=
\log p_{\mathrm{baseline}}(y)
-
\log p_{\mathrm{intervention}}(y)
\]

Optionally add KL or Jensen-Shannon divergence between next-token distributions.

Interpretation:

> How much does removing this evidence disrupt the computation immediately following the intervention?

---

## 10. Free-Rollout Behavioral Evaluation

For each intervention condition:

1. keep the clean prefix up to the intervention point,
2. apply the intervention in the frozen window,
3. let the model freely continue generation afterward.

Use the locked Qwen Thinking generation protocol from Stage 1.

For stochastic generation:

- use fixed seeds,
- record seeds,
- match seeds across intervention conditions when possible.

Record:

```text
full continuation
final answer
correct / wrong
reasoning length
first meaningful semantic divergence
intermediate evidence statements if identifiable
```

Do not make prevalence claims from five examples.

---

## 11. Primary Analysis Table

For each example construct:

```text
                    A-window                B-window

Baseline            baseline                baseline

ROI_A knockout      ΔA_A                    ΔA_B

ROI_B knockout      ΔB_A                    ΔB_B

Irrelevant ROI      ΔI_A                    ΔI_B
```

The desired pattern is:

```text
A-window:
ROI_A >> ROI_B ≈ irrelevant

B-window:
ROI_B >> ROI_A ≈ irrelevant
```

This is the core evidence-specific temporal crossover.

---

## 12. Optional Crossover Score

For descriptive summarization only:

\[
C =
(\Delta_{A|Awin}-\Delta_{B|Awin})
+
(\Delta_{B|Bwin}-\Delta_{A|Bwin})
\]

Optionally normalize relative to irrelevant-ROI effects.

Do not overformalize this metric for a five-example pilot.

---

## 13. Per-Example Interpretation

Assign each example one category after all conditions are complete.

### P1 — Strong evidence-specific crossover
A dominates in A-window, B dominates in B-window, controls small.

### P2 — Partial evidence specificity
Only one window shows convincing evidence specificity.

### P3 — General visual fragility
Target, wrong, and irrelevant ROI knockout produce similar effects.

### P4 — Persistent evidence dependence
The same evidence remains causally important across both windows.

### P5 — No detectable ROI-level causal dependence
All ROI interventions have small effects.

### P6 — Uninterpretable
Technical or annotation issues prevent reliable interpretation.

Do not force the preferred P1 result.

---

## 14. GO / CONDITIONAL GO / NO-GO

### Strong GO
Recommend scaling to the full annotated Stage 2A set if:

- at least 3/5 examples show strong or reasonably clear evidence-specific crossover,
- target ROI effects exceed irrelevant controls,
- local causal effects are reproducible,
- intervention implementation is stable.

### Conditional GO
Recommend another small revised pilot if:

- ~2/5 show crossover,
- several show partial specificity,
- timing/window definition appears to matter,
- target effects still differ from irrelevant controls.

### NO-GO
Do not scale ROI knockout if:

- 0–1/5 show evidence-specific effects,
- target ROI is not stronger than irrelevant ROI,
- generic visual disruption or ROI size explains the effects,
- intervention cannot reproduce baseline faithfully,
- Stage 2A spatial attention patterns fail to predict causal effects.

A NO-GO is scientifically meaningful.

---

## 15. Important Negative Result

If Stage 2A showed:

```text
attention focus: A → B
```

but Stage 2B shows no A/B-specific causal dependence, treat that as a serious finding:

> **Spatial attention shifts are not sufficient evidence of evidence-specific visual usage in Thinking MLLMs.**

Do not hide or reinterpret this result.

---

## 16. Do Not Yet Test WHY

Do not yet test:

- uncertainty triggers,
- subgoal-trigger hypotheses,
- evidence availability manipulation,
- A→B versus B→A reasoning-order manipulation.

First establish whether a meaningful causal visual-use event exists.

---

## 17. Do Not Yet Test Handoff / Memory

Do not run:

- hidden-state injection,
- prompt-state patching,
- reasoning-state patching,
- KV-cache patching,
- visual-memory horizon experiments.

These require a validated causal visual-use event first.

---

## 18. Output Structure

Create:

```text
outputs/
  stage2b/
    config/
      intervention_config.json
      pilot_manifest.jsonl

    smoke/
      intervention_validation.md
      intervention_validation.json

    examples/
      699/
      739/
      2799/
      3044/
      3764/

    summaries/
      local_effects.json
      behavioral_effects.json
      crossover_summary.json
      stage2b_summary.md
      stage2b_acceptance.json
      next_stage_recommendation.md
```

Do not overwrite Stage 1 or Stage 2A.

---

## 19. Per-Example Artifacts

For each example save:

```text
annotation_snapshot.json
roi_mapping_snapshot.json

conditions/
  baseline/
  A_roi_Awindow/
  B_roi_Awindow/
  irrelevant_roi_Awindow/
  A_roi_Bwindow/
  B_roi_Bwindow/
  irrelevant_roi_Bwindow/

local_effects.json
behavioral_effects.json
crossover_table.json
interpretation.md
```

Add wrong-timing conditions only if they are actually run.

---

## 20. `stage2b_summary.md`

Include:

1. intervention implementation,
2. exact pilot sample list,
3. frozen ROI/window definitions,
4. smoke validation,
5. local teacher-forced results,
6. free-rollout results,
7. target/wrong/irrelevant controls,
8. per-example classifications,
9. crossover count,
10. technical limitations,
11. scientific interpretation,
12. project-level GO / CONDITIONAL GO / NO-GO.

Do not report dataset-wide prevalence from five samples.

---

## 21. `next_stage_recommendation.md`

Recommend exactly one next action:

### Option A
Scale evidence-specific causal analysis to the remaining annotated examples.

### Option B
Refine timing/ROI intervention and repeat a small pilot.

### Option C
Abandon attention-guided ROI causality as the main route and redesign the measurement strategy.

Do not automatically start the recommendation.

---

## 22. Technical Acceptance Criteria

Stage 2B technically passes only if:

1. all five frozen pilot examples are attempted,
2. baseline hooked inference is validated,
3. target ROI masking is correctly implemented,
4. wrong-evidence controls are implemented,
5. same-size irrelevant controls are implemented,
6. A/B windows remain frozen from Stage 2A,
7. local teacher-forced metrics are produced,
8. free-rollout behavioral outputs are produced,
9. Stage 2A annotations are not modified after outcomes are seen,
10. every example receives an interpretation category,
11. a project-level GO / CONDITIONAL GO / NO-GO is written,
12. no WHY or memory stage is started automatically.

Technical PASS does not require a positive scientific result.

---

## 23. Stop Condition

After the five-example pilot and all reports are complete:

> **STOP.**

Do not expand to the remaining 15 annotated examples automatically.

Do not start WHY experiments.

Do not start handoff / memory experiments.

Wait for review of Stage 2B results.
