# Stage 12B-S — Full Scientific Failure-Bottleneck Profiling

## 0. One-line objective

Resume the original Stage 12B science now that Stage 12B-R established a pathology-aware validity rule.

The scientific question is:

\[
\boxed{
\textbf{When Qwen3-VL-4B-Instruct fails a multimodal reasoning problem,
is the bottleneck primarily visual-evidence recovery,
task-context evidence access/use,
or downstream reasoning after correct evidence is supplied?}
}
\]

This stage opens correctness for the first time and estimates the frozen Stage 12B bottleneck profile.

No prompt, model, runtime, cap, validity rule, \(E^*\), or bottleneck definition may be changed.

---

# 1. Why this stage is now justified

Stage 12B originally stopped because severe repetition had been treated as technical invalidity.

Stage 12B-R prospectively repaired that criterion and validated it on an untouched 12-family set.

The repaired rule is:

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

Reasoning pathologies such as:

- severe repetition;
- reopening after a provisional answer;
- nonconvergent reasoning;
- unusually long but advancing computation

are retained as **scientific model behaviors**, not automatic exclusions.

Stage 12B-R returned:

\[
\boxed{
\texttt{VALIDITY\_REPAIRED}
}
\]

Therefore the original scientific profiling may now resume.

---

# 2. Paper-level role

This is the behavioral foundation of the new main Claim 1:

> **Where and why do modern VLMs fail, and which failures are later reduced by additional inference-time reasoning?**

The intended paper arc is:

\[
\boxed{
\textbf{Where does the VLM fail?}
}
\]

\[
\downarrow
\]

\[
\boxed{
\textbf{Which failure states are rescued by CoT / Thinking?}
}
\]

\[
\downarrow
\]

\[
\boxed{
\textbf{How does reasoning causally control visual retrieval?}
}
\]

\[
\downarrow
\]

\[
\boxed{
\textbf{How is retrieved evidence propagated into later reasoning?}
}
\]

Stage 12B-S estimates only the first box.

---

# 3. Frozen scientific objects

Everything below remains unchanged from Stage 12B / 12B-R.

## Model

\[
\boxed{
\textbf{Qwen3-VL-4B-Instruct}
}
\]

Revision:

\[
\boxed{
\texttt{ebb281ec70b05090aa6165b016eac8ec08e71b17}
}
\]

Runtime:

- BF16
- vLLM 0.11.0
- same processor/tokenizer
- same image preprocessing
- same sampling implementation

## Dataset

\[
\boxed{
61 \text{ independent MathVision families}
}
\]

Composition:

- 24 multiple-choice;
- 37 open-ended.

## Evidence

Preserve exactly:

- 157 frozen \(E^*\) facts;
- all fact requests;
- source answers;
- original questions;
- image hashes;
- prior \(E^*\) sufficiency judgments.

No fact may be added, removed, rewritten, or reinterpreted after outcomes are opened.

---

# 4. Frozen conditions

Each family has three scientific conditions:

\[
\boxed{
E,\quad N,\quad O
}
\]

## E — Direct Evidence Probe

Image present.

Ask only for the frozen task-critical visual evidence \(E^*\).

Cap:

\[
\boxed{
256
}
\]

generated tokens.

## N — Native Instruct Task Solving

Original image + exact original question.

No added:

- answer-only instruction;
- no-reasoning instruction;
- CoT instruction.

Spontaneous reasoning is allowed.

Cap:

\[
\boxed{
32768
}
\]

generated tokens.

## O — Equal-Evidence Oracle

No image.

Supply the exact frozen correct \(E^*\) as text and preserve the original question.

No final-answer leakage or extra derivation.

Cap:

\[
\boxed{
32768
}
\]

generated tokens.

---

# 5. Frozen generation recipe

For N and O:

- temperature = 0.7
- top-p = 0.8
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 1.5

Use the previously frozen per-family seed policy.

Do not perform:

- prompt search;
- cap search;
- sampling search;
- retry-on-failure;
- best-of-N;
- answer-guided reruns.

