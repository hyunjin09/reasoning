# Stage 9A.4 — Qwen3-VL-4B Baseline Repair and Bounded Finite-Access Test

## 0. One-line objective

Repair the invalid Qwen3 baseline from Stage 9A.3 by moving to **Qwen3-VL-4B-Instruct**, then test—using the already validated VAB-style masking assay—whether **finite direct image-token access is sufficient** under prompted CoT.

Primary question:

\[
\boxed{
\textbf{Does Qwen3-VL-4B-Instruct preserve CoT performance when direct
generated-token access to image keys is restricted to a finite early window?}
}
\]

This is a **bounded baseline-repair + transfer test**.

It is not a dense VAB reproduction and must not expand into one.

---

# 1. Why this experiment is necessary

Stage 9A.3 successfully calibrated the masking instrument on Qwen2.5-VL-3B-Instruct:

- FULL accuracy: 70.83%
- zero generated-query visual access: 48.96%
- all decoder layers through token 64: 71.88%
- the finite token-64 condition passed the 5 pp preservation criterion with strong bootstrap stability
- the null-sink control preserved the qualitative pattern

Therefore the core VAB-style intervention is now validated on Qwen2.5-VL.

However, Qwen3-VL-2B-Instruct failed the mandatory FULL-access validity gates before masked science:

- low full-access accuracy
- incomplete CoT realization
- many capped / missing final answers

The Qwen3 masked grid was correctly not run.

The next scientific question is therefore not “repair the mask.”

It is:

\[
\boxed{
\textbf{Can a valid Qwen3 baseline be established at a slightly larger matched-family scale,
and if so, does the calibrated finite-access phenomenon transfer?}
}
\]

---

# 2. Why Qwen3-VL-4B-Instruct

Use:

\[
\boxed{
\textbf{Qwen3-VL-4B-Instruct}
}
\]

instead of further repairing the 2B checkpoint.

Reasons:

1. The 2B FULL baseline was below the 60% task-validity floor.
2. Extending the token cap alone cannot guarantee recovery of the original floor.
3. The 4B checkpoint remains small enough for bounded A6000 execution.
4. It is closer in capability scale to the Qwen2.5-VL-3B positive control than Qwen3-VL-2B.
5. It aligns naturally with the Qwen3-VL-4B-Thinking scale already used in the broader mechanistic project.

This is still **not parameter matched** to Qwen2.5-VL-3B.

Do not attribute any generation difference to parameter count, DeepStack, MRoPE, data, or a specific architectural component.

---

# 3. DeepStack interpretation boundary

Qwen3-VL uses native DeepStack-style visual feature injection.

For this primary experiment:

\[
\boxed{
\textbf{Do not disable, alter, or ablate DeepStack.}
}
\]

The goal is to characterize the native Qwen3-VL-4B-Instruct visual-access regime.

The VAB-style intervention continues to target:

\[
\boxed{
\text{generated-token query}
\rightarrow
\text{cached image-token keys}
}
\]

during decoding.

If Qwen3 differs from Qwen2.5 under the validated assay, that establishes a **model-generation access-regime difference candidate**, not a DeepStack causal attribution.

A DeepStack-specific intervention would require a separate plan.

---

# 4. Frozen data and prompt

Reuse the exact Stage 9A.3 controlled task.

## Primary images

\[
\boxed{
32 \text{ frozen synthetic images}
}
\]

## Queries

Each image has:

- 1 color-count query
- 1 shape-count query

Total:

\[
\boxed{
64 \text{ frozen query instances}
}
\]

Reuse exactly:

- image files
- question wording
- option permutations
- answer keys
- CoT instruction
- final-answer format
- preprocessing
- scoring adapter
- bootstrap seed

No new synthetic images are needed for the main test.

---

# 5. Frozen CoT prompt

Use the same Stage 9A.3 prompted-CoT instruction:

> Think step by step. You must write intermediate steps.

No prompt search.

No prompt rewrite after outcomes are opened.

Use the native Qwen3-VL-4B-Instruct chat template only as required by the checkpoint.

---

# 6. Decoding

Use:

\[
\boxed{
\text{greedy decoding}
}
\]

with:

- `do_sample = false`
- native EOS stopping
- BF16 weights
- TF32 off
- same image preprocessing as Stage 9A.3
- same mask-capable attention backend for FULL and restricted-access conditions

For Qwen3-VL-4B-Instruct set:

\[
\boxed{
\text{max\_new\_tokens}=512
}
\]

This is a prospective baseline repair relative to the invalid 2B/256-token setting.

