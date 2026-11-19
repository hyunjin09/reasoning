# Stage 12V-S — Localizing the Portable Thinking State

## 0. Objective

Starting from the Stage 12U-S **STATE_PRODUCTION_SIGNAL**, localize:

1. **when** a successful Thinking reasoning trace becomes sufficient for the Instruct checkpoint to solve the task without the image; and
2. **which newly produced intermediate deduction(s)** causally make that textual state portable.

Primary question:

\[
oxed{
	extbf{What does Thinking add to its reasoning trajectory that turns an Instruct-unsolvable state into an Instruct-solvable state?}
}
\]

The key transition is:

\[
R_T^{\mathrm{before}}\rightarrow I^-
\quad\longrightarrow\quad
R_T^{\mathrm{after}}\rightarrow I^+
\]

followed by causal ablation/editing of the content newly added between those two prefixes.

This stage studies **externalized textual reasoning states**, not all hidden-state computation.

---

## 1. Motivation

Stage 12U-S produced a strong targeted state-production result on five frozen B4 \(C^-T^+\) families:

\[
R_T\rightarrow T = 5/5
\]

\[
R_T\rightarrow I = 4/5.
\]

Question-only Instruct succeeded on:

\[
Q\rightarrow I = 0/5,
\]

and shuffled Thinking traces did not rescue Instruct.

Thus on four primary B4 families:

\[
oxed{
	extbf{Thinking produced a task-specific externalized reasoning state that the Instruct checkpoint could use to solve a problem it otherwise could not solve.}
}
\]

These are especially informative because B4 means:

\[
E^-O^-,
\]

so frozen correct \(E^*\) alone had already failed to rescue Native Instruct.

The unresolved question is:

\[
oxed{
	extbf{What information or derived computation inside that Thinking trace makes it portable?}
}
\]

---

## 2. Candidate paper claim

A positive result would support:

> **Thinking does more than recover raw visual facts: it transforms them into task-specific intermediate deductions that causally make downstream solution computation accessible to the Instruct checkpoint.**

Use this only for the targeted production-support cohort unless later replicated.

---

## 3. Primary cohort

Use exactly the four Stage 12U-S B4 families classified as:

\[
oxed{	exttt{PRODUCTION\_SUPPORT}}
\]

Call:

\[
oxed{\mathcal P_{\mathrm{portable}},\quad n=4.}
\]

These families satisfy:

- Native Instruct failure;
- prompted-CoT failure;
- native Thinking success;
- historical correct-\(E^*\) Instruct oracle failure;
- image-free \(R_T\rightarrow T\) success;
- image-free \(R_T\rightarrow I\) success;
- image-free \(Q\rightarrow I\) failure.

Do not alter this cohort after localization begins.

Preserve the fifth B4 \(C^-T^+\) family that did not meet production support as a descriptive negative control only.

---

## 4. Frozen source traces

Reuse the exact successful Thinking source traces from Stage 12U-S.

Do not regenerate Thinking reasoning.

Reuse:

- original question;
- original Thinking trace;
- Stage 12U-S canonicalization;
- answer-leak audit;
- source trace hashes;
- final answer-safe prefix.

All scientific replays in this stage are image-free.

---

## 5. Semantic-step segmentation

Before any new replay outcome is generated, segment each answer-safe Thinking prefix into:

\[
S_1,S_2,\ldots,S_m
\]

where each \(S_k\) is one coherent reasoning action.

Preferred boundaries:

- paragraph;
- sentence;
- displayed equation block;
- numbered step.

Possible step roles:

- reading/binding a visual relation;
- defining an entity/variable;
- deriving a relation;
- computing an intermediate value;
- introducing a constraint;
- resolving ambiguity;
- choosing a subproblem;
- combining earlier results;
- concluding an intermediate result.

Do not define boundaries based on replay outcomes.

---

## 6. Step annotation

Assign one primary semantic category to every step before replay:

- `VISUAL_EVIDENCE`
- `ENTITY_BINDING`
- `REPRESENTATION_SETUP`
- `DERIVED_RELATION`
- `INTERMEDIATE_CALCULATION`
- `SUBGOAL_CONCLUSION`
- `CONSISTENCY_CHECK`
- `REINTERPRETATION`
- `META_REASONING`
- `OTHER`

Also record whether the step:

- introduces a new factual proposition;
- is directly image-derived or derived;
- depends on frozen \(E^*\);
- introduces a new numeric/symbolic value;
- corrects an earlier error;
- restates prior content.

---

## 7. Prefix family

Define cumulative prefixes:

\[
P_k=S_1\oplus S_2\oplus\cdots\oplus S_k.
\]

All prefixes:

- use no image;
- retain the exact original question;
- use Instruct assistant-prefix continuation;
- contain no explicit final-answer candidate;
- preserve original Thinking wording exactly.

The Stage 12U-S portable prefix is \(P_m\).

---

## 8. Phase A — Coarse localization

For each primary family choose deterministic anchors at approximately:

\[
0,20,40,60,80,100\%
\]

of semantic-step count, snapped to actual boundaries.

Always include:

- \(P_0\): question only;
- \(P_m\): full portable prefix.

Run each prefix into Instruct with:

\[
oxed{3\text{ frozen seeds}}
\]

derived prospectively from:

`SHA256(stage12vs-v1|family_id|phaseA|step_index|replicate)`.

Item-level success:

\[
oxed{\ge2/3\text{ correct continuations}.}
\]

No best-of-three selection.

---

## 9. Replication gate

Localization is valid for a family only if:

\[
P_0\rightarrow I^-
\]

and:

\[
P_m\rightarrow I^+.
\]

If more than one of the four primary families fails to replicate full-prefix portability:

\[
oxed{	exttt{PORTABILITY\_UNSTABLE}}
\]

and stop before content ablation.

No seed search or prefix repair.

---

## 10. Phase B — Fine localization

Find the earliest coarse interval:

\[
[P_a,P_b]
\]

with:

\[
P_a\rightarrow I^-,
\qquad
P_b\rightarrow I^+.
\]

Apply deterministic binary search over semantic-step boundaries until adjacent prefixes are found:

\[
oxed{
P_{k-1}\rightarrow I^-,
\qquad
P_k\rightarrow I^+.
}
\]

Call \(S_k\):

\[
oxed{	exttt{PORTABILITY\_STEP}}.
\]

Use 3 frozen seeds at every tested boundary.

---

## 11. Stability rule

A transition at \(k\) is `STABLE` only if:

1. \(P_{k-1}\) is majority incorrect;
2. \(P_k\) is majority correct;
3. at least one later tested prefix remains majority correct.

If success repeatedly appears and disappears, label:

\[
	exttt{NONMONOTONIC\_PORTABILITY}
\]

and do not claim a sharp state transition.

---

## 12. Thinking-side adjacent-prefix check

After localizing the Instruct transition, replay:

\[
P_{k-1}\rightarrow T
\]

and:

\[
P_k\rightarrow T
\]

with 3 frozen seeds.

Interpretation:

### Pattern A

\[
P_{k-1}\rightarrow T^-,
\quad
P_k\rightarrow T^+.
\]

The new step creates an answer-sufficient textual state for both checkpoints.

### Pattern B

\[
P_{k-1}\rightarrow T^+,
\quad
P_{k-1}\rightarrow I^-,
\]

then:

\[
P_k\rightarrow I^+.
\]

Thinking could already use the earlier state, while Instruct becomes able to use it only after additional externalization.

---

## 13. Phase C — Critical-step interventions

For every stable transition, intervene on \(S_k\).

All intervention texts are frozen before generation.

Use 3 seeds per condition.

### C1 — Critical-step deletion

Remove \(S_k\) from \(P_k\).

Primary necessity signature:

\[
P_k\rightarrow I^+
\quad\text{but}\quad
P_k^{DROP}\rightarrow I^-.
\]

### C2 — Semantic counterfactual

Minimally alter the semantic conclusion of \(S_k\) while preserving syntax, entities where possible, approximate length, and style.

Examples:

- change a derived quantity;
- invert a relation;
- swap a binding;
- alter a geometric relation;
- change one inferred constraint.

Do not insert the final answer.

Primary content-sensitive signature:

\[
P_k\rightarrow I^+
\quad\text{but}\quad
P_k^{CF}\rightarrow I^- \text{ or follows the counterfactual}.
\]

### C3 — Semantics-preserving paraphrase

Rewrite \(S_k\) while preserving its proposition exactly.

Desired control:

\[
P_k^{PARA}\rightarrow I^+.
\]

### C4 — Matched noncritical deletion

Choose an earlier noncritical step with nearest token length to \(S_k\), ties broken by earliest position.

Delete that step from \(P_k\).

Desired specificity:

\[
P_k^{DROP}\rightarrow I^-,
\qquad
P_k^{CTRL\_DROP}\rightarrow I^+.
\]

### C5 — Replicated raw-evidence control

Rerun:

\[
Q+E^*\rightarrow I
\]

with 3 fresh frozen seeds using the frozen Stage 12B-S oracle text.

