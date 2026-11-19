# Stage 10A-R — Bounded Causal Phase-Transition Localization

## 0. One-line objective

Localize, within the same successful reasoning trajectories, the functional transition from a **direct-visual-access-dependent regime** to a **text-sufficient reasoning regime**.

Primary question:

\[
\boxed{
\textbf{As visual evidence is resolved during reasoning, does direct visual necessity decrease
while the generated reasoning prefix becomes sufficient to solve the task without the image?}
}
\]

This is a bounded follow-up to Stage 10A.

It is the decisive experiment for whether **phase-structured multimodal reasoning** can remain a headline empirical claim.

---

# 1. Why this experiment is necessary

Stage 10A established two important facts:

1. Fresh image-free replay from later reasoning prefixes can solve many problems.
2. Counterfactually editing a self-generated visual fact can redirect downstream reasoning.

Thus, generated reasoning text is a genuine causal carrier.

However, Stage 10A did **not** establish a handoff boundary:

\[
N_V(t_{\text{pre}})-N_V(t_{\text{post}})=0
\]

under the frozen anchors.

The likely issue is that the previous `pre` anchor was already too late: it often contained object inventories or other visual evidence.

Therefore the remaining question is not whether later text can matter. It is:

\[
\boxed{
\textbf{Can we prospectively localize an earlier transition where visual dependence falls
as text sufficiency rises?}
}
\]

No anchor may be moved after intervention outcomes are opened.

---

# 2. Paper claim this stage can support

If successful:

> **Multimodal reasoning transitions from a direct visual-evidence acquisition regime into a text-sufficient reasoning regime once the task-relevant visual evidence has been resolved in the reasoning trace.**

Combined with prior dynamic re-access results, this supports the broader framework:

\[
\boxed{
V_A
\rightarrow
T_1
\rightarrow
V_B
\rightarrow
T_2
\rightarrow
V_A
}
\]

where new visual demands can reopen a perceptual-access regime.

Do **not** require a sharp discontinuity.

"Phase" is defined functionally by changing causal dependence and sufficiency.

---

# 3. What a null would mean

If the prospectively frozen anchors do not show:

\[
N_V(t)\downarrow
\]

together with:

\[
S_T(t)\uparrow
\]

then do not continue searching for a better boundary.

The paper should demote `phase-structured reasoning` from headline claim to discussion-level interpretation.

The already established results remain:

- reasoning-conditioned visual retrieval;
- dynamic source retargeting;
- visual alignment \(\neq\) causal retrieval;
- generated text is a causal carrier;
- native visual use \(\neq\) ablation necessity.

---

# 4. Model

Use:

\[
\boxed{
\textbf{Qwen3-VL-4B-Thinking}
}
\]

with the exact native execution path already validated in Stage 9A.5 / Stage 10A.

Freeze:

- checkpoint revision;
- BF16;
- TF32 off;
- greedy decoding;
- native Thinking template;
- DeepStack;
- image preprocessing;
- mask-capable backend;
- answer extraction/scoring.

No model or decoding changes.

---

# 5. Dataset

Reuse the same controlled counting corpus.

## Primary cohort

Select:

\[
\boxed{
24 \text{ independent images}
}
\]

with at most one query per image.

Target balance:

- 12 color-count;
- 12 shape-count.

Eligibility:

1. native FULL trajectory has a valid final answer;
2. native FULL answer is correct;
3. the trajectory contains enough explicit reasoning to identify the frozen semantic anchor sequence below;
4. source fact is unambiguous.

This is explicitly a **successful-reasoning phase-localization cohort**.

The claim is about the computation supporting successful reasoning, not benchmark-population prevalence.

## Reserve

Freeze:

\[
\boxed{
8 \text{ additional independent images}
}
\]

before intervention outcomes.

Do not use them unless the precision-extension gate is met.

---

# 6. Anchor taxonomy

Every primary trajectory receives the same prospective semantic anchor taxonomy.

Anchor annotation must be completed and sealed before any Stage 10A-R intervention outcome is opened.

## A0 — Start-of-reasoning

Immediately after multimodal prefill and before any substantive self-generated visual reasoning has been emitted.

For fresh text-only replay, this is effectively:

\[
\text{question + task prompt only}
\]

with no image.

Purpose:

> establish the earliest visual-dependent / text-insufficient reference point.

---

## A1 — First task-relevant visual observation

Immediately after the first explicit observation relevant to the asked attribute.

Examples:

- first red object identified;
- first circle identified.

