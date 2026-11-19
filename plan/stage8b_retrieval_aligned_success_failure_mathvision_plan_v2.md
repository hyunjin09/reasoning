# Stage 8B (Revised) — Retrieval-Aligned Success/Failure Divergence on MathVision

## 0. Stage status and revision rationale

This plan **supersedes the earlier Stage 8B plan**.

A 32-example Qwen3-VL-2B-Thinking / MathVision transfer batch established that the frozen Stage 8A retrieval detector transfers successfully, but also exposed a protocol mismatch:

- under the prior Stage 8B pilot protocol (`temperature=0.6`), 22/32 traces hit the 40,960-token cap without `</think>`;
- those capped traces were initially treated as unusable for correct/wrong outcome analysis;
- however, the Qwen MathVision evaluation path does **not** automatically invalidate a trace because `</think>` is missing or because generation hits the output cap;
- instead, benchmark correctness is determined by extracting an answer from the generated response;
- therefore Stage 8B should use **Qwen-compatible MathVision scoring** rather than `cap -> invalid`.

The revised canonical Stage 8B protocol is therefore:

\[
\boxed{
\text{MathVision-specific generation}
+
\text{Qwen-style answer extraction}
+
\text{cap retained as a separate trajectory attribute}
}
\]

The previous `temperature=0.6` 32-example batch remains a **transfer/protocol pilot** and must not be mixed into the main Stage 8B outcome cohort.

---

# 1. One-line objective

Use the **frozen Stage 8A active-retrieval detector** to align MathVision reasoning trajectories at moments of visual retrieval, then determine:

\[
\boxed{
\textbf{where successful and failed reasoning first diverge}
}
\]

in Qwen3-VL-2B-Thinking.

The central mechanistic question is:

\[
\boxed{
\textbf{When visual retrieval is active, what computational property distinguishes successful from failed reasoning?}
}
\]

This is a **diagnostic stage**, not an intervention-first stage.

Any later intervention must be chosen from the failure location discovered here.

---

# 2. Why this experiment is necessary for the paper

Stage 8A established:

\[
\boxed{
\text{active visual retrieval is passively observable online}
}
\]

on Qwen3-VL-2B-Thinking using a frozen QK/attention-side retrieval proxy.

Stage 8A did **not** justify selective Value reinjection because:

- the preregistered routing-active / transport-weak cohort missed its size gate;
- cheap transport-strength metrics did not generalize;
- weak-transport cases were not demonstrated to be visual-reading failures that reinjection would correct.

Therefore the next high-value question is not:

> Can we amplify visual Value?

It is:

> **Once retrieval is active, where do successful and failed reasoning trajectories actually diverge?**

This directly leverages the strongest new capability from Stage 8A:

\[
\boxed{
\text{we can now align reasoning by internally detected retrieval events}
}
\]

rather than by arbitrary token position or post-hoc evidence spans.

---

# 3. Relation to vSTREAM / Real-Time Visual Attribution Streaming

Prior work such as **Real-Time Visual Attribution Streaming in Thinking Model (vSTREAM)** reports that successful and failed reasoning can exhibit different visual-attribution trajectory geometry.

Stage 8B must **not** stop at reproducing:

\[
\text{correct trajectory}
\neq
\text{wrong trajectory}.
\]

Our intended contribution is:

\[
\boxed{
\text{trajectory-level difference}
\rightarrow
\text{retrieval-event alignment}
\rightarrow
\text{mechanistic failure localization}
}
\]

The key question is:

> **Which stage of the visual-retrieval lifecycle explains the success/failure trajectory difference?**

The lifecycle under test is:

\[
\text{reasoning context}
\rightarrow
\text{retrieval activation}
\rightarrow
\text{source routing}
\rightarrow
\text{Value-rich transport}
\rightarrow
\text{local visual evidence}
\rightarrow
\text{downstream reasoning}
\]

---

# 4. Paper claims this stage may support

The broad target claim is:

> **Successful and failed multimodal reasoning do not merely differ globally in trajectory shape; they diverge at reproducible stages of the visual-retrieval computation or subsequent evidence use.**

Specific claims must be selected only after the data identify the divergence point.

Possible outcomes:

## Claim A — Retrieval activation failure

