# Stage 12Y-S — What Does Thinking Do in Multimodal Math Reasoning?
## Evidence Recovery vs Equal-Evidence Reasoning vs Reasoning-State Construction

## 0. One-line objective

Directly decompose the role of the Qwen3-VL Thinking variant in multimodal math reasoning into three candidate functions:

\[
\boxed{
\text{visual evidence recovery}
\rightarrow
\text{reasoning from the same evidence}
\rightarrow
\text{construction of a useful intermediate reasoning state}
}
\]

Primary question:

\[
\boxed{
\textbf{When Thinking outperforms Instruct on a visual math problem, does it help because it
recovers the needed visual evidence, because it reasons better from the same evidence,
or because it constructs a better intermediate state from that evidence?}
}
\]

This is the multimodal analogue of the broader question raised by work such as *Empty Shelves or Lost Keys?*: what computational role does Thinking play?

The purpose is **not** to assume that the role is the same in factual QA and VLM reasoning. The purpose is to identify the VLM role empirically.

---

# 1. Why this is the next experiment

The existing Stage 12 results establish several pieces, but not yet a unified role for Thinking.

## 1.1 Visual evidence is a real bottleneck

The original developmental cohort showed that supplying correct task-critical visual evidence \(E^*\) rescued a substantial fraction of Native Instruct failures.

Stage 12X-S then reproduced this qualitatively on a fresh source-selected cohort:

\[
16/39
\]

complete native failures were rescued by the equal-evidence oracle.

Thus:

\[
\boxed{
\textbf{failure to recover/use the task-critical visual evidence is a substantial source of error.}
}
\]

---

## 1.2 Generic CoT is not the explanation

Prompted CoT on the same Instruct checkpoint did not reliably repair the dominant B1/B4 failures.

Therefore:

\[
\boxed{
\text{more explicit reasoning tokens}
\neq
\text{Thinking's full advantage}.
}
\]

---

## 1.3 Thinking-state production is promising but targeted

Stage 12U-S showed that on the developmental B4 \(C^-T^+\) cases:

\[
R_T\rightarrow T=5/5
\]

and:

\[
R_T\rightarrow I=4/5.
\]

This supports:

\[
\boxed{
\textbf{Thinking can produce an intermediate textual state that Instruct can use.}
}
\]

However:

- Stage 12V-S did not identify one necessary critical step;
- Stage 12W-S did not identify a robust cross-family block-level mechanism;
- Stage 12X-S could not independently re-test portability because fresh B4 \(C^-T^+\) yield was only 2.

Therefore the next experiment should not depend on rare B4 Thinking-only cases.

Instead, it should measure the role of Thinking **across the whole source-frozen math cohort**.

---

# 2. Conceptual decomposition

Define three functional stages.

## Role A — Visual evidence recovery

\[
\text{image}
\rightarrow
E^*
\]

Question:

> Does the Thinking checkpoint more reliably recover/report the task-critical visual facts?

---

## Role B — Equal-evidence downstream reasoning

\[
E^*
\rightarrow
\text{solution}
\]

Question:

> If both checkpoints receive the exact same correct textual evidence, does Thinking still outperform Instruct?

This removes visual evidence uncertainty.

---

## Role C — Reasoning-state construction

\[
E^*
\rightarrow
R_T
\rightarrow
\text{solution}
\]

Question:

> In cases where Thinking succeeds from the same \(E^*\) but Instruct fails, does the intermediate reasoning state produced by Thinking make Instruct succeed when transplanted?

This is the strongest test of:

\[
\boxed{
\textbf{Thinking as state construction}
}
\]

rather than merely better evidence access.

---

# 3. Core contrast with factual-QA Thinking

The experiment is motivated by the following conceptual contrast.

A simplified factual-QA role is:

\[
\text{stored information}
\rightarrow
\boxed{\text{access}}
\rightarrow
\text{answer}.
\]

Multimodal reasoning introduces an additional transformation problem:

\[
\text{visual input}
\rightarrow
\boxed{\text{recover task-relevant evidence}}
\rightarrow
\boxed{\text{construct task-specific derived state}}
\rightarrow
\text{answer}.
\]

Do **not** assume a strict LLM/VLM dichotomy.

The allowed goal is narrower:

> identify which of these functions is measurably associated with Thinking gains in multimodal math reasoning.

---

# 4. Cohort

Reuse the exact 96-family Stage 12X-S final-QC-passed cohort.

Reasons:

1. it was selected prospectively using source-only criteria;
2. all families are historically fresh relative to the developmental Stage 12 cohort;
3. all \(E^*\) annotations and oracle renderings are already frozen;
4. source selection did not depend on model outcomes;
5. reusing it avoids a second annotation-driven source-selection process.

This stage is a **paired role-decomposition study**, not another held-out replication claim.

Do not alter the 96-family membership.

---

# 5. Frozen information reused from Stage 12X-S

Reuse without modification:

- original images;
- original questions;
- gold answers;
- frozen \(E^*\);
- frozen evidence requests;
- exact equal-evidence oracle text;
- Stage 12X-S direct evidence probe from Instruct:
  \[
  E_I;
  \]
- Stage 12X-S Native Instruct image-task output:
  \[
  I_{\mathrm{img}};
  \]
- Stage 12X-S Equal-Evidence Instruct output:
  \[
  I_{E^*}.
  \]

The existing single-run outcomes are the **screening observations** only.

They are not sufficient by themselves for confirmatory role claims.

---

# 6. New Phase A conditions

Run three new conditions on all 96 families.

## A1 — Thinking evidence probe

\[
\boxed{
E_T
}
\]

- Qwen3-VL-4B-Thinking;
- original image present;
- same frozen evidence requests used for \(E_I\);
- no task-solving request;
- score the same required \(E^*\) atoms;
- use the pinned Thinking recipe.

Purpose:

\[
E_T \text{ vs } E_I
\]

measures demonstrated task-critical visual evidence recovery.

Important:

> This is demonstrated recovery/reporting, not proof of latent internal access.

---

## A2 — Thinking native image task

\[
\boxed{
T_{\mathrm{img}}
}
\]

- original image;
- original question;
- native Thinking checkpoint;
- no added suffix.

Purpose:

\[
T_{\mathrm{img}} \text{ vs } I_{\mathrm{img}}
\]

measures the native image-task variant gap.

---

## A3 — Thinking equal-evidence task

\[
\boxed{
T_{E^*}
}
\]

- no image;
- exact same frozen \(Q+E^*\) text used for \(I_{E^*}\);
- native Thinking checkpoint.

Purpose:

\[
T_{E^*} \text{ vs } I_{E^*}
\]

measures the Thinking-vs-Instruct gap after visual uncertainty is removed.

---

# 7. Model recipes

## Instruct

Pinned Qwen3-VL-4B-Instruct:

- temperature = 0.7
- top-p = 0.8
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 1.5
- max new tokens = 32,768

## Thinking

Pinned Qwen3-VL-4B-Thinking revision:

`1de27d8c51f12e819435303b9e84c4e25ba8401e`

- temperature = 1.0
- top-p = 0.95
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 0
- max new tokens = 81,920

Checkpoint, decoding, and output-budget differences remain explicit.

This experiment identifies **functional role differences between the deployed variants**, not a pure causal "Thinking switch."

---

# 8. Phase A scoring

Use the same pathology-aware validity rule:

\[
\texttt{TECHNICALLY\_VALID}
=
\texttt{INPUT\_VALID}
\land
\texttt{SCOREABLE}
\land
\neg\texttt{TRUNCATED\_BEFORE\_OUTCOME}.
\]

Repetition and long reasoning are scientific behavior.

For evidence probes:

\[
E_M^+=1
\]

iff all required atoms are correct.

For tasks:

- `CORRECT`
- `INCORRECT`
- `UNSCOREABLE_TECHNICAL`

Score A1/A2/A3 arm-by-arm before constructing role labels.

---

# 9. Population-level descriptive quantities

On common scoreable denominators report:

## Native image variant gap

\[
\boxed{
G_{\mathrm{img}}
=
Acc(T_{\mathrm{img}})
-
Acc(I_{\mathrm{img}})
}
\]

## Equal-evidence variant gap

\[
\boxed{
G_{E^*}
=
Acc(T_{E^*})
-
Acc(I_{E^*})
}
\]

## Direct evidence-recovery gap

\[
\boxed{
G_{\mathrm{access}}
=
Acc(E_T)
-
Acc(E_I)
}
\]

## Evidence-equalization attenuation

\[
\boxed{
A_{\mathrm{evidence}}
=
G_{\mathrm{img}}
-
G_{E^*}
}
\]

Interpret \(A_{\mathrm{evidence}}>0\) only descriptively:

> part of the native variant gap attenuates when task-critical evidence is textually equalized.

Do **not** call this formal causal mediation.

---

# 10. Native Thinking-only transition table

Among jointly scoreable native image cases satisfying:

\[
I_{\mathrm{img}}^-
\land
T_{\mathrm{img}}^+,
\]

classify each into one of four predeclared states.

## A — Gap collapses under gold evidence

\[
I_{E^*}^+
\]

Interpretation:

> the native Instruct failure is compatible with an evidence-side bottleneck.

If additionally:

\[
E_I^-
\land
E_T^+,
\]

this becomes strong evidence-access support.

---

## B — Gap persists under equal evidence

\[
I_{E^*}^-
\land
T_{E^*}^+.
\]

Interpretation:

\[
\boxed{
\textbf{Thinking retains an advantage even after visual evidence uncertainty is removed.}
}
\]

This is the primary downstream-reasoning stratum.

---

## C — Both fail under equal evidence

\[
I_{E^*}^-
\land
T_{E^*}^-.
\]

Interpretation:

> the native Thinking success is not reproduced from frozen \(E^*\) alone.

Possible explanations include richer image-side state, stochasticity, or incomplete \(E^*\) sufficiency for the Thinking computation.

Do not force an access/downstream label.

---

## D — Other / technically unresolved

Preserve missingness and unusual regressions explicitly.

---

# 11. Phase A screening labels

Define:

## `ACCESS_SCREEN_STRONG`

A family satisfies:

\[
I_{\mathrm{img}}^-,
\quad
T_{\mathrm{img}}^+,
\]

\[
I_{E^*}^+,
\]

and:

\[
E_I^-,
\quad
E_T^+.
\]

This is the cleanest screen for a Thinking-associated visual evidence-recovery role.

---

## `ACCESS_SCREEN_WEAK`

\[
I_{\mathrm{img}}^-,
\quad
T_{\mathrm{img}}^+,
\quad
I_{E^*}^+,
\]

without requiring probe discordance.

---

## `DOWNSTREAM_SCREEN`

\[
\boxed{
I_{E^*}^-,
\quad
T_{E^*}^+
}
\]

under identical frozen textual evidence.

Prefer the native-linked subset also satisfying:

\[
I_{\mathrm{img}}^-,
\quad
T_{\mathrm{img}}^+.
\]

---

# 12. Why Phase A is only a screen

The existing Instruct conditions are single historical runs, and Phase A Thinking runs are also single trajectories.

Therefore all mechanistic role claims require **fresh-seed confirmation**.

Phase A is used only to define candidate strata.

No final access/downstream claim is made from one-run discordances.

---

# 13. Phase B — Fresh-seed confirmation

Freeze candidate IDs immediately after Phase A scoring.

Within each stratum, order candidates by:

`SHA256(stage12ys-v1|role|family_id)`.

Confirm:

- up to 16 `ACCESS_SCREEN_STRONG` candidates;
- if fewer than 8 strong candidates exist, supplement with `ACCESS_SCREEN_WEAK` to a maximum of 16;
- up to 16 `DOWNSTREAM_SCREEN` candidates.

A family may participate in multiple descriptive strata if logically eligible, but duplicated calls must be reused, not regenerated.

---

# 14. Phase B seeds

Use:

\[
\boxed{
3 \text{ fresh frozen seeds per model-condition}
}
\]

derived prospectively from:

`SHA256(stage12ys-v1|family_id|condition|replicate)`.

Use the same replicate indices across the two checkpoints.

No best-of-three selection.

Family-level success:

\[
\boxed{
\ge2/3 \text{ correct}
}
\]

for task outputs and:

\[
\boxed{
\ge2/3 \text{ all-atoms-correct}
}
\]

for evidence probes.

---

# 15. Confirmatory access panel

For each access candidate rerun, with fresh seeds:

\[
E_I,\quad E_T,
\]

\[
I_{\mathrm{img}},\quad T_{\mathrm{img}},
\]

\[
I_{E^*},\quad T_{E^*}.
\]

All six arms use the frozen original inputs.

Define:

\[
\boxed{
\texttt{ACCESS\_ROLE\_SUPPORT}
}
\]

iff:

1. native:
   \[
   I_{\mathrm{img}}^-,
   \quad
   T_{\mathrm{img}}^+;
   \]
2. Instruct is rescued by equalized evidence:
   \[
   I_{E^*}^+;
   \]
3. direct evidence recovery differs:
   \[
   E_I^-,
   \quad
   E_T^+.
   \]

This supports:

> Thinking's native advantage on this item is associated with better demonstrated recovery of the task-critical visual evidence.

It does not prove hidden representation was absent in Instruct.

---

# 16. Confirmatory downstream panel

For each downstream candidate rerun:

\[
I_{E^*},\quad T_{E^*}
\]

with three fresh seeds.

Also rerun:

\[
I_{\mathrm{img}},\quad T_{\mathrm{img}}
\]

when the candidate was native-linked in Phase A.

Define:

\[
\boxed{
\texttt{DOWNSTREAM\_ROLE\_SUPPORT}
}
\]

iff:

\[
I_{E^*}^-,
\quad
T_{E^*}^+
\]

under the exact same textual \(E^*\) input on fresh seeds.

Define stronger:

\[
\boxed{
\texttt{NATIVE\_LINKED\_DOWNSTREAM\_SUPPORT}
}
\]

if additionally:

\[
I_{\mathrm{img}}^-,
\quad
T_{\mathrm{img}}^+.
\]

This is direct evidence that the Thinking advantage can persist **after visual evidence is equalized**.

---

# 17. Phase C — State-construction assay under equal evidence

This phase is the key new experiment.

Run it only on confirmed `DOWNSTREAM_ROLE_SUPPORT` families.

The source condition is:

\[
Q+E^*\rightarrow T^+.
\]

Thus the source Thinking trajectory is already **image-free**.

This removes visual-access uncertainty from the state-construction assay.

---

# 18. Source Thinking trace

For each confirmed downstream family, select the first successful fresh-seed \(T_{E^*}\) trajectory in ascending frozen replicate order.

Do not choose the "best" trace.

Construct:

\[
\boxed{
R_{T,E^*}^{safe}
}
\]

using the Stage 12U-S answer-safe rule:

> maximal visible Thinking reasoning prefix ending before the first explicit task-answer candidate or commitment.

Remove only model-control wrappers for cross-checkpoint canonicalization.

Before replay, freeze:

- prefix hash;
- cut point;
- token count;
- incidental gold-value flag;
- explicit-final absent;
- explicit-answer-candidate absent.

---

# 19. Phase C replay conditions

All conditions use the exact same:

\[
Q+E^*
\]

text and no image.

Run:

## C1 — Same-model textual-state sufficiency

\[
\boxed{
(Q+E^*)+R_{T,E^*}\rightarrow T
}
\]

## C2 — Cross-checkpoint state portability

\[
\boxed{
(Q+E^*)+R_{T,E^*}\rightarrow I
}
\]

## C3 — Instruct equal-evidence baseline

\[
\boxed{
Q+E^*\rightarrow I
}
\]

Use fresh replay seeds, not the source-screen outcome.

## C4 — Shuffled-state control

\[
\boxed{
(Q_i+E_i^*)+R_{T,E^*,j}\rightarrow I_i,
\quad j\neq i
}
\]

Use deterministic cyclic permutation among Phase C candidates.

No image is present in any Phase C condition.

---

# 20. Phase C replay seeds

Use:

\[
\boxed{
5 \text{ frozen seeds per condition}
}
\]

derived from:

`SHA256(stage12ys-v1|state-transfer|family_id|condition|replicate)`.

Family-level success:

\[
\boxed{
\ge3/5.
}
\]

Do not search seeds or prefixes.

---

# 21. State-construction support

Define:

\[
\boxed{
\texttt{STATE\_CONSTRUCTION\_SUPPORT}
}
\]

iff:

1. source family has confirmed:
   \[
   I_{E^*}^-,
   \quad
   T_{E^*}^+;
   \]
2. same-model replay:
   \[
   R_{T,E^*}\rightarrow T^+;
   \]
3. cross-checkpoint replay:
   \[
   R_{T,E^*}\rightarrow I^+;
   \]
4. equal-evidence Instruct baseline remains:
   \[
   Q+E^*\rightarrow I^-;
   \]
5. shuffled Thinking state fails:
   \[
   R_{T,E^*,shuffle}\rightarrow I^-.
   \]

This is the cleanest evidence for:

\[
\boxed{
\textbf{Thinking transforms already-available correct evidence into a more useful intermediate reasoning state.}
}
\]

Because both source and target receive the same frozen \(E^*\), this result cannot be explained by better image access in the replay assay.

---

# 22. Main role decomposition

The final analysis has three separate support counts.

## Access role

\[
N_{\mathrm{access}}
=
\#\texttt{ACCESS\_ROLE\_SUPPORT}.
\]

## Equal-evidence downstream role

\[
N_{\mathrm{downstream}}
=
\#\texttt{DOWNSTREAM\_ROLE\_SUPPORT}.
\]

## State-construction role

\[
N_{\mathrm{state}}
=
\#\texttt{STATE\_CONSTRUCTION\_SUPPORT}.
\]

These roles are not assumed to be mutually exclusive at the model-family level.

The goal is not to force one universal role.

---

# 23. Decision states

## `VISUAL_ACCESS_ROLE_SIGNAL`

Declare if:

- at least 5 access candidates receive fresh-seed confirmation;
- at least 60% satisfy `ACCESS_ROLE_SUPPORT`;
- and at least 3 independent families satisfy the full strong access signature.

Allowed interpretation:

> Thinking can improve multimodal math performance by improving demonstrated recovery of task-critical visual evidence.

---

## `EQUAL_EVIDENCE_REASONING_SIGNAL`

Declare if:

- at least 5 downstream candidates receive fresh-seed confirmation;
- at least 60% satisfy `DOWNSTREAM_ROLE_SUPPORT`;
- and at least 3 independent families remain Thinking-only under identical \(E^*\).

Allowed interpretation:

> Thinking's advantage is not limited to visual evidence recovery; it can persist when both checkpoints receive the same correct task-critical evidence.

---

## `STATE_CONSTRUCTION_ROLE_SIGNAL`

Declare if:

- at least 3 confirmed downstream families enter Phase C;
- at least 2 satisfy `STATE_CONSTRUCTION_SUPPORT`;
- and at least 60% of Phase C-eligible families with resolved controls satisfy it.

Allowed interpretation:

> Thinking can transform already-available task-critical evidence into an externalized intermediate reasoning state that enables the weaker Instruct checkpoint to solve the task.

---

## `MULTI_ROLE_THINKING_SIGNAL`

Declare if both:

- `VISUAL_ACCESS_ROLE_SIGNAL`;
- and `EQUAL_EVIDENCE_REASONING_SIGNAL`

are positive.

If state construction also passes, report it as the strongest downstream mechanistic support.

Interpretation:

> Thinking serves multiple functions in multimodal reasoning rather than one universal role.

---

## `ROLE_DECOMPOSITION_UNRESOLVED`

Declare if candidate yield or confirmation is insufficient for all three role signals.

Do not collapse low yield into a negative role claim.

---

# 24. Key paper-level comparisons

The most important figure should distinguish:

\[
\boxed{
\text{Thinking advantage before evidence equalization}
}
\]

from:

\[
\boxed{
\text{Thinking advantage after evidence equalization}.
}
\]

If:

\[
G_{\mathrm{img}} \gg G_{E^*},
\]

then evidence-side processes explain a substantial descriptive component of the native gap.

If:

\[
G_{E^*}>0
\]

with replicated T-only families, Thinking has a downstream role beyond visual evidence recovery.

If additionally:

\[
R_{T,E^*}\rightarrow I^+,
\]

then the downstream role includes **reasoning-state construction**.

---

# 25. What each outcome would mean

## Outcome 1 — Access dominates

Pattern:

\[
T_{\mathrm{img}}>I_{\mathrm{img}}
\]

but the gap largely collapses under:

\[
E^*.
\]

Together with:

\[
E_T>E_I,
\]

this supports:

> Thinking mainly helps the model recover task-relevant visual evidence in this cohort.

---

## Outcome 2 — Downstream gap remains

Pattern:

\[
T_{E^*}>I_{E^*}.
\]

This supports:

> Thinking remains useful after perceptual uncertainty is removed.

---

## Outcome 3 — State transfer works

Pattern:

\[
I_{E^*}^-,
\quad
T_{E^*}^+,
\]

then:

\[
R_{T,E^*}\rightarrow I^+.
\]

This supports the strongest claim:

> **Thinking constructs a more useful intermediate reasoning state from already-available evidence.**

---

## Outcome 4 — Both access and downstream signals

This is scientifically valuable.

Do not force a single role.

The correct claim becomes:

> Thinking contributes at multiple stages of multimodal reasoning.

---

# 26. Relation to the existing paper claims

A positive Stage 12Y-S can organize the current paper into a stronger hierarchy.

## Claim 1 — Where failures arise

Task-critical visual evidence recovery is a major failure bottleneck.

## Claim 2 — What Thinking does

Thinking can help at one or both of:

\[
\text{evidence recovery}
\]

and:

\[
\text{reasoning from the recovered evidence}.
\]

If Phase C is positive:

\[
\boxed{
\text{one downstream role is constructing a portable intermediate reasoning state}.
}
\]

## Claim 3 — How visual evidence enters computation

Existing mechanistic interventions show reasoning-conditioned target-specific visual retrieval and Value-rich/local carrier behavior.

This gives an integrated lifecycle:

\[
\boxed{
\text{reasoning demand}
\rightarrow
\text{visual evidence recovery}
\rightarrow
\text{derived reasoning-state construction}
\rightarrow
\text{downstream solution}.
}
\]

Only include the state-construction arrow as a broad Thinking-role claim if Stage 12Y-S supports it.

---

# 27. Important limitations

Do not claim:

- Thinking and Instruct differ only by reasoning mode;
- equal-evidence comparison is a causal post-training intervention;
- E-probe failure means the visual fact is absent from all internal states;
- all VLM Thinking gains have one role;
- text transfer identifies the complete neural mechanism;
- MathVision results automatically generalize to factual VQA or natural images.

This is initially a **multimodal math reasoning** claim.

---

# 28. Why this experiment is more informative than another B4 portability search

The previous held-out design required the rare conjunction:

\[
B4\land C^-\land T^+.
\]

Stage 12X-S produced only two such cases.

Stage 12Y-S instead obtains useful information from every family:

- evidence recovery comparison;
- native image-task comparison;
- equal-evidence comparison.

Rare transfer experiments are performed only after a broad downstream role is identified.

Thus the stage can answer the scientific question even if no large B4 Thinking-only subset appears.

---

# 29. Compute-efficient phase gates

## Phase A

Run all 96 new Thinking conditions:

\[
E_T,\quad T_{\mathrm{img}},\quad T_{E^*}.
\]

Total:

\[
\boxed{
288 \text{ new primary calls}
}
\]

with evidence-probe outputs expected to be shorter.

---

## Phase B

Fresh-seed confirmation only on screened role candidates.

Maximum unique candidate families:

\[
32
\]

before overlap.

Approximate hard maximum:

\[
\boxed{
32\times6\times3=576
}
\]

calls if all six arms are required for every candidate.

Reuse duplicate family-condition calls across strata.

---

## Phase C

For \(K\) confirmed downstream candidates:

\[
4\text{ conditions}\times5\text{ seeds}\times K
=
20K.
\]

If \(K>10\), freeze the first 10 under a predeclared hash order for Phase C.

---

# 30. Compute budget

Target:

\[
\boxed{
<12 \text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
16 \text{ GPU-hours}
}
\]

unless separately approved.

If Phase B candidate yield is very large, apply only the frozen candidate caps; do not enlarge compute based on observed effect size.

---

# 31. Required figures

## Figure Y1 — Three-stage role decomposition

```text
IMAGE
  |
  v
Task-critical evidence E*
  |
  v
Derived reasoning state
  |
  v
Answer

A: evidence recovery
B: equal-evidence reasoning
C: state construction
```

## Figure Y2 — Native vs equal-evidence model gap

Show:

\[
G_{\mathrm{img}}
\]

and:

\[
G_{E^*}.
\]

Also display:

\[
E_I \text{ vs } E_T.
\]

## Figure Y3 — Native Thinking-only decomposition

For:

\[
I_{\mathrm{img}}^-T_{\mathrm{img}}^+
\]

show counts of:

- gap collapses with \(E^*\);
- gap persists with \(E^*\);
- both fail with \(E^*\);
- unresolved.

## Figure Y4 — Confirmed role signatures

Per confirmed candidate show:

- evidence probe I/T;
- image task I/T;
- equal-evidence task I/T.

## Figure Y5 — Equal-evidence state construction

For Phase C families show:

- \(I_{E^*}\);
- \(T_{E^*}\);
- \(R_{T,E^*}\to T\);
- \(R_{T,E^*}\to I\);
- shuffled \(R_{T,E^*}\to I\).

---

# 32. Required artifacts

Produce:

1. `stage12ys_role_decomposition_spec.md`
2. `stage12ys_frozen96_manifest.json`
3. `stage12ys_reused_stage12x_inputs.json`
4. `stage12ys_phaseA_thinking_evidence_results.parquet`
5. `stage12ys_phaseA_thinking_image_results.parquet`
6. `stage12ys_phaseA_thinking_equal_evidence_results.parquet`
7. `stage12ys_phaseA_role_screen.parquet`
8. `stage12ys_phaseB_candidate_manifest.json`
9. `stage12ys_phaseB_seed_manifest.json`
10. `stage12ys_phaseB_confirmation_results.parquet`
11. `stage12ys_phaseB_role_labels.parquet`
12. `stage12ys_phaseC_candidate_manifest.json`
13. `stage12ys_phaseC_answer_safe_prefixes.json`
14. `stage12ys_phaseC_transfer_results.parquet`
15. `stage12ys_primary_inference.json`
16. `stage12ys_decision.json`
17. `stage12ys_resource_accounting.json`
18. `stage12ys_summary.md`

Preserve all prior Stage 12 artifacts and Stage 12X-S source/QC seals unchanged.

---

# 33. Exactly one recommendation at completion

## If `STATE_CONSTRUCTION_ROLE_SIGNAL`

Recommend:

> Repeat the same image-vs-equal-evidence role decomposition at one additional Qwen3-VL model scale to test whether state construction explains why Thinking is useful even in small VLMs.

## If `MULTI_ROLE_THINKING_SIGNAL` without state-construction transfer

Recommend:

> Replicate the access/downstream role mixture at one additional model scale before pursuing finer mechanisms.

## If only `VISUAL_ACCESS_ROLE_SIGNAL`

Recommend:

> Test whether the access-side Thinking advantage scales more strongly at small VLM sizes than equal-evidence reasoning advantage.

## If only `EQUAL_EVIDENCE_REASONING_SIGNAL`

Recommend:

> Focus the next mechanistic study entirely on post-evidence reasoning rather than image access.

## If `ROLE_DECOMPOSITION_UNRESOLVED`

Recommend:

> Stop role-mechanism expansion and retain the narrower supported claims about evidence bottlenecks and developmental state portability.

Do not launch automatically.

---

# 34. Final decision target

Stage 12Y-S exists to answer:

\[
\boxed{
\textbf{What role does Thinking play in multimodal math reasoning?}
}
\]

Specifically, distinguish:

\[
\boxed{
\textbf{Thinking as visual evidence recovery}
}
\]

from:

\[
\boxed{
\textbf{Thinking as better reasoning from the same evidence}
}
\]

and, when supported:

\[
\boxed{
\textbf{Thinking as construction of a better intermediate reasoning state}.
}
\]

The strongest possible result is:

\[
I_{E^*}^-,
\quad
T_{E^*}^+,
\quad
R_{T,E^*}\rightarrow I^+,
\]

because it shows that even after visual evidence is held fixed and made explicitly available, Thinking can create a reasoning state that enables the weaker Instruct checkpoint to solve the problem.

That would support a concise paper-level interpretation:

> **In multimodal math reasoning, Thinking is not merely an evidence-access mechanism; it can transform available visual evidence into a more useful state for downstream reasoning.**
