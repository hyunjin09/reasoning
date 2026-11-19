# Stage 12T-S — Native Thinking Rescue and Visual-Evidence Recovery

## 0. Objective

Test whether one source of the Qwen3-VL-4B-Thinking variant's advantage is that its reasoning process more successfully **recovers task-critical visual evidence** that Native Instruct and generic prompted CoT fail to recover.

Primary question:

\[
\boxed{
\textbf{Does native Thinking selectively rescue B1 failures, and are those rescues accompanied by correct recovery of }E^*\textbf{ in the Thinking trace?}
}
\]

The strongest target pattern is:

\[
\boxed{
B1 \land C^- \land T^+ \land \texttt{TRACE\_E\_FULL}^{T}
}
\]

This would support the interpretation that **improved task-conditioned visual-evidence recovery is one contributor to the Thinking variant's advantage**.

---

# 1. Why this stage matters

Stage 12B-S established the native failure map among 26 complete-profile failures:

\[
B1=E^-O^+=11,\quad
B2=E^+O^+=1,\quad
B3=E^+O^-=3,\quad
B4=E^-O^-=11.
\]

Correct \(E^*\) supplied as text rescued:

\[
\boxed{
12/26=46.2\%
}
\]

of complete-profile native failures.

The dominant result was not a large recoverable-but-unused B2 state. Instead, failures were concentrated in:

- **B1**: incomplete demonstrated recovery of task-critical visual evidence, but oracle-solvable;
- **B4**: incomplete demonstrated evidence recovery plus failure even after correct evidence is supplied.

Stage 12C-R then showed that same-checkpoint prompted CoT did not repair these bottlenecks:

\[
R_{C,B1}=1/10=10\%
\]

\[
R_{C,B4}=0/11=0\%
\]

and the sole B1 CoT rescue still had:

\[
\texttt{TRACE\_E\_WRONG\_OR\_CONFLICTING}.
\]

Thus:

\[
\boxed{
\textbf{generic explicit CoT did not reliably recover the missing task-critical evidence}
}
\]

in this cohort.

Stage 12T-R separately validated the 4B Thinking completion regime at:

\[
\boxed{
81{,}920 \text{ max output tokens}
}
\]

without opening correctness.

This makes the following scientific test identifiable:

\[
\boxed{
\textbf{Does native Thinking succeed where explicit CoT fails, specifically by recovering the missing visual evidence during reasoning?}
}
\]

---

# 2. Candidate paper claim

Strong positive form, only if supported:

> **One contributor to the native Thinking variant's advantage is improved task-conditioned recovery of visual evidence during reasoning: Thinking rescues failures associated with incomplete evidence recovery that prompted CoT does not, and the rescued traces explicitly recover the previously missing task-critical facts.**

Use **one contributor**, not **the reason**, because downstream gains may coexist.

Negative outcome is also informative:

> **The dominant visual-evidence-recovery bottleneck is not substantially repaired by either generic prompted CoT or native Thinking in this cohort.**

---

# 3. Causal-status discipline

The comparisons have different meanings.

## N vs C

Same Instruct checkpoint; prompt-level intervention.

## C vs T

Different checkpoints / model variants.

Therefore:

\[
\boxed{
\textbf{T vs C is not a causal “Thinking on/off” comparison.}
}
\]

Allowed:

> the native Thinking variant rescues additional failures beyond prompted CoT.

Not allowed:

> turning on Thinking caused the rescue.

Likewise:

\[
\texttt{TRACE\_E\_FULL}
\]

is visible-trace evidence, not proof of hidden-state retrieval.

---

# 4. Frozen cohort and labels

Use exactly the same:

\[
\boxed{
61 \text{ independent MathVision families}
}
\]

Preserve:

- 157 frozen \(E^*\) facts;
- original images/questions;
- source answers;
- Stage 12B-S E/N/O generations and labels;
- B1–B4 assignments;
- B1 explicit-wrong vs unresolved-only subtypes;
- Stage 12C-R CoT outputs/correctness;
- CoT visible-evidence states;
- Native/Oracle/CoT pathology labels;
- all technical-unresolved decisions.

No prior label may be changed after Thinking correctness is opened.

---

# 5. Primary strata

## B1 — primary visual-evidence-recovery stratum

\[
\boxed{
B1=E^-O^+,\quad n=11
}
\]

Interpretation:

> Native Instruct failed, demonstrated recovery of at least one required evidence atom was incomplete, but correct \(E^*\) made the task solvable.

Primary wording:

\[
\boxed{
\textbf{incomplete demonstrated recovery of task-critical visual evidence}
}
\]

