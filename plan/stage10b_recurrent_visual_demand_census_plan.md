# Stage 10B — Recurrent Visual-Demand Census and Candidate Discovery

## 0. One-line objective

Before testing causal perceptual-phase reopening, determine whether **natural long-form multimodal reasoning trajectories actually contain enough clean sequential/recurrent visual-demand episodes to justify that experiment**.

Primary question:

\[
\boxed{
\textbf{Do natural reasoning traces contain a resolved visual-demand episode,
an intervening text-sufficient reasoning period,
and then a genuinely new visual information demand that appears to trigger re-access?}
}
\]

This stage is a **census and go/no-go study**, not a causal reopening experiment.

---

# 1. Why this stage is necessary for the paper

Stage 10A-R established a bounded functional transition in successful controlled counting trajectories:

\[
\boxed{
\text{visual-access-dependent evidence resolution}
\rightarrow
\text{text-sufficient reasoning}
}
\]

However, the broader recurrent framework:

\[
V_A
\rightarrow
T_1
\rightarrow
V_B
\rightarrow
T_2
\rightarrow
V_A
\]

has **not** been measured as a complete within-trajectory cycle.

Prior Stage 4A established causal source retargeting / re-engagement of the form:

\[
A\rightarrow B\rightarrow A
\]

but did not establish that those source switches were separated by a text-sufficient regime or that a newly arising visual information demand reopened direct visual dependence.

Therefore, before spending compute on a causal reopening experiment, we must first answer:

> **Are there enough natural trajectories with this structure to make a recurrent-phase claim scientifically identifiable and worth testing?**

---

# 2. Paper-level value

This stage is not intended to create a new headline claim by itself.

Its main value is **story selection**.

## If clean recurrent-demand episodes are common enough

Proceed to a bounded causal test of:

\[
\boxed{
\text{new visual demand}
\rightarrow
\text{renewed visual necessity / source-specific retrieval}
}
\]

This could upgrade the paper from:

> visual-dependent reasoning transitions into text-sufficient reasoning

to:

> reasoning dynamically alternates between visual-evidence acquisition and text-sufficient regimes as information demands evolve.

## If clean episodes are rare

Do **not** force a recurrent-phase story.

Keep the stronger, already-supported claim:

\[
\boxed{
\text{visual-dependent evidence resolution}
\rightarrow
\text{text-sufficient reasoning}
}
\]

and retain Stage 4A as a separate result about dynamic causal source retargeting.

---

# 3. What a null does and does not mean

A low-yield census would mean:

> the current natural-task corpora do not provide enough clean recurrent-demand trajectories to support a recurrent phase-opening headline.

It would **not** establish that recurrent perceptual reopening is impossible.

Possible reasons for low yield include:

- the benchmark problems are front-loaded visually;
- the relevant information is extracted early;
- new subgoals rarely require genuinely unseen visual evidence;
- trajectories are too short or too compressed;
- visual facts are redundantly verbalized before later demand appears.

Therefore:

\[
\boxed{
\text{low natural yield}
\neq
\text{mechanism impossible}
}
\]

but it **does** imply that the paper should not claim recurrent phase organization without further evidence.

---

# 4. Competing explanations this census must distinguish

A later increase in image attention or retrieval score is not enough.

For each candidate event, distinguish the following cases.

## M1 — True new-demand candidate

\[
\text{resolved A}
\rightarrow
\text{text reasoning}
\rightarrow
\text{new demand B}
\rightarrow
\text{candidate B-specific visual re-access}
\]

Critically, B was not already available in the prior text.

## M2 — Previously textualized B

The later reasoning asks about B, but the needed B fact was already explicitly present or directly inferable from earlier text.

This is **not** a clean reopening candidate.

## M3 — Continued perceptual episode

A and B occur close together without an intervening text-sufficient / non-perceptual reasoning interval.

This is source switching inside one visual episode, not phase reopening.

## M4 — Image-aligned but demand-independent activity

The model shows image attention / retrieval-like activity without a clear new reasoning demand.

This is not evidence of demand-triggered reopening.

## M5 — New demand without candidate re-access

The reasoning develops a genuinely new B demand, but no plausible B-specific visual re-access follows.

This is scientifically important and must remain in the denominator.

---

# 5. Primary corpus

Use **existing natural-task traces first**.

No new model generation is allowed in the primary census unless required fields are unavailable.

Priority order:

1. existing Qwen3-VL-2B-Thinking MathVision traces from Stage 9A;
2. existing Qwen3-VL-2B-Thinking MathVerse traces from Stage 8A;
3. any other already-frozen natural-task Thinking traces with token-level reasoning text and compatible visual-routing summaries.

