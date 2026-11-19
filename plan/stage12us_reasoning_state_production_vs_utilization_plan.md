# Stage 12U-S — Externalized Reasoning-State Production vs Utilization

## 0. Objective

Isolate where the Thinking-vs-Instruct advantage lives after image processing:

\[
\boxed{
\text{better externalized reasoning-state production}
\quad\text{vs}\quad
\text{better utilization / repair of the same state}
}
\]

Primary question:

\[
\boxed{
\textbf{When Thinking succeeds where Instruct+CoT fails, is the advantage mainly that
Thinking produces a better intermediate reasoning state, or that the Thinking
checkpoint is better at using / repairing a given state?}
}
\]

This stage studies **externalized textual reasoning states**, not all hidden-state computation.

---

# 1. Motivation

Current frozen evidence:

- Stage 12B-S: correct \(E^*\) rescues 12/26 complete native failures.
- Stage 12C-R: prompted CoT rescues only 1/10 B1 and 0/11 B4.
- Stage 12T-S: Thinking rescues 3/10 B1 and 5/11 B4.
- All five B4 Thinking rescues are CoT failures.

Thus the strongest unexplained cohort is:

\[
\boxed{
B4 \land C^- \land T^+
}
\]

For these items:

- Native Instruct failed;
- correct \(E^*\) supplied to Native Instruct still failed;
- prompted CoT failed;
- native Thinking succeeded.

This makes them ideal for separating **reasoning-state production** from **state utilization / repair**.

---

# 2. Conceptual decomposition

We study:

\[
\text{image processing}
\rightarrow
R
\rightarrow
\text{continuation / utilization}
\rightarrow
\text{answer},
\]

where \(R\) is an externalized reasoning prefix.

Thinking may outperform because it:

1. produces a better reasoning state \(R_T\);
2. uses the same state better;
3. repairs a flawed state better;
4. relies on non-textual internal state not captured by \(R\);
5. combines several of these.

The experiment holds the textual prefix fixed while changing the target checkpoint.

---

# 3. Primary cohort

Use the frozen five families satisfying:

\[
\boxed{
B4\land C^-\land T^+
}
\]

Call this primary cohort:

\[
\boxed{
\mathcal P_{\mathrm{B4}},\quad n=5
}
\]

B4 is especially diagnostic because:

\[
E^-O^-.
\]

Correct visual evidence \(E^*\) alone was already insufficient for Native Instruct.

---

# 4. Secondary cohort

Use the frozen B1 families satisfying:

\[
\boxed{
B1\land C^-\land T^+
}
\]

Observed size is small; treat this cohort descriptively only.

---

# 5. Source traces

For each selected item preserve:

\[
R_T=\text{successful Thinking reasoning trace}
\]

\[
R_C=\text{failed prompted-CoT reasoning trace from Instruct}.
\]

Do not regenerate source traces.

Prompted CoT is the primary Instruct-source trace because it provides standardized explicit reasoning.

---

# 6. Answer-safe reasoning prefixes

For each \(R_T\) and \(R_C\), freeze:

\[
\boxed{
R^{safe}
}
\]

as the maximal prefix ending **before the first explicit task-answer commitment or answer candidate**.

Examples:

- `Final answer:`
- `\boxed{...}`
- `Therefore the answer is ...`
- explicit option selection
- unqualified direct answer statement.

Cuts are sealed before transfer generation.

For each prefix record:

- `EXPLICIT_FINAL_PRESENT` — must be false;
- `ANSWER_CANDIDATE_PRESENT` — must be false;
- `GOLD_VALUE_INCIDENTALLY_PRESENT` — descriptive only.

---

# 7. Source-state annotation

Before transfer outcomes are opened, annotate each source prefix on two axes.

## Visual evidence state

- `E_FULL`
- `E_PARTIAL`
- `E_WRONG_OR_CONFLICTING`
- `E_NOT_EXTERNALIZED`

## Downstream derivation state

