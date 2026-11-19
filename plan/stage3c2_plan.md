# Stage 3C.2 Plan — Semantic Alignment vs Task-Conditioned Retrieval and Attention-Sink Dynamics

## 0. Purpose

Stage 3C.2 follows the Stage 3C.1 result:

> **At independently causal-localized late-W4 retrieval coordinates, target-ROI attention is naturally high and strongly selective, with pronounced temporal QK-cosine sharpening, substantial target αV influx, and large post-`W_O` contribution.**

Stage 3C.1 also showed:

- target attention rises sharply near the causal retrieval coordinate;
- Q norm does not consistently surge;
- visual K norm is stable across query time;
- QK directional compatibility sharply increases;
- natural attention magnitude is not a universal per-head causal score;
- a strong candidate sink exists at the first prompt token `<|im_start|>`;
- candidate-sink mass is large, but its causal role is unknown.

The central ambiguity is now:

\[
\boxed{
\text{Does high target-ROI attention reflect semantic/text-image alignment,
task-conditioned retrieval demand,
or both?}
}
\]

A second question is:

\[
\boxed{
\text{When retrieval sharpens, where does the extra attention probability come from?}
}
\]

In particular:

- does candidate-sink mass fall as relevant visual attention rises?
- does mass instead move away from previous reasoning or other visual tokens?
- does sink behavior vary systematically across reasoning phases?

Stage 3C.2 is primarily a **causally anchored descriptive dissociation stage**.

It does **not** manipulate Q, K, attention probabilities, sink states, `h_pre`, or source paths.

The goal is to separate:

1. **semantic alignment**
2. **retrieval demand**
3. **attention-budget reallocation / sink dynamics**

before a later causal routing intervention.

---

# 1. Scientific Handoff

## Stage 2C

Most evidence-associated ROI attention was mention-centered.

This established:

> matching visual attention can coincide with textual semantic reference.

But attention alone could not distinguish:

- semantic alignment;
- genuine visual retrieval.

## Stage 3B.2

Future visual-source identity causally controlled the upcoming evidence at `E_d-1` and `E_d` while prior reasoning history was fixed.

Therefore:

> evidence-specific late visual retrieval is real.

## Stage 3B.5–3B.7-R

The causal pathway was localized to:

```text
target evidence ROI
→ late W4 causal query-head sets
→ Value-dominant transport
→ current reasoning state
→ evidence decision
```

## Stage 3C.1

At these independently causal-localized cells:

- target ROI attention was high;
- target ROI density exceeded irrelevant ROI by ~69× and ~135× for the two targets;
- QK cosine and scaled logits sharpened near retrieval;
- target αV and post-`W_O` contributions were large;
- natural attention-causal correlations were target-dependent;
- one causal ensemble member had near-zero natural target attention;
- `<|im_start|>` carried large candidate-sink mass.

Therefore the next descriptive question is:

> **What distinguishes a genuine retrieval-attention event from mere semantic alignment, and how is attention probability reallocated during retrieval?**

---

# 2. Frozen Causal Targets

Reuse the exact Stage 3C.1 targets.

## Target A

```text
E_d
W4
layer 29
heads [11, 6, 15, 12]
```

## Target B

```text
E_d - 1
W4
layer 28
heads [16, 0, 3, 6]
```

No new heads or layers may be selected using attention.

The Stage 3C.1 noncausal-head controls remain frozen.

---

# 3. Core Experimental Strategy

Stage 3C.2 must deliberately separate:

```text
M = mention-matched visual ROI
T = task-required causal visual ROI
I = matched irrelevant ROI
S = candidate sink positions
```

The key design requirement is:

\[
M \neq T
\]

for the primary dissociation examples.

If current text mentions the same object whose value must be retrieved, semantic alignment and retrieval demand are confounded.

Therefore the primary cohort must contain reasoning states where:

> **the visually/textually aligned entity and the causally required evidence region are distinct.**

