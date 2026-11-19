# Stage 12W-S — Distributed Reasoning-State Construction, Interference, and Repair

## 0. One-line objective

Test whether the portable Thinking-generated reasoning state identified in Stage 12U-S is supported by **distributed, task-specific derived reasoning content** rather than a single critical deduction, and whether additional reasoning can **degrade and later repair** that state.

Primary question:

\[
\boxed{
\textbf{Which distributed parts of a Thinking trace increase, disrupt, and restore
the probability that Instruct can solve the task without the image?}
}
\]

This stage follows the Stage 12V-S result that full-prefix portability replicated, but no single semantic step showed a robust causal-necessity signature.

The stage therefore shifts from:

\[
\text{single critical step}
\]

to:

\[
\boxed{
\text{distributed state construction}
+
\text{interference}
+
\text{repair}
}
\]

---

# 1. Why this experiment is necessary for the paper

The strongest current behavioral result is:

\[
\boxed{
\textbf{Thinking can produce task-specific externalized reasoning states that
the weaker Instruct checkpoint can use to solve otherwise unsolved problems.}
}
\]

Stage 12U-S established this on the targeted B4 production-support cohort:

- Thinking-prefix replay into Thinking succeeded on all five B4 cases;
- Thinking-prefix replay into Instruct succeeded on four of five;
- question-only Instruct did not solve those cases;
- shuffled Thinking traces did not reproduce the effect.

Stage 12V-S then tested whether one local semantic step caused the portability transition.

That stage found:

- full-prefix portability still replicated;
- only 2/4 families showed an adjacent apparent transition;
- one family was clearly nonmonotonic;
- one family was missingness-limited;
- deleting the apparent critical step did not destroy portability in either localized case;
- one content counterfactual affected one family, but the full causal signature failed.

Therefore:

\[
\boxed{
\textbf{portable reasoning-state construction is not well explained by one necessary local deduction.}
}
\]

The next paper-relevant question is whether the useful state is:

1. distributed across multiple semantic blocks;
2. specifically dependent on **derived reasoning** rather than raw \(E^*\);
3. vulnerable to interference from later reasoning;
4. repairable by subsequent reasoning.

---

# 2. Paper claim first

## Strong positive claim

If successful:

> **Thinking transforms task-relevant visual evidence into a distributed, task-specific reasoning state that is sufficient for downstream solution. Portability depends on multiple derived reasoning components rather than a single critical step, and the state can be disrupted and repaired as reasoning evolves.**

This would sharpen the Claim 1 lifecycle to:

\[
\boxed{
\text{visual evidence}
\rightarrow
\text{distributed derived state}
\rightarrow
\text{portable downstream computation}
}
\]

with nonmonotonic evolution:

\[
\text{usable}
\leftrightarrow
\text{interfered}
\leftrightarrow
\text{repaired}.
\]

## Conservative positive claim

If block-level necessity is supported but interference/repair is not:

> **Thinking's portable state is distributed across multiple reasoning blocks, rather than localized to one necessary deduction.**

## Null interpretation

If no block-level manipulation changes portability reliably:

> **The Stage 12U-S portability effect is real at the full-prefix level, but this stage does not identify which visible textual components are causally responsible. The useful state may be highly redundant, distributed below the chosen semantic granularity, or partly non-textual.**

This null does **not** invalidate Stage 12U-S.

---

# 3. Frozen cohort

Primary cohort:

\[
\boxed{
\mathcal P_{\mathrm{portable}},\quad n=4
}
\]

the same four Stage 12U-S B4 `PRODUCTION_SUPPORT` families.

Do not add families after interventions are designed.

Keep the Stage 12U-S nonportable B4 family as a descriptive negative control only.

---

# 4. Frozen source states

Reuse exactly:

- original questions;
- original successful Thinking traces;
- Stage 12U-S answer-safe prefixes;
- source trace hashes;
- Stage 12V-S semantic-step segmentation;
- Stage 12V-S step annotations;
- Stage 12U-S production-support labels.

Do not regenerate source Thinking traces.

All scientific target replay remains image-free unless explicitly specified as a frozen \(E^*\) text control.

---

# 5. Target model

Primary target:

\[
\boxed{
\textbf{Qwen3-VL-4B-Instruct}
}
\]

Use the exact frozen Instruct checkpoint and recipe:

- temperature = 0.7
- top-p = 0.8
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 1.5
- max new tokens = 32,768

No prompt search.
No decoding search.
No retries.

---

# 6. Same-seed portability landscape

Stage 12V-S showed that a 2/3 majority boundary can be seed-sensitive.

Therefore all conditions within a family must use the **same frozen seed set**.

Use:

\[
\boxed{
7 \text{ seeds per family-condition}
}
\]

generated prospectively from:

`SHA256(stage12ws-v1|family_id|replicate)`.

The same 7 replicate seeds are reused across:

- full trace;
- block deletions;
- block-only constructions;
- derived-state constructions;
- interference/repair tests;
- order controls.

This enables within-seed paired comparisons.

Primary quantity:

\[
\boxed{
p_I(R)=P(\text{Instruct correct}\mid Q+R)
}
\]

estimated as correct continuations out of 7.

Do not reduce the main analysis to a single majority label.

---

# 7. Semantic block construction

Using the already frozen semantic steps \(S_1,\ldots,S_m\), partition each full portable Thinking prefix into:

\[
\boxed{
5\text{ to }8 \text{ contiguous semantic blocks}
}
\]

before any new replay is generated.

Block boundaries must reflect coherent reasoning phases, not equal token counts alone.

Preferred block roles include:

1. `RAW_EVIDENCE_AND_BINDING`
2. `REPRESENTATION_SETUP`
3. `DERIVED_RELATIONS`
4. `INTERMEDIATE_COMPUTATION`
5. `REINTERPRETATION_OR_CHECKING`
6. `LATE_DERIVATION`
7. `REPAIR_OR_RESOLUTION`

Not every family must use every role.

The exact block map is frozen before outcomes.

---

# 8. Block content audit

For each block record:

- start/end semantic-step IDs;
- token count;
- primary functional role;
- direct image-derived propositions;
- derived propositions;
- new entity bindings;
- new intermediate values;
- corrections of prior statements;
- contradictions/reopenings;
- repeated/restated propositions.

This audit must not use replay outcomes.

---

# 9. Phase A — Full-state replication

Run the full portable Thinking prefix:

\[
R_T^{\mathrm{full}}\rightarrow I
\]

with the 7 frozen seeds.

Also run:

\[
Q\rightarrow I
\]

with the same 7 seeds.

Family is eligible for distributed-state inference only if:

\[
p_I(R_T^{\mathrm{full}})-p_I(Q)\ge \frac{3}{7}.
\]

If fewer than 3/4 primary families pass:

\[
\boxed{
\texttt{PORTABILITY\_WEAK\_UNDER\_PAIRED\_SEEDS}
}
\]

and stop before high-cost combinatorial ablation.

---

# 10. Phase B — Leave-one-block-out necessity

For each eligible family and each block \(B_j\), construct:

\[
R^{-B_j}
\]

by deleting that block from the full portable trace while preserving all remaining text exactly.

Run:

\[
R^{-B_j}\rightarrow I
\]

with the same 7 seeds.

Define paired block effect:

\[
\boxed{
\Delta_j
=
p_I(R_T^{\mathrm{full}})
-
p_I(R^{-B_j})
}
\]

Interpretation:

- large positive \(\Delta_j\): block supports portability;
- near-zero \(\Delta_j\): block individually redundant;
- negative \(\Delta_j\): block may interfere with portability.

---

# 11. Phase C — Raw evidence vs derived state

This is the most important conceptual test.

For each family construct four image-free conditions.

## C0 — Raw evidence only

\[
Q+E^*\rightarrow I
\]

using the frozen Stage 12B-S oracle text.

## C1 — Raw evidence + derived blocks

\[
Q+E^*+D\rightarrow I
\]

where \(D\) is the concatenation of blocks annotated as:

- `DERIVED_RELATIONS`;
- `INTERMEDIATE_COMPUTATION`;
- `SUBGOAL_CONCLUSION`;
- `REPAIR_OR_RESOLUTION`;

excluding direct raw-evidence restatements where possible.

## C2 — Full Thinking prefix

\[
Q+R_T^{\mathrm{full}}\rightarrow I
\]

## C3 — Full Thinking prefix minus derived blocks

\[
Q+(R_T^{\mathrm{full}}-D)\rightarrow I
\]

Run all four with the same 7 seeds.

---

# 12. Derived-state signature

