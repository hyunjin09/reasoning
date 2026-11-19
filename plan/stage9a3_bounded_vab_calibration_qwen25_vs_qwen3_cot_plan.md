# Stage 9A.3 — Bounded VAB Calibration: Qwen2.5-VL CoT → Qwen3-VL CoT

## 0. One-line objective

First verify that our **model-wide direct image-token masking implementation** can recover the published VAB-style phenomenon on **Qwen2.5-VL-Instruct + prompted CoT**, then apply the **identical frozen assay** to **Qwen3-VL-Instruct + prompted CoT**.

Primary question:

\[
\boxed{
\textbf{Does the finite direct-visual-access regime reported for Qwen2.5-VL CoT
also hold in Qwen3-VL CoT under the same causal masking assay?}
}
\]

This is a **bounded calibration / generation-comparison experiment**.

It is **not** a full reproduction of the VAB paper and must not expand into one.

---

# 1. Why this experiment is necessary

Our current project has established strong **native causal visual-use dynamics** in Qwen3-VL Thinking, including late source-sensitive retrieval and controlled \(A\rightarrow B\rightarrow A\) source retargeting.

However, the comparison to VAB is currently underidentified.

VAB reports that prompted CoT in Qwen2.5-VL can often preserve task performance after direct generated-token access to image tokens is restricted to a finite early region.

Our recent Qwen3-VL experiments did **not** cleanly reproduce a monotone finite VAB-like boundary, but those experiments:

- used MathVision rather than the VAB controlled task;
- primarily masked a previously established late retrieval layer window;
- were designed to compare visual-access dynamics, not to reproduce VAB.

Therefore three explanations remain open:

1. **Implementation/task mismatch**
2. **Qwen2.5 → Qwen3 model-generation change**
3. **No real discrepancy; the previous Qwen3 assay measured a different quantity**

The cheapest way to distinguish them is:

\[
\boxed{
\text{Qwen2.5-VL CoT positive control}
\rightarrow
\text{same frozen assay on Qwen3-VL CoT}
}
\]

---

# 2. Paper claim a positive result can support

There are two scientifically distinct positive outcomes.

## Outcome A — VAB-like behavior transfers to Qwen3-VL CoT

If both Qwen2.5-VL CoT and Qwen3-VL CoT preserve performance under a finite early direct-access region:

> **The VAB-style CoT access regime generalizes across Qwen2.5-VL and Qwen3-VL Instruct checkpoints.**

Then the next important comparison is:

\[
\boxed{
\text{Qwen3-VL CoT}
\quad vs\quad
\text{Qwen3-VL Thinking}
}
\]

under the same model-wide necessity assay.

## Outcome B — VAB-like behavior appears in Qwen2.5 but not Qwen3

If the Qwen2.5 positive control succeeds but Qwen3 requires materially later/broader direct access:

> **The visual-access regime changed across Qwen model generations, so the difference cannot be attributed solely to Thinking specialization.**

This would be a high-value comparative result.

---

# 3. What a null does NOT rule out

## If Qwen2.5 does not reproduce VAB

Do **not** conclude that VAB is false.

This would only show that our bounded reimplementation failed to recover the published phenomenon under the chosen:

- model size,
- task generator,
- prompt,
- masking backend,
- coarse cutoff grid.

The correct interpretation is:

\[
\boxed{
\text{positive-control calibration failed}
}
\]

and **Qwen3 must not be interpreted comparatively from this assay**.

## If Qwen2.5 and Qwen3 look similar

This does not imply:

- Thinking and CoT are computationally identical;
- dynamic source retargeting is absent;
- native visual use equals visual necessity.

It only argues against a large **Instruct generation-level** shift in the tested VAB-style necessity regime.

---

# 4. Competing mechanisms distinguished

This experiment distinguishes:

### M1 — Implementation mismatch

Our mask does not recover the known Qwen2.5 phenomenon.

### M2 — Model-generation shift

\[
\text{Qwen2.5 CoT: finite early access}
\]

but:

\[
\text{Qwen3 CoT: later/broader access}
\]

