# Stage 2C Plan: Temporal and Measurement Audit

## 1. Objective

Stage 2C is a measurement-audit stage. It should not try to rescue the Stage 2A attention hypothesis or make a new causal claim.

Stages 2A and 2B showed:

- Stage 2A: some reasoning trajectories show descriptive alignment between the currently discussed evidence and its visual ROI.
- Stage 2B: blocking generated-query -> selected-ROI attention edges during the annotated reasoning windows usually did not damage local computation.
- Therefore, `high ROI attention` cannot currently be interpreted as `fresh evidence acquisition`.

Stage 2C should determine **what the existing attention signal actually means temporally** and prepare a cleaner causal experiment.

Target cohort: **50 completed-correct examples**.
Minimum valid cohort after screening: **40 examples**.

Do not start the next causal stage automatically.

---

## 2. Three Considerations That Must Guide the Audit

### C1. Timing / acquisition mismatch

If the model outputs:

`AB is 3`

then blocking the AB ROI during that span may already be too late. The model may have extracted `AB=3` during prefill or earlier reasoning.

Thus:

`ROI dispensable during mention != ROI unnecessary for acquisition`.

### C2. Semantic-alignment confound

A text state containing `AB` may naturally have high QK similarity with the visual AB region.

Likewise a token related to `car` may attend to the visual car region even if the information needed to generate `car` was acquired earlier.

Thus:

`high attention to matching ROI`

may reflect semantic alignment rather than fresh visual reading.

### C3. Information can move across carriers

In a Thinking MLLM, visual information may be available through at least:

- V: visual-token states,
- Q: prompt/question-token states,
- R: previous generated-reasoning states.

Possible paths include:

`V_A -> R_t`

`V_A -> Q -> R_t`

`V_A -> R_<t -> R_t`

Stage 2C will not prove these paths, but it must identify the temporal regions needed for a later carrier-tracing experiment.

---

## 3. Core Questions

Stage 2C should answer:

1. What exact next-token decision does each stored attention row correspond to?
2. When does a visual fact first become explicit in generated reasoning?
3. Does ROI attention rise before, during, or after that first explicit expression?
4. Does ROI attention rise again when the same entity/fact is mentioned later?
5. Were the Stage 2B intervention windows before acquisition candidates, or mostly after the evidence was already explicit?
6. Can we identify a large clean set of **pre-explicit-evidence** examples suitable for counterfactual visual-content experiments?

---

## 4. Cohort

Use approximately 50 completed-correct Stage 1B trajectories.

Prefer:

- all usable 20 Stage 2A annotated examples,
- plus about 30 additional completed-correct examples.

Selection must be performed **without inspecting ROI-attention patterns**.

For new examples, require at least one visual fact that:

- is reasonably localizable,
- is not already fully stated in the text prompt,
- is explicitly verbalized or clearly used in the generated reasoning,
- has a clear correct baseline trajectory,
- has reliable visual-token mapping.

A single clean evidence item is sufficient. Two evidence items are not required.

Keep an exclusion log.

---

## 5. Evidence Event Annotation

For each evidence item annotate:

### E0 — Entity onset

First generated token/span naming the relevant entity.

Example:

`AB`

### E1 — Fact completion

Earliest generated position where the full fact is explicitly recoverable from the CoT.

Example:

`AB is 3`

or:

`AB is perpendicular to CD`

### E2 — First downstream use

First later reasoning span that uses the fact to derive something new.

Example:

`Therefore AB^2 = 9`

Also record repeated later mentions of the entity or fact.

---

## 6. Temporal Regions

For each evidence item define:

- PRE: before E0/E1; fact not yet explicit in generated text.
- ENTITY: around E0.
- FACT: span where the full evidence becomes explicit by E1.
- POST: after E1.
- USE: around E2.

The **PRE-E1 region is primary** for future acquisition/handoff work.

Once E1 has occurred, the explicit CoT itself may already act as a textual memory of the visual fact.

---

## 7. Mandatory Attention-Indexing Audit

Before interpreting any timing result, inspect the Stage 1 instrumentation and determine exactly what each stored attention row means.

Resolve whether a row labeled with generated token `y_t` is the attention used to:

- predict `y_t`, or
- process `y_t` and predict `y_(t+1)`.

Create one hand-checked example containing:

- context tokens,
- query position,
- stored attention row,
- logits produced,
- next generated token.

If code/artifacts alone are insufficient, run only the smallest deterministic smoke test needed to resolve indexing.

Do not modify historical arrays; instead define a corrected canonical alignment for Stage 2C.

---

## 8. ROI Annotation and Mapping

For new examples:

1. annotate evidence ROI in image coordinates,
2. map it to retained visual-token indices,
3. save the mapping,
4. manually inspect an overlay.

Reuse frozen Stage 2A mappings unless there is a documented bug.

---

## 9. Event-Aligned Attention Analysis

For each evidence item compute ROI attention/density relative to:

- E0,
- E1,
- E2.

Use both token-level and span-level views where available.

Create event-centered windows around E0/E1, e.g. a prospectively fixed +/-64-token window or an equivalent span-based window.

Do not choose the window after seeing results.

Measure at least:

- mean PRE ROI attention,
- mean ENTITY ROI attention,
- mean FACT ROI attention,
- mean POST ROI attention,
- mean USE ROI attention,
- local ROI-attention maximum relative to E0,
- local maximum relative to E1,
- attention center-of-mass timing relative to E1.

Report distributions, not just means.

---

## 10. Timing Categories

Classify each evidence event descriptively:

### T1 — Pre-mention lead
ROI attention is clearly elevated before the evidence becomes explicit.

This is only an acquisition candidate.

### T2 — Mention-centered
Attention rises mainly around E0/E1.

Could reflect acquisition, semantic alignment, or both.

### T3 — Post-mention lag
Attention is strongest after the evidence is already explicit.

Poor evidence for initial acquisition.

### T4 — Repeated mention-locked
ROI attention rises again around later references to the same entity/fact.

Consistent with semantic alignment.

### T5 — Persistent
ROI attention stays elevated broadly.

### T6 — No clear temporal structure

Do not force expected categories.

---

## 11. Semantic-Alignment Audit

For evidence items with repeated later references, compare ROI attention around:

1. first entity mention,
2. first full fact expression,
3. later repeated entity mentions,
4. later repeated fact uses,
5. matched nearby spans without the relevant semantic reference.

Key question:

> Does the ROI become active because new evidence is being acquired, or because the generated text currently represents the same semantic entity/fact?

A pattern such as:

`PRE low -> first mention high -> later repeated mentions high`

would be consistent with semantic/text-vision alignment.

A pattern such as:

`PRE high -> first mention moderate -> later mentions low`

would be more compatible with an acquisition candidate.

Both remain descriptive.

---

## 12. Explicit Scratchpad Audit

For every fact, mark E1 precisely.

After E1, prior generated text may literally contain the visual fact.

Therefore all future claims must distinguish:

`pre-E1 latent period`

from:

`post-E1 explicit scratchpad period`.

Do not interpret post-E1 visual dispensability as evidence of latent handoff without additional intervention.

---

## 13. Re-Audit Stage 2B

For all five Stage 2B examples:

`699, 739, 2799, 3044, 3764`

and for every A/B intervention window, record:

- intervention start/end,
- E0,
- E1,
- E2,
- relation of intervention window to these events.

Classify each window as:

- PRE-E0,
- E0-to-E1,
- POST-E1 before use,
- USE,
- late POST.

If a Stage 2B window begins after E1, state explicitly:

> This tests direct visual re-access after the evidence was already explicit, not initial evidence acquisition.

Also audit any apparent labeling/timing inconsistencies, including cases where A/B naming does not match temporal order.

---

## 14. Reinterpret Stage 2A

Revisit the Stage 2A A/B attention-shift examples using E0/E1/E2.

For each apparent A->B shift ask:

- Did A attention rise before A became explicit?
- Did it peak only while A was being verbalized?
- Did B attention rise before B became explicit?
- Did later repeated mentions produce similar peaks?

Do not overwrite the original Stage 2A report. Produce a separate reinterpretation.

---

## 15. Candidate Pool for the Next Causal Stage

The main Stage 2C deliverable is a larger set of clean **pre-explicit-evidence** candidates.

A strong candidate should have:

1. a localized visual fact,
2. clear E0 and E1,
3. an evidence-neutral pre-E1 reasoning prefix,
4. no textual leakage of the fact before E1,
5. a plausible image-only counterfactual edit,
6. correct baseline reasoning,
7. reliable ROI mapping.

