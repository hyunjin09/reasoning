# Stage 8B.1a — 224-Example Bounded MathVision Discovery Census

## 0. Objective

Extend the existing **32-item T=1.0 MathVision transfer/protocol audit** with **224 additional outcome-independent MathVision examples**, yielding a **256-item bounded discovery cohort**.

The purpose is **not** to complete the full Stage 8B census.

The purpose is to decide whether there is a sufficiently strong and reproducible **retrieval-aligned success/failure divergence** to justify:

1. same-item correct/wrong paired-rollout confirmation, and
2. a small causal validation subset.

The stage-level question is:

\[
oxed{
	extbf{Do successful and failed MathVision trajectories differ at active visual-retrieval events in a way worth mechanistically following up?}
}
\]

## 1. Why this experiment is necessary for the paper

Stage 8A established that active visual retrieval can be passively detected online.

Stage 8B v2 then showed on a 32-item MathVision audit that:

- the frozen Stage 8A detector transfers under the revised T=1.0 MathVision protocol;
- benchmark-style correct/wrong outcomes occur at useful rates;
- capped outputs must remain separate from correctness, but the revised benchmark protocol is operationally usable;
- full-census execution would be expensive.

Therefore the next experiment should **not** immediately spend compute on the full MathVision benchmark.

Instead, we need a bounded discovery cohort large enough to answer:

\[
oxed{
	ext{Is there a retrieval-aligned success/failure effect large enough to justify deeper causal work?}
}
\]

A positive result would support moving from:

> correct and wrong reasoning trajectories look different

to:

> correct and wrong trajectories diverge at a reproducible stage of active visual retrieval or downstream evidence use.

A null would justify stopping before a much larger census.

## 2. Exact paper claim a positive result could support

This stage should not preselect the mechanism.

The desired broad claim is:

> **Successful and failed multimodal reasoning exhibit reproducible differences when aligned to independently detected visual-retrieval events.**

The specific mechanism depends on which stage diverges.

Possible positive interpretations include:

- failed trajectories retrieve less often when visual evidence is needed;
- retrieval activates normally, but target routing is weaker in failed local reads;
- routing is similar, but causal visual influence is weaker;
- local retrieval is correct and divergence occurs downstream;
- failed local reads are followed by repeated re-retrieval / trajectory wandering.

## 3. What a null does NOT rule out

A null broad correct-vs-wrong difference does **not** imply that visual retrieval is irrelevant.

Possible reasons include:

- final-answer correctness is too coarse;
- only local visual-read failures differ;
- cross-item difficulty masks effects;
- same-item stochastic pairs are needed;
- failure occurs after correct retrieval;
- source-specific effects are diluted by global features.

Therefore this stage must preserve both:

\[
oxed{	ext{benchmark outcome}}
\]

and:

\[
oxed{	ext{local visual-read outcome}}
\]

where available.

## 4. Cohort construction

### Existing cohort

Already completed:

- 32 MathVision examples
- Qwen3-VL-2B-Thinking
- T=1.0 canonical Stage 8B v2 protocol
- frozen Stage 8A detector
- benchmark-style outcome extraction
- 12 correct / 16 wrong / 4 unresolved
- detector-transfer Gate 1 passed

These 32 examples remain part of the bounded discovery cohort.

### New cohort

Add exactly:

\[
oxed{224 	ext{ new MathVision examples}}
\]

so that:

\[
32 + 224 = 256
\]

total examples.

Selection must be:

- from the existing fixed MathVision census order;
- **outcome-independent**;
- frozen before generation;
- without cherry-picking by item difficulty, category, or expected correctness.

Do not select examples based on detector score, outcome likelihood, or perceived usefulness.

## 5. Model and frozen generation protocol

Use:

**Qwen3-VL-2B-Thinking**

Canonical Stage 8B v2 generation:

- BF16
- `temperature = 1.0`
- `top_p = 0.95`
- `top_k = 20`
- repetition penalty = 1.0
- presence penalty = 0.0
- `max_new_tokens = 40960`
- normal EOS stopping
- frozen MathVision prompt/chat preprocessing
- frozen image preprocessing / pixel handling
- deterministic run/seed bookkeeping

No changes from the successful 32-item T=1.0 audit.

## 6. Frozen retrieval detector

Use the **Stage 8A frozen detector unchanged**.

Do not:

- refit the model,
- change the feature set,
- change the layer/head aggregation,
- change the threshold,
- recalibrate using MathVision correctness labels.

Frozen threshold:

\[
oxed{
	au_R = 0.5478025980771918
}
\]

The detector is used only as an **active-retrieval event anchor**.

## 7. Benchmark scoring

Use the revised Stage 8B v2 scoring protocol.

For every response assign:

\[
Y^{bench}
\in
\{
	ext{correct},
	ext{wrong},
	ext{unresolved}
\}
\]

using the frozen local Qwen-compatible MathVision answer-extraction adapter.

Important:

\[
oxed{
	ext{cap} 
ot\Rightarrow 	ext{invalid}
}
\]

and:

\[
oxed{
	ext{missing } </think> 
ot\Rightarrow 	ext{invalid}.
}
\]

If an answer can be unambiguously extracted, score it.

If not, keep it unresolved.

## 8. Completion status remains separate

Also assign:

\[
C
\in
\{
	ext{normal completed},
	ext{capped},
	ext{other abnormal stop}
\}.
\]

Store:

- generated-token count,
- `</think>` presence,
- EOS presence,
- whether 40,960 was reached,
- whether an answer was extracted,
- where the adopted answer occurred.

Correctness and completion must never be collapsed into one label.

## 9. Main purpose of the 256-item cohort

The 256 examples are a **bounded discovery census**, not a final prevalence estimate.

The main decision after this stage is:

\[
oxed{
	extbf{Is there a reproducible retrieval-aligned success/failure divergence worth confirming?}
}
\]

Do not extend to the full benchmark automatically.

## 10. Passive whole-trajectory analysis

For every trajectory compute:

### Retrieval count

\[
N_R=\#\{t:R_t>	au_R\}
\]

### Retrieval density

\[
D_R=
rac{N_R}{	ext{generated reasoning tokens}}
\]

### First retrieval timing

- absolute token position
- normalized reasoning fraction

### Inter-retrieval intervals

\[
\Delta t_i=t_{i+1}-t_i
\]

### Retrieval recurrence

- repeated retrieval count
- bursts
- late re-retrieval

### Retrieval trajectory geometry

Using the passive retrieval feature vector:

- path length
- displacement
- tortuosity
- local curvature
- recurrence

### Source/ROI movement

Where source localization is available:

- target-source share
- source switching
- target-vs-alternative movement

## 11. Broad outcome comparisons

Run at least:

### A. All benchmark-correct vs benchmark-wrong

Primary descriptive broad comparison.

### B. Normal-completion correct vs wrong

Controls for cap/completion status.

### C. Length-matched correct vs wrong

Match on generated reasoning length.

### D. Cap-matched correct vs wrong

If sample counts permit.

### E. Capped vs normal-completion

Separate trajectory-dynamics analysis.

Do not infer retrieval failure from completion status alone.

## 12. Retrieval-event-aligned analysis

For active retrieval events:

\[
R_t>	au_R
\]

define:

\[
t=0
\]

as retrieval onset.

Analyze:

\[
[t-8,\ldots,t,\ldots,t+8]
\]

Primary window:

\[
k=8
\]

Secondary robustness:

\[
k=4,\;16.
\]

## 13. Event annotation

On a stratified reviewed subset, annotate active events as:

### T — task-required visual retrieval

Current reasoning genuinely requires visual information.

### M — mention-only

Visual entity is mentioned without requiring reacquisition.

### U — unresolved active retrieval

Semantic status unclear.

Primary mechanistic comparisons use T events.

## 14. Local visual-read outcome

For localizable T events annotate:

### L+ — locally correct visual read

The local visual claim matches the source evidence.

### L− — locally incorrect visual read

The local quantity/relation/binding/source-conditioned statement is wrong.

### L? — unresolved

Local correctness cannot be certified.

The primary retrieval-mechanism contrast is:

\[
oxed{
L+ 	ext{ vs } L-
}
\]

not merely final correct vs final wrong.

## 15. Retrieval-stage features

### Level 1 — Retrieval activation

- frozen retrieval score
- visual attention mass
- QK visual competitiveness
- attention concentration
- local temporal rise

Question:

> Did failed local reads fail to activate retrieval?

### Level 2 — Source routing

For localizable source/ROI cases:

\[
\Delta QK_{T-X}=QK_T-QK_X
\]

\[
\Delta A_{T-X}=A_T-A_X
\]