### M3 — Stable Instruct-CoT access regime

Both generations exhibit similar finite access behavior.

This experiment does **not** yet distinguish:

- Qwen3 Instruct vs Qwen3 Thinking;
- architecture change vs training-data change;
- which Qwen3 architectural component causes any generation difference.

---

# 5. Stage dependency

This stage is sequential.

## Phase A — Qwen2.5 positive-control calibration

Run first.

## Phase B — Qwen3 transfer

Run **only if Phase A passes the positive-control gate**.

Do not spend Qwen3 compute if the Qwen2.5 calibration fails.

No Stage 9B experiment is authorized automatically.

---

# 6. Models

## Phase A

\[
\boxed{
\textbf{Qwen2.5-VL-3B-Instruct}
}
\]

Use the smallest practical Qwen2.5-VL checkpoint in the VAB model family to minimize compute.

## Phase B

\[
\boxed{
\textbf{Qwen3-VL-2B-Instruct}
}
\]

The parameter counts are not identical.

This is a **generation/family comparison at small scale**, not a parameter-matched causal attribution.

Do not claim that any difference is caused by a specific architectural change.

---

# 7. Reasoning condition

Both models use the **same frozen prompted-CoT condition**.

Use one fixed prompt as close as practical to the VAB elicitation:

> Think step by step. You must write intermediate steps.

Keep:

- question wording;
- option format;
- final-answer format;
- CoT instruction

identical across Qwen2.5 and Qwen3 unless checkpoint chat-template syntax forces a formatting difference.

No prompt search.

No alternative CoT wording after results are opened.

---

# 8. Primary controlled task

Use a **small VAB-style synthetic counting task**.

The purpose is:

\[
\boxed{
\text{recover the access phenomenon cheaply and cleanly}
}
\]

not benchmark generalization.

## Images

Freeze:

\[
\boxed{
32 \text{ synthetic images}
}
\]

Each image contains approximately 6–7 simple objects.

Use attributes modeled on the VAB setup:

- color
- shape
- size
- coarse location
- angle

Primary queries use only:

\[
\boxed{
\text{color and shape counting}
}
\]

to maximize full-access reliability.

Each image contributes:

- 1 color-count query
- 1 shape-count query

Total:

\[
\boxed{
64 \text{ query instances}
}
\]

The same images, targets, and option permutations are used for both model generations.

---

# 9. Frozen reserve

Generate and freeze an additional:

\[
\boxed{
16 \text{ images}
}
\]

before scientific results are opened.

These are **reserve only**.

They may be added to Phase A only if:

1. Qwen2.5 shows the expected directional pattern;
2. the result is visibly precision-limited rather than null;
3. implementation checks pass;
4. no cutoff/prompt retuning occurs.

Maximum positive-control sample after extension:

\[
\boxed{
48 \text{ images / 96 queries}
}
\]

Do not exceed this without user authorization.

---

# 10. Decoding

Use:

\[
\boxed{
\text{greedy decoding}
}
\]

for both models.

Recommended:

- `do_sample = false`
- native EOS stopping
- bounded generation cap appropriate for the short counting task

Do **not** use a 40,960-token cap if the controlled CoT task can be safely bounded much lower.

Freeze the cap from a small preflight before scientific results.

The goal is to avoid paying long-form MathVision-style generation cost for this calibration.

---

# 11. CoT validity gate

Before masking science, verify on the 32 full-access images that:

1. at least 90% of trajectories contain nontrivial intermediate reasoning;
2. final option extraction is valid;
3. full-access accuracy is materially above chance;
4. generation length is suitable for the frozen cutoff grid.

If Qwen2.5 does not actually produce CoT under the frozen prompt:

\[
\boxed{
\text{STOP}
}
\]

Do not prompt-sweep to rescue it.

---

# 12. Direct image-token masking intervention

The intervention must be **model-wide**, not restricted to layers 19–22.

For current generated-token query \(G_t\) and image-key positions \(V\), set:

\[
M_{G_t,j}=-\infty
\qquad
\forall j\in V
\]