The historical B4 label is never changed.

Strong derived-state pattern:

\[
E^*\rightarrow I^-,
\qquad
P_k\rightarrow I^+.
\]

---

## 14. Optional evidence-plus-step test

Run only if C1–C5 finish within budget:

\[
Q+E^*+S_k\rightarrow I.
\]

If successful:

\[
oxed{
E^*+S_k\text{ approximately summarizes the portable state.}
}
\]

If unsuccessful, broader accumulated context is required.

This condition is secondary.

---

## 15. Primary endpoints

### V-P1 — Portability transition localization

Number of families with:

\[
P_{k-1}\rightarrow I^-,
\quad
P_k\rightarrow I^+.
\]

Target: at least 3/4.

### V-P2 — Critical-step necessity

Count families where:

\[
P_k^+,
\quad
P_k^{DROP-}.
\]

### V-P3 — Semantic sensitivity

Count families where:

\[
P_k^+,
\quad
P_k^{CF-}\text{ or CF-following}.
\]

### V-P4 — Paraphrase preservation

Count:

\[
P_k^{PARA+}.
\]

### V-P5 — Specificity

Count families where:

\[
P_k^{DROP-}
\]

but:

\[
P_k^{CTRL\_DROP+}.
\]

---

## 16. Causal portability signature

A family satisfies:

\[
oxed{	exttt{CAUSAL\_PORTABILITY\_STEP}}
\]

if all hold:

1. stable adjacent transition;
2. critical deletion breaks portability;
3. semantic counterfactual breaks or redirects portability;
4. semantics-preserving paraphrase retains portability;
5. matched noncritical deletion preserves portability.

This is the strongest evidence that a **specific semantic intermediate deduction** makes the Thinking state portable to Instruct.

---

## 17. Step-type analysis

For every localized portability step report its pre-frozen semantic category.

Do not force a shared category.

A common mechanism may be claimed only if at least 3 localized causal steps share a coherent functional property.

The likely higher-level distinction is:

\[
oxed{
\text{raw visual evidence}
\rightarrow
\text{task-specific derived reasoning state}
}
\]

even if surface step types differ.

---

## 18. Decision states

### `DERIVED_STATE_CAUSAL_SIGNAL`

Declare if:

1. stable adjacent portability is localized in at least 3/4;
2. at least 3 families satisfy `CAUSAL_PORTABILITY_STEP`;
3. replicated \(E^*\)-only Instruct control remains majority incorrect in at least 3 of those families.

Interpretation:

> specific Thinking-derived intermediate reasoning content, beyond raw task-critical visual facts, causally makes the state usable by Instruct.

### `PORTABILITY_LOCALIZED_BUT_DISTRIBUTED`

Stable transition in at least 3/4, but fewer than 3 causal single-step signatures.

Interpretation:

> portability emerges at identifiable positions but depends on distributed accumulated context rather than one local deduction.

### `PORTABILITY_NONMONOTONIC`

Fewer than 3 families show a stable adjacent transition because success repeatedly appears/disappears.

### `PORTABILITY_UNSTABLE`

Full Stage 12U-S portability fails to replicate on more than one primary family.

---

## 19. Allowed claim under a strong positive result

> **Thinking does more than recover raw visual facts: it transforms them into task-specific intermediate deductions that causally make downstream solution computation accessible to the Instruct checkpoint.**

This is targeted mechanistic localization, not a benchmark-wide prevalence claim.

---

## 20. What this stage does not prove

Do not claim:

- all Thinking gains are caused by identified textual deductions;
- the identified text step is identical to a hidden-state mechanism;
- checkpoint differences are caused purely by reasoning mode;
- the same step type generalizes to all VLM tasks;
- four targeted families estimate population prevalence.

---

## 21. Connection to Claims 2 and 3

A positive result would tighten the lifecycle:

\[
\text{reasoning-conditioned visual retrieval}
\rightarrow
\text{evidence acquisition}
\rightarrow
\boxed{\text{derived portable reasoning state}}
\rightarrow
\text{later computation}.
\]

The new contribution would go beyond:

> generated text can carry evidence

to:

> **specific derived reasoning content in the Thinking trace can be causally necessary for making that state usable by a weaker downstream solver.**

---

## 22. Negative-result interpretation

If localization works but single-step ablations do not:

> portability is likely distributed across accumulated reasoning context.

If semantic counterfactuals do not matter:

- redundancy;
- self-repair;
- distributed state;
- positional coincidence rather than causal content

remain alternatives.

If replicated \(E^*\)-only control sometimes succeeds, keep the frozen historical B4 label but report stochastic evidence sufficiency and weaken “beyond \(E^*\)” claims for that family.

