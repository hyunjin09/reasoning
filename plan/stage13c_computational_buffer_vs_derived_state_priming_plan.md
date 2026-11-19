# Stage 13C — Why Does Thinking Help After Evidence Is Already Available?
## Computational Buffer vs Derived-State Priming under Equal Evidence

## 0. Objective

Decompose the confirmed 4B equal-evidence Thinking advantage into two candidate mechanisms inspired by *Thinking to Recall*:

\[
\boxed{
\textbf{content-independent computational buffer}
\quad\text{vs}\quad
\textbf{content-dependent derived-state priming}
}
\]

Stage 13A already established:

\[
\boxed{
Acc(T_{E^*})-Acc(I_{E^*})=+11.11\text{ pp}
}
\]

when both deployed 4B variants received the same correct task-critical evidence \(E^*\) without the image.

Stage 13C asks:

\[
\boxed{
\textbf{Why does Thinking still help after the evidence is already available?}
}
\]

This stage is restricted to the validated 4B setting and does not reopen cross-scale analysis after the Stage 13B technical stop.

---

## 1. Paper claim first

The current confirmed claim is:

> **Thinking's benefit is not reducible to visual evidence recovery.**

Stage 13C tests two complementary mechanisms.

### H1 — Computational buffer

\[
\boxed{
\textbf{Additional reasoning-token computation helps even when the intervening tokens carry no task semantics.}
}
\]

### H2 — Derived-state priming

\[
\boxed{
\textbf{Thinking-generated task-specific intermediate deductions themselves make downstream solving easier.}
}
\]

The strongest possible conclusion is:

> **Thinking's post-evidence advantage is supported by complementary content-independent computation and content-dependent semantic state construction.**

Do not claim that these mechanisms exhaust all Thinking gains unless the data justify it.

---

## 2. Identification strategy

The key design principle is to separate:

\[
\text{amount of reasoning-token computation}
\]

from:

\[
\text{semantic content carried by those tokens}.
\]

Stage 12V/W tested local necessity and remained unresolved.

Stage 13C instead uses controlled substitution:

- preserve reasoning-token length while destroying semantics;
- preserve extracted semantic deductions while matching token length with dummy controls;
- transplant only those deductions into Instruct.

This is a sufficiency/decomposition experiment, not another localization experiment.

---

## 3. Model setting

Use only the validated 4B pair:

- Qwen3-VL-4B-Instruct
- Qwen3-VL-4B-Thinking

Use the exact pinned checkpoints/revisions from Stage 13A.

No image is used anywhere in Stage 13C.

Every scientific condition starts from the exact frozen:

\[
\boxed{Q+E^*}
\]

input from Stage 13A.

Thus the entire stage operates **after evidence equalization**.

---

## 4. Scientific cohort

Prospectively select:

\[
\boxed{24\text{ families}}
\]

from the frozen Stage 13A 96-family cohort.

Selection may use only source-side fields:

- family ID;
- answer type;
- MathVision difficulty metadata;
- \(E^*\) atom count;
- source hashes.

Do not use:

- Stage 13A correctness;
- Thinking-only/Instruct-only label;
- response length;
- B1–B4 class;
- prior portability outcomes.

Within source-only strata, order by:

`SHA256(stage13c-v1|family_id)`

Freeze exactly 24 families before any new intervention generation.

---

## 5. Technical validation cohort

Choose 4 additional families from the remaining Stage 13A cohort by a separate source-only hash.

These are technical only.

Validate:

1. forced reasoning-token injection;
2. exact forced-token count;
3. correct opening/closing of the Thinking reasoning channel;
4. no accidental native reasoning after the forced trace;
5. final answer generation after the forced trace;
6. exact dummy-token length matching;
7. no image tokens;
8. no final-answer leakage from intervention text.

Technical families never enter scientific inference.

---

## 6. Frozen source Thinking trace

For every scientific family, use the **first technically resolved Stage 13A Thinking equal-evidence replicate in ascending frozen replicate order**.