outside the allowed layer/time access region.

Image K/V remain cached.

Do not erase:

- prefill computation;
- previously propagated image-derived residual state;
- text-side K/V already computed.

Thus the intervention asks:

\[
\boxed{
\textbf{How much continued direct generated-token access to image keys is necessary?}
}
\]

---

# 13. Technical validation before science

Run 8 fixed examples per model.

Require:

## V1 — Full-access no-op

The intervention-capable FULL condition reproduces the same-backend no-intervention output/logits within frozen tolerance.

## V2 — Image-key blocking

Masked generated-query → image-key probabilities are exactly zero or numerically equivalent to zero.

## V3 — Prefill preservation

Prompt/image prefill remains unchanged.

## V4 — Cache continuation

Autoregressive continuation remains valid after the access restriction begins.

## V5 — Layer semantics

Layer cutoffs apply at the intended normalized depth.

## V6 — Token semantics

Temporal cutoffs apply at the intended generated-token index.

Technical failure is not a scientific null.

---

# 14. Coarse layer grid

This stage does **not** estimate an exact boundary.

Use normalized decoder-depth cutoffs:

\[
\boxed{
\{0,\ 0.5L,\ 0.75L,\ L\}
}
\]

where cutoffs are rounded deterministically to valid decoder-layer indices.

Interpretation:

- `0`: no generated-query direct image access;
- `0.5L`: only first half of decoder layers retain direct access;
- `0.75L`: first three quarters retain access;
- `L`: all layers retain access.

Use the same normalized fractions for Qwen2.5 and Qwen3.

---

# 15. Coarse token grid

Freeze after full-access preflight but before masked outcomes.

Default grid:

\[
\boxed{
t_c\in\{0,\ 16,\ 64,\ \text{FULL}\}
}
\]

If >90% of full-access CoT generations finish before token 64, replace `64` prospectively with a smaller fixed cutoff based only on the full-access length distribution.

Do not choose cutoffs from masked accuracy.

---

# 16. Main grid size

Primary grid:

\[
4 \text{ layer cutoffs}
\times
4 \text{ token cutoffs}
=
16 \text{ conditions/query}
\]

With:

\[
64 \text{ query instances}
\]

this yields at most:

\[
\boxed{
1024 \text{ short continuations/model}
}
\]

before aliases/unreached cutoffs are collapsed.

This is the intended order of magnitude.

Do not expand into a dense 2D VAB sweep.

---

# 17. Full-access floor

For each model, require full-access accuracy:

\[
\boxed{
\ge 60\%
}
\]

on the 64 primary query instances.

If Qwen2.5 fails this floor:

- do not interpret preserved masked performance as a VAB;
- stop and report task/model mismatch.

If Qwen3 later fails the floor while Qwen2.5 passes:

- report underidentification of the generation comparison;
- do not retune the task after seeing Qwen3 masked outcomes.

---

# 18. Positive-control criterion for Qwen2.5

We do **not** need exact numerical reproduction of the published boundary.

Phase A passes if the coarse grid establishes all of:

1. a strongly restricted condition causes clear performance damage;
2. at least one **finite non-FULL access condition** remains within:

\[
\boxed{
5 \text{ percentage points}
}
\]

of full-access accuracy;
3. that performance-preserving condition is materially smaller than FULL in either token duration, layer depth, or both;
4. the pattern is directionally stable in image-cluster bootstrap uncertainty;
5. implementation checks remain valid.

This is sufficient to establish:

\[
\boxed{
\text{VAB-like finite access behavior recovered}
}
\]

for calibration purposes.

Do not require exact published cutoff coordinates.

---

# 19. Optional Phase A reserve extension

Use the 16 reserve images only if:

- a finite-access condition is within 10 pp of FULL;
- point estimate suggests the VAB-like pattern;
- the 5 pp gate is uncertain due sample size.

Run the **same frozen 16-condition grid** on the reserve.

No cutoff changes.

No prompt changes.

Then evaluate on all 48 images.

If Phase A still fails:

\[
\boxed{
\text{STOP before Qwen3}
}
\]

