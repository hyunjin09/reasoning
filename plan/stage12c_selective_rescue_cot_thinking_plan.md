# Stage 12C — Selective Rescue of Native VLM Failure Bottlenecks by Prompted CoT and Native Thinking

## 0. Objective

Starting from the **sealed Stage 12B-S native failure map**, test:

\[
\boxed{\textbf{Which native VLM failure states are rescued by prompted CoT, and which are additionally rescued by the native Thinking variant?}}
\]

Stage 12C does **not** re-estimate where native failures occur. Stage 12B-S already established that profile.

The new question is whether extra inference-time reasoning selectively repairs failures associated with:

1. incomplete demonstrated recovery of task-critical visual evidence, or
2. mixed upstream plus downstream difficulty.

---

# 1. Motivation from Stage 12B-S

Among the 26 native failures with complete \(E/N/O\) profiles:

\[
B1=E^-O^+=11/26=42.3\%
\]

\[
B2=E^+O^+=1/26=3.8\%
\]

\[
B3=E^+O^-=3/26=11.5\%
\]

\[
B4=E^-O^-=11/26=42.3\%
\]

and:

\[
\boxed{P(O^+\mid N^-)=12/26=46.2\%}
\]

Correct task-critical evidence supplied as text therefore rescued nearly half of complete-profile native failures.

The important qualitative result was **not** a dominant multimodal Lost-Keys state. Clearly recoverable-but-native-unused evidence \(B2\) contained only one family.

Instead, the native profile was dominated by:

- **B1** — incomplete demonstrated task-critical evidence recovery, but oracle-solvable;
- **B4** — incomplete demonstrated evidence recovery plus failure even after correct evidence is supplied.

So the next question becomes:

\[
\boxed{\textbf{Can CoT or Thinking compensate for incomplete visual-evidence recovery, and can they also repair mixed failures with a downstream component?}}
\]

---

# 2. Paper role

The intended paper structure becomes:

## Claim 1A — Where does the VLM fail?

Stage 12B-S:

> A substantial fraction of native failures disappear when correct task-critical visual evidence is supplied, while clearly recoverable-but-unused evidence is rare in this cohort. Incomplete evidence recovery, often compounded by downstream reasoning failure, is a major bottleneck.

## Claim 1B — What does additional reasoning rescue?

Stage 12C:

> Test whether prompted CoT and native Thinking selectively rescue B1, B4, or neither.

## Claim 2 — Why can reasoning change evidence access?

Existing causal result:

\[
\boxed{\text{recent reasoning context}\rightarrow\text{target-specific causal visual retrieval}}
\]

## Claim 3 — What happens after evidence is retrieved?

Existing lifecycle:

\[
\boxed{
\text{retrieval}
\rightarrow
\text{Value-rich transfer}
\rightarrow
\text{local K/V + residual}
\rightarrow
\text{causal generated text}
\rightarrow
\text{text-sufficient reasoning}
}
\]

Stage 12C is the bridge between the behavioral failure map and the existing mechanistic claims.

---

# 3. Frozen cohort and labels

Use exactly the same:

\[
\boxed{61\text{ independent MathVision families}}
\]

from Stage 12B-S.

Freeze and preserve:

- all 157 \(E^*\) facts;
- original images/questions;
- source answers;
- E/N/O outputs;
- E/N/O correctness;
- B1–B4 labels;
- technical-unresolved labels;
- pathology labels;
- all Stage 12B-S scoring decisions.

No Stage 12B-S label may change after C/T generation.

---

# 4. Primary strata

Because the observed category sizes are highly unequal, the inferential emphasis is frozen prospectively.

## Primary stratum 1 — B1

\[
\boxed{B1=E^-O^+}
\]

Observed size:

\[
\boxed{n=11}
\]

Interpretation:

> native failure with incomplete demonstrated recovery of at least one required evidence atom, but success when correct \(E^*\) is supplied.

This is the main **upstream-rescuable** stratum.

## Primary stratum 2 — B4

\[
\boxed{B4=E^-O^-}
\]

Observed size:

\[
\boxed{n=11}
\]

Interpretation:

> incomplete demonstrated evidence recovery plus failure even after correct \(E^*\) is supplied under Native Instruct.

This is the main **mixed upstream/downstream** stratum.

## Descriptive-only strata

- \(B2=E^+O^+\), \(n=1\)
- \(B3=E^+O^-\), \(n=3\)

