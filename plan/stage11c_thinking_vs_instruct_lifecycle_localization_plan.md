# Stage 11C — What Does Thinking Improve? Thinking-vs-Instruct Lifecycle Localization with a Short CoT Control

## 0. One-line objective

Localize **where the Qwen3-VL-2B Thinking variant gains over the Qwen3-VL-2B Instruct Direct variant** by equalizing task-critical visual evidence, then use prompted CoT on the same Instruct checkpoint as a compact control for the alternative explanation that the gain is merely due to eliciting longer reasoning.

Primary question:

\[
\boxed{
\textbf{Relative to Instruct Direct, does the Thinking variant gain mainly by obtaining/accessing
the right visual evidence, by reasoning better once that evidence is known, or both?}
}
\]

Secondary control question:

\[
\boxed{
\textbf{Is any residual downstream Thinking advantage reproducible by prompting the same
Instruct checkpoint to perform explicit CoT?}
}
\]

This is the final bounded attempt to develop the Thinking-performance story.

---

# 1. Why this stage is scientifically useful

The paper's first two claims are already substantially supported.

## Claim 1 — Reasoning-conditioned causal visual retrieval

\[
\boxed{
\text{reasoning demand}
\rightarrow
\text{target-specific causal visual retrieval}
}
\]

## Claim 2 — Causal lifecycle toward text-sufficient reasoning

\[
\boxed{
\text{visual retrieval}
\rightarrow
\text{short-lived internal/textual carriers}
\rightarrow
\text{text-sufficient computation}
}
\]

The unresolved performance question is:

> **What does the Thinking variant do differently from the Instruct variant that leads to better multimodal reasoning performance?**

Prior Thinking-vs-CoT work did **not** support a simple explanation based on keeping direct visual access open for longer.

Stage 11A produced too few clean Thinking-vs-CoT bottleneck localizations.

Stage 11B moved to a harder MathVision regime, but both modes rarely solved/finished the task, so the required Thinking-vs-CoT discordance never became feasible.

Stage 11C therefore changes the primary comparison:

\[
\boxed{
\textbf{Thinking vs Instruct Direct}
}
\]

and uses prompted CoT only as a same-checkpoint reasoning control.

---

# 2. Important causal scope

Qwen3-VL-2B-Thinking and Qwen3-VL-2B-Instruct are distinct model variants/checkpoints.

Therefore this stage may support:

> **The Thinking variant's performance advantage over the Instruct variant is operationally localized to upstream visual-evidence access, downstream reasoning, or both.**

It must **not** claim:

> turning on Thinking in the same weights causally produces the gain.

The prompted-CoT arm is different:

\[
\text{Instruct Direct}
\rightarrow
\text{Instruct + CoT prompt}
\]

uses the same Instruct checkpoint and serves as a control for **reasoning elicitation**.

---

# 3. Final Claim 3 if successful

Outcome-neutral form:

> **Relative to the Instruct variant, Thinking improves a specific stage of the visual-reasoning lifecycle; a same-checkpoint prompted-CoT control tests whether the residual advantage is explained by explicit reasoning elicitation alone.**

Possible final forms depend on the result:

### Upstream-dominant

> **Much of the Thinking variant's advantage arises before downstream reasoning, from more effective acquisition or access to task-critical visual evidence.**

### Downstream-dominant

> **The Thinking variant retains a substantial advantage after visual evidence is equalized, localizing much of the gain downstream of visual evidence acquisition.**

### Mixed

> **Thinking improves both access to task-critical visual evidence and subsequent reasoning over that evidence.**

### CoT control interpretation

If prompted CoT matches the Thinking oracle performance:

> **Much of the residual downstream advantage is reproducible by eliciting explicit reasoning from the Instruct checkpoint.**

If Thinking remains above CoT:

> **The residual Thinking advantage is not explained by prompted longer reasoning alone.**

---

# 4. Core operational decomposition

Let:

- \(T\): Qwen3-VL-2B-Thinking;
- \(D\): Qwen3-VL-2B-Instruct Direct;
- \(C\): Qwen3-VL-2B-Instruct with the frozen prompted-CoT protocol.

