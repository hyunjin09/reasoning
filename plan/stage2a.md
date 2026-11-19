You are continuing the **Visual–Reasoning Dynamics in Thinking MLLMs** project.

Your task is to execute **Stage 2A: Paired Descriptive Analysis and Evidence-ROI Discovery**.

This stage uses **only existing Stage 1 artifacts**.

> **Do not run any new model inference in Stage 2A.**

Do not perform causal knockout, counterfactual image generation, activation patching, KV-cache intervention, attention manipulation, re-grounding, or any performance-improving method.

The purpose of Stage 2A is to use the already-expensive Stage 1 dataset to determine **where the first causal experiments should be performed**.

---

# 0. Read Project State First

Before doing anything, read the relevant project documents and Stage 1 artifacts.

At minimum inspect:

```text
overview.md

outputs/stage1/summaries/stage1_summary.md
outputs/stage1/summaries/stage1_statistics.json
outputs/stage1/summaries/candidate_hypotheses.md

outputs/stage1/discovery/cohort_manifest.jsonl
outputs/stage1/discovery/raw_outcome_manifest.jsonl

outputs/stage1/discovery/paired_variants/pairing_manifest.jsonl
outputs/stage1/discovery/paired_variants/pairing_report.md

Stage 1 artifact inventory / attention-storage report
```

Also inspect the existing per-example bundles.

Do not overwrite historical Stage 0 or Stage 1 results.

---

# 1. Current Scientific Context

The broader project asks:

> **When does a Thinking MLLM rely on fresh visual evidence versus accumulated reasoning context, what drives those transitions, how is acquired evidence carried forward, and how do these dynamics fail?**

Stage 1 established descriptive temporal attention dynamics but did **not** establish causal visual usage.

Important Stage 1 findings include:

* visual attention is broadly modulated over long reasoning trajectories,
* average behavior is somewhat early-heavy,
* trajectories are heterogeneous,
* candidate visual-attention peaks do not map trivially onto semantic stages,
* entropy does not simply increase at candidate visual peaks,
* raw attention therefore cannot be treated as a causal LOOK signal.

The next question is:

> **Can we identify clean, evidence-specific temporal patterns in the existing data that justify targeted causal intervention?**

---

# 2. Existing Stage 1 Dataset

The canonical Stage 1B discovery set contains:

```text
100 unique underlying MathVerse problems
×
2 variants
=
200 examples
```

The paired variants are:

```text
Vision Intensive
Vision Dominant
```

Outcome composition:

```text
36 pairs: correct / correct
6 pairs:  correct / wrong
4 pairs:  wrong / correct
52 pairs: wrong / wrong
2 pairs:  wrong / truncated
```

Therefore:

```text
82 completed-correct trajectories
116 completed-wrong trajectories
2 truncated trajectories
```

The primary paired descriptive analysis in Stage 2A should begin with the:

> **36 both-correct pairs = 72 trajectories**

because both variants successfully solve the same underlying problem.

---

# 3. Existing Attention Artifacts

For all 200 canonical Stage 1B examples, the following useful attention information already exists.

Token-level:

```text
modality_by_layer: [T, 36, 3]
modality_density_by_layer: [T, 36, 3]

selected_head_mass: [T, 4, 32, 3]

visual_focus: [T, V]
```

Span-level:

```text
modality_mass_by_span_layer: [S, 36, 3]
modality_density_by_span_layer: [S, 36, 3]

visual_focus_distribution: [S, V]

uncertainty_by_span
```

Where the source modalities are:

```text
visual
prompt
reasoning
```

Important limitations:

* `visual_focus` is layer/head aggregated,
* no per-layer spatial visual distribution is retained,
* no per-head spatial visual distribution is retained,
* no individual prompt-token attention,
* no individual previous-reasoning-token attention,
* no hidden states,
* no KV cache,
* no full attention matrices.

Stage 2A must respect these limitations.

---