Report exact transitions only. Do not make inferential claims from B2/B3.

---

# 5. Important B1 qualification

Within B1:

- 7/11 have at least one explicitly incorrect evidence atom;
- 4/11 are \(E^-\) because evidence was unresolved or underspecified without an explicitly incorrect atom.

Therefore the primary wording is:

\[
\boxed{\textbf{incomplete demonstrated recovery of task-critical visual evidence}}
\]

not “11 visual misreads.”

Secondary descriptive subtypes:

- `B1_EXPLICIT_WRONG` \(n=7\)
- `B1_UNRESOLVED_ONLY` \(n=4\)

---

# 6. New conditions

Run two new task-solving conditions on **all 61 families**:

\[
\boxed{C=\text{Prompted CoT on Qwen3-VL-4B-Instruct}}
\]

\[
\boxed{T=\text{Qwen3-VL-4B-Thinking}}
\]

Running all 61, not only native failures, allows:

- overall paired accuracy estimates;
- native-failure rescue;
- native-success regressions;
- unbiased paired transition tables.

---

# 7. Condition C — Prompted CoT

Use the **same Qwen3-VL-4B-Instruct checkpoint** as native N.

Input:

- exact original image;
- exact original question;
- same image preprocessing.

Append only:

> ` Let's think step by step.`

Do not add:

- a new system prompt;
- answer-only constraints;
- custom final-answer instructions;
- other reasoning scaffolds.

Generation:

- temperature = 0.7
- top-p = 0.8
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 1.5
- max output = 32768

This is the clean same-checkpoint prompt intervention.

---

# 8. Condition T — Native Thinking

Use the exact Qwen3-VL-4B-Thinking checkpoint and recipe previously validated in the project.

Before generation:

1. recover the exact pinned checkpoint revision from the prior 4B Thinking experiment;
2. record it in the manifest;
3. hash the manifest;
4. do not substitute another revision after observing outputs.

Use:

- exact original image;
- exact original question;
- no added CoT suffix.

Default previously validated Thinking recipe:

- temperature = 1.0
- top-p = 0.95
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 0
- max output = 40960

If the historical 4B Thinking artifact specifies a different exact validated recipe, use that exact recipe and document it **before generation**.

---

# 9. Interpretation discipline

## N vs C

Same checkpoint.

Supported causal language:

> explicit CoT prompting changes task performance on the same Instruct model.

## C vs T

Different checkpoints / variants.

Use:

> the native Thinking variant rescues additional cases beyond prompted CoT.

Do **not** say:

> turning on Thinking caused the difference.

## N vs T

Also a model-variant comparison.

Use descriptive paired language only.

---

# 10. Pathology-aware validity

Reuse the Stage 12B-R rule:

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

Do not exclude a response merely for:

- severe repetition;
- reopening;
- nonconvergence;
- long advancing computation.

Those remain scientific behavior labels.

---

# 11. Minimal technical sanity check

Before the full run, deterministically freeze 12 families using identity only.

Do not select by B1–B4 class.

Run C and T.

Do not open correctness.

For each arm require:

- `INPUT_VALID = 12/12`
- `SCOREABLE >= 10/12`
- `TRUNCATED_BEFORE_OUTCOME <= 1/12`

No repetition threshold.

If either arm fails badly:

\[
\boxed{\texttt{TECHNICAL\_STOP}}
\]

Do not search prompt variants.

If both pass, continue with the remaining 49 families under the identical frozen protocol.

The 12 sanity cases are part of the 61 and must not be regenerated after passing.

---

# 12. Blinded correctness scoring

Score C and T independently.

Each scoring packet contains only:

- family ID;
- original question;
- source answer;
- that arm's response.

Do not expose:

- N result;
- E result;
- O result;
- B1–B4 label;
- the other new arm;
- rescue status.

Use the same frozen MathVision scoring policy as Stage 12B-S.

Preserve:

- `CORRECT`
- `INCORRECT`
- `UNSCOREABLE_TECHNICAL`

Use the same ambiguity-triggered second-review rule and deterministic 20% audit of otherwise unambiguous cases.

---

# 13. Primary endpoints

## P1 — CoT rescue of B1

\[
\boxed{
R_{C,B1}=P(C^+\mid B1)
}
\]

## P2 — Thinking rescue of B1

\[
\boxed{
R_{T,B1}=P(T^+\mid B1)
}
\]

## P3 — CoT rescue of B4

