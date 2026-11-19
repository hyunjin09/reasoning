# Stage 8B.2 — Block 2: Retrieval-Event / Local-Read Success–Failure Analysis

## 0. Scope

This is the second analysis block for the completed 256-example MathVision bounded census.

Block 1 established:

\[
oxed{
	ext{No robust whole-trajectory retrieval phenotype is established from final correctness alone.}
}
\]

Raw wrong trajectories were longer, had more retrieval episodes, and were more tortuous, but those effects did not survive the full prespecified controls.

Therefore Block 2 changes the primary label from:

\[
	ext{final correct vs final wrong}
\]

to:

\[
oxed{
	ext{local visual read success }(L+)
\quad	ext{vs}\quad
	ext{local visual read failure }(L-)
}
\]

at **active task-required retrieval events**.

The core question is:

\[
oxed{
	extbf{When visual retrieval is active and task-required, where does a correct visual read diverge from an incorrect one?}
}
\]

This block is still primarily **diagnostic**.

No reinjection, rollback, routing intervention, or paired-rollout confirmation is launched in this block.

## 1. Why this block is necessary for the paper

Block 1 showed that final-answer correctness is too coarse to serve as a direct proxy for visual-retrieval quality.

A wrong final answer may contain:
- an incorrect local visual read,
- a correct local visual read followed by arithmetic failure,
- a correct read followed by binding/integration failure,
- or another downstream reasoning error.

Therefore the next paper-relevant question is not:

> How do correct and wrong final trajectories differ?

but:

> **At moments when the model is actively retrieving task-required visual evidence, what distinguishes a successful read from a failed read?**

This directly tests the retrieval lifecycle discovered in earlier stages:

\[
	ext{retrieval activation}
ightarrow
	ext{source routing}
ightarrow
	ext{Value-rich transport}
ightarrow
	ext{local evidence emission}
ightarrow
	ext{downstream use}
\]

The goal is to identify the **first reproducible divergence** between L+ and L−.

## 2. Paper claims this block may support

The block should not assume the failure stage in advance.

Possible positive claims include:

### Claim A — Retrieval activation deficit

> Incorrect visual reads are preceded by weaker or delayed active retrieval.

### Claim B — Routing-quality deficit

> Successful and failed reads activate retrieval similarly, but failed reads show weaker target-specific visual routing.

### Claim C — Source competition / ambiguity

> Failed reads exhibit lower target-vs-confuser separation or greater cross-head/source disagreement.

### Claim D — Transport-side difference

> Routing is similar, but Value/post-W_O visual transport differs between successful and failed local reads.

### Claim E — No pre-read passive divergence

> Correct and incorrect local reads are not separable in passive retrieval-state features before evidence emission, implying that failure may arise in extraction/content representation or later use.

Any of these outcomes is informative.

## 3. What a null does NOT rule out

A null L+ vs L− difference in passive features does **not** imply that retrieval failures do not exist.

Possible explanations:
- the divergence is causal but not passively decodable;
- the demanded source is correctly routed but visual content is mis-extracted;
- the relevant representation lives in a feature not measured here;
- multiple failure mechanisms are mixed within L−;
- divergence occurs after the local read rather than before it.

A passive null should therefore motivate a small later causal subset, not immediate abandonment.

## 4. Frozen inputs from Block 0

Use the frozen Block 0 artifacts unchanged:

- 256-example cohort
- benchmark outcome labels
- completion labels
- frozen Stage 8A detector
- frozen threshold:
  \[
  	au_R = 0.5478025980771918
  \]
- retrieval episodes
- normalized reasoning phases
- passive QK/attention features
- outcome-independent semantic-review membership

No event may be added or removed based on correctness or observed effect.

## 5. Frozen semantic review membership

Use exactly the Block 0 outcome-independent review membership.

If membership was defined as up to three retrieval episodes per trajectory:

1. earliest eligible episode,
2. one middle episode nearest normalized position 0.5,
3. latest eligible episode,

retain that rule exactly.

Do not select extra events merely because they contain visually interesting mistakes.

## 6. Event semantic annotation

For every frozen reviewed retrieval episode assign:

### T — task-required visual retrieval

The reasoning step genuinely requires visual evidence that is not already sufficiently available from textual/reasoning context.

### M — mention-only / alignment event

Visual content or entity is mentioned, but reacquisition is not required for the current inference.

### U — unresolved semantic status

Cannot certify whether the episode is task-required retrieval.

Primary Block 2 analysis uses only **T events**.

M events remain an important negative/reference group.