# 4. Stage 2A Goals

Stage 2A has three main goals.

## Goal A — Understand the VI/VD pairing

Verify exactly what differs between the Vision Intensive and Vision Dominant members of a pair.

## Goal B — Paired descriptive analysis

Ask whether the same successfully solved underlying problem exhibits systematically different visual/reasoning dynamics under the two modality variants.

## Goal C — Build a clean evidence-specific subset

Identify examples with at least two distinguishable visual evidence items, annotate their ROIs and reasoning stages, and use existing `visual_focus` arrays to determine whether evidence-specific temporal focus patterns are observable.

The output should directly determine whether Stage 2B causal evidence-specific intervention is justified.

---

# 5. Stage 2A.1 — Manual Audit of VI/VD Pairs

Before any large paired analysis, manually inspect at least:

> **10 randomly selected both-correct VI/VD pairs**

For each pair inspect:

* question text,
* image,
* answer,
* variant metadata,
* visual information present in each image,
* whether textual information differs,
* whether evidence has been moved between text/image,
* whether the underlying mathematical reasoning is truly matched.

Create:

```text
outputs/stage2a/manual_pair_audit.md
```

For each audited pair record:

```text
base_problem_id

Vision Intensive:
  example_id
  question
  image description
  visually available facts

Vision Dominant:
  example_id
  question
  image description
  visually available facts

same question text?
same answer?
same underlying reasoning?
what exactly differs?
is a paired visual-reliance comparison scientifically interpretable?
```

Do not assume the dataset label alone tells us the exact modality manipulation.

---

# 6. Pair Audit Gate

After auditing 10 pairs, answer:

> **Is Vision Intensive versus Vision Dominant a sufficiently interpretable paired manipulation for descriptive visual-dynamics comparison?**

If yes, continue.

If not, do not force the paired analysis.

Instead:

* explain the mismatch,
* identify which subset of pairs remains interpretable,
* continue only on the interpretable subset if sufficiently large.

Do not run new inference.

---

# 7. Stage 2A.2 — Both-Correct Paired Descriptive Analysis

Primary cohort:

```text
36 both-correct pairs
72 trajectories
```

The main question is:

> **For the same underlying problem solved correctly in both conditions, does the model allocate attention differently when the visual-information condition changes?**

Use paired statistics whenever possible.

Do not pool VI and VD as independent unrelated samples.

---

# 8. Signals to Compare

For each trajectory derive span-level and normalized-time summaries for:

## Visual engagement

```text
visual attention total mass
visual attention per-token density
```

## Reasoning-side engagement

```text
previous reasoning attention total mass
previous reasoning attention density
```

## Prompt-side engagement

```text
prompt attention total mass
prompt attention density
```

## Visual-focus dynamics

```text
similarity to prefill focus
similarity to previous span
spatial entropy
top-k overlap
focus turnover
candidate peak count
candidate peak prominence
candidate peak timing
```

## Uncertainty

```text
entropy
top-1 probability
top1-top2 margin
```

---

# 9. Normalize Reasoning Time Carefully

VI and VD trajectories may have different lengths.

Do not compare token 1000 in one trace directly with token 1000 in another as the primary analysis.

Use at least two alignment views.

## A. Normalized reasoning progress

Map each trajectory onto:

```text
0% → 100%
```

of completed reasoning.

Use a fixed number of bins, for example:

```text
20 or 50 normalized bins
```

Document the interpolation/aggregation procedure.

## B. Semantic-span alignment

Compare coarse reasoning stages where possible, such as:

```text
VISUAL_READ
COMPUTE
RELATION_INFERENCE
VERIFY
PLAN
ANSWER_SELECTION
```

Do not claim that semantic labels are ground-truth cognitive states.

---

# 10. Core Paired Questions

Test descriptively whether Vision Dominant versus Vision Intensive differs in:

### Q1

Overall visual attention mass/density.

### Q2

Early / middle / late visual engagement.

