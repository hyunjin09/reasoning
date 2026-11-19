# Stage 11A — Visual-Evidence Bottleneck Census for Thinking vs CoT

## 0. One-line objective

Decompose matched multimodal reasoning failures into **visual-evidence availability**, **native evidence access/externalization**, and **downstream reasoning/utilization** bottlenecks, and determine which bottleneck is most plausibly associated with the performance advantage of native Thinking over prompted CoT.

Primary question:

\[
\boxed{
\textbf{When Thinking succeeds where CoT or Direct fails, is the advantage mainly in
obtaining the required visual evidence, accessing it during native reasoning,
or reasoning correctly once the evidence is already available?}
}
\]

This is a **bounded bottleneck census and feasibility stage**.

It is not yet the full causal Equal-Evidence Oracle experiment.

---

# 1. Why this stage is necessary for the paper

Claims 1 and 2 are already substantially supported.

## Claim 1

\[
\boxed{
\text{reasoning demand}
\rightarrow
\text{target-specific causal visual retrieval}
}
\]

The project has causal source-switching, context-intervention, demand-vs-mention, and retrieval-detector evidence.

## Claim 2

\[
\boxed{
\text{visual retrieval}
\rightarrow
\text{internal/textual causal carriers}
\rightarrow
\text{text-sufficient reasoning}
}
\]

Stage 10A / 10A-R established:

- generated visual reasoning text can be causally used;
- direct visual necessity falls as evidence becomes resolved;
- fresh text-only sufficiency rises sharply after evidence resolution.

The major remaining scientific question is therefore:

\[
\boxed{
\textbf{Where does the pipeline fail, and what does Thinking improve?}
}
\]

This is the multimodal analogue of separating:

> information unavailable

from:

> information available but not successfully accessed

from:

> information available and accessed but not correctly used.

The goal is to connect the mechanistic retrieval/lifecycle findings to actual performance differences.

---

# 2. Paper claim this stage can support

Stage 11A alone can support a **descriptive bottleneck decomposition**, not a complete causal explanation of Thinking.

Target outcome-neutral sentence:

> **We decompose multimodal reasoning failures into visual-evidence availability, native evidence-access, and downstream-utilization bottlenecks, and identify which bottleneck is preferentially associated with successful Thinking trajectories.**

A stronger causal sentence about why Thinking is better requires Stage 11B Equal-Evidence Oracle.

---

# 3. The pipeline to decompose

For each item, define a minimal task-critical visual evidence set:

\[
E^*
\]

and decompose the reasoning pipeline as:

\[
\boxed{
\text{Image}
\rightarrow
\text{probe-accessible }E^*
\rightarrow
\text{native reasoning access to }E^*
\rightarrow
\text{downstream reasoning}
\rightarrow
\text{answer}
}
\]

Three candidate bottlenecks follow.

## B1 — Evidence-availability limitation

Even when the required visual evidence is explicitly requested, the model fails to recover \(E^*\).

## B2 — Native evidence-access limitation

The model can recover \(E^*\) under an explicit visual probe, but \(E^*\) is absent, wrong, or incomplete in the native problem-solving trajectory.

## B3 — Downstream reasoning/utilization limitation

The native trajectory contains correct sufficient \(E^*\), but the model still reaches an incorrect task answer.

---

# 4. Terminology discipline

Do **not** use `encoded` / `not encoded` as the primary terminology.

The image remains an external input and direct probing changes the demand state.

Use:

- `PROBE_ACCESSIBLE`
- `PROBE_INACCESSIBLE`
- `NATIVE_EVIDENCE_CORRECT`
- `NATIVE_EVIDENCE_PARTIAL`
- `NATIVE_EVIDENCE_WRONG`
- `NATIVE_EVIDENCE_ABSENT`
- `DOWNSTREAM_FAILURE`

Safe interpretation:

> the evidence is recoverable when directly requested

not:

> the model definitely encoded the evidence internally.

Likewise, absence from the generated trace does **not** prove absence from hidden state.

---

# 5. Model and existing matched corpus

Primary feasibility corpus:

\[
\boxed{
\textbf{Qwen3-VL-2B}
}
\]

using the existing Stage 9A matched MathVision family:

- Direct;
- prompted CoT;
- native Thinking.

Reuse the already-frozen native trajectories.

