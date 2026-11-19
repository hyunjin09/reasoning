# Stage 10A — Causal Perceptual-to-Textual Handoff

## 0. One-line objective

Test whether visual evidence acquired during reasoning is **causally handed off into the model's generated reasoning text**, such that direct image access becomes less necessary while the textualized evidence becomes sufficient and causally controls later reasoning.

Primary question:

\[
\boxed{
\textbf{Does control over downstream reasoning shift from the image to self-generated text after visual evidence is externalized?}
}
\]

This is the key experiment needed to turn the current **phase-structured reasoning** hypothesis into a causal result.

The experiment is deliberately bounded so that **each analysis block should complete within a few GPU-hours**.

---

# 1. Why this experiment is necessary

Current results already show:

1. visual evidence can causally control upcoming reasoning;
2. direct image access can later become dispensable;
3. reasoning can reopen visual access when new visual demand appears;
4. retrieved visual evidence is carried only locally in recent K/V and residual state.

What is still missing is the causal middle step:

\[
\boxed{
\text{visual evidence}
\rightarrow
\text{text-/reasoning-mediated state}
}
\]

A drop in direct visual necessity does **not** by itself prove that the information has been transferred into textual/symbolic form.

The strongest paper-level claim we want to test is:

> **Multimodal reasoning contains a causal perceptual-to-textual handoff: once visual evidence is externalized into the reasoning trace, downstream computation can rely on that textualized evidence instead of continued direct image access.**

---

# 2. Claim a positive result would support

A positive result requires all three components:

## H1 — Visual necessity decreases after evidence emission

\[
N_V(t_{\text{post}})
<
N_V(t_{\text{pre}})
\]

## H2 — Text-prefix sufficiency increases after evidence emission

\[
S_T(t_{\text{post}})
>
S_T(t_{\text{pre}})
\]

## H3 — The textualized fact causally controls downstream reasoning

If the model originally writes:

> "There are four red objects."

then changing only that textual fact to:

> "There are five red objects."

should redirect downstream reasoning toward five after the handoff.

The strongest supported claim would be:

\[
\boxed{
\textbf{causal control shifts from perceptual input to generated reasoning text}
}
\]

---

# 3. What a null would NOT rule out

A null does not imply:

- visual evidence is never transferred internally;
- later reasoning does not use hidden-state visual information;
- phase structure is false in all tasks;
- textual reasoning is irrelevant.

It may instead indicate:

- the transfer is primarily latent/hidden rather than explicit-text mediated;
- the selected evidence statement is not the main carrier;
- the task is too simple or too ambiguous;
- the handoff occurs at a different semantic point.

Do not respond to a null by widening windows or selecting new facts post hoc.

---

# 4. Model and task

## Primary model

\[
\boxed{
\textbf{Qwen3-VL-4B-Thinking}
}
\]

Use the already validated native Thinking execution path.

## Primary controlled task

Reuse the **same 32-image / 64-query controlled color-and-shape counting set** from Stage 9A.5.

Reasons:

- cheap generation;
- clear ground-truth visual facts;
- explicit self-generated evidence statements;
- already validated FULL baseline;
- easy counterfactual text editing;
- direct comparison to the finite-access result.

No new image generation is required.

---

# 5. Event selection

For each FULL Thinking trajectory, identify the **first explicit visual evidence statement** that contains the task-critical fact.

Examples:

- "There are four red objects."
- "I count three circles."
- "The number of blue shapes is two."

Define three semantic anchors:

## \(t_{\text{pre}}\)

The last reasoning position **before** the task-critical visual fact is explicitly stated.

## \(t_{\text{emit}}\)

Immediately after the model first states the task-critical visual fact.

## \(t_{\text{post}}\)

A later point after the fact has been used in at least one downstream reasoning step, but before final-answer emission.

Freeze anchor selection using only:

- trajectory text;
- image/question;
- semantic fact identity.

Do not use intervention outcomes or final correctness to choose anchors.

---

# 6. Cohort size

Use a bounded independent-image cohort.

## Primary cohort

\[
\boxed{
24 \text{ images}
}
\]

with at most one eligible query per image.

Prefer a balanced mix of:

- color-count
- shape-count

and only trajectories where:

- FULL reasoning explicitly states the task-critical fact;
- anchor points are unambiguous;
- final answer is valid under FULL.

## Reserve

Freeze:

\[
\boxed{
8 \text{ additional images}
}
\]

for precision extension only.

Do not exceed 32 images without new authorization.

This should keep all analysis blocks within a few GPU-hours.

---

# 7. Stage 10A.1 — Text-prefix sufficiency

## Question

Once the visual fact has been stated, is the **reasoning text alone** sufficient to continue correctly without the image?

For each selected item and each anchor:

\[
t\in
\{t_{\text{pre}},t_{\text{emit}},t_{\text{post}}\}
\]

construct a **fresh continuation** with:

- original question text;
- self-generated reasoning text up to \(t\);
- **no image**;
- no original KV cache;
- no hidden state copied from the multimodal run.

This cleanly removes latent visual state from the original execution.

Define:

\[
S_T(t)
=
P(\text{correct final answer from text-only replay at }t)
\]

Primary contrast:

\[
\boxed{
S_T(t_{\text{post}})
-
S_T(t_{\text{pre}})
}
\]

Secondary:

\[
S_T(t_{\text{emit}})
-
S_T(t_{\text{pre}})
\]

### Positive pattern

\[
\boxed{
\text{pre: low text sufficiency}
\rightarrow
\text{post: high text sufficiency}
}
\]

### Compute target

At most:

\[
24 \times 3 = 72
\]

short fresh continuations.

Target:

\[
\boxed{
<1.5 \text{ GPU-hours}
}
\]

---

# 8. Stage 10A.2 — Visual necessity around the same handoff

## Question

Does direct image access become less necessary after the visual fact is externalized?

At the same anchors, use the original multimodal prefix and then remove **future direct generated-query → image-key access** from that anchor onward.

Use model-wide image-key masking, preserving:

- prior prefix;
- existing cache;
- prior image-derived hidden state.

Define:

\[
N_V(t)
=
Acc_{\text{FULL}}
-
Acc_{\text{image-off after }t}
\]

Primary contrast:

\[
\boxed{
N_V(t_{\text{pre}})
-
N_V(t_{\text{post}})
}
\]

### Positive pattern

\[
\boxed{
\text{pre: image removal hurts}
\rightarrow
\text{post: image removal hurts much less}
}
\]

### Compute target

At most:

\[
24 \times 3 = 72
\]

short continuations.

Target:

\[
\boxed{
<1.5 \text{ GPU-hours}
}
\]

---

# 9. Stage 10A.3 — Causal text-edit test

This is the decisive textual-mediation assay.

## Question

After the model has emitted the correct visual fact, does that **self-generated textual fact** causally control downstream reasoning?

For each item at \(t_{\text{emit}}\) or \(t_{\text{post}}\), create:

### C0 — Original text

Keep the original self-generated fact.

### C1 — Counterfactual text

Change only the fact value to another valid value.

Example:

> "There are four red objects."

→

> "There are five red objects."

### C2 — Text deletion

Delete the minimal evidence-bearing clause.

### C3 — Sham edit

Make a semantics-preserving edit of similar textual size.

All conditions run:

\[
\boxed{
\text{without the image}
}
\]

to isolate text-mediated control.

Primary endpoint:

\[
\boxed{
\text{Does downstream answer/evidence follow the counterfactual text value?}
}
\]

Secondary:

- deletion damage;
- sham effect;
- downstream log-prob shift.

### Strong positive criterion

Counterfactual text edits should:

1. produce a directional semantic shift;
2. exceed sham effects;
3. affect downstream reasoning more than deletion-independent perturbation noise.

### Compute target

For 24 items:

\[
24 \times 4 = 96
\]

short continuations.

Target:

\[
\boxed{
<2 \text{ GPU-hours}
}
\]

---

# 10. Stage 10A.4 — Image × Text causal dominance

Run only if Stage 10A.3 shows a clear text-edit effect.

For each item, compare four conditions after evidence emission:

| Condition | Image content | Reasoning text |
|---|---|---|
| I0T0 | original | original |
| I1T0 | counterfactual image/source | original text |
| I0T1 | original image | counterfactual text |
| I1T1 | counterfactual image | counterfactual text |

Primary question:

\[
\boxed{
\textbf{After handoff, does downstream reasoning follow text more strongly than image?}
}
\]

Define directional effects:

\[
E_{\text{image}}
\]

and

\[
E_{\text{text}}
\]

on the same downstream semantic target.

Strong handoff signature:

\[
\boxed{
E_{\text{text}} > E_{\text{image}}
}
\]

after evidence emission.

If feasible, repeat a smaller version at \(t_{\text{pre}}\).

Ideal causal reversal:

\[
\boxed{
t_{\text{pre}}:
E_{\text{image}}>E_{\text{text}}
}
\]

\[
\boxed{
t_{\text{post}}:
E_{\text{text}}>E_{\text{image}}
}
\]

This would directly support:

\[
\boxed{
\textbf{perceptual control}
\rightarrow
\textbf{textual control}
}
\]

### Compute target

Use only:

\[
\boxed{
12 \text{ highest-confidence primary items}
}
\]

selected before opening 2×2 outcomes.

At most:

\[
12\times4\times2
=
96
\]

local continuations for pre/post.

Target:

\[
\boxed{
<2 \text{ GPU-hours}
}
\]

---

# 11. Primary statistical unit

Independent unit:

\[
\boxed{
\text{image}
}
\]

Use:

- paired image-level comparisons;
- 4,000 image-cluster bootstrap draws;
- equal image weighting;
- exact binomial / paired sign summaries where helpful.

Do not treat:

- two queries from one image;
- multiple anchors;
- multiple intervention conditions

as independent samples.

---

# 12. Primary claim gate

Support a **causal perceptual-to-textual handoff** only if:

1. text-only replay improves substantially from pre to post;
2. image-removal damage decreases substantially from pre to post;
3. counterfactual text edits directionally redirect downstream reasoning;
4. text-edit effects exceed sham;
5. deletion is harmful or at least clearly different from sham;
6. the effect is not driven by one visual attribute type;
7. the 2×2 subset, if triggered, is consistent with increased post-handoff text dominance.

Do not call the process "symbolic handoff" if only conditions 1–2 pass.

Use:

> **perceptual-to-reasoning-state handoff**

unless text causality is directly established.

---

# 13. Phase definition

Do **not** require a discontinuous sharp boundary.

Define phases functionally.

## Perceptual-access regime

A reasoning interval where:

- direct visual access remains causally important;
- text-only continuation is insufficient.

## Handoff regime

A transition region where:

\[
N_V(t)\downarrow
\]

and:

\[
S_T(t)\uparrow
\]

while explicit evidence appears in the reasoning trace.

## Text-mediated reasoning regime

A region where:

- direct image access is largely dispensable for the current subgoal;
- text-only continuation is sufficient;
- textual evidence causally controls downstream reasoning.

This definition remains valid even if transitions are gradual.

---

# 14. Optional reserve extension

Use the 8 reserve images only if:

1. all primary point estimates support handoff;
2. uncertainty remains wide;
3. no technical failure appears;
4. no condition definition changes.

Run the same frozen conditions.

Maximum cohort:

\[
\boxed{
32 \text{ images}
}
\]

Do not use reserve to rescue a null result.

---

# 15. Natural-task bridge — optional only after controlled success

If the controlled 24-image study establishes the full handoff pattern, run a **small MathVision bridge**.

Use:

\[
\boxed{
12\text{–}16 \text{ previously reviewed Qwen3-VL-4B Thinking events}
}
\]

where:

- a visual fact is explicitly stated;
- a downstream reasoning step uses it;
- source identity is clear.

Run only:

1. text-only replay pre/post;
2. original vs counterfactual text edit.

Do not repeat the full 2×2 on MathVision initially.

Target:

\[
\boxed{
<2 \text{ GPU-hours}
}
\]

This provides natural-task validation without expanding the project.

---

# 16. Thinking vs CoT comparison is not part of the primary Stage 10A gate

First establish the handoff mechanism cleanly in Thinking.

Only after Stage 10A succeeds should a matched CoT comparison ask:

- does CoT externalize visual facts less accurately?
- does text-only sufficiency emerge later?
- is text-mediated causal control weaker?
- does an oracle visual-fact handoff close the accuracy gap?

That should be Stage 10B.

Do not mix that comparison into the initial handoff discovery.

---

# 17. Compute budget

The experiment must remain bounded.

Expected upper bounds:

| Block | Max continuations | Target GPU-hours |
|---|---:|---:|
| 10A.1 Text-only replay | 72 | <1.5 h |
| 10A.2 Visual necessity | 72 | <1.5 h |
| 10A.3 Text edit/delete/sham | 96 | <2 h |
| 10A.4 2×2 causal dominance | 96 | <2 h |
| Optional reserve | bounded | <1.5 h |
| Optional MathVision bridge | 12–16 events | <2 h |

