# Stage 12C-R — Decoupled CoT Science and Thinking Completion Validation

## 0. One-line objective

Do **not** let the 4B Thinking completion issue block the main Claim 1 analysis.

Split the stopped Stage 12C into two independent branches:

\[
\boxed{
\textbf{Branch A: finish the scientifically valid Prompted-CoT rescue experiment}
}
\]

and

\[
\boxed{
\textbf{Branch B: separately validate the 4B Thinking MathVision completion regime}
}
\]

Branch A may produce a scientific result even if Branch B fails.

No Stage 12B-S label is changed.

---

# 1. Why the split is necessary

The frozen Stage 12C sanity check produced:

| Arm | Input-valid | Scoreable | Pre-outcome truncation | Result |
|---|---:|---:|---:|---|
| Prompted CoT \(C\) | 12/12 | 11/12 | 0/12 | **PASS** |
| Native Thinking \(T\) | 12/12 | 10/12 | 2/12 | **FAIL** |

The two Thinking failures reached the 40,960-token cap without a committed final answer.

Therefore:

- the same-checkpoint \(N\rightarrow C\) experiment is technically valid;
- the Thinking variant is not yet validated for scientific rescue estimation;
- the Lost-Keys / bottleneck correctness outcomes remain unopened for C/T;
- the main Claim 1 should no longer be blocked by the Thinking technical branch.

---

# 2. Paper-level dependency

Stage 12B-S already established the main behavioral result:

\[
\boxed{
P(O^+\mid N^-)=12/26=46.2\%
}
\]

and the complete-profile native failure map:

\[
B1=E^-O^+=11
\]

\[
B2=E^+O^+=1
\]

\[
B3=E^+O^-=3
\]

\[
B4=E^-O^-=11
\]

The strongest current finding is:

> Native multimodal failures frequently involve incomplete demonstrated recovery of task-critical visual evidence, often compounded by downstream reasoning difficulty; clearly recoverable-but-unused evidence is rare in this cohort.

The next scientific question is already answerable with CoT alone:

\[
\boxed{
\textbf{Can explicit inference-time reasoning rescue these frozen native failure states?}
}
\]

Thinking is an optional additional variant comparison, not a prerequisite for this claim.

---

# 3. Frozen objects shared by both branches

Preserve exactly:

- all 61 MathVision families;
- all 157 frozen \(E^*\) facts;
- all Stage 12B-S E/N/O generations;
- all Stage 12B-S correctness labels;
- all B1–B4 assignments;
- all pathology labels;
- all technical-unresolved labels;
- the sealed 12 Stage 12C sanity-family IDs;
- original images/questions/source answers;
- model revisions;
- image preprocessing;
- runtime environment;
- family seed policy.

No Stage 12B-S label may be changed after C/T generation.

---

# 4. Branch A — Complete the Prompted-CoT scientific rescue study

## 4.1 Scientific claim tested

Primary question:

\[
\boxed{
\textbf{Does explicit CoT prompting on the same Instruct checkpoint rescue
native failures associated with incomplete visual-evidence recovery, mixed failure, or both?}
}
\]

This is a clean same-checkpoint prompt intervention.

---

# 5. Branch A condition

Use:

\[
\boxed{
C=\text{Qwen3-VL-4B-Instruct + ` Let's think step by step.`}
}
\]

Checkpoint:

\[
\texttt{ebb281ec70b05090aa6165b016eac8ec08e71b17}
\]

Generation recipe:

- temperature = 0.7
- top-p = 0.8
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 1.5
- max output tokens = 32,768

Use the exact Stage 12C prompt and runtime.

No prompt search.

No retries.

No output-budget changes.

---

# 6. Reuse the 12 existing CoT sanity generations

The 12 Stage 12C CoT sanity outputs passed the frozen technical gate:

- 12/12 input-valid;
- 11/12 scoreable;
- 0/12 pre-outcome caps.

Their correctness was not opened.

Therefore:

\[
\boxed{
\textbf{reuse these 12 outputs in the full 61-family CoT analysis}
}
\]

Do not regenerate them.

Generate C only for the remaining:

\[
\boxed{
61-12=49 \text{ families}
}
\]

