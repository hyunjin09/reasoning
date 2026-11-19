# Stage 10C — Causal Reopening of Visual Dependence After New Demand

## 0. One-line objective

Test whether a **new visual information demand that arises after an intervening text-reasoning interval causally reopens direct, source-specific visual dependence**.

Primary question:

\[
oxed{
	extbf{When a new subgoal requires visual evidence absent from the current reasoning trace,
does direct visual dependence rise again specifically for the newly demanded source?}
}
\]

This stage is the causal follow-up to the Stage 10B natural recurrent-demand census.

---

# 1. Why this experiment is necessary for the paper

The paper now has two strong but separate pieces.

## Stage 10A-R

Within successful controlled trajectories:

\[
oxed{
	ext{visual-access-dependent evidence resolution}
ightarrow
	ext{text-sufficient reasoning}
}
\]

Direct visual necessity falls sharply once task-relevant evidence is resolved in the reasoning trace.

## Stage 10B

Across 224 frozen natural MathVision/MathVerse Thinking trajectories:

- 37/224 satisfy the semantic C1–C4 structure;
- 26/224 are clean C1–C5 passive candidates;
- 26/37 semantic-positive cases show qualifying target-specific re-access;
- all 26 primary clean trajectories are sequential S1 cases;
- no clean S2 return recurrence was observed.

Thus natural trajectories exist with:

\[
oxed{
A	ext{ resolved}
ightarrow
T
ightarrow
	ext{new unresolved }B	ext{ demand}
ightarrow
	ext{B-specific retrieval-like activity}
}
\]

But Stage 10B is passive.

It does **not** establish that the post-demand activity is functionally necessary, source-specific in a causal sense, or a genuine reopening of visual dependence.

Stage 10C tests that missing causal link.

---

# 2. Exact paper claim enabled by success

If the primary gate passes:

> **A text-reasoning interval is not necessarily terminal for direct perception: when a new subgoal requires visual evidence that is absent from the current reasoning trace, direct visual dependence can causally re-emerge.**

If source specificity also passes:

> **The renewed dependence is concentrated on the visual source required by the new subgoal rather than reflecting generic image use.**

Combined formulation:

\[
oxed{
	extbf{New unresolved visual demand can reopen direct, source-specific visual dependence
after an intervening text-reasoning interval.}
}
\]

Do **not** claim:

- universal recurrent alternation;
- repeated \(Aightarrow Bightarrow A\) phase cycles;
- that every new subgoal reopens vision;
- that visual access is the only available carrier.

The observed Stage 10B topology supports:

\[
oxed{
V_Aightarrow Tightarrow V_B
}
\]

not a full recurrent oscillation.

---

# 3. What a null would and would not rule out

A clean null would constrain the strong reopening account for the tested natural candidates.

It would support one of several alternatives:

- passive target alignment without causal use;
- sufficient latent/internal image-derived state despite absent explicit text;
- diffuse/global image dependence rather than B-specific dependence;
- intervention redundancy;
- a routing signature that does not reflect functionally necessary retrieval.

A null would **not** prove that reopening is impossible in all multimodal reasoning.

It would not rule out:

- other tasks;
- other models;
- stronger or different visual demands;
- redundant visual pathways;
- intervention weakness;
- reopening outside the frozen local window.

Therefore:

\[
oxed{
	ext{null here}
\Rightarrow
	ext{do not promote causal reopening as a headline claim}
}
\]

not:

\[
	ext{reopening never occurs.}
\]

---

# 4. Competing mechanisms to discriminate

## M1 — True causal reopening

Before B demand, direct visual access has low local causal value.

After B demand:

\[
	ext{visual dependence rises}
\]

and the demanded B source matters more than an irrelevant source.

Expected:

\[
D_{	ext{POST-all}}
>
D_{	ext{PRE-all}}
\]

and:

\[
D_{	ext{POST-target}}
>
D_{	ext{POST-irrelevant}}
\]

## M2 — Continuous visual dependence

The model was already visually dependent during the preceding text interval.

Expected:

\[
D_{	ext{POST-all}}
pprox
D_{	ext{PRE-all}}
\]

with both substantial.

## M3 — Passive retrieval-like alignment

Stage 10B routing rises after B demand, but the routed visual information is not functionally important.

Expected:

\[
D_{	ext{POST-all}}pprox 0
\]

and:

\[
D_{	ext{POST-target}}pprox D_{	ext{POST-irrelevant}}pprox 0.
\]

## M4 — Generic image reopening

Post-demand image access becomes useful, but not specifically through B.

Expected:

\[
D_{	ext{POST-all}}
>
D_{	ext{PRE-all}}
\]

but:

\[
D_{	ext{POST-target}}
pprox
D_{	ext{POST-irrelevant}}.
\]

## M5 — Redundant B-source access

All-image blocking hurts after B demand, but blocking the annotated B ROI alone does not.

Interpret as redundancy / imperfect ROI localization, not as evidence against all reopening.

---

# 5. Model and runtime

Use:

\[
oxed{
	extbf{Qwen3-VL-2B-Thinking}
}
\]

Freeze the exact historical execution path compatible with Stage 8A / Stage 9A artifacts:

- exact checkpoint revision;
- native Thinking template;
- BF16;
- TF32 off;
- greedy decoding;
- original image preprocessing;
- original generation cap unless a frozen short local assay is used;
- same attention/routing backend where technically possible.

No model comparison in this stage.

No CoT arm.

No new benchmark generation.

---

# 6. Frozen candidate cohort

Stage 10B found:

\[
oxed{
26 	ext{ clean independent C1--C5 trajectories}
}
\]

A raw anchor-gap sensitivity requiring at least 24 tokens between the resolved-A quote and B onset retains:

\[
oxed{
24 	ext{ clean trajectories}
}
\]

Use these 24 as the causal experiment pool because they support a matched pre-demand control window.

No candidate may be added after causal outcomes are opened.

## Primary / reserve split

Before interventions:

- 16 primary trajectories;
- 8 reserve trajectories.

Select by deterministic hash within dataset, balancing MathVision / MathVerse as closely as the 24-case pool permits.

Do not select based on:

- detector magnitude;
- routing strength;
- baseline correctness;
- expected intervention sensitivity;
- final answer correctness.

The two Stage 10B clean trajectories failing the 24-token gap criterion are excluded from the core matched-window causal test but may be retained only as descriptive non-primary cases.

---

# 7. Frozen semantic anchors

Reuse Stage 10B sealed annotations.

For every candidate:

- \(A_{	ext{resolved}}\): earlier visual fact/subgoal resolution;
- \(T\): intervening text-reasoning interval;
- \(B_{	ext{onset}}\): onset of the new visual information demand;
- \(ROI_B\): demanded B source/region;
- \(ROI_C\): matched irrelevant control region;
- prior B availability = `ABSENT`.

No anchor may be moved after intervention results.

No new B target may be substituted post hoc.

---

# 8. Matched local windows

Use a fixed:

\[
oxed{
24	ext{-generated-token window}
}
\]

for the core matched intervention.

## PRE window

The final 24 generated tokens of the sealed intervening text-reasoning interval immediately preceding \(B_{	ext{onset}}\).

This window must not contain a newly introduced B fact.

## POST window

The first 24 generated tokens beginning at \(B_{	ext{onset}}\).

After the 24-token intervention window, restore normal visual access and continue generation.

This local design distinguishes:

> "visual access mattered somewhere later"

from:

> "visual dependence specifically rose when the new B demand appeared."

---

# 9. Block A — Causal reopening necessity

For each primary trajectory run:

1. `NATIVE / NO-OP`
2. `PRE_ALL_OFF`
3. `POST_ALL_OFF`

## PRE_ALL_OFF

During the PRE window only:

\[
	ext{generated-query}ightarrow	ext{all image keys}
\]

is blocked across the same decoder layers used by the validated full-access mask implementation.

After 24 tokens, restore normal visual access.

## POST_ALL_OFF

Apply the identical mask only during the POST window.

After 24 tokens, restore normal visual access.

Everything else remains unchanged.

---

# 10. Why the PRE control is essential

A post-demand mask alone cannot identify reopening.

If blocking vision after B demand causes failure, that only shows:

> image access mattered after B demand.

It does **not** show that dependence increased relative to the prior text-reasoning interval.

The causal reopening contrast is:

\[
oxed{
R
=
D_{	ext{POST-all}}
-
D_{	ext{PRE-all}}
}
\]

Positive \(R\) means the same local visual-access removal is more damaging after the new B demand than immediately before it.

---

# 11. Block B — Source specificity

For each primary trajectory run in the POST window:

4. `POST_TARGET_OFF`
5. `POST_IRRELEVANT_OFF`

