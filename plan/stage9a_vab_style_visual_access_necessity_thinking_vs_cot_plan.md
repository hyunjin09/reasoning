# Stage 9A — VAB-Style Visual Access Necessity: Thinking vs CoT

## 0. Status and scope

This is the **decisive Stage 9A visual-access regime test**.

The previously completed native-usage comparison should be treated as the **Stage 9A pilot / native visual-use characterization**. That pilot did **not** establish that Qwen3-VL-2B-Thinking has more recurrent/demand-aligned visual retrieval than Qwen3-VL-2B-Instruct+CoT. However, it measured **native usage / retrieval-like activity**, not the functional **necessity of continued direct image-token access**.

This Stage 9A experiment therefore asks the actual causal regime question:

\[
\boxed{
\textbf{Does native Thinking rely on direct image-token access later in reasoning
than prompted CoT does?}
}
\]

The experiment reimplements the **Visual Access Sweep / Visual Access Boundary (VAB)** intervention from Osaka et al., *Visual Access Boundaries in Vision-Language Model Reasoning* (arXiv:2607.12815, 2026).

The goal is to match the published intervention and controlled task as closely as possible from the paper specification. No exact source-code reproduction is claimed.

---

# 1. Why this experiment is necessary

The project currently has evidence for **local causal visual use**: visual source/value interventions can alter upcoming visual evidence late in reasoning.

VAB asks a stricter question:

> If generated tokens are prevented from directly attending to image-token keys after a layer/time cutoff, does task performance deteriorate?

These are not equivalent.

A visual pathway can be causally used under native computation yet be non-necessary under deletion because redundant internal state compensates.

\[
\boxed{
\text{visual usage}
\neq
\text{visual necessity}
}
\]

The Stage 9A pilot characterized usage.

This Stage 9A proper experiment directly tests necessity.

---

# 2. Paper-level claim this experiment can unlock

High-upside hypothesis:

\[
\boxed{
\textbf{Prompted CoT has a finite early visual-access boundary,
whereas native Thinking continues to require direct image-token access later in reasoning.}
}
\]

A positive result would support:

> **Thinking does not necessarily look at vision more often, but its later reasoning remains more functionally dependent on direct visual access.**

This would reconcile:
- Stage 9A pilot: no stronger Thinking retrieval-frequency phenotype;
- our earlier source-sensitive causal re-access results;
- VAB: prompted CoT often does not require prolonged direct image-token access.

---

# 3. What a positive result would mean

### Prompted CoT

\[
\text{early visual access}
\rightarrow
\text{image-derived internal state}
\rightarrow
\text{mostly language-side continuation}
\]

### Native Thinking

\[
\text{visual access}
\rightarrow
\text{reasoning}
\rightarrow
\text{later direct visual access remains necessary}
\]

Do **not** claim that Thinking attends to the image at every token.

The target claim is **late/recurrent necessity**, not continuous attention.

---

# 4. What a null would mean

If:

\[
VAB_{\text{Thinking}}
\approx
VAB_{\text{CoT}}
\]

then do not claim that Thinking relies on prolonged direct image-token access.

Instead:

> Both modes can locally use visual sources, but late direct access may be functionally redundant because image-derived information is already available through internal state.

This strengthens:

\[
\boxed{
\text{source-sensitive causal use}
\neq
\text{necessity under access removal}
}
\]

A null does not invalidate the earlier dynamic source-retargeting result.

---

# 5. Faithfulness to the VAB paper

## 5.1 Reproduce directly from the paper

1. **Visual access** = direct self-attention from generated-token queries to image-token keys.
2. Access is allowed only inside:

\[
\ell\le\ell_{\text{cutoff}},
\qquad
t\le t_{\text{cutoff}}
\]

3. Outside the rectangle, generated-query → image-key attention logits are set to \(-\infty\) before softmax.
4. Prompt/prefill tokens are unaffected by the main intervention.
5. Previously propagated image-derived hidden-state information remains intact.
6. Effective token window:

\[
t_{\mathrm{eff}}=\min(t_{\text{cutoff}},T_{\mathrm{gen}})
\]

7. Main tolerance:

\[
\boxed{\epsilon=0.05}
\]

8. Sensitivity:

\[
\epsilon\in\{0.03,0.05,0.07,0.10\}
\]

9. Greedy decoding on frozen checkpoints.
10. Include the VAB artifact controls:
   - late-layer query-text → image block;
   - null-sink attention-mass control.

## 5.2 Reimplementation boundary

The paper gives the mathematical intervention, controlled-task specification, prompts, and controls. Exact original code should not be assumed.

If implementation details are unspecified:
- use a documented fixed random seed;
- freeze the synthetic generator;
- freeze the sweep grid;
- freeze backend/mask semantics before scientific outcomes;
- do not claim bitwise reproduction.

This is a:

\[
\boxed{
\textbf{paper-specification reimplementation of VAB on Qwen3-VL}
}
\]

---

# 6. Models and arms

## Arm D — Instruct Direct
**Qwen3-VL-2B-Instruct**

Purpose:
- VAB Direct baseline;
- Direct full-access anchor.

## Arm C — Instruct CoT
**Qwen3-VL-2B-Instruct**

Use the VAB-style wording:

> Think step by step. You must write intermediate steps.

Use the paper-style final braced option-key format.

## Arm T — Native Thinking
**Qwen3-VL-2B-Thinking**

Use the native Thinking chat/template path.

Do not append another step-by-step instruction.

Use the same question/options/final braced option-key requirement.

---

# 7. Precision and execution path

Use:
- BF16 model execution;
- TF32 off;
- same image preprocessing across matched checkpoints;
- same attention backend for full-access and masked conditions.

Because explicit image-key masking is required, use an attention backend that correctly exposes/applies the additive mask.

Do not compare a masked eager path to an unmasked FlashAttention path.

For every arm, the scientific baseline is the **same mask-capable execution path with intervention disabled**.

---

# 8. VAB-style controlled dataset

Primary experiment uses a controlled synthetic counting task modeled directly on VAB.

## Image format
- 256 × 256 RGB
- matplotlib-generated
- 6–7 objects/image
- fixed preregistered random seed

## Attributes

### Color
- red
- green
- yellow
- blue

### Shape
- star
- circle
- triangle
- square

### Size
- xs = 18 px
- s = 24 px
- l = 30 px
- xl = 36 px

### Location
- upper-left
- upper-right
- lower-left
- lower-right

### Angle
- 0°
- 45°
- 90°
- 135°

---

# 9. Primary task subset

The VAB paper's clean main boundary result is centered on color/shape counting.

Use:

\[
\boxed{
150 \text{ synthetic images}
}
\]

with:

\[
\boxed{
2 \text{ primary queries/image: color + shape}
}
\]

for:

\[
\boxed{
300 \text{ primary query instances}
}
\]

per arm.

Use identical images, questions, targets, and option permutations across D/C/T.

Other attributes are not rescue endpoints.

---

# 10. Prompt format

## Direct

```text
How many {attribute_value} objects are in the image?
options: {A: ..., B: ..., C: ..., D: ..., E: ...}
Answer with the option key only (no ':' or value).
Respond with a single final line in the curly braces format: {A}
```

## CoT

```text
How many {attribute_value} objects are in the image?
options: {A: ..., B: ..., C: ..., D: ..., E: ...}
Think step by step. You must write intermediate steps.
Respond in curly braces format: {A}
```

## Thinking

Use the same question/options/final-answer format but rely on the native Thinking template.

Option permutations are sampled once and frozen.

No constrained decoding.

---

# 11. Decoding

To match VAB:

\[
\boxed{\text{greedy decoding}}
\]

Use:
- `do_sample = false`
- native EOS stopping
- `max_new_tokens = 40960`

Report:
- completion rate
- cap rate
- mean/median generated tokens

for all arms.

---

