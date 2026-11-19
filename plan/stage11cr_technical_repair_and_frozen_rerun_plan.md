# Stage 11C-R — Technical Repair and Frozen Rerun of Thinking-vs-Instruct Lifecycle Localization

## 0. One-line objective

Repair the **completion-validity failure** that prevented Stage 11C from reaching an interpretable native Thinking-vs-Instruct comparison, then rerun the **already-frozen Stage 11C scientific design without changing the cohort, \(E^*\), endpoints, or hypotheses**.

Primary technical question:

\[
\boxed{
\textbf{Can we reproduce a known-good Qwen3-VL-2B completion regime and identify
the execution discrepancy that caused Stage 11C to loop/nonterminate?}
}
\]

Primary scientific question, only after technical repair passes:

\[
\boxed{
\textbf{Relative to Instruct Direct, does the Thinking variant gain mainly through
visual-evidence acquisition/access, downstream reasoning after evidence is known,
or both?}
}
\]

This is a **technical repair + frozen rerun**, not a new benchmark search and not a redesign of the scientific hypothesis.

---

# 1. Why a rerun is justified

Stage 11C did **not** produce a scientific null.

It stopped at a prespecified completion-validity gate before estimating:

\[
P1 = G_{TD}^{N}
\]

\[
P2 = G_{TD}^{O}
\]

\[
P3 = \Delta G_{TD}.
\]

The failure was technical/completion-limited:

- 12/12 Thinking calibration cases hit the common token cap;
- 11/12 Direct calibration cases hit the common token cap;
- in the first 16 frozen primary families:
  - Thinking: 16/16 cap hits, 16/16 no committed final;
  - Direct: 15/16 cap hits, 10/16 no committed final.

Therefore the scientific question was never validly tested.

The correct next step is not:

> change the benchmark until the desired gap appears.

It is:

> identify and repair the execution/completion discrepancy, then rerun the exact frozen scientific design.

---

# 2. What must remain frozen

The following Stage 11C scientific objects must remain unchanged.

## Cohort

Reuse exactly:

- 120 source-reviewed \(E^*\)-eligible held-out families;
- 80 frozen primary families;
- 40 frozen reserve families.

No new family may be added.

No family may be removed based on Stage 11C output behavior.

The 16 previously executed primary cases remain in the primary cohort.

## Evidence

Reuse exactly:

- frozen \(E^*\) for every family;
- frozen \(E^*\) sufficiency judgments;
- frozen neutral-control subset;
- frozen CoT subset;
- frozen native-state subset.

No post-outcome \(E^*\) repair.

## Scientific endpoints

Reuse exactly the Stage 11C primary endpoints:

\[
\boxed{
P1 = G_{TD}^{N}=Acc_T^N-Acc_D^N
}
\]

\[
\boxed{
P2 = G_{TD}^{O}=Acc_T^O-Acc_D^O
}
\]

\[
\boxed{
P3 = \Delta G_{TD}=G_{TD}^{N}-G_{TD}^{O}
}
\]

No new primary endpoint may be introduced after the repair.

## Scientific gates

Retain the original logic:

1. valid native Thinking-vs-Direct performance regime;
2. meaningful native gap;
3. oracle validity;
4. gap localization;
5. optional short CoT control only under the original conditional logic.

---

# 3. What may change

Only the **technical execution protocol required to restore valid completion behavior** may change.

Permitted repair dimensions include:

- exact chat/template construction;
- BOS/EOS/stop-token handling;
- `max_new_tokens` vs total sequence-length semantics;
- generation stopping criteria;
- tokenizer/model revision mismatch;
- image-input formatting;
- modality tag construction;
- generation kwargs;
- repetition penalty if it differs from the known-good protocol;
- sampling vs greedy if the historical known-good protocol differs;
- attention backend if the known-good protocol requires it;
- cache implementation;
- single-item vs historical batch execution path;
- response postprocessing if it affects stopping detection.

Changes are allowed only when justified by **technical reproduction evidence**, not by accuracy or T-D performance.

---

# 4. Forbidden changes

Do **not**:

- change the benchmark;
- alter difficulty selection;
- replace Qwen3-VL-2B with another model;
- select new favorable examples;
- modify \(E^*\);
- increase only one mode's token budget;
- select a protocol based on which one improves Thinking accuracy;
- inspect oracle outcomes before native technical validity passes;
- redefine the native performance gate after seeing rerun outcomes;
- change prompts semantically to make the task easier;
- search multiple execution protocols and choose the one with the largest T-D gap.

