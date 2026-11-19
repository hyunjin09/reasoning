# Stage 8B — Retrieval-Aligned Success/Failure Divergence on MathVision

## 0. One-line objective

Use the **frozen Stage 8A active-retrieval detector** to align reasoning trajectories at moments of visual retrieval, then determine **where successful and failed reasoning first diverge** in Qwen3-VL-2B-Thinking.

The central question is:

\[
oxed{
	extbf{When visual retrieval is active, what computational property distinguishes successful from failed reasoning?}
}
\]

This stage is **diagnostic, not intervention-first**.  
The intervention direction should be chosen only after the divergence point is identified.

## 1. Why this experiment is necessary for the paper

Stage 8A established an important new capability:

\[
oxed{
	ext{active visual retrieval is passively observable online}
}
\]

using a frozen QK/attention-side retrieval proxy on Qwen3-VL-2B-Thinking.

However, Stage 8A did **not** identify a sufficiently large and generalizable "weak transport" cohort that would justify selective Value reinjection.

Therefore the next high-value question is not:

> Can we force more visual Value into the model?

but:

> **Once retrieval is active, where do successful and failed reasoning trajectories actually diverge?**

This connects our mechanistic work to prior trajectory-level observations such as **Real-Time Visual Attribution Streaming in Thinking Model (vSTREAM)**, which reports that successful and failed reasoning exhibit different visual-attribution trajectories.

Our intended contribution is not to reproduce the claim that trajectories differ.

Instead, we ask:

\[
oxed{
	extbf{Can those success/failure trajectory differences be localized to a specific stage of the causal visual-retrieval lifecycle?}
}
\]

The lifecycle to test is:

\[
	ext{reasoning context}
ightarrow
	ext{retrieval activation}
ightarrow
	ext{source routing}
ightarrow
	ext{Value-rich transport}
ightarrow
	ext{local visual evidence}
ightarrow
	ext{downstream reasoning}
\]

## 2. Paper claim if successful

The strongest desired claim is:

> **Successful and failed multimodal reasoning do not merely differ globally in trajectory shape; they diverge at identifiable stages of the visual-retrieval computation.**

A more specific claim should be made only if supported by the data.

Possible outcomes include:

- **Retrieval activation failure:** failed trajectories under-activate visual retrieval at points where successful trajectories reliably re-engage vision.
- **Routing-quality failure:** correct and incorrect trajectories activate retrieval similarly, but failed visual reads show weaker target-specific routing at retrieval onset.
- **Transport/influence failure:** retrieval activation and routing are comparable, but visual evidence exerts weaker causal influence in failed local reads.
- **Downstream failure:** many wrong final answers exhibit retrieval dynamics and local visual reads comparable to successful trajectories, with divergence occurring only after visual evidence has entered the reasoning state.
- **Re-retrieval instability:** failed trajectories exhibit repeated or unstable retrieval after an initially unsuccessful visual read, mechanistically linking local retrieval failure to trajectory wandering.

The stage must **not choose one of these claims in advance**.

## 3. What a null does NOT rule out

A null difference between final-correct and final-wrong trajectories does **not** imply that visual retrieval is irrelevant to failure.

Possible reasons include:

- final-answer errors occur downstream of otherwise normal retrieval;
- correct and wrong trajectories differ only for a specific failure subtype;
- cross-item difficulty confounds broad comparisons;
- retrieval divergence exists only within same-item stochastic pairs;
- divergence is source-specific and diluted by global visual features;
- the passive retrieval detector marks event onset but not the causal sub-process that fails;
- failure may occur after retrieval in binding, extraction, arithmetic, or integration.

Therefore the analysis must proceed from broad outcome labels to **local visual-read labels** and **within-item matched pairs**.

## 4. Competing mechanisms to distinguish

### H1 — No-retrieval failure

Wrong trajectories fail because visual retrieval is not activated when needed.

Predictions:
- fewer retrieval events,
- delayed first retrieval,
- lower retrieval probability at annotated visual-demand points,
- lower event-aligned QK/attention engagement.

### H2 — Routing-quality failure

Wrong trajectories activate retrieval but address the wrong or less task-relevant visual source.

Prediction:

\[
R_{	ext{correct}}
pprox
R_{	ext{wrong}}
\]