\[
\boxed{
R_{C,B4}=P(C^+\mid B4)
}
\]

## P4 — Thinking rescue of B4

\[
\boxed{
R_{T,B4}=P(T^+\mid B4)
}
\]

These four quantities are the primary result.

---

# 14. Rescue selectivity

Define:

\[
\boxed{
\Delta_C=R_{C,B1}-R_{C,B4}
}
\]

and:

\[
\boxed{
\Delta_T=R_{T,B1}-R_{T,B4}
}
\]

Interpretation:

- positive: mode preferentially rescues upstream-rescuable B1;
- near zero: similar rescue across B1/B4;
- negative: mode preferentially rescues mixed B4.

Because \(n=11\) per primary stratum, report exact counts and uncertainty without overclaiming small differences.

---

# 15. Thinking-only vs CoT-only rescue

Within each \(B_j\), report:

\[
N_{T\text{-only},j}
=
\#\{T^+,C^-\mid B_j\}
\]

\[
N_{C\text{-only},j}
=
\#\{C^+,T^-\mid B_j\}
\]

and:

\[
\boxed{
\Delta_{T-C,j}
=
P(T^+,C^-\mid B_j)
-
P(C^+,T^-\mid B_j)
}
\]

This is a paired **variant-comparison** quantity, not a causal Thinking-on effect.

---

# 16. Overall performance — secondary

Across all scientifically scoreable families report:

\[
Acc_N,\quad Acc_C,\quad Acc_T
\]

with paired transitions.

For N vs C:

- \(N^-C^+\): CoT rescues
- \(N^+C^-\): CoT regressions

For C vs T:

- \(C^-T^+\): Thinking-only successes
- \(C^+T^-\): CoT-only successes

Overall accuracy is secondary.

The headline remains **conditional rescue by frozen native failure type**.

---

# 17. Visible evidence-state annotation

Final-answer rescue alone does not show whether visual evidence recovery itself improved.

Therefore annotate C and T visible reasoning traces for the 26 native failures with complete Stage 12B-S profiles.

Annotation packets contain only:

- family ID;
- frozen \(E^*\);
- one C or T trace.

Do not expose:

- task correctness;
- N/E/O outcomes;
- B1–B4 label;
- paired-arm trace.

Labels:

## `TRACE_E_FULL`

All required \(E^*\) facts are explicitly and correctly externalized before the final answer.

## `TRACE_E_PARTIAL`

At least one required fact is correct, but the full set is not demonstrated.

## `TRACE_E_WRONG_OR_CONFLICTING`

At least one required evidence atom is explicitly wrong or later contradicted.

## `TRACE_E_NOT_EXTERNALIZED`

The trace does not explicitly state enough of \(E^*\) to judge recovery.

Important:

\[
\boxed{
\texttt{TRACE\_E\_NOT\_EXTERNALIZED}
\neq
\text{internal evidence absence}
}
\]

This is visible-trace evidence only.

---

# 18. Evidence-recovery-consistent rescue

For B1 define:

\[
\boxed{
\texttt{EVIDENCE\_RECOVERY\_CONSISTENT\_RESCUE}
=
M^+
\land
\texttt{TRACE\_E\_FULL}
}
\]

for \(M\in\{C,T\}\).

Report:

\[
P(\texttt{TRACE\_E\_FULL}\mid M^+,B1)
\]

and:

\[
P(\texttt{TRACE\_E\_FULL}\mid M^-,B1)
\]

descriptively.

If B1 rescue frequently co-occurs with `TRACE_E_FULL`, that supports the interpretation that additional reasoning is associated with recovery of the previously incomplete task-critical evidence.

It does **not** prove hidden-state retrieval.

---

# 19. B1 explicit-wrong vs unresolved-only

Secondary only.

Compare exact rescue transitions for:

- `B1_EXPLICIT_WRONG` \(n=7\)
- `B1_UNRESOLVED_ONLY` \(n=4\)

for C and T.

This matters because rescue concentrated only in unresolved-only cases would be weaker evidence for correction of genuine visual misinterpretation.

No significance testing on these tiny cells.

---

# 20. Pathology transitions

Reuse:

- R1 `SEVERE_REPETITION`
- R2 `REOPEN_AFTER_PROVISIONAL_ANSWER`
- R3 `NONCONVERGENT_REASONING`
- R4 `LONG_ADVANCING_COMPUTATION`
- R5 `TERMINAL_AMBIGUITY`