Do not tune the cap after masked outcomes.

---

# 7. Phase R0 — FULL baseline only

Before any masked Qwen3 science, run only:

\[
\boxed{
\text{FULL direct visual access}
}
\]

on all 64 primary queries.

No masked condition is authorized until the FULL gate passes.

Measure:

- accuracy
- intermediate-reasoning rate
- valid final option rate
- normal EOS rate
- cap rate
- mean / median generation length
- unscorable rate

---

# 8. FULL baseline validity gates

Proceed to masked science only if all are satisfied.

## G1 — Accuracy

\[
\boxed{
Acc_{\text{FULL}}\ge60\%
}
\]

## G2 — CoT realization

At least:

\[
\boxed{
90\%
}
\]

of trajectories contain nontrivial intermediate reasoning before the final answer.

## G3 — Final-answer validity

At least:

\[
\boxed{
90\%
}
\]

produce a valid extractable final option.

## G4 — Completion

Operational cap gate:

\[
\boxed{
\text{cap rate}\le10\%
}
\]

unless all capped traces already contain a valid final answer before truncation.

## G5 — Technical validity

FULL mask-capable execution must pass the same-backend no-op checks.

If any gate fails:

\[
\boxed{
\textbf{STOP before masked conditions.}
}
\]

Do not change prompt, task, model, or cap within this plan.

---

# 9. Technical mask validation

Run 8 fixed technical examples before Phase R1.

Require:

## V1 — FULL no-op
Same-backend FULL reproduces no-intervention logits/tokens within frozen tolerance.

## V2 — Exact visual blocking
Masked generated-query → image-key attention probability is zero.

## V3 — Prefill unchanged
Image/question prefill remains native.

## V4 — Cache continuation
Autoregressive continuation remains valid after access cutoff.

## V5 — Temporal cutoff semantics
Token-64/128/256 transitions occur at the intended generated-token index.

## V6 — Model-wide scope
All decoder layers participate in the temporal access restriction.

Technical failure is an implementation stop, not a scientific null.

---

# 10. Phase R1 — Minimal calibrated transfer test

If Phase R0 passes, first run only the two masked conditions below.

The FULL baseline is reused.

## Condition Z — Zero generated-query access

\[
\boxed{
t_c=0
}
\]

No generated token may directly attend to image-token keys.

Purpose:

> verify that visual access matters in Qwen3 under this task.

## Condition 64 — All decoder layers through token 64

\[
\boxed{
t_c=64
}
\]

All decoder layers retain direct image access for the first 64 generated tokens; direct generated-query → image-key access is blocked thereafter.

This is the **frozen Qwen2.5 calibrated finite-access condition**.

No layer truncation is used.

---

# 11. Primary Stage 9A.4 contrasts

Let:

\[
Damage(t)
=
Acc_{\text{FULL}}
-
Acc(t)
\]

Primary quantities:

## P1 — Zero-access necessity

\[
\boxed{
Damage(0)
}
\]

A positive effect shows that some generated-token direct visual access is useful/necessary.

## P2 — Token-64 preservation

\[
\boxed{
Damage(64)
}
\]

Primary finite-access criterion:

\[
\boxed{
Damage(64)\le5\text{ pp}
}
\]

## P3 — Qwen2.5 → Qwen3 same-cutoff shift

Use the frozen Qwen2.5 token-64 result:

\[
Damage_{Q2.5}(64)=-1.04\text{ pp}
\]

Define:

\[
\Gamma_{64}
=
Damage_{Q3}(64)
-
Damage_{Q2.5}(64)
\]

This comparison is descriptive / paired-by-task, not a same-checkpoint causal attribution.

---

# 12. Decision after token 64

## Outcome R1-A — Token 64 preserves Qwen3 performance

If:

\[
Damage(64)\le5\text{ pp}
\]

and zero access causes meaningful damage:

\[
Damage(0)>5\text{ pp}
\]

then conclude:

\[
\boxed{
\textbf{Finite direct visual access is sufficient in Qwen3-VL-4B-Instruct CoT.}
}
\]

No token-128/256 conditions are required.

Proceed only to the bounded null-sink control.

## Outcome R1-B — Token 64 is insufficient

If:

\[
Damage(64)>5\text{ pp}
\]

while FULL is valid and zero access is damaging, proceed sequentially to Phase R2.

Do not immediately run a dense grid.

## Outcome R1-C — Zero access is not damaging

If:

\[
Damage(0)\le5\text{ pp}
\]