From the 40-50 valid examples, aim for at least **20 counterfactual-ready candidates** if possible.

Do not generate edited images yet.

---

## 16. Planned Direction After Stage 2C — Do Not Execute Yet

### Stage 3A — Counterfactual visual-content sensitivity

Use same text / same reasoning prefix but different visual evidence content.

Example:

`AB=3 <-> AB=5`

Ask whether changing only visual content changes **pre-mention** computation.

This should become the primary causal signal instead of raw attention.

### Stage 3B — Carrier tracing

Only on examples with clear counterfactual sensitivity, test where evidence is causally represented:

- V visual states,
- Q prompt/question states,
- R previous reasoning states.

Use carefully validated activation/KV patching or an equivalent causal method.

### Stage 3C — Cutoff / reveal timing

If carrier transfer is observed:

- cutoff: how long must evidence remain visually accessible?
- reveal: how late can evidence become accessible and still be used?

### Stage 4 — Multi-evidence refresh

Only after the single-evidence mechanism is established, return to A/B reasoning and test:

`Acquire A -> Carry A -> Acquire B -> Carry B`.

---

## 17. Required Outputs

Create:

```text
outputs/stage2c/
  cohort/
    cohort_manifest.jsonl
    exclusion_log.jsonl

  convention_audit/
    attention_indexing_audit.md
    attention_indexing_example.json

  annotations/
    evidence_event_annotations.jsonl
    repeated_mentions.jsonl
    roi_annotations.jsonl

  analysis/
    event_aligned_statistics.json
    timing_categories.jsonl
    repeated_mention_statistics.json
    figures/

  stage2ab_reaudit/
    stage2a_reinterpretation.md
    stage2b_window_timing_audit.md
    stage2b_window_timing.json

  candidates/
    counterfactual_ready_candidates.jsonl
    candidate_report.md

  summaries/
    stage2c_summary.md
    stage2c_acceptance.json
    next_stage_recommendation.md
```

Do not modify Stage 1, Stage 2A, or Stage 2B historical artifacts.

---

## 18. Required Figures

At minimum:

1. ROI attention aligned to E0,
2. ROI attention aligned to E1,
3. PRE / ENTITY / FACT / POST / USE comparison,
4. distribution of ROI peak timing relative to E1,
5. first-mention vs repeated-mention attention,
6. representative T1-T6 examples,
7. Stage 2B intervention windows relative to E0/E1/E2.

Avoid allowing a few extremely long trajectories to dominate averages.

---

## 19. Acceptance Criteria

Stage 2C passes if:

1. attention indexing is explicitly verified,
2. 50 examples are targeted,
3. at least 40 valid examples remain,
4. selection is attention-blind,
5. E0/E1/E2 annotations are completed,
6. new ROI mappings are manually checked,
7. PRE/ENTITY/FACT/POST/USE analysis is completed,
8. first vs repeated mention analysis is completed,
9. semantic alignment remains a competing hypothesis,
10. all five Stage 2B examples are temporally re-audited,
11. Stage 2A is reinterpreted under the new timing definitions,
12. at least a best-effort counterfactual-ready candidate pool is produced,
13. no large new causal experiment is run,
14. no carrier-patching experiment is started,
15. an explicit next-stage recommendation is written.

---

## 20. Decision

Choose one:

### GO — Counterfactual content sensitivity
Enough clean pre-E1 examples exist for Stage 3A.

### CONDITIONAL GO
The direction is valid but more curation/data is needed.

### REDESIGN
MathVerse trajectories cannot cleanly support pre-acquisition analysis; recommend a controlled benchmark instead.

---

## 21. Scientific Boundary

Stage 2C should distinguish, as far as possible descriptively:

`visual acquisition`

from:

`text-vision semantic alignment`

from:

`direct visual re-access after evidence is already available elsewhere`.

It should **not** claim that any of these mechanisms has been causally proven.

The next causal stage should be based on **visual-content sensitivity and carrier tracing**, not raw attention magnitude.

---

## 22. Stop Condition

After the audit, candidate pool, summary, and recommendation are complete:

**STOP.**

Do not generate counterfactual data automatically.
Do not begin carrier patching.
Do not begin cutoff/reveal experiments.

Return Stage 2C results for review so the next plan can be designed using the full accumulated evidence.
