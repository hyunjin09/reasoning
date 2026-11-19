# Stage 12X-S — Held-Out Replication of Portable Thinking-State Production

## 0. Objective

Test whether the strongest Stage 12U-S result replicates on a **fresh, previously untouched MathVision cohort**:

\[
\boxed{
\textbf{Thinking produces task-specific externalized reasoning states that
a weaker Instruct checkpoint can use to solve problems it otherwise cannot solve.}
}
\]

This stage deliberately stops fine-grained text localization. Stage 12V-S and Stage 12W-S showed that full-prefix portability is real in the developmental cohort, but a single necessary deduction or robust cross-family block-level mechanism was not identified.

The next highest-value question is therefore:

\[
\boxed{
\textbf{Does portable reasoning-state production generalize to new problems
selected without using any prior model outcomes?}
}
\]

---

## 1. Why this experiment is necessary

The current developmental story is:

1. Stage 12B-S: correct \(E^*\) repaired nearly half of complete Native Instruct failures.
2. Stage 12C-R: generic prompted CoT barely rescued B1/B4.
3. Stage 12T-S: native Thinking rescued additional failures, especially B4.
4. Stage 12U-S: on five targeted B4 \(C^-T^+\) families,
   \[
   R_T\rightarrow T=5/5,\qquad R_T\rightarrow I=4/5,
   \]
   while question-only and shuffled-trace controls did not explain the effect.
5. Stage 12V-S / 12W-S: the portable state could not be robustly localized to one necessary textual step or one cross-family distributed block mechanism.

Therefore the strongest supported statement is:

> **Thinking can produce a task-specific intermediate reasoning state that is portable to Instruct.**

Before promoting this to a broad paper claim, it needs a fresh held-out replication.

---

## 2. Claim under test

### If successful

> **On fresh multimodal reasoning problems, the native Thinking variant again produces task-specific intermediate reasoning states that enable the Instruct checkpoint to solve problems it otherwise fails, including cases where raw task-critical visual evidence alone is insufficient.**

### If unsuccessful

> **Portable reasoning-state production was observed in the developmental cohort but did not replicate at sufficient yield on a fresh held-out cohort.**

Do not return to the development set to rescue the claim.

---

## 3. Overall study structure

Three phases:

### Phase A — Fresh failure map
Run:
\[
E,\quad N,\quad O
\]
on a fresh \(E^*\)-annotated cohort.

Purpose: identify fresh B4 failures prospectively.

### Phase B — CoT / Thinking screen
Run:
\[
C,\quad T
\]
only on fresh B4 families.

Purpose: identify:
\[
\boxed{B4\land C^-\land T^+}
\]

### Phase C — Held-out portability test
For those fresh candidates test:

\[
R_T\rightarrow T,\qquad
R_T\rightarrow I
\]

plus question-only and shuffled-trace controls.

No single-step or block-level localization in this stage.

---

## 4. Historical exclusion rule

Before source selection, build a complete exclusion list from **all prior project manifests**.

Exclude every MathVision family that appeared in any previous technical, sanity, reserve, validation, or scientific set whose behavior was inspected, including all Stage 8/9/11/12 lineages.

Archive:

- full excluded family list;
- source file hashes;
- exclusion-manifest hash.

The new cohort must be:

\[
\boxed{
\textbf{family-disjoint from all prior technical and scientific exposure.}
}
\]

---

## 5. Fresh source cohort

Prospectively freeze:

\[
\boxed{96\text{ fresh }E^*\text{-eligible families}}
\]

plus:

\[
\boxed{32\text{ reserve candidates}}.
\]

Selection uses only source metadata:

- family ID;
- answer type;
- difficulty/level where available;
- broad task category where available.

Do not use model correctness, response length, trace appearance, or expected difficulty.

Use deterministic SHA256 ordering.

This is a **mechanism-replication cohort**, not a benchmark-prevalence sample.