The answer must not yet be textually determined.

---

## A2 — Partial evidence accumulation

After the model has accumulated multiple task-relevant observations but before the prefix is sufficient to determine the correct task answer from text alone.

Operational rule:

- at least two relevant evidence units are present, where possible;
- the answer remains underdetermined from the text prefix alone to a blinded semantic reviewer.

If no meaningful partial-accumulation point exists, mark A2 unavailable for that item.

Do not invent one.

---

## A3 — First textually complete evidence point

The earliest point at which a reviewer, using **only the question and generated reasoning text up to that point**, can determine the correct answer without inspecting the image.

Important:

- A3 need not contain an explicit final count statement;
- it may be an inventory from which the count is directly inferable;
- this is a semantic anchor, not an intervention outcome.

Freeze A3 before running text-only replay.

---

## A4 — First explicit task-critical fact

Immediately after the first explicit answer-relevant fact/count statement.

Example:

> "There are four red objects."

This is similar to the prior Stage 10A emission anchor, now placed within a longer frozen progression.

---

# 7. Annotation blinding

Anchor reviewers may see:

- image;
- question;
- native reasoning prefix.

They may use source ground truth to determine whether A3 is textually complete.

They must not see:

- Stage 10A-R intervention outputs;
- text-only replay correctness;
- image-off outcomes;
- bootstrap effects.

Seal:

- token spans;
- anchor rationale;
- unavailable anchors;
- source fact.

before GPU intervention execution.

---

# 8. Assay 1 — Future visual-access necessity

For each available anchor \(A_i\), continue from the exact native multimodal prefix/cache while blocking all **future generated-query → image-key access** across all decoder layers.

Preserve:

- native prefix;
- prior K/V;
- prior image-derived internal state;
- all text tokens already generated.

Define:

\[
N_V(A_i)
=
Acc_{\text{FULL}}
-
Acc_{\text{image-off from }A_i}
\]

Primary early-vs-late contrast:

\[
\boxed{
N_V(A_0)-N_V(A_4)
}
\]

Secondary transition contrasts:

\[
N_V(A_1)-N_V(A_3)
\]

and:

\[
N_V(A_2)-N_V(A_3)
\]

where A2 exists.

Expected phase pattern:

\[
\boxed{
N_V(A_0),N_V(A_1)
>
N_V(A_3),N_V(A_4)
}
\]

---

# 9. Assay 2 — Fresh text-prefix sufficiency

At the same anchors, start a **fresh image-free run**.

Input contains only:

- original question/task text;
- self-generated reasoning text up to the anchor.

Do not carry over:

- image;
- original multimodal K/V;
- hidden states;
- image-derived cache.

Define:

\[
S_T(A_i)
=
P(\text{correct final answer from fresh text-only replay})
\]

Primary contrast:

\[
\boxed{
S_T(A_4)-S_T(A_0)
}
\]

Secondary:

\[
S_T(A_3)-S_T(A_1)
\]

and:

\[
S_T(A_3)-S_T(A_2)
\]

where A2 exists.

Expected phase pattern:

\[
\boxed{
S_T(A_0),S_T(A_1)
<
S_T(A_3),S_T(A_4)
}
\]

---

# 10. The central localization test

The main paper-relevant quantity is not a universal token boundary.

It is the joint semantic progression:

\[
\boxed{
N_V(A_i)\downarrow
\qquad\text{while}\qquad
S_T(A_i)\uparrow
}
\]

across the frozen evidence-resolution sequence.

The centerpiece figure should plot both curves over:

\[
A_0\rightarrow A_1\rightarrow A_2\rightarrow A_3\rightarrow A_4
\]

No monotonicity is assumed item-by-item.

The claim concerns the paired population-level functional transition.

---

# 11. Per-item transition state

As a secondary analysis, define the earliest anchor \(H\) satisfying both:

1. fresh text-only replay is correct;
2. future image-off continuation is correct.

This is an operational **text-sufficient / visual-dispensable state**.

Report:

- fraction of images with an identifiable \(H\);
- distribution of \(H\) across A0–A4;
- whether \(H\) occurs at or near A3.

Do not require all later anchors to remain correct; report nonmonotonic cases explicitly.

This is secondary and must not replace the primary paired contrasts.

---

# 12. Existing text-causality result

Do **not** rerun the full Stage 10A text-edit panel.

Stage 10A already established that counterfactual edits to the emitted count can causally redirect downstream reasoning.

Use that result as the causal-text-carrier component.