No baseline regeneration unless an artifact is technically missing.

Important scope:

> the CoT arm is the exact prompted-CoT protocol used in Stage 9A.

Do not generalize the result to every possible CoT prompting strategy.

---

# 6. Corpus construction

Start from all existing:

\[
\boxed{
128 \text{ Stage 9A MathVision families}
}
\]

with the same underlying image/question available across Direct / CoT / Thinking.

## Phase A — Evidence identifiability review

Review all 128 items without looking at model accuracy by mode.

Classify each item as:

- `E_STAR_ELIGIBLE`
- `E_STAR_AMBIGUOUS`
- `E_STAR_TOO_LARGE`
- `NO_VISUAL_BOTTLENECK`
- `ANNOTATION_UNRESOLVED`

Primary Stage 11A analysis uses only `E_STAR_ELIGIBLE` items.

Eligibility must be determined **without seeing Direct / CoT / Thinking correctness**.

---

# 7. Definition of \(E^*\)

For each eligible item:

\[
\boxed{
E^* =
\text{the smallest human-verifiable set of image-derived propositions
needed to solve the task once the nonvisual problem text is known}
}
\]

\(E^*\) may contain 1–4 atomic facts.

Examples:

- `number of red triangles = 4`
- `angle ABC = 60°`
- `segment AB is perpendicular to CD`
- `point P lies inside the circle`
- `the graph crosses y=2 at x=3 and x=7`

## Exclude from \(E^*\)

Do not include:

- arithmetic consequences that should be derived by reasoning;
- final answer labels;
- purely textual facts already given in the question;
- unnecessary visual details.

The aim is to isolate **visual evidence**, not solve the downstream reasoning in advance.

---

# 8. \(E^*\) sufficiency check

Before any model probe outcomes are opened, validate that:

\[
\boxed{
\text{question text} + E^*
}
\]

is sufficient in principle to determine the correct answer.

Use two independent semantic-review passes.

For each item mark:

- `SUFFICIENT`
- `INSUFFICIENT`
- `AMBIGUOUS`

Only `SUFFICIENT` items enter the primary bottleneck analysis.

If the reviewers disagree, adjudicate before opening model outcomes.

This protects against mistakenly calling downstream failure when the provided evidence set was incomplete.

---

# 9. Evidence annotation schema

Represent \(E^*\) as atomic propositions:

\[
E^*=\{e_1,\ldots,e_k\}
\]

with \(1\le k\le4\).

For every atomic evidence unit store:

- evidence type;
- source ROI / visual referent where identifiable;
- normalized gold value;
- accepted paraphrases;
- whether exact lexical expression is required;
- whether the evidence is directly visible or requires trivial visual aggregation.

Examples of evidence types:

- count;
- color;
- shape;
- spatial relation;
- angle/length label;
- graph coordinate;
- diagram topology;
- chart/table lookup;
- ordering/comparison.

---

# 10. Block A — Explicit visual-evidence probe

For every eligible item, ask the model **directly for \(E^*\)** using the original image.

Do this under all three modes:

\[
\boxed{
\text{Direct},\quad
\text{CoT},\quad
\text{Thinking}
}
\]

Use a mode-matched template but the same semantic request.

Example structure:

> Inspect the image and report only the following task-relevant visual facts needed for the problem: [requested attributes / relations]. Do not solve the original problem.

The prompt may specify which quantities/relations to report but must not reveal their values.

## Output scoring

For each \(e_i\):

- `CORRECT`
- `WRONG`
- `MISSING`
- `AMBIGUOUS`

Item-level:

- `PROBE_ACCESSIBLE` if all required \(e_i\) are correct;
- `PROBE_PARTIAL` if some but not all are correct;
- `PROBE_INACCESSIBLE` otherwise.

This is a **capability-under-explicit-demand** assay.

It is not a native reasoning measurement.

---

# 11. Block B — Native reasoning evidence state

Reuse the original Stage 9A Direct / CoT / Thinking trajectories.

For each mode and each eligible item, annotate whether \(E^*\) appears in the native trajectory before the final answer.

## Native evidence states

### N0 — ABSENT

No sufficient evidence corresponding to \(E^*\) appears.

### N1 — PARTIAL

Only a subset of the required evidence is correctly present.

### N2 — CORRECT_SUFFICIENT

