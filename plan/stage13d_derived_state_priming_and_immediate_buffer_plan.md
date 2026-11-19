# Stage 13D — Post-Evidence Mechanism without Free-Reasoning Reopening
## Derived-State Priming + Immediate-Answer Computational-Buffer Assay

## 0. Objective

Follow up the Stage 13C technical stop with two mechanism tests that remain identifiable under the current Qwen3-VL-4B runtime:

1. **Derived-state priming** — test whether task-specific intermediate deductions produced by Thinking are themselves useful to Instruct after \(E^*\) is already supplied.
2. **Immediate-answer computational buffer** — test whether forcing a longer semantically empty reasoning trajectory shifts the model's *immediate answer distribution* toward the correct answer, without allowing any post-close free reasoning.

Primary question:

\[
\boxed{
\textbf{Why does Thinking retain an advantage after the correct visual evidence is already available?}
}
\]

Stage 13A already established:

\[
\boxed{
Acc(T_{E^*})-Acc(I_{E^*})=+11.11\text{ pp}
}
\]

under identical image-free \(Q+E^*\).

Stage 13D asks whether that post-evidence advantage is supported by:

\[
\boxed{
\text{content-dependent semantic state construction}
}
\]

and/or:

\[
\boxed{
\text{content-independent extra computation}.
}
\]

This stage does **not** require the model to obey a final `</think>` boundary during free generation.

---

## 1. Why Stage 13D is different from blocked Stage 13C

Stage 13C failed because the Thinking checkpoint repeatedly resumed free reasoning after the forced close marker.

Therefore the intended short-vs-long dummy comparison no longer isolated different amounts of reasoning computation.

Stage 13D removes that confound in two ways.

### Semantic arm

No forced Thinking trace is needed.

Extracted Thinking-derived semantic content is transplanted into Instruct as:

\[
Q+E^*+D_T.
\]

### Compute arm

After a forced dummy reasoning trace and forced close, the model is **not allowed to generate free tokens**.

Instead, the experiment immediately scores candidate answers.

Thus reasoning reopening cannot contaminate the compute contrast.

---

## 2. Paper-level hypotheses

### H1 — Derived-state priming

\[
\boxed{
\textbf{Thinking-generated task-specific intermediate deductions are themselves sufficient to improve downstream solving.}
}
\]

Positive interpretation:

> **Thinking transforms already-available evidence into semantically useful intermediate state.**

### H2 — Computational buffer