- `DERIVATION_VALID`
- `DERIVATION_FLAWED`
- `DERIVATION_UNCLEAR`

This distinction is essential.

If \(R_C\to T^+\) but \(R_C\) is already flawed, that supports **repair**, not the claim that Instruct's state was already adequate.

---

# 8. Canonicalization

Create canonical textual prefixes:

\[
\widetilde R_T,\widetilde R_C
\]

by:

1. preserving visible reasoning text exactly;
2. removing only checkpoint-specific control wrappers such as `<think>` / `</think>`;
3. preserving equations, symbols, whitespace, and order;
4. making no semantic edits;
5. adding no answer or correction.

Hash all canonical prefixes before target generation.

---

# 9. Target injection semantics

All transfer conditions are **image-free**.

Input:

\[
\text{original question}
+
\text{assistant reasoning prefix}.
\]

Do not quote the trace as a new user message.

Use assistant-prefix continuation.

## Instruct target

Render the question with the native 4B-Instruct chat template, prefill the assistant with \(\widetilde R\), and continue.

## Thinking target

Render the question with the native 4B-Thinking template, place \(\widetilde R\) inside the open reasoning channel, and continue.

No extra “continue reasoning” instruction.

---

# 10. Four core transfer conditions

For each item run the 2×2 matrix:

| Source state | Instruct target | Thinking target |
|---|---|---|
| Thinking \(R_T\) | \(R_T\rightarrow I\) | \(R_T\rightarrow T\) |
| Instruct-CoT \(R_C\) | \(R_C\rightarrow I\) | \(R_C\rightarrow T\) |

All conditions use:

- no image;
- same question;
- same canonical prefix for both targets within each row.

---

# 11. Meaning of the four conditions

## \(R_T\rightarrow T\)

Same-model text sufficiency.

If successful:

\[
\boxed{
R_T \text{ is answer-sufficient for Thinking under image-free replay}
}
\]

This is required before interpreting \(R_T\rightarrow I\).

## \(R_T\rightarrow I\)

State-production test.

If \(R_T\rightarrow T^+\) and \(R_T\rightarrow I^+\):

\[
\boxed{
\textbf{Thinking produced a portable useful reasoning state that Instruct can use.}
}
\]

For B4 this is especially strong because \(E^*\) alone had already failed under Instruct.

## \(R_C\rightarrow I\)

Same-state Instruct baseline.

This reveals whether the failed CoT state was already sufficient but lost due continuation stochasticity.

## \(R_C\rightarrow T\)

State-utilization / repair test.

If:

\[
R_C\rightarrow I^-,
\quad
R_C\rightarrow T^+,
\]

then the same externalized state produces different outcomes across target checkpoints.

Interpretation depends on source-state quality:

- correct evidence + valid derivation → **utilization**
- flawed derivation/evidence → **repair/refinement**

---

# 12. Question-only controls

For each item run:

\[
Q\rightarrow I
\]

and:

\[
Q\rightarrow T
\]

with no image and no reasoning prefix.

A transfer result is stronger when:

\[
Q\rightarrow M^-,
\quad
Q+R\rightarrow M^+.
\]

---

# 13. Shuffled-trace controls

Create a deterministic cyclic permutation within the primary cohort.

Run secondary controls such as:

\[
R_{T,j}\rightarrow I_i
\]

and:

\[
R_{C,j}\rightarrow T_i,
\quad j\neq i.
\]

Purpose:

> test whether success depends on task-relevant reasoning content rather than merely receiving a long prefix.

Do not choose pairings after outcomes are known.

---

# 14. Stochastic replication

Use:

\[
\boxed{
3 \text{ prospectively frozen seeds per family-condition}
}
\]

derived from:

`SHA256(stage12us-v1|family_id|condition|replicate)`.

Define item-level success as:

\[
\boxed{
\ge 2/3 \text{ correct continuations}
}
\]

while reporting all run-level outcomes.

No best-of-three selection.

---

# 15. Target recipes

## Instruct