Define a family as `DERIVED_STATE_SUPPORT` if:

\[
p_I(E^*+D) - p_I(E^*) \ge \frac{3}{7}
\]

and:

\[
p_I(R_T^{\mathrm{full}})
-
p_I(R_T^{\mathrm{full}}-D)
\ge \frac{3}{7}.
\]

This is the strongest evidence that **task-specific derived reasoning**, not raw visual facts alone, supports portability.

---

# 13. Phase D — Minimal block-set search

Only run if Phase B/C identify at least two supportive blocks.

Purpose:

> determine whether portability depends on a combination of individually redundant components.

Define candidate supportive blocks from the frozen Phase B/C results, then use bounded greedy backward elimination:

1. start from the full trace;
2. remove the block with the smallest observed effect;
3. replay with the same 7 seeds;
4. continue while:
   \[
   p_I(R)\ge p_I(R_T^{\mathrm{full}})-1/7;
   \]
5. stop when the next deletion reduces success by at least \(3/7\).

Do not search all subsets.

Freeze the elimination order before executing Phase D.

Call the retained set:

\[
\boxed{
\mathcal B_{\mathrm{portable}}
}
\]

the candidate distributed portable state.

---

# 14. Distributed-necessity signature

Define `DISTRIBUTED_NECESSITY` if:

1. no single block deletion causes a drop \(\ge4/7\);
2. removing a pre-frozen combination of at least two blocks causes a drop \(\ge4/7\);
3. a matched-length low-importance block-set deletion does not produce the same drop.

Interpretation:

\[
\boxed{
\textbf{portability depends on a distributed set of reasoning components rather than one local deduction.}
}
\]

---

# 15. Phase E — Block-order control

Test whether portability is a bag of facts or a structured trajectory.

For each family construct exactly one predeclared order perturbation:

- keep `RAW_EVIDENCE_AND_BINDING` first;
- deterministically swap the two largest derived/computation blocks;
- preserve block contents exactly.

Call:

\[
R^{\mathrm{ORDER}}.
\]

Run with the same 7 seeds.

Order-sensitive signature:

\[
\boxed{
p_I(R_T^{\mathrm{full}})
-
p_I(R^{\mathrm{ORDER}})
\ge \frac{3}{7}.
}
\]

Do not test multiple permutations after seeing results.

---

# 16. Phase F — Nonmonotonic interference / repair

Use the Stage 12V-S family with the clearest nonmonotonic prefix pattern as the primary natural experiment.

Let:

\[
P_a^+
\rightarrow
P_b^-
\rightarrow
P_c^+
\]

be the frozen portability sequence.

Define:

\[
B_{\mathrm{interfere}}
=
P_b-P_a
\]

and:

\[
B_{\mathrm{repair}}
=
P_c-P_b.
\]

Freeze exact spans before generation.

Run:

### F1 — Interference deletion

\[
P_b-B_{\mathrm{interfere}}
\rightarrow I
\]

### F2 — Interference addition

\[
P_a+B_{\mathrm{interfere}}
\rightarrow I
\]

### F3 — Repair addition

\[
P_b+B_{\mathrm{repair}}
\rightarrow I
\]

### F4 — Repair deletion

\[
P_c-B_{\mathrm{repair}}
\rightarrow I
\]

with the same 7 seeds.

---

# 17. Interference signature

Support `STATE_INTERFERENCE` if:

\[
p_I(P_b-B_{\mathrm{interfere}})
-
p_I(P_b)
\ge \frac{3}{7}
\]

and/or:

\[
p_I(P_a)
-
p_I(P_a+B_{\mathrm{interfere}})
\ge \frac{3}{7}.
\]

Interpretation:

> later reasoning can make an otherwise usable textual state less useful.

---

# 18. Repair signature

Support `STATE_REPAIR` if:

\[
p_I(P_b+B_{\mathrm{repair}})
-
p_I(P_b)
\ge \frac{3}{7}
\]

and/or:

\[
p_I(P_c)
-
p_I(P_c-B_{\mathrm{repair}})
\ge \frac{3}{7}.
\]

Interpretation:

> subsequent reasoning can restore portability after degradation.

---

# 19. Matched-length controls

For every high-impact deletion/composite ablation, define one matched-length control using low-importance blocks.

Selection rule:

1. choose block(s) with closest total token length;
2. exclude candidate supportive/interference/repair blocks;
3. break ties by earlier position.

