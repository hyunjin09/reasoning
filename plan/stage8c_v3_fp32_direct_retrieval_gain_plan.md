# Stage 8C v3 — Direct FP32 Retrieval-Triggered Visual Gain on MathVision

## 0. Revision status

This plan **supersedes the BF16 decomposition-repair path for Stage 8C**.

Per the current decision, do **not** run any additional:

- BF16 repair experiment,
- BF16→FP32 transfer study,
- detector transfer audit,
- FP32 retrieval re-calibration,
- pre-efficacy V1–V6 validation bundle.

Instead, proceed directly with the **entire Qwen3-VL-2B-Thinking model in FP32** for both baseline and intervention arms.

The scientific comparison is therefore always:

\[
\boxed{
\text{FP32 native baseline}
\quad\text{vs}\quad
\text{FP32 retrieval-triggered visual gain}
}
\]

The frozen Stage 8A retrieval detector and threshold are reused **as-is**, without FP32 re-calibration.

---

# 1. One-line objective

Determine whether selectively strengthening the model's native visual attention contribution at **frozen active-retrieval moments** improves MathVision performance when the entire model runs in FP32.

Core question:

\[
\boxed{
\textbf{Does retrieval-triggered visual gain improve difficult multimodal reasoning in FP32 Qwen3-VL-2B-Thinking?}
}
\]

This stage is an **empirical intervention benchmark**.

It is not a test of BF16 equivalence.

---

# 2. Why FP32 is now the canonical intervention regime

The BF16-preserving implementation was stopped because splitting visual/nonvisual source reductions introduced independent BF16 rounding that violated the frozen reconstruction bound.

The present decision is to avoid that low-precision decomposition problem by running the **entire intervention experiment in FP32**.

This changes the execution regime but keeps the intervention concept unchanged:

\[
\text{detect native retrieval}
\rightarrow
\text{strengthen native visual contribution}
\rightarrow
\text{measure task performance}
\]

No claim of BF16/FP32 trajectory equivalence is required for this stage.

---

# 3. Interpretation boundary

Because the retrieval detector was calibrated previously and is reused without FP32 transfer validation, a positive result may support:

> **A frozen retrieval-aware policy improves MathVision performance in FP32 Qwen3-VL-2B-Thinking.**

It must **not** be phrased as:

> the BF16 retrieval detector was revalidated in FP32,

or:

> the FP32 retrieval state is numerically identical to the BF16 retrieval state.

The detector is treated as a fixed control policy inherited from prior work.

---

# 4. Model and inference protocol

## Model

**Qwen3-VL-2B-Thinking**

## Precision

Run the **entire model in FP32**.

Use FP32 for:

- model weights,
- attention Q/K/V computation,
- attention probabilities,
- Value accumulation,
- output projection,
- residual stream,
- MLP computation,
- KV cache,
- logits,

where supported by the implementation.

Do not intentionally cast the scientific path back to BF16.

If an unavoidable framework operation internally uses another precision, record it explicitly.

---

# 5. MathVision generation protocol

Keep the benchmark generation protocol unchanged except for model precision:

- temperature = 1.0
- top_p = 0.95
- top_k = 20
- repetition penalty = 1.0
- presence penalty = 0.0
- max_new_tokens = 40960
- normal EOS stopping
- frozen MathVision prompt/chat formatting
- frozen image/pixel preprocessing
- frozen Qwen-compatible local answer-scoring adapter

No answer extraction rule changes.

---

# 6. Frozen retrieval trigger

Reuse the Stage 8A detector **without refitting or recalibration**.

Frozen threshold:

\[
\boxed{
\tau_R = 0.5478025980771918
}
\]

Use the frozen gap-4 retrieval-episode logic.

Primary intervention timing:

\[
\boxed{
\text{first active token of each retrieval episode}
}
\]

Do not use benchmark answer, ROI labels, T/M/U labels, L+/L− labels, or future tokens online.

---

# 7. Online trigger implementation

At each decoding step:

1. run the normal FP32 forward needed to compute the frozen retrieval score;
2. do not sample yet;
3. if no new retrieval episode starts:
   - use native FP32 logits;