Also record:

- target rank
- target attention share
- target-vs-rest margin
- target-vs-nearest-confuser margin

Question:

> Retrieval activates, but does failed reasoning route less selectively to the demanded source?

### Level 3 — Value / transport features

Descriptive only at this stage:

- target \(lpha V\)
- visual \(lpha V\) norm
- target-vs-distractor \(lpha V\)
- post-\(W_O\) visual contribution
- contribution/residual ratio
- head cancellation/disagreement

Do not reinterpret these as validated causal-grounding metrics.

Stage 8A already showed cheap transport magnitudes are not reliable general online weakness gates.

### Level 4 — Post-retrieval dynamics

Measure:

- immediate re-retrieval
- revision of the same visual fact
- repeated source switching
- persistence of the local claim
- downstream arithmetic/integration trajectory
- late visual re-engagement

Question:

> Does a failed local read produce repeated retrieval instability or wandering?

## 16. Main comparisons

### Primary A — L+ vs L−

At task-required active retrieval events.

This is the most important mechanistic comparison.

### Primary B — benchmark-correct vs benchmark-wrong among L+

Tests downstream failure after correct local visual reads.

### Secondary C — benchmark-correct vs benchmark-wrong overall

Broad trajectory comparison.

### Secondary D — capped vs normal-completion

Separate reasoning-stability comparison.

## 17. vSTREAM bridge analysis

Compute trajectory descriptors analogous in spirit to vSTREAM:

- path length
- tortuosity
- recurrence
- source movement

But the paper question is not:

> Are wrong trajectories more tortuous?

It is:

\[
oxed{
	extbf{Which retrieval-stage failure explains the trajectory difference?}
}
\]

Examples to test:

- L− followed by elevated re-retrieval
- routing ambiguity followed by source switching
- repeated unresolved retrieval followed by high tortuosity
- L+ / final-wrong trajectories with stable visual retrieval but later reasoning failure

## 18. Discovery sample-size expectations

The 32-item pilot produced:

- 12 correct
- 16 wrong
- 4 unresolved

and reviewed-prefix local events:

- 33 L+
- 4 L−
- 1 unresolved

These are **pilot point estimates only**.

Do not treat them as prevalence guarantees.

At 256 examples, use the observed cohort rather than extrapolated counts for final go/no-go decisions.

## 19. Bounded-census success criteria

The 256-item stage is not required to hit the original full Stage 8B target of:

- 250 correct
- 250 wrong

because this is a discovery checkpoint.

Instead require:

### Gate A — outcome yield

At least:

- 64 benchmark-correct
- 64 benchmark-wrong

scorable trajectories.

If one class falls below 64, do not proceed automatically.

### Gate B — retrieval coverage

Frozen retrieval detector remains nondegenerate across the larger MathVision cohort.

Require:

- active retrieval in a substantial majority of reviewed visually demanding items;
- no obvious collapse in hard-negative specificity.

Do not refit.

### Gate C — local-read yield

Preferred:

- at least 64 L+
- at least 24 L−

independent events

for the discovery comparison.

Stretch target:

- 32+ L−

If L− remains too rare, do not loosen annotation definitions.

### Gate D — discovery divergence

At least one retrieval-aligned difference must be:

- directionally meaningful,
- not explained by completion status alone,
- not explained by reasoning length alone,
- present in more than one problem family/subtype,
- large enough to justify same-item paired confirmation.

Do not require causal validation yet.

## 20. What counts as a meaningful discovery signal?

Examples include:

### Signal 1 — activation deficit

\[
R_{L-}<R_{L+}
\]

with matching for event type and reasoning position.

### Signal 2 — routing deficit

\[
R_{L-}pprox R_{L+}
\]

but:

\[
\Delta QK_{T-X}^{L-}
<
\Delta QK_{T-X}^{L+}.
\]

### Signal 3 — repeated retrieval after local error

\[
P(	ext{re-retrieval within }w\mid L-)
>
P(	ext{re-retrieval within }w\mid L+).
\]

### Signal 4 — trajectory instability conditioned on local failure

\[
	ext{tortuosity}_{L-	ext{-containing}}
>
	ext{tortuosity}_{L+	ext{-only}}.
\]

### Signal 5 — downstream failure

L+ / final-wrong trajectories look retrieval-wise similar to L+ / final-correct trajectories.

This would imply the failure lies later.