but:

\[
	ext{target-vs-distractor routing margin}_{	ext{correct}}
>
	ext{target-vs-distractor routing margin}_{	ext{wrong}}.
\]

### H3 — Visual-influence failure

Retrieval and routing occur, but the retrieved visual evidence has weaker causal influence on the local prediction.

Predictions:
- similar retrieval proxy,
- similar target routing,
- lower visual-off / source-switch causal effect in failed local reads.

### H4 — Correct retrieval, downstream reasoning failure

Wrong final answers are often preceded by locally correct, causally grounded visual reads.

Predictions:
- local retrieval dynamics similar to final-correct trajectories,
- local visual claim correct,
- divergence emerges later during calculation/integration/reasoning.

### H5 — Retrieval instability / repeated re-query failure

Failed trajectories show unstable or repeated retrieval after an unsuccessful visual read.

Predictions:
- more retrieval events after the first required visual read,
- shorter inter-retrieval intervals,
- more source switching or retrieval recurrence,
- larger trajectory path length/tortuosity,
- repeated retrieval concentrated after locally wrong or unresolved visual claims.

This is the most direct mechanistic bridge to vSTREAM-style trajectory differences.

## 5. Model

**Qwen3-VL-2B-Thinking**

Use the same validated execution path and decoding protocol as Stage 8A.

Recommended generation protocol:
- BF16
- temperature 0.6
- top-p 0.95
- top-k 20
- multiple seeds for paired-rollout stage
- EOS normal stopping
- `max_new_tokens = 40960`

Do not alter the Stage 8A retrieval detector during this stage.

## 6. Primary benchmark selection

### Primary benchmark: MathVision

MathVision is preferred because:
- Qwen3-VL-2B-Thinking is imperfect enough to produce substantial correct and wrong cohorts;
- many items require nontrivial diagram-grounded mathematical reasoning;
- visual evidence is often localizable;
- intermediate visual claims can frequently be annotated;
- it is harder than the MathVerse cohort used for much of the original mechanism discovery.

Do not assume official-report accuracy under our exact decoding protocol.

First run a **native outcome census** under the frozen protocol.

## 7. Stage structure

This stage has four parts:

1. **8B.0 — Native MathVision census**
2. **8B.1 — Large correct/wrong trajectory comparison**
3. **8B.2 — Retrieval-event-aligned mechanistic comparison**
4. **8B.3 — Same-item correct/wrong paired-rollout confirmation**

A small causal subset follows only after the passive analysis identifies candidate divergence points.

## 8. Stage 8B.0 — Native MathVision census

### Goal

Measure the actual correct/wrong yield of Qwen3-VL-2B-Thinking under our exact inference protocol.

### Procedure

Run the full benchmark if feasible.

For every item record:
- final answer,
- benchmark correctness,
- generation length,
- stop reason,
- reasoning trace,
- Stage 8A retrieval-proxy time series,
- retrieval-event timestamps using the frozen threshold.

### Initial target cohort

Do **not** force exactly 500/500.

Preferred passive-analysis target:
- at least **300 final-correct trajectories**
- at least **300 final-wrong trajectories**

If the full benchmark naturally yields more, preserve all trajectories and create a balanced matched analysis cohort.

If one class has fewer than 250 usable examples, continue with all available examples but report the limitation.

## 9. Matching for the broad correct/wrong cohort

A raw correct-vs-wrong comparison is heavily confounded by item difficulty.

Construct a matched analysis cohort using available item metadata and trajectory properties.

Match or stratify by as many of the following as feasible:
- problem category,
- diagram/type category,
- answer format,
- number of visual entities,
- estimated visual clutter,
- reasoning length,
- question length,
- required number of visual reads,
- retrieval-event count,
- benchmark subcategory.

Outcome correctness must **not** be used to alter the frozen retrieval detector.

The broad comparison is descriptive and hypothesis-generating.

The strongest confirmation will come from same-item paired rollouts.

## 10. Stage 8B.1 — Whole-trajectory comparison

### Purpose

Replicate and extend the trajectory-level success/failure distinction before local mechanistic alignment.

This section should be explicitly framed as a **vSTREAM-adjacent baseline**, not the primary novelty.

## 11. Whole-trajectory measures

For each trajectory compute:

### Retrieval frequency

\[
N_R = \#\{t:R_t>	au_R\}
\]

and:

\[
	ext{retrieval density}
=
rac{N_R}{	ext{reasoning tokens}}.
\]

### First retrieval timing
- absolute token index,
- normalized reasoning fraction.

### Inter-retrieval interval

\[
\Delta t_i = t_{i+1}-t_i.
\]

### Retrieval burstiness
Measure clustering of retrieval events over reasoning time.

### Retrieval recurrence
Number of repeated retrieval episodes after an earlier visual-read event.

### QK/attention trajectory movement
Construct event-level or step-level passive retrieval-feature vectors and measure:
- path length,
- displacement,
- tortuosity,
- local curvature,
- recurrence.

### Source/ROI trajectory movement
For localizable items, measure visual-source distribution movement across reasoning.

### Late-reasoning retrieval
Fraction of retrieval events after 50%, 70%, and 85% of reasoning completion.

## 12. Whole-trajectory questions

Test whether wrong trajectories show:
- more retrieval,
- less retrieval,
- later retrieval,
- more repeated retrieval,
- more unstable source allocation,
- larger path length,
- larger tortuosity.

These are secondary descriptive results.

A significant difference here is **not sufficient** for the main claim.

## 13. Stage 8B.2 — Retrieval-event-aligned mechanistic comparison

### Core idea

Use the frozen Stage 8A detector to define:

\[
t=0
\equiv
	ext{active retrieval event}.
\]

Align correct and wrong trajectories around these events.

Analyze:

\[
[t-k,\ldots,t,\ldots,t+k]
\]

for a fixed preregistered local window.

Suggested initial window:

\[
k=8
\]

tokens, with \(k=4\) and \(k=16\) as secondary robustness checks.

## 14. Event types

Separate retrieval events into:

### T — task-required visual retrieval
The next reasoning step genuinely requires visual information.

### M — mention-only
A visual entity is mentioned but reacquisition is not required.

### U — unclassified active retrieval
The frozen Stage 8A detector fires, but manual semantic annotation is unavailable or ambiguous.

Primary mechanistic comparisons should use **T events**.

U events can be used for whole-trajectory statistics.

## 15. Local visual-read correctness annotation

For every sufficiently localizable T event, annotate the immediate visual evidence used after retrieval.

Define:

### L+ — locally correct visual read
The model's local claim matches the relevant visual evidence.

### L− — locally incorrect visual read
The model emits an incorrect visual claim, relation, quantity, binding, or source-conditioned statement.

### L? — unresolved
The local claim cannot be certified.

This local label is critical.

Final correctness alone is not a valid label for retrieval quality.

## 16. Main 2 × 2 outcome structure

| Local visual read | Final answer | Interpretation |
|---|---|---|
| L+ | correct | successful retrieval + successful downstream reasoning |
| L− | wrong | visual-stage failure candidate |
| L+ | wrong | downstream reasoning/integration failure candidate |
| L− | correct | compensation/recovery candidate |

The primary retrieval-mechanism contrast is:

\[
oxed{
L+ 	ext{ vs } L-
}
\]

not merely final correct vs final wrong.

Final correctness remains a secondary axis.

## 17. Retrieval-stage feature hierarchy

### Level 1 — Retrieval activation

Use the frozen Stage 8A features:
- retrieval probability / score,
- visual attention mass,
- QK visual competitiveness,
- visual concentration,
- local temporal rise.

Question:

> Did the wrong trajectory fail to engage retrieval?

### Level 2 — Target/source routing

For localizable events compute:

\[
\Delta QK_{T-X}
=
QK_T-QK_X
\]

\[
\Delta A_{T-X}
=
A_T-A_X
\]

where \(T\) is the demanded region/source and \(X\) is the strongest plausible alternative or matched irrelevant source.

Also report:
- target rank among visual regions,
- target attention share,
- target-vs-rest margin,
- target-vs-nearest-confuser margin.

Question:

> Retrieval is active, but is the wrong visual source being addressed?

### Level 3 — Value transport

Compute:
- target \(lpha V\),
- visual \(lpha V\) norm,
- target-vs-distractor \(lpha V\) margin,
- post-\(W_O\) visual contribution,
- visual contribution / residual ratio,
- head cancellation/disagreement.

