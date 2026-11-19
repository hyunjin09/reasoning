# Stage 12B-R — Pathology-Aware Validity Repair for VLM Failure Profiling

## 0. One-line objective

Repair the Stage 12B validity criterion so that it matches the actual research question:

\[
\boxed{
\textbf{Where and why does a modern VLM fail?}
}
\]

The key change is:

\[
\boxed{
\text{technical invalidity}
\neq
\text{pathological model reasoning}
}
\]

Severe repetition, repeated reopening of a solution, nonconvergent reasoning, or unusually long reasoning are **scientific behaviors to preserve and analyze**, not automatic technical exclusions, provided the input is valid and the output remains scoreable.

This stage validates that distinction prospectively on an untouched technical set before any Stage 12B correctness or bottleneck proportions are opened.

---

# 1. Why Stage 12B stopped

Stage 12B used three conditions:

\[
E=\text{direct evidence probe}
\]

\[
N=\text{Native Instruct task solving}
\]

\[
O=\text{image-free Equal-Evidence Oracle}
\]

On the frozen 12 technical cases:

- \(E\): 12/12 parseable, 0 caps, 0 severe repetition;
- \(N\): 12/12 committed finals, 0 caps, but 4/12 severe repetition;
- \(O\): 11/12 committed finals, 0 caps, but 3/12 severe repetition.

The stage stopped because severe repetition had been predeclared as a technical gate.

However, this conflicts with the scientific question.

A model that:

- receives the correct input,
- runs to normal completion,
- produces a scoreable answer,
- but repeatedly reopens the same interpretation/calculation

may be exhibiting exactly the kind of **downstream reasoning pathology** the paper aims to explain.

Therefore the next step is not prompt search.

It is to prospectively redefine assay validity around **scoreability and input integrity**, while preserving reasoning pathologies as scientific labels.

---

# 2. Paper-level motivation

The new Claim 1 asks:

\[
\boxed{
\textbf{When a VLM is wrong, where in the evidence-to-reasoning pipeline does it fail?}
}
\]

The intended decomposition is:

\[
\text{Image}
\rightarrow
E^*
\rightarrow
\text{task-conditioned use}
\rightarrow
\text{downstream reasoning}
\rightarrow
\text{answer}
\]

A loop or repeated reinterpretation **after the required evidence is already available** is not necessarily a broken assay.

It may be evidence for:

\[
\boxed{
\text{failure of reasoning convergence / utilization}
}
\]

Therefore the validity definition must not censor these behaviors before the scientific analysis begins.

---

# 3. Main methodological repair

## Old Stage 12B rule

A response could fail the technical gate because:

\[
\text{SEVERE\_REPETITION}=1
\]

even if it:

- used the intended input;
- stopped normally;
- contained a committed final answer;
- was scoreable.

## New Stage 12B-R rule

A response is **technically valid** if the experimental input is intact and the scientific outcome can be scored.

Reasoning pathology is recorded separately.

Formally:

\[
\boxed{
\texttt{TECHNICALLY\_VALID}
=
\texttt{INPUT\_VALID}
\land
\texttt{SCOREABLE}
\land
\neg\texttt{TRUNCATED\_BEFORE\_OUTCOME}
}
\]

No repetition term appears in this validity equation.

---

# 4. What remains completely frozen

Do not modify:

- all 61 MathVision families;
- all 157 frozen \(E^*\) facts;
- image hashes;
- original questions;
- source answers;
- evidence requests;
- prior \(E^*\) sufficiency judgments;
- Qwen3-VL-4B-Instruct checkpoint revision;
- BF16/vLLM runtime;
- image preprocessing;
- Stage 12B sampling recipe;
- E/N/O prompt templates;
- E cap = 256;
- N/O cap = 32768;
- Stage 12B scientific P1–P6 definitions;
- Stage 12B bottleneck B1–B4 definitions.

No prompt repair.

No cap search.

No sampling search.

No correctness-guided adaptation.

---

# 5. Model and runtime

Use exactly:

\[
\boxed{
\textbf{Qwen3-VL-4B-Instruct}
}
\]

revision:

\[
\boxed{
\texttt{ebb281ec70b05090aa6165b016eac8ec08e71b17}
}
\]