# 12. CoT elicitation validity gate

Before interpreting VAB:

1. ≥90% of CoT trajectories contain nontrivial intermediate reasoning before the final option;
2. CoT median generation length is materially above Direct;
3. option extraction remains valid.

Do not try multiple CoT prompts after failure.

If the single frozen VAB-style prompt does not instantiate meaningful CoT on Qwen3-VL-2B-Instruct, report that limitation and stop the CoT-vs-Thinking VAB claim.

---

# 13. Exact intervention definition

Let:
- \(V\) = image-token key positions;
- \(G_t\) = generated-token query at generation step \(t\);
- \(L\) = number of decoder layers.

For layer \(\ell\), modify attention logits:

\[
M^\ell_{ij}=-\infty
\]

for all:

\[
i=G_t,\quad j\in V
\]

whenever:

\[
\boxed{
\ell>\ell_{\text{cutoff}}
\quad\text{or}\quad
t>t_{\text{cutoff}}
}
\]

Otherwise retain the native mask.

Direct image access is therefore allowed only when both:

\[
\ell\le\ell_{\text{cutoff}}
\]

and:

\[
t\le t_{\text{cutoff}}
\]

hold.

---

# 14. Cached-decoding semantics

At generation step \(t\):

- image-token K/V remain in cache;
- prompt/text K/V remain unchanged;
- only the current generated query's direct attention to image-key positions is masked;
- no previously propagated residual/text-side image information is erased.

Stage 9A tests:

\[
\boxed{\text{continued direct image-token access}}
\]

not all previously incorporated visual information.

---

# 15. Cutoff indexing

Use 1-indexed conceptual notation in reports and document exact implementation indexing.

## Layer
- `0`: no generated-query → image-key access
- `1 ... L`: access through that decoder layer
- `L`: full layer-axis access

## Token
- `0`: no generated token directly accesses image keys
- positive \(t\): first \(t\) generated tokens retain access
- `FULL`: no token-axis restriction

For Thinking, all native thinking tokens count on this generated-time axis.

---

# 16. Sweep grid

Freeze before outcomes.

## Layer grid

Use every decoder-layer cutoff:

\[
\boxed{
\ell_{\text{cutoff}}\in\{0,1,\ldots,L\}
}
\]

## Token grid

\[
\boxed{
t_{\text{cutoff}}
\in
\{0,1,2,4,8,16,32,64,128,256,512,1024,2048,4096,\text{FULL}\}
}
\]

For shorter trajectories, declared high cutoffs collapse to full access through \(t_{\mathrm{eff}}\).

Do not add token cutoffs after viewing scientific heatmaps.

---

# 17. Sweep structure

## Direct
Run a full layer sweep at token `FULL`:

\[
(\ell_{\text{cutoff}},\text{FULL})
\]

## CoT
Run the full 2D layer × token sweep.

## Thinking
Run exactly the same full 2D grid as CoT.

This symmetric 2D CoT-vs-Thinking comparison is the core novel test.

---

# 18. Full-access baselines

For arm \(p\in\{D,C,T\}\):

\[
A^p_{\text{full}}
\]

is accuracy at:

\[
(\ell=L,\;t=\text{FULL})
\]

using the same mask-capable path.

The full-access sentinel must reproduce the disabled-intervention path before scientific interpretation.

---

# 19. VAB definitions

For arm \(p\):

\[
A^p(\ell,\tau)
\]

is accuracy at cutoff \((\ell,\tau)\).

Define:

\[
\boxed{
\Delta_p(\ell,\tau)
=
A^p_{\text{full}}-A^p(\ell,\tau)
}
\]

Primary tolerance:

\[
\boxed{\epsilon=0.05}
\]

Performance-preserving region:

\[
\Delta_p(\ell,\tau)\le0.05
\]

---

# 20. Direct-anchored criteria

For VAB comparability also define:

\[
\Delta_{DA,C}(\ell,\tau)
=
A^D_{\text{full}}-A^C(\ell,\tau)
\]