\[
\boxed{
\textbf{Additional semantically empty reasoning-token computation improves the model's immediate answer state.}
}
\]

Positive interpretation:

> **Part of the post-evidence Thinking benefit is content-independent computation performed across additional autoregressive reasoning steps.**

### Complementary interpretation

If both H1 and H2 are supported:

> **Thinking's post-evidence advantage is supported by complementary semantic state construction and content-independent additional computation.**

Do not claim that these mechanisms exhaust all residual Thinking gains.

---

## 3. Frozen model setting

Use only the validated 4B checkpoints:

- Qwen3-VL-4B-Instruct
- Qwen3-VL-4B-Thinking

Use the exact Stage 13A pinned revisions and intended recipes.

No image is used in any Stage 13D scientific condition.

Every family starts from the exact frozen:

\[
\boxed{
Q+E^*
}
\]

used in Stage 13A.

---

## 4. Cohort

Reuse the exact source-only 24-family scientific cohort already sealed for Stage 13C.

Reasons:

- it was selected without Stage 13A outcome information;
- Stage 13C ran no scientific mechanism calls;
- reusing it preserves prospectivity;
- no new source selection is needed.

Also reuse the disjoint Stage 13C technical4 set for validation.

Do not add/remove families after inspecting derived-state content.

---

## 5. Source Thinking trajectories

For every scientific family, reuse the exact Stage 13C source-trace rule:

> the first technically resolved Stage 13A Thinking equal-evidence replicate in ascending frozen replicate order.

Do not select by final correctness.

Call the source reasoning trace:

\[
R_i.
\]

Record:

- source trace hash;
- source final correctness;
- reasoning token count;
- source replicate ID.

---

## 6. Derived-state extraction

From each \(R_i\), extract an ordered compact list:

\[
\boxed{
D_i=\{d_{i1},\ldots,d_{im}\}
}
\]

containing only **new task-specific intermediate propositions introduced during Thinking**.

Eligible content includes:

- new entity bindings;
- transformed representations;
- derived geometric/algebraic relations;
- intermediate quantities;
- subgoal conclusions;
- consistency constraints;
- corrections that establish new task-relevant propositions.

Remove:

- question restatements;
- direct \(E^*\) restatements;
- meta reasoning;
- generic planning;
- stylistic filler;
- candidate-answer guessing;
- explicit final-answer commitments;
- answer-equivalent final conclusions.

The intended object is:

\[
\boxed{
\textbf{semantic reasoning content beyond already-supplied }E^*.
}
\]

---

## 7. Extraction contract and audit

Finalize the Stage 13C draft extractions before any Stage 13D scientific output is generated.

For every \(D_i\) record:

- `SAFE_NONEMPTY`
- `EXPLICIT_FINAL_PRESENT`
- `ANSWER_COMMITMENT_PRESENT`
- `GOLD_EQUIVALENT_PRESENT`
- `QUESTION_RESTATEMENT_PRESENT`
- `E_STAR_RESTATEMENT_PRESENT`
- `ALL_VERIFIED_CORRECT`
- `HAS_VERIFIED_ERROR`
- `MIXED_OR_UNCLEAR`

Primary semantic interventions require:

\[
\boxed{
\texttt{SAFE\_NONEMPTY}=1.
}
\]

If no safe derived state can be extracted:

\[
\texttt{NO\_SAFE\_DERIVED\_CONTENT}.
\]

Such families are excluded from the semantic-effect denominator.

No extraction may be revised after intervention outcomes are opened.

---

## 8. Phase A — Derived-state priming in Instruct

This is the **primary Stage 13D experiment**.

Run on every family with safe nonempty \(D_i\).

All conditions use the exact same image-free:

\[
Q+E^*.
\]

Use:

\[
\boxed{
5\text{ fresh frozen seeds per condition}.
}
\]

### A0 — Baseline

\[
\boxed{
I_{\mathrm{BASE}}
=
I(Q+E^*)
}
\]

Use fresh Stage 13D seeds.

### A1 — Thinking-derived semantic state

\[
\boxed{
I_{\mathrm{DERIVED}}
=
I(Q+E^*+D_i)
}
\]

Use a fixed neutral wrapper:

> `Intermediate deductions available so far:`

followed by the frozen \(D_i\), then:

> `Solve the original problem using the information above.`

Use exactly the same wrapper for all semantic-context controls.

### A2 — Length-matched dummy context

\[
\boxed{
I_{\mathrm{DUMMY}}
=
I(Q+E^*+\widetilde D_i)
}
\]

where \(\widetilde D_i\) is task-independent dummy text matched to the Instruct-token length of \(D_i\).

Use the fixed dummy sentence repeated/truncated:

> `This is additional intermediate context.`

No task-specific mathematical content.

### A3 — Shuffled derived state

\[
\boxed{
I_{\mathrm{SHUFFLED}}
}
\]

Replace \(D_i\) with \(D_j\) from another family.

Freeze donor selection before generation:

1. \(j\neq i\);
2. minimize absolute Instruct-token-length difference;
3. break ties with:
   `SHA256(stage13d-v1|target_id|donor_id)`.

This controls for generic mathematical-looking semantic content.

---

## 9. Primary derived-state endpoints

Define family-level five-seed accuracies.

### Baseline gain

\[
\Delta_{\mathrm{base}}
=
Acc(I_{\mathrm{DERIVED}})
-
Acc(I_{\mathrm{BASE}})
\]

### Dummy-controlled semantic gain

\[
\boxed{
\Delta_{\mathrm{dummy}}
=
Acc(I_{\mathrm{DERIVED}})
-
Acc(I_{\mathrm{DUMMY}})
}
\]

### Task-specificity gain

\[
\boxed{
\Delta_{\mathrm{shuffle}}
=
Acc(I_{\mathrm{DERIVED}})
-
Acc(I_{\mathrm{SHUFFLED}})
}
\]

The primary semantic estimand is:

\[
\boxed{
\Delta_{\mathrm{dummy}}.
}
\]

---

## 10. Derived-state priming decision

Declare:

\[
\boxed{
\texttt{DERIVED\_STATE\_PRIMING\_CONFIRMED}
}
\]

iff:

1. at least 12 families have safe nonempty \(D_i\) and fully resolved A0–A3 outcomes;
2. mean:
   \[
   \Delta_{\mathrm{dummy}}\ge+5\text{ pp};
   \]
3. 95% paired family-bootstrap lower bound for \(\Delta_{\mathrm{dummy}}\) is \(>0\);
4. \(\Delta_{\mathrm{base}}>0\);
5. \(\Delta_{\mathrm{shuffle}}>0\).

Interpretation:

> **Thinking-generated derived semantic content itself improves equal-evidence Instruct solving.**

This is the closest VLM-math analogue of factual priming.

---

## 11. Strong selected-case rescue readout

After the primary semantic analysis is sealed, report the subset of Stage 13A families that were majority:

\[
I_{E^*}^-,
\quad
T_{E^*}^+.
\]

Among overlapping Stage 13D families, report whether:

\[
I_{\mathrm{DERIVED}}^+
\]

while:

\[
I_{\mathrm{BASE}}^-,
\quad
I_{\mathrm{DUMMY}}^-,
\quad
I_{\mathrm{SHUFFLED}}^-.
\]

Call such a family:

\[
\boxed{
\texttt{TRACE\_SPECIFIC\_DERIVED\_RESCUE}.
}
\]

This is secondary.

---

## 12. Secondary failure prediction: correct vs flawed derived state

Use the pre-frozen correctness labels.

Compare descriptively:

\[
Acc(I_{\mathrm{DERIVED}})
\]

for:

- `ALL_VERIFIED_CORRECT`
- `HAS_VERIFIED_ERROR`
- `MIXED_OR_UNCLEAR`

Also report:

\[
I_{\mathrm{DERIVED}}-I_{\mathrm{DUMMY}}
\]

within each group.

A pattern where verified-correct derived states help more than flawed ones is consistent with semantic-state priming.

Do not call this causal hallucination propagation without a separate intervention.

---

## 13. Phase B — Immediate-answer computational-buffer assay

This is a **secondary mechanism assay**.

It avoids the Stage 13C reopening problem by never allowing free generation after the forced reasoning trace.

Primary Phase B uses only multiple-choice families.

Open-ended families are excluded from the primary buffer test because candidate-sequence scoring adds extra equivalence/length assumptions.

---

## 14. MC subset

From the frozen 24-family cohort, define before scientific scoring:

\[
\boxed{
\mathcal M
=
\{\text{families with fixed multiple-choice options}\}.
}
\]

Require at least:

\[
\boxed{
8\text{ MC families}
}
\]

for a cohort-level buffer decision.

If fewer than 8:

\[
\texttt{BUFFER\_COHORT\_TOO\_SMALL}.
\]

Report Phase B descriptively only.

---

## 15. Forced dummy traces

Use the Thinking checkpoint and base input:

\[
Q+E^*.
\]

Open the native reasoning channel.

Use the task-independent phrase:

> `Let me think.`

### B1 — Short dummy

Force exactly:

\[
\boxed{
16\text{ reasoning tokens}
}
\]

then force the native reasoning close token.

### B2 — Long dummy

Let \(L_i\) be the source Thinking reasoning-token count.

Force exactly:

\[
\boxed{
L_i\text{ dummy reasoning tokens}
}
\]

then force the native reasoning close token.

Use one-token-at-a-time KV continuation.

Save exact forced-token receipts.

---

## 16. No free generation after close

This is the critical Stage 13D contract.

After the forced close:

\[
\boxed{
\textbf{do not sample or generate any free model tokens.}
}
\]

Immediately score the answer options.

Any implementation that generates free text after close invalidates the buffer assay.

---

## 17. Immediate answer scoring

For every MC family, use the frozen answer options exactly as presented.

After the forced close, append the same fixed answer introducer:

> `Final answer:`

Then teacher-force each candidate answer.

For option \(a\), compute normalized log-likelihood:

\[
\ell(a)
=
\frac{1}{|a|}
\sum_{t=1}^{|a|}
\log p(a_t\mid Q,E^*,\text{forced trace},\text{answer prefix},a_{<t}).
\]

Primary candidate representation:

- canonical option letter if available;
- otherwise exact option text.

Freeze representation before scientific scoring.

---

## 18. Buffer readouts

Let \(a_i^*\) be the gold option.

### Gold normalized log-likelihood

\[
L_i^{gold}
=
\ell(a_i^*)
\]

### Gold margin over strongest distractor

\[
\boxed{
M_i
=
\ell(a_i^*)
-
\max_{a\neq a_i^*}\ell(a)
}
\]

Primary buffer effect:

\[
\boxed{
\Delta M_i
=
M_i^{LONG}
-
M_i^{SHORT}.
}
\]

Also report whether the top-scoring option is gold.

---

## 19. Computational-buffer decision

Declare:

\[
\boxed{
\texttt{IMMEDIATE\_BUFFER\_SIGNAL}
}
\]

iff:

1. at least 8 MC families have valid short/long scoring;
2. mean:
   \[
   \Delta M>0;
   \]
3. 95% paired family-bootstrap interval for \(\Delta M\) excludes 0;
4. at least 60% of families have:
   \[
   \Delta M_i>0.
   \]

Secondary binary readout:

\[
Top1^{LONG}>Top1^{SHORT}
\]

is reported but does not drive the decision.

Interpretation:

> **More semantically empty forced reasoning computation moves the immediate answer state toward the correct option.**

---

## 20. Buffer technical validation

Use the disjoint technical4 families first.

Validate:

1. exact short forced-token count;
2. exact long forced-token count;
3. one-token-at-a-time KV continuation;
4. forced native close at expected position;
5. zero free-generated tokens after close;
6. fixed answer prefix identical across conditions;
7. candidate likelihoods reproducible under deterministic teacher forcing;
8. no image tokens;
9. no option-order mismatch.

If immediate scoring cannot be implemented cleanly:

\[
\boxed{
\texttt{IMMEDIATE\_BUFFER\_ASSAY\_BLOCKED}.
}
\]

Skip Phase B while preserving Phase A.

Do not stop the semantic priming experiment.

---

## 21. Why free-generation accuracy is not used for the buffer test

The target hypothesis is:

\[
\text{additional computation changes the answer state}
\]

not:

\[
\text{additional computation + uncontrolled subsequent reasoning changes final generation}.
\]

Immediate scoring measures the state directly after the forced computation budget and avoids the Stage 13C reopening confound.

---

## 22. Decision hierarchy

### `SEMANTIC_PRIMING_ONLY`

Derived-state priming confirmed; buffer absent or blocked.

### `BUFFER_ONLY`

Immediate buffer signal confirmed; semantic priming not confirmed.

### `COMPLEMENTARY_BUFFER_AND_SEMANTIC_PRIMING`

Both signals pass.

Interpretation:

> post-evidence Thinking benefit has evidence for both content-independent computation and content-dependent semantic state construction.

### `POST_EVIDENCE_MECHANISM_PARTIAL`

One arm is suggestive but subthreshold.

### `POST_EVIDENCE_MECHANISM_UNRESOLVED`

Neither arm provides robust support.

Stage 13A remains unchanged.

---

## 23. Identification boundary

This project does not have a hybrid checkpoint where Thinking can be toggled ON/OFF while all parameters remain fixed.

Therefore:

- immediate buffer assay = same-Thinking-checkpoint intervention;
- semantic priming assay = portability/sufficiency in Instruct;
- Stage 13A = deployed-variant comparison.

Do not claim:

> "we fully decompose the causal effect of enabling Thinking."

Allowed:

> "we identify mechanisms capable of contributing to the confirmed post-evidence Thinking advantage."

---

## 24. Seed policy

### Phase A

Use:

\[
\boxed{
5\text{ frozen seeds per family-condition}.
}
\]

Derive from:

`SHA256(stage13d-v1|family_id|condition|replicate)`.

Same replicate indices across A0–A3.

No best-of-five.

### Phase B

Teacher-forced candidate scoring is deterministic.

No sampling-based answer generation is used.

---

## 25. Statistical reporting

Independent unit:

\[
\boxed{
\text{family}.
}
\]

For Phase A:

- family-level 5-seed accuracy;
- paired mean differences;
- 10,000 family-bootstrap percentile intervals;
- positive/zero/negative family effects;
- missingness bounds.

For Phase B:

- family-level short/long margins;
- paired mean \(\Delta M\);
- 10,000 family-bootstrap interval;
- proportion with \(\Delta M_i>0\).

Seeds are not independent population samples.

---

## 26. Technical validity for Phase A

Use:

\[
\texttt{TECHNICALLY\_VALID}
=
\texttt{INPUT\_VALID}
\land
\texttt{SCOREABLE}
\land
\neg\texttt{TRUNCATED\_BEFORE\_OUTCOME}.
\]

A cap hit with a clear unretracted answer is scoreable.

Pre-outcome truncation is technical missingness.

Repetition is scientific behavior.

If >20% technical missingness occurs in any A0–A3 arm during a frozen initial-8-family tranche:

\[
\texttt{SEMANTIC\_ARM\_TECHNICAL\_STOP}.
\]

Stop remaining Phase A calls without prompt/cap changes.

Phase B may proceed only if its own technical contract is valid.

---

## 27. Scoring audit

### Phase A

- score arms separately before paired contrasts;
- use frozen MathVision equivalence policy;
- review all ambiguous cases;
- deterministic 20% second-pass QC.

### Phase B

- programmatic option-likelihood scoring;
- independently recompute margins from saved token log-probabilities;
- preserve full token-level receipts.

Same-agent semantic QC is not independent-rater reliability.

---

## 28. Compute estimate

Assume approximately 20 safe semantic families.

### Phase A

Maximum if all 24 are eligible:

\[
24\times4\times5
=
480
\]

Instruct calls.

Recommended execution rule:

- run A0–A3 only on safe-semantic families;
- archive ineligible families without scientific calls.

### Phase B

No long free generation.

Cost consists of forced dummy forward passes plus candidate teacher forcing on MC families.

Target:

\[
\boxed{
<8\text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
12\text{ GPU-hours}
}
\]

unless separately approved.

---

## 29. Required figures

### Figure 13D-1 — Derived-state priming

Show:

\[
I_{\mathrm{BASE}},
\quad
I_{\mathrm{DUMMY}},
\quad
I_{\mathrm{SHUFFLED}},
\quad
I_{\mathrm{DERIVED}}.
\]

### Figure 13D-2 — Family-level semantic effects

Show:

\[
I_{\mathrm{DERIVED}}-I_{\mathrm{DUMMY}}
\]

per family.

### Figure 13D-3 — Selected-case rescue

For overlapping Stage 13A Thinking-only families, show baseline/dummy/shuffled/derived outcomes.

### Figure 13D-4 — Immediate buffer margin

Show:

\[
M^{SHORT}
\quad\text{vs}\quad
M^{LONG}.
\]

### Figure 13D-5 — Buffer-effect distribution

Show:

\[
\Delta M_i=M_i^{LONG}-M_i^{SHORT}.
\]

---

## 30. Required artifacts

Produce:

1. `stage13d_post_evidence_mechanism_spec.md`
2. `stage13d_frozen24_manifest.json`
3. `stage13d_technical4_manifest.json`
4. `stage13d_source_trace_manifest.json`
5. `stage13d_derived_state_extractions.json`
6. `stage13d_derived_state_audit.json`
7. `stage13d_semantic_context_controls.json`
8. `stage13d_semantic_seed_manifest.json`
9. `stage13d_semantic_results.parquet`
10. `stage13d_semantic_scoring_audit.json`
11. `stage13d_mc_buffer_manifest.json`
12. `stage13d_buffer_forced_sequences.json`
13. `stage13d_buffer_technical_validation.json`
14. `stage13d_buffer_option_logprobs.parquet`
15. `stage13d_buffer_family_margins.parquet`
16. `stage13d_missingness_bounds.json`
17. `stage13d_primary_inference.json`
18. `stage13d_decision.json`
19. `stage13d_resource_accounting.json`
20. `stage13d_summary.md`

Preserve all Stage 12 and prior Stage 13 artifacts unchanged.

---

## 31. Exactly one recommendation at completion

### If `COMPLEMENTARY_BUFFER_AND_SEMANTIC_PRIMING`

Recommend:

> Treat this as the final 4B Thinking-mechanism result and stop further mechanism expansion.

### If `SEMANTIC_PRIMING_ONLY`

Recommend:

> Validate the derived-state priming effect once on an independent fresh cohort before elevating it to a broad mechanism claim.

### If `BUFFER_ONLY`

Recommend:

> Compare the immediate computational-buffer effect with a matched text-only reasoning model before making a modality-specific interpretation.

### If `POST_EVIDENCE_MECHANISM_PARTIAL`

Recommend:

> Preserve the supported component as secondary mechanism evidence and stop additional decomposition unless a cleaner hybrid ON/OFF model becomes available.

### If `POST_EVIDENCE_MECHANISM_UNRESOLVED`

Recommend:

> Retain Stage 13A's confirmed post-evidence advantage as the strongest Thinking claim and close the mechanism branch.

Do not launch automatically.

---

## 32. Final decision target

Stage 13D exists to answer:

\[
\boxed{
\textbf{What makes Thinking useful after the correct visual evidence is already available?}
}
\]

The semantic test asks:

\[
\boxed{
I(Q+E^*+D_T)
>
I(Q+E^*+\text{dummy/shuffled content})?
}
\]

The compute test asks:

\[
\boxed{
M^{LONG}>M^{SHORT}
}
\]

immediately after semantically empty forced reasoning, with no opportunity for free reasoning reopening.

A dual positive result would support:

> **After evidence is equalized, Thinking can help through both additional computation and task-specific semantic state construction.**