All necessary \(E^*\) is correctly present or directly inferable from the generated reasoning text.

### N3 — WRONG

The trajectory explicitly contains an incorrect task-critical visual fact.

### N4 — CONFLICTING

Correct and incorrect versions coexist or the state changes during reasoning.

### N5 — NOT_EXTERNALIZED

The trace does not expose enough evidence to classify.

`N5` must remain separate from `N0`.

Generated-text absence is not proof of hidden-state absence.

---

# 12. Native answer outcome

For the original problem-solving trajectory, record:

- `FINAL_CORRECT`
- `FINAL_WRONG`
- `NO_VALID_FINAL`

Do not collapse `NO_VALID_FINAL` into a visual-error category.

Retain benchmark scoring separately from local evidence state.

---

# 13. Bottleneck profiles

Assign profiles **per mode, per item**.

## P1 — Candidate evidence-availability bottleneck

\[
\text{probe not fully accessible}
\]

and native answer is wrong/unresolved.

Interpretation:

> required evidence was not reliably recoverable even under explicit demand.

Do not call this "not encoded."

---

## P2 — Candidate native-access bottleneck

\[
\text{PROBE_ACCESSIBLE}
\]

but native state is:

- `ABSENT`,
- `PARTIAL`,
- `WRONG`, or
- `CONFLICTING`,

and native answer is wrong/unresolved.

Interpretation:

> the required evidence is recoverable under direct demand but was not correctly available in the observable native reasoning trace.

This is the closest multimodal analogue of an **available-but-not-accessed** state.

---

## P3 — Downstream reasoning/utilization bottleneck

\[
\text{NATIVE\_EVIDENCE\_CORRECT\_SUFFICIENT}
\]

but:

\[
\text{FINAL\_WRONG or NO\_VALID\_FINAL}.
\]

Interpretation:

> the trajectory had sufficient correct visual evidence but still failed downstream.

---

## P4 — Successful pipeline

\[
\text{NATIVE\_EVIDENCE\_CORRECT\_SUFFICIENT}
\]

and:

\[
\text{FINAL\_CORRECT}.
\]

---

## P5 — Unresolved / mixed

Anything that cannot be cleanly assigned.

Do not force every item into P1–P4.

---

# 14. Thinking-vs-CoT matched analysis

The central descriptive comparison is item-matched Thinking vs CoT.

For each eligible item ask:

> What changed when CoT failed and Thinking succeeded?

Define the primary discordant subset:

\[
\boxed{
\text{Thinking correct}
\land
\text{CoT wrong/unresolved}
}
\]

Within this subset classify whether Thinking's improvement is associated with:

### A — Availability gain

Thinking probe recovers \(E^*\), CoT probe does not.

### B — Native access gain

Both probes recover \(E^*\), but:

- Thinking native state = `CORRECT_SUFFICIENT`;
- CoT native state is `ABSENT/PARTIAL/WRONG/CONFLICTING`.

### C — Downstream reasoning gain

Both native trajectories contain correct sufficient \(E^*\), but only Thinking reaches the correct answer.

### D — Mixed / unresolved

No clean localization.

This is the key Stage 11A output.

---

# 15. Direct arm

Direct is secondary but valuable.

Use it to ask whether the progression is:

\[
\text{Direct}
\rightarrow
\text{CoT}
\rightarrow
\text{Thinking}
\]

primarily in:

- evidence availability;
- native evidence access;
- downstream reasoning.

Do not require monotonic ordering.

Direct is a comparison arm, not the primary inferential contrast.

---

# 16. Primary endpoints

Freeze the following before probe outcomes are opened.

## E1 — \(E^*\) eligibility yield

\[
P(E^*\text{ identifiable and sufficient})
\]

across the 128 Stage 9A families.

This determines whether the framework is broadly usable.

---

## E2 — Probe-accessible evidence rate by mode

\[
P(\text{PROBE\_ACCESSIBLE}\mid m)
\]

for:

\[
m\in\{\text{Direct, CoT, Thinking}\}.
\]

---

## E3 — Native correct-evidence rate by mode

\[
P(\text{N2 CORRECT\_SUFFICIENT}\mid m)
\]

---

## E4 — Downstream failure despite correct evidence

\[
P(\text{FINAL wrong}\mid \text{N2},m)
\]