Generation:

- temperature = 0.7
- top-p = 0.8
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 1.5
- E cap = 256
- N cap = 32768
- O cap = 32768

Use the same seed policy as Stage 12B.

---

# 6. Development vs validation roles

The original Stage 12B 12-case set has already exposed the mismatch between the old gate and the research question.

Therefore treat those 12 cases as:

\[
\boxed{
\textbf{technical development / audit cases}
}
\]

Do not use them to validate the repaired rule.

Their correctness remains unopened.

---

# 7. Freeze a fresh untouched 12-case validation set

Before any new generation, deterministically select:

\[
\boxed{
12 \text{ families}
}
\]

from the remaining 49 Stage 12B families.

Selection must depend only on:

- family identity;
- answer type if needed to preserve a reasonable MC/open-ended mix.

Do not use:

- prior model outputs;
- task correctness;
- \(E^*\) correctness;
- difficulty;
- subject;
- expected pathology;
- token length.

Record the exact deterministic selection rule and hash before generation.

The fresh 12 cases are used only to validate **scoreability and input integrity**.

---

# 8. Conditions on the fresh validation set

Run the original frozen:

\[
\boxed{
E,\quad N,\quad O
}
\]

with no changes.

## E — evidence probe

Image present.

Ask only for the frozen task-critical visual evidence.

## N — Native Instruct

Exact original image + original question.

No added CoT instruction.

No answer-only instruction.

Spontaneous reasoning is allowed.

## O — Equal-Evidence Oracle

No image.

Exact frozen \(E^*\) supplied as text.

Original question preserved.

No answer leakage.

---

# 9. New technical validity taxonomy

For every generated response assign the following **without opening gold correctness**.

---

## 9.1 INPUT_VALID

True iff:

- intended family is loaded;
- correct image is present for E/N;
- no image is present for O;
- correct frozen \(E^*\) is inserted into O;
- original question matches the frozen source;
- no final answer leakage is introduced;
- request labels correspond to the intended evidence facts.

If false:

\[
\boxed{
\texttt{TECHNICAL\_INVALID}
}
\]

---

## 9.2 SCOREABLE

### E

True iff the response contains an interpretable answer for the requested evidence fact(s), even if semantically wrong.

### N/O

True iff a unique scientific task outcome can be extracted.

Acceptable examples:

- one explicit final answer;
- a later explicit revision that unambiguously supersedes an earlier provisional answer;
- a standard benchmark-extractable answer even after long reasoning.

Not scoreable:

- multiple contradictory terminal answers with no clear final commitment;
- no task answer at all;
- malformed output where the target answer cannot be determined.

Do not require stylistic cleanliness.

---

## 9.3 TRUNCATED_BEFORE_OUTCOME

True iff the generation cap is reached before a scoreable outcome is produced.

This is a technical invalidity for primary scientific profiling.

If the model reaches the cap **after** already producing a unique committed answer, preserve both:

- the answer;
- the cap/repetition pathology.

Do not automatically invalidate the scoreable outcome.

Record this case separately.

---

# 10. Scientific pathology labels

These labels are **not exclusion criteria**.

Record them for N and O.

---

## R1 — SEVERE_REPETITION

The model repeatedly cycles through substantially the same interpretation, calculation, or argument without meaningful progress.

Semantic review is primary.

Exact n-gram statistics are supporting diagnostics only.

---

## R2 — REOPEN_AFTER_PROVISIONAL_ANSWER

The model reaches a plausible/provisional answer and then reopens the problem, restarting interpretation or derivation.

---

## R3 — NONCONVERGENT_REASONING

The model continues exploring mutually inconsistent or repeatedly revised hypotheses without stable convergence.

This may overlap with R1/R2.

---

## R4 — LONG_ADVANCING_COMPUTATION

The output is very long but continues making distinguishable computational progress.

Example:

- long digit enumeration;
- extended case analysis.

This is **not** severe repetition merely because it is long.

---

## R5 — TERMINAL_AMBIGUITY

Multiple incompatible answers remain at the end with no unique commitment.

Unlike R1–R4, this also makes the output unscoreable.

---