The repair target is:

\[
\boxed{
\text{normal, reproducible completion behavior}
}
\]

not:

\[
\text{larger Thinking advantage}.
\]

---

# 5. Phase R0 — Historical known-good reconstruction

Before any new scientific rerun, reconstruct the exact execution recipes from prior project artifacts.

Use at least two known-good sources if available:

1. Stage 9A Qwen3-VL-2B Thinking / Instruct runs with normal answer completion;
2. any other earlier Qwen3-VL-2B run that reliably produced committed answers under comparable MathVision inputs.

Create a machine-readable comparison table for:

- model revision;
- tokenizer revision;
- processor revision;
- chat template;
- system/user prompt formatting;
- image insertion format;
- BOS/EOS IDs;
- stop-token IDs;
- `max_new_tokens`;
- total context limit;
- decoding mode;
- temperature;
- top-p/top-k;
- repetition penalty;
- cache settings;
- batch size;
- attention backend;
- image preprocessing;
- answer extraction;
- generation termination rule.

Do not infer missing values.

If an exact historical field cannot be recovered, mark it `UNKNOWN`.

---

# 6. Phase R1 — Fixed known-good reproduction set

Freeze exactly:

\[
\boxed{
12 \text{ known-good historical cases}
}
\]

before testing candidate repairs.

Target composition:

- 6 historical Thinking cases;
- 6 historical Instruct Direct cases;
- all previously observed to reach a committed final answer under a validated run.

Prefer cases with saved token sequences/logits.

These cases are **technical validation only**.

They must not overlap the 80 Stage 11C primary families if avoidable.

---

# 7. Reproduction criterion

The first goal is not exact accuracy reproduction.

The first goal is to recover normal generation behavior.

For each known-good case measure:

- EOS / valid stop reached;
- committed final answer present;
- generated length;
- prefix-token identity;
- first divergence token relative to historical output, if exact replay is possible;
- repetition/loop indicators;
- cap hit;
- logits at fixed checkpoints if historical logits exist.

## Exact-replay tier

Where deterministic historical replay is possible, require exact token identity.

## Behavioral-reproduction tier

Where exact replay is impossible because of historical nondeterminism/backend differences, require:

- no pathological long repetition;
- committed final answer;
- no cap hit under the historical budget;
- broadly similar output length class.

Do not require matching correctness for technical validation.

---

# 8. Phase R2 — Discrepancy audit

Construct a finite discrepancy matrix between:

- `KNOWN_GOOD`
- `STAGE11C_FAILED`

Candidate dimensions must be evaluated **one at a time where possible**.

Priority order:

1. chat/template construction;
2. EOS / stop-token handling;
3. generation-length semantics;
4. generation kwargs;
5. tokenizer/model/processor revision;
6. image/modality formatting;
7. cache path;
8. attention backend;
9. batch behavior;
10. postprocessing/stopping detection.

For each dimension record:

- historical value;
- Stage 11C value;
- whether values differ;
- whether restoring the historical value improves completion behavior;
- whether exact replay improves;
- whether any new divergence appears.

No scientific accuracy labels should be shown during this audit.

---

# 9. Candidate repair selection

A repaired protocol may be chosen only using technical criteria.

## Required criteria

On the 12 fixed known-good cases:

\[
\boxed{
\text{cap-hit rate} \le 1/12
}
\]

and:

\[
\boxed{
\text{committed-final rate} \ge 10/12.
}
\]

Also require:

- no obvious pathological repetition in >1/12;
- no mode-specific catastrophic difference;
- no image-input validation failures.

If several protocols pass, choose by this fixed priority:

1. exact historical protocol;
2. smallest number of deviations from historical protocol;
3. highest exact token reproduction;
4. lowest cap-hit rate;
5. shortest median excess generation length.

Do **not** use task correctness or T-D gap for protocol choice.

---

# 10. If no repair passes

If no candidate protocol meets the technical gate:

\[
\boxed{
\textbf{STOP Stage 11C-R}
}
\]

Conclusion:

> The project could not restore a valid Qwen3-VL-2B completion regime for the frozen Stage 11C assay.

Do not:

- run the primary cohort;
- run the oracle;
- search another benchmark;
- switch models;
- increase the cap indefinitely.

This is a technical closure, not a mechanism result.

---

# 11. Phase R3 — Frozen technical validation on non-primary Stage 11C cases