Stage 10A-R only needs to localize:

\[
\boxed{
\text{when text becomes sufficient relative to direct visual necessity}
}
\]

This prevents redundant compute.

---

# 13. Optional transition-anchor text edit

Run only if the main localization succeeds and A3 often occurs **before** A4.

Purpose:

> test whether the earlier A3 state already contains a causally usable textual carrier before the explicit count statement.

Use only:

\[
\boxed{
12 \text{ images}
}
\]

selected prospectively from items with unambiguous A3 textual evidence.

Conditions:

- original A3 prefix;
- minimal counterfactual edit of the evidence-bearing text;
- semantics-preserving sham.

All runs are image-free.

This is optional and not needed if A3 ≈ A4 on most items.

Target:

\[
<1 \text{ GPU-hour}
\]

---

# 14. Primary statistical unit

Independent unit:

\[
\boxed{
\text{image}
}
\]

Use:

- paired image-level contrasts;
- equal image weighting;
- 4,000 bootstrap draws;
- same fixed project bootstrap seed where possible;
- 95% percentile intervals.

Do not treat:

- anchors;
- queries;
- tokens;
- two assays

as independent samples.

---

# 15. Primary endpoints

Freeze four primary scalar contrasts.

## P1 — Visual necessity decrease

\[
\boxed{
N_V(A_0)-N_V(A_4)
}
\]

## P2 — Text sufficiency increase

\[
\boxed{
S_T(A_4)-S_T(A_0)
}
\]

## P3 — Evidence-resolution visual shift

\[
\boxed{
N_V(A_1)-N_V(A_3)
}
\]

## P4 — Evidence-resolution text shift

\[
\boxed{
S_T(A_3)-S_T(A_1)
}
\]

Use multiplicity-aware intervals across these four primary contrasts.

A2 analyses are secondary because A2 may not exist in every trajectory.

---

# 16. Main claim gate

Support a functional phase transition only if:

1. P1 is positive;
2. P2 is positive;
3. P3 is positive;
4. P4 is positive;
5. at least the early→late pair (P1/P2) has uncertainty inconsistent with a zero-change interpretation;
6. the direction is present in both color and shape subsets;
7. no single image or small subgroup drives the pattern;
8. Stage 10A's existing causal text-edit result remains applicable to the A4 regime.

Strongest version:

\[
\boxed{
\text{visual necessity falls before/around A3 as text sufficiency rises}
}
\]

Do not require a hard discontinuity.

---

# 17. Claim language by outcome

## Outcome A — Clear joint transition

If:

\[
N_V\downarrow
\quad\text{and}\quad
S_T\uparrow
\]

across the frozen anchors:

Supported:

> **Successful multimodal reasoning transitions from a direct visual-access-dependent regime to a text-sufficient reasoning regime as task-relevant visual evidence is resolved.**

Together with Stage 10A text causality:

> **The later reasoning trace is not merely descriptive; it is a causal carrier that can support downstream computation without renewed direct image access.**

This permits `phase-structured multimodal reasoning` as a main framing.

---

## Outcome B — Text sufficiency rises, but visual necessity does not fall

Supported:

> generated reasoning increasingly contains sufficient visual evidence, but a distinct visual-to-text phase transition is not established.

Do not use phase structure as headline.

---

## Outcome C — Visual necessity falls, but text sufficiency does not rise

Supported:

> direct visual access becomes dispensable, but explicit reasoning text is not shown to be the sufficient downstream carrier.

Use:

> image-independent reasoning regime

not text-mediated phase.

---

## Outcome D — Neither changes robustly

Close the phase-transition branch.

Retain dynamic causal retrieval and redundant evidence-carrier framing.

Do not search additional anchors.

---

# 18. Compute budget

The experiment must remain small.

Primary maximum:

\[
24 \text{ images}
\times
5 \text{ anchors}
\times
2 \text{ assays}
=
240
\]

logical continuations.

Unavailable A2 anchors reduce this count.

Controlled trajectories are short.

Target:

| Block | Max continuations | Target GPU-hours |
|---|---:|---:|
| Visual necessity | ≤120 | <1.5 h |
| Text-prefix sufficiency | ≤120 | <1.5 h |
| Analysis/bootstrap | CPU | 0 GPU |
| Optional A3 text edit | ≤36 | <1 h |

Primary GPU target:

\[
\boxed{
<3 \text{ GPU-hours}
}
\]

Hard stop before optional work:

\[
\boxed{
>5 \text{ projected GPU-hours}
}
\]

