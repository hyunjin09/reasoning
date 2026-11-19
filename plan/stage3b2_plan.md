# Stage 3B.2 Plan — Counterfactual Visual-Source Switching and Evidence-Retrieval Timing

## 0. Purpose

Stage 3B.2 follows the Stage 3B.1 finding of **persistent direct-vision dependence**.

Stage 3B.1 showed that removing all future visual access usually destroys most of the Stage 3A evidence-specific counterfactual effect, even when the cutoff happens immediately before explicit evidence verbalization.

However, that result alone does **not** prove that the model is actively retrieving the *specific target evidence* from vision at that time.

All-visual cutoff could also hurt because:

- generic visual context remains necessary,
- target information is distributed across many visual tokens,
- visual computation acts as a general stabilizing input,
- or removing all visual access creates a broad off-manifold perturbation.

Stage 3B.2 therefore asks:

> **If the accumulated reasoning state is held fixed but the visual source available to future reasoning is switched from the original image to its counterfactual version, does the upcoming evidence identity switch as well?**

Example:

```text
history up to tau:        original image, AB = 3
future visual source:     switched to counterfactual, AB = 5
non-visual history:       kept unchanged
```

If the model's upcoming evidence preference moves from `3` toward `5`, this is direct evidence that the model is still retrieving **evidence-specific visual content** through the future direct-vision pathway.

This stage is still about **WHEN**.

Do not yet perform Q/R carrier localization, layer localization, attention-vs-MLP analysis, head/path analysis, or multi-evidence A/B refresh analysis.

---

# 1. Scientific Handoff From Previous Stages

## Stage 2A–2C — Attention is not acquisition

The project initially found evidence-aligned visual attention during reasoning.

Stage 2C later showed:

- 58/70 evidence events were mention-centered;
- only 3/70 were pre-mention leads;
- later semantic references also reactivated matching ROIs.

Therefore:

> **high matching-ROI attention cannot by itself distinguish semantic/text–vision alignment from fresh visual retrieval.**

---

## Stage 3A — Visual content is strongly causal

Using 49 unique base problems and localized original/counterfactual visual facts:

- CE expected direction: 49/49;
- mean CE: 3.2256 nats/token;
- mean sham-controlled CE: 3.1864;
- mean sham shift: 0.0392.

Therefore:

> **localized visual content causally controls the upcoming evidence statement.**

But Stage 3A did not establish when the image is read.

---

## Stage 3B.0 — Small prefill visual residual in Q

Generation-start visual cutoff preserved only:

- 14.5% mean;
- 6.1% median

of the Stage 3A full-vision effect.

The surviving residual was transferred by post-image prefix states, and Q-only patching captured nearly all of that residual at the median.

Therefore:

> **prefill creates a real Q-side visual residual, but it explains only a small fraction of the full evidence-specific effect.**

---

## Stage 3B.1 — Persistent direct-vision dependence

Across the same 49 bases:

- 0/49 reached retention >= 0.80;
- only 6/49 reached retention >= 0.50;
- median retention at E0-1 was 0.1114;
- 43/49 were persistent direct-vision dependence.

Therefore:

> **future direct visual access generally remains causally important until immediately before explicit evidence mention.**

But Stage 3B.1 removed **all** visual access.

It did not distinguish:

\[
	ext{specific evidence retrieval}
\]

from:

\[
	ext{generic/distributed visual dependence}
\]

Stage 3B.2 addresses exactly this distinction.

---

# 2. Main Research Question

For a localized counterfactual pair:

\[
I_O:\ f_O
\]

\[
I_C:\ f_C
\]

example:

\[
AB=3 \leftrightarrow AB=5
\]

construct a reasoning history under one image condition up to checkpoint \(	au\).

Then keep all accumulated non-visual states fixed, but replace the **future visual K/V source** with the other image condition.

Question:

> **Does changing only the visual source available to future generated queries causally change the upcoming evidence preference?**

If yes, the future direct-vision pathway carries information about the **identity/content of the target visual evidence**, rather than being merely generic visual support.

---

# 3. Primary Cohort

Use the exact frozen cohort from Stages 3A–3B.1:

- 49 unique `base_problem_id`s;
- 45 localized numeric-label edits;
- 4 structural edits.

Primary statistical unit:

```text
base_problem_id
```

Attempt all 49.

No selection based on attention, Stage 3B.1 retention, or effect size.

---

# 4. New Event Definition — Discriminative Evidence Decision E_d

For each original/counterfactual evidence pair, define:

\[
E_d
=
	ext{the first generated-token decision whose correct identity differs between }f_O	ext{ and }f_C
\]

Example:

```text
Original fact:       "AB is 3"
Counterfactual fact: "AB is 5"

shared text:         "AB is "
first discriminative content:
                     3 vs 5
                     ^
                     E_d
```

For multi-token values or structural facts:

- define the earliest token position where the original and counterfactual fact continuations diverge;
- retain the complete divergent suffix for sequence-level scoring.

`E_d` is the primary timing anchor.

---

# 5. Mandatory Manual E_d Audit

For every base verify:

1. original fact continuation;
2. counterfactual fact continuation;
3. tokenization of both;
4. longest common prefix;
5. first divergent token;
6. mapping to the baseline reasoning/fact-verbalization context;
7. whether text before E_d contains either discriminative value/content;
8. whether the target decision is semantically meaningful.

Save:

```text
outputs/stage3b2/annotations/discriminative_event_annotations.jsonl
```

Freeze these annotations before causal scoring.

---

# 6. Core Mechanistic Intervention — Future Visual-Source Switching

Use cached K/V states from validated original and counterfactual runs.

For original-history recipient:

```text
before tau:
    non-visual history = original
    visual source      = original

from tau onward:
    non-visual history = KEEP ORIGINAL
    previous reasoning = KEEP ORIGINAL
    visual K/V source  = SWITCH TO COUNTERFACTUAL
```

This is:

\[
H_{O
ightarrow C}(	au)
\]

Perform reciprocal:

\[
H_{C
ightarrow O}(	au)
\]

where counterfactual history is kept but future visual K/V comes from the original image.

Bidirectional design is mandatory.

---

# 7. What Must Remain Fixed During a Switch

At switch time \(	au\), do **not** replace:

- question/prompt K/V;
- system/instruction K/V;
- previous reasoning-token K/V;
- generated token identities;
- reasoning prefix;
- non-visual cached states;
- model weights;
- decoding/scoring protocol.

Replace only:

\[
oxed{	ext{visual-token cached K/V used by future generated queries}}
\]

across all 36 language layers.

---

# 8. Why Source Switching Is Preferred Here

Stage 3B.1 asked:

```text
future V = unavailable
```

Stage 3B.2 asks:

```text
future V = available, but contains the opposite evidence identity
```

The model remains on a valid multimodal pathway.

Thus the experiment tests whether reasoning follows the **new visual evidence identity**, not merely whether removal of vision is damaging.

---

# 9. Primary Switch Checkpoints

Anchor timing to \(E_d\).

Primary checkpoints:

```text
E_d - 64
E_d - 32
E_d - 16
E_d - 8
E_d - 4
E_d - 2
E_d - 1
E_d
```

Definition:

- switch at query index `k` means the query that predicts generated token `y_k` and every later generated query sees the substituted visual source;
- `E_d` means the visual source is switched for the decision that predicts the first discriminative evidence token itself.

Also include generation start as a reference point.

---

# 10. Normalized-Progress Checkpoints

Also evaluate:

```text
0%
25%
50%
75%
90%
```

of the interval from reasoning start to \(E_d\).

Deduplicate exact indices.

Freeze all switch positions before cohort scoring.

---

# 11. Primary Evidence-Preference Readout

Reuse Stage 3A:

\[
D = L_O - L_C
\]

where larger \(D\) means preference for original evidence.

For original history:

\[
D_{OO}(	au)
=
D(	ext{original history, original future visual source})
\]

\[
D_{OC}(	au)
=
D(	ext{original history, counterfactual future visual source})
\]

Define:

\[
S_{O
ightarrow C}(	au)
=
D_{OO}(	au)-D_{OC}(	au)
\]

Positive means counterfactual future vision moves original history toward the counterfactual fact.

For counterfactual history:

\[
D_{CC}(	au)
=
D(	ext{counterfactual history, counterfactual future visual source})
\]

\[
D_{CO}(	au)
=
D(	ext{counterfactual history, original future visual source})
\]

Define:

\[
S_{C
ightarrow O}(	au)
=
D_{CO}(	au)-D_{CC}(	au)
\]

Positive means original future vision moves counterfactual history toward the original fact.

---

# 12. Bidirectional Visual Retrieval Index

Define:

\[
BRI(	au)
=
rac{
S_{O
ightarrow C}(	au)
+
S_{C
ightarrow O}(	au)
}{2}
\]

Use unnormalized BRI as primary.

A normalized secondary quantity may divide by the full original-vs-counterfactual evidence gap, but never clip values and do not emphasize unstable ratios.

---