If a repair protocol passes known-good reproduction, validate it on:

\[
\boxed{
12 \text{ frozen non-primary Stage 11C cases}
}
\]

drawn from the reserve-compatible / technical pool.

Run both:

- Thinking;
- Instruct Direct.

Use the single frozen repaired protocol.

## Required validation gate

Across 24 calls:

- total cap-hit rate:
  \[
  \boxed{<15\%}
  \]
- each mode cap-hit rate:
  \[
  \boxed{<20\%}
  \]
- committed-final rate in each mode:
  \[
  \boxed{\ge75\%}
  \]
- no severe repetition pathology imbalance between modes.

If this gate fails, STOP before scientific rerun.

---

# 12. Generation budget after repair

Do not automatically inherit 8192.

Use the known-good repaired protocol's historical/common budget.

If a cap must be chosen, use exactly two predeclared candidates:

\[
4096,\quad8192.
\]

Choose the smallest common cap meeting the R3 completion gate.

Do not test higher caps unless historical known-good execution explicitly used them.

A longer cap is not a repair for looping behavior.

---

# 13. Scientific rerun identity

Once the technical protocol is frozen:

\[
\boxed{
\textbf{the scientific design reverts to the original Stage 11C plan}
}
\]

The rerun is labeled:

\[
\boxed{
\textbf{Stage 11C-R}
}
\]

All old Stage 11C outputs remain preserved as invalid technical-run evidence.

They are not pooled with repaired-run scientific outcomes.

---

# 14. Phase S1 — Re-run all 80 primary native T/D conditions

Run from scratch under the repaired protocol:

- `N-T`: native Thinking;
- `N-D`: Instruct Direct.

For all:

\[
\boxed{
80 \text{ frozen primary families}
}
\]

including the 16 previously attempted families.

Do not reuse old invalid Stage 11C generations.

---

# 15. Native validity gate

Before computing P1, check:

## Completion validity

Each mode:

\[
\boxed{
\text{cap-hit rate}<20\%
}
\]

and:

\[
\boxed{
\text{committed-final rate}\ge75\%.
}
\]

## Severe imbalance check

Absolute difference in committed-final rate:

\[
\boxed{
<20\text{ pp}
}
\]

between Thinking and Direct.

If this validity gate fails:

\[
\boxed{
\text{STOP before oracle}
}
\]

and do not interpret the native gap.

---

# 16. Native performance gate

Only after completion validity passes, compute:

\[
P1=G_{TD}^{N}.
\]

Proceed to oracle only if:

1. Thinking accuracy:
   \[
   \boxed{\ge25\%}
   \]

2. Direct accuracy:
   \[
   \boxed{\ge10\%}
   \]

3. native point-estimate gap:
   \[
   \boxed{\ge10\text{ pp}}
   \]

4. at least:
   \[
   \boxed{12}
   \]
   Thinking-correct / Direct-failed families.

If this gate fails:

> The frozen cohort does not provide an informative Thinking-vs-Direct performance advantage.

STOP Claim 3 without another benchmark search.

---

# 17. Phase S2 — Equal-Evidence Oracle

If the native gate passes, use the exact frozen \(E^*\).

For all 80 primary families:

## O-T

Thinking, text-only:

\[
\text{question} + E^*.
\]

## O-D

Instruct Direct, text-only:

\[
\text{question} + E^*.
\]

No image.

No multimodal cache.

No hidden-state transfer.

Evidence serialization remains identical to Stage 11C.

---

# 18. Oracle validity

Require:

- same \(E^*\) across T/D;
- no answer leakage;
- no image input;
- no severe completion imbalance;
- cap-hit rate <20% in each oracle arm;
- committed-final rate ≥75% in each oracle arm.

If invalid:

\[
\boxed{
\text{do not interpret P2/P3}
}
\]

Stop the oracle branch.

---

# 19. Primary scientific endpoints

Exactly as originally frozen.

## P1 — Native T-D gap

\[
\boxed{
P1
=
Acc_T^N-Acc_D^N
}
\]

## P2 — Oracle residual T-D gap

\[
\boxed{
P2
=
Acc_T^O-Acc_D^O
}
\]

## P3 — Gap closure

\[
\boxed{
P3
=
P1-P2
}
\]

No fourth primary endpoint.

---

# 20. Interpretation margins

Retain the original Stage 11C practical margins.

## Meaningful native gap

\[
\boxed{
P1\ge10\text{ pp}
}
\]

