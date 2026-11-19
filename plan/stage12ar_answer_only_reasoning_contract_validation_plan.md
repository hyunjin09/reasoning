# Stage 12A-R — Prompt-Contract Validation for Answer-Only vs Reasoning+Answer

## 0. One-line objective

Establish two technically valid, behaviorally distinct conditions on the **same Qwen3-VL-2B-Instruct checkpoint** before any Lost-Keys scientific inference:

\[
\boxed{
D=\text{stable Answer-Only}
}
\]

and

\[
\boxed{
C=\text{stable Reasoning+Answer}
}
\]

The scientific Lost-Keys question is **not evaluated in this stage**.

No \(E^*\) correctness, task correctness, rescue rate, or GO/NO-GO scientific endpoint may be opened until the D/C contracts pass this technical validation.

---

# 1. Why this stage is necessary

Stage 12A stopped at the technical gate.

The frozen 12-case results after the one previously allowed wording repair were:

- Evidence probe \(E\): technically acceptable.
- Answer-Only \(D\): 12/12 committed finals, 0/12 cap hits, 0/12 severe repetition, but only 9/12 strict format-valid.
- Reasoning+Answer \(C\): 8/12 committed finals, 4/12 cap hits, 6/12 severe repetition, and only 8/12 strict format-valid.

Therefore the Lost-Keys hypothesis remains untested.

The current bottleneck is not statistical power. It is that the experimental contrast:

\[
\boxed{
\text{Answer-Only}
\quad\text{vs}\quad
\text{Reasoning+Answer}
}
\]

has not yet been operationalized reliably.

Running more scientific samples before fixing this would only produce more data under an unstable condition.

---

# 2. Paper dependency

The intended top-level paper story is:

\[
\text{visual evidence recoverable?}
\rightarrow
\text{Answer-Only success?}
\rightarrow
\text{Reasoning rescue?}
\rightarrow
\text{Thinking rescue?}
\]

Stage 12A-R validates only the second arrow's experimental manipulation.

If D and C cannot be made technically distinct and stable, do not proceed with the multimodal Lost-Keys headline.

If D and C validate cleanly, rerun the frozen Stage 12A scientific test next.

---

# 3. What remains frozen

The following objects must not change.

## Model

\[
\boxed{
\textbf{Qwen3-VL-2B-Instruct}
}
\]

Use the same pinned checkpoint intended for Stage 12A.

## Dataset

Keep the original Stage 11A / Stage 12A:

\[
\boxed{
61 \text{ independent }E^*\text{-eligible MathVision families}
}
\]

No new benchmark discovery.

No family is added or dropped based on technical behavior.

## Evidence

All frozen:

- 61 family IDs;
- 157 \(E^*\) facts;
- image hashes;
- original questions;
- source answers;
- \(E^*\) requests;
- \(E^*\) sufficiency judgments.

Do not modify \(E^*\).

## Scientific thresholds

The Stage 12A scientific P1–P4 definitions and scientific GO/NO-GO thresholds remain unchanged and are not evaluated here.

---

# 4. Evidence probe E

The evidence-probe condition already passed the first technical gate.

Therefore:

\[
\boxed{
\textbf{E is frozen and is not redesigned in Stage 12A-R.}
}
\]

Do not spend GPU on further E prompt search.

The original E contract remains the future scientific condition.

---

# 5. Desired D/C experimental contrast

The manipulation must be conceptually clean.

## D — Instruct Answer-Only

The model should solve internally if needed but emit **only the final answer**.

Observable contract:

\[
\boxed{
\text{no visible intermediate reasoning}
}
\]

## C — Instruct Reasoning+Answer

The same checkpoint should be explicitly asked to externalize step-by-step reasoning and then commit a final answer.

Observable contract:

\[
\boxed{
\text{visible intermediate reasoning}
\rightarrow
\text{terminal final answer}
}
\]

The purpose is not to make D and C identical in token budget.