---

# 4. Primary Scientific Questions

Stage 3C.2 asks four questions.

## Q1 — Mention vs required evidence

When text refers to one visual entity but reasoning requires information from another ROI, does attention follow:

- the mentioned entity?
- the causally required evidence?
- both at different times?

## Q2 — Retrieval sharpening

Does task-required ROI routing sharpen specifically near the causal retrieval coordinate through:

- QK cosine increase;
- scaled attention-logit increase;
- target attention increase;
- αV increase;
- post-`W_O` contribution increase?

## Q3 — Attention-budget source

When target ROI attention increases, which source class loses probability mass?

Candidate sources:

```text
candidate sink
other visual
question/prompt
previous reasoning
special/other
mention-matched ROI
```

## Q4 — Retrieval vs alignment phenotype

Can Stage 3C.2 identify natural phenotypes such as:

```text
Alignment-only
Retrieval-only
Alignment-then-retrieval
Alignment+retrieval overlap
Low-attention causal retrieval
Sink-reallocation retrieval
Non-sink reallocation retrieval
```

These remain descriptive labels.

---

# 5. Cohort Construction

## 5.1 Primary dissociation cohort

Construct a prospective cohort of examples with:

```text
M != T
```

Target:

```text
24–36 unique base problems
```

Minimum:

```text
24 valid bases
```

Primary statistical unit:

```text
base_problem_id
```

The cohort should be disjoint from any dataset used to define the mention-vs-required annotation rules.

Use existing Stage 3 causal-valid examples where possible.

If insufficient, prospectively collect additional MathVerse examples under the locked generation/edit protocol.

## 5.2 Inclusion requirements

Each primary base must have:

1. a valid causal target ROI defined independently by counterfactual edit;
2. a frozen causal retrieval coordinate or a valid application of the same coordinate rule;
3. a distinct mention-matched visual entity/ROI;
4. `M != T`;
5. exact token/ROI mapping;
6. manually validated semantic relation;
7. no attention used for inclusion;
8. no attention used to define `M` or `T`;
9. enough history for at least three temporal checkpoints before retrieval;
10. no ambiguous overlap between mention and target ROI.

---

# 6. Mention-Matched ROI Definition

The mention-matched ROI `M` is defined from:

- explicit lexical/semantic entity reference in current reasoning;
- manually linked image entity;
- pre-attention annotation.

Examples:

```text
text says "BC"
→ M = visual BC entity/segment region
```

or:

```text
text says "the left segment"
→ M = manually corresponding visual entity
```

Do not define `M` from attention peaks.

If no unambiguous visual entity corresponds to the current mention, reject the event from the primary dissociation cohort.

---

# 7. Task-Required ROI Definition

The task-required ROI `T` must be the independently causal visual evidence region.

Primary definition:

```text
Stage 3A / Stage 3B.7-R counterfactual edit ROI
```

or an exactly analogous counterfactual-edited ROI in newly collected examples.

The key property is:

> changing `T` changes the evidence identity / decision under validated causal conditions.

Thus:

```text
T = causally required visual evidence
```

not merely a visually salient or semantically aligned region.

---

# 8. Matched Irrelevant ROI

Reuse or prospectively create `I`:

- disjoint from `M` and `T`;
- matched in token count when feasible;
- task-irrelevant;
- manually audited;
- frozen before attention extraction.

---

# 9. Candidate Sink Definition

Primary candidate sink:

```text
first prompt token <|im_start|>
```

as identified in Stage 3C.1.

Also record secondary candidate sink classes prospectively:

```text
assistant/control markers
BOS-like special tokens
newline/control positions
image-placeholder/special positions
```

Important:

> A high-attention special token is only a **candidate sink**.

Stage 3C.2 does not claim causal uselessness.

---

# 10. Temporal Grid

Use a frozen temporal grid relative to the causal retrieval coordinate.

For Target A:

```text
E_d - 16
E_d - 8
E_d - 4
E_d - 2
E_d - 1
E_d
```

For Target B, align relative to its own retrieval coordinate:

```text
T_B - 16
T_B - 8
T_B - 4
T_B - 2
T_B - 1
T_B
```

where:

```text
T_B = E_d - 1
```

For each event, record:

- whether the same entity mention is already active;
- whether retrieval demand is present;
- whether exact natural history exists;
- teacher-forced provenance if applicable.

---

# 11. Alignment-vs-Retrieval Event Labels

Each temporal checkpoint receives a blinded semantic label before attention analysis.

Primary categories:

## A0 — Neither

Current reasoning does not mention `M` strongly and does not yet require `T`.

## A1 — Mention-only

Current reasoning explicitly refers to `M`, but `T` is not yet needed for the immediate subgoal.

## A2 — Retrieval-needed

The immediate reasoning subgoal requires `T`, while current lexical mention is not `T`.

## A3 — Mention + retrieval

Current text explicitly references the target entity and the target evidence is also required.

These labels must be created from text/problem semantics without attention.

---

# 12. Strongest Within-Problem Contrast

Where possible, identify two states within the same problem with similar lexical mention but different retrieval need.

Example:

```text
State M:
"We already know AB; now compute CD."

State R:
"We now need to determine AB."
```

Both contain `AB`, but only State R requires direct AB visual evidence.

This is a strong secondary contrast because lexical alignment is partially controlled while retrieval demand differs.

Do not force this annotation where semantics are ambiguous.

---

# 13. Measurement Set

At every target/head/time/condition extract:

## 13.1 Attention quantities

```text
target ROI mass
target ROI density
mention ROI mass/density
irrelevant ROI mass/density
candidate sink mass
other visual mass
question mass
previous reasoning mass
special/other mass
attention entropy
```

## 13.2 QK quantities

For `T`, `M`, `I`, and sink positions:

```text
Q norm
K norm
QK cosine
raw dot product
scaled pre-softmax logit
```

Use the exact full-shape eager reconstruction protocol validated in Stage 3C.1.

## 13.3 Value / contribution quantities

For `T`, `M`, `I`, and sink:

```text
αV vector
αV norm
per-head post-W_O contribution
frozen-head-set post-W_O sum contribution
```

Do not interpret vector norm alone as causal importance.

---

# 14. Primary Alignment-vs-Retrieval Contrasts

## C1 — Mention vs target at retrieval

At retrieval-needed coordinates compare:

```text
T vs M
```

Questions:

- is QK cosine larger for T?
- is attention larger for T?
- is αV larger for T?

## C2 — Mention-only vs retrieval-needed

For the same or semantically matched entity context compare:

```text
mention-only state
vs
retrieval-needed state
```

Questions:

- does target QK sharpen only when evidence is needed?
- does target attention rise only when evidence is needed?
- does target αV rise even if lexical mention is stable?

## C3 — Temporal crossing

Measure whether:

```text
M dominance earlier
→ T dominance near retrieval
```

occurs within base.

This is the strongest descriptive signature of:

```text
semantic alignment → task-conditioned retrieval
```

---

# 15. Primary Phenotype Definitions

## P1 — Alignment-only

Mention ROI remains dominant even when a distinct target ROI is required.

Operationally:

- `M > T` in QK/attention at retrieval;
- target αV does not show a clear retrieval-specific rise.

## P2 — Retrieval-only

Target ROI dominates near retrieval despite distinct mention ROI.

Operationally:

- `T > M` in target QK/attention/αV near retrieval;
- no earlier mention-driven dominance is required.

## P3 — Alignment-then-retrieval

Earlier state:

```text
M > T
```

Near retrieval:

```text
T > M
```

with temporal QK/attention/αV crossover.

This is a key anticipated phenotype.

## P4 — Alignment+retrieval overlap

