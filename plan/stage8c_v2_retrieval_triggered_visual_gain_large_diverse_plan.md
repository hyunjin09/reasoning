# Stage 8C v2 — Retrieval-Triggered Visual Contribution Gain: Diverse Dose–Response and Large Held-Out MathVision Benchmark

## 0. One-line objective

Test whether the **active visual-retrieval state discovered in Stage 8A** is a useful test-time control point by selectively amplifying the model's **native visual Value-mediated attention contribution** at retrieval-episode onset, and determine whether the effect generalizes across a **large, diverse, family-disjoint MathVision cohort**.

The central question is:

\[
\boxed{
\textbf{Does strengthening native visual evidence specifically at active retrieval moments improve difficult multimodal reasoning across diverse visual-reasoning families?}
}
\]

This is a **bounded empirical intervention benchmark**.

It does **not** assume that insufficient Value magnitude is the natural cause of errors.

---

# 1. Why this revised design is necessary

A small intervention study could easily produce a noisy or subtype-specific accuracy increase.

To make the intervention result paper-worthy, we need to distinguish:

\[
\boxed{
\text{real general performance effect}
}
\]

from:

\[
\boxed{
\text{sampling noise / repeated template effect / narrow subtype effect}
}
\]

Therefore Stage 8C v2 increases both:

1. **sample size**, and
2. **effective diversity / family independence**.

The experiment must answer not only:

> Does accuracy improve?

but also:

> **Does the improvement survive across different visual-reasoning types and independent image families?**

---

# 2. Mechanistic basis

The intervention uses three established findings:

1. active visual retrieval is detectable online;
2. current reasoning query determines visual addressing;
3. retrieved visual semantic content is Value-rich.

At retrieval onset, define the native visual attention contribution:

\[
C_{\ell,t}^{V}
=
W_{O,\ell}
\left(
\operatorname{Concat}_{h}
\sum_{j\in V}
a_{\ell,h,t,j}V_{\ell,h,j}
\right)
\]

and apply:

\[
\boxed{
h_{\ell,t}^{post}
\leftarrow
h_{\ell,t}^{post}
+
(g-1)C_{\ell,t}^{V}
}
\]

for the verified 2B functional late retrieval window:

\[
\boxed{
\text{layers 19--22}
}
\]

No target ROI or answer information is supplied.

---

# 3. Paper claim if successful

The main claim is:

> **Active visual retrieval exposes a useful test-time control point: selectively strengthening the model's native visual contribution at retrieval onset improves held-out MathVision performance across diverse visual-reasoning families.**

A stronger timing-specific claim is allowed only if:

\[
\text{retrieval-triggered gain}
>
\text{matched random-timing gain}.
\]

A generality claim is allowed only if improvement is not driven by a single dominant subtype or repeated visual family.

---

# 4. What this stage must NOT claim

A positive result does not establish:

- that natural errors are caused by insufficient Value magnitude;
- that Value gain corrects the Block 2 routing phenotype;
- that stronger visual transport is universally optimal;
- that every subtype benefits equally;
- that the intervention generalizes beyond Qwen3-VL-2B-Thinking / MathVision without replication.

---

# 5. What a null does NOT rule out

A null result does not invalidate:

- reasoning-conditioned retrieval,
- online retrieval observability,
- Value-rich semantic transport.

Possible explanations:

- native visual transport is already calibrated;
- errors are dominated by routing, extraction, or downstream integration;
- this specific gain implementation is not the right intervention;
- benefit exists only in a narrow subgroup.

A clean held-out null should stop this intervention branch rather than trigger post-hoc retuning.

---

# 6. Model and canonical benchmark protocol

## Model

**Qwen3-VL-2B-Thinking**

## MathVision generation protocol

- BF16
- temperature = 1.0
- top_p = 0.95
- top_k = 20
- repetition penalty = 1.0
- presence penalty = 0.0
- max_new_tokens = 40960
- normal EOS stopping
- frozen MathVision chat/pixel preprocessing
- frozen Qwen-compatible local answer-scoring adapter

---

# 7. Frozen retrieval trigger

Use the Stage 8A detector unchanged.

\[
\boxed{
\tau_R = 0.5478025980771918
}
\]

Use the frozen gap-4 retrieval-episode definition.

Primary intervention timing:

\[
\boxed{
\text{first active token of each retrieval episode}
}
\]

Do not intervene at every active token in the primary policy.

---

