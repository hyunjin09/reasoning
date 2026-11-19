# Stage 8A — Qwen3-VL-2B-Thinking: Online Visual-Retrieval Proxy and Transport-Weak State Calibration

## 0. Purpose

Before testing Visual Value reinjection, determine two things on **Qwen3-VL-2B-Thinking**:

1. **WHEN** can an active visual-retrieval episode be detected from passive internal signals available at test time?
2. **WHEN is intervention justified** — i.e., among active retrieval episodes, can we identify states where visual evidence is being addressed but its native causal transport into the current computation is weak?

This stage is intentionally **pre-intervention**. No reinjection result should be interpreted until the trigger and gating variables are calibrated.

The desired future controller is:

\[
\boxed{
\text{Active visual retrieval}
\;\land\;
\text{weak visual transport}
\Rightarrow
\text{Visual Value reinjection}
}
\]

The immediate goal of this stage is to determine whether the two left-hand conditions are observable and sufficiently separable on Qwen3-VL-2B-Thinking.

---

## 1. Why this experiment is necessary for the paper

Our 4B results support the following mechanistic picture:

\[
\text{reasoning context}
\rightarrow
\text{target-specific visual retrieval}
\rightarrow
\text{Value-rich transport}
\rightarrow
\text{local reasoning-side carrier}
\]

We also observed that retrieval events are accompanied by passive phenotypes such as:

- stronger visual QK compatibility,
- increased visual attention,
- target-selective visual routing,
- stronger \(\alpha V\) / post-\(W_O\) transport.

However, we have **not** yet established that these signals can be turned into a reliable **online retrieval trigger**, nor that there exists a distinct state in which:

\[
\text{retrieval is active}
\quad\text{but}\quad
\text{visual transport is weak}.
\]

That distinction is essential for a principled reinjection intervention.

A positive result would support a paper-level transition from:

> We discovered how visual evidence is causally retrieved during reasoning.

To:

> The discovered retrieval mechanism exposes an online, model-internal control point: active retrieval can be detected, and weak transport can be selectively identified before intervention.

This stage also provides a compact **cross-scale replication** of the retrieval mechanism on Qwen3-VL-2B-Thinking.

---

## 2. Exact claims this stage may support

### Claim A — Online retrieval-state observability

> Active visual-retrieval episodes in a thinking MLLM can be detected from passive QK/attention-side signals available during the forward pass.

This is stronger than saying that attention is sometimes high near visual claims.

The detector must distinguish:

- true retrieval-required events,
- mention-only events,
- nearby non-retrieval reasoning,
- matched nonvisual reasoning.

### Claim B — Retrieval engagement and visual transport are not necessarily identical

If a stable cohort exists with:

\[
R_t \text{ high}
\quad\land\quad
G_t \text{ low},
\]

then we may claim:

> Visual routing can become active without the retrieved visual contribution exerting correspondingly strong causal influence on the current computation.

This would motivate selective Value reinjection.

### Claim C — Under-transported states may still contain usable visual semantics

If high-\(R\), low-\(G\) states retain semantic sensitivity under a Value-only counterfactual intervention, then:

> Some weakly grounded retrieval states contain usable visual information in the Value pathway that is under-utilized by the native computation.

This is the key prerequisite for Visual Value reinjection.

---

## 3. What this stage must NOT claim

This stage does **not** establish:

- that reinjection improves benchmark accuracy,
- that low grounding is generally caused by weak Value transport,
- that all wrong visual claims are under-transport failures,
- that attention magnitude alone measures causal retrieval,
- that high-\(R\), low-\(G\) states are MIRAGE in the no-image sense,
- that a 2B model uses the exact same heads/layers as the 4B model.

A separate intervention stage is required after the gates below are passed.

---

## 4. Competing mechanisms to distinguish

We want to distinguish at least four possibilities.

### H1 — Observable retrieval-state hypothesis

Active visual retrieval produces a reliable passive QK/attention signature.

\[
\text{retrieval active}
\Rightarrow
R_t \uparrow
\]

### H2 — Attention-only semantic-alignment hypothesis

The observed passive signal mainly reflects visual mention/alignment rather than causal retrieval.

Prediction:

- mention-only events look similar to retrieval-required events,
- passive proxy fails on hard negatives.

### H3 — Tight coupling hypothesis

Once retrieval is active, visual transport is almost always already strong.

\[
R_t \uparrow
\Rightarrow
G_t \uparrow
\]

If true, there is little justification for Value reinjection gating.

### H4 — Routing-active / transport-weak hypothesis

A nontrivial state exists in which:

\[
R_t \uparrow,
\qquad
G_t \downarrow,
\]

and at least some of these states retain usable visual semantics in the Value pathway.

This is the state required for a mechanistically motivated reinjection intervention.

---

## 5. Model and execution path

### Primary model

**Qwen3-VL-2B-Thinking**

Use the same official-style Thinking generation protocol as the canonical 4B experiments where applicable.

Recommended generation settings:

- BF16
- official-style Thinking sampling
- temperature 0.6
- top-p 0.95
- top-k 20
- seed 1234
- EOS normal stopping
- `max_new_tokens = 40960`

The 2B model must use its own technically validated cached/streaming execution path.

Do **not** assume 4B head indices transfer directly to 2B.

---

## 6. Technical calibration before scientific scoring

Before collecting the main cohort:

1. Verify normal EOS behavior on at least 10 representative MathVerse items.
2. Verify cached/streaming forward consistency within the accepted BF16 path.
3. Verify visual-token indexing and image K/V interception.
4. Verify per-head access to:
   - QK logits,
   - attention probabilities,
   - Value-weighted attention output,
   - post-\(W_O\) visual contribution.
5. Run a small causal localization set to identify the **2B functional late retrieval window**.

The purpose is not to reproduce exact 4B head IDs.

The desired cross-model replication is functional:

\[
\text{late target-selective routing}
\rightarrow
\text{Value-rich visual transfer}
\]

rather than index-identical circuitry.

---

## 7. Benchmark and cohort

### Primary benchmark

**MathVerse**

Use items with:

- localizable visual evidence,
- editable visual semantics,
- a clear intermediate visual claim,
- a usable matched semantic counterfactual,
- a matched render/sham edit where possible.

Prefer items already used successfully in the 4B causal-retrieval experiments, but generate **fresh 2B-native reasoning traces**.

Do not reuse a 4B reasoning prefix as the 2B causal prefix.

### Target cohort size

#### Discovery
- 48 base images / problem families
- target: 80–120 annotated reasoning events

#### Confirmation
- 48 disjoint base images / problem families
- target: 80–120 annotated reasoning events

Total target:

- **96 bases**
- approximately **160–240 events**

Split strictly by image/problem family.

If the event yield is too low, expand the pool before loosening definitions.

---

## 8. Event taxonomy

Annotate events from the 2B model's own native reasoning.

### Positive: retrieval-required event \(T\)

A step where the current reasoning requires a visual fact that is not already sufficiently available from text/reasoning history.

Examples:

- reading a labeled length,
- identifying a diagram relation,
- reading a visual quantity needed for the next computation.

A causal confirmation subset should show sensitivity to the relevant visual semantics.

### Hard negative 1: mention-only event \(M\)

The same or related visual entity is verbally mentioned, but current inference does not require reacquiring its visual content.

This is the most important negative.

### Hard negative 2: nearby non-retrieval step

A reasoning step temporally close to \(T\) but performing arithmetic, algebra, or integration using already available information.

### Hard negative 3: matched nonvisual reasoning

A reasoning step with similar token/length structure but no visual-information requirement.

---

## 9. Part I — Calibrate an online active-retrieval proxy

### Design principle

The retrieval trigger must use quantities available during the normal forward pass.

To keep the later transport gate conceptually separate, the primary retrieval proxy should initially exclude Value magnitude.

Use **QK/attention-side features** first.

Also avoid ROI annotations in the deployable proxy.

ROI-relative features may be used only for offline diagnostic analysis.

---

## 10. Candidate retrieval-proxy features

Compute features over the 2B causal late retrieval window.

### R1 — Total visual attention mass

\[
A_t^V
=
\sum_{j\in V} a_{t,j}
\]

Aggregate across selected causal heads/layers using median, trimmed mean, and max as discovery variants.

### R2 — Visual-vs-nonvisual QK competitiveness

For current query \(q_t\):

\[
Q_t^V
=
\operatorname{LSE}_{j\in V}(q_tK_j)
-
\operatorname{LSE}_{j\in N}(q_tK_j)
\]

where \(N\) contains nonvisual context tokens.

Also test reasoning-only competition:

\[
Q_t^{V-R}
=
\operatorname{LSE}_{j\in V}(q_tK_j)
-
\operatorname{LSE}_{j\in R}(q_tK_j).
\]

### R3 — Visual attention concentration

Examples:

- top-k visual attention mass,
- normalized entropy over visual tokens,
- max visual attention,
- effective number of attended visual tokens.

This asks whether retrieval events become more visually focused, not merely more visual in total mass.

### R4 — Temporal rise

For each passive quantity \(x_t\):