Do not select by correctness.

Call its reasoning channel:

\[
R_i.
\]

Record:

- source final correctness;
- reasoning-token count:
  \[
  L_i;
  \]
- source trace hash.

The source trace is used only to define:

1. long-dummy length;
2. task-specific derived semantic content.

---

## 7. Derived-state extraction

From each \(R_i\), extract an ordered list:

\[
\boxed{
D_i=\{d_{i1},\ldots,d_{im}\}
}
\]

containing only **new task-specific intermediate propositions introduced during Thinking**.

Eligible content includes:

- entity bindings not explicitly supplied in \(Q+E^*\);
- derived geometric/algebraic relations;
- intermediate quantities;
- transformed representations;
- subgoal conclusions;
- consistency constraints;
- corrections that establish a new task-relevant proposition.

Remove:

- question restatements;
- direct \(E^*\) restatements;
- generic meta-reasoning;
- search/planning language;
- stylistic filler;
- candidate-answer guessing;
- explicit final-answer commitments;
- statements explicitly identifying the requested answer;
- answer-equivalent final conclusions.

The target object is:

\[
\boxed{
\textbf{derived semantic content beyond already-supplied }E^*.
}
\]

---

## 8. Answer-leakage audit

Before scientific generation, audit every \(D_i\).

Record:

- `EXPLICIT_FINAL_PRESENT`
- `ANSWER_COMMITMENT_PRESENT`
- `GOLD_ANSWER_EQUIVALENT_PRESENT`
- `QUESTION_RESTATEMENT_PRESENT`
- `E_STAR_RESTATEMENT_PRESENT`

Primary semantic interventions require:

- no explicit final;
- no answer commitment;
- no statement that directly resolves the asked target.

Incidental occurrence of a gold numeric value in a genuinely intermediate calculation is separately flagged.

If a safe \(D_i\) cannot be produced, mark:

\[
\texttt{NO\_SAFE\_DERIVED\_CONTENT}
\]

before intervention outcomes are generated.

That family remains in the computational-buffer arm but is excluded from semantic-effect denominators.

---

## 9. Derived-content correctness audit

Before intervention outcomes are opened, classify \(D_i\) as:

- `ALL_VERIFIED_CORRECT`
- `HAS_VERIFIED_ERROR`
- `MIXED_OR_UNCLEAR`
- `NO_SAFE_DERIVED_CONTENT`

Use the original question, frozen \(E^*\), gold answer/solution evidence, and mathematical verification.

This is secondary and is not used to select the primary semantic cohort.

---

## 10. Critical implementation requirement: forced-token reasoning

The computational-buffer test is valid only if dummy/derived reasoning tokens are processed as a forced autoregressive reasoning trajectory.

For every forced Thinking condition:

1. open the native Thinking reasoning channel;
2. inject the pre-frozen sequence token-by-token with KV-cache continuation;
3. force exactly the specified sequence;
4. force the native reasoning-channel close marker;
5. generate the final answer normally using the frozen Thinking recipe.

Do **not** implement the scientific forced trace as a user-message context substitution.

Do **not** allow additional free reasoning after the forced trace.

Save receipts with:

- forced token IDs;
- forced decoding-step count;
- close-marker position;
- answer-generation start position.

If the runtime cannot implement this contract:

\[
\boxed{\texttt{FORCED\_TRACE\_CONTRACT\_BLOCKED}}
\]

and stop before scientific calls.

---

## 11. Dummy construction

Use one pre-frozen task-independent dummy phrase:

> `Let me think.`

For each family construct token-level dummy sequences by repeating/truncating the tokenizer output.

### Short dummy

Fixed:

\[
\boxed{16\text{ reasoning tokens}}
\]

for every family.

### Long dummy

Exact token count:

\[
\boxed{|L_i^{dummy}|=L_i.}
\]

### Derived-length dummy

For semantic conditions construct:

\[
D_i^{dummy}
\]