One logical call per remaining family.

---

# 7. Branch A validity rule

Reuse the pathology-aware rule:

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

Do not exclude for:

- severe repetition;
- reopening;
- nonconvergence;
- long advancing computation.

These remain scientific behavior labels.

---

# 8. Branch A blinded correctness scoring

After all 61 C outputs are complete and integrity-checked, open correctness.

Create C-only scoring packets containing:

- family ID;
- original question;
- source answer;
- C response.

Do not expose:

- E/N/O outcomes;
- B1–B4 label;
- native correctness;
- oracle correctness.

Use the same frozen MathVision equivalence policy as Stage 12B-S.

Labels:

- `CORRECT`
- `INCORRECT`
- `UNSCOREABLE_TECHNICAL`

Use the same ambiguity-triggered second review and deterministic 20% audit.

---

# 9. Branch A primary strata

Use the already sealed Stage 12B-S labels.

## B1 — primary upstream-rescuable stratum

\[
B1=E^-O^+,\qquad n=11
\]

Use the careful wording:

> incomplete demonstrated recovery of task-critical visual evidence.

Do not call all B1 cases visual misreads.

## B4 — primary mixed stratum

\[
B4=E^-O^-,\qquad n=11
\]

## B2/B3

- B2 \(n=1\)
- B3 \(n=3\)

Descriptive only.

---

# 10. Branch A primary endpoints

## A-P1 — CoT rescue of B1

\[
\boxed{
R_{C,B1}=P(C^+\mid B1)
}
\]

## A-P2 — CoT rescue of B4

\[
\boxed{
R_{C,B4}=P(C^+\mid B4)
}
\]

## A-P3 — Rescue selectivity

\[
\boxed{
\Delta_C=R_{C,B1}-R_{C,B4}
}
\]

Report:

- exact counts;
- Wilson 95% intervals;
- family-level 4,000-draw bootstrap interval for \(\Delta_C\).

---

# 11. Branch A overall paired comparison — secondary

Across families scoreable in both N and C, report:

\[
Acc_N,\qquad Acc_C
\]

and exact paired transitions:

- \(N^-C^+\): CoT rescue;
- \(N^+C^-\): CoT regression;
- both correct;
- both wrong.

Because N and C use the same checkpoint, an exact McNemar test may be reported as a secondary comparison.

Overall accuracy is not the headline.

---

# 12. Branch A visible-evidence analysis

For all 26 complete-profile native failures, annotate the visible C reasoning trace against frozen \(E^*\).

Use:

- `TRACE_E_FULL`
- `TRACE_E_PARTIAL`
- `TRACE_E_WRONG_OR_CONFLICTING`
- `TRACE_E_NOT_EXTERNALIZED`

The annotation packet contains only:

- family ID;
- frozen \(E^*\);
- C trace.

Do not expose:

- C correctness;
- N/E/O outcomes;
- B1–B4 label.

Important:

\[
\boxed{
\texttt{TRACE\_E\_NOT\_EXTERNALIZED}
\neq
\text{internal evidence absence}
}
\]

---

# 13. Branch A key mechanistic bridge

For B1, define:

\[
\boxed{
\texttt{EVIDENCE\_RECOVERY\_CONSISTENT\_RESCUE}
=
C^+
\land
\texttt{TRACE\_E\_FULL}
}
\]

Report:

\[
P(\texttt{TRACE\_E\_FULL}\mid C^+,B1)
\]

versus:

\[
P(\texttt{TRACE\_E\_FULL}\mid C^-,B1)
\]

descriptively.

If B1 rescue frequently coincides with `TRACE_E_FULL`, the paper may say:

> CoT rescue is accompanied by explicit recovery of the previously incomplete task-critical evidence, consistent with reasoning improving task-conditioned evidence recovery.

Do not claim hidden-state retrieval from visible text alone.

---

# 14. Branch A B1 subtype analysis

Within B1 preserve:

- `B1_EXPLICIT_WRONG`: 7 families
- `B1_UNRESOLVED_ONLY`: 4 families

Report exact CoT transitions separately.

Do not run significance tests on these tiny subgroups.

This determines whether rescue is limited to omission/underspecification or also corrects explicit evidence errors.