Run matched controls with the same 7 seeds.

This separates semantic content from simple context-length effects.

---

# 20. Primary endpoints

## W-P1 — Full-state portability under paired seeds

\[
p_I(R_T^{\mathrm{full}})
\]

vs:

\[
p_I(Q).
\]

## W-P2 — Block-level effect profile

\[
\Delta_j
=
p_I(R_T^{\mathrm{full}})
-
p_I(R^{-B_j}).
\]

## W-P3 — Derived-state support

Count families satisfying `DERIVED_STATE_SUPPORT`.

## W-P4 — Distributed necessity

Count families satisfying `DISTRIBUTED_NECESSITY`.

## W-P5 — Order sensitivity

Count families with the frozen order effect \(\ge3/7\).

## W-P6 — Interference / repair

Report paired seed effects for the nonmonotonic family.

---

# 21. Primary decision states

## `DISTRIBUTED_DERIVED_STATE_SIGNAL`

Declare if all hold:

1. full portability remains robust in at least 3/4 primary families;
2. at least 3/4 satisfy `DERIVED_STATE_SUPPORT`;
3. at least 2/4 satisfy `DISTRIBUTED_NECESSITY` or show clear multi-block dependence;
4. matched-length controls do not explain the effects.

Interpretation:

> Thinking constructs a distributed derived reasoning state, beyond raw visual evidence, that enables Instruct downstream solution.

## `DERIVED_STATE_ONLY`

Declare if at least 3/4 satisfy `DERIVED_STATE_SUPPORT`, but distributed block necessity is not established.

## `INTERFERENCE_REPAIR_SIGNAL`

May coexist with either state above.

Declare if the frozen nonmonotonic family shows both `STATE_INTERFERENCE` and `STATE_REPAIR`.

## `PORTABILITY_CONTENT_UNRESOLVED`

Declare if full portability replicates but neither derived-state nor block-level intervention produces robust paired effects.

## `PORTABILITY_WEAK_UNDER_PAIRED_SEEDS`

Declare if fewer than 3/4 primary families preserve a strong full-trace advantage over question-only under the new 7-seed panel.

Stop high-cost downstream phases.

---

# 22. Strongest paper claim if positive

If `DISTRIBUTED_DERIVED_STATE_SIGNAL`:

> **Thinking does not merely expose raw visual facts. It incrementally constructs a distributed, task-specific derived reasoning state that a weaker Instruct model can use to solve the task.**

If `INTERFERENCE_REPAIR_SIGNAL` also passes:

> **The usability of that state is nonmonotonic: additional reasoning can disrupt and later restore downstream solvability.**

---

# 23. What this stage cannot prove

Do not claim:

- the distributed textual state is the complete hidden mechanism;
- all Thinking gains use the same block structure;
- checkpoint differences are caused solely by Thinking post-training;
- B4 findings estimate benchmark-wide prevalence;
- block deletion identifies unique neural representations.

This is externalized-state causal analysis.

---

# 24. Connection to earlier claims

A positive result would create a coherent end-to-end account:

\[
\boxed{
\text{reasoning demand}
\rightarrow
\text{target-specific visual retrieval}
\rightarrow
\text{Value-rich transfer}
\rightarrow
\text{distributed derived reasoning state}
\rightarrow
\text{portable downstream computation}
}
\]

The new insight is the **transformation layer** between raw evidence and final reasoning.

---

# 25. Null discipline

If block deletion effects are weak:

- redundancy may be real;
- the state may be represented through overlapping restatements;
- blocks may be too coarse;
- useful information may partly reside in non-textual state.

Do not conclude that text is irrelevant; Stage 12U-S already established full-trace portability.

If order perturbation has no effect:

> portability may depend mainly on content rather than trajectory order.

If interference/repair fails to replicate:

> Stage 12V-S nonmonotonicity remains descriptive and seed-sensitive.

---

# 26. Statistical reporting

Independent unit:

\[
\boxed{
\text{family}
}
\]

Within family:

- same 7 seeds for all paired conditions;
- report seed-level correctness;
- report paired success differences.

Because \(n=4\):

- no asymptotic population significance;
- exact family counts;
- descriptive paired intervals where useful.

The mechanistic evidence comes from replicated within-family intervention patterns.

---

# 27. Execution order

Run strictly in this order:

1. freeze block segmentation and annotations;
2. freeze 7-seed panel;
3. Phase A full-state replication;
4. if gate passes, Phase B leave-one-block-out;
5. Phase C raw evidence vs derived state;
6. freeze candidate supportive blocks;
7. conditional Phase D minimal block-set search;
8. Phase E one order control;
9. Phase F interference/repair natural experiment;
10. scoring/audit;
11. decision.

Do not adapt blocks or seeds after outcomes.

---

# 28. Compute budget

Approximate maximum:

- Phase A: 56 calls
- Phase B: ~168 calls
- Phase C: 112 calls
- Phase D: <=84 calls
- Phase E: 28 calls
- Phase F: 28 calls

Target:

\[
\boxed{
<6 \text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
8 \text{ GPU-hours}
}
\]

unless separately approved.

Use phase gates to avoid unnecessary calls.

---

# 29. Required figures

## Figure W1 — Portability probability landscape

For each family show:

- full trace;
- question-only;
- leave-one-block-out conditions.

## Figure W2 — Raw evidence vs derived state

Show:

- \(E^*\);
- \(E^*+D\);
- full Thinking trace;
- full trace minus \(D\).

## Figure W3 — Distributed block necessity

Visualize block effects and candidate minimal portable block set.

## Figure W4 — Nonmonotonic interference and repair

Show:

\[
P_a^+
\rightarrow
P_b^-
\rightarrow
P_c^+
\]

and intervention outcomes.

## Figure W5 — Order sensitivity

Full trace vs frozen block-order perturbation.

---

# 30. Required artifacts

Produce:

1. `stage12ws_distributed_state_spec.md`
2. `stage12ws_primary_manifest.json`
3. `stage12ws_block_segmentation.json`
4. `stage12ws_block_annotations.json`
5. `stage12ws_seed_manifest.json`
6. `stage12ws_full_state_results.parquet`
7. `stage12ws_block_deletion_results.parquet`
8. `stage12ws_derived_state_results.parquet`
9. conditional `stage12ws_minimal_blockset_results.parquet`
10. `stage12ws_order_control_results.parquet`
11. `stage12ws_interference_repair_results.parquet`
12. `stage12ws_matched_controls.parquet`
13. `stage12ws_primary_inference.json`
14. `stage12ws_decision.json`
15. `stage12ws_resource_accounting.json`
16. `stage12ws_summary.md`

Preserve all prior Stage 12 artifacts unchanged.

---

# 31. Exactly one recommendation at completion

## If `DISTRIBUTED_DERIVED_STATE_SIGNAL`

Recommend:

> Align the identified distributed reasoning blocks with causal visual-retrieval and Value-transfer events to test how raw visual evidence is transformed into the portable derived state.

## If `DERIVED_STATE_ONLY`

Recommend:

> Test distributed semantic compression/summarization of the derived state rather than finer single-step necessity.

## If `INTERFERENCE_REPAIR_SIGNAL` dominates

Recommend:

> Causally manipulate the interfering and repairing blocks to identify the propositions that degrade and restore downstream usability.

## If `PORTABILITY_CONTENT_UNRESOLVED`

Recommend:

> Stop further text-granularity ablation and test whether cached/hidden non-textual state complements the portable text.

## If `PORTABILITY_WEAK_UNDER_PAIRED_SEEDS`

Recommend:

> Retain Stage 12U-S as the strongest supported production result and stop fine externalized-state localization.

Do not launch automatically.

---

# 32. Final decision target

Stage 12W-S exists to answer:

\[
\boxed{
\textbf{Is the Thinking-generated portable state a distributed task-specific transformation of visual evidence,
and can that state's downstream usability be disrupted and repaired during reasoning?}
}
\]

The strongest positive pattern is:

\[
\boxed{
E^* \text{ alone fails},
\quad
E^*+D \text{ succeeds},
\quad
R_T-D \text{ fails},
}
\]

together with:

\[
\boxed{
\text{multi-block rather than single-step necessity}
}
\]

and, where present:

\[
\boxed{
\text{interference}
\rightarrow
\text{loss of portability}
\rightarrow
\text{repair}
\rightarrow
\text{recovered portability}.
}
\]

A positive result would make the paper's central mechanism substantially more specific:

> **Thinking transforms visual evidence into distributed, task-specific reasoning states that support downstream computation.**