Subtypes:

- `B1_EXPLICIT_WRONG`: 7
- `B1_UNRESOLVED_ONLY`: 4

## B4 — primary mixed stratum

\[
\boxed{
B4=E^-O^-,\quad n=11
}
\]

Interpretation:

> incomplete demonstrated evidence recovery plus failure even after correct \(E^*\) is supplied to Native Instruct.

## B2 / B3

- B2: \(n=1\)
- B3: \(n=3\)

Descriptive only.

---

# 6. Thinking condition

Use:

\[
\boxed{
T=\textbf{Qwen3-VL-4B-Thinking}
}
\]

Pinned revision:

\[
\boxed{
\texttt{1de27d8c51f12e819435303b9e84c4e25ba8401e}
}
\]

Input:

- exact original image;
- exact original question;
- no added CoT suffix;
- no answer-only instruction.

Generation:

- temperature = 1.0
- top-p = 0.95
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 0
- max output tokens = 81,920
- same BF16/vLLM environment
- same image preprocessing
- same frozen per-family seed policy

No decoding search, retries, or third cap.

---

# 7. Reuse prior validated Thinking outputs

Stage 12T-R already generated the exact 81,920-token T condition on:

- 12 same12 technical families;
- 12 fresh validation families.

Their correctness was never opened.

Therefore:

\[
\boxed{
\textbf{reuse all 24 preserved outputs}
}
\]

Do not regenerate them.

Generate T only for the remaining:

\[
\boxed{
37 \text{ families}
}
\]

New logical calls:

\[
\boxed{
37
}
\]

---

# 8. Technical validity

Reuse:

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

Do not exclude merely for:

- severe repetition;
- reopening;
- nonconvergence;
- long advancing computation.

A capped response with a unique surviving task answer before the cap may remain scoreable under the frozen rule.

Pre-outcome truncation is technical missingness, not an incorrect answer.

---

# 9. Pre-correctness integrity pass

Before opening T correctness:

1. generate all remaining 37 outputs;
2. verify all 61 inputs;
3. classify scoreability;
4. classify pre-outcome truncation;
5. classify cap-after-outcome;
6. freeze R1–R5 pathology labels.

Only after this is sealed may gold correctness be opened.

---

# 10. Blinded Thinking scoring

Create a T-only scoring packet containing:

- family ID;
- original question;
- source answer;
- T response.

Do not expose:

- N/C correctness;
- E/O outcomes;
- B1–B4 class;
- CoT trace;
- Thinking evidence-state annotation;
- rescue status.

Use the same frozen MathVision equivalence policy.

Labels:

- `CORRECT`
- `INCORRECT`
- `UNSCOREABLE_TECHNICAL`

Use the same ambiguity-triggered second review and deterministic 20% audit.

---

# 11. T-P1 — Thinking rescue of B1

Among scoreable B1 families:

\[
\boxed{
R_{T,B1}=P(T^+\mid B1)
}
\]

Report:

- numerator;
- scoreable denominator;
- frozen total \(11\);
- technical missingness;
- Wilson 95% interval;
- missingness identification bounds.

This is the central endpoint.

---

# 12. T-P2 — Thinking rescue of B4

\[
\boxed{
R_{T,B4}=P(T^+\mid B4)
}
\]

Substantial B4 rescue would show that the Thinking advantage cannot be explained only by recovering missing visual facts.

---

# 13. T-P3 — Rescue selectivity

\[
\boxed{
\Delta_T
=
R_{T,B1}-R_{T,B4}
}
\]

Use 4,000 family-level bootstrap draws with a frozen seed.

Interpretation:

- positive: rescue relatively concentrated in B1;
- near zero: comparable B1/B4 rescue;
- negative: rescue more concentrated in B4.

Emphasize estimation; \(n=11\) per primary stratum.

---

# 14. T-P4 — Thinking beyond prompted CoT

Within jointly scoreable B1/B4 families report:

\[
C^-T^+,\quad
C^+T^-,\quad
C^+T^+,\quad
C^-T^-.
\]

Primary count:

\[
\boxed{
N_{T\text{-only},B1}
=
\#\{C^-T^+\mid B1\}
}
\]

Secondary:

\[
N_{T\text{-only},B4}
=
\#\{C^-T^+\mid B4\}.
\]

This asks whether native Thinking rescues failures that generic explicit CoT did not.

---

# 15. Visible Thinking evidence-state annotation

Annotate the Thinking trace for all 26 complete-profile native failures.

Packets contain only:

- family ID;
- frozen \(E^*\);
- Thinking trace.