---

## E5 — Thinking-over-CoT discordant localization

Among:

\[
\text{Thinking correct, CoT wrong}
\]

report fractions assigned to:

- availability gain;
- native access gain;
- downstream reasoning gain;
- mixed/unresolved.

This is the main paper-facing endpoint.

---

# 17. Secondary decomposition

Also report the reverse discordant subset:

\[
\text{CoT correct, Thinking wrong}
\]

to avoid interpreting all mode differences as unidirectional Thinking improvements.

Report:

- evidence type;
- problem category;
- reasoning length;
- native evidence timing;
- whether \(E^*\) is single-fact or multi-fact.

These are descriptive only unless separately powered.

---

# 18. Annotation blinding

Use a strict order.

## Pass 1 — \(E^*\) construction

Review:

- image;
- question;
- gold answer / source solution where needed.

Do **not** show any model trajectory or mode correctness.

Freeze:

- eligibility;
- \(E^*\);
- accepted paraphrases;
- sufficiency judgment.

## Pass 2 — Native evidence-state annotation

Review one trajectory at a time with mode identity hidden if feasible.

Do not show:

- other modes;
- direct-probe outputs;
- final correctness label.

Annotate N0–N5.

## Pass 3 — Probe scoring

Score direct evidence probes using frozen \(E^*\).

## Pass 4 — Bottleneck assignment

Only after all above artifacts are sealed, join:

- probe state;
- native evidence state;
- final correctness;
- mode.

This reduces outcome-shaped taxonomy.

---

# 19. Agreement

Use two independent annotation passes on at least:

\[
\boxed{
32 \text{ eligible items}
}
\]

for:

- \(E^*\) sufficiency;
- native evidence state;
- discordant localization category.

Report:

- raw agreement;
- Cohen's \(\kappa\) where meaningful;
- disagreement reasons.

If agreement for native evidence state is poor:

\[
\kappa < 0.6
\]

do not promote fine-grained bottleneck proportions.

Collapse to coarser categories and report the limitation.

---

# 20. Feasibility gates

Stage 11A exists partly to decide whether a causal Stage 11B is worth running.

## Strong GO to Equal-Evidence Oracle

Proceed if all are true:

1. at least:
   \[
   \boxed{
   48
   }
   \]
   independent items have clean, sufficient \(E^*\);

2. at least:
   \[
   \boxed{
   16
   }
   \]
   Thinking-correct / CoT-wrong discordant items exist among eligible cases;

3. at least two bottleneck categories contain:
   \[
   \boxed{
   \ge 8
   }
   \]
   independent items;

4. native evidence annotation has acceptable agreement;

5. the bottleneck distribution is not almost entirely `MIXED/UNRESOLVED`.

---

## Limited GO

If:

- 32–47 eligible items, or
- 8–15 Thinking-correct / CoT-wrong discordant items,

run only a small Equal-Evidence Oracle pilot.

Do not make a strong claim about why Thinking is better.

---

## No GO

If:

- fewer than 32 clean \(E^*\) items;
- fewer than 8 informative Thinking-vs-CoT discordant items;
- or evidence-state annotation is too ambiguous,

stop this branch.

Do not force a failure taxonomy onto unsuitable natural tasks.

---

# 21. Optional Equal-Evidence feasibility pilot

Run only after the Stage 11A census is frozen and only if the GO direction is plausible.

Use at most:

\[
\boxed{
12 \text{ eligible items}
}
\]

balanced across candidate bottleneck types.

Remove the image.

Provide:

\[
\text{question} + E^*_{\text{correct}}
\]

to:

- prompted CoT;
- Thinking.

Optional Direct arm if cheap.

Purpose:

> verify that the \(E^*\) representation is operationally sufficient for the model family and that an eventual oracle-gap experiment is interpretable.

This is not the full Stage 11B.

Do not select items based on oracle outcomes.

---

# 22. What Stage 11A can and cannot conclude

## Can conclude

Examples:

> Thinking-correct / CoT-wrong cases are disproportionately associated with correct native evidence access.

or:

> Most mode-discordant errors occur after both modes already possess correct task-critical visual evidence.

## Cannot conclude

Stage 11A alone cannot establish:

> Thinking is better because it retrieves visual evidence more effectively.

Why?