One logical run per family per arm.

---

# 6. Reuse of existing 24 technical families

Two technical sets already exist under the exact frozen Stage 12B protocol:

1. original Stage 12B development/audit set:
   \[
   12 \text{ families}
   \]

2. Stage 12B-R untouched validation set:
   \[
   12 \text{ families}
   \]

No task correctness or evidence correctness was used to select prompts, runtime, caps, or scientific definitions.

Therefore their preserved E/N/O generations may be reused in the main 61-family scientific analysis.

Do not regenerate them.

This avoids stochastic replacement after technical behavior has been inspected.

---

# 7. New generation required

Generate only the remaining:

\[
\boxed{
61-24=37 \text{ families}
}
\]

under the frozen E/N/O protocol.

New logical calls:

\[
\boxed{
37\times3=111
}
\]

No correctness may be opened until all planned remaining generations and integrity checks are complete.

---

# 8. Pre-scoring integrity pass

Before opening gold correctness, verify all 61 families.

For each arm record:

- `INPUT_VALID`;
- `SCOREABLE`;
- `TRUNCATED_BEFORE_OUTCOME`;
- `CAP_AFTER_OUTCOME`;
- stop reason.

Use the Stage 12B-R validity specification exactly.

No repetition threshold.

Pathology labels remain separate.

---

# 9. Primary denominator rule

Freeze the denominator before correctness is opened.

## 9.1 Native accuracy denominator

Native task accuracy is estimated among families with:

\[
\boxed{
N:\texttt{INPUT\_VALID}=1
\land
N:\texttt{SCOREABLE}=1
}
\]

Call this set:

\[
\mathcal N_{\text{scoreable}}
\]

Do not count technically unscoreable N outputs as automatically wrong.

Report their count separately.

---

## 9.2 Bottleneck-profile denominator

A family can receive a B1–B4 bottleneck label only if all three required outcomes are scientifically interpretable:

\[
\boxed{
E,N,O\text{ are input-valid and scoreable}
}
\]

Define:

\[
\mathcal C
=
\{i:E_i,N_i,O_i\text{ all scoreable and input-valid}\}
\]

The primary bottleneck profile is computed among:

\[
\boxed{
\mathcal F
=
\{i\in\mathcal C:N_i^-=1\}
}
\]

where \(N_i^-\) means a scientifically scored native task failure.

This is the **primary complete-profile failure set**.

---

## 9.3 Technical unresolved category

Any family lacking a scoreable E, N, or O outcome is not forced into B1–B4.

Assign:

\[
\boxed{
\texttt{TECHNICAL\_UNRESOLVED}
}
\]

and report separately.

Do not encode unscoreable as incorrect.

---

# 10. Arm-blind correctness scoring

Correctness scoring must be performed arm-by-arm without exposing paired outcomes.

The goal is to prevent knowledge of N/O rescue or failure from influencing E or task scoring.

---

## 10.1 Evidence scoring batch

Create a scoring file containing only:

- family ID;
- frozen evidence request(s);
- frozen gold \(E^*\);
- E response.

Do not include:

- N output;
- O output;
- native correctness;
- oracle correctness;
- pathology labels from other arms.

Score each evidence atom:

- `CORRECT`
- `INCORRECT`
- `UNRESOLVED`

Define:

\[
\boxed{
E^+=1
}
\]

iff all frozen task-critical atoms are `CORRECT`.

Otherwise:

\[
E^-=1
\]

for scientifically scoreable evidence responses.

Retain atom-level correctness separately.

---

## 10.2 Native scoring batch

Create a scoring file containing only:

- family ID;
- original question;
- source answer / gold;
- N response.

Do not include E or O outputs.

Score:

- `CORRECT`
- `INCORRECT`
- `UNRESOLVED_TECHNICAL`

For multiple choice, use benchmark option equivalence.

For open-ended tasks, use the frozen MathVision mathematical-equivalence policy.

---

## 10.3 Oracle scoring batch