Do not expose:

- correctness;
- B1–B4;
- N/C outcomes;
- E/O outcomes;
- CoT evidence-state label.

Use:

### `TRACE_E_FULL`
All required \(E^*\) facts are explicitly and correctly externalized before the final answer.

### `TRACE_E_PARTIAL`
At least one required fact is correct, but the full set is not demonstrated.

### `TRACE_E_WRONG_OR_CONFLICTING`
At least one required evidence fact is explicitly wrong or later contradicted.

### `TRACE_E_NOT_EXTERNALIZED`
The trace does not explicitly state enough \(E^*\) to judge full recovery.

Important:

\[
\boxed{
\texttt{TRACE\_E\_NOT\_EXTERNALIZED}
\neq
\text{internal evidence absence}
}
\]

---

# 16. Central evidence-linked rescue endpoint

For B1:

\[
\boxed{
\texttt{T\_EVIDENCE\_LINKED\_RESCUE}
=
T^+
\land
\texttt{TRACE\_E\_FULL}^{T}
}
\]

Report:

\[
P(\texttt{TRACE\_E\_FULL}^{T}\mid T^+,B1)
\]

and:

\[
P(\texttt{TRACE\_E\_FULL}^{T}\mid T^-,B1)
\]

descriptively.

This is the key behavioral evidence for:

> Thinking succeeds partly because its reasoning trajectory more successfully recovers the task-critical visual evidence.

---

# 17. Strongest cross-mode signature

Count:

\[
\boxed{
B1
\land
C^-
\land
T^+
\land
\texttt{TRACE\_E\_FULL}^{T}
}
\]

Call these:

\[
\boxed{
\texttt{THINKING\_ONLY\_EVIDENCE\_RECOVERY\_RESCUES}
}
\]

These are the most informative cases.

For each preserve:

- frozen \(E^*\);
- Native outcome;
- CoT outcome;
- Thinking outcome;
- CoT trace evidence state;
- Thinking trace evidence state.

Do not run mechanistic interventions yet.

---

# 18. CoT-to-Thinking evidence-state transitions

Stage 12C-R found no full-evidence B1 CoT rescue.

For jointly annotated B1 families compare:

\[
\text{CoT evidence state}
\rightarrow
\text{Thinking evidence state}.
\]

The key descriptive transition is:

\[
\boxed{
\texttt{C: WRONG/CONFLICTING}
\rightarrow
\texttt{T: FULL}
}
\]

especially when:

\[
C^-\rightarrow T^+.
\]

Because checkpoints differ, interpret this as association with the Thinking variant, not a pure reasoning-mode causal effect.

---

# 19. B1 explicit-wrong vs unresolved-only

Report exact Thinking rescue separately for:

## `B1_EXPLICIT_WRONG` \(n=7\)

Especially informative target:

\[
\boxed{
\texttt{B1\_EXPLICIT\_WRONG}
\land
C^-
\land
T^+
\land
\texttt{TRACE\_E\_FULL}^{T}
}
\]

This is stronger evidence for corrected visual-evidence recovery than rescuing an omission-only case.

## `B1_UNRESOLVED_ONLY` \(n=4\)

Report exact transitions.

No subgroup significance testing.

---

# 20. B4 interpretation

B4 satisfies:

\[
E^-O^-.
\]

If T rescues B4, do not attribute the rescue solely to visual-evidence recovery.

Possible explanations include:

- improved downstream reasoning;
- better convergence;
- better decomposition;
- better use of derived facts;
- other checkpoint/variant differences.

Substantial B4 rescue therefore motivates a separate downstream localization experiment.

---

# 21. Thinking pathology

Reuse:

- R1 `SEVERE_REPETITION`
- R2 `REOPEN_AFTER_PROVISIONAL_ANSWER`
- R3 `NONCONVERGENT_REASONING`
- R4 `LONG_ADVANCING_COMPUTATION`
- R5 `TERMINAL_AMBIGUITY`

Reasoning length and repetition are descriptive.

Do not assume:

\[
\text{longer reasoning}
\Rightarrow
\text{better evidence recovery}.
\]

---

# 22. Overall accuracy — secondary only

Across jointly scoreable families report:

\[
Acc_N,\quad Acc_C,\quad Acc_T.
\]

Also report:

## N vs T
- rescue;
- regression;
- both correct;
- both wrong.

## C vs T
- T-only success;
- C-only success;
- both correct;
- both wrong.

Aggregate accuracy must not replace the B1/B4 analysis.

---

# 23. Prospectively frozen decision states