---

# 20. Phase B — Qwen3 transfer

If Phase A passes, apply **exactly the same frozen assay** to Qwen3-VL-2B-Instruct.

Freeze:

- same 32 primary images;
- same 64 queries;
- same options;
- same CoT instruction;
- same normalized layer cutoffs;
- same token cutoffs;
- same decoding style;
- same scoring;
- same 5 pp tolerance.

Do not optimize the grid for Qwen3.

This asymmetry is intentional:

\[
\boxed{
\text{Qwen2.5 calibrates the instrument;
Qwen3 tests transfer of the visual-access regime.}
}
\]

---

# 21. Primary Qwen2.5 → Qwen3 comparison

Do not reduce each model to one arbitrary boundary point.

Compare the entire coarse accuracy surface using:

\[
Damage_m(\ell,t)
=
Acc_m(FULL)-Acc_m(\ell,t)
\]

for:

\[
m\in\{Q2.5,Q3\}
\]

Primary comparative quantities:

## C1 — Finite-access preservation

Does each model possess at least one finite condition with:

\[
Damage\le5\text{pp}?
\]

## C2 — Same-cutoff transfer

Take the **smallest frozen Qwen2.5 condition that passes the 5 pp gate** under a deterministic tie rule.

Evaluate Qwen3 at the identical normalized cutoff.

Define:

\[
\Gamma
=
Damage_{Q3}
-
Damage_{Q2.5}
\]

A large positive \(\Gamma\) indicates greater Qwen3 dependence at the same access budget.

## C3 — Surface shift

Compare Qwen3 vs Qwen2.5 damage across all 16 frozen conditions using paired image bootstrap.

This is descriptive/supporting unless a clear systematic shift appears.

---

# 22. Deterministic tie rule for Qwen2.5 calibration cutoff

If multiple Qwen2.5 conditions are within 5 pp of FULL:

1. choose the smallest token cutoff;
2. among ties, choose the shallowest layer cutoff;
3. if still tied, choose lexicographic layer/token order.

Freeze this rule before Phase A masked outcomes.

This prevents selecting the cutoff that maximizes the Qwen3 difference.

---

# 23. Statistical unit

Primary independent unit:

\[
\boxed{
\text{synthetic image}
}
\]

because the color and shape queries share one image.

Use:

- image-clustered bootstrap;
- 4000 draws;
- paired image resampling across models and conditions;
- equal image weighting.

Do not treat:

- queries,
- tokens,
- layer cutoffs,
- grid cells

as independent samples.

---

# 24. Main outcome matrix

## Outcome A — Qwen2.5 passes, Qwen3 also passes similarly

Interpretation:

\[
\boxed{
\text{VAB-like Instruct-CoT access behavior transfers from Qwen2.5 to Qwen3}
}
\]

Next high-value question:

\[
\boxed{
\text{Qwen3 Instruct-CoT vs Qwen3 Thinking}
}
\]

under the same model-wide access assay.

## Outcome B — Qwen2.5 passes, Qwen3 does not

High-value interpretation:

\[
\boxed{
\textbf{The direct visual-access regime changed across Qwen model generations.}
}
\]

Do not immediately attribute this to DeepStack, MRoPE, training, or any specific component.

Next step should determine whether Qwen3 Thinking differs further from Qwen3 Instruct.

## Outcome C — Qwen2.5 calibration fails

Interpretation:

\[
\boxed{
\text{our bounded VAB instrument is not validated}
}
\]

Stop.

Do not interpret Qwen3 from this assay.

Possible causes include:

- model-size difference;
- prompt mismatch;
- synthetic generator mismatch;
- masking implementation mismatch;
- insufficient coarse-grid resolution.

A separate repair plan would be required.

## Outcome D — Qwen2.5 passes but Qwen3 full-access floor fails

The generation comparison is underidentified.

Do not task-tune Qwen3 after opening masked results.

---

# 25. Minimal artifact controls

Keep controls bounded.

Run a null-sink / redistribution control only on:

1. FULL;
2. one damaging Qwen2.5 condition;
3. the selected finite Qwen2.5 calibration condition.

If Phase B runs, apply the same three logical conditions to Qwen3.

Do not run a full control grid.

The purpose is to verify that the main qualitative effect is not solely softmax redistribution.

---

# 26. Compute discipline

This experiment is deliberately small.

Before launch, produce an exact estimate of:

- unique continuations;
- expected generated tokens;
- GPU-hours per Phase A;
- projected Phase B GPU-hours.

Target:

\[
\boxed{
\text{Phase A} < 25 \text{ GPU-hours}
}
\]

and ideally much lower.

Phase B should be of comparable or lower order on the 2B checkpoint.

If the estimate exceeds:

\[
\boxed{
40 \text{ GPU-hours for Phase A}
}
\]

stop and simplify before running.

Do not silently expand to MathVision-scale compute.

---

# 27. Transition from the prior Stage 9A run

The previous MathVision Stage 9A main analysis and all completed controls remain immutable.

This calibration experiment does not overwrite or reinterpret those artifacts.

If previous optional/pending GPU controls are still running, safely stop them at a valid boundary before allocating substantial compute here, preserving every completed output and receipt.

Record the reason:

> compute was redirected from optional robustness characterization after the prior main hypothesis gate had already failed, toward a new positive-control calibration required to interpret the VAB comparison.

Do not delete prior outputs.

---

# 28. Required artifacts

Produce:

1. `stage9a3_vab_calibration_spec.md`
2. `stage9a3_synthetic_dataset_manifest.json`
3. `stage9a3_prompt_manifest.json`
4. `stage9a3_mask_validation_qwen25.json`
5. `stage9a3_qwen25_full_access.json`
6. `stage9a3_qwen25_coarse_grid.parquet`
7. `stage9a3_qwen25_positive_control.json`
8. optional `stage9a3_qwen25_reserve_extension.json`
9. if Phase A passes: `stage9a3_mask_validation_qwen3.json`
10. if Phase A passes: `stage9a3_qwen3_full_access.json`
11. if Phase A passes: `stage9a3_qwen3_coarse_grid.parquet`
12. if Phase A passes: `stage9a3_generation_comparison.json`
13. `stage9a3_bounded_null_sink_control.json`
14. `stage9a3_resource_accounting.json`
15. `stage9a3_summary.md`

---

# 29. Key figures

## Figure 1 — Bounded VAB intervention

Show the generated-query → image-key access rectangle across:

- decoder depth;
- generated-token time.

## Figure 2 — Qwen2.5 positive-control coarse surface

Show the 4 × 4 accuracy/damage grid.

Highlight:

- FULL;
- damaging restriction;
- smallest finite performance-preserving condition.

## Figure 3 — Qwen3 transfer surface

Only if Phase A passes.

Use the exact same axes/grid.

## Figure 4 — Same-cutoff generation comparison

At the frozen Qwen2.5 calibration cutoff:

\[
Damage_{Q2.5}
\quad vs\quad
Damage_{Q3}
\]

with image-bootstrap uncertainty.

---

# 30. Exactly one recommendation at completion

## If Qwen2.5 passes and Qwen3 is similar

Recommend:

> proceed to a bounded Qwen3-Instruct-CoT vs Qwen3-Thinking model-wide visual-access comparison using the validated assay.

## If Qwen2.5 passes and Qwen3 differs

Recommend:

> prioritize the Qwen2.5→Qwen3 visual-access regime shift before attributing any difference to Thinking specialization.

## If Qwen2.5 fails

Recommend:

> stop the generation comparison and repair/validate the VAB reimplementation before drawing any Qwen3 conclusion.

Do not automatically launch the recommendation.

---

# 31. Final decision target

This stage is successful if it cleanly answers:

\[
\boxed{
\textbf{Can our bounded causal masking assay first recover VAB-like behavior in
Qwen2.5-VL CoT, and if so, does that same access regime transfer to Qwen3-VL CoT?}
}
\]

The experiment is intentionally small because its purpose is **calibration and discrimination**, not precise boundary estimation.