---

## 6. Fresh \(E^*\) annotation

For every selected family define:

\[
E^*=\{e_1,\ldots,e_k\},\quad 1\le k\le4,
\]

where \(E^*\) is the minimal set of directly image-derived facts sufficient, with the nonvisual question text, to solve the problem.

Rules:

- directly image-derived only;
- no final answer;
- no downstream derivation;
- preserve units/entity bindings;
- each request must uniquely identify its target fact.

Complete all annotation before generation.

Quality control:

1. primary review of all 96;
2. deterministic 25% second-pass review;
3. disagreements resolved using source image/question only;
4. exact evidence requests and oracle rendering frozen before model generation.

If an item is not \(E^*\)-eligible, replace only from the pre-frozen reserve in deterministic order.

---

## 7. Phase A conditions

Run all 96 primary families under:

\[
E,\quad N,\quad O.
\]

### E — direct evidence probe
- original image;
- frozen evidence requests only;
- cap 256.

### N — Native Instruct
- Qwen3-VL-4B-Instruct;
- original image + original question;
- no added CoT;
- temperature 0.7;
- top-p 0.8;
- top-k 20;
- repetition penalty 1.0;
- presence penalty 1.5;
- max output 32,768.

### O — Equal-Evidence Oracle
- same Instruct checkpoint;
- no image;
- frozen \(Q+E^*\);
- same generation recipe as N.

---

## 8. Validity and scoring

Reuse the Stage 12B-R rule:

\[
\texttt{TECHNICALLY\_VALID}
=
\texttt{INPUT\_VALID}
\land
\texttt{SCOREABLE}
\land
\neg\texttt{TRUNCATED\_BEFORE\_OUTCOME}.
\]

Repetition/reopening/nonconvergence are behaviors, not automatic exclusions.

Score E/N/O arm-by-arm without paired outcomes visible.

Define:

\[
E^+=1
\]

iff all required frozen atoms are correct.

Task labels:

- `CORRECT`
- `INCORRECT`
- `UNSCOREABLE_TECHNICAL`

Use the same MathVision equivalence policy as prior Stage 12 work.

Run ambiguity-triggered second review plus deterministic 20% audit.

---

## 9. Fresh failure taxonomy

Among complete scoreable native failures:

\[
B1=E^-O^+,
\]

\[
B2=E^+O^+,
\]

\[
B3=E^+O^-,
\]

\[
B4=E^-O^-.
\]

The Phase B set is:

\[
\boxed{\mathcal B_4^{fresh}}.
\]

Do not redefine B4 after seeing C/T.

Also report fresh:

\[
P(O^+\mid N^-)
\]

and B1–B4 counts as secondary held-out context.

---

## 10. Phase B — Fresh B4 CoT / Thinking screen

Run C and T on all fresh scoreable B4 families.

If fresh B4 count exceeds 24, prospectively use the first 24 under a candidate hash order frozen before E/N/O correctness is opened.

### C — Prompted CoT
Same Instruct checkpoint as N.

Original image/question plus exactly:

> ` Let's think step by step.`

Recipe:

- temperature 0.7;
- top-p 0.8;
- top-k 20;
- repetition penalty 1.0;
- presence penalty 1.5;
- max output 32,768.

### T — Native Thinking
Pinned Qwen3-VL-4B-Thinking revision:

`1de27d8c51f12e819435303b9e84c4e25ba8401e`

Recipe:

- temperature 1.0;
- top-p 0.95;
- top-k 20;
- repetition penalty 1.0;
- presence penalty 0;
- max output 81,920.

No retries or decoding search.

---

## 11. Fresh transfer candidates

A family is transfer-eligible iff:

\[
\boxed{
B4\land C^-\land T^+
}
\]

with C and T scoreable.

Call:

\[
\boxed{\mathcal P_{\mathrm{fresh}}}.
\]

### Yield gate

If:

\[
|\mathcal P_{\mathrm{fresh}}|\ge5,
\]

proceed normally.

If:

\[
3\le|\mathcal P_{\mathrm{fresh}}|<5,
\]

run Phase C but label the result low-yield.

If fewer than 3 candidates:

\[
\boxed{\texttt{HELDOUT\_CANDIDATE\_SPARSE}}
\]

and stop before portability claims.

Do not expand the cohort after seeing yield.

---

## 12. Thinking source prefix

For each fresh transfer candidate, reuse the exact successful Thinking trajectory from Phase B.

Construct one answer-safe prefix:

\[
R_T^{safe}
\]

using the Stage 12U-S rule:

> maximal Thinking reasoning prefix ending before the first explicit task-answer candidate or commitment.

Do not choose the cut based on replay outcomes.

Remove only model-control wrappers when canonicalizing across checkpoints.

Before replay record:

- no explicit final;
- no explicit answer candidate;
- incidental gold-value occurrence;
- visible \(E^*\) state;
- token length;
- cut position;
- source trace hash.

Freeze before target generation.

---

## 13. Phase C core replay conditions

All conditions are image-free.

For every candidate run:

### P1 — same-model Thinking sufficiency
\[
R_T\rightarrow T
\]

### P2 — cross-checkpoint portability
\[
R_T\rightarrow I
\]

### P3 — Instruct question-only
\[
Q\rightarrow I
\]

### P4 — Thinking question-only
\[
Q\rightarrow T
\]

### P5 — shuffled Thinking trace to Instruct
\[
R_{T,j}\rightarrow I_i,\quad j\neq i
\]

using a deterministic cyclic permutation within the fresh candidate set.

No fine localization or content ablation.

---

## 14. Replay seeds

Use:

\[
\boxed{5\text{ frozen seeds per family-condition}}
\]

derived prospectively from:

`SHA256(stage12xs-v1|family_id|condition|replicate)`.

Use the same replicate indices across paired conditions.

Item-level success:

\[
\boxed{\ge3/5\text{ correct}}.
\]

Report all run-level outcomes.

No best-of-five selection.

---

## 15. Target replay recipes

### Instruct target
- same pinned 4B-Instruct checkpoint;
- assistant-prefix continuation;
- no image;
- temperature 0.7;
- top-p 0.8;
- top-k 20;
- repetition penalty 1.0;
- presence penalty 1.5;
- max new tokens 32,768.

### Thinking target
- same pinned 4B-Thinking checkpoint;
- prefix inserted into the native open reasoning channel;
- no image;
- temperature 1.0;
- top-p 0.95;
- top-k 20;
- repetition penalty 1.0;
- presence penalty 0;
- max new tokens 81,920.

---

## 16. Held-out production-support definition

A fresh family satisfies:

\[
\boxed{\texttt{HELDOUT\_PRODUCTION\_SUPPORT}}
\]

iff:

1. source family is:
   \[
   B4\land C^-\land T^+;
   \]
2. same-model replay:
   \[
   R_T\rightarrow T^+
   \]
   by at least 3/5;
3. cross-checkpoint replay:
   \[
   R_T\rightarrow I^+
   \]
   by at least 3/5;
4. Instruct question-only:
   \[
   Q\rightarrow I^-
   \]
   by at most 2/5;
5. shuffled trace:
   \[
   R_{T,\mathrm{shuffle}}\rightarrow I^-
   \]
   by at most 2/5.

This is the exact held-out analogue of the Stage 12U-S state-production signal.

Also report a stricter secondary version requiring both control success rates to be at most 1/5.

---

## 17. Primary endpoints

### X-P1 — Fresh B4 yield
\[
N_{B4}^{fresh}
\]

### X-P2 — Fresh Thinking-only B4 yield
\[
N_{\mathrm{cand}}=|\mathcal P_{\mathrm{fresh}}|
\]