## `THINKING_VISUAL_RECOVERY_SIGNAL`

Declare if all hold:

1. at least 5 scoreable B1 families are rescued by T;
2. at least 3 B1 families satisfy:
   \[
   C^- \land T^+;
   \]
3. at least 3 B1 families satisfy:
   \[
   C^- \land T^+ \land \texttt{TRACE\_E\_FULL}^{T}.
   \]

Interpretation:

> the native Thinking variant shows a meaningful rescue pattern consistent with improved task-conditioned visual-evidence recovery.

---

## `THINKING_RESCUE_WITHOUT_CLEAR_EVIDENCE_LINK`

Declare if:

- B1 has at least 5 T rescues;
- but fewer than 3 T-only B1 rescues show `TRACE_E_FULL`.

Interpretation:

> Thinking rescues upstream-rescuable failures, but visible traces do not establish improved evidence recovery as the explanation.

---

## `THINKING_DOWNSTREAM_SIGNAL`

Declare if B4 has at least:

\[
\boxed{5}
\]

Thinking rescues.

This may coexist with a visual-recovery signal.

---

## `THINKING_RESCUE_SPARSE`

Declare if both:

- B1 has fewer than 5 T rescues;
- B4 has fewer than 5 T rescues.

Then the main Claim 1 remains Stage 12B-S plus the sparse CoT result.

---

## `THINKING_TECHNICAL_BREAKDOWN`

Only if the full 61-family run materially violates the validated 81,920-token scoreability/input-integrity regime.

Repetition alone is not technical breakdown.

---

# 24. Positive-result claim language

If `THINKING_VISUAL_RECOVERY_SIGNAL`:

> **One contributor to the native Thinking variant's advantage is improved task-conditioned recovery of visual evidence during reasoning: Thinking rescues failures associated with incomplete evidence recovery that prompted CoT does not, and the rescued traces explicitly recover the previously missing task-critical facts.**

Do not say:

> Thinking is better because it sees better.

Do not say:

> improved evidence recovery is the only source of Thinking's advantage.

---

# 25. What this stage cannot prove

Even with a strong positive result, do not claim:

- `TRACE_E_FULL` equals hidden-state retrieval;
- T vs C is a causal Thinking on/off effect;
- a specific attention head or KV carrier caused the rescue;
- all modern VLMs share this failure/recovery pattern;
- the 61-family cohort estimates benchmark-wide prevalence.

---

# 26. Mechanistic follow-up if the visual-recovery signal is positive

Select frozen B1 families satisfying:

\[
C^-T^+
\]

especially:

\[
C^-T^+\land\texttt{TRACE\_E\_FULL}^{T}.
\]

Then use the existing Claim 2 machinery to compare Native / CoT / Thinking:

1. target-specific visual retrieval timing;
2. causal source substitution where feasible;
3. demanded ROI vs irrelevant ROI dependence;
4. Value-rich semantic transfer;
5. whether the missing \(E^*\) becomes causally available before the successful reasoning step.

Primary next question:

\[
\boxed{
\textbf{Does Thinking rescue coincide with stronger or better-targeted causal visual retrieval of the missing evidence?}
}
\]

This would directly connect Claim 1 to Claim 2.

---

# 27. Follow-up if B4 rescue is substantial

If `THINKING_DOWNSTREAM_SIGNAL`, run a separate Thinking Equal-Evidence Oracle on the rescued B4 families.

Question:

\[
\boxed{
\textbf{Does Thinking remain superior when correct }E^*\textbf{ is explicitly equalized?}
}
\]

A persistent T advantage would support a downstream benefit and connect Claim 1 to Claim 3.

Do not launch this in Stage 12T-S.

---

# 28. Null discipline

If Thinking rescue is sparse, do not weaken the Stage 12B-S result.

The appropriate conclusion is:

> task-critical visual-evidence recovery is a major native bottleneck, but neither generic prompted CoT nor native Thinking substantially repairs the primary frozen failure strata in this developmental cohort.

If T rescues B1 but does not externalize correct \(E^*\), do not force an evidence-recovery explanation.

If T rescues B4, do not explain that gain solely through better vision.

---

# 29. Statistical inference

Independent unit:

\[
\boxed{
\text{problem/image family}
}
\]

For B1/B4 rescue:

- exact counts;
- scoreable denominator;
- frozen total;
- Wilson 95% interval;
- missingness bounds.

For:

\[
\Delta_T
\]

use 4,000 family-level bootstrap draws with a frozen seed.

For C-vs-T transitions:

- exact paired discordant counts;
- descriptive paired intervals where useful;
- no causal interpretation.