Because native evidence state is observational and explicit probing changes the demand.

The causal localization requires giving modes the **same correct evidence** and asking whether the performance gap collapses.

That is Stage 11B.

---

# 23. Competing mechanisms and predicted signatures

## M1 — Thinking mainly improves visual evidence availability

Prediction:

\[
Probe_T > Probe_{CoT}
\]

and Thinking-correct / CoT-wrong cases frequently show `availability gain`.

Stage 11B prediction:

equalizing \(E^*\) should strongly reduce the gap.

---

## M2 — Thinking mainly improves native evidence access/retrieval

Prediction:

\[
Probe_T \approx Probe_{CoT}
\]

but:

\[
NativeEvidence_T > NativeEvidence_{CoT}.
\]

Thinking-correct / CoT-wrong cases concentrate in `native access gain`.

Stage 11B prediction:

equalizing \(E^*\) should strongly reduce the gap.

---

## M3 — Thinking mainly improves downstream reasoning

Prediction:

\[
Probe_T \approx Probe_{CoT}
\]

and:

\[
NativeEvidence_T \approx NativeEvidence_{CoT}
\]

while Thinking succeeds more often after both already contain correct \(E^*\).

Stage 11B prediction:

Thinking advantage persists under Equal-Evidence Oracle.

---

## M4 — Mixed improvement

Different items fail at different points.

Stage 11B should show partial gap closure.

---

## M5 — No stable bottleneck difference

Mode differences do not localize consistently.

Then do not make Claim 3 a main contribution.

---

# 24. Null discipline

A null mode difference at one layer of the decomposition does not eliminate other mechanisms.

Examples:

- equal probe accuracy does not imply equal native retrieval;
- equal native text evidence does not imply equal hidden-state evidence;
- persistent oracle gap does not prove perception is irrelevant;
- absent text evidence does not prove inaccessible hidden representation;
- a direct probe may overestimate native availability because it explicitly creates demand.

Every conclusion must be phrased at the level actually measured.

---

# 25. Relation to prior results

This stage should be interpreted against two established findings.

## Prior failure studies

Final task correctness is not a reliable proxy for local grounding correctness.

Therefore Stage 11A explicitly separates:

\[
\text{evidence state}
\]

from:

\[
\text{final answer}.
\]

## Stage 9 Thinking vs CoT

Thinking substantially outperformed matched prompted CoT, but coarse finite direct-image-access sufficiency was similar.

Therefore:

\[
\boxed{
\textbf{Thinking is not simply better because it keeps direct vision open longer.}
}
\]

Stage 11A asks what changes instead.

---

# 26. Statistics

Independent unit:

\[
\boxed{
\text{problem/image family}
}
\]

Use:

- paired item-level mode comparisons;
- equal item weighting;
- bootstrap 95% intervals;
- exact/McNemar-style paired summaries where appropriate.

Primary analysis is descriptive/localizational.

Do not run large hypothesis grids.

Report denominators clearly for:

- all 128 families;
- \(E^*\)-eligible items;
- mode-discordant subsets;
- each bottleneck category.

---

# 27. Compute budget

Most work is annotation and reuse of existing trajectories.

## Existing trajectory reuse

\[
0 \text{ GPU-hours}
\]

## New explicit evidence probes

Maximum primary:

\[
64 \text{ eligible items}
\times
3 \text{ modes}
=
192 \text{ short runs}
\]

If more than 64 items are eligible, use a deterministic 64-item probe subset stratified by problem/evidence type.

Target:

\[
\boxed{
<1.5 \text{ GPU-hours}
}
\]

## Optional Equal-Evidence pilot

At most:

\[
12\times 2\text{--}3
\]

short text-only runs.

Target:

\[
\boxed{
<0.5 \text{ GPU-hours}
}
\]

Hard Stage 11A cap:

\[
\boxed{
<2.5 \text{ GPU-hours}
}
\]

No new full benchmark generation.

---

# 28. Required figures

## Figure 1 — Bottleneck model

\[
\text{Image}
\rightarrow
\text{probe-accessible }E^*
\rightarrow
\text{native evidence access}
\rightarrow
\text{downstream reasoning}
\rightarrow
\text{answer}
\]

with B1/B2/B3 failure locations.

---

## Figure 2 — Evidence accessibility and native access by mode