## Meaningful upstream/evidence contribution

\[
\boxed{
P3\ge5\text{ pp}
}
\]

and:

\[
\boxed{
P3/P1\ge0.35
}
\]

when \(P1>0\).

## Meaningful residual downstream gap

\[
\boxed{
P2\ge5\text{ pp}
}
\]

Use uncertainty intervals in addition to point margins.

---

# 21. Scientific outcome logic

## Outcome A — Upstream-dominant

\[
P1>0,\quad P3\text{ meaningfully positive},\quad P2\text{ small}.
\]

Supported:

> **A large component of the Thinking variant's advantage lies upstream of downstream reasoning over correct evidence, implicating visual-evidence acquisition/access.**

## Outcome B — Downstream-dominant

\[
P1>0,\quad P2\text{ meaningfully positive},\quad P3\text{ small}.
\]

Supported:

> **The Thinking variant retains most of its advantage after task-critical visual evidence is equalized, localizing much of the gain downstream of visual evidence acquisition.**

## Outcome C — Mixed

\[
P1>0,\quad P2>0,\quad P3>0
\]

with both P2 and P3 practically meaningful.

Supported:

> **Thinking improves both visual-evidence acquisition/access and downstream reasoning over already-correct evidence.**

## Outcome D — No native gap

No Claim 3 mechanism localization.

Stop.

## Outcome E — Oracle invalid

No Claim 3 mechanism localization.

Stop.

---

# 22. Phase S3 — Neutral text control

Run only if oracle is valid.

Reuse the exact frozen Stage 11C 24-family neutral subset.

Conditions:

- `NEUTRAL-T`
- `NEUTRAL-D`

Use the repaired execution protocol.

Purpose:

> distinguish evidence-specific oracle gains from generic extra-text scaffolding.

This remains secondary.

---

# 23. Phase S4 — Short CoT control

Run only if the original conditional trigger is met:

- native gate passes;
- oracle valid;
- nontrivial residual downstream gap remains or the paper requires the explicit-reasoning control.

Reuse the exact frozen 48-family CoT subset.

Conditions:

## N-C

Image + question + frozen prompted-CoT instruction.

## O-C

Text-only question + identical \(E^*\) + same prompted-CoT instruction.

Use the same repaired Instruct execution protocol.

Do not expand beyond the frozen 48 cases.

---

# 24. CoT interpretation

Compare:

\[
D^O,\quad C^O,\quad T^O.
\]

## If

\[
T^O\approx C^O>D^O
\]

then:

> much of the residual downstream benefit is reproducible by explicit reasoning elicitation on the same Instruct checkpoint.

## If

\[
T^O>C^O>D^O
\]

then:

> prompted CoT recovers part of the downstream benefit, but Thinking retains an additional advantage.

## If

\[
T^O>C^O\approx D^O
\]

then:

> the residual Thinking advantage is not explained by prompted CoT alone.

Do not claim algorithmic equivalence.

---

# 25. Reserve rule

The 40 frozen reserve families may be opened only if:

1. native and oracle validity pass;
2. P1 is meaningfully positive;
3. P2/P3 point estimates clearly support Outcome A/B/C;
4. one key interval remains precision-limited;
5. no major predeclared subgroup reversal exists.

Do not use reserve to rescue:

- technical invalidity;
- absent native gap;
- invalid oracle;
- wrong-direction effects.

Maximum eligible cohort:

\[
\boxed{
120
}
\]

---

# 26. Statistics

Independent unit:

\[
\boxed{
\text{problem/image family}
}
\]

For P1–P3:

- equal family weighting;
- paired bootstrap;
- 4,000 draws;
- fixed seed;
- 95% percentile intervals;
- multiplicity-aware intervals across P1–P3.

Also report:

- paired discordance counts;
- McNemar-style descriptive summaries;
- cap-hit/completion rates;
- major subject/evidence-type point estimates.

CoT remains secondary.

---

# 27. Repair transparency requirements

The paper/supplement must explicitly document:

1. original Stage 11C STOP;
2. why it was classified as technical invalidity rather than a scientific null;
3. every execution-field difference discovered;
4. exact repair chosen;
5. why the repair was selected without using accuracy;
6. known-good reproduction results;
7. non-primary validation results;
8. old invalid outputs preserved separately;
9. confirmation that cohort/\(E^*\)/endpoints were unchanged.

This is essential to distinguish a legitimate technical rerun from post-hoc scientific rescue.