These are descriptive unless supported by causal tests.

Do not treat raw norm as causal grounding.

### Level 4 — Causal visual dependence

On a selected subset perform:
- visual-off intervention,
- target source suppression,
- target-vs-alternative source switch,
- semantic counterfactual Value intervention where appropriate,
- matched sham controls.

Measure \(G_t^{causal}\) using:
- full-span CE effect,
- next-token distribution change,
- target-vs-alternative preference shift,
- semantic followability.

Question:

> Does the actual visual source exert less or different causal control in failed local reads?

### Level 5 — Post-retrieval reasoning state

After the local visual read, examine:
- whether the retrieved evidence is preserved in local residual/KV state,
- whether the model re-queries vision immediately,
- whether the same evidence is revised,
- whether downstream arithmetic/integration departs despite a correct local read.

Question:

> Did failure occur after successful visual retrieval?

## 18. Primary event-level comparisons

### Comparison A — L+ vs L−
At active T retrieval events:

\[
	ext{local correct visual read}
\quad	ext{vs}\quad
	ext{local incorrect visual read}.
\]

This is the primary mechanistic contrast.

### Comparison B — Final-correct vs final-wrong among L+
This isolates downstream failure after successful visual read.

### Comparison C — Final-correct vs final-wrong overall
Use only as a broad descriptive comparison.

## 19. Stage 8B.3 — Same-item paired-rollout confirmation

### Why this is necessary

Cross-item correct/wrong comparison is confounded by:
- problem difficulty,
- image complexity,
- required reasoning depth,
- visibility,
- source ambiguity.

The strongest design is:

\[
oxed{
	ext{same image + same question + different stochastic outcome}
}
\]

## 20. Paired-rollout generation

For selected MathVision items, generate multiple independent rollouts using fixed protocol with multiple seeds.

Suggested initial design:
- 4–8 seeds per item,
- preserve all generations,
- identify items with at least:
  - one correct rollout,
  - one wrong rollout.

Prefer items with at least one localizable T retrieval event in both outcomes.

## 21. Paired cohort target

Target:
- **at least 64 same-item correct/wrong pairs**
- from **at least 48 unique MathVision items**

Stretch target:
- 96–128 pairs.

If 64 pairs cannot be obtained without excessive compute, stop and report the achievable paired yield rather than changing the pairing definition.

## 22. Semantic event matching within paired rollouts

Within each same-item pair:

1. Identify the same required visual subgoal.
2. Match the corresponding retrieval event in correct and wrong trajectories.
3. Align at active retrieval onset.
4. Compare the retrieval lifecycle stage-by-stage.

Do not pair arbitrary retrieval events merely because they occur at similar normalized reasoning time.

Semantic subgoal matching is required.

## 23. Paired mechanistic question

For each pair, determine the **first stage at which the two trajectories diverge**:

1. retrieval activation,
2. source routing,
3. Value transport,
4. causal visual influence,
5. local visual evidence emission,
6. downstream integration.

This produces a mechanistic divergence label per pair.

## 24. Failure-location taxonomy

Use the following taxonomy only when evidence supports it.

### F0 — No retrieval activation
Required visual retrieval does not activate.

### F1 — Misrouting
Retrieval activates but target source selectivity is impaired.

### F2 — Source-coupled extraction/content error
Target source is causally used but local visual content is wrong.

### F3 — Weak/altered causal influence
Routing is similar but visual evidence has reduced or qualitatively different causal effect.

### F4 — Correct local retrieval, downstream integration failure
Local visual evidence is correct and grounded; later reasoning fails.

### F5 — Retrieval instability / repeated unsuccessful re-query
Repeated retrieval or switching follows an unresolved/incorrect local read.

### FU — unresolved
The first divergence cannot be certified.

Do not force every wrong trajectory into a mechanistic class.

## 25. vSTREAM-style trajectory analysis as a bridge, not the endpoint

Reproduce analogous trajectory descriptors where feasible:
- path length,
- tortuosity,
- source movement,
- recurrence.

Then condition these metrics on our mechanistic labels.

The important question is not only:

\[
	ext{wrong trajectory is more tortuous?}
\]

but:

\[
oxed{
	ext{Which retrieval failure state explains the increased tortuosity?}
}
\]