---

# 15. Branch A pathology analysis

Annotate C with the frozen R1–R5 guide:

- R1 severe repetition
- R2 reopening
- R3 nonconvergence
- R4 long advancing computation
- R5 terminal ambiguity

For B4 in particular, ask whether successful C responses coincide with resolution of prior native/oracle pathology.

Secondary question:

\[
\boxed{
\textbf{Does CoT rescue mixed failures by improving convergence even when evidence alone was insufficient?}
}
\]

---

# 16. Branch A decision rule

## `COT_RESCUE_INFORMATIVE`

Declare if either:

1. B1 has at least:
   \[
   \boxed{5}
   \]
   CoT rescues;

or

2. B4 has at least:
   \[
   \boxed{5}
   \]
   CoT rescues.

Interpretation:

> CoT rescue has enough yield to become part of Claim 1 and motivate a focused mechanistic follow-up.

## `COT_RESCUE_SPARSE`

If both B1 and B4 have fewer than 5 rescues.

Interpretation:

> Stage 12B-S remains the main Claim 1 result; prompted CoT is only a secondary comparison.

## `COT_TECHNICAL_BREAKDOWN`

Only if full-cohort C scoreability/input integrity is substantially worse than the validated sanity behavior.

Repetition alone is not technical breakdown.

---

# 17. Branch A outcome interpretation

## If B1 rescue dominates

Potential claim:

> **Explicit CoT prompting preferentially rescues native failures associated with incomplete demonstrated recovery of task-critical visual evidence.**

This connects directly to existing Claim 2:

\[
\text{reasoning context}
\rightarrow
\text{target-specific causal visual retrieval}
\]

## If B4 rescue dominates

Potential claim:

> **Explicit CoT also repairs mixed failures that are not solved by supplying correct evidence alone, indicating a downstream reasoning benefit.**

This connects more strongly to Claim 3.

## If both are substantial

Potential claim:

> **Inference-time reasoning repairs failures at multiple stages of the multimodal evidence-to-reasoning pipeline.**

## If rescue is sparse

Do not force CoT into the main headline.

---

# 18. Branch B — Separate Thinking completion validation

Branch B is technical only.

No task correctness is opened.

No rescue rate is estimated.

Its sole purpose is:

\[
\boxed{
\textbf{Is 40,960 tokens too short for the 4B Thinking MathVision regime,
or does nonconvergent completion persist even when the budget is doubled?}
}
\]

---

# 19. What remains frozen in Branch B

Use the exact Stage 12C Thinking condition except for one predeclared change:

\[
\boxed{
40{,}960
\rightarrow
81{,}920
}
\]

Everything else remains fixed.

Checkpoint:

\[
\texttt{1de27d8c51f12e819435303b9e84c4e25ba8401e}
\]

Generation:

- temperature = 1.0
- top-p = 0.95
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 0
- original image/question;
- no CoT suffix;
- same BF16/vLLM environment;
- same per-family seed policy.

Do not change temperature, penalties, prompt, or model.

This is a **cap-only technical intervention**.

---

# 20. Branch B phase 1 — Paired cap-extension diagnostic

Rerun the same sealed 12 Stage 12C sanity families at:

\[
\boxed{
81{,}920 \text{ max output tokens}
}
\]

Do not open correctness.

The purpose is paired diagnosis against the already preserved 40,960-token outputs.

Record:

- input validity;
- scoreability;
- pre-outcome truncation;
- normal stop;
- generated length;
- presence of closed `</think>`;
- presence of final-answer channel;
- R1–R5 pathologies.

For the two previously capped families, explicitly record whether the longer run:

- reaches a scoreable final;
- remains uncommitted;
- reaches the new cap.

---

# 21. Prefix diagnostic

Where deterministic runtime behavior permits, compare the 81,920-token rerun with the original 40,960-token run.

Record whether the new run's first 40,960 generated tokens are identical to the original output.

This is diagnostic only.

If prefixes match and the run later reaches a final:

> evidence supports a pure output-budget limitation for that trajectory.

If prefixes match and the run continues looping to 81,920:

> evidence supports persistent nonconvergence under this recipe.

If prefixes diverge:

> the paired completion diagnosis is less clean, but technical scoreability remains evaluable.

Do not require prefix identity as a validity gate.

---

# 22. Branch B phase-1 decision

## `CAP_EXTENSION_PROMISING`

Declare if:

- input-valid = 12/12;
- scoreable >= 11/12;
- pre-outcome truncation <= 1/12.

If met, freeze the 81,920-token recipe and proceed to a fresh untouched validation set.

## `THINKING_COMPLETION_UNSTABLE`

Declare if:

- scoreable < 11/12;
- or pre-outcome truncation >= 2/12.

Stop Branch B.

Do not test a third cap.

Do not search decoding parameters.

---

# 23. Branch B phase 2 — Fresh untouched validation

Only if phase 1 returns `CAP_EXTENSION_PROMISING`.

Before phase-1 generation, prospectively freeze a second 12-family validation set from the remaining 49 families.

Selection rule:

- deterministic SHA256 rank over:
  `stage12tr-fresh-validation-v1|family_id`
- use identity and answer type only;
- target 5 multiple-choice and 7 open-ended where possible;
- exclude the original 12 sanity families.

Do not generate this fresh set unless phase 1 passes.

Run the frozen 81,920-token Thinking recipe on these 12.

No correctness.

---

# 24. Branch B fresh-validation gate

Require:

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
\text{PRE\_OUTCOME\_TRUNCATION}\le1/12
}
\]

No repetition threshold.

If passed:

\[
\boxed{
\texttt{THINKING\_REGIME\_VALIDATED}
}
\]

If failed:

\[
\boxed{
\texttt{THINKING\_REGIME\_UNSTABLE}
}
\]

No further cap or decoding search in this stage.

---

# 25. Scientific meaning of Branch B outcomes

## If `THINKING_REGIME_VALIDATED`

The 81,920-token recipe may be used in a later, separately authorized Thinking rescue study.

It does **not** establish that Thinking is more accurate.

## If `THINKING_REGIME_UNSTABLE`

Do not force native Thinking into Claim 1.

Preserve the technical observation:

> long-form 4B Thinking completion is unstable on this MathVision cohort under the tested native sampled recipe, even with an extended output budget.

Do not interpret this as a negative task-performance result.

---

# 26. Why Branch B does not block Branch A

The scientific status is intentionally asymmetric:

\[
\boxed{
C:\text{validated and ready for science}
}
\]

\[
\boxed{
T:\text{technical completion regime unresolved}
}
\]

Therefore:

- Branch A should proceed regardless of Branch B outcome;
- Branch B must not delay CoT correctness scoring;
- a failed Thinking technical branch does not invalidate the CoT rescue result;
- Claim 1 can be completed without T.

---

# 27. Next scientific stage if Thinking validates

Only after:

\[
\texttt{THINKING\_REGIME\_VALIDATED}
\]

create a new **Stage 12T-S** plan.

That stage would run T scientifically on all 61 families and estimate:

\[
P(T^+\mid B1)
\]

\[
P(T^+\mid B4)
\]

plus paired C-vs-T transitions.

Do not perform those analyses in this plan.

---

# 28. Competing explanations distinguished

This split design separates several possibilities.

## Mechanism A — Explicit reasoning helps upstream evidence recovery

Evidence:

- high \(R_{C,B1}\);
- rescued B1 traces often become `TRACE_E_FULL`.

## Mechanism B — Explicit reasoning mainly helps downstream reasoning

Evidence:

- high \(R_{C,B4}\);
- rescue accompanied by pathology resolution rather than clear evidence-state change.

## Mechanism C — CoT gives little benefit

Evidence:

- low rescue in B1 and B4.

Then Stage 12B-S remains the main Claim 1.

## Technical explanation T1 — Thinking was cap-limited

Evidence:

- 40,960 capped;
- 81,920 completes;
- especially convincing with prefix continuity.

## Technical explanation T2 — Thinking is persistently nonconvergent

Evidence:

- long runs remain uncommitted or hit 81,920;
- repeated reopening/nonconvergence persists.

---

# 29. Null discipline

A sparse CoT rescue result does **not** invalidate:

- the Stage 12B-S bottleneck profile;
- the existing causal visual-retrieval mechanism;
- the visual-to-text lifecycle.