The purpose is to create a controlled difference in whether intermediate reasoning is externally elicited.

---

# 6. Output-type clarification

The 61 families contain:

- 24 multiple-choice;
- 37 open-ended.

The previously user-approved native-answer clarification remains frozen.

## Multiple choice

Final answer type:

\[
\boxed{
\text{one option letter}
}
\]

## Open-ended

Final answer type:

\[
\boxed{
\text{one final value or expression}
}
\]

No options may be invented for open-ended problems.

---

# 7. Technical development set

Reuse the already-fixed 12 Stage 12A technical families:

- 2035
- 750
- 528
- 2749
- 653
- 725
- 2359
- 57
- 2975
- 1140
- 1988
- 2553

Composition:

- 4 multiple-choice;
- 8 open-ended.

These cases are the **prompt-development set**.

Their prior Stage 12A correctness remains unopened.

Only:

- output-format compliance;
- completion;
- cap behavior;
- repetition pathology

may be inspected.

---

# 8. Fresh technical validation set

Before running any new prompt candidate, deterministically freeze a second:

\[
\boxed{
12 \text{ families}
}
\]

from the remaining 49 Stage 12A families.

Selection rule:

- deterministic hash over family ID with a fixed new seed;
- target 4–6 multiple-choice where possible;
- otherwise preserve the natural MC/open-ended mix.

Do not use:

- task correctness;
- \(E^*\) probe correctness;
- prior native outcomes;
- difficulty;
- subject;
- expected model behavior.

This second set is the **technical validation set**.

It must remain untouched until a single D/C contract has been selected using the development set.

---

# 9. Runtime

For D and C use the same Instruct checkpoint and the same base generation recipe.

Default generation recipe:

- temperature = 0.7
- top-p = 0.8
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 1.5
- identical image preprocessing
- identical tokenizer / processor
- identical runtime backend
- identical seed policy

Do not use Thinking-model decoding settings.

The D/C difference should come from the **prompt/output contract**, not a different model or sampling family.

---

# 10. D prompt — freeze one minimal repair

Stage 12A repair-v3 already achieved:

- 12/12 committed finals;
- 0 cap hits;
- 0 severe repetition;
- 9/12 strict format validity.

Therefore do not search a large D prompt space.

Use exactly one new minimal contract:

## D-MC

> Solve the problem silently.  
> Do not show any reasoning or explanation.  
> Respond with exactly one option letter: A, B, C, D, or E.  
> Output nothing else.

## D-Open

> Solve the problem silently.  
> Do not show any reasoning or explanation.  
> Respond with exactly one final value or mathematical expression.  
> Output nothing else.

The exact original image/question remains unchanged before this suffix.

---

# 11. C prompt — bounded canonical candidates

Stage 12A C is the unresolved condition.

Evaluate exactly **two** predeclared C prompt candidates on the 12-case development set.

Do not add a third candidate after outcomes.

## C0 — Canonical CoT

Append:

> Let's think step by step.

The original MathVision question/output hint remains intact.

Purpose:

> use the simplest canonical explicit-reasoning elicitation.

## C1 — CoT + explicit terminal contract

Append:

> Let's think step by step.  
> After your reasoning, end with exactly one line of the form `Final answer: X`, where X is the final option letter, value, or expression.

Purpose:

> preserve explicit reasoning while making answer commitment easier to detect.

For MCQ, X is the option letter.

For open-ended problems, X is the final value/expression.

---

# 12. C generation budget

Use one common C budget during technical development:

\[
\boxed{
32768 \text{ generated tokens}
}
\]

Rationale:

- 8192 was not completion-valid in Stage 12A;
- Qwen's benchmark-specific Instruct MathVision protocol uses a much larger budget;
- this is a technical condition-definition step, not a short-CoT ablation.

A longer budget is **not** considered successful if the output contains severe repetition and merely reaches the cap later.

Record both:

- cap hit;
- severe repetition.

Do not test a larger budget in this stage.

---

# 13. D generation budget