# 8. Two-pass online execution

At each decoding step:

## Pass 1 — probe

Run the normal forward pass and compute \(R_t\).

Do not sample yet.

## If no new retrieval episode starts

- sample from native logits;
- commit native cache.

## If a retrieval episode starts

- discard the probe-pass current-token cache update;
- rerun the same prefix with gain intervention;
- sample exactly once from intervention logits;
- commit intervention cache/state.

No future-token information is used.

Sampling RNG is consumed once per generated token.

---

# 9. Intervention dose

Effective visual gain:

\[
\boxed{
g \in \{1.00,\;1.25,\;1.50,\;2.00\}
}
\]

Interpretation:

- \(g=1.00\): native baseline
- \(g=1.25\): 25% additional native visual contribution
- \(g=1.50\): 50% additional
- \(g=2.00\): 100% additional

Do not add new intermediate gains after results are opened.

A \(3.0\times\) arm is not preregistered.

---

# 10. Stage structure

Stage 8C v2 has four parts:

1. **8C.0 — Technical validation**
2. **8C.1 — Diverse 128-item development dose calibration**
3. **8C.2 — Diverse 512-item held-out confirmation**
4. **8C.3 — 256-item timing-specificity control**

A preregistered extension to 1024 total held-out items is allowed only under the narrow condition defined later.

---

# 11. Cohort independence rules

The Stage 8C cohorts must be disjoint from:

- Stage 8B 256-item discovery cohort;
- Block 3A seed-expansion base items;
- Block 3A new rollout items;
- any prior intervention-development items.

Development and held-out test must also be mutually disjoint.

---

# 12. Family independence

The unit of visual diversity is not only item ID.

Create a **visual-family ID** that groups:

- exact duplicate images;
- resized/re-rendered versions of the same figure;
- same underlying diagram with trivial formatting changes;
- known benchmark variants sharing the same visual construction.

Require:

\[
\boxed{
\text{no visual family overlaps between dev and test}
}
\]

where family metadata permit identification.

If uncertain whether two samples are the same visual family, conservatively group them.

---

# 13. Diversity dimensions

Cohort construction should preserve broad coverage across available MathVision metadata.

Stratify where metadata are reliable by:

- MathVision subject/category;
- geometry / spatial / counting / measurement / graph-chart / binding-like problem type where available;
- answer format:
  - multiple choice,
  - numeric,
  - symbolic/expression;
- difficulty metadata;
- visual density / number of candidate visual entities where available.

Do not invent missing metadata.

If a field is unavailable, record it as missing rather than infer it post hoc from outcomes.

---

# 14. Retrieval-complexity diversity

If available **without using intervention outcomes**, characterize items by baseline/native retrieval complexity:

- no/very few retrieval episodes;
- single/few retrieval episodes;
- repeated retrieval;
- long reasoning with recurrent visual access.

This may be used for **post-hoc heterogeneity analysis**, but main test membership must not be selected based on expected intervention benefit.

Do not enrich the main held-out test for intervention-friendly samples.

---

# 15. Stage 8C.0 — Technical validation

Before scientific runs, verify:

### V1 — Gain-1 exactness

\[
g=1.0
\]

reproduces native inference within the frozen execution-path tolerance.

Prefer exact equality in the intervention code path.

### V2 — Non-trigger exactness

No retrieval onset → intervention-enabled path equals native path.

### V3 — Visual decomposition

\[
C^V + C^{nonV}
\]

reconstructs native attention output within expected numerical tolerance.

### V4 — Cache validity

Post-intervention continuation uses intervention-state cache.

### V5 — Trigger validity

Online trigger reproduces frozen retrieval detection on audited prefixes.

### V6 — No oracle leakage

The online intervention must not access:

- benchmark answer,
- ROI labels,
- T/M/U labels,
- L+/L− labels,
- future tokens.

If any check fails, stop.

---

# 16. Stage 8C.1 — Diverse development cohort

Freeze:

\[
\boxed{
128 \text{ new MathVision items}
}
\]

for dose calibration.

The 128 items should be stratified to cover the available benchmark diversity.

Development-set construction happens **before intervention outcomes are opened**.

---

# 17. Development diversity requirements

Where possible, ensure:

- no duplicate visual families;
- no single major subtype dominates the cohort;
- multiple difficulty levels;
- multiple answer formats;
- both simpler and denser visual layouts.

If exact balance is impossible, preserve benchmark-proportional sampling and report the realized distribution.