It means only:

> explicit CoT prompting does not substantially rescue these frozen native failure strata in this cohort.

A failed Thinking completion validation does **not** establish:

- Thinking is less accurate;
- Thinking cannot rescue B1/B4;
- Thinking reasoning is intrinsically defective.

It establishes only that the tested long-form sampled completion regime is not sufficiently scoreable for the planned scientific comparison.

---

# 30. Compute budget

## Branch A

New C calls:

\[
\boxed{
49
}
\]

Target:

\[
\boxed{
<3.5 \text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
5 \text{ GPU-hours}
}
\]

## Branch B phase 1

12 Thinking calls at max 81,920 tokens.

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

## Branch B phase 2

Conditional 12 fresh Thinking calls.

Same target/hard budget.

Do not launch a full 61-family T study in this stage.

---

# 31. Required Branch A artifacts

Produce:

1. `stage12cr_cot_scientific_spec.md`
2. `stage12cr_cot_manifest.json`
3. `stage12cr_cot_integrity.parquet`
4. `stage12cr_cot_results.parquet`
5. `stage12cr_cot_scoring_blind.parquet`
6. `stage12cr_cot_second_review.json`
7. `stage12cr_cot_trace_evidence_states.parquet`
8. `stage12cr_cot_pathology.parquet`
9. `stage12cr_cot_primary_inference.json`
10. `stage12cr_cot_decision.json`
11. `stage12cr_cot_resource_accounting.json`
12. `stage12cr_cot_summary.md`

---

# 32. Required Branch B artifacts

Produce:

1. `stage12tr_completion_spec.md`
2. `stage12tr_same12_manifest.json`
3. `stage12tr_fresh12_manifest.json`
4. `stage12tr_same12_results.parquet`
5. `stage12tr_prefix_diagnostics.parquet`
6. `stage12tr_same12_decision.json`
7. conditional `stage12tr_fresh12_results.parquet`
8. conditional `stage12tr_fresh12_decision.json`
9. `stage12tr_pathology_labels.parquet`
10. `stage12tr_resource_accounting.json`
11. `stage12tr_summary.md`

Preserve all original Stage 12C artifacts unchanged.

---

# 33. Required figures for Branch A

## Figure A1 — Frozen bottleneck map with CoT rescue overlay

Show B1–B4 native failure counts and C rescue counts.

## Figure A2 — B1 vs B4 CoT rescue

Show:

\[
R_{C,B1}
\quad\text{vs}\quad
R_{C,B4}
\]

with intervals.

## Figure A3 — Native-to-CoT paired transitions

Show:

- rescue;
- regression;
- both correct;
- both wrong.

## Figure A4 — B1 visible evidence state

Split rescued vs non-rescued B1 traces across:

- FULL;
- PARTIAL;
- WRONG/CONFLICTING;
- NOT_EXTERNALIZED.

## Figure A5 — B4 pathology resolution

Show whether CoT success coincides with convergence improvements.

No scientific figure is required for Branch B beyond a compact technical completion table.

---

# 34. Exactly one scientific recommendation at completion

Use the Branch A result for the paper-facing recommendation.

## If B1 rescue dominates

Recommend:

> Run a focused causal retrieval comparison on B1 native failures rescued by CoT.

## If B4 rescue dominates

Recommend:

> Run a CoT Equal-Evidence follow-up on rescued B4 cases to isolate downstream benefit.

## If both are substantial

Recommend:

> Follow both an upstream B1 retrieval branch and a downstream B4 equal-evidence branch.

## If CoT rescue is sparse

Recommend:

> Keep Stage 12B-S as the main Claim 1 and stop the CoT rescue branch.

Branch B produces only a technical authorization decision for a future T study.

Do not combine the two recommendations.

---

# 35. Final decision targets

## Branch A

\[
\boxed{
\textbf{Does explicit CoT prompting rescue the native failure states already identified in Stage 12B-S?}
}
\]

## Branch B

\[
\boxed{
\textbf{Is the 4B Thinking MathVision regime merely output-budget limited,
or does completion instability persist after a single cap-only extension?}
}
\]

The two questions must remain independent.
