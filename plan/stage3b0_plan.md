# Stage 3B.0 Plan — Prefill Visual-to-Language Transfer

## 0. Purpose

Stage 3B.0 asks a narrowly defined mechanistic question:

> **Before any reasoning token is generated, has task-relevant visual evidence already been transferred into non-visual prefix representations strongly enough to support later reasoning without further direct access to visual tokens?**

This stage is motivated by two facts:

1. Stage 3A established robust causal visual-content sensitivity from strict pre-E0 prefixes.
2. Prior MLLM information-flow work suggests that visual information can be transferred into language-side/question-token representations during lower-to-middle transformer layers, after which direct visual access may become less necessary.

Stage 3B.0 should therefore distinguish:

\[
\text{continued direct visual reading during reasoning}
\]

from:

\[
\text{visual information already encoded into language-side prefix states during prefill}
\]

This stage is **coarse carrier localization only**.

Do **not** perform layer-wise localization yet.
Do **not** start Stage 3B.1 automatically.

---

# 1. Scientific Context From Previous Stages

## Stage 2A–2C

The project originally observed that evidence-aligned visual ROIs often receive high attention while the model verbalizes the corresponding evidence.

However, Stage 2C showed:

- 58/70 evidence events were mention-centered;
- only 3/70 were pre-mention leads;
- later references to the same fact also reactivated the matching ROI;
- 8/10 Stage 2B target windows began after the evidence was already explicit in CoT.

Therefore:

> **ROI attention is not a reliable marker of fresh visual-evidence acquisition.**

A strong current methodological finding is:

\[
\text{Attention WHEN} \neq \text{Causal visual-information WHEN}
\]

---

## Stage 3A

Stage 3A used localized visual counterfactuals and strict pre-E0 prefixes.

Frozen primary cohort:

- 49 unique base problems;
- 45 localized numeric-label edits;
- 4 structural visual edits.

Main result:

- CE in expected direction: 49/49;
- mean CE: 3.2256 nats/token;
- mean sham-controlled CE: 3.1864;
- mean sham shift: 0.0392;
- 46/46 evaluable problems showed positive early sensitivity by at least E0-8;
- counterfactual rollouts stated the changed fact exactly in 46/49 cases.

Thus:

> **Changing localized visual content causally changes the model's upcoming evidence preference before explicit evidence verbalization.**

But Stage 3A does **not** establish where the information is carried.

A positive pre-E0 probe can still arise because the model re-accesses visual tokens while scoring/generating the later evidence statement.

Stage 3B.0 addresses this ambiguity.

---

# 2. Main Research Questions

Stage 3B.0 has three ordered questions.

## RQ1 — Prefill sufficiency

If the model sees the image normally during prefill, but **all direct access to visual tokens is blocked from the first generated reasoning token onward**, does the original-vs-counterfactual evidence distinction survive?

If yes:

> enough image-dependent information is already available in non-visual prefix states after prefill to support the later evidence distinction.

This does **not yet identify which prefix tokens carry it**.

---

## RQ2 — Broad language-side prefix carrier

Can swapping the image-conditioned cached states of the eligible **non-visual prefix positions** between original and counterfactual runs causally transfer the evidence identity?

If yes:

> prefill created a causal visual representation inside language-side prefix states.

---

## RQ3 — Question-token carrier

Does patching **question-token cached states** alone transfer a substantial fraction of the evidence identity?

If yes:

> question-token representations are a causal carrier of the visual fact after prefill.

If broad prefix patching works but question-only patching does not, inspect other post-image prefix groups before making a claim.

---

# 3. Primary Cohort

Use the **same frozen 49 unique base problems from Stage 3A**.

Do not create a new hypothesis-enriched cohort.

Primary unit:

```text
base_problem_id
```

Do not count multiple events from one base problem as independent primary samples.

Analyze:

- all 49 as primary cohort;
- 45 numeric-label edits as a major robustness stratum;
- 4 structural edits as a separately reported small stratum.

No selection based on attention is allowed.

---

# 4. Stage 3B.0 Conceptual Model

At the end of prefill, before reasoning generation begins, the KV cache contains states corresponding to input token positions.

Define candidate token populations only after inspecting the actual Qwen3-VL prompt layout.

At minimum distinguish:

\[
V = \text{visual-token positions}
\]

\[
Q = \text{question/content-text positions}
\]

and potentially:

\[
T = \text{trailing non-visual prefix positions after the question}
\]

such as assistant/header/control/newline tokens that occur after the image and may causally receive image-conditioned information.

Define:

\[
P_{\text{post-image}}
=
\text{all eligible non-visual prefix positions after the visual tokens}
\]

This broad set is the initial language-side carrier candidate.

Do **not** assume in advance that Q alone is the only possible carrier.

---

# 5. Mandatory Token-Layout / Causal-Order Audit

Before interventions, inspect the exact multimodal token layout for at least 3 representative examples and verify:

1. visual-token indices;
2. question-token indices;
3. system/instruction-token indices;
4. assistant/header/trailing-prefix indices;
5. which non-visual positions occur **after** visual tokens and therefore can causally attend to them during prefill;
6. whether original/counterfactual/sham images produce identical visual-token counts and identical text-token positions;
7. whether all patch source/recipient positions align exactly.

Create:

```text
outputs/stage3b0/layout_audit/token_layout_audit.md
outputs/stage3b0/layout_audit/token_group_definition.json
```

The token groups used in the causal analysis must be frozen before cohort-scale results are inspected.

---

# 6. Intervention A — Generation-Start Visual Cutoff

This is the first and most important experiment.

## Procedure

For each original, counterfactual, and sham condition:

1. perform multimodal prefill normally;
2. allow all normal image→later-prefix communication during prefill;
3. from the **first generated reasoning query onward**, block every generated query from attending to **all visual-token key positions**;
4. keep this visual cutoff active for the entire teacher-forced strict pre-E0 reasoning prefix and subsequent evidence probe;
5. keep all non-visual prefix/reasoning attention intact.

Conceptually:

```text
PREFILL:
V -> Q/P     allowed

GENERATION:
R_t -> V     BLOCKED for every t
R_t -> Q/P   allowed
R_t -> R_<t  allowed
```

Apply the generated-query→visual cutoff across all language-model layers and heads.

Do not remove visual embeddings or alter model weights.

---

# 7. Why Generation-Start Cutoff Matters

Suppose the image contains:

```text
AB = 3
```

If the model can still distinguish:

```text
original image      -> "AB is 3"
counterfactual image -> "AB is 5"
```

when direct visual access has been disabled since the **first generated token**, then the later evidence distinction cannot depend on fresh generated-query→visual access.

The relevant image-dependent information must already have been made available through some non-visual prefill representation that can influence generation.

This is evidence for:

\[
\boxed{\text{prefill visual-to-language transfer / non-visual prefill sufficiency}}
\]

It is not yet evidence for Q specifically.

---

# 8. Primary Metric for Prefill Sufficiency

Reuse Stage 3A's evidence-specific scoring definition.

For each condition:

\[
D(I)
=
L_o(I)-L_c(I)
\]

where \(L_o\) and \(L_c\) are length-normalized sequence log-probabilities of the original and counterfactual evidence continuations.

Define:

\[
CE_{\text{full}}
=
D(I_o)-D(I_c)
\]

from Stage 3A.

Under generation-start visual cutoff:

\[
CE_{\text{cut}}
=
D_{\text{cut}}(I_o)-D_{\text{cut}}(I_c)
\]

Define per-problem retention:

\[
\rho
=
\frac{CE_{\text{cut}}}{CE_{\text{full}}}
\]

Report \(\rho\) without clipping.

Also compute the sham-controlled cutoff effect.

Primary questions:

- Is \(CE_{\text{cut}}\) still in the expected direction?
- How much of Stage 3A's visual-content effect survives?
- Is the cutoff effect much larger than sham effects?

Do not use final-answer accuracy as the sole metric.

---

# 9. Intervention B — Broad Non-Visual Prefix KV Patching

Only after generation-start cutoff is technically validated.

Use paired runs:

```text
O = original image
C = counterfactual image
```

Text tokens are identical.

Run both through prefill and cache their K/V states.

Then construct a recipient run with:

```text
visual source during prefill: C
future direct visual access: BLOCKED
non-visual post-image prefix K/V: patched from O
```

Patch:

\[
P_{\text{post-image}}^{O}
\rightarrow
P_{\text{post-image}}^{C}
\]

across all language-model layers for this coarse Stage 3B.0 test.

Then teacher-force the exact same strict pre-E0 reasoning prefix and score the evidence preference.

If the recipient shifts from counterfactual toward original evidence identity, this indicates that the patched language-side prefix states causally carry image-dependent evidence.

---

# 10. Reciprocal Patching

Do not rely only on original→counterfactual rescue.

Also perform:

\[
P_{\text{post-image}}^{C}
\rightarrow
P_{\text{post-image}}^{O}
\]

Expected direction:

```text
Original recipient + counterfactual prefix states
    -> shifts toward counterfactual fact
```

Bidirectional transfer is much stronger evidence than one-sided rescue.

---

# 11. Intervention C — Question-Only KV Patching

After broad-prefix patching is validated, patch only:

\[
Q^O \rightarrow Q^C
\]

and reciprocally:

\[
Q^C \rightarrow Q^O
\]

Keep:

- recipient visual-prefill states unchanged;
- recipient non-question prefix states unchanged;
- future direct visual access blocked;
- generated reasoning prefix token IDs identical.

Question-token patching should use cached K/V states at the same token positions across source and recipient.

Do not perform layer-wise Q patching yet.

Patch Q across all language layers for the coarse carrier test.

---

# 12. Other Prefix Groups as Controls

Depending on the audited Qwen3-VL prompt layout, define non-overlapping or nested groups prospectively.

Useful candidates:

- Q: actual user question/content tokens;
- T: trailing assistant/control/header tokens occurring after the image/question;
- P_post-image: all eligible non-visual positions after visual tokens.

At minimum compare:

```text
P_post-image patch
Q-only patch
```

If technically clean, also test:

```text
T-only patch
Q+T patch
```

This prevents incorrectly attributing all prefill visual transfer to Q if the actual carrier is a trailing prompt position.

Do not add groups post hoc because one produced an attractive result.

---

# 13. Patch Controls

Every patching experiment must include:

## C0 — No patch
Recipient run with its own cache.

## C1 — Self patch
Recipient states replaced with an identical copy from the same condition.

Should have negligible effect.

## C2 — Original -> Counterfactual
Tests rescue toward original fact.

## C3 — Counterfactual -> Original
Tests reciprocal transfer toward counterfactual fact.

## C4 — Sham-source patch
When feasible, patch from the sham run into original or vice versa.

Since original and sham have the same semantics, semantic evidence preference should remain stable.

This controls for generic state transplantation effects.

---

# 14. Patch Metric

Let:

\[
D_O
\]

be original evidence preference,

\[
D_C
\]

counterfactual evidence preference,

and:

\[
D_{C \leftarrow O,Q}
\]

the counterfactual recipient with original Q states patched in.

Define directional normalized recovery:

\[
R_Q
=
\frac{
D_{C \leftarrow O,Q}-D_C
}{
D_O-D_C
}
\]

Interpretation:

- \(R_Q \approx 0\): Q patch transfers little evidence identity;
- \(R_Q > 0\): Q patch moves prediction toward source evidence;
- \(R_Q \approx 1\): strong source-like recovery;
- values >1 or <0 should be reported, not clipped.

Define the reciprocal metric analogously.

Compute the same for:

\[
R_{P_{\text{post-image}}}
\]

and any prospectively defined T or Q+T groups.

Use sham controls to quantify generic patch effects.

---

# 15. Technical Smoke Validation

Before all 49 examples, use 3 representative numeric-label examples.

Verify:

1. no-hook run exactly reproduces expected Stage 3A scoring;
2. a hooked no-op run is transparent;
3. generation-start visual cutoff masks all and only generated-query→visual-key edges;
4. visual cutoff begins at the first generated query, not during prefill;
5. original/counterfactual/sham prefix token IDs remain identical;
6. source/recipient Q/P token positions align exactly;
7. KV replacement shapes, layer indexing, GQA head semantics, and cache positions are correct;
8. self-patch is numerically/behaviorally near no-patch;
9. cached teacher-forced scoring remains deterministic;
10. no NaNs/infs occur.

If any smoke criterion fails, stop and debug.

---

# 16. Important GQA / KV-Cache Implementation Note