- Qwen3-VL-4B-Instruct
- temperature 0.7
- top-p 0.8
- top-k 20
- repetition penalty 1.0
- presence penalty 1.5
- max new tokens 32,768

## Thinking

- Qwen3-VL-4B-Thinking
- temperature 1.0
- top-p 0.95
- top-k 20
- repetition penalty 1.0
- presence penalty 0
- max new tokens 81,920

No decoding search or retries.

---

# 16. Technical validation

Before primary science, validate assistant-prefix injection on two non-primary families.

Require:

1. image token count = 0;
2. original question preserved;
3. canonical prefix rendered exactly;
4. generation begins after final prefix token;
5. both target checkpoints accept the injected prefix;
6. no source final answer is present;
7. outputs are scoreable.

Do not inspect primary-family correctness during validation.

---

# 17. Primary endpoints

Primary cohort:

\[
\mathcal P_{\mathrm{B4}},\quad n=5.
\]

## U-P1 — Thinking-prefix same-model sufficiency

\[
\boxed{
S_{TT}=P(R_T\rightarrow T^+)
}
\]

## U-P2 — Thinking-prefix portability to Instruct

Condition on \(R_T\rightarrow T^+\):

\[
\boxed{
S_{TI}=P(R_T\rightarrow I^+)
}
\]

This is the primary **state-production** endpoint.

## U-P3 — Instruct-prefix portability to Thinking

Report:

\[
\boxed{
S_{CT}=P(R_C\rightarrow T^+)
}
\]

jointly with:

\[
S_{CI}=P(R_C\rightarrow I^+).
\]

The key discordance is:

\[
\boxed{
R_C\rightarrow I^-
\land
R_C\rightarrow T^+
}
\]

## U-P4 — Trace dependence

Primary production event:

\[
\boxed{
R_T\rightarrow I^+
\land
Q\rightarrow I^-
}
\]

Primary utilization/repair event:

\[
\boxed{
R_C\rightarrow T^+
\land
Q\rightarrow T^-
}
\]

---

# 18. State-production support

An item is `PRODUCTION_SUPPORT` if all hold:

1. original:
   \[
   C^-\land T^+;
   \]
2. replay:
   \[
   R_T\rightarrow T^+;
   \]
3. cross-target:
   \[
   R_T\rightarrow I^+;
   \]
4. control:
   \[
   Q\rightarrow I^-.
   \]

Interpretation:

\[
\boxed{
\textbf{Thinking produced a portable answer-sufficient reasoning state.}
}
\]

For B4, this state contains useful content beyond frozen \(E^*\), since \(E^*\rightarrow I\) had already failed.

---

# 19. Strong utilization support

An item is `UTILIZATION_SUPPORT` only if:

1. \(R_C\) has no material evidence error;
2. \(R_C\) is `DERIVATION_VALID`;
3. \(R_C\rightarrow I^-\);
4. \(R_C\rightarrow T^+\);
5. \(Q\rightarrow T^-\).

Interpretation:

\[
\boxed{
\textbf{Thinking uses the same already-adequate externalized state more successfully.}
}
\]

---

# 20. Repair support

An item is `REPAIR_SUPPORT` if:

1. \(R_C\) is evidence-wrong and/or `DERIVATION_FLAWED`;
2. \(R_C\rightarrow I^-\);
3. \(R_C\rightarrow T^+\);
4. \(Q\rightarrow T^-\).

Interpretation:

\[
\boxed{
\textbf{Thinking can repair/refine an imperfect externalized reasoning state.}
}
\]

Do not collapse repair into utilization.

---

# 21. Text insufficiency

An item is `TEXT_NOT_SUFFICIENT` if original Thinking was correct but:

\[
R_T\rightarrow T^-.
\]

If common, visible text alone does not reproduce the successful Thinking computation.

Possible explanations include:

- original multimodal KV/hidden state;
- omitted reasoning content;
- prefix cutoff too early;
- stochastic continuation sensitivity.

Do not choose among them without further intervention.

---

# 22. Interpretation matrix