### X-P3 — Same-model text sufficiency
\[
P(R_T\rightarrow T^+)
\]

### X-P4 — Cross-checkpoint portability
\[
P(R_T\rightarrow I^+)
\]

### X-P5 — Held-out production support
\[
P(\texttt{HELDOUT\_PRODUCTION\_SUPPORT})
\]

Independent unit: family.

---

## 18. Main decision states

### `HELDOUT_STATE_PRODUCTION_REPLICATED`

Declare if all hold:

1. at least 5 fresh B4 \(C^-T^+\) candidates;
2. at least 80% of candidates show:
   \[
   R_T\rightarrow T^+;
   \]
3. at least 3 fresh families satisfy `HELDOUT_PRODUCTION_SUPPORT`;
4. at least 60% of transfer-eligible candidates satisfy `HELDOUT_PRODUCTION_SUPPORT`.

Interpretation:

> portable Thinking-state production replicates on a fresh outcome-independent cohort.

### `HELDOUT_PORTABILITY_PARTIAL`

At least 3 candidates and at least 2 production-support families, but full replication gate not met.

### `HELDOUT_CANDIDATE_SPARSE`

Fewer than 3 fresh candidates.

Yield limitation, not a portability null.

### `HELDOUT_STATE_PRODUCTION_NOT_REPLICATED`

Use only if at least 5 fresh transfer candidates exist but fewer than 2 satisfy held-out production support.

---

## 19. Secondary replication analyses

Report descriptively:

- fresh \(P(O^+\mid N^-)\);
- fresh B1–B4 composition;
- fresh B4 C/T paired transitions;
- question-only T success among transfer candidates.

Do not require exact numerical agreement with the developmental cohort.

The key replication target is the **state-production transfer signature**, not prevalence equality.

---

## 20. Allowed positive claim

If `HELDOUT_STATE_PRODUCTION_REPLICATED`:

> **Portable reasoning-state production is not confined to the original development cases: on fresh B4 failures, native Thinking again produces task-specific intermediate reasoning text that is sufficient for the Thinking checkpoint and portable to the weaker Instruct checkpoint, while question-only and shuffled-trace controls fail.**

This supports a paper-level state-production claim.

---

## 21. Boundary that must remain

Even after successful replication, do not claim:

- one critical textual deduction causes portability;
- a specific block set is uniquely necessary;
- the visible text is the complete hidden mechanism;
- checkpoint differences are caused solely by Thinking post-training;
- B4 prevalence generalizes benchmark-wide.

Preserve the current boundary:

\[
\boxed{
\textbf{portable reasoning-state production: supported}
}
\]

\[
\boxed{
\textbf{fine-grained visible-text mechanism: unresolved}
}
\]

---

## 22. Null discipline

A low fresh B4 yield does not refute state production.

A cross-checkpoint replay failure does not by itself prove the useful state is non-textual.

Possible alternatives include:

- answer-safe cut too early;
- stochastic continuation;
- checkpoint-specific prefix compatibility.

That is why:

\[
R_T\rightarrow T
\]

is a mandatory same-model sufficiency control.

If same-model replay fails widely, do not interpret cross-checkpoint replay as a pure Instruct-utilization failure.

---

## 23. Statistical reporting

Independent unit:

\[
\boxed{\text{family}}
\]

Phase A:

- exact counts;
- Wilson intervals for descriptive proportions.

Phase C:

- all 5 seed outcomes;
- family-level majority outcome;
- exact family counts and descriptive exact intervals.

Seeds are not independent population samples.

No multiplicity-heavy testing program.

---

## 24. Compute budget

### Phase A
\[
96\times3=288
\]
logical calls, with E short.

### Phase B
Hard maximum:
\[
24\times2=48
\]
C/T calls.

### Phase C
For \(K\) candidates:
\[
K\times5\text{ conditions}\times5\text{ seeds}=25K.
\]