Create a scoring file containing only:

- family ID;
- oracle question/input;
- source answer / gold;
- O response.

Do not include E or N outputs.

Use the same task-answer equivalence policy as N.

---

# 11. Ambiguous-scoring second-review rule

A second review is required prospectively for any case satisfying at least one of:

### Evidence ambiguity

- OCR-like symbol ambiguity;
- multiple plausible entity bindings;
- unit ambiguity;
- partial multi-atom response;
- mathematically equivalent but differently expressed fact;
- uncertain correspondence to the frozen request.

### Native / Oracle ambiguity

- multiple answer candidates with unclear supersession;
- nonstandard but potentially equivalent mathematical expression;
- ambiguous sign/unit convention;
- malformed but possibly extractable option;
- answer depends on benchmark-equivalence interpretation.

### Pathology-linked ambiguity

- a provisional answer is later reopened;
- a capped response contains an earlier commitment;
- terminal text contains competing expressions.

For these cases:

1. first review records a provisional label and reason;
2. second review is conducted without seeing the paired-arm outcomes;
3. disagreements are preserved;
4. adjudication uses only the frozen scoring policy and the arm's own response.

Do not resolve ambiguity using the desired bottleneck category.

---

# 12. Random scoring audit

In addition to ambiguity-triggered second review, randomly select:

\[
\boxed{
20\%
}
\]

of otherwise unambiguous families for a blinded second-pass correctness audit.

Use a deterministic hash-based selection frozen before correctness scoring.

Report agreement separately for:

- E atom scoring;
- N task scoring;
- O task scoring.

This is a quality-control estimate, not an independent human inter-rater reliability claim unless a genuinely independent reviewer is used.

---

# 13. Frozen bottleneck taxonomy

Only classify families in:

\[
\mathcal F
=
\{i\in\mathcal C:N_i^-=1\}
\]

---

## B1 — Perceptual / evidence-availability bottleneck candidate

\[
\boxed{
E^- \land O^+
}
\]

Interpretation:

> the model fails natively and cannot fully recover the required visual evidence under direct probing, but succeeds when the correct evidence is explicitly supplied.

This is the strongest operational upstream perception/evidence-availability pattern.

Do not claim hidden-state absence.

---

## B2 — Task-context evidence access/use bottleneck candidate

\[
\boxed{
E^+ \land O^+
}
\]

Interpretation:

> the required evidence is directly recoverable and behaviorally sufficient when explicitly supplied, yet native task solving fails.

This is the primary multimodal `Lost Keys` analogue.

Do not claim that the failed native trajectory internally contained the correct evidence.

---

## B3 — Downstream reasoning bottleneck candidate

\[
\boxed{
E^+ \land O^-
}
\]

Interpretation:

> the required evidence is directly recoverable, but supplying it explicitly still does not yield the correct task answer.

This localizes the operational failure downstream of basic visual evidence recovery.

---

## B4 — Mixed / unresolved bottleneck candidate

\[
\boxed{
E^- \land O^-
}
\]

Interpretation:

> both evidence recovery and oracle task solving fail.

No unique stage is identified.

---

# 14. Frozen primary endpoints

Preserve the original Stage 12B P1–P6 definitions, with denominators now made explicit.

## P1 — Native failure prevalence

Among \(\mathcal N_{\text{scoreable}}\):

\[
\boxed{
P1=P(N^-)
}
\]

Report native task accuracy alongside it.

## P2 — Oracle-rescuable failure fraction

Among \(\mathcal F\):

\[
\boxed{
P2=P(O^+\mid N^-)
}
\]

This is the broadest upstream-vs-downstream localization quantity.

## P3 — Perceptual / evidence-availability fraction

\[
\boxed{
P3=P(E^-,O^+\mid N^-)
}
\]

equivalently the B1 fraction within \(\mathcal F\).

## P4 — Task-context evidence access/use fraction

\[
\boxed{
P4=P(E^+,O^+\mid N^-)
}
\]