the controlled task does not establish generated-token direct visual necessity in Qwen3.

Stop the finite-access interpretation.

Do not search for a later cutoff.

---

# 13. Phase R2 — Sequential temporal extension

Run only if token 64 is insufficient.

First run:

\[
\boxed{
t_c=128
}
\]

all decoder layers.

If:

\[
Damage(128)\le5\text{ pp}
\]

stop the search and select token 128.

Otherwise run:

\[
\boxed{
t_c=256
}
\]

all decoder layers.

If:

\[
Damage(256)\le5\text{ pp}
\]

stop and select token 256.

Do not run additional token cutoffs in this plan.

Maximum scientific condition set:

- FULL
- ZERO
- token 64
- token 128
- token 256

---

# 14. Interpretation of sequential outcomes

## Selected cutoff = 64

\[
\boxed{
\text{Qwen2.5 and Qwen3 both show coarse finite early direct-access sufficiency}
}
\]

No large generation shift is established at this resolution.

## Selected cutoff = 128 or 256

\[
\boxed{
\textbf{Qwen3 still shows finite direct-access sufficiency,
but requires a later access budget than Qwen2.5 under the bounded assay.}
}
\]

This is a model-generation regime-shift candidate.

## No tested finite cutoff preserves performance

If token 64, 128, and 256 all exceed 5 pp damage:

\[
\boxed{
\text{finite direct-access sufficiency is not established in Qwen3 within the bounded grid}
}
\]

Do **not** conclude that FULL access is strictly necessary.

---

# 15. Statistical unit and inference

Primary independent unit:

\[
\boxed{
\text{synthetic image}
}
\]

because color and shape queries share a scene.

Use:

- 4,000 paired image-cluster bootstrap draws
- equal image weighting
- the same frozen Stage 9A.3 bootstrap seed where compatible
- 95% intervals for damage

Do not treat queries, generated tokens, or conditions as independent samples.

---

# 16. Bounded reserve extension

Reuse the already frozen Stage 9A.3 reserve:

\[
\boxed{
16 \text{ images / 32 queries}
}
\]

only if:

1. FULL baseline on the primary 32-image set passes;
2. the selected finite cutoff has a point estimate within 10 pp of FULL;
3. its 5 pp preservation status is uncertainty-limited;
4. implementation checks pass.

If triggered, run only:

- FULL
- ZERO
- currently selected finite cutoff

on the 16 reserve images.

Do not rerun all sequential cutoffs on reserve unless the selected cutoff changes prospectively before reserve outcomes are opened.

Maximum combined sample:

\[
\boxed{
48 \text{ images / 96 queries}
}
\]

---

# 17. Null-sink / redistribution control

Run only after a finite Qwen3 cutoff has been selected.

Use the primary 32 images and exactly:

1. FULL
2. ZERO
3. selected finite cutoff

Implement the same bounded null-sink logic already validated in Stage 9A.3.

Purpose:

\[
\boxed{
\text{verify that finite-access preservation is not solely a softmax-redistribution artifact}
}
\]

Do not run a full null-sink grid.

---

# 18. No DeepStack ablation in this stage

Even if Qwen3 differs from Qwen2.5:

\[
\boxed{
\textbf{do not disable DeepStack in Stage 9A.4}
}
\]

A difference may reflect:

- DeepStack
- other architectural changes
- training differences
- model capacity
- checkpoint-specific behavior

A DeepStack-specific causal test requires a separate hypothesis and plan.

---

# 19. Compute discipline

This experiment should remain small.

Before launch, estimate:

- Phase R0 FULL baseline GPU-hours
- Phase R1 ZERO + token64
- worst-case R2 token128 + token256
- optional reserve
- bounded null-sink control

Target:

\[
\boxed{
\text{primary + worst-case sequential masked science} < 15 \text{ GPU-hours}
}
\]

Prefer substantially lower.

Hard stop:

\[
\boxed{
>25 \text{ projected GPU-hours before reserve/control}
}
\]

requires simplification or user approval.

Do not expand into MathVision-scale compute.

---

# 20. Relation to prior Stage 9A.3

Stage 9A.3 established:

\[
\boxed{
\text{Qwen2.5-VL-3B CoT has a VAB-like finite-access regime}
}
\]

under the calibrated controlled task.

It did **not** establish the Qwen3 regime because the 2B FULL baseline failed validity gates.

Stage 9A.4 changes only the Qwen3 checkpoint / cap needed to obtain a valid baseline.

Keep frozen:

- task
- images
- options
- CoT prompt
- greedy decoding
- mask semantics
- 5 pp preservation tolerance
- Qwen2.5 positive-control result

Do not reinterpret or overwrite Stage 9A.3.

---

# 21. Outcome matrix

## Outcome A — Qwen3 FULL valid; token64 sufficient

Supported:

> **Finite direct visual access is sufficient in both Qwen2.5-VL CoT and Qwen3-VL CoT under the bounded assay.**

Next high-value comparison:

\[
\boxed{
\text{Qwen3-VL-4B Instruct-CoT vs Qwen3-VL-4B Thinking}
}
\]

using the validated model-wide assay.

## Outcome B — Qwen3 FULL valid; token128/256 required

Supported:

> **Qwen3-VL CoT retains finite direct-access sufficiency, but the sufficient temporal access budget is later than in Qwen2.5-VL under the bounded assay.**

This is a model-generation access-regime difference candidate.

Do not attribute it to DeepStack yet.

## Outcome C — Qwen3 FULL valid; no tested finite cutoff sufficient

Supported:

> **The Qwen2.5 finite-access result does not transfer to Qwen3 within the tested temporal budget.**

This is a stronger generation-shift candidate, but not proof that FULL access is strictly necessary.

## Outcome D — Qwen3 FULL baseline still invalid

Stop.

The controlled counting task remains unsuitable for Qwen3 comparison at this checkpoint/decoding setup.

Do not run masked science.

---

# 22. Main paper-story dependency

## If Outcome A

VAB-like finite access is not a Qwen2.5-only phenomenon.

The next question becomes:

\[
\boxed{
\text{Does native Thinking differ from matched Qwen3 CoT despite this shared finite-access regime?}
}
\]

## If Outcome B/C

A Qwen model-generation difference becomes scientifically important.

Then:

\[
\boxed{
\text{Qwen2.5 vs Qwen3 visual-access regime}
}
\]

must be resolved before attributing differences to Thinking specialization.

## If Outcome D

Keep VAB as external context only.

Do not make a Qwen-generation claim.

---

# 23. Required artifacts

Produce:

1. `stage9a4_qwen3_4b_repair_spec.md`
2. `stage9a4_qwen3_4b_mask_validation.json`
3. `stage9a4_qwen3_4b_full_baseline.json`
4. `stage9a4_qwen3_4b_primary64.parquet`
5. optional `stage9a4_qwen3_4b_token128.parquet`
6. optional `stage9a4_qwen3_4b_token256.parquet`
7. `stage9a4_qwen3_4b_finite_access_decision.json`
8. optional `stage9a4_qwen3_4b_reserve_extension.json`
9. optional `stage9a4_qwen3_4b_null_sink_control.json`
10. `stage9a4_qwen25_qwen3_comparison.json`
11. `stage9a4_resource_accounting.json`
12. `stage9a4_summary.md`

---

# 24. Key figures

## Figure 1 — Baseline validity

Qwen2.5-3B FULL vs Qwen3-4B FULL:

- accuracy
- CoT realization
- final-answer validity
- cap rate

## Figure 2 — Temporal finite-access comparison

Show accuracy/damage for:

- FULL
- ZERO
- token64
- optional token128
- optional token256

for Qwen2.5 and Qwen3.

## Figure 3 — Same token64 comparison

Highlight:

\[
Damage_{Q2.5}(64)
\quad vs\quad
Damage_{Q3}(64)
\]

## Figure 4 — Null-sink robustness

Only if a finite Qwen3 cutoff is selected.

---

# 25. Exactly one recommendation at completion

## If Qwen3 token64 is sufficient

Recommend:

> proceed to a bounded Qwen3-VL-4B Instruct-CoT vs Qwen3-VL-4B Thinking model-wide direct-access comparison.

## If Qwen3 requires token128/256 or no tested finite cutoff suffices

Recommend:

> characterize the Qwen2.5→Qwen3 access-regime shift before attributing any difference to Thinking specialization.

## If Qwen3 FULL baseline fails

Recommend:

> stop the controlled VAB-transfer branch for Qwen3 under this task and retain Qwen2.5 calibration only.

Do not launch the recommendation automatically.

---

# 26. Final decision target

\[
\boxed{
\textbf{After repairing Qwen3 baseline validity with Qwen3-VL-4B-Instruct,
is a finite early window of direct image-token access sufficient for prompted CoT,
as it was in the calibrated Qwen2.5-VL-3B assay?}
}
\]

The purpose is to test the Qwen3 access regime fairly and cheaply—not to force a VAB-positive result.