For each held-out item define a minimal task-critical visual evidence set:

\[
E^*
\]

such that:

\[
\text{question text}+E^*
\]

is sufficient to solve the task without the image.

## Native Thinking-vs-Direct gap

\[
\boxed{
G_{TD}^{N}
=
Acc_T^{N}
-
Acc_D^{N}
}
\]

This is the total model-variant performance difference on the selected cohort.

## Equal-Evidence Oracle gap

Remove the image and provide the **same correct \(E^*\)** to both variants:

\[
\boxed{
G_{TD}^{O}
=
Acc_T^{O}
-
Acc_D^{O}
}
\]

This is the residual difference after task-critical visual evidence is equalized.

## Gap closure

\[
\boxed{
\Delta G_{TD}
=
G_{TD}^{N}
-
G_{TD}^{O}
}
\]

Interpretation:

- large positive closure → upstream visual-evidence acquisition/access explains part of the native gap;
- persistent oracle gap → downstream reasoning/integration contributes;
- both → mixed mechanism.

This is an **operational gap localization**, not a formal causal mediation decomposition.

---

# 5. CoT as a compact same-checkpoint control

On a prospectively frozen subset, add:

\[
C^N,\quad C^O
\]

using the same Instruct checkpoint.

The key oracle contrasts are:

\[
\boxed{
G_{CD}^{O}
=
Acc_C^{O}-Acc_D^{O}
}
\]

and:

\[
\boxed{
G_{TC}^{O}
=
Acc_T^{O}-Acc_C^{O}.
}
\]

Interpretation:

### If

\[
T^O\approx C^O>D^O
\]

then the residual downstream benefit is largely reproducible by explicit reasoning elicitation.

### If

\[
T^O>C^O>D^O
\]

then Thinking retains an additional downstream advantage beyond prompted CoT.

### If

\[
T^O\approx D^O\approx C^O
\]

then most of the native Thinking advantage was upstream of downstream reasoning.

The CoT arm is a **control**, not the primary Claim 3 comparison.

---

# 6. Why not simply use harder MathVision again

Stage 11B showed that MathVision levels 3–5 on Qwen3-VL-2B moved into an uninformative regime where both models rarely committed correct answers.

Stage 11C therefore targets a **medium-hard sweet spot**, not maximal difficulty.

Desired regime:

\[
\boxed{
\text{Thinking has substantial success}
\quad\text{and}\quad
\text{Instruct Direct has substantial but lower success.}
}
\]

The selection objective is informative separation, not low absolute accuracy.

---

# 7. Development data: no new discovery experiment required initially

Use the already-completed Stage 9A / Stage 11A MathVision families as **development data only**.

They may be used to choose a source-side selection rule for a new held-out cohort.

Development data may inform:

- MathVision difficulty level;
- subject/category;
- solution depth;
- evidence type;
- \(E^*\)-eligibility predictors;
- approximate Thinking-vs-Direct separation.

They may **not** enter the Stage 11C confirmatory estimate.

This avoids another expensive benchmark-discovery loop.

---

# 8. Predeclare the held-out selection rule

Using development data, choose exactly one primary source-side rule before opening any new held-out model outcomes.

Candidate rule space is restricted to:

- MathVision levels 2–4;
- official subject/category;
- source solution length/depth;
- diagram/graph/table/geometry type;
- source-only \(E^*\)-eligibility features.

Level 5 is excluded from the primary Claim 3 cohort because the preceding harder screen was too completion-limited under Qwen3-VL-2B.

Do not use new held-out model correctness to redefine the rule.

At most one fallback rule may be frozen before held-out execution.

---

# 9. Selection-rule target

The development-selected rule should target approximately:

\[
\boxed{
30\%\le Acc_T^N\le70\%
}
\]

\[
\boxed{
10\%\le Acc_D^N\le50\%
}
\]

with an expected:

\[
\boxed{
G_{TD}^{N}\ge10\text{ percentage points}
}
\]