equivalently the B2 fraction.

This is the primary multimodal Lost-Keys quantity.

## P5 — Downstream reasoning fraction

\[
\boxed{
P5=P(E^+,O^-\mid N^-)
}
\]

equivalently the B3 fraction.

## P6 — Mixed / unresolved fraction

\[
\boxed{
P6=P(E^-,O^-\mid N^-)
}
\]

equivalently the B4 fraction.

Within \(\mathcal F\):

\[
\boxed{
P3+P4+P5+P6=1
}
\]

up to rounding.

---

# 15. Secondary oracle-rescue contrasts

Report:

\[
\boxed{
P(O^+\mid E^+,N^-)
}
\]

and:

\[
\boxed{
P(O^+\mid E^-,N^-)
}
\]

within the complete-profile set.

Define:

\[
\Delta_O
=
P(O^+\mid E^+,N^-)
-
P(O^+\mid E^-,N^-)
\]

This is descriptive.

Do not interpret it as a causal effect of evidence probing.

---

# 16. Pathology labels remain scientific outcomes

Preserve the Stage 12B-R pathology definitions.

For N and O record:

- R1 `SEVERE_REPETITION`
- R2 `REOPEN_AFTER_PROVISIONAL_ANSWER`
- R3 `NONCONVERGENT_REASONING`
- R4 `LONG_ADVANCING_COMPUTATION`
- R5 `TERMINAL_AMBIGUITY`

R1–R4 are never automatic exclusions.

R5 may make the outcome unscoreable under the frozen scoreability rule.

---

# 17. Secondary downstream-failure taxonomy

For scientifically valid task failures, classify visible reasoning into:

\[
\boxed{
\texttt{WRONG\_CONVERGED}
}
\]

\[
\boxed{
\texttt{LOOP\_OR\_REOPEN}
}
\]

\[
\boxed{
\texttt{NONCONVERGENT}
}
\]

\[
\boxed{
\texttt{OTHER}
}
\]

This classification is secondary and must not alter B1–B4.

---

# 18. Key pathology analyses

These analyses answer a more specific version of “why does reasoning fail?”

## 18.1 Oracle pathology persistence

For families with pathology in N, classify O as:

- `RESOLVED`
- `PERSISTED_SAME_TYPE`
- `PERSISTED_DIFFERENT_TYPE`
- `UNSCOREABLE`

Question:

> does supplying correct visual evidence eliminate native reasoning pathology or does the pathology persist downstream?

## 18.2 Evidence-resolved but pathological failure

Identify:

\[
\boxed{
E^+\land O^-\land(R1\lor R2\lor R3)
}
\]

These are strong downstream-failure candidates:

- evidence is directly recoverable;
- oracle supplies it explicitly;
- reasoning still fails pathologically.

## 18.3 Native pathology resolved by oracle

Identify:

\[
\boxed{
N^- \land R_j^{N}=1 \land O^+ \land R_j^{O}=0
}
\]

These cases suggest that some apparent reasoning pathology may be downstream of unresolved visual evidence acquisition/access.

Do not claim causality beyond the oracle manipulation.

---

# 19. Statistical inference

Independent unit:

\[
\boxed{
\text{problem/image family}
}
\]

Report:

- exact counts;
- point estimates;
- Wilson 95% intervals for proportions;
- family-level bootstrap intervals for selected contrasts.

Use:

\[
\boxed{
4000
}
\]

bootstrap draws with a frozen seed.

Do not treat:

- evidence atoms;
- tokens;
- reasoning steps

as independent observations.

---

# 20. Frozen profile decision rule

Preserve the original Stage 12B decision logic.

## PROFILE_INFORMATIVE

Declare if:

1. at least:
   \[
   \boxed{
   20
   }
   \]
   scientifically scored native failures are observed;

2. among B1–B3:
   - at least two categories contain:
     \[
     \boxed{
     \ge5
     }
     \]
     independent families,

     **or**

   - one category alone contains:
     \[
     \boxed{
     \ge10
     }
     \]
     independent families;