requires user approval or simplification.

Do not launch benchmark-scale free generation.

---

# 19. Execution order

## Phase L0 — Annotation only

Freeze:

- 24 primary images;
- 8 reserve;
- A0–A4 anchors;
- A2 availability;
- A3 rationale.

No GPU intervention outcomes may be opened.

## Phase L1 — Assay 1 + Assay 2

Run both primary assays on the 24-image cohort.

## Phase L2 — Primary inference

Compute P1–P4 and the joint trajectory figure.

### If Outcome A

Optional A3 text-edit subset may run.

### Otherwise

STOP.

Do not use reserve.

---

# 20. Reserve rule

Use the 8 reserve images only if:

1. all four primary point estimates have the expected direction;
2. at least one key interval remains precision-limited;
3. no technical/annotation failure exists;
4. the pattern is not clearly null.

Run the identical frozen anchor/assay protocol.

Maximum total:

\[
\boxed{
32 \text{ images}
}
\]

Do not use reserve after a directional failure.

---

# 21. Relation to prior results

This experiment should be interpreted jointly with:

## Stage 4A

New reasoning demand can retarget causal visual source:

\[
A\rightarrow B\rightarrow A
\]

## Stage 10A

Self-generated visual facts can causally influence downstream reasoning.

## Stage 9A.3–9A.5

Finite direct visual-access budgets can preserve performance in controlled CoT/Thinking tasks.

Stage 10A-R asks the missing middle:

\[
\boxed{
\textbf{Does the reasoning trajectory itself show the transition from visual dependence
to text sufficiency as evidence is resolved?}
}
\]

---

# 22. Paper-level synthesis if successful

If Stage 10A-R succeeds, the paper can use the following high-level model:

\[
\boxed{
\text{reasoning demand}
\rightarrow
\text{visual evidence acquisition}
\rightarrow
\text{text-sufficient reasoning}
}
\]

with recurrent reopening:

\[
\boxed{
V_A
\rightarrow
T_1
\rightarrow
V_B
\rightarrow
T_2
\rightarrow
V_A
}
\]

This makes reasoning-conditioned dynamic visual retrieval a mechanism **inside** the broader phase-structured framework.

A front-loaded Visual Access Boundary becomes a special case where visual demand occurs only once near the beginning.

---

# 23. Required artifacts

Produce:

1. `stage10ar_phase_localization_spec.md`
2. `stage10ar_anchor_annotations.json`
3. `stage10ar_primary_cohort.json`
4. `stage10ar_visual_necessity.parquet`
5. `stage10ar_text_sufficiency.parquet`
6. `stage10ar_primary_inference.json`
7. `stage10ar_item_transition_states.json`
8. optional `stage10ar_a3_text_edit.json`
9. optional `stage10ar_reserve_extension.json`
10. `stage10ar_resource_accounting.json`
11. `stage10ar_summary.md`

---

# 24. Key figures

## Figure 1 — Frozen semantic progression

\[
A_0
\rightarrow
A_1
\rightarrow
A_2
\rightarrow
A_3
\rightarrow
A_4
\]

with example reasoning text.

## Figure 2 — Central phase-transition plot

Overlay:

\[
N_V(A_i)
\]

and:

\[
S_T(A_i)
\]

across semantic anchors.

This is the centerpiece figure.

## Figure 3 — Per-item transition states

Show the earliest text-sufficient / visual-dispensable anchor per item.

## Figure 4 — Integration with dynamic re-access

Conceptual figure:

\[
V_A\rightarrow T_1\rightarrow V_B\rightarrow T_2\rightarrow V_A
\]

linking Stage 10A-R to Stage 4A.

---

# 25. Exactly one recommendation at completion

## If Outcome A

Recommend:

> promote phase-structured multimodal reasoning to the main paper framework and next test whether new visual demand causally reopens the perceptual-access regime in a controlled recurrent-demand task.

## Otherwise

Recommend:

> demote the phase-transition framing and finalize the paper around reasoning-conditioned dynamic visual retrieval, causal text carriage, and native-use-versus-necessity dissociation.

Do not launch the recommended next stage automatically.

---

# 26. Final decision target

This experiment exists to make one paper-level decision:

\[
\boxed{
\textbf{Can we empirically support a functional transition from visual-access-dependent
reasoning to text-sufficient reasoning within the same trajectories?}
}
\]

If yes, `phase-structured multimodal reasoning` becomes an empirical framework.

If no, stop expanding that claim.