with exact token length equal to serialized \(D_i\) under the relevant checkpoint tokenizer.

Archive all token IDs before generation.

---

## 12. Phase A — Computational-buffer assay

Run on all 24 scientific families.

All conditions use \(Q+E^*\) and the Thinking checkpoint.

Use:

\[
\boxed{5\text{ fresh frozen seeds per condition}.}
\]

### A0 — Native Thinking

\[
\boxed{T_{\mathrm{NATIVE}}}
\]

Normal Thinking generation from \(Q+E^*\).

### A1 — Short dummy

\[
\boxed{T_{\mathrm{SHORT}}}
\]

Force the 16-token dummy trace, close reasoning, generate answer.

### A2 — Long dummy

\[
\boxed{T_{\mathrm{LONG}}}
\]

Force the semantically meaningless dummy trace with length \(L_i\), close reasoning, generate answer.

---

## 13. Computational-buffer endpoint

For each family:

\[
b_i
=
Acc_i(T_{\mathrm{LONG}})
-
Acc_i(T_{\mathrm{SHORT}}).
\]

Cohort effect:

\[
\boxed{
B=\frac{1}{N}\sum_i b_i.
}
\]

Declare:

\[
\boxed{\texttt{COMPUTATIONAL\_BUFFER\_SIGNAL}}
\]

iff:

1. at least 20/24 families are fully resolved for A1/A2;
2. \(B\ge+5\) pp;
3. 95% paired family-bootstrap lower bound \(>0\).

Interpretation:

> additional reasoning-token computation improves post-evidence performance even without task-specific reasoning semantics.

---

## 14. Does compute explain the full Thinking benefit?

Define:

\[
r_i
=
Acc_i(T_{\mathrm{NATIVE}})
-
Acc_i(T_{\mathrm{LONG}}).
\]

Cohort residual:

\[
\boxed{
R=\frac{1}{N}\sum_i r_i.
}
\]

Declare:

\[
\boxed{\texttt{COMPUTE\_ALONE\_INSUFFICIENT}}
\]

iff:

1. `COMPUTATIONAL_BUFFER_SIGNAL` passes;
2. \(R\ge+5\) pp;
3. 95% family-bootstrap lower bound \(>0\).

Interpretation:

> meaningless extra computation recovers part, but not all, of native Thinking performance.

---

## 15. Phase B — Same-checkpoint semantic-content assay

Run on every family with safe nonempty \(D_i\).

Use the same Thinking checkpoint and identical forced-trace machinery.

### B1 — Derived semantic trace

\[
\boxed{T_{\mathrm{DERIVED}}}
\]

Force serialized \(D_i\), close reasoning, generate answer.

### B2 — Length-matched derived dummy

\[
\boxed{T_{\mathrm{DERIVED\_DUMMY}}}
\]

Force a dummy trace with exactly the same token length as \(D_i\), close reasoning, generate answer.

---

## 16. Same-checkpoint semantic endpoint

For each eligible family:

\[
s_i
=
Acc_i(T_{\mathrm{DERIVED}})
-
Acc_i(T_{\mathrm{DERIVED\_DUMMY}}).
\]

Declare:

\[
\boxed{\texttt{DERIVED\_SEMANTIC\_SIGNAL}}
\]

iff:

1. at least 12 families have safe nonempty \(D_i\) and complete paired outcomes;
2. mean semantic effect \(S\ge+5\) pp;
3. 95% paired family-bootstrap lower bound \(>0\).

Interpretation:

> task-specific derived content helps beyond an equal amount of forced reasoning-token computation.

---

## 17. Phase C — Portable derived-state priming in Instruct

Test whether the extracted deductions themselves help the weaker Instruct checkpoint.

All conditions use no image and the exact same \(Q+E^*\) base input.

Use:

\[
\boxed{5\text{ fresh frozen seeds per condition}.}
\]

### C0 — Instruct baseline

\[
\boxed{
I_{\mathrm{BASE}}=I(Q+E^*)
}
\]

