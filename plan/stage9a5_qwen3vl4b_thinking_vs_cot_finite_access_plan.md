# Stage 9A.5 — Qwen3-VL-4B Thinking Finite-Access Comparison

## 0. One-line objective

Using the validated model-wide VAB-style masking assay, test whether **Qwen3-VL-4B-Thinking** requires direct image-token access for longer or later portions of reasoning than the matched **Qwen3-VL-4B-Instruct + CoT** checkpoint.

Primary question:

\[
\boxed{
\textbf{Does native Thinking exhibit a different direct visual-access necessity regime
from prompted CoT at the same Qwen3-VL-4B scale?}
}
\]

This is the decisive same-generation / same-scale comparison.

---

# 1. Why this experiment is necessary for the paper

The project currently has three relevant results:

## Result A — Thinking uses vision dynamically under native computation

Prior mechanistic experiments in Qwen3-VL Thinking established:

\[
\text{reasoning demand}
\rightarrow
\text{target-specific visual re-access}
\]

and controlled source retargeting:

\[
A\rightarrow B\rightarrow A
\quad\Rightarrow\quad
\text{causal visual source }A\rightarrow B\rightarrow A
\]

This establishes **native causal visual use**.

## Result B — Qwen2.5-VL CoT shows finite direct-access sufficiency

Stage 9A.3 recovered a VAB-like regime in Qwen2.5-VL-3B-Instruct+CoT:

- zero generated-query visual access strongly harms accuracy;
- direct access through token 64 is sufficient to preserve performance under the frozen 5 pp criterion.

## Result C — Qwen3-VL-4B Instruct+CoT also shows finite direct-access sufficiency, but later

Stage 9A.4 established a valid Qwen3-VL-4B-Instruct+CoT baseline:

- FULL accuracy ≈ 70%;
- zero access is strongly harmful;
- token 64 is insufficient;
- token 128 is the first tested preserving cutoff.

Therefore the remaining key question is:

\[
\boxed{
\textbf{Is Thinking actually different from matched Qwen3 CoT in direct-access necessity,
or does it merely use vision dynamically while remaining similarly finite-access sufficient?}
}
\]

This experiment determines whether the paper can support a Thinking-vs-CoT access-regime claim.

---

# 2. Paper claims this stage can support

## Claim A — Thinking-specific prolonged direct-access necessity

If Thinking requires a later temporal cutoff than Qwen3 CoT:

> **Native Thinking remains functionally dependent on direct image-token access later into reasoning than prompted CoT.**

This would support:

\[
\boxed{
\textbf{Thinking specialization changes the visual-access regime.}
}
\]

## Claim B — Shared finite-access necessity despite different native-use dynamics

If Thinking and CoT have similar finite-access sufficiency:

> **Thinking dynamically re-accesses visual sources under native computation, but prolonged direct visual access is not uniquely more necessary than in prompted CoT.**

This would support the distinction:

\[
\boxed{
\textbf{native causal use}
\neq
\textbf{ablation necessity}
}
\]

This is scientifically useful and does not invalidate the dynamic re-access result.

---

# 3. What this experiment cannot establish

Even if Thinking differs from CoT, do **not** claim:

- the difference is caused by "thinking" as a process;
- the difference is caused by a specific training objective;
- the difference is caused by DeepStack;
- persistent visual representations are absent;
- all Thinking models behave this way.

The comparison is between two matched-scale Qwen3-VL checkpoints:

\[
\boxed{
\text{Qwen3-VL-4B-Instruct + CoT}
\quad\text{vs}\quad
\text{Qwen3-VL-4B-Thinking}
}
\]

Checkpoint/training specialization remains a confound.

---

# 4. Models

## Reference arm — already completed

\[
\boxed{
\textbf{Qwen3-VL-4B-Instruct + prompted CoT}
}
\]

Use the frozen Stage 9A.4 results.

Do not rerun unless a technical identity check fails.

Frozen reference facts:

- valid FULL baseline;
- zero-access damage;
- token 64 insufficient;
- token 128 first tested preserving cutoff;
- bounded null-sink control completed.