---

# 28. Compute budget

## Technical repair

Known-good reproduction + discrepancy audit:

\[
\boxed{
<2 \text{ GPU-hours target}
}
\]

Non-primary repaired validation:

\[
\boxed{
<0.5 \text{ GPU-hours}
}
\]

## Scientific rerun

Primary native T/D:

\[
80\times2=160
\]

Oracle T/D, conditional:

\[
80\times2=160
\]

Neutral control:

\[
24\times2=48
\]

CoT control, conditional:

\[
48\times2=96
\]

Reserve, conditional:

\[
40\times4=160
\]

Target total:

\[
\boxed{
<7 \text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
9 \text{ GPU-hours}
}
\]

without explicit approval.

Do not spend the scientific budget unless technical validation passes.

---

# 29. Required artifacts

Produce:

1. `stage11cr_repair_spec.md`
2. `stage11cr_historical_runtime_comparison.json`
3. `stage11cr_known_good_manifest.json`
4. `stage11cr_known_good_reproduction.parquet`
5. `stage11cr_discrepancy_audit.json`
6. `stage11cr_repaired_protocol.json`
7. `stage11cr_nonprimary_validation.json`
8. `stage11cr_native_td_results.parquet`
9. `stage11cr_native_validity_gate.json`
10. `stage11cr_native_performance_gate.json`
11. conditional `stage11cr_oracle_td_results.parquet`
12. conditional `stage11cr_oracle_validity.json`
13. `stage11cr_primary_inference.json`
14. conditional `stage11cr_neutral_control.json`
15. conditional `stage11cr_cot_control.parquet`
16. conditional `stage11cr_reserve_extension.json`
17. `stage11cr_resource_accounting.json`
18. `stage11cr_summary.md`

Preserve all original Stage 11C artifacts separately.

---

# 30. Required figures

## Figure R1 — Technical failure and repair

Show:

- Stage 11C cap-hit / no-final behavior;
- known-good historical behavior;
- repaired known-good behavior.

This is a supplement/validation figure.

## Figure R2 — Native Thinking-vs-Direct

Only if native validity passes.

## Figure R3 — Equal-Evidence Oracle

Only if oracle executes.

## Figure R4 — Gap localization

\[
P1,\quad P2,\quad P3.
\]

## Figure R5 — Short CoT control

Only if executed.

---

# 31. Final claim wording by outcome

## Upstream-dominant

> **Under a technically validated rerun, much of the Thinking variant's advantage over Instruct Direct is reduced when task-critical visual evidence is equalized, implicating upstream evidence acquisition/access.**

## Downstream-dominant

> **Under a technically validated rerun, the Thinking variant retains a substantial advantage over Instruct Direct even when both receive identical correct visual evidence, implicating downstream reasoning/integration.**

## Mixed

> **Thinking gains both from upstream access to task-critical visual evidence and from downstream reasoning over already-correct evidence.**

## No informative scientific result

> **After repairing the completion-validity issue, the frozen cohort did not provide an interpretable performance gap / oracle result sufficient to localize the Thinking advantage.**

---

# 32. Null discipline

Even after repair:

- a small P3 does not mean visual retrieval is irrelevant;
- a large P3 does not prove the Stage 4A retrieval mechanism is the sole cause;
- a persistent P2 does not mean perception is unimportant;
- a CoT match does not imply algorithmic equivalence;
- an oracle intervention changes the input representation and is an operational localization tool.

All claims must remain at the measured level.

---

# 33. Exactly one recommendation at completion

## If the repaired run yields a clean P1–P3 localization

Recommend:

> Promote Claim 3 using the frozen Thinking-vs-Instruct lifecycle localization, with CoT only as the same-checkpoint reasoning control.

## If technical repair fails or the repaired scientific result remains noninformative

Recommend:

> Close the Thinking-performance mechanism branch and finalize the paper around Claims 1 and 2.

Do not launch another benchmark/model search automatically.

---

# 34. Final decision target

Stage 11C-R exists to answer two questions in order:

\[
\boxed{
\textbf{1. Can the failed Stage 11C assay be restored to a valid completion regime
without changing the scientific design?}
}
\]

and only if yes:

\[
\boxed{
\textbf{2. Where in the visual-reasoning lifecycle does the Thinking variant gain over
Instruct Direct, and can prompted CoT reproduce the downstream component?}
}
\]

The technical repair is successful only if it restores valid completion **without using accuracy to choose the protocol**.