# 13. Mandatory Controls

At every primary checkpoint include:

## C0 — No switch

```text
O history + O visual
C history + C visual
```

## C1 — Self replacement

Same visual K/V copied back into itself.

Should be transparent.

## C2 — O history + C visual

Primary O→C switch.

## C3 — C history + O visual

Reciprocal C→O switch.

## C4 — Sham source switch

At minimum:

```text
O history + sham visual
```

Original and sham have the same semantic fact, so this should cause a much smaller evidence-specific shift than O↔C switching.

---

# 14. Technical Smoke Validation

Use 3 numeric-label bases.

Verify:

1. O+O and C+C reproduce validated no-switch scoring;
2. self visual-K/V replacement is transparent;
3. O+Sham has negligible evidence-specific shift;
4. source visual-token counts/positions match;
5. text token positions match;
6. post-RoPE K/V tensor shapes and GQA cache layout are verified;
7. only visual-position K/V is replaced;
8. Q/P/R cache entries remain unchanged;
9. switching starts at the intended query index;
10. no query before tau uses the substitute;
11. all queries from tau onward use the substitute;
12. deterministic scoring is reproduced;
13. no NaNs/infs occur.

Stop if smoke fails.

---

# 15. Primary Analysis A — Does Late Visual Identity Control the Fact?

For each checkpoint report:

- N;
- mean/median O→C switch effect;
- mean/median C→O switch effect;
- mean/median BRI;
- bootstrap CI over base problems;
- source-consistent proportion in each direction;
- bidirectionally source-consistent proportion;
- sham-switch effect.

Central question:

> **Does future visual-source identity continue to control the upcoming evidence very close to E_d?**

---

# 16. Primary Analysis B — Retrieval-Timing Curves

Construct:

\[
BRI_i(	au)
\]

for every problem.

Aggregate in:

- tokens relative to E_d;
- normalized progress to E_d.

Descriptive categories:

### R1 — Persistent late retrieval
Strong source control at E_d-1 or E_d.

### R2 — Early retrieval / commitment
Switching works earlier but loses effect before E_d.

### R3 — Gradual source influence
Effect changes progressively.

### R4 — Weak identity-specific retrieval
All-V cutoff matters, but source switching has little evidence-specific effect.

### R5 — Complex / non-monotonic

Do not filter categories.

---

# 17. Primary Analysis C — Source Switching vs Stage 3B.1 Cutoff

At exact matching timings compare:

\[
	ext{Stage 3B.1 cutoff damage}
\]

with:

\[
	ext{Stage 3B.2 source-switch effect}
\]

Interpretation:

## High cutoff damage + high switch effect
Direct vision carries the **specific evidence identity**.

## High cutoff damage + low switch effect
Direct vision matters, but current evidence does not show target-fact retrieval; generic/distributed visual support remains possible.

## Low cutoff damage + low switch effect
Future visual access is largely dispensable.

## Low cutoff damage + high switch effect
Potential override/sensitivity phenomenon; inspect carefully.

Create a per-problem quadrant analysis.

---

# 18. Strongest Desired Finding

The strongest result would be:

> **Even when the accumulated reasoning state was built under the original image, switching only the future visual K/V source to the counterfactual image immediately before the discriminative evidence decision shifts the model toward the counterfactual fact.**

That would support:

\[
oxed{
	ext{Thinking MLLMs actively retrieve evidence-specific visual content during reasoning}
}
\]

rather than merely relying on generic persistent visual context.

---

# 19. Sham-Control Requirement

The above claim requires:

\[
|S_{O
ightarrow Sham}|
\ll
|S_{O
ightarrow C}|
\]

and negligible self-switch effects.

If sham switching is comparable, stop and redesign.

---

# 20. Secondary Free-Rollout Validation

Teacher-forced evidence preference is primary.

For selected checkpoints:

```text
E_d - 16
E_d - 4
E_d
```

where available, run matched-seed short rollouts after source switching.

Conditions:

- O history + O future vision
- O history + C future vision
- O history + sham future vision
- reciprocal C history + O future vision

Record:

- first discriminative fact;
- source-consistent classification;
- first semantic divergence;
- whether accumulated old evidence is overridden.

Behavioral validation only.

---

# 21. Attention Is Secondary Only

Do not use attention to select examples or switching times.

After causal results are frozen, compare source-switch sensitivity with Stage 2C attention for exact matching events.

Questions:

- does attention peak coincide with strong source control?
- can mention-centered attention occur with weak source control?
- can source control remain high without high ROI attention?

This helps separate semantic alignment from causal retrieval.