### C1 — Instruct + Thinking-derived state

\[
\boxed{
I_{\mathrm{DERIVED}}
=
I(Q+E^*+D_i)
}
\]

Present \(D_i\) as additional intermediate reasoning context, not as an answer.

### C2 — Instruct + matched dummy context

\[
\boxed{
I_{\mathrm{DUMMY}}
=
I(Q+E^*+D_i^{dummy,I})
}
\]

with exact Instruct-token-length matching.

### C3 — Instruct + shuffled derived state

\[
\boxed{I_{\mathrm{SHUFFLED}}}
\]

Use \(D_j\) from another family.

Donor selection is frozen before generation:

1. donor must differ from target;
2. minimize absolute Instruct-token-length difference;
3. break ties by:
   `SHA256(stage13c-v1|target_id|donor_id)`.

---

## 18. Portable derived-priming endpoint

Primary semantic contrast:

\[
\boxed{
P_{\mathrm{dummy}}
=
Acc(I_{\mathrm{DERIVED}})
-
Acc(I_{\mathrm{DUMMY}})
}
\]

Task-specificity contrast:

\[
\boxed{
P_{\mathrm{shuffle}}
=
Acc(I_{\mathrm{DERIVED}})
-
Acc(I_{\mathrm{SHUFFLED}})
}
\]

Baseline gain:

\[
\boxed{
P_{\mathrm{base}}
=
Acc(I_{\mathrm{DERIVED}})
-
Acc(I_{\mathrm{BASE}})
}
\]

Declare:

\[
\boxed{\texttt{PORTABLE\_DERIVED\_PRIMING\_SIGNAL}}
\]

iff:

1. at least 12 families have safe nonempty \(D_i\) and complete C0–C3 outcomes;
2. \(P_{\mathrm{dummy}}\ge+5\) pp with bootstrap lower bound \(>0\);
3. \(P_{\mathrm{base}}>0\);
4. \(P_{\mathrm{shuffle}}>0\).

Interpretation:

> Thinking-generated derived semantic content itself improves Instruct's ability to solve the equal-evidence task.

---

## 19. Optional selected-case readout

After primary analyses are sealed, report the overlapping Stage 13A majority:

\[
I_{E^*}^-,
\quad
T_{E^*}^+
\]

families descriptively.

Ask whether:

\[
I_{\mathrm{DERIVED}}
\]

rescues their equal-evidence Instruct failure.

Do not use this selected subset for the primary mechanism decision.

---

## 20. Secondary correctness-of-derived-state analysis

Compare intervention effects by the pre-frozen \(D_i\) correctness label:

- `ALL_VERIFIED_CORRECT`
- `HAS_VERIFIED_ERROR`
- `MIXED_OR_UNCLEAR`

Ask descriptively whether verified-correct derived states lead to better final outcomes than erroneous/mixed states.

This is secondary and hypothesis-generating.

Do not claim causal hallucination propagation from this small cohort.

---

## 21. Main decision states

### `COMPUTATIONAL_BUFFER_ONLY`

Declare if:

- computational-buffer signal passes;
- neither semantic signal passes;
- native-vs-long-dummy residual is not robust.

### `DERIVED_STATE_PRIMING_ONLY`

Declare if:

- same-checkpoint semantic and/or portable derived-priming signal passes;
- computational-buffer signal does not pass.

### `COMPLEMENTARY_COMPUTE_AND_SEMANTICS`

Declare if:

1. computational-buffer signal passes;
2. at least one semantic signal passes;
3. native Thinking remains above long dummy or semantic intervention independently improves performance.

Interpretation:

> post-evidence Thinking benefit is supported by complementary content-independent computation and content-dependent task-specific state construction.

### `COMPUTE_PARTIAL_SEMANTICS_UNRESOLVED`

Use if:

- buffer passes;
- native exceeds long dummy;
- semantic interventions do not identify the residual.