Do not oversample a subtype because early interventions look promising there.

---

# 18. Development dose arms

Run every dev item under:

\[
\boxed{
g=1.00,\;1.25,\;1.50,\;2.00
}
\]

using the same item-level sampling seed across doses.

Primary timing:

- retrieval-episode onset only.

---

# 19. Development primary outcomes

For each dose report:

- benchmark accuracy;
- W→C;
- C→W;
- unresolved transitions;
- EOS rate;
- cap rate;
- mean/median reasoning length;
- intervention count;
- runtime overhead.

Also report results by major subtype when each subgroup has adequate size.

---

# 20. Development diversity-aware dose selection

Select exactly one non-native dose \(g^\*\).

Primary criterion:

\[
\boxed{
\text{highest overall development accuracy}
}
\]

Tie-breakers:

1. larger:
   \[
   W\rightarrow C - C\rightarrow W
   \]
2. no major represented subtype with severe degradation;
3. smaller cap-rate increase;
4. smaller reasoning-length increase;
5. smaller gain.

---

# 21. "No catastrophic subtype harm" rule

For any subtype with at least 15 development examples, flag severe harm if intervention accuracy drops by:

\[
\boxed{
>10 \text{ percentage points}
}
\]

relative to native baseline.

If the nominal best dose causes severe harm in multiple sufficiently represented subtypes, select the next-best safer dose or stop if no dose is acceptable.

This rule is a safety/robustness criterion, not evidence of subtype-specific efficacy.

---

# 22. Development no-go gate

Stop before held-out confirmation if all non-native doses satisfy any of the following overall patterns:

- no positive accuracy change;
- C→W >= W→C;
- cap rate rises by >10 percentage points;
- median reasoning length rises by >50% without meaningful accuracy gain;
- benefit is entirely concentrated in one narrow subtype while major represented subtypes degrade.

Do not introduce new doses after seeing development outcomes.

---

# 23. Stage 8C.2 — Diverse held-out test cohort

Freeze:

\[
\boxed{
512 \text{ new MathVision items}
}
\]

disjoint from all prior discovery/dev items and visual families.

This is the primary confirmatory benchmark.

---

# 24. Test-cohort diversity

The 512 held-out items should maximize **effective independent coverage**, not merely raw count.

Require:

- visual-family disjointness from dev and prior stages;
- broad benchmark subtype coverage;
- broad difficulty coverage;
- multiple answer formats;
- no outcome-based selection.

If benchmark composition is naturally imbalanced, preserve the benchmark distribution and use subgroup analyses rather than artificially constructing an unrepresentative balanced set.

---

# 25. Main held-out arms

Run all 512 items under:

### C0 — Native baseline

\[
g=1.0
\]

### C1 — Retrieval-triggered frozen gain

\[
g=g^\*
\]

Use the same item-level sampling seed across C0 and C1.

No test-set retuning.

---

# 26. Primary held-out endpoint

\[
\boxed{
\Delta Acc
=
Acc(C1)-Acc(C0)
}
\]

Report:

- C0 accuracy;
- C1 accuracy;
- percentage-point change;
- W→C;
- C→W;
- unresolved transitions;
- paired item bootstrap 95% CI;
- visual-family-clustered bootstrap 95% CI;
- paired binary test such as McNemar.

The **family-clustered interval is mandatory** when multiple items share a family.

---

# 27. Why family-clustered inference is required

If many test samples are closely related visual variants, item-level confidence intervals can be artificially narrow.

Therefore report both:

\[
\boxed{
\text{item-level uncertainty}
}
\]

and:

\[
\boxed{
\text{visual-family-level uncertainty}
}
\]

The paper claim should use the more conservative interpretation when they disagree.

---

# 28. Held-out success gate

The intervention is confirmed as performance-improving only if:

1. \(\Delta Acc>0\);
2. paired item-level 95% CI excludes zero;
3. family-clustered 95% CI excludes zero;
4. W→C > C→W;
5. cap rate worsens by no more than 5 percentage points;
6. median reasoning length increases by no more than 25%, unless the accuracy gain is clearly substantial;
7. effect is not explained entirely by one single major subtype.

---

# 29. Subtype heterogeneity analysis

After the primary global test, report effect by sufficiently represented subgroup:

- subject/category;
- problem type;
- answer format;
- difficulty bin;
- retrieval-complexity bin.

For each subgroup report:

- baseline accuracy;
- intervention accuracy;
- W→C;
- C→W;
- sample size.

These are secondary.

Do not claim subgroup efficacy without adequate sample size and correction/replication.

---

# 30. Diversity robustness criterion

A global positive result is stronger if:

- most well-represented subgroups have nonnegative point estimates;
- no major subgroup shows large reproducible harm;
- the positive effect survives removal of the single best-performing subtype.

Perform a leave-one-major-subtype-out sensitivity analysis.

This is not a new primary endpoint, but it guards against a narrow-template effect.

---

# 31. Stage 8C.3 — Timing-specificity control

Freeze:

\[
\boxed{
256 \text{ items from the held-out test set}
}
\]

before opening test outcomes.

Run:

### C2 — Matched random-timing gain

Use the same \(g^\*\).

For each item:

- obtain baseline retrieval-onset count \(K_i\);
- choose \(K_i\) non-retrieval token positions;
- exclude positions within ±16 tokens of baseline retrieval episodes;
- phase-match random positions to retrieval positions where feasible;
- freeze timing schedule before C2 run.

---

# 32. Timing-specificity endpoint

Compare:

\[
C1 \text{ vs } C2
\]

on the same 256 items.

Interpretation:

## If:

\[
C1 > C2
\]

and C1 improves over baseline:

> retrieval onset is a useful intervention timing signal.

## If:

\[
C1 \approx C2 > C0
\]

> visual amplification may help, but retrieval timing is not established as necessary.

## If:

\[
C2 > C1
\]

> retrieval-aware timing is not supported.

---

# 33. Local-read audit

Freeze an outcome-independent subset of:

\[
\boxed{
128 \text{ test items}
}
\]

for semantic review.

Compare C0 vs C1 around matched retrieval-triggered episodes.

Annotate:

- T/M/U
- L+/L−/L?
- whether local visual claim changed
- whether correction preceded final-answer rescue

Secondary question:

\[
P(L+|C1) > P(L+|C0)?
\]

This helps determine whether any final accuracy gain is plausibly mediated through better visual reading.

---

# 34. Rescue and collateral-damage analysis

## W→C cases

For a frozen reviewed subset, inspect:

- local visual-claim change;
- timing of intervention relative to correction;
- reasoning-length change;
- retrieval recurrence change.

## C→W cases

Inspect:

- whether correct visual evidence was distorted;
- whether wrong source was amplified;
- whether reasoning became longer or more repetitive;
- whether a downstream error, rather than visual read, caused regression.

Do not hide collateral damage behind aggregate accuracy.

---

# 35. Dose-response figure

Development figure must include:

\[
g =
1.00,\;1.25,\;1.50,\;2.00
\]

with:

- overall accuracy;
- W→C − C→W;
- cap rate;
- reasoning length.

Also show subtype point estimates for sufficiently represented subgroups in a supplementary figure.

---

# 36. Preregistered extension to 1024 held-out items

A larger test extension is allowed only under the following condition:

After the first 512 held-out items:

1. \(\Delta Acc > 0\);
2. W→C > C→W;
3. the item-level or family-level CI still includes zero;
4. no major safety/collateral-damage gate fails;
5. the observed effect is small enough that 512 is plausibly underpowered rather than null.

Then, and only then, freeze an additional:

\[
\boxed{
512 \text{ new held-out items}
}
\]

to reach:

\[
\boxed{
1024 \text{ total test items}
}
\]

using the same frozen \(g^\*\), trigger, and analysis.

Do not extend if the 512-item point estimate is zero/negative.

Do not use the first 512 outcomes to change dose or policy.

---

# 37. Extension interpretation

The 1024 extension is **precision expansion**, not a new experiment.

Combine the two 512-item test blocks only if:

- same policy;
- same model/protocol;
- same scoring;
- same family rules;
- no parameter changes.

Report both:

- first-512 result;
- combined-1024 result.

Do not hide a null first block behind the combined estimate.

---

# 38. Statistical unit

Primary unit:

\[
\boxed{
\text{MathVision item}
}
\]

Clustered robustness unit:

\[
\boxed{
\text{visual family}
}
\]

Do not treat:

- tokens,
- retrieval events,
- intervention events

as independent samples for benchmark-performance inference.

---

# 39. Multiplicity discipline

Primary confirmatory test:

\[
\boxed{
C1 \text{ vs } C0
}
\]

on the 512-item held-out cohort.

Secondary:

- C1 vs C2 timing specificity;
- subgroup heterogeneity;
- local-read audit;
- cap rate;
- reasoning length;
- trajectory dynamics.

The intervention story fails if the primary held-out result fails.

---

# 40. Required controls

Minimum:

- native \(g=1.0\);
- retrieval-triggered frozen \(g^\*\);
- matched random-timing \(g^\*\);
- technical no-op exactness.

No online use of:

- target ROI,
- benchmark answer,
- T/M/U labels,
- L+/L− labels.

---

# 41. Compute-efficient execution order

1. Freeze dev128 and test512 manifests with visual-family IDs and subtype metadata.
2. Run 8C.0 validity.
3. Run four-dose dev128.
4. Freeze \(g^\*\).
5. If dev gate passes, run test512 C0/C1.
6. Evaluate primary effect and family-clustered uncertainty.
7. Run/complete timing-control256.
8. Run local-read audit128.
9. Decide whether:
   - intervention story is confirmed;
   - 1024 precision extension is justified;
   - or intervention branch stops.

---

# 42. Outcome matrix

## Outcome A — Strong positive

Conditions:

- test512 accuracy improves;
- item/family CIs exclude zero;
- W→C > C→W;
- no major subtype-specific harm;
- C1 > C2.

Supported:

> active retrieval is a useful, timing-specific control point.

---

## Outcome B — Positive but timing-unspecific

C1 improves but:

\[
C1 \approx C2.
\]

Supported:

> visual amplification helps.

Not supported:

> retrieval timing is essential.

---

## Outcome C — Small positive, uncertain CI

If preregistered extension conditions pass:

- extend to 1024.

No policy retuning.

---

## Outcome D — Local reads improve but final accuracy does not

Interpretation:

> visual reading can be strengthened, but downstream reasoning remains the dominant bottleneck.

Next:

- Block 3B.

---

## Outcome E — Null or harmful

Stop intervention branch.

Return to:

**Block 3B — Post-Read Recovery / Wandering Dynamics**

---

# 43. Required artifacts

Produce:

1. `stage8c_v2_family_manifest.json`
2. `stage8c_v2_dev128_manifest.json`
3. `stage8c_v2_test512_manifest.json`
4. `stage8c_v2_technical_validation.json`
5. `stage8c_v2_dev_dose_results.json`
6. `stage8c_v2_dose_freeze.json`
7. `stage8c_v2_test_primary_accuracy.json`
8. `stage8c_v2_family_clustered_inference.json`
9. `stage8c_v2_subtype_heterogeneity.json`
10. `stage8c_v2_timing_control256.json`
11. `stage8c_v2_local_read_audit128.parquet`
12. `stage8c_v2_rescue_collateral_review.json`
13. `stage8c_v2_runtime_overhead.json`
14. optional `stage8c_v2_extension512_manifest.json`
15. optional `stage8c_v2_combined1024_result.json`
16. `stage8c_v2_summary.md`

---

# 44. Key figures

## Figure 1 — Dev128 dose-response

Accuracy, W→C−C→W, cap rate, reasoning length across:

\[
1.00,\;1.25,\;1.50,\;2.00
\]

## Figure 2 — Test512 paired accuracy

Native vs frozen gain.

## Figure 3 — Family-clustered robustness

Item-level vs family-level effect uncertainty.

## Figure 4 — Subtype heterogeneity

Effect across major problem/visual types.

## Figure 5 — Timing specificity

Native vs retrieval-triggered vs matched random timing.

## Figure 6 — Rescue vs collateral damage

W→C and C→W trajectories.

## Figure 7 — Local-read audit

L+/L− composition under baseline vs intervention.

---

# 45. Final decision criterion

Stage 8C v2 succeeds only if the intervention moves from:

\[
\boxed{
\text{mechanistically plausible control idea}
}
\]

to:

\[
\boxed{
\textbf{a frozen retrieval-triggered visual gain that improves held-out MathVision performance across diverse, independent visual families with acceptable collateral damage}
}
\]

The strongest result additionally requires:

\[
\boxed{
\text{retrieval-triggered gain}
>
\text{matched random-timing gain}
}
\]

showing that both:

- **how much** visual evidence is strengthened, and
- **when** it is strengthened

matter.

If this criterion is not met, stop the intervention branch and return to:

\[
\boxed{
\textbf{Block 3B — Post-Read Recovery / Wandering Dynamics}
}
\]