# 11. Why pathology must remain scientific data

The paper asks where failures occur.

If correct evidence is already supplied in O but the model:

\[
\text{reopens}
\rightarrow
\text{loops}
\rightarrow
\text{fails to converge}
\]

then this behavior is directly relevant to a downstream reasoning bottleneck.

Therefore:

\[
\boxed{
\text{reasoning pathology}
\subset
\text{scientific outcome space}
}
\]

not:

\[
\text{reasoning pathology}
\subset
\text{technical exclusions}
\]

unless it prevents a scoreable outcome.

---

# 12. Fresh validation gate

No task correctness is opened.

The repaired assay is valid if all of the following hold.

## E

\[
\boxed{
\text{INPUT\_VALID}=12/12
}
\]

\[
\boxed{
\text{SCOREABLE}\ge10/12
}
\]

\[
\boxed{
\text{TRUNCATED\_BEFORE\_OUTCOME}\le1/12
}
\]

## N

\[
\boxed{
\text{INPUT\_VALID}=12/12
}
\]

\[
\boxed{
\text{SCOREABLE}\ge10/12
}
\]

\[
\boxed{
\text{TRUNCATED\_BEFORE\_OUTCOME}\le1/12
}
\]

## O

\[
\boxed{
\text{INPUT\_VALID}=12/12
}
\]

\[
\boxed{
\text{SCOREABLE}\ge10/12
}
\]

\[
\boxed{
\text{TRUNCATED\_BEFORE\_OUTCOME}\le1/12
}
\]

There is **no repetition threshold**.

All R1–R5 frequencies must still be reported.

---

# 13. Decision states

## VALIDITY_REPAIRED

Declare if E/N/O all pass the fresh validation gate.

Interpretation:

> The original Stage 12B assay is technically scoreable under a pathology-aware validity definition that preserves native reasoning failures as scientific data.

Do not interpret bottleneck prevalence yet.

---

## SCOREABILITY_FAIL

Declare if N or O produces too many unscoreable or pre-outcome-truncated responses.

Interpretation:

> The assay still cannot reliably separate scientific model failures from missing outcomes.

Stop.

---

## INPUT_INTEGRITY_FAIL

Declare if any systematic prompt/image/oracle corruption is detected.

Stop.

---

# 14. What happens after VALIDITY_REPAIRED

Freeze the repaired validity rule.

Then resume the original Stage 12B scientific profiling on all 61 families.

Important:

- do not change E/N/O prompts;
- do not change runtime;
- do not change caps;
- do not exclude repetitive reasoning simply because it is repetitive.

The scientific cohort may include:

- the original 12 development cases;
- the 12 fresh validation cases;
- the remaining 37 cases.

Because no task correctness was used in validity repair, all 61 may remain in the main analysis.

For transparency, report sensitivity analyses excluding:

1. the original 12 development cases;
2. all 24 technical-development/validation cases.

---

# 15. Scientific profiling after validity repair

The original Stage 12B taxonomy remains frozen.

For native failures \(N^-\):

---

## B1 — Perceptual / evidence-availability candidate

\[
\boxed{
E^- \land O^+
}
\]

---

## B2 — Task-context evidence access/use candidate

\[
\boxed{
E^+ \land O^+
}
\]

This is the multimodal Lost-Keys-like state.

---

## B3 — Downstream reasoning candidate

\[
\boxed{
E^+ \land O^-
}
\]

---

## B4 — Mixed / unresolved

\[
\boxed{
E^- \land O^-
}
\]

Do not change these definitions.

---

# 16. Add one new secondary downstream taxonomy

For every native or oracle failure, classify the visible reasoning outcome into:

\[
\boxed{
\text{wrong-converged}
}
\]

\[
\boxed{
\text{loop/reopen pathology}
}
\]

\[
\boxed{
\text{nonconvergent/ambiguous}
}
\]

\[
\boxed{
\text{unresolved technical}
}
\]

This is secondary.

It does not replace B1–B4.

Its purpose is to answer a more specific version of:

> **Why does downstream reasoning fail after evidence is available?**

---

# 17. Key new scientific contrasts enabled by this repair

Once correctness is opened after validation:

## Oracle pathology shift

Compare:

\[
P(R_j\mid N^-)
\]

vs:

\[
P(R_j\mid O^-)
\]

for relevant pathology labels \(R_j\).

Question:

> does supplying correct \(E^*\) reduce evidence-search/reinterpretation pathologies, or do the same reasoning failures persist?

---

## Oracle persistence

For cases pathological in N, ask whether O:

- resolves the pathology;
- preserves the pathology;
- changes the pathology type.

This is especially informative when N and O fail on the same family.

---

## Evidence-resolved but reasoning-pathological state

Identify:

\[
\boxed{
E^+ \land O^- \land R_j
}
\]

These are particularly strong downstream-failure candidates because:

- the evidence is directly recoverable;
- the oracle explicitly supplies it;
- reasoning still fails pathologically.

---

# 18. Competing explanations

This repaired design distinguishes:

## A. Repetition was only a technical nuisance

Prediction:

- pathology labels occur but are weakly related to correctness/bottleneck type.

## B. Repetition is part of downstream failure

Prediction:

- R1/R2/R3 concentrate in \(O^-\), especially B3/B4.

## C. Repetition reflects unresolved visual interpretation

Prediction:

- pathology is common in N but decreases substantially in O when correct \(E^*\) is supplied.

This would itself support an upstream evidence-access interpretation.

---

# 19. What a null does NOT mean

If pathology labels are not associated with error:

- do not conclude reasoning convergence is never important;
- the main B1–B4 bottleneck profile may still be informative.

If fresh validation fails:

- do not infer anything about perceptual/access/downstream prevalence;
- do not infer the Lost-Keys hypothesis is false;
- do not infer the existing mechanistic retrieval results are wrong.

---

# 20. Reviewer-facing methodological rationale

The repaired validity rule should be stated explicitly:

> **We distinguish assay failure from model failure. Outputs are excluded only when the experimental input is corrupted, no unique scientific outcome can be extracted, or generation truncates before an outcome. Repetition, solution reopening, and nonconvergent reasoning are retained as model behaviors and analyzed as candidate downstream failure modes.**

This is aligned with the paper's actual question:

\[
\boxed{
\textbf{where and why reasoning fails}
}
\]

rather than artificially conditioning the analysis on clean reasoning trajectories.

---

# 21. Compute budget

## Validation phase

Fresh 12 families × 3 conditions:

\[
\boxed{
36 \text{ calls}
}
\]

Target:

\[
\boxed{
<0.6 \text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
1.0 \text{ GPU-hours}
}
\]

## Full Stage 12B scientific profiling

Do **not** launch automatically.

After `VALIDITY_REPAIRED`, the remaining Stage 12B calls may be authorized separately.

---

# 22. Required artifacts

Produce:

1. `stage12br_pathology_aware_validity_spec.md`
2. `stage12br_validation_manifest.json`
3. `stage12br_validity_rules.json`
4. `stage12br_pathology_annotation_guide.md`
5. `stage12br_validation_results.parquet`
6. `stage12br_pathology_labels.parquet`
7. `stage12br_validation_decision.json`
8. `stage12br_resource_accounting.json`
9. `stage12br_summary.md`

Preserve all Stage 12B artifacts unchanged.

---

# 23. Final summary requirements

Report:

1. fresh validation IDs and deterministic selection rule;
2. E/N/O input-integrity rates;
3. E/N/O scoreability rates;
4. truncation-before-outcome rates;
5. R1–R5 pathology frequencies;
6. exact decision token;
7. no task correctness;
8. no bottleneck proportions;
9. no CoT/Thinking.

End with exactly one:

- `VALIDITY_REPAIRED — Stage12B scientific profiling may resume`
- `SCOREABILITY_FAIL — do not resume Stage12B`
- `INPUT_INTEGRITY_FAIL — do not resume Stage12B`

---

# 24. Final decision target

This stage asks only:

\[
\boxed{
\textbf{Can the native and oracle conditions be treated as scientifically scoreable
while preserving pathological reasoning as part of the phenomenon rather than censoring it?}
}
\]

If yes, resume the original Stage 12B failure profiling.

If no, stop before any scientific bottleneck inference.