\[
\Delta_{DA,T}(\ell,\tau)
=
A^D_{\text{full}}-A^T(\ell,\tau)
\]

These ask whether restricted CoT/Thinking can still reach Direct full-access performance.

If the target is unattainable, report `N/A`.

The **own-baseline criterion is primary** for Thinking-vs-CoT dependence.

---

# 21. Boundary reporting

Do not hide a 2D access region behind an arbitrary single point.

Report:

1. full 2D accuracy heatmap;
2. \(\epsilon\)-admissible region;
3. Pareto-minimal admissible cutoffs;
4. full-time layer boundary \(\ell_p^*\) at `t=FULL`;
5. full-depth temporal boundary \(\tau_p^*\) at \(\ell=L\);
6. paper-style representative 2D point only under a frozen deterministic tie rule.

---

# 22. Primary scientific endpoints

## P1 — CoT temporal VAB replication

Does Qwen3-VL-2B-Instruct+CoT show a finite temporal boundary?

\[
\boxed{
\tau_C^* < \text{full reasoning horizon}
}
\]

while remaining within 5 pp of full CoT accuracy.

This is the VAB replication prerequisite.

## P2 — Thinking temporal access requirement

Compare:

\[
\boxed{
\tau_T^*-\tau_C^*
}
\]

Primary hypothesis:

\[
\boxed{
\tau_T^*>\tau_C^*
}
\]

Also report:

\[
\rho_p
=
\frac{\tau_p^*}
{\operatorname{median}(T_{\mathrm{gen},p})}
\]

as a descriptive normalized boundary.

## P3 — CoT-boundary transfer test

Take a frozen CoT-sufficient cutoff:

\[
(\ell_C^*,\tau_C^*)
\]

and evaluate Thinking at the identical cutoff.

Define:

\[
\Gamma
=
\Delta_T(\ell_C^*,\tau_C^*)
-
\Delta_C(\ell_C^*,\tau_C^*)
\]

Strong evidence requires:

\[
\Gamma>0
\]

with:

\[
\Delta_T(\ell_C^*,\tau_C^*)>0.05
\]

and:

\[
\Delta_C(\ell_C^*,\tau_C^*)\le0.05
\]

## P4 — Thinking own-boundary structure

Does Thinking require:
- later token access;
- deeper layer access;
- or a qualitatively broader access region?

Temporal extension is the primary target.

---

# 23. Statistical inference

Primary independent unit:

\[
\boxed{\text{synthetic image}}
\]

because color/shape queries share the same scene.

Use:
- 4000 image-cluster bootstrap draws;
- paired resampling across arms/cutoffs;
- 95% CIs for accuracy-damage contrasts;
- bootstrap boundary distributions.

For each bootstrap:
1. resample images;
2. recompute full-access accuracy;
3. recompute admissible regions;
4. recompute boundary summaries.

Do not treat queries, tokens, or grid points as independent.

---

# 24. Tolerance sensitivity

Without rerunning inference, extract boundaries for:

\[
\epsilon\in\{0.03,0.05,0.07,0.10\}
\]

Report whether:

\[
\tau_T^*>\tau_C^*
\]

is stable across tolerances.

---

# 25. Intervention validity tests

Before full scientific execution, run 8–16 bounded examples.

Require:

## V1 — Full-access no-op
At \((L,\text{FULL})\), reproduce disabled-mask:
- generated tokens under greedy decoding;
- logits within frozen tolerance;
- answer extraction.

## V2 — Mask zeroing
For every masked image key:

\[
a_{ij}=0
\]

post-softmax.

## V3 — Layer semantics
Mask starts exactly after \(\ell_{\text{cutoff}}\).

## V4 — Token semantics
Mask starts exactly after \(t_{\text{cutoff}}\).

## V5 — Prefill preservation
Main Visual Access Sweep does not alter image/question prefill.

## V6 — Cache continuation
Autoregressive cached decoding remains correct after crossing the cutoff.