Examples:
- Does F1 misrouting precede repeated visual switching?
- Does F5 repeated retrieval account for most high-tortuosity failures?
- Are F4 downstream failures trajectory-stable despite wrong final answers?

This is the intended conceptual extension beyond purely descriptive trajectory geometry.

## 26. Causal subset selection

Do not run expensive causal assays on the full passive cohort.

After passive analysis, select a preregistered stratified causal subset.

Target:
- 24 L+ events,
- 24 L− events,
- 24 L+ / final-wrong events if available,

matched by:
- benchmark subtype,
- visual source type,
- retrieval score,
- approximate reasoning position,
- image/problem family when feasible.

Total target:

\[
48	ext{–}72	ext{ causal events}.
\]

If L− yield is too low, use all available L− events and matched L+ controls.

## 27. Main statistical analysis

Use item/family as the unit of independence whenever possible.

For cross-sectional cohorts:
- family/item bootstrap confidence intervals,
- mixed-effects or clustered models where appropriate.

For same-item pairs:
- paired differences,
- paired bootstrap over items,
- sign test / Wilcoxon as robustness checks.

Primary comparisons should be preregistered before causal intervention results are opened.

Avoid treating token-level observations as independent samples.

## 28. Required controls

- **Mention-only control:** the retrieval detector must not define failure solely from visual mention.
- **Reasoning-position control:** match or regress out normalized trajectory position.
- **Reasoning-length control:** wrong trajectories may simply be longer.
- **Problem-subtype control:** stratify geometry, charts, spatial, counting, etc. where possible.
- **Retrieval-score matching:** when comparing downstream properties, match L+ and L− events with similar retrieval activation strength.
- **Same-item stochastic pairs:** strongest defense against difficulty confounding.

## 29. Preregistered primary hypotheses

### H-primary-1
Among task-required retrieval events, local incorrect reads differ from local correct reads in at least one post-activation retrieval component:

\[
	ext{routing}
\quad	ext{or}\quad
	ext{causal visual influence}
\quad	ext{or}\quad
	ext{post-retrieval stability}.
\]

This is intentionally stage-agnostic.

### H-primary-2
The first-divergence distribution is not concentrated solely at retrieval activation.

That is, failures are not explained simply by "the model did not look."

### H-primary-3
At least one failure-localization effect replicates in the same-item paired cohort with the same direction.

This is the main robustness gate.

## 30. Success gates

### Gate 0 — Benchmark yield
At least:
- 250 correct,
- 250 wrong

usable native MathVision trajectories.

Preferred:
- 300+ per class.

If not met, use all available data and reconsider benchmark only if class imbalance is severe.

### Gate 1 — Frozen retrieval detector transfers
The Stage 8A detector must produce plausible, nondegenerate retrieval events on MathVision.

Require:
- retrieval events across at least 70% of visually demanding items,
- manual review confirms meaningful retrieval alignment on a random audited subset,
- mention-only / obvious nonvisual false-alarm rate remains acceptable.

Do not retrain the detector using correctness labels.

If transfer fails badly, stop and recalibrate retrieval detection before success/failure analysis.

### Gate 2 — Local visual-read cohort
Obtain at least:
- 64 L+ events,
- 32 L− events,

from independent items/families for the primary L+ vs L− analysis.

If L− is rarer, preserve all L− events and do not inflate them via loose annotation.

### Gate 3 — Same-item paired cohort
Obtain at least:
- 64 correct/wrong paired rollouts,
- from at least 48 unique items.

If lower, the cross-item analysis remains descriptive and causal generalization should be limited.

### Gate 4 — Replicated divergence
At least one retrieval-stage difference must:
1. be robust in the broad cohort,
2. survive matched controls,
3. replicate directionally in same-item pairs,
4. remain interpretable under causal subset intervention where applicable.

Only then should it motivate a new intervention.

## 31. What would justify a new intervention?

The intervention must follow the discovered failure location.