For Direct / CoT / Thinking show:

- probe-accessible rate;
- native correct-sufficient evidence rate;
- final accuracy.

---

## Figure 3 — Failure decomposition by mode

Stacked or alluvial view:

- availability limitation;
- native access limitation;
- downstream reasoning limitation;
- mixed/unresolved;
- success.

---

## Figure 4 — Thinking-correct / CoT-wrong localization

Primary paper-facing figure.

Show how discordant cases distribute among:

- availability gain;
- native access gain;
- downstream reasoning gain;
- mixed/unresolved.

---

## Figure 5 — Optional oracle-feasibility pilot

Only if executed.

Show native gap vs correct-\(E^*\) text-only gap.

Do not treat pilot as final causal estimate.

---

# 29. Required artifacts

Produce:

1. `stage11a_bottleneck_census_spec.md`
2. `stage11a_e_star_eligibility.json`
3. `stage11a_e_star_gold.parquet`
4. `stage11a_e_star_sufficiency_review.json`
5. `stage11a_native_evidence_states.parquet`
6. `stage11a_probe_manifest.json`
7. `stage11a_probe_results.parquet`
8. `stage11a_bottleneck_profiles.parquet`
9. `stage11a_thinking_cot_discordance.json`
10. `stage11a_annotation_agreement.json`
11. `stage11a_primary_inference.json`
12. optional `stage11a_equal_evidence_pilot.json`
13. `stage11a_go_nogo_decision.json`
14. `stage11a_resource_accounting.json`
15. `stage11a_summary.md`

---

# 30. Outcome-dependent paper claims

## Outcome A — Thinking advantage concentrates in native evidence access

Potential paper sentence:

> **Thinking's advantage is concentrated in cases where task-critical visual evidence is recoverable under direct demand but fails to enter the observable reasoning state under prompted CoT.**

Do not use causal language until Stage 11B.

---

## Outcome B — Thinking advantage concentrates downstream

Potential paper sentence:

> **Thinking often succeeds after both modes already possess the same correct task-critical visual evidence, implicating downstream reasoning rather than visual evidence access as the dominant remaining bottleneck.**

Again, Stage 11B is required for causal confirmation.

---

## Outcome C — Availability differs

Potential paper sentence:

> **Thinking more reliably recovers task-critical visual evidence even under explicit evidence probes.**

Interpret as demand-conditioned evidence accessibility, not internal encoding.

---

## Outcome D — Mixed

Potential paper sentence:

> **Multimodal reasoning failures arise from multiple bottlenecks, and Thinking improves more than one stage of the pipeline.**

Use the Equal-Evidence Oracle to quantify how much of the gap remains after evidence equalization.

---

## Outcome E — No stable decomposition

Do not promote Claim 3.

Finalize the paper around Claims 1 and 2.

---

# 31. Next stage if GO — Stage 11B

Stage 11B should be a causal **Equal-Evidence Oracle**.

Core design:

\[
\text{same question}
+
\text{same correct }E^*
\]

with:

- image removed;
- evidence text held identical across CoT and Thinking.

Primary causal quantity:

\[
\boxed{
\text{native Thinking--CoT gap}
-
\text{oracle Thinking--CoT gap}
}
\]

Interpretation:

- gap collapses → upstream evidence acquisition/access explains much of Thinking's advantage;
- gap persists → downstream reasoning advantage remains after evidence equalization;
- partial closure → both contribute.

Do not launch Stage 11B automatically.

---

# 32. Exactly one recommendation at completion

If the Strong GO criteria pass:

> Freeze the \(E^*\)-eligible cohort and run a preregistered Equal-Evidence Oracle to causally localize the Thinking–CoT performance gap.

If Limited GO:

> Run only a small Equal-Evidence Oracle pilot and keep Claim 3 secondary.

If No GO:

> Stop the bottleneck branch and finalize the paper around the already-established causal retrieval and visual-to-text lifecycle claims.

---

# 33. Final decision target

This stage exists to answer:

\[
\boxed{
\textbf{Is the Thinking-vs-CoT performance difference cleanly localizable
to visual-evidence availability, native evidence access, downstream reasoning,
or a mixture of these bottlenecks?}
}
\]

If the decomposition is identifiable and sufficiently populated, test it causally next.

If not, do not force Claim 3.