---

# 30. Sensitivity analyses

Report:

## S1
Exclude original Stage 12B development families.

## S2
Exclude all families previously used in technical development/validation before Stage 12T-S.

Re-estimate where sample size permits:

- B1 T rescue;
- B4 T rescue;
- T-only B1 rescue;
- evidence-linked T rescue.

These are sensitivity analyses only.

---

# 31. Required figures

## Figure T1 — Native failure map with CoT and Thinking rescue overlay

Frozen B1–B4 counts plus:

- CoT rescue;
- Thinking rescue.

## Figure T2 — B1/B4 rescue by mode

Show:

\[
R_{C,B1},\quad R_{T,B1},\quad R_{C,B4},\quad R_{T,B4}.
\]

## Figure T3 — B1 C-to-T paired transitions

- both fail;
- C-only;
- T-only;
- both succeed.

## Figure T4 — B1 visible evidence-state transitions

Highlight:

\[
\texttt{C: WRONG/CONFLICTING}
\rightarrow
\texttt{T: FULL}.
\]

## Figure T5 — Thinking-only evidence-linked rescue examples

Use deterministic selection after labels are frozen, e.g. smallest family IDs among:

\[
B1\land C^-\land T^+\land\texttt{TRACE\_E\_FULL}^{T}.
\]

---

# 32. Required artifacts

Produce:

1. `stage12ts_thinking_scientific_spec.md`
2. `stage12ts_thinking_manifest.json`
3. `stage12ts_reused24_manifest.json`
4. `stage12ts_remaining37_manifest.json`
5. `stage12ts_integrity_results.parquet`
6. `stage12ts_thinking_results.parquet`
7. `stage12ts_thinking_scoring_blind.parquet`
8. `stage12ts_scoring_review_log.json`
9. `stage12ts_trace_evidence_states.parquet`
10. `stage12ts_cot_thinking_transitions.parquet`
11. `stage12ts_pathology.parquet`
12. `stage12ts_primary_inference.json`
13. `stage12ts_sensitivity_results.json`
14. `stage12ts_decision.json`
15. `stage12ts_resource_accounting.json`
16. `stage12ts_summary.md`

Preserve all Stage 12B-S, Stage 12C-R, and Stage 12T-R artifacts unchanged.

---

# 33. Compute budget

New Thinking generation:

\[
\boxed{
37 \text{ calls}
}
\]

at max 81,920 tokens.

The validated 24 outputs are reused.

Target:

\[
\boxed{
<4.5 \text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
6.5 \text{ GPU-hours}
}
\]

unless separately approved.

Do not run:

- new E probes;
- new N;
- new CoT;
- new Native-Instruct Oracle;
- Thinking Oracle;
- hidden-state interventions;
- benchmark mining;
- decoding search.

---

# 34. Exactly one recommendation at completion

## If `THINKING_VISUAL_RECOVERY_SIGNAL`

Recommend:

> Run a focused causal visual-retrieval comparison on B1 families that fail under CoT but succeed under Thinking with full task-critical evidence recovery in the Thinking trace.

## If `THINKING_DOWNSTREAM_SIGNAL` without visual-recovery signal

Recommend:

> Run Thinking Equal-Evidence Oracles on rescued B4 families to localize the gain downstream of visual evidence acquisition.

## If both signals occur

Recommend:

> Prioritize the B1 causal-retrieval analysis first, then test B4 downstream persistence with Thinking Equal-Evidence Oracles.

## If `THINKING_RESCUE_WITHOUT_CLEAR_EVIDENCE_LINK`

Recommend:

> Investigate alternative mechanisms on T-rescued B1 cases before attributing the gain to visual-evidence recovery.

## If `THINKING_RESCUE_SPARSE`

Recommend:

> Stop the rescue branch and retain Stage 12B-S plus the sparse CoT result as the completed Claim 1 behavioral story.

Do not launch automatically.

---

# 35. Final decision target

Stage 12T-S exists to answer:

\[
\boxed{
\textbf{Is one source of the native Thinking variant's advantage that its reasoning process
more successfully recovers task-critical visual evidence that Native Instruct and generic CoT fail to recover?}
}
\]

The decisive pattern is not simply:

\[
Acc_T>Acc_C.
\]

It is:

\[
\boxed{
B1
\land
C^-
\land
T^+
\land
\texttt{TRACE\_E\_FULL}^{T}
}
\]

appearing at meaningful yield.

That result would provide the strongest behavioral bridge yet between the new Claim 1 failure analysis and the existing Claim 2 causal visual-retrieval mechanism.