Use:

\[
\boxed{
64 \text{ generated tokens}
}
\]

for D technical validation.

The output contract requires one answer only.

A 64-token cap avoids accidental truncation of an open-ended mathematical expression while still preventing long visible reasoning from becoming the condition.

If visible reasoning begins, the response is format-invalid even if a final answer later appears.

---

# 14. Development-set technical endpoints

No correctness scoring.

For each D/C response record:

- `FORMAT_VALID`
- `VISIBLE_REASONING_PRESENT`
- `COMMITTED_FINAL`
- `CAP_HIT`
- `SEVERE_REPETITION`
- generated-token count
- EOS / stop reason

For C additionally record:

- whether reasoning is substantively present;
- whether a terminal final-answer commitment exists.

---

# 15. D development gate

The fixed D repair passes development only if:

\[
\boxed{
\text{format valid}\ge10/12
}
\]

\[
\boxed{
\text{committed final}\ge11/12
}
\]

\[
\boxed{
\text{visible reasoning}\le1/12
}
\]

\[
\boxed{
\text{cap hits}=0
}
\]

\[
\boxed{
\text{severe repetition}=0
}
\]

If D fails, STOP Stage 12A-R.

Do not search another Answer-Only wording.

---

# 16. C candidate gate

Each C candidate is evaluated independently.

A candidate is technically acceptable only if:

\[
\boxed{
\text{visible reasoning}\ge10/12
}
\]

\[
\boxed{
\text{committed final}\ge10/12
}
\]

\[
\boxed{
\text{format valid}\ge10/12
}
\]

\[
\boxed{
\text{cap hits}\le1/12
}
\]

\[
\boxed{
\text{severe repetition}\le1/12
}
\]

If neither C0 nor C1 passes:

\[
\boxed{
\textbf{TECHNICAL STOP}
}
\]

Do not search more C prompts in this stage.

---

# 17. C candidate selection rule

If only one candidate passes, freeze it.

If both pass, choose by the following priority:

1. fewer severe-repetition cases;
2. fewer cap hits;
3. more committed finals;
4. more strict format-valid outputs;
5. shorter median generated length;
6. if still tied, choose C0 because it is the simpler intervention.

Do not use:

- correctness;
- rescue;
- \(E^*\) state;
- answer quality

to choose C.

---

# 18. Fresh validation gate

Once one D and one C contract are frozen, run them on the untouched 12-case validation set.

No prompt modification is allowed after these outputs.

## D validation requirements

\[
\boxed{
\text{format valid}\ge10/12
}
\]

\[
\boxed{
\text{committed final}\ge11/12
}
\]

\[
\boxed{
\text{visible reasoning}\le1/12
}
\]

\[
\boxed{
\text{cap hits}=0
}
\]

\[
\boxed{
\text{severe repetition}=0
}
\]

## C validation requirements

\[
\boxed{
\text{visible reasoning}\ge10/12
}
\]

\[
\boxed{
\text{committed final}\ge10/12
}
\]

\[
\boxed{
\text{format valid}\ge10/12
}
\]

\[
\boxed{
\text{cap hits}\le1/12
}
\]

\[
\boxed{
\text{severe repetition}\le1/12
}
\]

Both must pass.

---

# 19. Decision states

## CONTRACT_VALID

Declare only if:

- D passes development;
- one C candidate passes development;
- frozen D/C both pass the untouched validation set.

Interpretation:

> The Answer-Only vs Reasoning+Answer manipulation is technically operationalized and can be used for the Stage 12A Lost-Keys scientific test.

Do not run the 61-family scientific test automatically.

## D_INVALID

If D fails the development or validation gate:

> The Answer-Only condition is not reliably enforceable under the current setup.

Stop.

## C_INVALID

If no C candidate passes development, or the frozen C fails validation:

> The Reasoning+Answer condition is not completion-valid enough for the Lost-Keys comparison.

Stop.

## CONTRACT_UNSTABLE