Failed trajectories do not activate visual retrieval when successful trajectories do.

## Claim B — Routing-quality failure

Correct and incorrect trajectories activate retrieval similarly, but failed visual reads exhibit weaker target-specific routing.

## Claim C — Causal influence failure

Retrieval and routing appear similar, but visual evidence has weaker causal control over local prediction in failed reads.

## Claim D — Extraction/content failure

The correct source is causally engaged, but the visual content extracted from it is wrong.

## Claim E — Downstream integration failure

Visual retrieval and the local visual read are correct, but reasoning later fails.

## Claim F — Retrieval instability / repeated re-query

An initial unresolved or incorrect read is followed by repeated re-retrieval, switching, or wandering.

---

# 5. What a null does NOT rule out

A null final-correct vs final-wrong difference at retrieval onset does **not** establish that vision is irrelevant to failure.

Possible explanations include:

- many final-answer errors occur after successful retrieval;
- only a subset of wrong trajectories contain local visual-read failures;
- cross-item problem difficulty dominates broad comparisons;
- the divergence becomes visible only under same-item stochastic pairing;
- source-specific differences are diluted by global visual metrics;
- failure occurs in extraction, binding, arithmetic, or integration after retrieval activation.

Therefore the stage must distinguish:

\[
\boxed{
\text{final outcome}
}
\]

from:

\[
\boxed{
\text{local visual-read outcome}.
}
\]

---

# 6. Model

**Qwen3-VL-2B-Thinking**

Use the validated mechanistic/instrumented execution path.

The Stage 8A retrieval detector is frozen and must not be refit using Stage 8B correctness labels.

---

# 7. Revised canonical MathVision generation protocol

For the **main Stage 8B cohort**, use the MathVision-specific Qwen-style generation recipe:

- BF16
- `temperature = 1.0`
- `top_p = 0.95`
- `top_k = 20`
- repetition penalty = 1.0
- presence penalty = 0.0
- `max_new_tokens = 40960`
- normal EOS stopping
- MathVision-compatible prompt formatting
- MathVision-compatible image preprocessing / pixel limits
- deterministic seed bookkeeping for each run

The key revision from the earlier pilot is:

\[
\boxed{
T=1.0
}
\]

for the Stage 8B canonical MathVision cohort.

The previous `T=0.6` 32-example batch is preserved as historical protocol/transfer evidence only.

Do **not** pool `T=0.6` and `T=1.0` trajectories in the primary analysis.

---

# 8. Revised benchmark scoring: cap is not invalid

## 8.1 Primary benchmark correctness label

For every generated response define:

\[
Y^{bench}
\in
\{\text{correct},\text{wrong},\text{unscorable}\}.
\]

Use the Qwen-compatible MathVision answer-extraction path.

Operationally:

- if `</think>` exists, use the post-`</think>` response for answer extraction;
- if `</think>` is absent, do **not** automatically mark invalid;
- retain the generated response and attempt benchmark-style answer extraction from it;
- score extracted answer against MathVision ground truth.

Thus:

\[
\boxed{
\text{40,960-token cap}
\not\Rightarrow
\text{invalid}
}
\]

and:

\[
\boxed{
\text{missing } </think>
\not\Rightarrow
\text{invalid}.
}
\]

A capped trajectory may be benchmark-correct or benchmark-wrong if an answer can be extracted from the generated text.

---

# 9. Keep completion status as a separate label

For every trajectory also store:

\[
C
\in
\{
\text{normal completed},
\text{capped without final section},
\text{other abnormal stop}
\}.
\]

At minimum record:

- whether `</think>` appeared,
- whether EOS appeared,
- generated-token length,
- whether the 40,960 cap was reached,
- whether a benchmark answer was extractable,
- where the extracted answer appeared in the trace.

The two axes must remain separate:

\[
\boxed{
Y^{bench}
\neq
C.
}
\]

Examples:

- benchmark-correct + capped
- benchmark-wrong + capped
- benchmark-correct + normal completion
- benchmark-wrong + normal completion

are all valid states.

---

# 10. Why completion status must remain separate

A correct/wrong retrieval comparison can be confounded if cap status strongly changes trajectory dynamics.

For example, capped traces may have:

- longer reasoning,
- repeated setup,
- repeated source reconsideration,
- more retrieval events,
- greater retrieval recurrence,
- higher trajectory tortuosity.

Therefore the stage requires three parallel analyses:

1. **benchmark-faithful correct vs wrong**
2. **completion-controlled correct vs wrong**
3. **capped vs normal-completion trajectory analysis**

Do not collapse these questions.

---

# 11. Stage 8B structure

The revised stage has five parts:

1. **8B.0 — Protocol revalidation at T=1.0**
2. **8B.1 — Native MathVision benchmark census**
3. **8B.2 — Whole-trajectory correct/wrong analysis**
4. **8B.3 — Retrieval-event-aligned mechanistic analysis**
5. **8B.4 — Same-item correct/wrong paired-rollout confirmation**

A small causal subset follows only after passive divergence hypotheses are frozen.

---

# 12. Stage 8B.0 — T=1.0 protocol revalidation

Before any large census, rerun the same or equivalent 32-item transfer set using the revised canonical protocol.

## Required checks

Measure:

- cap rate,
- `</think>` rate,
- EOS rate,
- extracted benchmark correctness,
- answer extractability,
- generation-length distribution,
- frozen Stage 8A detector transfer.

The detector must remain frozen.

No threshold refit is permitted.

---

# 13. Stage 8B.0 detector-transfer gate

The revised T=1.0 protocol should satisfy the same spirit as the prior transfer audit.

Require:

- active retrieval detected on \(\ge 70\%\) of clearly visually demanding reviewed items;
- prediction within the local tolerance window for \(\ge 70\%\) of annotated T events;
- low false alarm on hard-negative anchors;
- no obvious detector collapse under the temperature shift.

If the frozen detector fails badly at `T=1.0`, stop the large census and diagnose transfer before continuing.

---

# 14. Stage 8B.0 feasibility decision

The purpose is not to require a low cap rate.

Because capped traces are now benchmark-scorable, the key feasibility quantity is:

\[
\boxed{
\text{correct/wrong extractable outcome yield}
}
\]

not normal-EOS completion rate alone.

Continue to the census if:

- most trajectories yield a benchmark correctness label;
- correct and wrong both appear at useful rates;
- the retrieval detector transfers.

A high cap rate is acceptable for the **benchmark-faithful** analysis if answer extraction remains usable, but it must be retained as a covariate / stratification variable.

---

# 15. Stage 8B.1 — Native MathVision census

## Goal

Build a large benchmark-faithful correct/wrong outcome cohort under the revised Qwen-compatible protocol.

## Preferred target

Do not require exactly 500/500.

Preferred target:

- at least **300 benchmark-correct**
- at least **300 benchmark-wrong**

usable trajectories.

Minimum analysis target:

- at least **250 correct**
- at least **250 wrong**

if compute permits.

If the full benchmark naturally provides more, preserve all runs and construct balanced/matched analysis subsets afterward.

---

# 16. Census outputs per example

Store:

- item ID
- image/question
- full reasoning trace
- generated-token count
- stop/completion status
- presence/absence of `</think>`
- extracted answer
- extraction source/span
- benchmark correctness
- Stage 8A retrieval score time series
- thresholded retrieval event timestamps
- model logits/features needed for passive retrieval analysis
- benchmark subtype / available metadata

---

# 17. Primary outcome definition

For the broad Stage 8B cohort:

\[
\boxed{
\text{Correct}
=
\text{Qwen-compatible MathVision benchmark correct}
}
\]

\[
\boxed{
\text{Wrong}
=
\text{Qwen-compatible MathVision benchmark incorrect}
}
\]

Do **not** redefine capped outputs as failures merely because they lack a final-answer section.

---

# 18. Completion-controlled analysis

Because completion status may correlate with both outcome and trajectory geometry, perform:

### Analysis A — all benchmark-scorable traces

Correct vs wrong regardless of cap status.

### Analysis B — normal-completion only

Correct vs wrong among traces with normal reasoning termination.

### Analysis C — cap-matched / completion-matched

Match correct and wrong trajectories by:

- cap status,
- generated length,
- normalized reasoning position.

### Analysis D — capped-only

Correct vs wrong among capped trajectories if sample size permits.