Qwen3-VL may use grouped-query attention.

Do not assume dense-attention K/V tensor shapes.

The implementation must explicitly validate:

- number of query heads;
- number of K/V heads;
- cache tensor layout;
- sequence-position dimension;
- layer indexing.

Never patch tensors by guessed axis order.

Save tensor-shape diagnostics from the smoke test.

---

# 17. Primary Analyses

## Analysis A — Does prefill suffice?

Across 49 bases report:

- \(CE_{\text{full}}\)
- \(CE_{\text{cut}}\)
- retention ratio \(\rho\)
- expected-direction proportion
- sham-controlled cutoff CE
- bootstrap CI over base problems

This answers RQ1.

---

## Analysis B — Is evidence in language-side prefix states?

For broad \(P_{\text{post-image}}\) patching report:

- O→C directional recovery
- C→O directional recovery
- source-consistent shift rate
- sham/self patch effects

This answers RQ2.

---

## Analysis C — Is Q a major carrier?

For Q-only patching report the same metrics.

Compare:

\[
R_Q
\]

with:

\[
R_{P_{\text{post-image}}}
\]

Possible interpretation:

- \(R_Q \approx R_P\): Q explains most broad-prefix transfer;
- \(R_Q \ll R_P\): important evidence exists in other prefix positions;
- both small despite cutoff retention: inspect token partition/technical assumptions before concluding no carrier.

This answers RQ3.

---

# 18. Secondary Behavioral Validation

For a subset or all examples, perform matched-seed short free rollouts with generation-start visual cutoff under:

- original
- counterfactual
- sham

Record first visual-fact statement.

Question:

> Does the original/counterfactual semantic distinction survive when reasoning generation has never had direct access to visual tokens?

This is behavioral validation only.

Primary conclusions should rely on evidence-specific preference metrics.

---

# 19. Do Not Use Attention as the Primary Signal

Stage 3B.0 must not select examples, token groups, or patch targets based on Stage 2 visual-attention magnitude.

Attention may be inspected after causal results are frozen as a secondary comparison.

Do not use attention to define successful transfer.

---

# 20. Interpretation Matrix

## Pattern A — Strong generation-start cutoff retention + strong Q patch

Interpretation:

> Visual evidence is already causally encoded into question-side representations during prefill and can support later reasoning without fresh direct visual access.

This is the cleanest result motivating Stage 3B.1 layer-wise V→Q localization.

---

## Pattern B — Strong cutoff retention + broad-prefix patch works, Q patch weak

Interpretation:

> Prefill transfers the evidence into non-visual prefix states, but Q alone is not the dominant carrier.

Inspect prospectively defined trailing prefix groups.

Do not force a Q-centric story.

---

## Pattern C — Strong cutoff retention + no prefix patch works

Possible explanations:

- token-group definition missed the true carrier;
- information is redundantly distributed across several prefix groups;
- patch implementation fails to preserve a distributed code;
- other special positions act as carriers.

Do not jump directly to reasoning-state memory.

---

## Pattern D — Weak generation-start cutoff retention

Interpretation:

> Prefill alone is insufficient; later direct visual access remains important.

This would motivate a different Stage 3B.1 centered on when post-prefill visual transfer occurs during reasoning.

---

## Pattern E — Partial heterogeneous retention

Interpretation:

> Visual-information strategy is example/evidence dependent.

Analyze:
- numeric vs structural evidence;
- evidence type;
- E0 position;
- reasoning length.

Do not filter heterogeneity away.

---

# 21. Scientific Claims Allowed

If supported, Stage 3B.0 may claim:

> A substantial fraction of visual evidence remains behaviorally distinguishable even when direct visual access is disabled from the first generated token.

and, if patching supports it:

> Image-conditioned non-visual prefix states causally carry visual evidence after prefill.

and, more specifically if Q patch succeeds:

> Question-token cached representations causally carry task-relevant visual evidence established during multimodal prefill.

---

# 22. Claims Not Yet Allowed

Stage 3B.0 must not yet claim:

- the exact layer where V→Q transfer occurs;
- Q is the only carrier;
- Q→R handoff occurs;
- reasoning states progressively accumulate evidence;
- visual information is stored in MLPs;
- a specific attention head/path implements transfer;
- direct vision becomes dispensable at a particular reasoning-time boundary beyond generation start;
- evidence B is later retrieved from Q during a specific reasoning subgoal;
- LOOK/THINK states exist.