and:

\[
\boxed{
P(E^*\text{-eligible})\ge40\%.
}
\]

These are design targets, not post hoc inclusion rules.

No held-out family is dropped because its realized outcome differs from these expectations.

---

# 10. Held-out source pool

Use fresh, non-overlapping MathVision families.

Target source pool:

\[
\boxed{
200\text{–}300
}
\]

families satisfying the frozen source-side selection rule.

No overlap with:

- Stage 9A;
- Stage 11A;
- Stage 11B active discovery families;
- repaired/aliased prior families.

Perform source-similarity checks before inference.

Freeze the manifest before model outcomes.

---

# 11. \(E^*\) construction

For every source-pool family, construct:

\[
\boxed{
E^*
=
\text{the minimal set of image-derived propositions sufficient
to solve the task with the original question text}
}
\]

Constraints:

- 1–4 atomic facts;
- directly image-derived or trivial visual aggregation;
- no final answer;
- no downstream arithmetic derivation;
- no reasoning hint;
- no unnecessary visual facts.

Examples:

- `AB = 6`
- `∠ABC = 60°`
- `there are 4 shaded triangles`
- `the graph intersects y=2 at x=1 and x=5`

---

# 12. \(E^*\) blinding and sufficiency review

\(E^*\) must be frozen **before any held-out model outcome is opened**.

Reviewers may see:

- image;
- question;
- gold/source solution.

They may not see:

- Thinking output;
- Direct output;
- CoT output;
- any mode correctness.

Use two independent semantic reviews.

Labels:

- `SUFFICIENT`
- `INSUFFICIENT`
- `AMBIGUOUS`

Primary eligibility requires:

\[
\boxed{
\texttt{SUFFICIENT}
}
\]

Target agreement:

\[
\kappa\ge0.6
\]

where meaningful.

Do not broaden \(E^*\) rules after inference begins.

---

# 13. Primary / reserve cohort

Stop source annotation when either:

1. 120 clean \(E^*\)-eligible held-out families are obtained; or
2. 300 source families have been reviewed.

Freeze:

\[
\boxed{
80 \text{ primary eligible families}
}
\]

and:

\[
\boxed{
40 \text{ reserve eligible families}
}
\]

using deterministic hashing stratified by major subject/evidence type.

Minimum acceptable primary cohort:

\[
\boxed{
64
}
\]

eligible families.

If fewer than 64 clean eligible families exist, STOP Claim 3.

---

# 14. Runtime discipline

Use:

- Qwen3-VL-2B-Thinking;
- Qwen3-VL-2B-Instruct;
- BF16;
- TF32 off;
- greedy decoding;
- native preprocessing;
- batch size:
  \[
  \boxed{1}
  \]
  for all scientific generations.

Batch size 1 is mandatory because Stage 11B observed batch-size-sensitive generation divergence.

Use identical answer extraction rules across arms where output formats permit.

---

# 15. Common generation-cap calibration

Prior stages showed severe mode-dependent noncompletion under unsuitable caps/prompts.

Before primary execution, use exactly:

\[
\boxed{
12
}
\]

non-primary technical cases.

Evaluate common candidate caps:

\[
4096,\quad8192
\]

generated tokens.

Choose the **smallest common cap** for which:

- cap-hit rate is <10% in Thinking;
- cap-hit rate is <10% in Direct;
- no major mode-specific completion pathology appears.

If neither qualifies:

- use 8192;
- mark the stage completion-limited;
- do not increase one mode's cap separately.

If either mode has >25% cap-hit on the first 16 primary native runs, STOP before oracle execution.

This is a technical validity gate, not a performance gate.

---

# 16. Phase A — Native Thinking vs Instruct Direct

For all 80 primary families run:

## N-T

Original image + question under native Thinking.

## N-D

Original image + question under Instruct Direct.

Compute:

\[
G_{TD}^{N}.
\]

---

# 17. Native performance gate

Proceed to the Equal-Evidence Oracle only if all are true:

1. native Thinking accuracy:
   \[
   \boxed{\ge25\%}
   \]