4. if a new retrieval episode starts:
   - apply the visual-gain modification for that forward;
   - sample from the modified logits;
   - continue from the modified FP32 state/cache.

The same trigger rule is used for every dose.

---

# 8. Visual contribution definition

For layer \(\ell\), current token \(t\), define:

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

computed in FP32.

Use the established late retrieval window:

\[
\boxed{
\text{layers 19--22}
}
\]

Do not tune head subsets during Stage 8C v3.

---

# 9. Gain intervention

Apply:

\[
\boxed{
h_{\ell,t}^{post}
\leftarrow
h_{\ell,t}^{post}
+
(g-1)C_{\ell,t}^{V}
}
\]

at retrieval-episode onset.

Dose grid:

\[
\boxed{
g \in \{1.00,\;1.25,\;1.50,\;2.00\}
}
\]

Interpretation:

- 1.00× = FP32 native baseline
- 1.25× = +25% visual contribution
- 1.50× = +50%
- 2.00× = +100%

Do not add new gains after outcomes are opened.

---

# 10. No pre-efficacy transfer/audit stage

Do **not** run a separate:

- FP32 transfer cohort,
- FP32 detector audit,
- BF16-vs-FP32 behavior comparison,
- decomposition-validation cohort,
- pre-dose semantic review.

Proceed directly to the frozen development intervention experiment.

Operational failures such as crash/OOM are execution failures, not scientific gates.

---

# 11. Cohort design

Retain the large/diverse Stage 8C v2 structure.

## Development

\[
\boxed{
128 \text{ new MathVision items}
}
\]

## Held-out test

\[
\boxed{
512 \text{ new MathVision items}
}
\]

## Timing-specificity subset

\[
\boxed{
256 \text{ test items}
}
\]

## Local-read audit subset

\[
\boxed{
128 \text{ test items}
}
\]

Reuse already frozen cohort manifests if they remain available and untouched.

Do not redraw cohorts because precision changed.

---

# 12. Independence from prior research data

Dev/test items must remain disjoint from:

- Stage 8B 256-item discovery cohort,
- Block 3A base items,
- Block 3A additional seeded rollouts,
- any prior intervention-development items.

No outcome-conditioned replacement.

---

# 13. Visual-family independence

Preserve the existing conservative family rules.

Do not allow dev/test overlap for:

- exact duplicate images,
- rescaled versions,
- known repeated templates,
- known aliases,
- identified connected visual families.

When uncertain, prefer conservative grouping.

---

# 14. Diversity requirement

The experiment should retain broad MathVision coverage across available metadata:

- subjects/categories,
- difficulty levels,
- multiple-choice and free-response formats,
- diverse diagram/visual structures where metadata exist.

Do not restrict the benchmark to retrieval-friendly or geometry-only examples.

The goal is to test whether the intervention survives diverse reasoning conditions.

---

# 15. Stage 8C.1 — FP32 development dose response

Run every dev128 item under all four doses:

\[
g=1.00,\;1.25,\;1.50,\;2.00
\]

Use the same item-level sampling seed across dose arms.

The FP32 \(g=1.00\) arm is the canonical baseline.

---

# 16. Development primary outcomes

For every dose report:

- benchmark accuracy,
- wrong → correct,
- correct → wrong,
- unresolved transitions,
- EOS rate,
- cap rate,
- mean reasoning length,
- median reasoning length,
- retrieval episode count,
- intervention count,
- runtime / GPU-hours.

Do not compare efficacy to prior BF16 accuracy as the primary test.

---

# 17. Development dose-selection rule

Choose exactly one non-native dose:

\[
g^\*
\]

using:

1. highest overall dev128 accuracy;
2. then largest:
   \[
   W\rightarrow C - C\rightarrow W
   \]
3. then lower cap-rate increase;
4. then lower reasoning-length increase;
5. then smaller gain.

Freeze \(g^\*\) before opening held-out intervention outcomes.

---

# 18. Development safety / no-go rule

Stop the intervention branch before test512 if all non-native doses show no useful net effect.

Treat as no-go if all doses satisfy one or more of:

- accuracy \(\le\) FP32 baseline;
- C→W \(\ge\) W→C;
- cap rate increases by >10 percentage points;
- median reasoning length increases by >50% without meaningful accuracy gain;
- improvement is driven entirely by a very narrow subgroup while multiple major subgroups degrade.