| Pattern | Interpretation |
|---|---|
| \(R_T\to T^+\), \(R_T\to I^+\) | **State production advantage** |
| \(R_C\to I^-\), \(R_C\to T^+\), source valid | **State utilization advantage** |
| \(R_C\to I^-\), \(R_C\to T^+\), source flawed | **State repair/refinement advantage** |
| Both production and utilization/repair | Mixed advantage |
| \(R_T\to T^-\) | Visible trace not sufficient |
| Q-only succeeds | Weakens trace-specific interpretation |
| Shuffled trace succeeds similarly | Weakens content-specific interpretation |

---

# 23. Prospective decision states

Because \(n=5\), this is a targeted mechanism-localization study, not prevalence estimation.

## `STATE_PRODUCTION_SIGNAL`

Declare if:

- \(R_T\rightarrow T\) succeeds on at least 4/5 B4 items;
- `PRODUCTION_SUPPORT` occurs on at least 3/5.

## `STATE_UTILIZATION_SIGNAL`

Declare if at least 3/5 B4 items satisfy `UTILIZATION_SUPPORT`.

## `STATE_REPAIR_SIGNAL`

Declare if at least 3/5 satisfy `REPAIR_SUPPORT`.

## `MIXED_STATE_SIGNAL`

Declare if production and utilization/repair both appear meaningfully without one dominating.

## `TEXT_STATE_INSUFFICIENT`

Declare if \(R_T\rightarrow T\) succeeds on fewer than 3/5 B4 items.

---

# 24. Why B4 is especially diagnostic

For every primary item:

\[
E^*\rightarrow I^-
\]

was already observed.

Therefore if:

\[
R_T\rightarrow I^+,
\]

then:

\[
\boxed{
E^* \text{ alone is insufficient for Instruct, but the richer Thinking-generated reasoning state is sufficient.}
}
\]

This localizes the useful content between raw task-critical visual facts and a richer derived intermediate state.

Candidate content includes:

- binding;
- transformed visual relations;
- subproblem decomposition;
- derived quantities;
- intermediate geometric/algebraic deductions;
- consistency constraints.

Do not assume which component matters without content ablation.

---

# 25. Secondary B1 interpretation

B1 has a stronger upstream visual-evidence component:

\[
E^-O^+.
\]

If a Thinking prefix has `E_FULL` and:

\[
R_T\rightarrow I^+,
\]

that supports a better evidence-bearing state production interpretation.

If an Instruct-CoT prefix already has correct \(E^*\) and:

\[
R_C\rightarrow I^-,
\quad
R_C\rightarrow T^+,
\]

that supports downstream utilization/repair.

B1 remains descriptive due small \(n\).

---

# 26. Null discipline

Failure of:

\[
R_T\rightarrow I
\]

does not prove the advantage is purely checkpoint-side utilization.

Possible alternatives:

- visible prefix omits useful hidden/KV state;
- cross-checkpoint representation mismatch;
- cutoff too early;
- stochastic continuation.

That is why:

\[
R_T\rightarrow T
\]

is a mandatory same-model sufficiency gate.

Likewise \(R_C\rightarrow T^+\) does not prove \(R_C\) was already a good state unless source-state annotation shows correct evidence and valid derivation.

---

# 27. Connection to the paper

## If state production dominates

Potential claim:

> Thinking's advantage is not simply longer reasoning or better final decoding; it generates more useful intermediate reasoning states that even the Instruct checkpoint can exploit once provided.

This connects to the existing text-carrier result:

\[
\text{visual evidence}
\rightarrow
\text{generated reasoning text}
\rightarrow
\text{downstream computation}.
\]

## If utilization/repair dominates

Potential claim:

> Thinking remains better even when the externalized reasoning state is held fixed, implicating downstream state utilization/refinement rather than state production alone.

---

# 28. Statistics

Primary independent unit:

\[
\boxed{
\text{family}
}
\]

Report:

- all 3-seed run-level outcomes;
- item-level majority success;
- exact counts over the five primary B4 families.