For B4, ask whether C/T rescue coincides with resolution of native/oracle reasoning pathology.

Examples:

\[
\text{loop/reopen}
\rightarrow
\text{convergent success}
\]

\[
\text{nonconvergence}
\rightarrow
\text{stable solution}
\]

This is secondary explanatory evidence.

---

# 21. Main outcome patterns

## Outcome A — B1 strongly rescued, B4 weakly rescued

Interpretation:

> additional reasoning primarily compensates for failures of task-critical visual evidence recovery.

If rescued B1 traces often become `TRACE_E_FULL`, this forms a strong behavioral bridge to Claim 2.

## Outcome B — Both B1 and B4 strongly rescued

Interpretation:

> additional reasoning helps at multiple stages: visual evidence recovery and downstream reasoning.

This supports the strongest stage-structured Claim 1.

## Outcome C — B4 rescued more than B1

Interpretation:

> additional reasoning primarily improves downstream integration/convergence rather than evidence recovery.

This shifts emphasis toward Claim 3.

## Outcome D — Many T-only rescues

Interpretation:

> the native Thinking variant recovers additional failures beyond prompted CoT.

Do not attribute the difference solely to “turning on thinking.”

## Outcome E — Little rescue

Interpretation:

> Stage 12B-S remains the main Claim 1 result; CoT/Thinking should remain secondary.

---

# 22. Statistical inference

Independent unit:

\[
\boxed{\text{problem/image family}}
\]

For P1–P4 report:

- numerator / denominator;
- proportion;
- Wilson 95% interval.

For \(\Delta_C,\Delta_T\):

- family-level bootstrap;
- 4000 draws;
- frozen seed.

For N vs C across all scoreable families:

- exact discordant counts;
- exact McNemar test may be reported as a secondary same-checkpoint comparison.

For C vs T:

- paired discordant counts and intervals;
- no causal variant interpretation.

The stage is primarily estimation and mechanism discrimination, not a large multiplicity-heavy testing program.

---

# 23. Decision rule

## `RESCUE_INFORMATIVE`

Declare if at least one is true:

1. B1 has at least:
   \[
   \boxed{5}
   \]
   rescues under C or T;

2. B4 has at least:
   \[
   \boxed{5}
   \]
   rescues under C or T;

3. B1+B4 contain at least:
   \[
   \boxed{4}
   \]
   Thinking-only rescues;

and C/T remain technically scoreable.

## `RESCUE_SPARSE`

If none hold.

Interpretation:

> selective rescue is too sparse to support a strong CoT/Thinking extension.

Keep Stage 12B-S as the main Claim 1 result.

## `TECHNICAL_STOP`

Only for broad C/T scoreability or input-integrity failure.

Repetition alone is not a technical stop.

---

# 24. Claims allowed under positive outcomes

If B1 rescue dominates:

> **Additional inference-time reasoning preferentially rescues native failures associated with incomplete demonstrated recovery of task-critical visual evidence.**

If B1 rescue co-occurs with `TRACE_E_FULL`:

> **Many rescued upstream failures are accompanied by correct externalization of previously incomplete task-critical evidence, consistent with reasoning improving task-conditioned evidence recovery.**

If B4 rescue is substantial:

> **Reasoning also rescues mixed failures that persist when correct visual evidence is supplied under Native Instruct, indicating an additional downstream benefit.**

If T adds rescue beyond C:

> **The native Thinking variant recovers additional failures beyond prompted CoT.**

---

# 25. Claims NOT allowed

Do not claim:

- visible trace evidence proves hidden internal retrieval;
- C/T rescue proves a specific head or KV pathway caused improvement;
- T vs C differences are caused solely by native Thinking computation;
- B1 is equivalent to proven visual misreading;
- the 61-family cohort establishes benchmark-wide prevalence;
- all modern VLMs share the same failure distribution.

---

# 26. Next stage under each outcome

## If B1 rescue is strong

Run a focused mechanistic comparison on frozen B1 cases:

\[
\boxed{
\textbf{Do rescued CoT/Thinking trajectories show stronger or retargeted causal retrieval of the missing }E^*\textbf{?}
}
\]

This directly connects Claim 1 to Claim 2.

## If B4 rescue is strong

Run Equal-Evidence Oracles under C and T on rescued B4 cases:

\[
\boxed{
\textbf{Does the C/T advantage persist after visual evidence is equalized?}
}
\]