Technical failure here requires implementation repair before science.

---

# 26. Artifact control 1 — late-layer query-text block

VAB considers a bypass in which prompt/query-text states continue to access image tokens and later pass information to generated tokens.

On frozen representative cutoff points near the boundaries, rerun with:

1. standard generated-token → image-key block;
2. additionally block query-text → image-key attention from the same layer cutoff upward.

Early-layer query-text access remains intact.

The qualitative CoT/Thinking conclusion should survive.

---

# 27. Artifact control 2 — null-sink

Standard \(-\infty\) masking redistributes attention over remaining real tokens.

Implement the VAB-style null-sink control on a frozen subset:

- removed image attention mass is redirected to a dummy nonvisual sink;
- remaining real-token attention should not inherit that mass.

Run at:
- full-access sentinel;
- one harmful cutoff;
- CoT boundary;
- Thinking boundary or nearest available point.

If exact null-sink implementation is infeasible, report that limitation explicitly.

---

# 28. Full-access floor gate

Chance for five-option counting is 20%.

Require primary full-access arm/attribute accuracy to be clearly above floor:

\[
\boxed{
A^p_{\text{full}}\ge50\%
}
\]

If an arm/attribute fails the gate, do not call preservation of low accuracy a meaningful VAB.

Color/shape are primary to minimize this problem.

---

# 29. Main claim gate

Support greater Thinking reliance only if all hold:

1. CoT exhibits a finite VAB.
2. Thinking requires a later temporal boundary than CoT.
3. The CoT-sufficient cutoff causes >5 pp degradation in Thinking.
4. The Thinking-vs-CoT damage difference has positive bootstrap support or comparably strong boundary separation.
5. The result survives reasonable \(\epsilon\) sensitivity.
6. Query-text and null-sink controls preserve the qualitative distinction.
7. Full-access performance is above the floor gate.

A visually different heatmap alone is insufficient.

---

# 30. Outcome matrix

## Outcome A — CoT finite VAB, Thinking substantially later VAB

Supported:

> **Prompted CoT can operate after direct image-token access becomes dispensable, while native Thinking remains functionally dependent on direct visual access later into reasoning.**

Next scientific question:

\[
\boxed{
\text{Is Thinking's late necessity sparse and demand-aligned rather than one later monotonic boundary?}
}
\]

This would motivate Stage 9B: an event-level **Visual Access Schedule** experiment.

## Outcome B — Similar finite VABs

Supported:

> Both reasoning modes can continue largely over already integrated image-derived state after a finite access region.

Implication:

\[
\boxed{
\text{late causal visual use can be redundant rather than globally necessary}
}
\]

Stop the Thinking-specific prolonged-access story.

## Outcome C — Thinking earlier/shallower than CoT

Reject the current hypothesis.

Possible interpretation:

> Thinking may integrate visual evidence earlier or more efficiently.

Do not reinterpret as recurrent late necessity.

## Outcome D — Neither arm has interpretable VAB

Distinguish:
- low full-access task accuracy;
- intervention implementation problem;
- genuine Qwen3-VL difference.

Do not infer Thinking-specific access from an ill-defined boundary.

---

# 31. Optional MathVision bridge — only after positive controlled result

Do not run a full MathVision 2D sweep initially.

If Outcome A is obtained, run a bounded bridge on:

\[
\boxed{64 \text{ frozen Stage 9A-pilot MathVision items}}
\]

using:
- full access;
- CoT-sufficient cutoff;
- Thinking-own cutoff;
- very-early/no-access control.

Use the existing reviewed answer extraction/scoring path.

Question:

> Does the controlled Thinking-specific necessity difference extend to long-form natural multimodal reasoning?

Do not launch this bridge after a null controlled result.

---

# 32. Relation to the Stage 9A pilot

The completed Stage 9A pilot asked:

\[
\boxed{
\text{How often does retrieval-like visual-use activity appear?}
}
\]

This Stage 9A proper experiment asks:

\[
\boxed{
\text{How long must direct image-token access remain available?}
}
\]

They can dissociate.

Possible meaningful outcomes include:

\[
\boxed{
\text{fewer retrieval episodes}
+
\text{greater late necessity}
}
\]

or:

\[
\boxed{
\text{native late visual use}
+
\text{late access redundancy}
}
\]

This experiment does not rerun the failed frequency claim.

---

# 33. Why this matters for the paper

A positive result would produce a sharper conceptual contrast:

1. Reasoning can causally retarget visual sources \(A\rightarrow B\rightarrow A\).
2. Retrieval activity itself is not uniquely more frequent in Thinking.
3. Yet direct image-token access remains necessary later in native Thinking than in prompted CoT.
4. Therefore the important distinction is not **how often** retrieval-like activity appears, but whether later reasoning **functionally depends** on renewed source access.

Potential paper contrast:

\[
\boxed{\textbf{CoT: Visual Access Boundary}}
\]

versus, only after an event-level follow-up:

\[
\boxed{\textbf{Thinking: Visual Access Schedule}}
\]

Do not call it a schedule from this sweep alone.

---

# 34. What this experiment does NOT establish

Even if positive, it does not prove:
- why Thinking needs later visual access;
- that every Thinking step accesses vision;
- that late access explains the entire accuracy advantage;
- cross-family generalization;
- absence of persistent visual representations;
- that the original VAB result is wrong.

The supported claim is narrower:

> Under the same VAB-style causal access restriction, native Qwen3-VL Thinking retains a later functional requirement for direct image-token access than matched Instruct-CoT.

---

# 35. Required artifacts

1. `stage9a_vab_reimplementation_spec.md`
2. `stage9a_synthetic_dataset_manifest.json`
3. `stage9a_prompt_and_option_manifest.json`
4. `stage9a_intervention_validation.json`
5. `stage9a_full_access_baselines.json`
6. `stage9a_direct_layer_sweep.parquet`
7. `stage9a_cot_2d_sweep.parquet`
8. `stage9a_thinking_2d_sweep.parquet`
9. `stage9a_vab_regions.json`
10. `stage9a_boundary_bootstrap.json`
11. `stage9a_epsilon_sensitivity.json`
12. `stage9a_cot_boundary_transfer.json`
13. `stage9a_query_text_block_control.json`
14. `stage9a_null_sink_control.json`
15. `stage9a_summary.md`

Optional only after positive primary gate:

16. `stage9a_mathvision_bridge64.json`

---

# 36. Key figures

## Figure 1 — VAB intervention schematic
Allowed rectangle in layer × generation time.

## Figure 2 — CoT VAB heatmap
Instruct-CoT accuracy over layer × token cutoff.

## Figure 3 — Thinking VAB heatmap
Same sweep for native Thinking.

## Figure 4 — Boundary comparison
Show \(\ell_C^*,\ell_T^*,\tau_C^*,\tau_T^*\), bootstrap uncertainty, and tolerance sensitivity.

## Figure 5 — CoT-boundary transfer
At a cutoff sufficient for CoT, compare:

\[
\Delta_C
\quad\text{vs}\quad
\Delta_T
\]

## Figure 6 — Artifact controls
Standard mask vs query-text block vs null-sink near frozen boundary points.

---

# 37. Exactly one next-action recommendation rule

At completion, output exactly one recommendation.

### If Outcome A
Recommend:

> proceed to Stage 9B event-level visual-necessity scheduling to test whether Thinking requires sparse demand-aligned re-access rather than simply a later monotonic boundary.

### Otherwise
Recommend:

> stop the Thinking-specific prolonged-access branch and retain causal visual use versus functional necessity as the boundary result.

Do not launch the recommendation automatically.

---

# 38. Final decision target

\[
\boxed{
\textbf{When direct generated-token access to image tokens is causally removed,
does native Thinking require that access later in generation than prompted CoT?}
}
\]

This is the decisive Stage 9A causal visual-access regime test.