### `POST_EVIDENCE_MECHANISM_UNRESOLVED`

Use if neither mechanism receives robust support.

This does not undo Stage 13A.

---

## 22. Interpretation table

| Pattern | Interpretation |
|---|---|
| Long dummy > short dummy | Computational-buffer contribution |
| Native > long dummy | Compute alone insufficient |
| Derived > derived-length dummy in Thinking | Semantic content matters within Thinking |
| Instruct + derived > Instruct + dummy | Derived content is portable/useful |
| Instruct + derived > shuffled derived | Effect is task-specific |
| Compute + semantic signals both positive | Complementary mechanisms |
| Neither positive | Mechanism remains unresolved |

---

## 23. Why this differs from Stage 12V/W

Stage 12V/W asked:

> Which step/block is necessary?

That can fail under redundancy.

Stage 13C asks:

\[
\boxed{
\textbf{Is extra computation sufficient to recover some benefit?}
}
\]

and:

\[
\boxed{
\textbf{Is extracted semantic content sufficient to improve downstream solving?}
}
\]

A distributed state can fail local necessity tests yet pass semantic sufficiency tests.

---

## 24. Identification boundary

Unlike the hybrid ON/OFF models in *Thinking to Recall*, this project compares separately deployed Instruct and Thinking checkpoints.

Therefore:

- same-checkpoint forced-trace comparisons within Thinking are the cleanest mechanism tests;
- Instruct transplantation tests portability/sufficiency;
- Instruct-vs-Thinking performance gaps remain deployed-variant comparisons.

Do not claim a pure causal "enable Thinking" switch.

---

## 25. Seed policy

For every new family-condition use:

\[
\boxed{5\text{ frozen seeds}.}
\]

Derive from:

`SHA256(stage13c-v1|family_id|condition|replicate)`

Use the same replicate indices across paired Thinking conditions and across paired Instruct conditions.

No best-of-five selection.

---

## 26. Statistical reporting

Independent unit:

\[
\boxed{\text{family}.}
\]

For each contrast report:

- family-level 5-seed accuracy;
- paired mean difference;
- 10,000 family-bootstrap percentile interval;
- positive / zero / negative family-effect counts;
- conservative technical-missingness bounds.

Seeds are not population-independent samples.

No prevalence claim from the 24-family mechanism cohort.

---

## 27. Technical validity

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

A cap hit with a clear unretracted answer remains scoreable.

Pre-outcome truncation is technical missingness.

Repetition/pathological reasoning remains model behavior.

If >20% technical missingness occurs in any intervention arm during a frozen first-8-family tranche:

\[
\boxed{\texttt{TECHNICAL\_STOP}}
\]

and halt before remaining scientific calls.

Do not change caps/prompts after the stop gate.

---

## 28. Scoring and audit

Score each intervention arm before opening paired contrasts.

Use the frozen MathVision answer-equivalence policy.

Perform:

- all ambiguity-triggered second reviews;
- deterministic 20% random second-pass review;
- exact input/token receipts.

Same-agent QC is not independent-rater reliability.

---

## 29. Compute estimate

Maximum new calls, assuming all 24 families are semantically eligible:

### Thinking

\[
24\times5\text{ conditions}\times5\text{ seeds}
=
600
\]

for:

- Native
- Short Dummy
- Long Dummy
- Derived
- Derived Dummy

### Instruct

\[
24\times4\times5
=
480
\]

for:

- Base
- Derived
- Dummy
- Shuffled

Maximum:

\[
\boxed{1080\text{ scientific calls}}
\]

plus technical validation.

Families with `NO_SAFE_DERIVED_CONTENT` skip semantic conditions.

Target:

\[
\boxed{<14\text{ GPU-hours}}
\]

Hard stop:

\[
\boxed{18\text{ GPU-hours}}
\]

unless separately approved.

---

## 30. Required figures

### Figure 13C-1 — Mechanism decomposition

Show:

\[
T_{\mathrm{SHORT}},
\quad
T_{\mathrm{LONG}},
\quad
T_{\mathrm{DERIVED}},
\quad
T_{\mathrm{NATIVE}}
\]

with paired family intervals.

### Figure 13C-2 — Computational-buffer effect

Show:

\[
T_{\mathrm{LONG}}-T_{\mathrm{SHORT}}
\]

and:

\[
T_{\mathrm{NATIVE}}-T_{\mathrm{LONG}}.
\]

### Figure 13C-3 — Same-checkpoint semantic effect

Show:

\[
T_{\mathrm{DERIVED}}
\quad\text{vs}\quad
T_{\mathrm{DERIVED\_DUMMY}}.
\]

### Figure 13C-4 — Portable derived priming

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

### Figure 13C-5 — Derived-content correctness

Secondary only, if denominator is sufficient.

---

## 31. Required artifacts

Produce:

1. `stage13c_post_evidence_mechanism_spec.md`
2. `stage13c_frozen24_manifest.json`
3. `stage13c_technical4_manifest.json`
4. `stage13c_source_trace_manifest.json`
5. `stage13c_derived_state_extractions.json`
6. `stage13c_derived_state_audit.json`
7. `stage13c_dummy_token_sequences.json`
8. `stage13c_seed_manifest.json`
9. `stage13c_forced_trace_technical_validation.json`
10. `stage13c_thinking_compute_results.parquet`
11. `stage13c_thinking_semantic_results.parquet`
12. `stage13c_instruct_priming_results.parquet`
13. `stage13c_scoring_audit.json`
14. `stage13c_family_level_effects.parquet`
15. `stage13c_missingness_bounds.json`
16. `stage13c_primary_inference.json`
17. `stage13c_decision.json`
18. `stage13c_resource_accounting.json`
19. `stage13c_summary.md`

Preserve all prior Stage 12 and Stage 13 artifacts unchanged.

---

## 32. Exactly one recommendation at completion

### If `COMPLEMENTARY_COMPUTE_AND_SEMANTICS`

Recommend:

> Use the confirmed decomposition as the final Thinking-mechanism result and stop further 4B role expansion.

### If `COMPUTATIONAL_BUFFER_ONLY`

Recommend:

> Test whether the same content-independent buffer effect appears in a matched text-only reasoning setting before making a modality-specific claim.

### If `DERIVED_STATE_PRIMING_ONLY`

Recommend:

> Treat task-specific semantic state construction as the primary post-evidence mechanism and validate it once on an independent fresh cohort.

### If `COMPUTE_PARTIAL_SEMANTICS_UNRESOLVED`

Recommend:

> Preserve the compute contribution and stop finer semantic localization unless an independent semantic extraction method becomes available.

### If `POST_EVIDENCE_MECHANISM_UNRESOLVED`

Recommend:

> Retain Stage 13A's confirmed post-evidence advantage as the strongest claim and do not expand the mechanism story.

Do not launch automatically.

---

## 33. Final decision target

Stage 13C exists to answer:

\[
\boxed{
\textbf{Why does Thinking help even after the correct visual evidence is already available?}
}
\]

The decomposition is:

\[
\boxed{
\text{post-evidence Thinking gain}
\overset{?}{=}
\text{content-independent computation}
+
\text{task-specific semantic state construction}
+
\text{unexplained residual}.
}
\]

The strongest positive pattern is:

\[
\boxed{
T_{\mathrm{LONG}}>T_{\mathrm{SHORT}}
}
\]

together with:

\[
\boxed{
T_{\mathrm{DERIVED}}>T_{\mathrm{DERIVED\_DUMMY}}
}
\]

and:

\[
\boxed{
I_{\mathrm{DERIVED}}>I_{\mathrm{DUMMY}},\ I_{\mathrm{SHUFFLED}}.
}
\]

That would support:

> **After visual evidence is equalized, Thinking can help through both additional reasoning-token computation and the construction of task-specific intermediate semantic state.**