2. native Direct accuracy:
   \[
   \boxed{\ge10\%}
   \]

3. point-estimate native gap:
   \[
   \boxed{
   G_{TD}^{N}\ge10\text{ pp}
   }
   \]

4. at least:
   \[
   \boxed{
   12
   }
   \]
   primary families are Thinking-correct / Direct-failed;

5. neither arm has major completion pathology.

If this gate fails:

\[
\boxed{
\text{STOP before oracle}
}
\]

and do not search another benchmark.

---

# 18. Phase B — Equal-Evidence Oracle

For the same primary families, remove the image and provide the same correct \(E^*\).

Fixed evidence block:

> **Task-relevant visual evidence:**  
> The following facts have been read correctly from the image and may be used as given:  
> - Fact 1: ...  
> - Fact 2: ...  
>  
> **Original question:**  
> ...

Run:

## O-T

Thinking variant, text-only question + \(E^*\).

## O-D

Instruct Direct, text-only question + identical \(E^*\).

Do not include:

- final answer;
- derived calculations;
- reasoning instructions;
- chain-of-thought hints;
- mode-specific evidence wording.

---

# 19. Oracle validity

Before opening primary oracle outcomes, verify:

## V1 — Evidence sufficiency

Question + \(E^*\) is semantically sufficient.

## V2 — No final-answer leakage

\(E^*\) contains only visual facts.

## V3 — Image independence

No image, multimodal cache, or hidden state is present.

## V4 — Evidence equality

The evidence block is byte-identical across T and D except unavoidable model-template wrappers.

## V5 — No mode-specific completion pathology

Oracle completion/cap rates remain comparable.

---

# 20. Neutral-text control

On a deterministic:

\[
\boxed{
24
}
\]

primary families frozen before outcomes, add a text-only neutral control of similar length/format that does not supply the missing visual facts.

Purpose:

> rule out the explanation that any oracle improvement is merely extra textual scaffolding.

Conditions:

- `NEUTRAL-T`
- `NEUTRAL-D`

This control is secondary.

Do not expand it beyond 24 cases.

---

# 21. Primary endpoints

Use exactly three primary endpoints.

## P1 — Native Thinking-vs-Direct gap

\[
\boxed{
P1
=
G_{TD}^{N}
=
Acc_T^N-Acc_D^N
}
\]

## P2 — Oracle residual Thinking-vs-Direct gap

\[
\boxed{
P2
=
G_{TD}^{O}
=
Acc_T^O-Acc_D^O
}
\]

## P3 — Evidence-equalization gap closure

\[
\boxed{
P3
=
\Delta G_{TD}
=
G_{TD}^{N}-G_{TD}^{O}
}
\]

Note:

\[
P3
=
(Acc_D^O-Acc_D^N)
-
(Acc_T^O-Acc_T^N)
\]

so a separate "differential oracle gain" endpoint would be algebraically redundant and is not added.

---

# 22. Practical interpretation margins

Predeclare:

## Meaningful native gap

\[
\boxed{
P1\ge10\text{ pp}
}
\]

## Meaningful evidence-access contribution

\[
\boxed{
P3\ge5\text{ pp}
}
\]

and, when \(P1>0\),

\[
\boxed{
\text{ClosureFraction}
=
P3/P1
\ge0.35
}
\]

## Meaningful residual downstream gap

\[
\boxed{
P2\ge5\text{ pp}
}
\]

Use confidence intervals in addition to these practical margins.

Do not rely on point estimates alone for a headline claim.

---

# 23. Outcome logic for the main Thinking-vs-Direct comparison

## Outcome A — Upstream-dominant

Requirements:

- P1 meaningfully positive;
- P3 meaningfully positive;
- P2 small / compatible with near-zero residual.

Supported:

> **A large component of the Thinking variant's advantage arises before downstream reasoning over correct evidence, implicating task-critical visual-evidence acquisition/access.**

## Outcome B — Downstream-dominant

Requirements:

- P1 meaningfully positive;
- P2 meaningfully positive;
- P3 small.