3. the repaired validity rule remains satisfied at full-cohort scale;

4. oracle integrity remains intact.

Interpretation:

> the failure taxonomy has enough yield to support a selective CoT/Thinking rescue study.

## PROFILE_SPARSE

Declare if:

- fewer than 20 scientifically scored native failures occur;
- or bottleneck categories are too sparse for conditional rescue analysis.

This is a cohort-yield limitation, not evidence against the taxonomy.

## TECHNICAL_BREAKDOWN

Declare only if full-cohort scoreability/input integrity is substantially worse than the validated assay, e.g.:

- systematic input corruption;
- widespread unscoreable outputs;
- unexpected truncation that prevents primary profiling.

Do not use repetition frequency alone to declare technical breakdown.

---

# 21. Sensitivity analyses

The main analysis uses all scientifically valid families.

Also report two preregistered sensitivity profiles.

## S1 — Exclude original Stage 12B development set

Remove the original 12 technical-development families.

Re-estimate:

- P1–P6;
- B1–B4 counts.

## S2 — Exclude all 24 technical families

Remove:

- original 12 development families;
- Stage 12B-R 12 validation families.

Re-estimate the same quantities on the remaining 37 families.

These are sensitivity analyses only.

Do not replace the main 61-family analysis unless a validity problem is discovered.

---

# 22. Interpretation matrix

After P1–P6 are opened, use the following outcome-dependent framing.

## If B1 is large

Primary story:

> a substantial share of errors originate in failure to recover task-critical visual evidence.

Next rescue question:

> can CoT or Thinking improve visual evidence recovery?

## If B2 is large

Primary story:

> many errors occur despite directly recoverable and behaviorally sufficient visual evidence.

This is the strongest multimodal Lost-Keys result.

Next rescue question:

> do CoT and Thinking selectively rescue these access/use failures?

This outcome connects most directly to the existing causal result:

\[
\text{reasoning context}
\rightarrow
\text{target-specific visual retrieval}
\]

## If B3 is large

Primary story:

> many errors persist even after correct task-critical visual evidence is explicitly supplied.

Next rescue question:

> does CoT/Thinking primarily improve downstream integration, convergence, or calculation?

This outcome connects strongly to the existing visual-to-text lifecycle and downstream carrier results.

## If B1/B2/B3 are all substantial

Primary story:

> multimodal reasoning errors arise at multiple distinct stages of the evidence-to-reasoning pipeline.

This supports a stage-structured failure map rather than a single dominant bottleneck.

---

# 23. What Stage 12B-S may claim

If informative:

> **Modern VLM failures can be behaviorally localized into visual-evidence recovery, task-context evidence access/use, and downstream reasoning bottlenecks using direct evidence probes and an equal-evidence causal bypass.**

If B2 is substantial:

> **A substantial subset of native errors occur even when task-critical visual evidence is directly recoverable and sufficient to solve the task when explicitly supplied.**

If B3 is substantial:

> **A substantial subset of errors persist after visual evidence is equalized, localizing the bottleneck downstream of basic evidence recovery.**

---

# 24. What Stage 12B-S may NOT claim

Do not claim yet:

- CoT fixes a specific bottleneck;
- Thinking fixes a specific bottleneck;
- Thinking is better because it retrieves better;
- B2 proves the failed native trajectory internally represented the correct evidence;
- B3 proves perception was perfect;
- a specific attention head or KV carrier caused any individual benchmark failure.

Those require later stages.

---

# 25. Next stage if PROFILE_INFORMATIVE

Freeze all Stage 12B-S labels before adding new model conditions.

Then run:

\[
\boxed{
C=\text{Qwen3-VL-4B-Instruct + prompted CoT}
}
\]

and:

\[
\boxed{
T=\text{Qwen3-VL-4B-Thinking}
}
\]

on the same frozen families.

Primary questions:

\[
P(C^+\mid N^-,B_j)
\]

and:

\[
P(T^+\mid N^-,B_j)
\]