Suggested coarse windows:

```text
0–25%
25–75%
75–100%
```

### Q3

Number of candidate visual-attention peaks.

### Q4

Late recurrent visual peaks.

### Q5

Visual-focus turnover / spatial shift.

### Q6

Reasoning-token attention density.

### Q7

Prompt attention density.

### Q8

Uncertainty trajectory.

### Q9

Reasoning length.

### Q10

Whether increased visual engagement is accompanied by reduced reasoning-side engagement, or whether both increase together.

This last question is relevant to the project's core idea of:

```text
fresh visual route
versus
accumulated reasoning route
```

but Stage 2A must remain descriptive.

---

# 11. Statistical Analysis

Because samples are paired by underlying problem, use paired analyses.

At minimum report:

```text
paired mean / median differences
bootstrap confidence intervals
paired effect sizes
```

Use an appropriate paired nonparametric test when distributions are highly non-normal.

Avoid running dozens of significance tests without correction or interpretation.

The important output is the **effect pattern and magnitude**, not p-value hunting.

---

# 12. Possible Outcomes

Remain open to all outcomes.

## Outcome A — Vision Dominant has systematically greater visual engagement

Potential interpretation:

> descriptive evidence that the model adapts visual reliance to modality availability.

Still not causal.

## Outcome B — Early visual behavior is similar, but Vision Dominant has more late/recurrent engagement

Potentially more interesting:

> the difference may emerge during reasoning rather than initial perception.

This would motivate later causal testing of fresh evidence demand.

## Outcome C — VI uses more prompt/reasoning attention while VD uses more visual attention

Potentially relevant to:

> adaptive allocation between visual and accumulated-context pathways.

Still descriptive.

## Outcome D — Almost no VI/VD difference

Also informative.

Possible explanations:

* raw attention poorly reflects visual necessity,
* both variants still require similar visual processing,
* the variant manipulation does not isolate the desired factor,
* model routing is insensitive to the manipulation.

This would strengthen the need for causal intervention or controlled data.

Do not force a positive conclusion.

---

# 13. Stage 2A.3 — Evidence/ROI Candidate Discovery

In parallel with the paired analysis, construct a small clean mechanistic subset.

Target:

> **20–30 examples**

Prefer completed-correct trajectories.

The examples should contain at least two visually distinguishable evidence items needed at different reasoning stages.

Example:

```text
Evidence A:
  semantic fact: AC = 3
  ROI: image coordinates / mapped visual tokens

Evidence B:
  semantic fact: BD is tangent to the circle
  ROI: image coordinates / mapped visual tokens
```

Good examples should satisfy as many of the following as possible:

1. at least two independent visual facts,
2. evidence A and B are spatially distinguishable,
3. evidence A and B are required at different reasoning stages,
4. ROI boundaries are reasonably unambiguous,
5. generated reasoning is interpretable,
6. no obvious text shortcut eliminates the need for the evidence,
7. visual-token mapping for both ROIs is reliable.

Do not require all 20–30 examples to show the expected temporal attention shift.

---

# 14. Annotation Schema

Create:

```text
outputs/stage2a/evidence_subset/evidence_annotations.jsonl
```

For each selected example record:

```text
example_id
base_problem_id
variant
correct

Evidence A:
  semantic_fact
  ROI_image_coordinates
  ROI_visual_token_indices
  expected_reasoning_stage

Evidence B:
  semantic_fact
  ROI_image_coordinates
  ROI_visual_token_indices
  expected_reasoning_stage

reasoning stages:
  span_ids
  semantic subgoal
  required evidence:
    A
    B
    A+B
    none

notes:
  ambiguity
  possible text shortcut
  annotation confidence
```

Do not infer required evidence purely from attention.

Use the problem structure and reasoning semantics.

---

# 15. ROI Mapping Validation

For each evidence ROI:

1. map image-space ROI to retained visual-token indices,
2. visualize the mapped ROI,
3. manually verify alignment.