## POST_TARGET_OFF

Block generated-query access only to image tokens in the frozen demanded B ROI.

## POST_IRRELEVANT_OFF

Block a matched-size control ROI selected and sealed before outcomes.

Control matching priority:

1. same number of image tokens;
2. same image;
3. similar spatial compactness;
4. not overlapping the B target;
5. not annotated as another currently necessary source.

The primary specificity contrast is:

\[
oxed{
S
=
D_{	ext{POST-target}}
-
D_{	ext{POST-irrelevant}}
}
\]

Positive \(S\) supports source-specific causal dependence.

---

# 12. Local outcome annotation

Final answer correctness is **not** the primary endpoint.

Prior project results already show that:

\[
	ext{final task correctness}

eq
	ext{local visual grounding correctness}.
\]

Therefore the primary behavioral endpoint is **local B resolution**.

Before interventions, seal for each trajectory:

- the B question/subgoal;
- the correct B fact from the image;
- the native B-evidence span, if present;
- accepted semantic paraphrases;
- whether B is numeric, categorical, relational, or structured.

Score the first:

\[
oxed{
64 	ext{ generated tokens after }B_{	ext{onset}}
}
\]

for:

- `B_CORRECT`
- `B_WRONG`
- `B_UNRESOLVED`
- `NO_FINAL_LOCAL_READ`

Primary binary score:

\[
Y_B=1
\]

iff the continuation resolves B correctly.

All scoring rules must be sealed before causal outputs are reviewed.

---

# 13. Teacher-forced mechanistic endpoint

To avoid relying only on free-generation branching, add a paired teacher-forced endpoint using the frozen native B-evidence span.

For the exact native continuation tokens, measure intervention-induced increase in negative log-likelihood over the B-evidence span:

\[
\Delta \mathrm{NLL}_B.
\]

Primary mechanistic contrasts:

\[
oxed{
\Delta\mathrm{NLL}_{B,	ext{POST-all}}
-
\Delta\mathrm{NLL}_{B,	ext{PRE-all}}
}
\]

and:

\[
oxed{
\Delta\mathrm{NLL}_{B,	ext{POST-target}}
-
\Delta\mathrm{NLL}_{B,	ext{POST-irrelevant}}
}
\]

This endpoint:

- holds the continuation path fixed;
- is defined even when free generation diverges;
- does not replace the behavioral endpoint.

Use it as convergent causal evidence.

---

# 14. Native B correctness strata

Do not select the primary cohort on native correctness.

Instead report:

## Full intention-to-test cohort

All 16 primary trajectories.

## Source-faithful native stratum

Trajectories whose native continuation resolves B correctly.

This stratum gives the clearest semantic interpretation of target-specific damage.

## Native-wrong / unresolved stratum

Retain descriptively.

Do not relabel intervention-induced changes as improvement or harm based only on final answer.

---

# 15. Primary endpoints

Freeze four primary endpoints.

## P1 — Behavioral reopening

\[
oxed{
P1
=
Acc_B(	ext{PRE_ALL_OFF})
-
Acc_B(	ext{POST_ALL_OFF})
}
\]

Expected:

\[
P1>0.
\]

## P2 — Mechanistic reopening

\[
oxed{
P2
=
\Delta\mathrm{NLL}_{B,	ext{POST-all}}
-
\Delta\mathrm{NLL}_{B,	ext{PRE-all}}
}
\]

Expected:

\[
P2>0.
\]

## P3 — Behavioral source specificity

\[
oxed{
P3
=
Acc_B(	ext{POST_IRRELEVANT_OFF})
-
Acc_B(	ext{POST_TARGET_OFF})
}
\]

Expected:

\[
P3>0.
\]

## P4 — Mechanistic source specificity

\[
oxed{
P4
=
\Delta\mathrm{NLL}_{B,	ext{POST-target}}
-
\Delta\mathrm{NLL}_{B,	ext{POST-irrelevant}}
}
\]

Expected:

\[
P4>0.
\]

Use problem/image-level paired bootstrap inference.

---

# 16. Primary claim gate

Support:

> **new unresolved visual demand causally reopens direct, source-specific visual dependence**

only if:

1. P1 has the expected positive direction;
2. P2 has the expected positive direction;
3. P3 has the expected positive direction;
4. P4 has the expected positive direction;
5. the reopening effect is not driven by one dataset only;
6. source specificity survives the source-faithful native stratum;
7. no small subgroup or single trajectory dominates the result;
8. technical mask validation passes.