Reasons:

- these are natural reasoning tasks rather than the controlled counting corpus;
- Stage 8A already supplies a frozen passive retrieval signature on Qwen3-VL-2B-Thinking;
- the same detector transferred from MathVerse to MathVision;
- using existing traces keeps this stage nearly compute-free.

Do **not** use the Stage 10A-R controlled counting cohort as the primary census.

It may be referenced only as the established single-transition positive control.

---

# 6. Unit of analysis

Primary independent unit:

\[
\boxed{
\text{problem/image trajectory}
}
\]

For prevalence/yield reporting:

- count at most one primary recurrent-demand candidate per independent trajectory;
- if several exist, choose the earliest event satisfying the frozen selection rule;
- retain all additional events as secondary descriptive data.

Do not treat multiple events in one trajectory as independent samples.

---

# 7. Candidate event definition

A clean candidate must satisfy **all five** components below.

## C1 — Resolved visual episode A

There is an earlier visual fact/subgoal \(A\) that becomes resolved in the reasoning trace.

Evidence may include:

- an explicit visual fact;
- an inventory;
- an intermediate quantity;
- a relation determined from the image.

The earlier text must be sufficient to identify that A has been resolved semantically.

This is a semantic annotation, not a causal certificate.

---

## C2 — Intervening text-reasoning interval

After A is resolved, the trajectory must contain an interval dominated by reasoning over already available information.

Require at least one of:

- a distinct symbolic/logical subgoal;
- a multi-step calculation;
- a conclusion derived from previously stated facts;
- at least 24 generated tokens with no newly introduced task-critical visual fact.

The exact threshold is frozen before outcome review:

\[
\boxed{
24 \text{ generated tokens}
}
\]

The semantic criterion takes precedence; token length is a guardrail.

---

## C3 — New visual demand B

A later reasoning step introduces a subgoal that requires a visual fact \(B\) not yet resolved.

Examples:

- a new object attribute;
- a new spatial relation;
- another region/object;
- a quantity not derivable from the already verbalized evidence.

The demand should be identifiable from the reasoning text itself.

---

## C4 — B is not already available in prior text

This is the key exclusion.

Using only:

- question;
- options, if present;
- generated text before B demand;

a blinded reviewer must be unable to determine the required B fact.

Classify prior-text availability as:

- `ABSENT`
- `PARTIAL`
- `SUFFICIENT`
- `AMBIGUOUS`

Primary clean candidates require:

\[
\boxed{
\texttt{ABSENT}
}
\]

`PARTIAL` and `AMBIGUOUS` are retained as secondary.

`SUFFICIENT` is excluded from clean reopening candidates.

---

## C5 — Candidate B-specific visual re-access

Within a frozen post-demand window, there must be evidence consistent with renewed access to the B-relevant visual source.

Primary window:

\[
\boxed{
\text{first 32 generated tokens after B-demand onset}
}
\]

Evidence hierarchy:

1. frozen Stage 8A passive retrieval detector, where compatible;
2. target-vs-irrelevant ROI QK/attention/Value-transfer signature;
3. explicit visual observation in the reasoning text;
4. source-specific routing metadata already present in historical artifacts.

A clean candidate requires either:

- detector-positive target-specific retrieval, or
- convergent target-specific routing + explicit B observation.

Do **not** count raw image attention alone.

---

# 8. Sequential vs recurrent taxonomy

Annotate each clean candidate as one of:

## S1 — Sequential new demand

\[
A
\rightarrow
T
\rightarrow
B
\]

The later demand concerns a different visual fact/source.

## S2 — Return recurrence

\[
A
\rightarrow
T_1
\rightarrow
B
\rightarrow
T_2
\rightarrow
A
\]

The model later returns to a previously relevant visual source/fact.

## S3 — Multiple sequential demands

\[
A
\rightarrow
T_1
\rightarrow
B
\rightarrow
T_2
\rightarrow
C
\]

No return is required.

The causal reopening experiment only needs S1 to be viable.

S2 is especially valuable but must not be required for GO.

---

# 9. Annotation procedure

Use two passes.

## Pass 1 — Semantic demand annotation

Review only:

- question;
- image;
- reasoning text.

Do not show retrieval detector outputs.

Annotate:

- A resolution point;
- text-reasoning interval;
- B-demand onset;
- B target/source;
- prior-text availability of B;
- sequential/recurrent category.

## Pass 2 — Re-access annotation