---

# 22. What Stage 3B.2 May Establish

If supported:

> **Future visual-source identity causally controls upcoming evidence even after a long reasoning history has accumulated.**

If late effects remain:

> **Thinking MLLMs actively retrieve evidence-specific visual content immediately before or during evidence verbalization.**

Combined with Stage 2C:

> **Mention-centered visual attention cannot be interpreted from attention alone; it may mix semantic alignment with genuine causal retrieval.**

---

# 23. What Stage 3B.2 Cannot Establish

Do not claim:

- which ROI tokens carry the effect;
- which layers perform retrieval;
- whether Q or R stores the retrieved evidence;
- attention vs MLP mechanism;
- responsible heads/circuits;
- persistence after verbalization;
- multi-evidence A/B episodes;
- LOOK/THINK states.

---

# 24. Decision After Stage 3B.2

## GO — Layer-wise visual-to-reasoning transfer analysis

Use if:

- O↔C switching robustly transfers evidence identity;
- bidirectional source consistency is strong;
- effect exceeds sham switching;
- substantial late pre-E_d source control remains.

Next question:

> **At which layers does the current reasoning state receive the evidence-specific visual content?**

---

## GO — Earlier commitment / non-visual carrier analysis

Use if switching works early but loses effect well before E_d despite later cutoff dependence.

This would imply a distinction between evidence commitment and generic visual support.

---

## REDIRECT — Generic/distributed visual dependence

Use if:

- all-V cutoff remains strongly damaging;
- but O↔C source switching gives little evidence-specific shift;
- or sham switching is comparable.

Then investigate distributed/global visual representations rather than specific evidence retrieval.

---

# 25. Output Structure

Create:

```text
outputs/stage3b2/
  config/
    stage3b2_config.json
    cohort_manifest.jsonl
    switch_checkpoint_schedule.jsonl

  annotations/
    discriminative_event_annotations.jsonl
    annotation_audit.md

  smoke/
    visual_source_switch_validation.md
    visual_source_switch_validation.json
    cache_integrity_diagnostics.json

  scoring/
    per_problem_switch_results.jsonl
    per_checkpoint_statistics.json
    rollout_results.jsonl

  analysis/
    retrieval_timing_curves.json
    bidirectional_retrieval_statistics.json
    cutoff_vs_switch_comparison.json
    evidence_type_analysis.json
    attention_secondary_comparison.json
    figures/

  summaries/
    stage3b2_summary.md
    stage3b2_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite earlier artifacts.

---

# 26. Required Figures

At minimum:

1. O→C and C→O switch effect vs E_d-relative time;
2. cohort BRI vs E_d-relative time;
3. BRI vs normalized reasoning progress;
4. per-problem retrieval-timing curves;
5. O→C effect vs sham effect;
6. Stage 3B.1 cutoff damage vs Stage 3B.2 switch effect;
7. R1–R5 timing-category examples;
8. numeric vs structural strata;
9. representative original-history → counterfactual-vision fact flips.

---

# 27. Acceptance Criteria

Stage 3B.2 technically passes if:

1. all 49 frozen bases are attempted;
2. E_d is frozen before causal scoring;
3. original/counterfactual tokenization is audited;
4. switch checkpoints are frozen before cohort scoring;
5. visual K/V replacement is validated across all layers;
6. non-visual Q/P/R cache is unchanged during switching;
7. O→C and C→O are both run;
8. self-switch controls are transparent;
9. sham-source controls are implemented;
10. evidence-specific switch effects are computed;
11. bidirectional statistics are reported;
12. Stage 3B.1 cutoff effects are compared at matching timings;
13. base_problem_id is the statistical unit;
14. attention is secondary only;
15. no layer/Q/R/module/head/path localization is started;
16. an explicit next-stage decision is written.

Technical PASS does not require a positive retrieval result.

---

# 28. Stop Condition

After:

- discriminative-event annotation,
- smoke validation,
- full 49-base source-switch timing experiment,
- bidirectional causal analysis,
- cutoff-vs-switch comparison,
- sham controls,
- secondary attention comparison,
- final recommendation,

**STOP.**

Do not start:

- layer-wise visual-to-reasoning localization;
- Q/R carrier patching;
- ROI-specific K/V switching;
- attention-vs-MLP analysis;
- head/path patching;
- multi-evidence A/B refresh;
- correct-vs-wrong failure analysis.

Return the complete Stage 3B.2 results for review.

The next stage must be designed only after jointly considering Stage 3B.2 with all prior Stage 2A–3B.1 findings.