---

## 23. Technical validity

All conditions are image-free.

Valid if:

\[
	exttt{INPUT\_VALID}
\land
	exttt{SCOREABLE}
\land
\neg	exttt{TRUNCATED\_BEFORE\_OUTCOME}.
\]

Repetition/reopening are behaviors, not exclusions.

Instruct recipe:

- temperature 0.7
- top-p 0.8
- top-k 20
- repetition penalty 1.0
- presence penalty 1.5
- max new tokens 32,768

Thinking adjacent-prefix checks:

- temperature 1.0
- top-p 0.95
- top-k 20
- repetition penalty 1.0
- presence penalty 0
- max new tokens 81,920

---

## 24. Statistics

Independent unit:

\[
oxed{	ext{family}}
\]

Each replay condition uses 3 frozen seeds and item-level majority success.

Because \(n=4\):

- report exact family counts;
- all seed outcomes;
- descriptive exact intervals only.

No asymptotic significance claims.

---

## 25. Compute budget

Approximate upper bounds:

- coarse localization: 72 Instruct calls;
- fine localization: up to 48 additional Instruct calls;
- Thinking adjacent checks: up to 24 calls;
- five content interventions: up to 60 Instruct calls;
- optional \(E^*+S_k\): 12 calls.

Target:

\[
oxed{<5\text{ GPU-hours}}
\]

Hard stop:

\[
oxed{7\text{ GPU-hours}}
\]

unless separately approved.

Do not run hidden-state interventions in this stage.

---

## 26. Required figures

### Figure V1 — Portability emergence along Thinking trace

For each family:

- x-axis: semantic-step index;
- y-axis: empirical Instruct success over 3 seeds.

Highlight earliest stable transition.

### Figure V2 — Before vs after portability step

\[
P_{k-1}\rightarrow I
\quad\text{vs}\quad
P_k\rightarrow I.
\]

### Figure V3 — Content intervention panel

Show:

- original;
- DROP;
- counterfactual;
- paraphrase;
- matched-control deletion;
- \(E^*\)-only.

### Figure V4 — Portability-step semantic roles

Summarize the type of each localized critical step.

---

## 27. Required artifacts

Produce:

1. `stage12vs_portable_state_localization_spec.md`
2. `stage12vs_primary_manifest.json`
3. `stage12vs_semantic_steps.json`
4. `stage12vs_step_annotations.json`
5. `stage12vs_coarse_prefix_manifest.json`
6. `stage12vs_coarse_results.parquet`
7. `stage12vs_fine_localization.json`
8. `stage12vs_adjacent_thinking_checks.parquet`
9. `stage12vs_critical_step_interventions.json`
10. `stage12vs_content_ablation_results.parquet`
11. `stage12vs_replicated_evidence_oracle.parquet`
12. optional `stage12vs_evidence_plus_step_results.parquet`
13. `stage12vs_primary_inference.json`
14. `stage12vs_decision.json`
15. `stage12vs_resource_accounting.json`
16. `stage12vs_summary.md`

Preserve all prior Stage 12 artifacts unchanged.

---

## 28. Exactly one recommendation at completion

### If `DERIVED_STATE_CAUSAL_SIGNAL`

Recommend:

> Compare the localized portable deductions to the causal visual-retrieval and Value-transfer events in the same trajectories to connect evidence acquisition to portable reasoning-state construction.

### If `PORTABILITY_LOCALIZED_BUT_DISTRIBUTED`

Recommend:

> Test block-wise reasoning-prefix necessity rather than single-step necessity.

### If `PORTABILITY_NONMONOTONIC`

Recommend:

> Characterize why textual-state usability appears and disappears before attempting hidden-state interventions.

### If `PORTABILITY_UNSTABLE`

Recommend:

> Stop fine localization and retain Stage 12U-S state production as the strongest supported result.

Do not launch automatically.

---

## 29. Final decision target

Stage 12V-S asks:

\[
oxed{
	extbf{Which specific Thinking-derived reasoning content converts a state that Instruct cannot use into a state that Instruct can use?}
}
\]

The decisive pattern is:

\[
P_{k-1}\rightarrow I^-
\longrightarrow
P_k\rightarrow I^+
\]

followed by:

\[
oxed{
	ext{critical deletion / semantic edit destroys portability, while paraphrase and matched-control deletion preserve it.}
}
\]

A positive result would move the paper from:

> Thinking produces better reasoning states

to:

> **Thinking constructs specific derived intermediate states that causally enable downstream solution computation.**