\[
\Delta x_t
=
x_t
-
\operatorname{median}(x_{t-k:t-1})
\]

Use a small fixed recent window selected on discovery.

This tests whether **relative activation** is more robust than an absolute scale across problems.

### R5 — Sink-release feature

Measure reduction in the relevant sink/special-token mass relative to the recent local baseline.

Use as a secondary feature only.

### R6 — Combined passive retrieval score

Compare at minimum:

1. attention only,
2. QK only,
3. QK + attention,
4. QK + attention + concentration/temporal features.

Use a simple interpretable classifier first:

- logistic regression,
- linear probe,
- or a fixed normalized score.

Do not begin with a high-capacity nonlinear model.

---

## 11. Retrieval-proxy ground truth

The primary event label is the semantic event taxonomy:

\[
Y_t^{event}
\in
\{T, M, nearby, nonvisual\}.
\]

Additionally, on a causal-confirmation subset, validate \(T\) using source-sensitive intervention:

- matched visual semantic counterfactual,
- target visual suppression/switch where available,
- matched sham/render control.

The purpose of causal confirmation is to ensure that the proxy is not merely learning annotation conventions.

---

## 12. Retrieval-proxy evaluation

Primary comparisons:

\[
T \text{ vs } M
\]

and

\[
T \text{ vs all hard negatives}.
\]

Report:

- AUROC
- AUPRC
- recall at fixed false-positive rate
- false-positive rate on mention-only events
- calibration error
- family-level bootstrap confidence intervals

Also compare against:

- token/lexical baseline,
- trajectory-position baseline,
- visual-word presence baseline,
- layer-0 / shallow-state baseline if feasible.

A useful proxy should beat these baselines.

---

## 13. Discovery-to-confirmation thresholding

Do **not** choose a hand-written attention threshold.

On the discovery split, choose \(\tau_R\) to satisfy:

- high recall for confirmed retrieval-required events,
- low false-positive rate on mention-only events.

Recommended target:

- retrieval recall \(\ge 0.80\)
- mention-only FPR \(\le 0.20\)

Freeze:

- feature set,
- normalization,
- causal layer/head subset,
- \(\tau_R\)

before evaluating confirmation.

If no candidate satisfies the gate, do not proceed to an online reinjection controller.

---

## 14. Part II — Measure native visual transport strength

Only analyze transport gating primarily within:

\[
R_t > \tau_R.
\]

The question is:

> Once retrieval is active, how strongly does the current visual pathway actually affect the current computation?

---

## 15. Expensive causal grounding / transport oracle

Use an intervention-based quantity as the scientific oracle.

### G1 — Visual-off next-token distribution effect

Compare:

\[
p_{\text{normal}}(y_{t+1})
\]

with:

\[
p_{\text{V-off}}(y_{t+1}),
\]

where the causal late visual contribution is removed while preserving the same prefix.

Measure:

\[
G_t^{JS}
=
D_{\mathrm{JS}}
\left(
p_{\text{normal}},
p_{\text{V-off}}
\right).
\]

### G2 — Evidence-span CE effect

For annotated upcoming visual evidence span \(E\):

\[
G_t^{CE}
=
CE_{\text{V-off}}(E)
-
CE_{\text{normal}}(E).
\]

Positive values indicate that the native visual contribution supports the upcoming evidence.

### G3 — Target-relative visual source dependence

Where ROI/source annotation exists:

\[
G_t^{VSD}
=
\text{effect(target visual removal/switch)}
-
\text{effect(irrelevant/sham)}.
\]

Use as an offline high-specificity diagnostic, not as the intended online gate.

---

## 16. Cheap transport-gate candidates

The eventual controller should not require an expensive extra causal forward pass if avoidable.

Compare cheap passive measures against \(G_t^{causal}\).

### T1 — Visual \(\alpha V\) magnitude ratio

\[
T_t^{\alpha V}
=
\frac{
\left\|
\sum_{j\in V} a_jV_j
\right\|
}{
\left\|
\sum_j a_jV_j
\right\|+\epsilon
}.
\]

### T2 — Post-\(W_O\) visual contribution ratio

\[
T_t^{WO}
=
\frac{
\|C_t^V\|
}{
\|C_t^{all}\|+\epsilon
}
\]

with

\[
C_t^V
=
\sum_{h\in H_{\text{causal}}}
W_O^{(h)}
\left(
\sum_{j\in V} a_{h,j}V_{h,j}
\right).
\]

### T3 — Visual contribution / residual ratio

\[
T_t^{res}
=
\frac{\|C_t^V\|}
{\|h_t\|+\epsilon}.
\]