- **If F0 dominates:** retrieval triggering / forced visual re-access.
- **If F1 dominates:** source-routing correction, target-selective QK intervention, competition suppression.
- **If F2 dominates:** visual extraction verification or local reread, not generic Value amplification.
- **If F3 dominates:** revisit transport / Value-path intervention, now with a demonstrated failure phenotype.
- **If F4 dominates:** do **not** apply visual retrieval intervention; focus on evidence preservation, arithmetic/integration, or reasoning-state consistency.
- **If F5 dominates:** retrieval stabilization, confidence/verification after first read, or prevention of repeated wandering re-query cycles.

No intervention should be chosen before this stage identifies a reproducible divergence.

## 32. What a positive result adds beyond vSTREAM

A strong result should allow us to say:

> Prior work showed that correct and incorrect thinking trajectories differ in visual-attribution geometry. We show **where that divergence arises in the causal retrieval computation** by aligning reasoning at independently detected visual-retrieval events.

The novelty is therefore:

\[
oxed{
	ext{trajectory difference}
ightarrow
	ext{retrieval-event alignment}
ightarrow
	ext{mechanistic failure localization}
}
\]

not merely another success/failure trajectory classifier.

## 33. What a null would mean

### Null: correct/wrong trajectories differ globally but not at retrieval events
Interpretation:
- vSTREAM-style trajectory differences may arise downstream or from general reasoning instability rather than retrieval quality.

This is useful and should redirect intervention away from vision.

### Null: L+ and L− retrieval states are indistinguishable passively
Does not rule out mechanistic differences.

Proceed with the small causal subset before concluding equivalence.

### Null: passive and causal retrieval properties are indistinguishable even for L+ vs L−
Likely interpretations:
- extraction error occurs inside representations not measured by current routing/transport features,
- local wrong-read annotation conflates heterogeneous mechanisms,
- visual retrieval is not the dominant failure source.

Do not force a visual intervention.

## 34. Compute-efficient execution order

1. Run MathVision native census and compute Stage 8A retrieval proxy.
2. Score final correctness and produce large correct/wrong cohort.
3. Run whole-trajectory passive analysis.
4. Annotate retrieval-required events and local visual-read correctness on a stratified subset.
5. Run retrieval-event-aligned passive analysis.
6. Generate same-item multi-seed rollouts only for items needed to reach the paired target.
7. Freeze candidate divergence hypotheses.
8. Run expensive causal assays only on the matched causal subset.
9. Decide whether any intervention is scientifically justified.

## 35. Stop conditions

Stop this branch if:
- Stage 8A retrieval detector does not transfer to MathVision,
- local visual-read failures are too rare to support comparison,
- same-item mixed outcomes cannot be obtained at reasonable compute,
- broad differences disappear under same-item pairing,
- no retrieval-stage divergence survives causal validation.

Do not respond to a null by repeatedly changing the failure taxonomy or thresholds.

## 36. Recommended outputs

Produce:
1. MathVision native census
2. Correct/wrong whole-trajectory comparison
3. Retrieval-event raster plots
4. Event-aligned QK/attention/Value trajectories
5. Local-read 2×2 outcome table
6. Same-item paired divergence plots
7. Failure-location taxonomy counts
8. vSTREAM-style trajectory geometry conditioned on failure location
9. Small causal validation panel
10. Explicit intervention decision

## 37. Key figures for the paper

### Figure A — Retrieval-aligned correct vs wrong trajectories
Event-aligned curves around \(t=0\) retrieval onset.

### Figure B — First divergence along the visual-retrieval lifecycle

\[
	ext{activation}
ightarrow
	ext{routing}
ightarrow
	ext{transport}
ightarrow
	ext{local evidence}
ightarrow
	ext{integration}
\]

Show where each failure family first diverges.

### Figure C — Same-item paired example
Same image/question, one correct and one wrong rollout, aligned at the same visual subgoal.

### Figure D — Trajectory wandering explained by retrieval failure
vSTREAM-style path/tortuosity conditioned on F0–F5 failure type.

## 38. Final decision criterion

This stage succeeds if it moves the paper from:

\[
	ext{correct and wrong trajectories look different}
\]

to:

\[
oxed{
	extbf{correct and wrong trajectories diverge at a reproducible,
mechanistically identifiable stage of active visual retrieval or downstream use.}
}
\]

The strongest outcome is not a classifier.

It is a **causal localization of failure within the visual-retrieval lifecycle**, validated in both a large MathVision cohort and same-item correct/wrong stochastic pairs.