for \(j\in\{1,2,3,4\}\).

The key paper question then becomes:

\[
\boxed{
\textbf{Which native VLM failure states are selectively rescued by prompted CoT and native Thinking?}
}
\]

Do not launch C/T automatically in this stage.

---

# 26. Relation to Claims 2 and 3

If B2 is populated and later selectively rescued:

## Claim 2

\[
\boxed{
\text{reasoning demand}
\rightarrow
\text{target-specific causal visual retrieval}
}
\]

provides a mechanistic explanation for improved task-context evidence access.

If B3 is populated:

## Claim 3

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

provides a mechanistic framework for understanding post-retrieval success and failure.

---

# 27. Required figures

## Figure 1 — Assay schematic

\[
\text{Image}
\rightarrow
E^*
\rightarrow
\text{task reasoning}
\rightarrow
\text{answer}
\]

Show:

- direct E probe;
- native N path;
- image-free O bypass.

## Figure 2 — Main native-failure composition

Among \(\mathcal F\), show B1–B4 counts and proportions.

This is the centerpiece figure.

## Figure 3 — Oracle rescue by evidence recoverability

Compare:

\[
P(O^+\mid E^+,N^-)
\]

vs:

\[
P(O^+\mid E^-,N^-)
\]

with intervals.

## Figure 4 — Reasoning pathology by bottleneck

Show R1–R4 frequencies across:

- B1;
- B2;
- B3;
- B4.

Treat as secondary/explanatory.

## Figure 5 — Representative examples

Use a deterministic rule after labels are frozen, e.g.:

- smallest family ID in each nonempty B1–B4 category.

Show:

- question summary;
- \(E^*\);
- E result;
- N result;
- O result;
- pathology labels.

Do not select examples by rhetorical strength.

---

# 28. Required artifacts

Produce:

1. `stage12bs_scientific_profile_spec.md`
2. `stage12bs_full_manifest.json`
3. `stage12bs_remaining_generation_manifest.json`
4. `stage12bs_integrity_results.parquet`
5. `stage12bs_evidence_scoring_blind.parquet`
6. `stage12bs_native_scoring_blind.parquet`
7. `stage12bs_oracle_scoring_blind.parquet`
8. `stage12bs_second_review_log.json`
9. `stage12bs_scoring_audit.json`
10. `stage12bs_failure_profiles.parquet`
11. `stage12bs_pathology_analysis.parquet`
12. `stage12bs_primary_inference.json`
13. `stage12bs_sensitivity_results.json`
14. `stage12bs_profile_decision.json`
15. `stage12bs_resource_accounting.json`
16. `stage12bs_summary.md`

Preserve all Stage 12B and 12B-R artifacts unchanged.

---

# 29. Compute budget

New generation:

\[
\boxed{
111 \text{ logical calls}
}
\]

for the remaining 37 families.

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

unless explicitly approved.

Do not run:

- CoT;
- Thinking;
- new benchmark mining;
- mechanistic interventions;
- additional prompt repair.

---

# 30. Exactly one recommendation at completion

## If PROFILE_INFORMATIVE

Recommend:

> Freeze the Stage 12B-S bottleneck labels and run prompted CoT plus native Thinking on the same families to test selective rescue by failure type.

## If PROFILE_SPARSE

Recommend:

> Build a fresh harder \(E^*\)-annotated cohort before testing selective CoT/Thinking rescue.

## If TECHNICAL_BREAKDOWN

Recommend:

> Diagnose the specific full-cohort scoreability/integrity failure without changing scientific bottleneck definitions.

Do not launch the recommendation automatically.

---

# 31. Final decision target

Stage 12B-S exists to answer:

\[
\boxed{
\textbf{Among scientifically scoreable native VLM failures,
what fraction localize to visual-evidence recovery,
task-context evidence access/use,
downstream reasoning,
or mixed unresolved failure?}
}
\]

Only after this profile is frozen should CoT and native Thinking be introduced as **selective rescue conditions**.