### T4 — Head-wise cancellation / dispersion

Measure whether strong visual contributions from multiple heads cancel after projection/summation.

Candidate statistics:

- ratio of norm-of-sum to sum-of-norms,
- cross-head cosine disagreement.

This is exploratory and should not become the main gate unless it clearly improves prediction.

---

## 17. Define the candidate intervention state

The state of interest is:

\[
\boxed{
R_t > \tau_R
\quad\land\quad
G_t^{causal} < \tau_G
}
\]

Interpretation:

> passive routing indicates an active visual-retrieval episode, but the native visual pathway has weak causal influence on the current computation.

This should initially be called:

**routing-active / transport-weak**

Do not call it "mirage" or "failed grounding" until additional evidence supports that interpretation.

---

## 18. Choosing the low-transport threshold

During discovery:

1. Examine the \(G_t^{causal}\) distribution within retrieval-positive events.
2. Determine whether it is:
   - continuous,
   - bimodal,
   - strongly skewed,
   - or effectively saturated high.
3. Choose \(\tau_G\) only after characterizing this distribution.

Preferred approach:

- define a low-transport region using discovery quantiles or mixture structure,
- then freeze \(\tau_G\) before confirmation.

Do not use a threshold chosen to maximize later reinjection gains.

That would make the intervention circular.

---

## 19. Part III — Does the weak-transport state still contain usable visual semantics?

This is the key reinjection prerequisite.

For events satisfying:

\[
R_t > \tau_R,
\qquad
G_t^{causal} < \tau_G,
\]

test whether the Value pathway still contains semantically useful visual information.

### Value-only semantic counterfactual test

Use matched original/counterfactual images with a local semantic edit.

At the fixed 2B-native reasoning prefix:

- keep reasoning history fixed,
- preserve current query/routing state,
- replace or patch the relevant visual **Value** representation from the counterfactual condition while keeping the appropriate routing variables fixed,
- compare against matched sham Value intervention.

Measure movement in the upcoming evidence preference.

Define:

\[
S_t^{V}
=
\Delta_{\text{semantic Value}}
-
\Delta_{\text{sham Value}}.
\]

A positive \(S_t^V\) indicates that usable semantic information remains available in the Value pathway.

---

## 20. The decisive reinjection-candidate phenotype

The strongest candidate state is:

\[
\boxed{
R_t \text{ high}
+
G_t \text{ low}
+
S_t^V \text{ positive}
}
\]

Interpretation:

1. the model is actively engaging the visual channel,
2. the native visual contribution is weak,
3. but the Value pathway still contains usable image semantics.

Only this state provides a strong mechanistic rationale for Value reinjection.

---

## 21. Primary analyses

### Analysis A — Which passive signal best predicts active retrieval?

Compare:

- attention only,
- QK only,
- QK + attention,
- QK + attention + temporal/concentration features.

Primary hard test:

\[
T \text{ vs mention-only } M.
\]

### Analysis B — Does a routing-active / transport-weak region actually exist?

Plot retrieval-positive events in:

\[
(R_t,\;G_t^{causal})
\]

space.

Quantify:

- number of events,
- number of independent image/problem families,
- fraction of retrieval-positive events,
- stability on confirmation.

### Analysis C — Can cheap transport metrics predict causal weakness?

Evaluate:

\[
T_t^{cheap}
\rightarrow
G_t^{causal}.
\]

Report correlation and classification performance for low-\(G\) identification.

The preferred deployable gate is the cheapest metric that remains stable on held-out confirmation.

### Analysis D — Is usable Value semantics preserved in low-\(G\) states?

For high-\(R\), low-\(G\) events:

\[
S_t^V
=
\Delta_{\text{semantic Value}}
-
\Delta_{\text{sham Value}}.
\]

This is the main scientific gate for proceeding to reinjection.

---

## 22. Preregistered success gates

### Gate 0 — Technical validity

All instrumentation and causal intervention checks pass on Qwen3-VL-2B-Thinking.

If not: stop and repair platform/model instrumentation.

### Gate 1 — Retrieval proxy

On held-out confirmation:

- retrieval-required vs hard-negative AUROC \(\ge 0.80\),
- mention-only FPR \(\le 0.20\) at the frozen operating point,
- joint QK/attention proxy clearly outperforms lexical/position baselines.

If this fails:

- do not claim an online retrieval detector,
- do not build a test-time trigger from the failed proxy.

### Gate 2 — Nontrivial weak-transport cohort

Require at least:

- **24 high-\(R\), low-\(G\) events**
- from **at least 12 independent image/problem families**

across discovery + confirmation,