If \(K>10\), deterministically select the first 10 candidates using a candidate hash frozen before Phase B correctness is opened.

Target:
\[
\boxed{<10\text{ GPU-hours}}
\]

Hard stop:
\[
\boxed{14\text{ GPU-hours}}
\]

unless separately approved.

Use phase gates to avoid unnecessary Thinking/transfer generation.

---

## 25. Required figures

### Figure X1 — Fresh held-out failure map
Native failures, B1–B4, oracle rescue.

### Figure X2 — Fresh B4 CoT/Thinking transitions
Both fail / CoT-only / Thinking-only / both succeed.

### Figure X3 — Held-out portability matrix
Per fresh candidate:
- \(R_T\to T\)
- \(R_T\to I\)
- \(Q\to I\)
- \(Q\to T\)
- shuffled \(R_T\to I\)

### Figure X4 — Development vs held-out state production
Compare Stage 12U-S targeted development cohort against Stage 12X-S fresh candidates using exact counts, not prevalence-equality claims.

---

## 26. Required artifacts

Produce:

1. `stage12xs_heldout_replication_spec.md`
2. `stage12xs_historical_exclusion_manifest.json`
3. `stage12xs_source_candidate_manifest.json`
4. `stage12xs_fresh96_manifest.json`
5. `stage12xs_reserve32_manifest.json`
6. `stage12xs_frozen_e_star.json`
7. `stage12xs_e_star_review.json`
8. `stage12xs_phaseA_results.parquet`
9. `stage12xs_fresh_failure_profiles.parquet`
10. `stage12xs_phaseB_b4_manifest.json`
11. `stage12xs_cot_results.parquet`
12. `stage12xs_thinking_results.parquet`
13. `stage12xs_transfer_candidate_manifest.json`
14. `stage12xs_answer_safe_prefixes.json`
15. `stage12xs_transfer_results.parquet`
16. `stage12xs_shuffled_controls.parquet`
17. `stage12xs_primary_inference.json`
18. `stage12xs_decision.json`
19. `stage12xs_resource_accounting.json`
20. `stage12xs_summary.md`

Preserve all prior Stage 12 artifacts unchanged.

---

## 27. Exactly one recommendation at completion

### If `HELDOUT_STATE_PRODUCTION_REPLICATED`

Recommend:

> Replicate portable reasoning-state production at one additional Qwen3-VL model scale before promoting it to a broad Thinking-VLM claim.

### If `HELDOUT_PORTABILITY_PARTIAL`

Recommend:

> Keep state production as a promising targeted mechanism and obtain one more independent held-out cohort before making a generalization claim.

### If `HELDOUT_CANDIDATE_SPARSE`

Recommend:

> Build a harder fresh \(E^*\)-annotated cohort to increase B4 Thinking-only yield before re-testing portability.

### If `HELDOUT_STATE_PRODUCTION_NOT_REPLICATED`

Recommend:

> Restrict the paper claim to the developmental cohort and do not present portable state production as a general Thinking mechanism.

Do not launch automatically.

---

## 28. Final decision target

Stage 12X-S exists to answer:

\[
\boxed{
\textbf{Does the strongest behavioral mechanism discovered in the developmental cohort —
Thinking producing a task-specific reasoning state that Instruct can use —
replicate on entirely fresh multimodal reasoning problems?}
}
\]

The decisive held-out signature is:

\[
\boxed{
B4
\land
C^-
\land
T^+
\land
(R_T\rightarrow T^+)
\land
(R_T\rightarrow I^+)
\land
(Q\rightarrow I^-)
\land
(R_{T,\mathrm{shuffle}}\rightarrow I^-).
}
\]

A positive result would make the Claim 1 story substantially more defensible while preserving the correct boundary:

\[
\boxed{
\textbf{portable reasoning-state production is supported;
its fine-grained visible-text mechanism remains unresolved.}
}
\]