Only after Pass 1 is frozen, reveal passive routing/retrieval signals.

Annotate:

- whether re-access occurs;
- timing relative to B demand;
- target specificity;
- confidence.

This prevents detector peaks from creating the semantic demand labels.

---

# 10. Blinding and disagreement

Use two independent annotation agents/review passes for the key labels:

- B-demand onset;
- B target/source;
- prior-text availability;
- clean candidate yes/no.

Resolve disagreement by adjudication **without viewing any future causal intervention outcomes**.

Report:

- raw agreement;
- Cohen's \(\kappa\) where appropriate;
- disagreement reasons.

The census is exploratory with respect to prevalence but the candidate definition must be frozen.

---

# 11. Passive retrieval detector use

The frozen Stage 8A detector is a **candidate signal**, not causal proof.

Permitted statement:

> retrieval-like visual access rises after a newly annotated B demand.

Not permitted:

> B demand causally reopened visual access.

That causal claim belongs to the next stage only.

Where detector compatibility is uncertain, report the event as `routing-only` rather than silently treating the detector as valid.

---

# 12. Primary endpoints

Freeze the following endpoints before reviewing re-access signals.

## E1 — Clean recurrent-demand yield

\[
\boxed{
Y_{\text{clean}}
=
\frac{
\# \text{independent trajectories satisfying C1--C5}
}{
\# \text{eligible trajectories}
}
}
\]

Report separately for:

- MathVision;
- MathVerse;
- pooled corpus.

---

## E2 — New-demand base rate

\[
Y_B
=
P(\text{C1--C4})
\]

This distinguishes:

- lack of new B demands

from:

- new demands that occur but do not show candidate re-access.

---

## E3 — Re-access given clean new demand

\[
P(\text{C5}\mid\text{C1--C4})
\]

This is the most important descriptive quantity for deciding whether a causal reopening test is worth running.

---

## E4 — Timing

For clean candidates:

\[
\Delta t
=
t_{\text{candidate re-access}}
-
t_{\text{B-demand onset}}
\]

Report:

- median;
- IQR;
- distribution up to 32 tokens.

---

## E5 — Sequential vs return recurrence

Report counts for:

- S1;
- S2;
- S3.

Do not overinterpret low-frequency S2 events.

---

# 13. Go / limited-go / no-go gate

Use independent trajectories, not event counts.

## Strong GO

Proceed to a full bounded causal reopening experiment if:

\[
\boxed{
\ge 24
}
\]

clean C1--C5 trajectories are found, with:

- at least 8 from each of two natural-task sources where available;
- no single source type accounting for >75% of candidates;
- acceptable annotation agreement.

This supports a 16-primary + 8-reserve causal design.

---

## Limited GO

If:

\[
\boxed{
12\text{--}23
}
\]

clean trajectories exist:

Proceed only to a **small causal pilot**.

Do not make a prevalence claim.

The pilot should answer whether the candidate phenomenon is causal at all.

---

## No GO

If:

\[
\boxed{
<12
}
\]

clean independent trajectories exist:

Stop the recurrent-phase branch.

Do not create synthetic tasks merely to rescue the headline.

Keep:

- Stage 10A-R phase transition;
- Stage 4A dynamic source retargeting;

as separate established findings.

---

# 14. Important negative cases to preserve

Do not discard trajectories that fail C5.

Create explicit categories:

- `NEW_DEMAND_NO_REACCESS`
- `B_ALREADY_TEXTUALIZED`
- `NO_TEXT_INTERVAL`
- `ATTENTION_ONLY`
- `TARGET_AMBIGUOUS`
- `TRACE_TOO_SHORT`
- `ROUTING_DATA_MISSING`

These negative categories are scientifically useful.

For example:

\[
\text{new B demand} + \text{no re-access}
\]

would directly constrain the recurrent-phase hypothesis.

---

# 15. No causal language in this stage

This stage may support:

> Natural long-form reasoning contains candidate sequential/recurrent visual-demand episodes in which new information needs are followed by target-specific retrieval-like activity.

It may **not** support:

> New reasoning demand causally reopens perception.

Nor:

> The model repeatedly alternates between visual and textual phases.

Those require the next causal experiment.

---

# 16. Minimal optional verification

Only if historical artifacts lack enough routing detail to classify C5:

Run a tiny **forward-only passive instrumentation repair** on a frozen subset.

Maximum:

\[
\boxed{
32 \text{ trajectories}
}
\]

No ablations, source substitutions, or causal interventions.

Purpose:

- reconstruct the frozen retrieval detector / target-specific routing traces.