with the state remaining visible after the threshold is frozen.

If this fails, Value reinjection is not sufficiently motivated as a selective intervention.

### Gate 3 — Usable Value semantics

Within the frozen high-\(R\), low-\(G\) cohort:

- semantic Value intervention exceeds matched sham in at least 70% of evaluable events,
- family-level median semantic-minus-sham effect \(>0\),
- bootstrap 95% CI for the family-level effect excludes 0.

If this passes, proceed to a separate reinjection stage.

If it fails, the bottleneck is unlikely to be simple under-utilization of an otherwise usable Value carrier.

---

## 23. What a null result does NOT rule out

### Null A — Passive proxy fails

Does **not** show that retrieval demand does not exist.

Possible explanations:

- 2B retrieval phenotype differs from 4B,
- signal is distributed across layers,
- absolute attention/QK scales are unstable,
- current features are insufficient,
- semantic demand exists upstream but passive retrieval phenotype is not linearly separable.

This null closes the proposed online trigger, not the causal demand mechanism itself.

### Null B — High-\(R\), low-\(G\) states are rare

Does **not** show that Value is unimportant.

It may mean that when 2B enters an active retrieval state, Value transport is usually already sufficient.

This would argue **against selective Value reinjection** as a useful intervention.

### Null C — Low-\(G\) states lack usable Value semantics

Possible interpretations:

- representation/extraction failed upstream,
- wrong source was retrieved,
- required semantics were never encoded in the relevant Value state,
- native routing and transport cannot be separated in the proposed way.

This is a strong reason **not** to continue with Value reinjection.

### Null D — Cheap transport metric fails but causal \(G\) works

This means the mechanistic state may exist, but the inexpensive online gate is not yet available.

A later intervention could still use an expensive two-pass causal gate as a proof of concept, but deployment claims should remain limited.

---

## 24. Why this stage has high marginal value

This stage is not another descriptive attention analysis.

It answers three unresolved questions that directly determine whether the next intervention is scientifically justified:

1. Can the 4B retrieval phenotype be observed online in a second model scale?
2. Does retrieval engagement separate from causal evidence transport?
3. When native transport is weak, is useful visual semantic content still present in the Value pathway?

Only if all three are sufficiently supported does Visual Value reinjection become a mechanism-derived intervention rather than an arbitrary steering trick.

---

## 25. Explicit stopping rule

Do **not** proceed automatically to reinjection.

Proceed only if:

\[
\boxed{
\text{online retrieval proxy works}
+
\text{high-R/low-G states exist}
+
\text{usable Value semantics remain}
}
\]

If one of these three links fails strongly, stop the reinjection branch and preserve the result as a mechanistic boundary.

---

## 26. If all gates pass: next stage

The next stage should test:

### Retrieval-Triggered Visual Value Reinjection

At steps satisfying the frozen controller:

\[
R_t > \tau_R
\quad\land\quad
T_t^{cheap}<\tau_T,
\]

apply a calibrated dose:

\[
h_t'
=
h_t
+
\lambda C_t^V.
\]

Compare against:

- no intervention,
- always reinject,
- retrieval-triggered only,
- random timing,
- norm-matched random vector,
- irrelevant/shuffled visual Value,
- nonvisual Value reinjection.

Primary mechanistic endpoint:

\[
\text{visual counterfactual followability}
\]

Secondary endpoints:

- local visual-claim accuracy,
- causal visual dependence,
- final-answer accuracy,
- collateral damage on already-grounded events.

That intervention is **not part of Stage 8A**.

---

## 27. Minimal paper-facing outcome table

| Question | Positive result | Paper implication |
|---|---|---|
| Can active retrieval be passively detected? | QK+attention separates retrieval from mention-only | Retrieval mechanism is online-observable |
| Do high-\(R\), low-\(G\) states exist? | Stable cohort across families | Retrieval engagement and causal transport can dissociate |
| Is useful visual semantics still in Value? | Semantic Value swap > sham | Weak transport may under-utilize available visual content |
| Do all three pass? | Yes | Reinjection is mechanistically justified |
| Any major gate fails? | No-go | Stop intervention branch; retain mechanistic boundary |

---

## 28. Final decision criterion

The stage is successful only if it creates a non-circular, held-out test-time rule of the form:

\[
\boxed{
\text{retrieval proxy says “vision is active”}
\quad\land\quad
\text{transport gate says “native visual influence is weak”}
}
\]

and the selected states demonstrably retain usable visual semantics in the Value pathway.

The desired output is not merely a classifier.

It is a mechanistically justified answer to:

> **When should the model's native visual Value pathway be strengthened?**