## New arm

\[
\boxed{
\textbf{Qwen3-VL-4B-Thinking}
}
\]

Use the native Thinking template / reasoning path.

Do not append the Instruct CoT prompt.

---

# 5. Dataset

Reuse the exact Stage 9A.3 / 9A.4 primary controlled task:

\[
\boxed{
32 \text{ frozen synthetic images}
}
\]

Each image has:

- 1 color-count query
- 1 shape-count query

Total:

\[
\boxed{
64 \text{ primary queries}
}
\]

Reuse exactly:

- image files;
- questions;
- option permutations;
- answer keys;
- preprocessing;
- scoring adapter;
- bootstrap seed;
- masking implementation.

No new primary images.

---

# 6. Optional reserve

Reuse the same already-frozen reserve:

\[
\boxed{
16 \text{ images / 32 queries}
}
\]

Do not use reserve unless the preregistered precision-extension rule in Section 18 is met.

---

# 7. Thinking prompt / response format

Use the native Qwen3-VL-4B-Thinking chat path.

Keep the task wording and final answer format identical to the Instruct controlled task wherever possible.

Do not add:

> Think step by step.

The model's native Thinking path supplies its own reasoning behavior.

Require the same final multiple-choice option format used in Stage 9A.4.

---

# 8. Decoding

Use the same high-level execution regime as Stage 9A.4:

- greedy decoding;
- `do_sample = false`;
- BF16;
- TF32 off;
- native EOS;
- same image preprocessing;
- same mask-capable attention backend;
- same model-wide generated-query → image-key masking semantics.

Use:

\[
\boxed{
\text{max\_new\_tokens}=512
}
\]

for the primary Thinking baseline unless the native Thinking interface requires a larger technical cap before any scientific masked outcome is observed.

If 512 is insufficient at FULL baseline, do **not** silently increase the cap after seeing masked results.

A baseline-only repair amendment would be required.

---

# 9. Phase T0 — FULL Thinking baseline only

Before any masked Thinking science, run:

\[
\boxed{
\text{FULL direct visual access}
}
\]

for all 64 queries.

Measure:

- all-example accuracy;
- valid final option rate;
- normal EOS rate;
- cap rate;
- mean/median generated reasoning tokens;
- unscorable rate.

Also record the generation-length distribution:

\[
\boxed{
T_{\text{Think}}
}
\]

because absolute token cutoffs must later be interpreted relative to Thinking's reasoning horizon.

---

# 10. FULL baseline validity gates

Proceed only if all are satisfied.

## G1 — Accuracy

\[
\boxed{
Acc_{\text{FULL,Think}}\ge60\%
}
\]

## G2 — Native Thinking realization

At least:

\[
\boxed{
90\%
}
\]

of trajectories contain nontrivial native reasoning before the final answer.

## G3 — Final-answer validity

At least:

\[
\boxed{
90\%
}
\]

produce a valid extractable final option.

## G4 — Completion

\[
\boxed{
\text{cap rate}\le10\%
}
\]

unless capped traces already contain valid final answers.

## G5 — Mask backend validity

FULL mask-capable execution must satisfy the same no-op checks as Stage 9A.4.

If any gate fails:

\[
\boxed{
\textbf{STOP before masked Thinking conditions.}
}
\]

Do not change the task or prompt within this plan.

---

# 11. Technical validation

Run the same bounded 8-example model checks used in Stage 9A.4.

Require:

## V1 — FULL no-op

Same-backend FULL reproduces no-intervention logits/tokens within frozen tolerance.

## V2 — Exact generated-query → image-key block

Masked image-key attention is numerically zero.

## V3 — Prefill unchanged

Image/question prefill remains native.

## V4 — Cache continuation valid

Cached autoregressive generation remains correct after access restriction begins.

## V5 — Temporal cutoff semantics

64 / 128 / 256 cutoffs occur at the intended generated-token index.

## V6 — All decoder layers included

The temporal access restriction applies model-wide, not only layers 19–22.

---

# 12. Phase T1 — Minimal Thinking finite-access panel

If FULL passes, run:

\[
\boxed{
\text{ZERO},\quad t=64,\quad t=128
}
\]

All decoder layers remain available until the token cutoff.

## ZERO

No generated token directly attends to image-token keys.

## token 64

Direct image access allowed through generated token 64, blocked thereafter.

## token 128

Direct image access allowed through generated token 128, blocked thereafter.

The token-128 condition is especially important because it is the first preserving Qwen3-4B Instruct-CoT cutoff.

---

# 13. Primary absolute-budget contrasts

Define:

\[
Damage_{\text{Think}}(t)
=
Acc_{\text{Think}}(\text{FULL})
-
Acc_{\text{Think}}(t)
\]

Primary quantities:

## P1 — Zero-access damage

\[
Damage_{\text{Think}}(0)
\]

## P2 — token-64 damage

\[
Damage_{\text{Think}}(64)
\]

## P3 — token-128 damage

\[
Damage_{\text{Think}}(128)
\]

Primary same-generation comparison:

\[
\boxed{
Damage_{\text{Think}}(128)
-
Damage_{\text{CoT}}(128)
}
\]

where the CoT token-128 result is frozen from Stage 9A.4.

---

# 14. First decision gate

## Outcome T1-A — Thinking token 128 preserves performance

If:

\[
Damage_{\text{Think}}(128)\le5\text{ pp}
\]

then Thinking shares coarse finite-access sufficiency at or before the CoT cutoff.

Do not run token 256 unless relative-time analysis reveals a strong unresolved interpretation issue.

Proceed to relative-time comparison and bounded redistribution control.

## Outcome T1-B — Thinking token 128 is insufficient

If:

\[
Damage_{\text{Think}}(128)>5\text{ pp}
\]

and ZERO is meaningfully damaging, run:

\[
\boxed{
t=256
}
\]

This tests whether Thinking requires a later absolute visual-access budget.

## Outcome T1-C — ZERO is not damaging

If:

\[
Damage_{\text{Think}}(0)\le5\text{ pp}
\]

stop the finite-access necessity interpretation.

Do not search for later cutoffs.

---

# 15. Optional token 256

Run only after Outcome T1-B.

If:

\[
Damage_{\text{Think}}(256)\le5\text{ pp}
\]

then:

> Thinking still has finite direct-access sufficiency, but at a later tested absolute budget than Instruct-CoT.

If token 256 is still >5 pp damage:

> Finite direct-access sufficiency is not established for Thinking within the bounded tested budget.

Do not conclude that FULL access is strictly necessary.

---

# 16. Relative-time normalization

Absolute token cutoffs are insufficient because Thinking and CoT may have different generation lengths.

Therefore Stage 9A.5 must include a **secondary normalized-time comparison**.

Use FULL baseline generation lengths only.

For each arm, compute descriptive access fractions:

\[
r_{64,p}
=
\frac{64}{T_p}
\]

\[
r_{128,p}
=
\frac{128}{T_p}
\]

using median and item-level FULL trajectory lengths.

Report:

- median fraction of reasoning horizon exposed at token 64;
- median fraction exposed at token 128;
- distribution of actual mask exposure;
- fraction of trajectories ending before each cutoff.

This distinguishes:

\[
\boxed{
\text{later absolute cutoff}
}
\]

from:

\[
\boxed{
\text{later relative reasoning-phase requirement}
}
\]

---

# 17. Optional matched relative-time intervention

Run this only if absolute cutoffs suggest Thinking requires more access than CoT **and** the difference could plausibly be explained by longer Thinking traces.

Use exactly two normalized cutoffs:

\[
\boxed{
50\%,\quad 75\%
}
\]

For each FULL baseline trajectory, define the cutoff from its frozen native generated length.

Run both CoT and Thinking on the same 32 images at these normalized access budgets.

This is a secondary discrimination assay.

Do not add more normalized cutoffs.

Primary question:

\[
\boxed{
\textbf{At the same relative reasoning phase, is Thinking still more dependent on direct vision?}
}
\]

If no absolute difference appears, this optional assay is not needed.

---

# 18. Reserve extension rule