## 21. Matching / confound controls

For broad correct/wrong analysis control or stratify by:

- completion status
- generated length
- MathVision subtype/category
- answer format
- question length
- retrieval count
- normalized retrieval position

For L+ vs L− control or match by:

- retrieval score
- task-required event type
- reasoning position
- source/ROI type
- problem family/subtype where feasible

Do not treat token-level events as independent.

Use item/family as the statistical unit wherever possible.

## 22. Statistical analysis

For broad comparisons:

- item-level bootstrap confidence intervals
- clustered / mixed-effects models where appropriate

For event-level analyses:

- cluster by item
- family-level bootstrap
- avoid pseudo-replication from multiple events in one trajectory

Report:

- effect sizes
- confidence intervals
- not only p-values

Discovery statistics should remain clearly labeled exploratory when appropriate.

## 23. No causal assays in Stage 8B.1a

Do **not** yet run:

- source suppression
- source switching
- visual-off causal scoring
- Value patching
- reinjection
- paired stochastic rollouts

The bounded census is passive + semantic annotation only.

The purpose is to identify which mechanistic divergence, if any, is worth causal confirmation.

## 24. No detector changes

Forbidden during this stage:

- threshold tuning
- feature changes
- retraining
- outcome-conditioned calibration
- MathVision-specific detector optimization

The Stage 8A detector must remain a fixed independent anchor.

## 25. Stop conditions

Stop Stage 8B after the 256-item analysis if:

- correct/wrong yield is too low;
- frozen retrieval detector no longer behaves reliably;
- L− events remain too rare for comparison;
- broad correct/wrong effects vanish after completion/length controls;
- no retrieval-aligned effect appears;
- observed differences are entirely explained by cap/completion status.

Do **not** launch the full census merely because the bounded census completed.

## 26. Proceed condition

Proceed to the next Stage 8B component only if the bounded census reveals at least one plausible retrieval-aligned divergence.

Then move to:

\[
oxed{
	ext{same-item correct/wrong paired-rollout confirmation}
}
\]

followed by:

\[
oxed{
	ext{small matched causal validation subset}
}
\]

Only after those pass should an intervention be designed.

## 27. If the bounded census is positive

The next stage should freeze the strongest discovered divergence.

Examples:

### If routing differs

Next:

- same-item correct/wrong pairs
- causal target-vs-alternative routing intervention

### If repeated retrieval differs

Next:

- same-item recurrence confirmation
- test whether local failure precedes wandering

### If local retrieval looks normal but final outcome differs

Next:

- investigate downstream integration, not visual intervention

### If transport features differ

Do not return directly to Value reinjection.

First validate the difference causally in matched L+/L− events.

## 28. Required artifacts

Produce:

1. `stage8b1a_256_census_summary.json`
2. benchmark correctness × completion-status table
3. retrieval-event count/density summary
4. correct/wrong trajectory comparison
5. capped/normal trajectory comparison
6. retrieval-aligned event plots
7. T/M/U annotation table
8. L+/L− local-read table
9. source-routing comparison
10. Value/transport descriptive comparison
11. recurrence / tortuosity analysis
12. discovery effect summary
13. explicit go/no-go recommendation

## 29. Key figures

### Figure 1 — Outcome × completion status

Show:

\[
	ext{correct/wrong/unresolved}
	imes
	ext{normal/capped}
\]

### Figure 2 — Whole-trajectory retrieval dynamics

Correct vs wrong, with completion-controlled overlays.

### Figure 3 — Retrieval-aligned L+ vs L−

QK / attention / routing curves around \(t=0\).

### Figure 4 — Re-retrieval after local read

Probability of another retrieval event after L+ vs L−.

### Figure 5 — vSTREAM bridge

Trajectory tortuosity/path length stratified by local retrieval outcome.

## 30. Final decision rule

The bounded census succeeds if it answers:

\[
oxed{
	extbf{Is there a reproducible and mechanistically interpretable difference
between successful and failed reasoning at active visual-retrieval events?}
}
\]

If **yes**:

- freeze the strongest divergence;
- proceed to same-item paired confirmation;
- then run a small causal validation subset.

If **no**:

- do not spend compute on the full MathVision census;
- close or redirect Stage 8B.

The goal is not to accumulate more correct/wrong samples.

The goal is to determine whether **active visual retrieval provides a mechanistic axis that explains reasoning success and failure**.