Do not introduce new dose values.

---

# 19. Development dose-response interpretation

## Intermediate optimum

Example:

\[
1.0 < 1.25 < 1.5 > 2.0
\]

Interpretation:

> moderate visual amplification is useful, but excessive gain produces collateral damage.

## Monotonic positive

Interpretation:

> stronger visual contribution remains beneficial through the tested range.

Do not infer a natural under-transport failure without further evidence.

## Flat

Interpretation:

> this gain variable is not an effective performance controller.

## Negative

Stop intervention branch.

---

# 20. Stage 8C.2 — FP32 held-out confirmation

Run all 512 held-out items under:

### C0 — FP32 native

\[
g=1.0
\]

### C1 — FP32 retrieval-triggered gain

\[
g=g^\*
\]

Use the same item-level sampling seed across C0 and C1.

No test-set retuning.

---

# 21. Primary confirmatory endpoint

\[
\boxed{
\Delta Acc
=
Acc(C1)-Acc(C0)
}
\]

Report:

- FP32 baseline accuracy,
- FP32 intervention accuracy,
- percentage-point difference,
- W→C,
- C→W,
- unresolved transitions,
- paired item bootstrap 95% CI,
- visual-family-clustered bootstrap 95% CI,
- paired binary test such as McNemar.

The primary comparison is **within FP32**.

---

# 22. Confirmatory success gate

Count Stage 8C as a positive intervention result only if:

1. \(\Delta Acc>0\);
2. paired item-level 95% CI excludes zero;
3. visual-family-clustered 95% CI excludes zero;
4. W→C > C→W;
5. cap rate worsens by no more than 5 percentage points;
6. median reasoning length worsens by no more than 25%, unless accompanied by a clearly substantial accuracy gain;
7. effect is not entirely due to one major subtype.

---

# 23. Subtype robustness

After the global test, report intervention effect by sufficiently represented:

- subject/category,
- difficulty bin,
- answer format,
- visual/problem subtype where available.

These are secondary.

A global positive result is stronger if:

- most represented subgroups are nonnegative;
- no major subgroup shows large reproducible harm;
- leave-one-major-subtype-out sensitivity retains a positive overall effect.

---

# 24. Stage 8C.3 — Timing-specificity control

On the frozen 256-item test subset, compare:

### C1 — retrieval-triggered gain

against:

### C2 — matched random-timing gain

Use the same frozen \(g^\*\).

For each item:

- match the number of intervention events to the baseline retrieval-onset count;
- choose non-retrieval positions;
- exclude ±16 tokens around baseline retrieval episodes;
- phase-match positions where feasible;
- freeze schedules before running C2.

---

# 25. Timing-specificity interpretation

## If:

\[
C1 > C2
\]

and C1 improves over C0:

> active retrieval is a useful timing signal.

## If:

\[
C1 \approx C2 > C0
\]

> FP32 visual amplification may help, but retrieval timing is not established as critical.

## If:

\[
C2 > C1
\]

> the retrieval-timing story is not supported.

---

# 26. Local-read audit

Use the frozen 128-item semantic-review subset.

Compare FP32 C0 vs C1 around matched retrieval-triggered episodes.

Annotate:

- T/M/U,
- L+/L−/L?,
- local claim change,
- whether local correction precedes a final-answer rescue.

Secondary question:

\[
P(L+|C1) > P(L+|C0)?
\]

This is interpretive support, not the primary endpoint.

---

# 27. Rescue and collateral-damage analysis

For:

\[
C0=\text{wrong},\quad C1=\text{correct}
\]

inspect a frozen subset for:

- changed local visual claim,
- intervention timing relative to correction,
- retrieval recurrence,
- reasoning-length change.

For:

\[
C0=\text{correct},\quad C1=\text{wrong}
\]

inspect:

- altered correct visual evidence,
- amplification of an incorrect source,
- increased recurrence,
- increased reasoning length,
- downstream failure.

Do not hide C→W behind aggregate accuracy.

---

# 28. Optional 1024-item precision extension

After test512, allow an additional 512 held-out items only if:

1. point estimate is positive;
2. W→C > C→W;
3. item-level or family-level CI still includes zero;
4. safety gates pass;
5. the result appears underpowered rather than null.

Then freeze:

\[
512 \text{ additional held-out items}
\]

and combine to:

\[
1024 \text{ total test items}.
\]

No dose/trigger changes.

Do not extend if the first 512 are zero or negative.

---

# 29. Statistical unit

Primary independent unit:

\[
\boxed{
\text{MathVision item}
}
\]

Robustness cluster:

\[
\boxed{
\text{visual family}
}
\]

Do not treat tokens, retrieval episodes, or intervention events as independent accuracy samples.

---

# 30. Multiplicity discipline

Primary confirmatory test:

\[
\boxed{
C1 \text{ vs } C0
}
\]

on held-out test512.

Secondary:

- C1 vs C2 timing specificity,
- subgroup effects,
- local-read audit,
- cap rate,
- reasoning length,
- trajectory dynamics.

A failed primary accuracy result is not rescued by a secondary metric.

---

# 31. Compute / execution policy

Because the full model is FP32:

- record per-run peak GPU memory,
- record tokens/sec,
- record GPU-hours,
- preserve OOM/crash logs if any.

If FP32 execution is too memory-intensive for the current A6000 path, stop and report the execution barrier.

Do not silently fall back to BF16.

Any precision fallback requires a new explicit decision.

---

# 32. Outcome matrix

## Outcome A — Strong positive + timing specificity

Supported:

> retrieval-triggered visual gain improves FP32 MathVision performance and retrieval timing matters.

## Outcome B — Positive but timing-unspecific

Supported:

> FP32 visual amplification improves performance.

Not supported:

> retrieval timing is essential.

## Outcome C — Local reads improve, final accuracy does not

Interpretation:

> visual reading can be improved, but downstream reasoning remains the bottleneck.

Next:

- Block 3B.

## Outcome D — Null or harmful

Stop intervention branch.

Return to:

- Block 3B recovery/wandering dynamics.

---

# 33. Required artifacts

Produce:

1. `stage8c_v3_fp32_execution_manifest.json`
2. `stage8c_v3_dev128_manifest.json`
3. `stage8c_v3_dev_dose_results.json`
4. `stage8c_v3_dose_freeze.json`
5. `stage8c_v3_test512_manifest.json`
6. `stage8c_v3_test_primary_accuracy.json`
7. `stage8c_v3_family_clustered_inference.json`
8. `stage8c_v3_subtype_heterogeneity.json`
9. `stage8c_v3_timing_control256.json`
10. `stage8c_v3_local_read_audit128.parquet`
11. `stage8c_v3_rescue_collateral_review.json`
12. `stage8c_v3_runtime_overhead.json`
13. optional `stage8c_v3_extension512_manifest.json`
14. optional `stage8c_v3_combined1024_result.json`
15. `stage8c_v3_summary.md`

---

# 34. Key figures

## Figure 1 — FP32 dev128 dose-response

\[
g=1.0,\;1.25,\;1.5,\;2.0
\]

Plot:

- accuracy,
- W→C−C→W,
- cap rate,
- reasoning length.

## Figure 2 — FP32 held-out paired accuracy

C0 vs C1.

## Figure 3 — Family-clustered robustness

Item-level vs visual-family-level uncertainty.

## Figure 4 — Subtype heterogeneity

Intervention effect across major problem families/subtypes.

## Figure 5 — Timing specificity

Native vs retrieval-triggered vs random timing.

## Figure 6 — Rescue / collateral damage

W→C and C→W counts.

## Figure 7 — Local-read audit

L+/L− composition under FP32 baseline vs intervention.

---

# 35. Final decision criterion

Stage 8C v3 succeeds only if:

\[
\boxed{
\textbf{a frozen retrieval-triggered visual gain improves held-out FP32 MathVision performance across diverse independent visual families with acceptable collateral damage}
}
\]

The strongest version additionally requires:

\[
\boxed{
\text{retrieval-triggered gain}
>
\text{matched random-timing gain}
}
\]

If not met, stop the intervention branch and return to:

\[
\boxed{
\textbf{Block 3B — Post-Read Recovery / Wandering Dynamics}
}
\]