The strongest version requires both reopening and specificity.

---

# 17. Tiered interpretation

## Outcome A — Reopening + source specificity

Supported:

> **A new visual information demand can causally reopen direct visual dependence, concentrated on the newly required source.**

## Outcome B — Reopening without source specificity

Supported:

> **direct visual dependence re-emerges after the new demand.**

Not supported:

> the reopened dependence is cleanly B-specific.

## Outcome C — Source specificity without clear PRE→POST increase

Supported:

> **the new subgoal engages a B-specific causal visual source.**

Not supported:

> visual dependence was reopened from a previously low-dependence state.

This favors continuous visual dependence / retargeting over phase reopening.

## Outcome D — Neither

Do not promote reopening.

Keep:

- Stage 10A-R phase transition;
- Stage 4A source retargeting;
- Stage 10B natural candidate census

as separate findings.

---

# 18. Optional Block C — Demand-swap closure

Run only if the primary reopening + source-specificity gate passes.

Purpose:

> test whether changing the current reasoning demand changes which visual source becomes causally important.

Use at most:

\[
oxed{
8 	ext{ trajectories}
}
\]

with cleanly separable alternative visual subgoals.

Construct, before intervention outcomes:

- original B-demand continuation;
- matched alternative-demand continuation \(B'\).

Hold fixed:

- image;
- all prior reasoning text;
- token budget.

Change only the local demand clause.

Test whether causal source dependence switches:

\[
ROI_B
ightarrow
ROI_{B'}.
\]

This optional block is the direct causal closure for:

\[
oxed{
	ext{reasoning demand selects the reopened source}
}
\]

Do not run if alternative demand construction is semantically unnatural.

---

# 19. Technical validation

Before primary execution, use exactly three non-primary / reserve-compatible cases.

Validate:

1. native prefix token IDs exactly match the frozen trace;
2. no-op resumed continuation matches native logits/tokens over the validation span;
3. PRE mask affects only the PRE window;
4. POST mask affects only the POST window;
5. access is restored after the 24-token window;
6. target ROI mask does not touch control ROI;
7. irrelevant ROI has matched token count;
8. teacher-forced NLL path uses the exact frozen native continuation;
9. no image preprocessing drift;
10. cache/resume behavior is stable.

If any validation fails, fix the implementation before opening primary outcomes.

Do not alter anchors or candidate membership.

---

# 20. Mask-control discipline

The project has previously observed that standard masking and null-sink masking can behave differently.

Therefore:

- the primary claim is explicitly intervention-specific;
- use the same standard generated-query→image-key blocking path already validated in this project;
- do not infer that masked information is literally absent from all internal state;
- prior image-derived cache/state before the local window remains intact.

For source specificity, the matched irrelevant ROI is the primary structural control.

Optional null-sink calibration may be run on at most 4 reserve cases only if the standard-mask result is strong and a reviewer-facing control is needed.

Do not make it a new full branch.

---

# 21. Statistics

Independent unit:

\[
oxed{
	ext{trajectory / problem-image pair}
}
\]

Use:

- paired trajectory-level effects;
- equal trajectory weighting;
- 4,000 bootstrap draws;
- fixed seed;
- 95% percentile intervals;
- multiplicity-aware intervals for P1–P4.

Also report:

- MathVision / MathVerse point estimates;
- leave-one-out sensitivity;
- source-faithful native stratum;
- target type breakdown;
- free-generation completion rates.

Do not treat tokens, windows, ROI patches, or repeated conditions as independent samples.

---

# 22. Reserve rule

Open the 8 reserve trajectories only if:

1. all four primary point estimates have the expected direction;
2. at least one key interval is precision-limited;
3. no technical failure exists;
4. the result is not clearly null or directionally inconsistent.

Run the identical frozen protocol.

If the primary 16 are directionally inconsistent, stop.

Do not use reserve to rescue a failed claim.

---

# 23. Compute budget

Primary logical conditions per trajectory:

- NATIVE / NO-OP reuse where exact historical continuation is available;
- PRE_ALL_OFF;
- POST_ALL_OFF;
- POST_TARGET_OFF;
- POST_IRRELEVANT_OFF;
- teacher-forced scoring under the same four intervention conditions.

Primary cohort:

\[
16 	ext{ trajectories}
\]

Reserve:

\[
8.
\]

Target GPU budget:

\[
oxed{
<2 	ext{ GPU-hours primary}
}
\]

Reserve extension target:

\[
oxed{
<1 	ext{ additional GPU-hour}
}
\]

Optional Block C:

\[
oxed{
<1 	ext{ GPU-hour}
}
\]

Hard project stop before exceeding:

\[
oxed{
4 	ext{ GPU-hours total}
}
\]

without explicit approval.

---

# 24. Required figures

## Figure 1 — Causal reopening schematic

\[
A_{	ext{resolved}}
ightarrow
T
ightarrow
B_{	ext{demand}}
\]

with PRE and POST intervention windows.

## Figure 2 — Behavioral reopening

Plot:

\[
Acc_B(	ext{PRE_ALL_OFF})
\]

vs:

\[
Acc_B(	ext{POST_ALL_OFF})
\]

paired by trajectory.

## Figure 3 — Mechanistic reopening

Plot paired:

\[
\Delta \mathrm{NLL}_B
\]

for PRE vs POST all-image masks.

## Figure 4 — Source specificity

Compare:

\[
	ext{POST_TARGET_OFF}
\]

vs:

\[
	ext{POST_IRRELEVANT_OFF}.
\]

## Figure 5 — Integrated paper framework

Only if Outcome A:

\[
oxed{
V_A
ightarrow
T
ightarrow
V_B
}
\]

with the explicit note:

> observed natural sequential reopening; not evidence of universal repeated alternation.

---

# 25. Required artifacts

Produce:

1. `stage10c_causal_reopening_spec.md`
2. `stage10c_frozen_candidate_split.json`
3. `stage10c_b_gold_annotations.json`
4. `stage10c_roi_controls.json`
5. `stage10c_technical_validation.json`
6. `stage10c_free_generation_results.parquet`
7. `stage10c_teacher_forced_nll.parquet`
8. `stage10c_primary_inference.json`
9. `stage10c_source_faithful_sensitivity.json`
10. optional `stage10c_reserve_extension.json`
11. optional `stage10c_demand_swap.json`
12. `stage10c_resource_accounting.json`
13. `stage10c_summary.md`

---

# 26. Paper integration if successful

Stage 10A-R:

\[
oxed{
V_Aightarrow T
}
\]

Stage 10B:

\[
oxed{
V_Aightarrow Tightarrow
	ext{new unresolved demand }B
ightarrow
	ext{passive B-specific re-access candidate}
}
\]

Stage 10C, if successful:

\[
oxed{
V_Aightarrow Tightarrow V_B
}
\]

Together this supports:

> **Multimodal reasoning is phase-structured in a functional sense: direct visual dependence can fall after evidence resolution and later re-emerge when a new subgoal requires visual evidence not already available in the reasoning trace.**

Do not upgrade this to:

> reasoning repeatedly alternates between visual and text phases

without observed repeated within-trajectory causal cycles.

---

# 27. Next-stage logic

## If Outcome A

The sequential phase-reopening story is causally supported.

Next priority should be **small natural-task / model-family generalization**, not another deeper reopening search.

Optional demand-swap closure is allowed first if not already run.

## If Outcome B

Keep causal reopening, but describe source specificity cautiously.

## If Outcome C

Frame the result as dynamic source retargeting under continuing visual dependence.

Do not call it phase reopening.

## If Outcome D

Stop the reopening branch.

Return to the already-supported core paper:

1. phase transition \(Vightarrow T\);
2. reasoning-conditioned source retargeting;
3. causal text carriage;
4. alignment \(
eq\) retrieval;
5. native use \(
eq\) ablation necessity.

---

# 28. Exactly one recommendation at completion

If the primary gate passes:

> Integrate causal visual reopening into the main phase-structured framework and next test only minimal cross-task/model generalization.

If the gate fails:

> Stop the reopening branch and finalize the paper around the already-established visual-to-text transition plus dynamic source retargeting as a separate causal phenomenon.

Do not launch follow-up work automatically.

---

# 29. Final decision target

This experiment exists to answer one paper-level question:

\[
oxed{
	extbf{After reasoning has moved through a nonvisual/text interval,
does a new unresolved visual information demand causally restore
direct dependence on the newly required visual source?}
}
\]

If yes, the paper gains a causal \(Vightarrow Tightarrow V\) sequential-transition result.

If no, do not claim causal reopening.