A correct/wrong effect is stronger if it survives these controls.

---

# 19. Separate capped-trajectory analysis

Capped traces are a potentially meaningful reasoning phenotype.

Compare:

\[
\boxed{
\text{capped}
\quad vs\quad
\text{normal completion}
}
\]

on:

- retrieval event count,
- retrieval density,
- inter-retrieval interval,
- repeated retrieval,
- late retrieval,
- source switching,
- retrieval-feature path length,
- tortuosity,
- repeated setup / reconsideration markers.

This analysis must remain separate from the main success/failure claim.

Do not interpret:

\[
\text{cap}
=
\text{wrong reasoning}.
\]

---

# 20. Stage 8B.2 — Whole-trajectory correct/wrong analysis

This is the vSTREAM-adjacent descriptive layer.

For each trajectory compute:

## Retrieval frequency

\[
N_R=\#\{t:R_t>\tau_R\}
\]

and retrieval density:

\[
\frac{N_R}{\text{reasoning tokens}}.
\]

## Retrieval timing

- first retrieval position
- normalized first retrieval fraction
- late-retrieval fraction

## Retrieval recurrence

- repeated retrieval count
- inter-retrieval intervals
- retrieval burstiness

## Retrieval trajectory geometry

Using passive retrieval-feature vectors:

- path length
- displacement
- tortuosity
- local curvature
- recurrence

## Source/ROI movement

For localizable samples:

- target-source movement
- source switching
- target-vs-alternative changes

This layer is descriptive and not sufficient by itself for the main mechanistic claim.

---

# 21. Matching for broad correct/wrong analysis

Raw correct-vs-wrong comparison is confounded by item difficulty and trajectory length.

Match or stratify by:

- MathVision category/subtype
- diagram/type category
- answer format
- question length
- image/source complexity where available
- generated reasoning length
- cap/completion status
- retrieval-event count
- normalized retrieval timing

Do not modify retrieval detection based on outcome labels.

---

# 22. Stage 8B.3 — Retrieval-event-aligned mechanistic analysis

Use the frozen Stage 8A detector to define active retrieval onset:

\[
t=0
\equiv
\text{retrieval event}.
\]

Analyze a local window:

\[
[t-k,\ldots,t,\ldots,t+k].
\]

Primary:

\[
k=8
\]

Secondary robustness:

\[
k=4,\;16.
\]

---

# 23. Event annotation

Classify selected active events as:

## T — task-required visual retrieval

Current reasoning genuinely requires visual information.

## M — mention-only

Visual entity mentioned without required reacquisition.

## U — unclassified active retrieval

Detector fires, but semantic status is unresolved.

Primary mechanistic comparisons use T events.

---

# 24. Local visual-read correctness

For sufficiently localizable T events, annotate:

## L+ — locally correct visual read

Immediate visual claim matches the relevant visual evidence.

## L− — locally incorrect visual read

Immediate visual quantity/relation/binding/source-conditioned claim is wrong.

## L? — unresolved

Cannot certify local truth.

This is critical because:

\[
\boxed{
\text{final wrong}
\not\Rightarrow
\text{retrieval wrong}.
}
\]

---

# 25. Main 2 × 2 structure

| Local visual read | Benchmark outcome | Interpretation |
|---|---|---|
| L+ | correct | successful retrieval + successful downstream reasoning |
| L− | wrong | visual-stage failure candidate |
| L+ | wrong | downstream reasoning/integration failure candidate |
| L− | correct | compensation/recovery candidate |

The primary retrieval-mechanism contrast is:

\[
\boxed{
L+ \text{ vs } L-
}
\]

Final benchmark correctness is a secondary axis.

---

# 26. Retrieval-stage feature hierarchy

## Level 1 — Retrieval activation

Use frozen Stage 8A features:

- retrieval score
- visual attention mass
- QK visual competitiveness
- visual concentration
- local temporal rise

Question:

> Did the failed read fail to engage retrieval?

---

## Level 2 — Target/source routing

For localizable events compute:

\[
\Delta QK_{T-X}=QK_T-QK_X
\]

\[
\Delta A_{T-X}=A_T-A_X
\]

and:

- target visual rank
- target attention share
- target-vs-rest margin
- target-vs-nearest-confuser margin

Question:

> Retrieval is active, but is the wrong source being addressed?

---

## Level 3 — Value transport

Compute:

- target \(\alpha V\)
- visual \(\alpha V\) norm
- target-vs-distractor \(\alpha V\) margin
- post-\(W_O\) visual contribution
- visual contribution / residual ratio
- head cancellation/disagreement

These are descriptive unless supported by causal tests.

Stage 8A already showed that simple transport magnitudes are not reliable cheap causal-grounding gates.

Do not reinterpret them as causal grounding scores.

---

## Level 4 — Causal visual dependence

On a selected subset perform:

- visual-off intervention
- target source suppression
- target-vs-alternative source switching
- matched sham
- semantic counterfactual / Value intervention where appropriate

Measure:

- next-token distribution change
- full evidence-span CE effect
- target-vs-alternative preference
- semantic followability

Question:

> Does the visual source exert less or different causal control in failed local reads?

---

## Level 5 — Post-retrieval reasoning

After a local read examine:

- whether visual evidence persists in recent residual/KV state
- whether the model re-queries vision
- whether the same evidence is revised
- whether downstream arithmetic/integration fails despite a correct read

Question:

> Did the failure occur after retrieval succeeded?

---

# 27. Primary comparisons

## Comparison A — L+ vs L− at active T retrieval

Primary mechanistic comparison.

## Comparison B — benchmark-correct vs benchmark-wrong among L+

Tests downstream reasoning failure after successful local visual read.

## Comparison C — all benchmark-correct vs all benchmark-wrong

Broad descriptive comparison.

## Comparison D — capped vs normally completed

Separate trajectory-dynamics question.

---

# 28. Stage 8B.4 — Same-item correct/wrong paired rollouts

Cross-item comparisons remain confounded by difficulty.

The strongest confirmation uses:

\[
\boxed{
\text{same image}
+
\text{same question}
+
\text{different stochastic outcome}
}
\]

For selected MathVision items generate multiple seeds under the **same canonical T=1.0 protocol**.

Suggested:

- 4–8 seeds per item
- preserve all trajectories
- identify items with at least one benchmark-correct and one benchmark-wrong rollout

Cap status is allowed and recorded separately.

---

# 29. Paired cohort target

Target:

- at least **64 correct/wrong rollout pairs**
- from at least **48 unique MathVision items**

Stretch:

- 96–128 pairs.

Do not weaken the pairing definition merely to hit the count.

---

# 30. Semantic retrieval-event matching within pairs

Within a same-item correct/wrong pair:

1. identify the same visual subgoal;
2. locate the corresponding active retrieval event;
3. align retrieval onset;
4. compare stage-by-stage.

Do not pair arbitrary events based only on normalized time.

---

# 31. First-divergence localization

For each paired item determine the earliest supported divergence:

1. retrieval activation
2. source routing
3. Value transport
4. causal visual influence
5. local visual evidence emission
6. downstream integration
7. repeated retrieval / instability

This produces a per-pair mechanistic localization rather than a generic classifier.

---

# 32. Failure taxonomy

Use only when supported.

## F0 — No retrieval activation

Required retrieval does not activate.

## F1 — Misrouting

Retrieval activates but target source selectivity is impaired.

## F2 — Source-coupled extraction/content error

The demanded source is causally used but the local content is wrong.

## F3 — Weak/altered causal visual influence

Routing appears comparable, but causal evidence influence differs.

## F4 — Correct local retrieval, downstream failure

The local visual read is correct and grounded; later reasoning fails.

## F5 — Retrieval instability / repeated unsuccessful re-query

Repeated retrieval or switching follows an unresolved/incorrect read.

## FU — unresolved

Do not force every wrong trajectory into a class.

---

# 33. vSTREAM bridge analysis

Reproduce trajectory descriptors where feasible:

- path length
- tortuosity
- recurrence
- source movement

Then condition them on the mechanistic failure taxonomy.

The important question is:

\[
\boxed{
\text{Which retrieval failure state explains trajectory wandering?}
}
\]

Examples:

- does F1 misrouting precede repeated switching?
- does F5 account for high-tortuosity trajectories?
- are F4 downstream failures visually stable despite wrong benchmark answers?
- are capped trajectories especially enriched for repeated retrieval independent of correctness?

This is the intended extension beyond vSTREAM-style descriptive geometry.

---

# 34. Causal subset

Do not run expensive interventions on the entire census.

After passive analysis, freeze a matched causal subset.

Target:

- 24 L+ events
- 24 L− events
- 24 L+ / benchmark-wrong events if available

Match by:

- MathVision subtype
- source type
- retrieval score
- approximate reasoning position
- cap/completion status where possible
- item/family

Total target:

\[
48\text{–}72
\]

causal events.

---

# 35. Statistical unit and analysis

Use item/problem as the unit of independence.

For broad cohorts:

- item-level bootstrap
- clustered/mixed-effects models as appropriate

For same-item rollouts:

- paired differences
- paired bootstrap over items
- sign test / Wilcoxon as robustness checks

Do not treat token-level observations as independent samples.

---

# 36. Required controls

## Control 1 — Mention-only

Retrieval effects must not reduce to visual-word mention.

## Control 2 — Reasoning position

Match/regress normalized trajectory position.

## Control 3 — Reasoning length

Especially important because of capped trajectories.

## Control 4 — Completion status

Correct/wrong effects must be checked with cap status controlled.

## Control 5 — Problem subtype

Stratify MathVision categories where feasible.

## Control 6 — Retrieval-score matching

When comparing post-activation properties, match L+ and L− events with similar retrieval activation strength.

## Control 7 — Same-item stochastic pairs

Strongest defense against item-difficulty confounding.

---

# 37. Preregistered primary hypotheses

## H-primary-1

Among task-required retrieval events, locally incorrect reads differ from locally correct reads in at least one post-activation stage:

\[
\text{routing}
\quad\text{or}\quad
\text{causal visual influence}
\quad\text{or}\quad
\text{post-retrieval stability}.
\]

## H-primary-2

Failure is not explained solely by absence of retrieval activation.

## H-primary-3

At least one retrieval-stage divergence replicates directionally in the same-item paired cohort.

## H-primary-4

Any broad correct/wrong trajectory difference remains interpretable after controlling for completion/cap status.

---

# 38. Revised success gates

## Gate 0 — T=1.0 protocol validity

The revised MathVision protocol executes correctly and benchmark-style answer extraction works.

## Gate 1 — Frozen detector transfer

Stage 8A detector remains valid under T=1.0 MathVision generation.

## Gate 2 — Benchmark outcome yield

Obtain at least:

- 250 benchmark-correct
- 250 benchmark-wrong

scorable trajectories

or stop earlier if a power/feasibility analysis demonstrates a smaller adequate cohort.

Capped traces may count if benchmark correctness is extractable.

## Gate 3 — Local visual-read cohort

Obtain at least:

- 64 L+
- 32 L−

independent local retrieval events.

If L− is rarer, preserve all L−; do not loosen annotation.

## Gate 4 — Same-item paired cohort

At least:

- 64 correct/wrong pairs
- 48 unique items

preferred.

## Gate 5 — Replicated divergence

At least one mechanistic divergence must:

1. appear in the broad cohort;
2. survive matching/controls;
3. survive completion-status control;
4. replicate directionally in same-item pairs;
5. remain consistent with the causal subset where applicable.

Only then should it motivate an intervention.

---

# 39. What would justify a later intervention?

The intervention must follow the discovered failure location.

## If F0 dominates

Consider retrieval triggering / forced re-access.

## If F1 dominates

Consider source-routing correction or QK competition intervention.

## If F2 dominates

Consider local visual extraction verification / reread.

Do not use generic Value amplification.

## If F3 dominates

Revisit Value/transport intervention, now with a demonstrated failure phenotype.

## If F4 dominates

Do **not** apply a visual retrieval intervention.

Focus on evidence preservation, arithmetic, integration, or reasoning-state consistency.

## If F5 dominates

Consider retrieval stabilization, verification after first read, or reducing repeated wandering re-query.

---

# 40. What a positive result adds beyond vSTREAM

A strong Stage 8B result should support:

> Prior work showed that correct and incorrect thinking trajectories differ in visual-attribution geometry. We show **where those differences arise in the causal visual-retrieval lifecycle**, using an independently frozen online retrieval detector.

The novelty is:

\[
\boxed{
\text{trajectory geometry}
\rightarrow
\text{active retrieval alignment}
\rightarrow
\text{failure localization}
}
\]

not another correct/wrong trajectory classifier.

---

# 41. What a null means

## Null A — Global correct/wrong difference, no retrieval-aligned difference

Trajectory instability may arise downstream from visual retrieval.

## Null B — L+ and L− look passively similar

Run the small causal subset before concluding equivalence.

## Null C — Passive and causal retrieval properties are similar

Possible explanations:

- extraction/content error occurs in unmeasured representation stages;
- local-error annotation mixes multiple mechanisms;
- visual retrieval is not the dominant failure source.

Do not force a visual intervention.

## Null D — broad effects vanish after completion control

The original signal was likely driven by cap/trajectory-length differences rather than correctness.

This is scientifically useful and should be reported as such.

---

# 42. Compute-efficient execution order

1. **Re-run transfer/protocol audit at T=1.0.**
2. Verify Qwen-compatible answer extraction on normal and capped traces.
3. Verify frozen Stage 8A detector transfer.
4. Estimate benchmark-correct / benchmark-wrong / capped yield.
5. Launch census only if outcome yield is feasible.
6. Perform whole-trajectory correct/wrong and cap/completion analyses.
7. Annotate local T events and L+/L− on a stratified subset.
8. Run retrieval-event-aligned passive analysis.
9. Generate same-item multi-seed rollouts only as needed for paired confirmation.
10. Freeze divergence hypotheses.
11. Run expensive causal assays on the matched subset.
12. Decide whether any intervention is justified.

---

# 43. Explicit stop conditions

Stop or redesign if:

- the frozen Stage 8A detector does not transfer at T=1.0;
- benchmark-style answer extraction leaves too many traces unscorable;
- correct/wrong outcome yield is too imbalanced for the planned comparison;
- local L− events are too rare;
- broad effects disappear under completion-status controls;
- same-item paired effects do not replicate;
- no retrieval-stage divergence survives causal validation.

Do not respond to nulls by repeatedly changing thresholds, outcome definitions, or failure categories.

---

# 44. Required outputs

1. T=1.0 protocol-transfer report
2. benchmark-faithful MathVision census
3. benchmark correctness × completion-status table
4. correct/wrong whole-trajectory comparison
5. capped vs normal-completion trajectory comparison
6. retrieval-event raster plots
7. retrieval-aligned QK/attention/Value curves
8. L+/L− local visual-read table
9. same-item paired divergence plots
10. failure-location taxonomy
11. vSTREAM-style trajectory geometry conditioned on failure type
12. causal validation subset
13. explicit intervention/no-intervention decision

---

# 45. Key paper figures

## Figure A — Outcome × completion state

Show:

\[
\text{correct/wrong}
\times
\text{normal/capped}
\]

to make clear that benchmark correctness and completion are distinct.

## Figure B — Retrieval-aligned success/failure curves

Align at frozen active-retrieval onset.

## Figure C — First divergence along the retrieval lifecycle

\[
\text{activation}
\rightarrow
\text{routing}
\rightarrow
\text{transport}
\rightarrow
\text{local evidence}
\rightarrow
\text{integration}
\]

## Figure D — Same-item correct/wrong pair

Same image/question, different stochastic outcome.

## Figure E — Trajectory wandering conditioned on failure location

Connect to vSTREAM-style path/tortuosity without reducing the contribution to descriptive geometry.

---

# 46. Final decision criterion

Stage 8B succeeds if it moves the paper from:

\[
\text{correct and wrong trajectories look different}
\]

to:

\[
\boxed{
\textbf{correct and wrong trajectories diverge at a reproducible,
mechanistically identifiable stage of active visual retrieval or downstream evidence use}
}
\]

under:

- Qwen-compatible MathVision generation,
- Qwen-compatible answer extraction,
- explicit preservation of capped trajectories,
- completion-status controls,
- and same-item confirmation.

The strongest outcome is not a correct/wrong classifier.

It is a **mechanistic explanation of why success and failure trajectories differ**.