Use exact binomial intervals only as descriptive uncertainty.

Do not make asymptotic significance claims from \(n=5\).

---

# 29. Required figures

## Figure U1 — Production vs utilization assay

```text
Thinking trace R_T ──→ Thinking
                  └──→ Instruct

Instruct trace R_C ──→ Instruct
                  └──→ Thinking

(all image-free)
```

## Figure U2 — Per-family transfer matrix

Columns:

- \(R_T\to T\)
- \(R_T\to I\)
- \(R_C\to I\)
- \(R_C\to T\)
- Q→I
- Q→T

## Figure U3 — Interpretation class

Per family:

- production support;
- utilization support;
- repair support;
- text insufficient;
- unresolved.

## Figure U4 — Source-state content

Show:

- evidence state;
- derivation state;
- answer-leak audit.

---

# 30. Required artifacts

Produce:

1. `stage12us_reasoning_state_transfer_spec.md`
2. `stage12us_primary_b4_manifest.json`
3. `stage12us_secondary_b1_manifest.json`
4. `stage12us_source_prefixes.json`
5. `stage12us_prefix_content_audit.json`
6. `stage12us_canonical_trace_hashes.json`
7. `stage12us_technical_validation.json`
8. `stage12us_transfer_results.parquet`
9. `stage12us_question_only_controls.parquet`
10. `stage12us_shuffled_trace_controls.parquet`
11. `stage12us_scoring_review.json`
12. `stage12us_item_interpretations.parquet`
13. `stage12us_primary_inference.json`
14. `stage12us_decision.json`
15. `stage12us_resource_accounting.json`
16. `stage12us_summary.md`

Preserve all Stage 12B-S, 12C-R, 12T-R, and 12T-S artifacts unchanged.

---

# 31. Compute budget

Primary B4 core + question-only panel:

- 5 families;
- 6 conditions;
- 3 seeds;

\[
\boxed{
90 \text{ logical calls}
}
\]

Secondary B1 panel:

\[
\boxed{
36 \text{ additional calls}
}
\]

if executed.

Shuffled controls may add up to 30 calls.

Target:

\[
\boxed{
<5 \text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
7 \text{ GPU-hours}
}
\]

unless separately approved.

Do not run hidden-state interventions in this stage.

---

# 32. Exactly one recommendation at completion

## If `STATE_PRODUCTION_SIGNAL`

Recommend:

> Localize which Thinking-derived intermediate deductions make the state portable to Instruct using prefix-position and content ablations.

## If `STATE_UTILIZATION_SIGNAL`

Recommend:

> Hold the transferred reasoning state fixed and causally compare downstream computation between Instruct and Thinking.

## If `STATE_REPAIR_SIGNAL`

Recommend:

> Identify which flawed Instruct reasoning components Thinking corrects using counterfactual repair/edit interventions.

## If `MIXED_STATE_SIGNAL`

Recommend:

> Decompose production and utilization separately with prefix-localization and fixed-state downstream interventions.

## If `TEXT_STATE_INSUFFICIENT`

Recommend:

> Test whether non-textual cached/hidden state is required before making further production-vs-utilization claims.

Do not launch automatically.

---

# 33. Final decision target

Stage 12U-S exists to answer:

\[
\boxed{
\textbf{When Thinking succeeds where Instruct+CoT fails, is the main advantage that
Thinking produces a better portable reasoning state, or that it is better at
using / repairing the same state?}
}
\]

The critical isolation is:

\[
\boxed{
R_T\rightarrow T,\;
R_T\rightarrow I,\;
R_C\rightarrow I,\;
R_C\rightarrow T
}
\]

with:

- no image;
- the same question;
- frozen answer-safe prefixes;
- question-only and shuffled-trace controls.

This is the cleanest next behavioral step for separating:

\[
\boxed{
\text{image/evidence acquisition}
\rightarrow
\text{reasoning-state production}
\rightarrow
\text{state utilization / repair}
}
\]