Use the frozen 16-image reserve only if:

1. a primary Thinking-vs-CoT contrast is in the hypothesized direction;
2. its interval includes zero or 5 pp preservation status is precision-limited;
3. no technical/control failure is present;
4. the result is not clearly null;
5. no cutoff values are changed.

If triggered, run only:

- FULL;
- ZERO;
- the currently decision-relevant cutoff

on reserve.

Maximum total:

\[
\boxed{
48 \text{ images / 96 queries}
}
\]

Do not use reserve to rescue a clearly null pattern.

---

# 19. Null-sink / redistribution control

Run only on the primary 32 images and only after the finite-access decision.

Conditions:

1. FULL
2. ZERO
3. selected Thinking finite cutoff

If Thinking and CoT share token 128 as the key cutoff, this gives a direct same-condition robustness comparison.

Do not run a full control grid.

---

# 20. Statistical unit

Primary independent unit:

\[
\boxed{
\text{synthetic image}
}
\]

because color and shape queries share one scene.

Use:

- 4,000 image-cluster bootstrap draws;
- equal image weighting;
- paired resampling across CoT and Thinking;
- same frozen bootstrap seed where possible;
- 95% intervals for damage contrasts.

Do not treat queries, generated tokens, or cutoffs as independent samples.

---

# 21. Primary claim gate

Support a Thinking-specific prolonged direct-access regime only if all hold:

1. Thinking FULL baseline is valid.
2. ZERO access is meaningfully damaging.
3. At token 128, Thinking damage exceeds the 5 pp preservation criterion.
4. Thinking damage at token 128 is larger than matched CoT damage in the same direction with meaningful paired bootstrap support.
5. A later Thinking cutoff (e.g. token 256) restores performance, or the tested budget remains insufficient.
6. The difference is not explained solely by trajectories ending before/after the fixed cutoff.
7. If needed, normalized 50%/75% intervention supports a genuine relative-time difference.
8. Bounded null-sink control preserves the qualitative result.

A raw difference in generation length is not enough.

---

# 22. Outcome matrix

## Outcome A — Thinking and CoT both preserve at token 128

Interpretation:

\[
\boxed{
\textbf{Thinking and prompted CoT share coarse finite direct-access sufficiency.}
}
\]

Important paper implication:

> Thinking can dynamically and causally re-access visual sources under native computation even though prolonged direct access is not more necessary than in CoT under ablation.

This strengthens:

\[
\boxed{
\textbf{native causal visual use}
\neq
\textbf{ablation necessity}
}
\]

Do not claim Thinking-specific prolonged access.

## Outcome B — Thinking requires token 256, CoT preserves at 128

Interpretation:

\[
\boxed{
\textbf{Thinking has a later absolute direct-access requirement than matched CoT.}
}
\]

Then use relative-time analysis to determine whether this is:

- longer reasoning only, or
- a genuine later reasoning-phase access requirement.

If relative-time difference survives:

> Thinking specialization is associated with a changed visual-access regime.

## Outcome C — Thinking remains damaged at token 256

Interpretation:

> Finite direct-access sufficiency is not established for Thinking within the tested window, whereas it is established for matched CoT.

This is the strongest Thinking-vs-CoT regime-difference candidate.

Do not claim FULL access is strictly necessary.

## Outcome D — Thinking ZERO not damaging

The controlled task does not establish generated-token direct visual necessity in Thinking.

Stop the branch.

## Outcome E — Thinking FULL baseline invalid

Stop before masked science.

No CoT-vs-Thinking necessity conclusion.

---

# 23. Relation to the main paper story

This experiment does **not** determine whether dynamic re-access exists in Thinking; that has already been established through source-sensitive causal interventions.

It determines whether that native-use mechanism is also reflected in **greater ablation necessity**.

Thus the paper can distinguish:

\[
\boxed{
\textbf{What the model uses natively}
}
\]

from:

\[
\boxed{
\textbf{What the model strictly needs under intervention}
}
\]

This comparison is conceptually important regardless of outcome.

---

# 24. Connection to VAB

The final comparative chain is:

\[
\boxed{
\text{Qwen2.5-VL-3B CoT}
\rightarrow
\text{Qwen3-VL-4B CoT}
\rightarrow
\text{Qwen3-VL-4B Thinking}
}
\]

with the same core model-wide masking definition.

This allows three interpretations:

### Stable CoT + stable Thinking finite access
Finite-access sufficiency is broad; native re-access and necessity must be distinguished.

### Qwen3 CoT later than Qwen2.5, Thinking similar to Qwen3 CoT
Model-generation shift dominates.

### Qwen3 Thinking later than matched Qwen3 CoT
Thinking specialization adds an access-regime shift beyond the generation effect.

---

# 25. Compute discipline

This experiment should remain bounded.

Primary 32-image conditions:

- FULL
- ZERO
- token64
- token128
- optional token256

Target total:

\[
\boxed{
<10 \text{ GPU-hours}
}
\]

including bounded null-sink control if possible.

Hard stop before reserve / normalized intervention:

\[
\boxed{
>15 \text{ projected GPU-hours}
}
\]

requires a compute amendment or user approval.

Do not expand into a dense 2D grid.

---

# 26. Required artifacts

Produce:

1. `stage9a5_qwen3_4b_thinking_spec.md`
2. `stage9a5_thinking_mask_validation.json`
3. `stage9a5_thinking_full_baseline.json`
4. `stage9a5_thinking_primary64.parquet`
5. optional `stage9a5_thinking_token256.parquet`
6. `stage9a5_absolute_access_comparison.json`
7. `stage9a5_relative_time_analysis.json`
8. optional `stage9a5_relative_time_intervention.json`
9. optional `stage9a5_reserve_extension.json`
10. `stage9a5_null_sink_control.json`
11. `stage9a5_cot_vs_thinking_inference.json`
12. `stage9a5_resource_accounting.json`
13. `stage9a5_summary.md`

---

# 27. Key figures

## Figure 1 — CoT vs Thinking FULL validity

Show:

- accuracy
- reasoning length
- completion
- cap rate
- valid extraction

## Figure 2 — Absolute finite-access comparison

Plot for Qwen3-4B CoT and Thinking:

- FULL
- ZERO
- token64
- token128
- optional token256

## Figure 3 — Same token-128 contrast

Show:

\[
Damage_{\text{CoT}}(128)
\quad\text{vs}\quad
Damage_{\text{Think}}(128)
\]

with image-bootstrap uncertainty.

## Figure 4 — Relative reasoning-time exposure

Show:

- generation length distributions
- fraction of reasoning horizon covered by token64/128/256
- optional 50%/75% intervention if triggered

## Figure 5 — Native use vs necessity synthesis

Conceptual figure combining:

- prior dynamic source retargeting / active retrieval evidence
- current access-removal necessity result

Purpose:

\[
\boxed{
\text{native causal use}
\quad\text{vs}\quad
\text{ablation necessity}
}
\]

---

# 28. Exactly one recommendation at completion

## If Thinking is clearly later/more dependent than CoT

Recommend:

> develop the Thinking-specific visual-access-regime claim and test whether the extra necessity is aligned with controlled recurrent visual demand.

## If Thinking and CoT are similar

Recommend:

> retain dynamic visual re-access as the main Thinking mechanism and emphasize the dissociation between native causal use and ablation necessity rather than a Thinking-specific VAB claim.

## If baseline/assay validity fails

Recommend:

> stop the CoT-vs-Thinking finite-access branch and retain the already established native causal-retrieval story.

Do not launch the recommendation automatically.

---

# 29. Final decision target

\[
\boxed{
\textbf{Under the same validated model-wide visual-access intervention,
does Qwen3-VL-4B-Thinking require direct image-token access later in reasoning
than matched Qwen3-VL-4B-Instruct+CoT?}
}
\]

This experiment determines whether the paper can support a **Thinking-specific visual-access necessity claim**, or whether the stronger and more accurate story is instead:

\[
\boxed{
\textbf{Thinking dynamically uses vision even when prolonged direct access is not uniquely necessary.}
}
\]