This isolates downstream benefit and connects Claim 1 to Claim 3.

## If Thinking-only rescue is strong

Focus on C-failed / T-success cases and compare:

- visible evidence state;
- target-specific retrieval;
- downstream convergence/carrier behavior.

Do not infer checkpoint-causal effects without further controls.

## If rescue is sparse

Stop the rescue branch.

Center Claim 1 on Stage 12B-S:

> correct task-critical visual evidence repairs nearly half of complete native failures, clearly recoverable-but-unused evidence is rare, and mixed failures remain common.

---

# 27. Generalization requirement

Stage 12C uses the same developmental 61-family cohort.

Even a strong selective-rescue result is not yet a population-wide prevalence claim.

After the mechanism is clear, confirm the key pattern on a fresh held-out \(E^*\)-annotated cohort.

Do not expand the cohort before learning whether B1/B4 rescue is present.

---

# 28. Required figures

## Figure 1 — Native failure map with rescue overlay

Stage 12B-S B1–B4 composition plus:

- C rescue count;
- T rescue count.

Emphasize B1/B4.

Mark B2/B3 descriptive-only.

## Figure 2 — Rescue rates in B1 vs B4

Show:

\[
R_{C,B1},\quad R_{T,B1},\quad R_{C,B4},\quad R_{T,B4}
\]

with intervals.

## Figure 3 — CoT-only vs Thinking-only transitions

Within B1/B4:

- both fail;
- C-only;
- T-only;
- both succeed.

## Figure 4 — Visible evidence state in B1

Split C/T traces by:

- TRACE_E_FULL;
- PARTIAL;
- WRONG/CONFLICTING;
- NOT_EXTERNALIZED;

and rescued vs not rescued.

## Figure 5 — Pathology resolution in B4

Show whether C/T:

- resolve;
- preserve;
- change;
- remain unscoreable.

---

# 29. Required artifacts

Produce:

1. `stage12c_selective_rescue_spec.md`
2. `stage12c_frozen_bottleneck_manifest.json`
3. `stage12c_cot_manifest.json`
4. `stage12c_thinking_manifest.json`
5. `stage12c_technical_sanity.json`
6. `stage12c_cot_results.parquet`
7. `stage12c_thinking_results.parquet`
8. `stage12c_cot_scoring_blind.parquet`
9. `stage12c_thinking_scoring_blind.parquet`
10. `stage12c_scoring_review_log.json`
11. `stage12c_rescue_transitions.parquet`
12. `stage12c_trace_evidence_states.parquet`
13. `stage12c_pathology_transitions.parquet`
14. `stage12c_primary_inference.json`
15. `stage12c_rescue_decision.json`
16. `stage12c_resource_accounting.json`
17. `stage12c_summary.md`

Preserve all Stage 12B-S artifacts unchanged.

---

# 30. Compute budget

Primary new generations:

\[
\boxed{61\times2=122}
\]

logical calls.

The 12-family sanity subset is part of those 122 and must not be regenerated after passing.

Target:

\[
\boxed{<6\text{ GPU-hours}}
\]

Hard stop:

\[
\boxed{8\text{ GPU-hours}}
\]

unless explicitly approved.

Do not run in this stage:

- new E probes;
- new Native N runs;
- new Stage 12B-S Oracle O runs;
- C/T Equal-Evidence Oracles;
- hidden-state mechanistic interventions;
- new benchmark mining.

---

# 31. Exactly one recommendation at completion

## If B1 rescue dominates

Recommend:

> Run a focused causal visual-retrieval comparison on frozen B1 failures rescued by CoT and/or Thinking.

## If B4 rescue dominates

Recommend:

> Run C/T Equal-Evidence Oracles on rescued B4 cases to localize the remaining gain downstream of visual evidence acquisition.

## If both are substantial

Recommend:

> Split the mechanistic follow-up into upstream B1 retrieval analysis and downstream B4 equal-evidence analysis.

## If rescue is sparse

Recommend:

> Stop the rescue branch and retain Stage 12B-S failure localization as the main Claim 1 result.

Do not launch automatically.

---

# 32. Final decision target

Stage 12C exists to answer:

\[
\boxed{
\textbf{Given the frozen native failure map, does additional inference-time reasoning selectively rescue failures associated with incomplete visual-evidence recovery, mixed upstream/downstream difficulty, or both?}
}
\]

The result determines whether CoT/Thinking becomes part of the main Claim 1 story or remains a secondary comparison.