Supported:

> **The Thinking variant retains most of its advantage after visual evidence is equalized, localizing much of the gain downstream of visual evidence acquisition.**

## Outcome C — Mixed

Requirements:

- P1 positive;
- P3 meaningfully positive;
- P2 remains meaningfully positive.

Supported:

> **Thinking gains both from upstream visual-evidence acquisition/access and from downstream reasoning over already-correct evidence.**

## Outcome D — No informative native gap

If P1 is small or unstable:

> no Thinking-performance mechanism can be localized on this cohort.

STOP Claim 3.

## Outcome E — Oracle invalid/disruptive

If oracle completion collapses or both variants degrade strongly relative to neutral controls:

> the intervention is not interpretable.

Do not make a bottleneck claim.

---

# 24. Phase C — Short CoT control

Run only if:

1. the native T-vs-D gate passes;
2. the oracle is valid;
3. P2 indicates a nontrivial residual downstream gap **or** the paper needs to test whether explicit reasoning alone explains the downstream effect.

Freeze before outcomes a deterministic subset:

\[
\boxed{
48
}
\]

primary families, stratified by subject/evidence type.

Do not select this subset by T/D correctness or oracle response.

Run:

## N-C

Image + question with the exact prompted-CoT protocol on the Instruct checkpoint.

## O-C

Text-only question + identical correct \(E^*\) with the same prompted-CoT protocol.

This is the only CoT block.

---

# 25. CoT control quantities

Secondary quantities:

\[
\boxed{
G_{CD}^{N}
=
Acc_C^N-Acc_D^N
}
\]

\[
\boxed{
G_{TC}^{N}
=
Acc_T^N-Acc_C^N
}
\]

\[
\boxed{
G_{CD}^{O}
=
Acc_C^O-Acc_D^O
}
\]

\[
\boxed{
G_{TC}^{O}
=
Acc_T^O-Acc_C^O.
}
\]

The central downstream comparison is:

\[
\boxed{
T^O,\quad C^O,\quad D^O.
}
\]

---

# 26. CoT interpretation

## Pattern 1

\[
T^O\approx C^O>D^O
\]

Interpretation:

> **Much of the residual downstream benefit is reproducible by eliciting explicit reasoning from the same Instruct checkpoint.**

Do not claim the Thinking and CoT computations are mechanistically identical.

## Pattern 2

\[
T^O>C^O>D^O
\]

Interpretation:

> **Prompted CoT recovers part of the downstream benefit, but Thinking retains an additional advantage beyond explicit reasoning elicitation.**

## Pattern 3

\[
T^O>C^O\approx D^O
\]

Interpretation:

> **The residual downstream Thinking advantage is not explained by prompting the Instruct model to reason longer.**

## Pattern 4

\[
T^O\approx C^O\approx D^O
\]

Interpretation:

> **The native Thinking advantage was primarily upstream of downstream reasoning.**

---

# 27. What CoT can and cannot establish

Because C and D use the same Instruct checkpoint:

\[
C-D
\]

is a cleaner test of **reasoning elicitation** than T-D.

However:

- CoT prompting may not reproduce native Thinking's internal computation;
- output length alone is not the manipulated variable;
- prompt wording and decoding trajectory also change.

Safe claim:

> prompted explicit reasoning can/cannot reproduce the observed residual performance advantage.

Unsafe claim:

> longer reasoning tokens causally explain the Thinking advantage.

---

# 28. Secondary native evidence-state analysis

Only after P1–P3 are frozen, annotate native T/D reasoning states on a deterministic subset.

Use coarse categories:

- `CORRECT_SUFFICIENT`
- `OBSERVABLE_INSUFFICIENT`
- `CONFLICTING`
- `NOT_EXTERNALIZED`

Purpose:

> provide mechanistic interpretation for the oracle result.

Do not make these annotations the primary causal evidence.

Examples:

### If upstream-dominant

Ask whether Direct more often has observable insufficient/conflicting \(E^*\).

### If downstream-dominant