Primary controlled study target:

\[
\boxed{
<7 \text{ GPU-hours total}
}
\]

Hard stop:

\[
\boxed{
>10 \text{ projected GPU-hours before optional bridge}
}
\]

requires simplification or user approval.

Do not launch long free-running benchmark generation.

---

# 18. Execution order

Run sequentially.

## Gate A

10A.1 + 10A.2

If neither shows the expected crossing:

\[
\boxed{
\text{STOP}
}
\]

Do not run text-edit claims.

## Gate B

10A.3

If counterfactual text does not directionally control downstream reasoning:

\[
\boxed{
\text{STOP the textual-mediation claim}
}
\]

Do not run 2×2.

## Gate C

10A.4

Run only after clear text causality.

This staged execution minimizes compute and prevents overinterpreting weak signals.

---

# 19. Outcome matrix

## Outcome A — Full causal handoff

Observed:

\[
N_V(t)\downarrow
\]

\[
S_T(t)\uparrow
\]

and:

\[
\text{text edit}\rightarrow\text{downstream semantic shift}
\]

with 2×2 support.

Supported claim:

\[
\boxed{
\textbf{Multimodal reasoning contains a causal perceptual-to-textual handoff.}
}
\]

This upgrades the phase-structured reasoning story into a main empirical contribution.

## Outcome B — Visual necessity falls and text-only sufficiency rises, but text edits do not control reasoning

Interpretation:

> evidence is handed into an image-independent reasoning state, but explicit text mediation is not established.

Use:

\[
\boxed{
\textbf{perceptual-to-reasoning-state handoff}
}
\]

not "symbolic/textual handoff."

## Outcome C — Text edits control downstream reasoning, but visual necessity does not fall

Interpretation:

> textual evidence is a causal carrier, but perceptual handoff/phase termination is not established.

Do not claim distinct phases.

## Outcome D — No stable pre/post transition

Stop the phase-structured claim.

Retain the stronger existing results:

- reasoning-conditioned retrieval;
- dynamic source retargeting;
- alignment ≠ retrieval;
- native use ≠ ablation necessity.

---

# 20. Required artifacts

Produce:

1. `stage10a_handoff_spec.md`
2. `stage10a_event_selection.json`
3. `stage10a_text_prefix_sufficiency.parquet`
4. `stage10a_visual_necessity.parquet`
5. `stage10a_text_edit_results.parquet`
6. optional `stage10a_image_text_2x2.parquet`
7. `stage10a_primary_inference.json`
8. optional `stage10a_reserve_extension.json`
9. optional `stage10a_mathvision_bridge.json`
10. `stage10a_resource_accounting.json`
11. `stage10a_summary.md`

---

# 21. Key figures

## Figure 1 — Handoff schematic

\[
\text{Image}
\rightarrow
\text{visual evidence}
\rightarrow
\text{reasoning text}
\rightarrow
\text{downstream computation}
\]

## Figure 2 — Visual necessity vs text sufficiency

Plot:

\[
N_V(t)
\]

and:

\[
S_T(t)
\]

at pre / emit / post anchors.

The desired crossing is the centerpiece.

## Figure 3 — Counterfactual text control

Show:

\[
4\rightarrow5
\]

in self-generated text and corresponding downstream semantic shift.

## Figure 4 — Image × Text causal dominance

Show pre/post:

\[
E_{\text{image}}
\]

vs:

\[
E_{\text{text}}
\]

The strongest possible result is a causal dominance reversal.

---

# 22. Final paper dependency

If Stage 10A succeeds, the paper can promote:

\[
\boxed{
\textbf{Phase-Structured Multimodal Reasoning}
}
\]

from a hypothesis to an empirical result.

The resulting causal lifecycle becomes:

\[
\boxed{
\text{visual demand}
\rightarrow
\text{perceptual acquisition}
\rightarrow
\text{text-mediated handoff}
\rightarrow
\text{image-independent reasoning}
\rightarrow
\text{new visual demand}
\rightarrow
\text{re-access}
}
\]

If Stage 10A fails, do not force this framing.

Retain the narrower but already strong thesis:

\[
\boxed{
\textbf{Visual evidence acquisition is dynamically and causally retargeted by reasoning demand.}
}
\]