Target GPU budget:

\[
\boxed{
<1 \text{ GPU-hour}
}
\]

If the needed traces already exist, allocate zero GPU.

---

# 17. Statistics

This is primarily a yield/candidate-discovery stage.

Report:

- Wilson or exact binomial 95% intervals for trajectory-level proportions;
- dataset-stratified estimates;
- annotation agreement;
- target-type breakdown;
- length-matched descriptive sensitivity if needed.

Do not run large multiple-hypothesis significance searches.

The key decision is the frozen GO gate.

---

# 18. Figures

## Figure 1 — Candidate anatomy

Show one clean example:

\[
A
\rightarrow
\text{text reasoning}
\rightarrow
B\text{ demand}
\rightarrow
B\text{-specific re-access}
\]

with:

- reasoning text;
- semantic anchors;
- detector/routing trace.

## Figure 2 — Census flow

Flow diagram:

\[
\text{all traces}
\rightarrow
\text{new B demand}
\rightarrow
\text{B absent from prior text}
\rightarrow
\text{candidate re-access}
\]

with counts at each step.

## Figure 3 — Timing

Distribution of:

\[
t_{\text{re-access}}-t_{\text{B-demand}}
\]

## Figure 4 — Candidate taxonomy

Counts of:

- S1 sequential;
- S2 return recurrence;
- S3 multiple sequential;
- negative categories.

---

# 19. Required artifacts

Produce:

1. `stage10b_recurrent_demand_census_spec.md`
2. `stage10b_corpus_manifest.json`
3. `stage10b_semantic_annotations.parquet`
4. `stage10b_reaccess_annotations.parquet`
5. `stage10b_candidate_events.parquet`
6. `stage10b_negative_cases.parquet`
7. `stage10b_annotation_agreement.json`
8. `stage10b_yield_inference.json`
9. `stage10b_go_nogo_decision.json`
10. `stage10b_resource_accounting.json`
11. `stage10b_summary.md`

Optional, only if passive repair is needed:

12. `stage10b_passive_reinstrumentation.parquet`

---

# 20. Resource budget

Primary census:

\[
\boxed{
\text{CPU / annotation only}
}
\]

Target new GPU use:

\[
\boxed{
0 \text{ GPU-hours}
}
\]

Optional passive repair hard cap:

\[
\boxed{
<1 \text{ GPU-hour}
}
\]

No new benchmark-scale generation.

No causal intervention in this stage.

---

# 21. Interpretation table

| Result | Interpretation | Next action |
|---|---|---|
| ≥24 clean trajectories | Natural recurrent-demand phenomenon has sufficient yield | Design bounded causal reopening test |
| 12–23 clean trajectories | Phenomenon exists but is sparse | Small causal pilot only |
| <12 clean trajectories | Current natural corpora do not support recurrent-phase headline | Stop recurrent branch |
| Many C1–C4 but few C5 | New demands arise, but passive re-access is weak/rare | Do not assume reopening |
| Few C1–C4 | Tasks are mostly front-loaded visually | Keep single-transition phase claim |
| Many B_ALREADY_TEXTUALIZED | Later "visual" subgoals often rely on previously extracted evidence | Strengthens text-sufficiency interpretation |

---

# 22. Paper claim dependency

This stage exists to decide whether the paper should remain at:

\[
\boxed{
\text{visual evidence resolution}
\rightarrow
\text{text-sufficient reasoning}
}
\]

or whether it is justified to test the broader claim:

\[
\boxed{
\text{reasoning demand dynamically reopens perceptual access}
}
\]

The recurrent claim must not be promoted merely because it is conceptually elegant.

It must first have adequate natural support.

---

# 23. Exactly one recommendation at completion

## If Strong GO

Recommend:

> Run a bounded causal reopening experiment on the frozen clean recurrent-demand cohort, testing whether visual necessity and source-specific causal dependence rise after the new B demand.

## If Limited GO

Recommend:

> Run only a small causal pilot on the cleanest frozen cases; do not promote recurrence to a headline claim yet.

## If No GO

Recommend:

> Stop the recurrent-phase branch and finalize the paper around the established visual-dependent to text-sufficient transition plus dynamic source retargeting as a separate result.

Do not launch any follow-up automatically.

---

# 24. Final decision target

The sole decision this stage must make is:

\[
\boxed{
\textbf{Are there enough naturally occurring, clean recurrent visual-demand trajectories
to justify a causal perceptual-reopening experiment?}
}
\]

If yes, freeze those cases and test causality next.

If no, stop.