If development passes but untouched validation fails:

> The prompt contract overfits / does not generalize technically across the cohort.

Stop.

---

# 20. What this stage may and may not conclude

## May conclude

If valid:

> We have a technically stable same-checkpoint manipulation that separates answer-only output from explicit reasoning-plus-answer output.

## May not conclude

This stage cannot say:

- reasoning improves accuracy;
- Lost-Keys cases exist;
- reasoning selectively rescues \(E^+\) failures;
- Thinking is better;
- visual retrieval is the cause.

No task correctness is opened.

---

# 21. Scientific rerun after CONTRACT_VALID

The next stage should rerun Stage 12A scientifically under the frozen contracts.

Conditions:

\[
E,\quad D,\quad C
\]

on all 61 families.

Primary scientific endpoints remain:

\[
P1=P(E^+)
\]

\[
P2=P(E^+\land D^-)
\]

\[
P3=P(C^+\mid D^-,E^+)
\]

\[
P4=
P(C^+\mid D^-,E^+)
-
P(C^+\mid D^-,E^-)
\]

The prompt-development and validation sets may remain in the 61-family scientific cohort because no task correctness was used for contract selection, but the scientific report must include a sensitivity analysis excluding all 24 technical cases.

Do not launch that scientific rerun automatically.

---

# 22. Why no more samples are needed yet

The current uncertainty is not statistical.

It is:

\[
\boxed{
\textbf{Can D and C be made into valid experimental conditions?}
}
\]

Increasing \(n\) before this is resolved only multiplies invalid observations.

Therefore Stage 12A-R intentionally uses:

- 12 development cases;
- 12 untouched validation cases;

and no full-cohort generation.

---

# 23. Null discipline

Failure of this technical contract does **not** imply:

- no Lost-Keys phenotype;
- no benefit from reasoning;
- no Thinking advantage;
- no visual-access bottleneck.

It only means:

> this particular Answer-Only vs Reasoning+Answer operationalization is not stable enough to support the intended scientific comparison.

Conversely, technical success does not imply any scientific effect.

---

# 24. Compute budget

Maximum new logical calls:

## Development

- D: 12
- C0: 12
- C1: 12

Total:

\[
36
\]

## Validation

- D: 12
- frozen C: 12

Total:

\[
24
\]

Grand maximum:

\[
\boxed{
60 \text{ calls}
}
\]

No E reruns.

Target:

\[
\boxed{
<1.5 \text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
2.5 \text{ GPU-hours}
}
\]

unless explicitly approved.

---

# 25. Required artifacts

Produce:

1. `stage12ar_contract_validation_spec.md`
2. `stage12ar_development_manifest.json`
3. `stage12ar_validation_manifest.json`
4. `stage12ar_prompt_contracts.md`
5. `stage12ar_development_results.parquet`
6. `stage12ar_candidate_selection.json`
7. `stage12ar_validation_results.parquet`
8. `stage12ar_contract_decision.json`
9. `stage12ar_resource_accounting.json`
10. `stage12ar_summary.md`

Preserve all Stage 12A technical artifacts separately.

---

# 26. Final summary format

The summary must report:

1. D development compliance;
2. C0 development compliance;
3. C1 development compliance;
4. selected C contract and why;
5. untouched validation results;
6. exact decision token.

End with exactly one:

- `CONTRACT_VALID — Stage12A scientific rerun is justified`
- `D_INVALID — do not rerun Stage12A`
- `C_INVALID — do not rerun Stage12A`
- `CONTRACT_UNSTABLE — do not rerun Stage12A`

Do not launch the scientific rerun.

---

# 27. Final decision target

This stage exists to answer only:

\[
\boxed{
\textbf{Can we establish a technically stable same-checkpoint contrast between
Answer-Only and explicit Reasoning+Answer before evaluating the Lost-Keys hypothesis?}
}
\]

If yes, rerun Stage 12A scientifically next.

If no, stop the Lost-Keys branch before spending more samples.