Both M and T remain elevated.

Interpretation:

- semantic grounding and task retrieval may coexist.

## P5 — Low-attention causal retrieval

Target αV/post-W_O contribution rises or the head is independently causal despite low target α.

This preserves Stage 3C.1 head-level heterogeneity.

---

# 16. Attention-Budget Accounting

For every head/time:

```text
A_T
+ A_M_nonoverlap
+ A_I
+ A_other_visual
+ A_Q
+ A_R
+ A_sink
+ A_other
= 1
```

Use mutually exclusive token sets.

Verify closure within BF16 tolerance.

---

# 17. Sink Reallocation Analysis

For each retrieval event define changes from an earlier matched checkpoint:

```text
ΔA_T
ΔA_sink
ΔA_M
ΔA_other_visual
ΔA_Q
ΔA_R
ΔA_other
```

Primary question:

> When `A_T` rises, which mass decreases?

Descriptive sink reallocation ratio:

```text
SRR = (-ΔA_sink) / ΔA_T
```

only when:

```text
ΔA_T > 0
```

Do not clip.

Do not interpret as a causal fraction.

---

# 18. Sink Phenotype Categories

## S1 — Sink-release retrieval

Target attention rises while candidate-sink mass decreases substantially.

Possible interpretation:

> sink acts as a probability reservoir during natural retrieval.

Still descriptive.

## S2 — Non-sink reallocation

Target attention rises while sink remains stable; mass comes from:

- previous reasoning;
- other visual;
- prompt;
- other positions.

## S3 — Persistent sink

Sink remains high throughout retrieval.

Interpretation:

> sink-like attention may coexist with strong relevant retrieval.

## S4 — Phase-modulated sink

Sink changes systematically across:

```text
ordinary reasoning
mention alignment
retrieval-needed state
evidence expression
```

This would motivate later causal sink analysis.

---

# 19. Sink Semantic Sensitivity

For O/O_sham/C/C_sham compare candidate-sink:

```text
attention mass
QK cosine
αV norm
post-W_O contribution
```

Questions:

- does sink mass remain largely semantic-invariant?
- does sink Value contribution change despite stable mass?
- is sink behavior tied to reasoning phase rather than evidence identity?

This is descriptive only.

---

# 20. Attention Entropy and Competition

Measure:

```text
full attention entropy
visual-only entropy
non-sink entropy
```

Primary questions:

1. does retrieval correspond to global sharpening?
2. or only relevant-vs-distractor redistribution?
3. does removing sink mass descriptively reveal stronger visual competition?

Do not renormalize and reinterpret as causal unless explicitly labeled as descriptive re-expression.

---

# 21. QK Sharpening Decomposition

Stage 3C.1 suggested QK cosine is the dominant natural routing signature.

Stage 3C.2 should separate:

```text
QK_T
QK_M
QK_I
QK_sink
```

over time.

Test:

```text
Δcos(Q,K_T)
vs
Δcos(Q,K_M)
```

from early/mention-only to retrieval-needed states.

Important expected discriminator:

> if textual mention stays similar while `QK_T` selectively sharpens with retrieval demand, simple lexical alignment becomes insufficient as an explanation.

---

# 22. Noncausal-Head Controls

Use the frozen Stage 3C.1 noncausal head sets.

Repeat the same descriptive measurements.

Questions:

- do noncausal heads show mention alignment without retrieval-specific target sharpening?
- is sink behavior generic across heads?
- is T-vs-M crossover enriched in the independently causal heads?

This remains descriptive because the causal/noncausal designation comes from prior intervention results.

---

# 23. Head-Level Heterogeneity

Do not average away head differences.

For every frozen causal head report:

```text
target attention
mention attention
QK_T
QK_M
sink mass
target αV
sink αV
```

over time.

Special attention to:

```text
Target B head 6
```

because Stage 3C.1 showed very low natural target attention despite causal ensemble membership.

Question:

> Does head 6 express a different phenotype, such as low-α/high-value or ensemble interaction?

No causal claim from this descriptive stage.

---

# 24. Statistical Analysis

Primary unit:

```text
base_problem_id
```

Use within-base aggregation before cohort inference.

Report:

- medians;
- bootstrap 95% CIs;
- paired sign fractions;
- Spearman correlations as secondary;
- Holm correction across the frozen primary contrast family.

Primary contrast family:

```text
T vs M at retrieval
retrieval-needed vs mention-only for QK_T
retrieval-needed vs mention-only for A_T
retrieval-needed vs mention-only for αV_T
sink change during retrieval
T-vs-M temporal crossover
causal-vs-noncausal head enrichment
```

---

# 25. Primary Scientific Outcomes

## O1 — Task-conditioned retrieval phenotype

Support if:

- T becomes dominant over M near retrieval;
- QK_T sharpens selectively;
- target αV rises;
- effect is enriched in prior causal heads.

Conclusion:

> **Natural high visual attention near causal retrieval is not explained by semantic mention alignment alone.**

## O2 — Alignment-dominant phenotype

Support if:

- M remains dominant;
- T does not selectively sharpen when retrieval becomes necessary.

Conclusion:

> **High visual attention primarily reflects semantic/text-image alignment in these states.**

This would not invalidate the causal Value pathway.

## O3 — Alignment-then-retrieval

Support if:

```text
early / mention phase:
M dominates

retrieval phase:
T overtakes M
```

Conclusion:

> **Semantic grounding and task-conditioned retrieval are temporally distinct natural attention phenomena.**

This would strongly reconcile Stage 2 and Stage 3.

## O4 — Mixed / heterogeneous

Different problems or heads express different phenotypes.

Do not force one universal mechanism.

---

# 26. Sink Scientific Outcomes

## Sink-release phenotype

If target gain is strongly paired with sink loss:

> **Candidate-sink attention behaves as a natural probability reservoir during retrieval.**

Still descriptive until causal intervention.

## Persistent-sink phenotype

If sink remains high while target rises:

> **Relevant retrieval coexists with persistent sink allocation; attention mass is not a simple finite semantic-information budget.**

## Source-specific reallocation

If target gain comes mainly from R, Q, or other visual positions:

> retrieval reallocates attention from specific competing source classes rather than from the sink.

---

# 27. What Stage 3C.2 Does NOT Establish

Do not claim:

- QK sharpening causes retrieval;
- reasoning state causally triggers retrieval;
- sink is causally useless;
- sink can safely be removed;
- increasing target attention improves evidence use;
- attention mass is an information fraction;
- causal routing competition;
- LOOK/THINK states.

No attention/routing/sink intervention is allowed in this stage.

---

# 28. Decision After Stage 3C.2

Recommend exactly one next causal direction.

## GO — Relevant-vs-Distractor Routing Causality

Use if task-conditioned target sharpening is observed.

Next question:

> **Does causally changing retrieval routing between required and mention/distractor ROIs change Value influx and evidence preference?**

Potential interventions for the next stage:

- query patching;
- QK compatibility manipulation;
- target-vs-distractor routing intervention;
- recipient-state-controlled query swap.

Do not execute here.

## GO — Sink Causality

Use if sink-release dynamics are strong and systematic.

Next question:

> **Is candidate-sink mass dispensable, and does redistributing sink probability alter relevant visual retrieval?**

Do not execute here.

## GO — Alignment Causality

Use if mention alignment dominates over task-required routing.

Next:

> manipulate mention/referential state while keeping visual task demand fixed.

## REDIRECT — Phenotype heterogeneous / weak

If no clear dissociation appears, retain Stage 3C.1 and move to multi-evidence causal refresh without forcing an attention mechanism.

---

# 29. Output Structure

Create:

```text
outputs/stage3c2/
  config/
    stage3c2_config.json
    frozen_targets.json
    primary_contrasts.json
    temporal_grid.json
    sink_definitions.json

  cohort/
    candidate_manifest.jsonl
    primary_dissociation_manifest.jsonl
    exclusions.jsonl

  annotations/
    mention_roi_annotations.jsonl
    required_roi_annotations.jsonl
    irrelevant_roi_annotations.jsonl
    semantic_state_labels.jsonl
    state_pair_annotations.jsonl

  audit/
    token_roi_layout_audit.json
    source_partition_audit.json
    attention_reconstruction_audit.json
    sink_definition_audit.json
    measurement_reproducibility.json

  measurements/
    per_head_time_condition.jsonl
    source_mass_results.jsonl
    qk_results.jsonl
    value_contribution_results.jsonl
    sink_results.jsonl

  analysis/
    mention_vs_required_statistics.json
    temporal_crossover_statistics.json
    qk_sharpening_statistics.json
    attention_budget_statistics.json
    sink_dynamics_statistics.json
    entropy_statistics.json
    causal_vs_noncausal_head_comparison.json
    head_heterogeneity.json
    condition_controls.json
    figures/

  summaries/
    stage3c2_summary.md
    stage3c2_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3C.1 or earlier artifacts.

---

# 30. Required Figures

At minimum:

1. temporal `QK_T` vs `QK_M`;
2. temporal target vs mention ROI attention;
3. temporal target vs mention αV;
4. target/mention crossover examples;
5. retrieval-needed vs mention-only paired target attention;
6. retrieval-needed vs mention-only paired QK cosine;
7. attention-budget stacked profile over time;
8. candidate-sink mass over time;
9. `Δtarget attention` vs `-Δsink attention`;
10. target vs sink αV/post-`W_O` dynamics;
11. causal-head vs frozen noncausal-head phenotype comparison;
12. per-head heterogeneity including Target-B head 6;
13. entropy over time;
14. O/O_sham/C/C_sham sink and target controls.

---

# 31. Acceptance Criteria

Stage 3C.2 technically passes if:

1. the exact Stage 3C.1 causal targets remain frozen;
2. no attention is used to define the causal target ROI;
3. mention ROI is manually/semantically defined without attention;
4. primary examples satisfy `M != T`;
5. at least 24 valid primary bases are retained;
6. temporal state labels are frozen before attention analysis;
7. exact Stage 3C.1 full-shape eager reconstruction is reused;
8. source-mass partition closure passes tolerance;
9. target/mention/irrelevant/sink sets are mutually audited;
10. QK cosine/logit and αV/post-W_O are extracted exactly;
11. attention-budget accounting sums correctly;
12. candidate-sink status remains descriptive;
13. noncausal-head controls are frozen from prior causal work;
14. base_problem_id remains the statistical unit;
15. all primary contrasts are prospectively frozen;
16. Holm correction is applied to the frozen family;
17. head-level heterogeneity is preserved;
18. no Q/K/alpha/sink/h_pre/source-state intervention is run;
19. no Stage 4 or failure experiment is started;
20. exactly one next causal recommendation is written.

Technical PASS does not require a retrieval-dominant or sink-release result.

---

# 32. Stop Condition

After:

- dissociation cohort construction;
- semantic mention/retrieval annotation;
- exact attention/QK/Value extraction;
- temporal mention-vs-target analysis;
- attention-budget accounting;
- sink dynamics;
- noncausal-head and sham controls;
- phenotype classification;
- exactly one next-stage recommendation;

**STOP.**

Do not start:

- query patching;
- QK manipulation;
- target-vs-distractor routing intervention;
- sink knockout;
- sink mass redistribution;
- `h_pre` patching;
- multi-evidence causal refresh;
- failure analysis.

Return the complete Stage 3C.2 results for review.

The next plan must be chosen only after jointly considering Stage 3C.2 with all prior Stage 2A–3C.1 evidence.