Ask whether both variants often already contain correct sufficient \(E^*\).

---

# 29. Statistics

Independent unit:

\[
\boxed{
\text{problem/image family}
}
\]

For P1–P3:

- equal family weighting;
- paired family bootstrap;
- 4,000 draws;
- fixed seed;
- 95% percentile intervals;
- multiplicity-aware intervals across the three primary endpoints.

Also report:

- exact paired discordance counts;
- McNemar-style descriptive summaries;
- major subject/evidence-type point estimates;
- completion/cap rates.

Do not treat:

- evidence atoms;
- tokens;
- reasoning steps

as independent observations.

CoT analyses are secondary and should not enlarge the primary hypothesis family.

---

# 30. Reserve rule

Open the 40 reserve eligible families only if:

1. P1 remains meaningfully positive;
2. the oracle is valid;
3. P2/P3 point estimates cleanly favor Outcome A, B, or C;
4. at least one key interval remains precision-limited;
5. no major subgroup reversal or completion pathology exists.

Maximum total eligible families:

\[
\boxed{
120
}
\]

Do not use reserve to rescue:

- absent native gap;
- invalid oracle;
- wrong-direction primary effects.

---

# 31. Compute budget

## Source annotation

CPU / model-agent review only.

## Primary native T/D

\[
80\times2=160
\]

runs.

## Primary oracle T/D

Conditional on native gate:

\[
80\times2=160
\]

runs.

## Neutral control

\[
24\times2=48
\]

short text-only runs.

## CoT control

Conditional:

\[
48\times2=96
\]

runs.

## Reserve

At most:

\[
40\times4=160
\]

additional T/D native+oracle runs.

Target primary GPU allocation:

\[
\boxed{
<5 \text{ GPU-hours}
}
\]

Target including conditional CoT:

\[
\boxed{
<6.5 \text{ GPU-hours}
}
\]

Hard total stop:

\[
\boxed{
8 \text{ GPU-hours}
}
\]

without explicit approval.

No benchmark-wide generation outside the frozen cohort.

---

# 32. Failure-prevention rules learned from Stages 11A/11B

1. **No explicit evidence probe as a primary assay.**
   Stage 11A showed strong mode-dependent cap confounding.

2. **No maximal-hardness selection.**
   Stage 11B showed that too-hard 2B tasks can collapse into T-/D-/C- noncompletion.

3. **Batch size 1 only.**
   Stage 11B observed batch-size-sensitive divergence.

4. **No outcome-selected oracle cohort.**
   Do not select only Thinking-correct / Direct-wrong cases.

5. **No post-null benchmark search.**
   If the frozen held-out cohort lacks a native T-D gap, stop.

6. **No mode-specific token-cap rescue.**
   One common cap for all arms.

7. **No \(E^*\) repair after model outcomes.**
   Source-side evidence representations are frozen first.

---

# 33. Required figures

## Figure 1 — Claim 3 design

\[
\text{Image}
\rightarrow
E^*
\rightarrow
\text{downstream reasoning}
\]

Show native T/D and the intervention:

\[
\text{replace visual acquisition with identical correct }E^*.
\]

## Figure 2 — Held-out native Thinking-vs-Direct performance

Show:

\[
T^N,\quad D^N
\]

with paired family effects and discordances.

## Figure 3 — Equal-Evidence Oracle

Show:

\[
T^N,\quad D^N,\quad T^O,\quad D^O.
\]

## Figure 4 — Gap localization

Centerpiece Claim 3 panel:

\[
G_{TD}^{N}
\]

\[
G_{TD}^{O}
\]

\[
\Delta G_{TD}.
\]

Annotate result as:

- upstream-dominant;
- downstream-dominant;
- mixed.

## Figure 5 — Short CoT control

Only if executed:

\[
D^O,\quad C^O,\quad T^O
\]

with secondary native comparison.

Takeaway:

> whether prompted explicit reasoning can reproduce the residual downstream advantage.

---

# 34. Required artifacts

Produce:

1. `stage11c_thinking_vs_instruct_spec.md`
2. `stage11c_development_selection_rule.json`
3. `stage11c_heldout_source_manifest.json`
4. `stage11c_e_star_gold.parquet`
5. `stage11c_e_star_sufficiency_review.json`
6. `stage11c_primary_split.json`
7. `stage11c_cap_validation.json`
8. `stage11c_native_td_results.parquet`
9. `stage11c_native_gate.json`
10. `stage11c_oracle_td_results.parquet`
11. `stage11c_oracle_validity.json`
12. `stage11c_primary_inference.json`
13. `stage11c_neutral_control.json`
14. optional `stage11c_cot_control.parquet`
15. optional `stage11c_native_evidence_states.parquet`
16. optional `stage11c_reserve_extension.json`
17. `stage11c_resource_accounting.json`
18. `stage11c_summary.md`

---

# 35. Paper integration by outcome

## If upstream-dominant

Claim 3:

> **Compared with the Instruct variant, Thinking's performance advantage is substantially reduced when task-critical visual evidence is equalized, linking part of the gain to more effective visual-evidence acquisition/access.**

This directly connects Claim 3 to Claim 1.

## If downstream-dominant

Claim 3:

> **The Thinking variant retains a substantial advantage over Instruct Direct after receiving identical correct visual evidence, localizing much of the gain to downstream reasoning/integration.**

Then use CoT to test whether this is merely elicited explicit reasoning.

This connects Claim 3 to Claim 2.

## If mixed

Claim 3:

> **Thinking improves both access to task-critical visual evidence and reasoning over already-correct evidence.**

Use CoT to localize the residual downstream component.

## If no informative result

Do not promote Claim 3.

Discussion wording:

> **The Thinking variant is more accurate in our earlier matched setting, but the mechanism of that advantage remains unresolved.**

Finalize the paper around Claims 1 and 2.

---

# 36. Null discipline

A small \(\Delta G_{TD}\) does not mean visual retrieval is unimportant.

It means:

> equalizing the chosen task-critical \(E^*\) did not explain much of the T-D performance gap on this cohort.

Possible reasons include:

- downstream reasoning dominates;
- \(E^*\) omits useful representational detail;
- both variants already recover \(E^*\);
- oracle presentation changes computation.

A large \(\Delta G_{TD}\) does not prove the previously identified retrieval mechanism is the sole cause of the Thinking advantage.

It supports a broader upstream visual-evidence acquisition/access contribution.

Likewise, a CoT control match does not prove native Thinking and prompted CoT use the same algorithm.

---

# 37. Stop rules

Stop Stage 11C and Claim 3 development if any occurs:

1. fewer than 64 clean held-out \(E^*\)-eligible families;
2. native T-D performance gate fails;
3. common-cap completion validity fails;
4. oracle validity fails;
5. primary result depends on outcome-selected filtering;
6. result reverses strongly across major predeclared strata;
7. hard total compute cap would be exceeded.

Do not:

- search another benchmark after a failed held-out cohort;
- change \(E^*\) after outcomes;
- extend only one model's generation budget;
- promote CoT from control to a new exploratory branch.

---

# 38. Exactly one recommendation at completion

## If P1–P3 cleanly identify upstream, downstream, or mixed advantage

Recommend:

> Promote Claim 3 using the held-out Thinking-vs-Instruct localization, with prompted CoT only as the same-checkpoint reasoning control.

## Otherwise

Recommend:

> Keep Thinking-vs-Instruct as an unresolved performance observation and finalize the paper around the established causal retrieval and visual-to-text lifecycle claims.

Do not launch another mechanism search automatically.

---

# 39. Final decision target

This stage exists to answer:

\[
\boxed{
\textbf{What stage of the visual-reasoning lifecycle distinguishes the Thinking variant
from the Instruct variant, and can prompted CoT on the same Instruct weights reproduce
the downstream part of that advantage?}
}
\]

The main comparison is:

\[
\boxed{
\textbf{Thinking vs Instruct Direct}
}
\]

The CoT arm is intentionally a short control, not the main story.