## 7. Local-read outcome annotation

For every T event, annotate the immediate visual claim or visual evidence use following retrieval.

### L+ — locally correct visual read

The model’s local claim matches the relevant image evidence.

Examples:
- correct number,
- correct geometric relation,
- correct object/label binding,
- correct local visual comparison.

### L− — locally incorrect visual read

The model emits a wrong visual quantity, relation, binding, or source-conditioned statement.

### L? — unresolved

Local correctness cannot be confidently certified.

Important:

\[
oxed{
	ext{final wrong} 
ot\Rightarrow L-
}
\]

and:

\[
oxed{
	ext{final correct} 
ot\Rightarrow L+
}
\]

Local and final outcome are separate axes.

## 8. Primary 2 × 2 structure

Preserve:

| Local visual read | Final benchmark outcome | Interpretation |
|---|---|---|
| L+ | correct | successful visual read + successful downstream reasoning |
| L− | wrong | visual-stage failure candidate |
| L+ | wrong | downstream reasoning/integration failure candidate |
| L− | correct | compensation / recovery candidate |

The **primary Block 2 contrast** is:

\[
oxed{
L+ 	ext{ vs } L-
}
\]

Final correctness is secondary.

## 9. Block 2 analysis order

The analysis must proceed in the following order:

\[
oxed{
	ext{Activation}
ightarrow
	ext{Routing}
ightarrow
	ext{Source competition}
ightarrow
	ext{Transport phenotype}
}
\]

Do not skip directly to Value features.

The purpose is to identify the earliest stage at which L+ and L− differ.

## 10. Level 1 — Retrieval activation

At each T event compare L+ vs L− on frozen active-retrieval features.

Primary activation variables:

- frozen retrieval score R_t
- peak retrieval score within episode
- episode mean retrieval score
- episode AUC above threshold
- visual attention mass
- visual QK competitiveness
- attention concentration
- episode duration

Also compare the local pre-retrieval rise:

\[
\Delta R_t
=
R_t - \operatorname{median}(R_{t-w:t-1})
\]

using a frozen local window.

Question:

\[
oxed{
	ext{Does failed visual reading begin with weaker active retrieval?}
}
\]

## 11. Activation interpretation

If:

\[
R_{L-} < R_{L+}
\]

robustly, candidate interpretation:

> local read failure may begin at insufficient visual retrieval engagement.

If:

\[
R_{L-} pprox R_{L+}
\]

then retrieval activation itself is not the main differentiator, and analysis proceeds to source routing.

This second outcome is especially important because it would imply:

> **the model is looking, but may be looking/selecting incorrectly.**

## 12. Level 2 — Source / ROI routing

For T events where the demanded visual source can be localized, define:

- T: demanded target source / ROI
- X: strongest plausible alternative/confuser
- I: matched irrelevant source where available

Compute:

\[
\Delta QK_{T-X}
=
QK_T-QK_X
\]

\[
\Delta A_{T-X}
=
A_T-A_X
\]

and where possible:

\[
\Delta QK_{T-I}
\]

\[
\Delta A_{T-I}
\]

Additional routing metrics:

- target rank among visual regions
- target attention share
- target-vs-rest margin
- target-vs-nearest-confuser margin
- top-1 source identity
- entropy over candidate visual sources

Question:

\[
oxed{
	ext{Does retrieval activate normally but route less selectively in }L-?
}
\]

## 13. Source-specific replay

Native files do not contain all source-specific QK/Value measurements.

After T/L annotation is sealed, perform bounded **observational replay** only for source-localizable T events.

This replay may recover:

- source-specific QK
- source-specific attention
- target-vs-confuser routing margins
- target/source alphaV
- post-W_O source contribution

This is **not a causal intervention**.

No source suppression, switching, or patching occurs in Block 2.

## 14. Replay subset policy

Prefer replay on all source-localizable L− T events and a matched L+ control set.

Match L+ controls by:

- MathVision subtype
- reasoning position
- retrieval score
- source/ROI type
- completion status where feasible
- question / trajectory length where feasible

If L− is sufficiently numerous, use 1:1 or 1:2 matching.

Do not choose L+ controls based on favorable routing values.

## 15. Level 3 — Source competition / ambiguity

Measure whether failed reads are characterized by less decisive source selection.

Candidate metrics:

- target-vs-confuser QK margin
- target-vs-confuser attention margin
- target source rank
- source entropy
- top-2 margin
- number of candidate visual sources receiving substantial mass

Question:

\[
oxed{
	ext{Is }L-	ext{ associated with ambiguous competition rather than absent retrieval?}
}
\]

This is particularly important for a mechanistic extension beyond vSTREAM.

## 16. Cross-head / cross-layer agreement

For source-localizable events compute:

- fraction of causal late heads favoring target over confuser
- variance of target-vs-confuser QK margin across heads
- variance of target-vs-confuser attention margin
- layer-to-layer agreement on top source
- cross-head source entropy
- target consensus score

These are secondary but potentially informative.

Stage 8A showed that simple head disagreement is not a useful cheap transport gate.

That does **not** rule out disagreement as a phenotype of local read failure.

## 17. Level 4 — Value / transport phenotype

Only after activation and routing analyses are complete, compare descriptive transport-side features.

Candidate quantities:

- target alphaV
- target-vs-confuser alphaV margin
- total visual alphaV norm
- post-W_O target contribution
- visual contribution / residual ratio
- cross-head cancellation
- source-conditioned Value direction similarity

Important:

\[
oxed{
	ext{Do not interpret raw magnitude as causal grounding.}
}
\]

Stage 8A already showed that cheap transport magnitude does not reliably identify causal weakness.

This level asks only whether L+ and L− have different transport phenotypes.

## 18. Demand coverage analysis

Use semantic T annotations to test whether correct and failed reasoning differ in whether task-required visual moments are covered by retrieval.

Define:

\[
Coverage
=
P(
	ext{active retrieval within local window}
\mid
T
)
\]

Compare coverage by final outcome as a secondary analysis.

Also measure:

\[
UnnecessaryRetrieval
=
P(
	ext{retrieval episode at M/nonvisual state}
)
\]

The main purpose is to distinguish:

- failure to retrieve when needed,
- excessive retrieval without demand,
- normal retrieval activation with poor local reading.

## 19. Source-sequence alignment

Where multiple semantic T events in a trajectory can be source-labeled, construct:

- demanded-source sequence
- retrieved top-source sequence

Example:

\[
Aightarrow Bightarrow A
\]

versus:

\[
Aightarrow Xightarrow B
\]

Measure:

- source-transition accuracy
- normalized edit distance
- lag between demand change and source change
- oscillation count
- stale-source persistence

This is secondary/exploratory in Block 2 but directly connects to the Stage 4A dynamic-retrieval discovery.

## 20. Primary statistical comparisons

Primary tests:

### P1 — Retrieval activation

L+ vs L− on:

- frozen retrieval score
- episode AUC
- visual QK competitiveness
- visual attention mass

### P2 — Source routing

Among source-localizable replay events:

L+ vs L− on:

- Delta QK_T-X
- Delta A_T-X
- target rank / target share

### P3 — Source ambiguity

Compare:

- source entropy
- top-2 margin
- cross-head target consensus

Transport-side quantities are secondary unless routing is similar and transport shows a coherent difference.

## 21. Final-outcome secondary analyses

After the primary L+ vs L− analysis, stratify by final outcome.

Important subgroups:

### S1 — L+ / final correct

Successful local read and successful final reasoning.

### S2 — L+ / final wrong

Correct local visual read followed by downstream failure.

### S3 — L− / final wrong

Local visual failure followed by final failure.

### S4 — L− / final correct

Local visual failure followed by recovery/compensation.

Do not let subgroup sample size drive overinterpretation.

Block 3 will focus on what happens after these local outcomes.

## 22. Matching / confound controls

For L+ vs L−, control or match by:

- reasoning position
- frozen retrieval score
- MathVision subtype
- source/ROI type
- question length
- trajectory length
- completion status
- episode duration where appropriate

Do not over-control for variables that may themselves be downstream consequences of local read failure.

Source-routing measures should preferably be analyzed in matched source-localizable subsets.

## 23. Statistical unit

Primary independent unit:

- MathVision item / image family

Multiple reviewed events within one trajectory are clustered.

Do not treat all retrieval episodes as independent samples.

Use:

- clustered bootstrap by item/family
- mixed-effects model where useful
- paired/matched statistics in replay subsets

## 24. Multiplicity discipline

Freeze three primary families before opening results:

1. retrieval activation
2. target/source routing
3. source ambiguity

Value/transport features, head/layer agreement, demand coverage, and source-sequence alignment are secondary/exploratory unless a later confirmation stage validates them.

Do not promote a single isolated significant feature if neighboring features disagree.

## 25. Sample-size / yield gate

Before main inference, report:

- number of T events
- number of M events
- number of U events
- number of L+
- number of L−
- number of L?
- unique families for L+
- unique families for L−
- source-localizable L+
- source-localizable L−

Preferred minimum:

\[
oxed{
L+ \ge 64
}
\]

and:

\[
oxed{
L- \ge 24
}
\]

from independent families/events where possible.

Stretch target:

\[
L- \ge 32
\]

If L− is below 24, do not loosen annotation rules.

Run descriptive analysis, but limit inferential claims.

## 26. Decision tree

### Outcome A — Activation differs

If L− has robustly weaker retrieval activation:

\[
oxed{
	ext{failure may begin before/at retrieval engagement}
}
\]

Block 3 should examine whether missed/weak retrieval predicts later re-query.

### Outcome B — Activation similar, routing differs

If:

\[
R_{L+}pprox R_{L-}
\]

but:

\[
\Delta QK_{T-X}^{L+}
>
\Delta QK_{T-X}^{L-}
\]

then:

\[
oxed{
	ext{the model looks in both cases, but failed reads route less selectively}
}
\]

This is a high-value mechanistic result.

### Outcome C — Activation/routing similar, ambiguity higher

Interpretation:

> failure may arise from unresolved competition across plausible visual sources.

### Outcome D — Activation/routing similar, transport differs

Interpretation:

> investigate transport causally in a later matched subset.

Do not jump directly to Value reinjection.

### Outcome E — No passive difference

Interpretation:

> local read failures may arise in extraction/content representation or another unmeasured stage.

A small causal subset remains warranted.

## 27. Connection to Block 1

Block 1 found no robust fully controlled final-correct vs final-wrong global retrieval phenotype.

Therefore Block 2 should explicitly test whether local labels reveal a sharper effect:

\[
oxed{
	ext{final outcome coarse}
\quadightarrow\quad
	ext{local visual-read outcome mechanistically informative}
}
\]

A positive L+ vs L− effect would explain why broad final-outcome grouping was diluted.

A null would shift attention toward extraction or downstream reasoning.

## 28. What Block 2 must NOT claim

Block 2 alone does not establish:

- causal source misrouting,
- that routing differences cause wrong final answers,
- that visual attention magnitude equals causal grounding,
- that Value magnitude is a grounding score,
- that all wrong answers are visual failures,
- that repeated retrieval is harmful.

Causal validation and post-read dynamics come later.

## 29. Required outputs

Produce:

1. `stage8b_block2_event_annotation_summary.json`
2. `stage8b_block2_TMU_table.parquet`
3. `stage8b_block2_local_read_table.parquet`
4. `stage8b_block2_activation_comparison.json`
5. `stage8b_block2_source_routing_comparison.json`
6. `stage8b_block2_source_ambiguity_comparison.json`
7. `stage8b_block2_transport_descriptive.json`
8. `stage8b_block2_head_layer_agreement.json`
9. `stage8b_block2_demand_coverage.json`
10. `stage8b_block2_source_sequence_alignment.json`
11. `stage8b_block2_replay_manifest.json`
12. `stage8b_block2_summary.md`

## 30. Key figures

### Figure 1 — L+ vs L− retrieval activation

Event-aligned retrieval score / QK / attention.

### Figure 2 — Target-vs-confuser routing

Delta QK_T-X and Delta A_T-X for L+ vs L−.

### Figure 3 — Source rank / ambiguity

Target rank, top-2 margin, source entropy.

### Figure 4 — Head/layer source consensus

Successful vs failed local reads.

### Figure 5 — Local-read outcome × final outcome

2 × 2 matrix:

- L+ correct
- L+ wrong
- L− correct
- L− wrong

## 31. Block 2 completion criterion

Block 2 is complete when we can answer:

\[
oxed{
	extbf{At active task-required visual retrieval events, what is the earliest
reproducible computational difference between a correct and incorrect local visual read?}
}
\]

Possible answers include:

- activation,
- routing,
- source ambiguity,
- transport phenotype,
- or no passive difference.

## 32. Handoff to Block 3

Regardless of Block 2 outcome, Block 3 should then ask:

\[
oxed{
	extbf{What happens after a local visual read succeeds or fails?}
}
\]

Block 3 will focus on:

- retrieval-to-use latency
- re-retrieval
- recovery
- repeated failed retrieval
- evidence mutation
- refresh compliance
- pre-error vs post-error wandering
- L− final-correct recovery
- L+ final-wrong downstream failure

Block 2 identifies **where the local read diverges**.

Block 3 explains **how that local outcome shapes the rest of the reasoning trajectory**.