Save a small visualization for each selected evidence ROI where practical.

Do not proceed with an example if ROI-to-token mapping is clearly wrong.

---

# 16. Evidence-Specific Descriptive Curves

Using the existing:

```text
visual_focus: [T, V]
visual_focus_distribution: [S, V]
```

compute for each evidence ROI:

```text
ROI_A_attention(t)
ROI_B_attention(t)
```

and span-level equivalents.

Use both:

### Raw ROI mass

[
A_{s,A}
=======

\sum_{v \in ROI_A} P^{vis}_s(v)
]

### ROI-size-normalized density

[
D_{s,A}
=======

\frac{A_{s,A}}{|ROI_A|}
]

and similarly for B.

Normalization matters because ROI sizes differ.

---

# 17. Desired Evidence-Specific Pattern

A particularly interesting descriptive pattern would be:

```text
early:
A high
B low

middle:
A lower
B low

late:
A low
B high
```

or:

[
A_{attention}:
HIGH \rightarrow LOW \rightarrow LOW
]

[
B_{attention}:
LOW \rightarrow LOW \rightarrow HIGH
]

But:

> **Do not select only examples that show this pattern.**

Report how often clean A/B examples show:

```text
expected A→B shift
persistent A
persistent B
simultaneous A/B
no clear ROI selectivity
unexpected reverse shift
```

This prevalence matters.

---

# 18. Relation to Semantic Evidence Demand

For the annotated subset, compare evidence-specific attention to the manually annotated reasoning stages.

Questions:

> Does A attention rise near stages requiring A?

> Does B attention rise near stages requiring B?

> Does attention remain high after evidence should already be available?

> Does a new evidence-demand stage coincide with a new ROI focus?

Again, this remains descriptive.

---

# 19. Candidate Intervention Windows

For each selected A/B example, identify candidate reasoning windows for a future Stage 2B causal experiment.

For example:

```text
A_acquisition_window
A_computation_window
B_acquisition_window
B_computation_window
```

Save token/span indices.

The purpose is to prevent Stage 2B from requiring an expensive blind sweep over all reasoning tokens.

Do not perform the intervention yet.

---

# 20. Stage 2A Go / No-Go Question

The main gate is:

> **Can the existing Stage 1 artifacts identify a sufficiently large set of clean examples where different visual evidence items are associated with distinct reasoning stages and interpretable temporal focus patterns?**

### Strong GO

Proceed toward Stage 2B if:

* at least ~20 clean A/B examples are identified,
* ROI mapping is reliable,
* evidence demand can be reasonably annotated,
* temporal ROI curves are interpretable,
* at least a meaningful subset exhibits stage/evidence-related focus changes.

### Conditional GO

Proceed with caution if:

* only 10–19 very clean examples exist,
* but the evidence-specific patterns are strong and consistent.

Document the reduced scale.

### NO-GO

Do not design ROI-specific causal intervention yet if:

* fewer than ~10 clean examples can be found,
* ROI mapping is unreliable,
* evidence identity cannot be separated,
* visual-focus curves are too diffuse/noisy,
* reasoning stages cannot be matched to evidence demand.

Instead recommend either:

* a small controlled evidence-switch dataset,
* a different MathVerse subset,
* or another causal question.

---

# 21. Scientific Boundaries

Stage 2A may say:

> Vision Dominant and Vision Intensive trajectories exhibit different descriptive visual dynamics.

> ROI A attention tends to precede ROI B attention in a subset of multi-evidence problems.

> Certain reasoning stages align with different visual regions.

Stage 2A must **not** say:

> Evidence A is causally required here.

> The model causally reacquires B here.

> The model LOOKs here.

> The model THINKs from stored memory here.

> Visual attention shift proves evidence acquisition.

> New evidence demand causes visual access.

These require Stage 2B or later.

---

# 22. Required Outputs

Create:

```text
outputs/stage2a/
```

Suggested structure:

```text
outputs/stage2a/
  manual_pair_audit.md

  paired_analysis/
    both_correct_pair_manifest.jsonl
    paired_statistics.json
    paired_analysis.md
    figures/

  evidence_subset/
    evidence_annotations.jsonl
    evidence_subset_report.md

    examples/
      <example_id>/
        roi_A.json
        roi_B.json
        roi_mapping.png
        evidence_timeline.png
        candidate_intervention_windows.json

  summaries/
    stage2a_summary.md
    stage2a_acceptance.json
    stage2b_recommendation.md
```

Do not modify original Stage 1 artifacts.

---

# 23. Required Report: `paired_analysis.md`

Include:

1. pair-audit result,
2. number of interpretable pairs,
3. both-correct paired cohort definition,
4. VI vs VD differences in:

   * visual attention,
   * reasoning attention,
   * prompt attention,
   * peak statistics,
   * focus turnover,
   * uncertainty,
   * reasoning length,
5. effect sizes / paired CIs,
6. representative pair examples,
7. null or contradictory findings,
8. limitations.

---

# 24. Required Report: `evidence_subset_report.md`

Include:

```text
number screened
number accepted
number rejected
rejection reasons

evidence types
ROI-size distribution
reasoning-stage distribution
annotation confidence

frequency of:
  A→B attention shift
  persistent A
  persistent B
  simultaneous A/B
  no clear selectivity
  other
```

Do not hide negative examples.

---

# 25. Required Report: `stage2b_recommendation.md`

Based only on Stage 2A results, recommend the most informative next causal experiment.

If evidence-specific ROI intervention is justified, specify:

```text
which examples
which evidence ROIs
which reasoning spans
what causal quantity should be measured
what matched controls are required
```

Likely controls include:

```text
target ROI knockout
same-size irrelevant ROI knockout
no intervention
possibly matched counterfactual evidence
```

But:

> **Do not execute Stage 2B.**

---

# 26. Acceptance Criteria

Stage 2A passes if:

1. at least 10 VI/VD pairs are manually audited,
2. the paired manipulation is documented and scientifically interpretable,
3. both-correct VI/VD paired descriptive analysis is completed,
4. paired statistics use within-problem comparisons,
5. reasoning length is handled through normalized progress and/or span alignment,
6. no raw attention result is called causal visual usage,
7. at least 20 clean A/B evidence examples are targeted,
8. ROI mappings are manually sanity-checked,
9. evidence-specific temporal curves are generated,
10. candidate intervention windows are identified,
11. a clear Stage 2B GO / CONDITIONAL GO / NO-GO recommendation is produced,
12. no new model inference is run.

If only 10–19 high-quality A/B examples are available, Stage 2A may pass conditionally if this is explicitly documented.

---

# 27. Stop Conditions

Stop and report rather than forcing the analysis if:

* VI/VD pairs are not interpretable as a meaningful paired manipulation,
* existing visual-token mapping is insufficient for ROI analysis,
* evidence A/B cannot be reliably identified,
* most visual attention is too spatially diffuse to support evidence-specific analysis,
* candidate ROI shifts appear to be artifacts of normalization or trajectory length,
* existing Stage 1 artifacts are inconsistent or incomplete.

Unexpected or null findings are valid results.

---

# 28. Final Deliverables

Before finishing, provide:

1. `manual_pair_audit.md`
2. paired both-correct VI/VD analysis
3. paired statistics and figures
4. 20–30 target A/B evidence examples if available
5. evidence/ROI annotations
6. evidence-specific temporal curves
7. candidate Stage 2B intervention windows
8. `stage2a_summary.md`
9. `stage2a_acceptance.json`
10. `stage2b_recommendation.md`
11. explicit `GO`, `CONDITIONAL GO`, or `NO-GO`

Then **STOP**.

Do not run any new inference and do not begin Stage 2B automatically.