These require later stages.

---

# 23. Decision for Stage 3B.1

At the end, recommend exactly one next action.

## GO — Layer-wise prefill V→Q/P localization

Use if:

- generation-start cutoff retains substantial evidence-specific CE across a large fraction of the 49 bases;
- broad non-visual prefix patching shows robust bidirectional evidence transfer;
- Q or another prospectively defined prefix group shows clear causal carrier behavior;
- technical controls pass.

Then Stage 3B.1 should localize **which layers create this prefill carrier** using layer-window patching/attention knockout and complementary readouts.

---

## CONDITIONAL GO — Carrier partition refinement

Use if:

- prefill sufficiency is strong;
- broad prefix states carry evidence;
- but Q alone does not localize it cleanly.

Before layer-wise analysis, refine the non-visual carrier partition.

---

## REDIRECT — Post-prefill acquisition timing

Use if:

- generation-start cutoff largely destroys Stage 3A's visual-content effect.

Then prefill transfer is insufficient, and the next stage should locate when direct visual access during reasoning establishes a sufficient non-visual state.

---

# 24. Output Structure

Create:

```text
outputs/stage3b0/
  config/
    stage3b0_config.json
    cohort_manifest.jsonl

  layout_audit/
    token_layout_audit.md
    token_group_definition.json
    cache_shape_diagnostics.json

  smoke/
    hook_transparency.json
    visual_cutoff_validation.md
    kv_patch_validation.md

  cutoff/
    per_problem_cutoff_results.jsonl
    cutoff_statistics.json
    rollout_results.jsonl

  patching/
    broad_prefix_patch_results.jsonl
    question_patch_results.jsonl
    optional_group_patch_results.jsonl
    patch_statistics.json

  analysis/
    prefill_sufficiency.md
    carrier_comparison.md
    evidence_type_analysis.md
    figures/

  summaries/
    stage3b0_summary.md
    stage3b0_acceptance.json
    stage3b1_recommendation.md
```

Do not overwrite Stage 3A or earlier artifacts.

---

# 25. Required Figures

At minimum:

1. Stage 3A full-vision CE vs generation-start-cutoff CE;
2. per-problem cutoff retention ratio \(\rho\);
3. original/counterfactual/sham evidence preference under cutoff;
4. broad-prefix patch recovery distribution;
5. Q-only patch recovery distribution;
6. broad-prefix vs Q recovery per problem;
7. numeric-label vs structural-edit strata;
8. representative causal patch examples.

---

# 26. Technical Acceptance Criteria

Stage 3B.0 technically passes if:

1. all 49 frozen Stage 3A base problems are attempted;
2. exact prompt/token layout is audited;
3. causal token groups are prospectively frozen;
4. original/counterfactual/sham text-token alignment is validated;
5. generation-start visual cutoff is verified;
6. hooked no-op inference is transparent;
7. grouped-query-attention cache layout is explicitly validated;
8. broad non-visual prefix patching is implemented bidirectionally;
9. Q-only patching is implemented bidirectionally;
10. self/sham patch controls are implemented;
11. evidence-specific CE and patch recovery metrics are produced;
12. base_problem_id remains the statistical unit;
13. attention is not used for cohort/target selection;
14. no layer-wise Stage 3B.1 experiment is started;
15. a GO / CONDITIONAL GO / REDIRECT recommendation is written.

Technical PASS does not require the preferred scientific result.

---

# 27. Stop Condition

After completing:

- layout audit,
- smoke validation,
- generation-start visual cutoff,
- broad-prefix patching,
- Q-only patching,
- controls,
- cohort statistics,
- interpretation,
- Stage 3B.1 recommendation,

**STOP.**

Do not start:

- layer-wise V→Q localization;
- layer-specific attention knockout;
- Q→R reasoning-time patching;
- module/head/path analysis;
- cutoff/reveal timing sweep;
- multi-evidence refresh experiments.

Return the complete Stage 3B.0 results for review.

Only after reviewing Stage 3B.0 together with Stages 2A–3A should Stage 3B.1 be designed.
