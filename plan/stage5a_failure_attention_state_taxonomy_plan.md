# Stage 5A Plan — Failure / Attention-State Taxonomy
## When the Model Looks at the Image, What Computational State Is It In?

## 0. Purpose

Stages 3C and 4A establish that high visual attention is not sufficient to characterize multimodal reasoning.

We now have several independently grounded phenomena:

```text
semantic alignment
task-conditioned causal retrieval
reasoning-triggered visual dependence
dynamic A → B → A source switching
visual re-engagement / refresh
local visual-source insensitivity
mixed A/B support
isolated stale-source failures
correct local retrieval followed by globally wrong reasoning
```

Stage 4A provides the strongest dynamic result so far:

```text
reasoning demand: A → B → A
causal visual dependence: A → B → A
```

with robust native source switching and later re-engagement, while the specific Stage 3C.10 R16/layers16–23 trigger retargeting assay did not generalize robustly enough to establish O3.

The next paper-critical question is:

> **When visual attention is high, what does that attention actually mean?**

Stage 5A does **not** assume that high visual attention corresponds to one mechanism.

Instead it constructs a large, causally grounded taxonomy of multimodal states and failures, separating:

```text
alignment
retrieval
verification / re-check
dynamic refresh
mixed support
misretrieval
failed refresh / stale evidence
unsupported grounding
mirage
visual hallucination
downstream integration failure
```

The primary goal is not to build a classifier.

The primary goal is to determine whether apparently similar visual-attention events correspond to **different causal computations**.

---

# 1. Why This Stage Is Important for the Paper

The main paper story after Stage 4A is:

> **Thinking MLLMs dynamically retrieve visual evidence according to evolving reasoning demands.**

That claim explains *when and what* the model causally uses.

But a major interpretability ambiguity remains:

```text
high visual attention
```

can arise during:

- mere semantic alignment;
- genuine evidence retrieval;
- re-checking / verification;
- wrong-source retrieval;
- stale-source persistence;
- unsupported visual claims;
- hallucination-like grounding.

If Stage 5A shows that these states have distinct causal/internal signatures, the paper gains a second conceptual insight:

> **Visual attention is not a unitary state. The same apparent visual grounding can correspond to fundamentally different causal computations.**

This also creates a principled foundation for the later mechanism-guided failure-rescue experiment.

---

# 2. Why Taxonomy Comes Before Full Failure Rescue

Stage 4A contained only:

```text
0 strict A-dominant B-event failures
2 strict stale-B A2 cases
1 tied B case
```

so a full Stage 4B intervention would have had too little clean failure support.

The correct sequence is:

```text
discover causal failure classes at scale
→ determine which class is common and mechanistically coherent
→ design a failure-class-matched intervention
```

Stage 5A therefore identifies the failure class that a later Stage 5B rescue experiment should target.

---

# 3. Core Scientific Questions

Stage 5A asks:

1. **Can semantic alignment and genuine retrieval be distinguished internally when both produce high visual attention?**
2. **Do correct retrieval, verification, refresh, misretrieval, and hallucination occupy distinct causal states?**
3. **Can high-attention but low-causality “mirage” events be identified?**
4. **When a visual claim is wrong, where did the causal pipeline fail?**
5. **Is hallucination mainly a failure to retrieve, retrieval of the wrong source, incorrect source-coupled extraction, or downstream reasoning integration?**
6. **Does attention magnitude alone distinguish these states?**
7. **Which feature families add discriminative information beyond attention: QK, Value transport, causal source dependence, retrieval-trigger effects, residual state, or sink dynamics?**
8. **Which failure phenotype is frequent and coherent enough to justify a mechanism-guided rescue stage?**

---

# 4. Claim Discipline

Stage 5A must preserve three distinctions.

## 4.1 Attention is not the ground-truth label

No event is labeled:

```text
retrieval
hallucination
mirage
misretrieval
```

because of attention magnitude alone.

Labels must first come from:

```text
semantic correctness
reasoning demand
causal source dependence
counterfactual semantic control
temporal reasoning structure
```

Attention is analyzed **after causal/semantic labels freeze**.

## 4.2 Wrong final answer is not automatically hallucination

A wrong final answer may arise from:

```text
correct visual retrieval
+
later arithmetic/logical failure
```

Such a case is an integration/reasoning failure, not a visual hallucination.

## 4.3 A null in one causal assay does not prove absence of visual information

Redundancy, earlier acquisition, broad residual state, or source-window mismatch may mask necessity.

Use multiple convergent assays before assigning strong failure labels.

---

# 5. Taxonomy Is Multi-Axis, Not Initially One-Hot

Do not begin by forcing every event into one exclusive class.

Every event receives frozen labels along independent axes.

## Axis A — Semantic / reasoning role

```text
MENTION_ONLY
CURRENTLY_DEMANDED
VISUAL_CLAIM
VERIFICATION_OR_RECHECK
REFRESH_OR_REENGAGEMENT
SUBGOAL_TRANSITION
OTHER
```

## Axis B — Local claim correctness

```text
CORRECT
INCORRECT
UNDECIDABLE
NO_EXPLICIT_CLAIM
```

## Axis C — Causal visual-source profile

```text
DEMANDED_ROI_DOMINANT
ALTERNATIVE_ROI_DOMINANT
MIXED_VISUAL_SUPPORT
LOCAL_VISUAL_INSENSITIVE
UNRESOLVED
```

## Axis D — Temporal state

```text
FIRST_USE
REUSE_WITHOUT_INTERVENING_SOURCE
REFRESH_AFTER_OTHER_SOURCE
STALE_PRIOR_SOURCE
NONE
```

## Axis E — Attention phenotype

Frozen only after Axes A–D:

```text
HIGH_MATCHED_VISUAL_ATTENTION
LOW_MATCHED_VISUAL_ATTENTION
TARGET_DOMINANT
MENTION_DOMINANT
MIXED_ATTENTION
SINK_RELEASE
SINK_PERSISTENT
```

Human-readable failure/state classes are derived from combinations of these axes.

---

# 6. Derived State Classes

## 6.1 Semantic Alignment

Operationally:

- current text semantically mentions/aligns with visual entity M;
- M is not the current demanded causal source;
- M may receive elevated visual attention;
- M has weak current-readout causal dependence relative to demanded T.

Core idea:

```text
looks at what it is talking about
without needing that source for the current inference
```

## 6.2 Genuine Retrieval

Operationally:

- a demanded ROI T is prospectively identified;
- T suppression harms the local evidence readout;
- T effect exceeds irrelevant / non-demanded ROI;
- counterfactual T content controls the local semantic preference where available.

## 6.3 Verification / Re-check

Operationally:

- the visual fact has already been explicitly available in prior reasoning;
- the same fact is later semantically required again;
- local source dependence on that ROI reappears.

Do not assume verification implies a new acquisition event.

## 6.4 Dynamic Refresh / Re-engagement

Operationally:

- source A was used;
- reasoning later required source B;
- A becomes causally dominant again at a later A2 event.

Stage 4A supplies positive anchor cases.

## 6.5 Misretrieval

Operationally:

- reasoning demand specifies source T;
- a distinct non-demanded source X has stronger causal dependence than T;
- the local output is incorrect or inconsistent with the demanded fact.

Do not define misretrieval from attention alone.

## 6.6 Failed Refresh / Stale Evidence

Operationally:

- reasoning demand returns to source A after a B interval;
- source B remains causally dominant or A fails to re-establish local causal dependence;
- local A-related reasoning is impaired.

Stage 4A stale-B cases are historical anchors, not the primary cohort.

## 6.7 Unsupported Grounding

Operationally:

- the generated text makes a visual claim about source X;
- local X causal dependence is weak;
- counterfactual X content has little semantic control where available.

This is the causal precursor to a possible mirage label.

## 6.8 Mirage

A stricter subclass of unsupported grounding:

```text
apparently strong visual grounding phenotype
+
weak causal grounding
```

Operational definition must be frozen from the discovery cohort before confirmation.

A candidate strict definition is:

- unsupported-grounding causal profile;
- matched visual-attention z-score above the frozen high-attention threshold.

Mirage explicitly means:

> **It looks visually grounded from attention, but the attended visual source is not strongly causal for the claim.**

## 6.9 Visual Hallucination

Operationally:

- local visual claim is objectively inconsistent with the image;
- the event is subclassified by its causal source profile.

Subtypes are below.

## 6.10 Integration Failure

Operationally:

- local visual evidence/claim is correct;
- demanded ROI is causally grounded;
- later reasoning/final answer becomes wrong.

This is downstream of visual acquisition and should not be conflated with hallucination.

---

# 7. Hallucination Subtypes

## H-NR — No-Retrieval / Weak-Grounding Hallucination

```text
incorrect visual claim
+
weak demanded/claimed ROI causal dependence
+
weak counterfactual semantic control where available
```

## H-MR — Misretrieval Hallucination

```text
incorrect visual claim
+
wrong/alternative ROI causally dominates demanded ROI
```

## H-SC — Source-Coupled Extraction Error

```text
incorrect visual claim
+
correct ROI is causally important
+
counterfactual manipulation of that ROI systematically moves the claim
```

Interpretation:

> the output is source-coupled but the extracted/decoded visual content is wrong.

Do not claim that a particular hidden representation itself is incorrect unless separately probed.

## H-ST — Stale-Source Hallucination

```text
current demand switched
+
previous source remains causally dominant
+
resulting claim is wrong
```

## H-INT — Downstream Integration Error

Not a visual hallucination proper:

```text
correct causally grounded visual fact
+
later reasoning error
```

Keep separate.

---

# 8. Cohort Architecture

Stage 5A uses three complementary cohorts.

## 8.1 Historical causal-anchor cohort

Reuse prior independently labeled events for calibration and conceptual anchoring.

Include where available:

```text
Stage 3C.2 M≠T alignment/retrieval events
Stage 3C.10 reasoning-triggered retrieval events
Stage 4A A1/B/A2 switch/refresh events
Stage 4A stale-B / tied / mixed-support events
Stage 3C.9R isolated checkpoints / source-sensitive nonrescued events
```

Historical anchors are **not** used to estimate prevalence in the new cohort.

## 8.2 Fresh natural-prevalence cohort

Target:

```text
200 unique bases
```

Minimum:

```text
160
```

Selection rule:

> first eligible score-blind prefix from a prospectively frozen generation screen.

Do not balance by correctness.

This cohort estimates how often semantic/correctness states arise naturally.

## 8.3 Fresh causal-atlas cohort

Target:

```text
128 unique bases
```

Minimum:

```text
96
```

Construct from the natural cohort using prospectively frozen semantic strata.

Target composition, if feasible:

```text
64 locally correct / successful visual-reasoning bases
64 locally incorrect / failure-containing bases
```

This is a case-control mechanistic cohort and **must not** be used for natural prevalence estimates.

Match correct/failure cases where feasible on:

```text
evidence type
geometry/template family
reasoning progress
event role
candidate length
```

No matching uses attention or causal-source effects.

---

# 9. Screening Budget

Recommended initial generation budget:

```text
800 trajectories
```

with prospective extension to:

```text
1400
```

only if required to obtain the frozen cohort sizes.

Retain complete accounting:

```text
attempted
completed
correct final
wrong final
visual-event eligible
local claim correct
local claim incorrect
multi-source eligible
counterfactual-edit eligible
retained natural
retained causal atlas
```

Do not relax semantic validity to increase hallucination yield.

---

# 10. Evidence Diversity

The primary cohort should not be limited to one exact visual-fact form if the benchmark supports broader clean annotations.

Stratify and report:

```text
length labels
angle labels
radius labels
formula labels
numeric text labels
spatial/relational evidence if cleanly localizable
other localized visual facts
```

Do not claim generality beyond represented strata.

Template family must be recorded to allow grouped generalization analysis.

---

# 11. Event Selection

For every retained base, identify up to:

```text
3 frozen visual-relevant events
```

before causal scoring.

Prospective event priorities:

1. first explicit visual claim or visual-demand event;
2. first later event with a changed subgoal/source demand;
3. final or late visual claim/re-use event.

If fewer than 3 valid events exist, retain the available frozen events.

No event is selected because of attention or causal score.

---

# 12. Event Annotation

Each event stores:

```text
token start/end
reasoning progress
mentioned visual entity
demanded visual entity
claimed visual fact
ground-truth visual fact
prior explicit availability of the fact
previous demanded source
next downstream use
local correctness
final correctness
```

Annotators are blind to attention and causal scores.

---

# 13. ROI Annotation

For every event freeze:

```text
T = demanded/correct source ROI
M = mentioned/aligned ROI if different
X = plausible alternative/wrong source ROI if present
I = irrelevant visual control ROI
```

Not every event requires all four.

All ROI definitions are attention-independent.

Exact visual-token maps must be stored.

---

# PHASE A — BROAD SEMANTIC / BEHAVIORAL CENSUS

## 14. Goal

Before expensive causal scoring, characterize the natural distribution of:

```text
alignment-only candidates
retrieval-demand candidates
verification/re-check candidates
refresh candidates
incorrect visual claims
wrong final answers with correct local visual claims
multi-source competition events
```

This phase estimates **semantic prevalence**, not causal-state prevalence.

---

# 15. Natural-Prevalence Outputs

Report per base and event:

```text
local visual claim correctness
final correctness
mention-demand mismatch
reuse/recheck status
source-switch status
A→B→A-like structure
```

Do not label hallucination subtypes yet.

---

# PHASE B — CAUSAL SOURCE PROFILE

## 16. Canonical Execution

Use the frozen A6000 protocol:

```text
A6000 only
BF16
fixed repaired cached path
max 2048 generated-token chunk
same model/tokenizer
same GQA/RoPE semantics
```

All arms for an event use the same execution path.

---

# 17. Primary Local Source Window

Use:

```text
W2 = [t-1, t]
```

as the primary causal source window, inherited from Stage 4A.

At all 36 language layers / all 32 heads:

```text
selected ROI contribution → 0
```

without attention renormalization.

---

# 18. W8 Sensitivity

Also run:

```text
W8 = [t-7, ..., t]
```

for the demanded ROI T on all causal-atlas events.

For M/X/I controls, W8 may be restricted to the frozen confirmatory subset if compute requires.

W2 remains primary.

A W2 null with W8 positive is labeled:

```text
BROADER_LOCAL_SOURCE_DEPENDENCE
```

not visual-insensitive.

---

# 19. Source Arms

Where available, score:

```text
Native
Suppress T
Suppress M
Suppress X
Suppress I
Suppress T+X or T+M as a secondary mixed-support control
```

Do not sum single-source effects to infer unique information fractions.

---

# 20. Source-Dependence Metrics

For ROI `R`:

```text
VSD_R = D_native - D_suppress_R
```

using the frozen local candidate preference.

Also retain:

```text
target-minus-irrelevant
target-minus-alternative
mentioned-minus-target
joint-minus-demanded
```

Unnormalized causal effects are primary.

---

# 21. Source-Profile Classification

Using frozen thresholds, classify:

## Demanded-source dominant

```text
VSD_T substantial
and
VSD_T > VSD_X/I
```

## Alternative-source dominant

```text
VSD_X > VSD_T
```

with minimum effect requirements.

## Mixed support

```text
VSD_T and VSD_X/M both substantial
```

## Local visual-insensitive

```text
W2 T weak
and
W8 T weak
```

under tested windows.

## Unresolved

Mechanically valid but conflicting/threshold-sensitive.

Do not force every event into a clean class.

---

# PHASE C — COUNTERFACTUAL SEMANTIC CONTROL

## 22. Why This Is Needed

Necessity through ROI suppression and semantic control through counterfactual editing answer different questions.

A high-attention event may:

```text
depend on the ROI generally
```

without its specific semantic content controlling the output.

Counterfactual edits test:

> **Does changing the visual fact itself move the local claim in the expected semantic direction?**

---

# 23. Counterfactual Subset

Target:

```text
64 causal-atlas bases
```

Minimum:

```text
48
```

Freeze before counterfactual effect scoring using only:

```text
edit feasibility
event validity
evidence-type strata
correct/failure semantic strata
```

No attention/VSD-based selection.

---

# 24. Counterfactual Conditions

For the primary claimed/demanded ROI:

```text
Original
Counterfactual semantic edit
Matched sham edit
```

For multi-source events where feasible:

```text
independent T/X or A/B factorial edits
```

Keep token layout and rendering pipeline matched.

---

# 25. Counterfactual Semantic Effect

Measure:

```text
CE =
semantic preference under original image
-
semantic preference under counterfactual image
```

with direction aligned to the edited fact.

Also report:

```text
CE - |sham shift|
```

A strong source-coupled event should show semantic control beyond sham.

---

# PHASE D — RETRIEVAL-DEMAND / TRIGGER PROFILE

## 26. Why Include Trigger Information

Stage 3C.10 showed that recent reasoning contribution causally changes target-specific visual dependence.

Stage 5A uses this as one possible internal signature, not as a required taxonomy label.

---

# 27. Trigger Assay

On a frozen subset of:

```text
96 causal-atlas bases target
minimum 80
```

remove recent-R contribution using the frozen Stage 3C.10 mechanism:

```text
last up to 16 generated reasoning positions
layers 16–23
current query only
all 32 heads
```

Measure the change in demanded ROI VSD.

Do not run a new trigger localization search.

---

# 28. Trigger Features

Store:

```text
TE_VSD_T
TE_VSD_X/M
target-specific trigger difference
```

Interpretation is secondary:

- retrieval may show positive demanded-source trigger dependence;
- alignment may not;
- failure states may show missing, wrong-source, or stale trigger profiles.

Do not require Stage 3C.10 exact generalization to every new event.

---

# PHASE E — INTERNAL ATTENTION / ROUTING / VALUE ATLAS

## 29. Passive Feature Freeze

Only after semantic and causal labels freeze, extract the same passive features for every event.

Primary feature families:

### Attention

```text
ROI attention mass
ROI attention density
target/mention/alternative attention ratios
visual-attention share
```

### QK routing

```text
QK cosine
scaled QK logits
target-minus-control QK
```

### Value transport

```text
alphaV norm
post-W_O contribution norm
```

### Sink

```text
<|im_start|> mass
sink release relative to matched prior state
largest losing/gaining source group
```

### State / uncertainty

```text
entropy
candidate margin
residual norms
attention-output norms
```

### Causal

```text
VSD_T/M/X/I
counterfactual CE
recent-R trigger effect
```

---

# 30. Layer / Head Scope

Use two predeclared views.

## Historical causal-coordinate view

Where compatible with the event:

```text
layers 28–29
historical selected causal-head sets
```

## All-head late-routing view

```text
all 32 heads
layers 28–29
```

If a new event lacks historical A/B target equivalence, do not invent new causal heads.

Additional all-layer passive summaries are descriptive only.

---

# 31. Matched Attention Normalization

Raw attention is confounded by:

```text
ROI size
sequence length
event position
token count
```

For every ROI-attention feature store:

```text
raw mass
density
matched z-score / matched percentile
```

using controls matched on:

```text
ROI token count
reasoning progress
source class
sequence-length bucket
```

Freeze matching rules before attention-state comparisons.

---

# PHASE F — ALIGNMENT VS RETRIEVAL CONFIRMATION

## 32. Core 2×2 Analysis

Construct events spanning:

```text
semantic alignment: yes / no
task-required causal retrieval: yes / no
```

The most informative cells are:

### Alignment + Retrieval

Mentioned entity is also causally needed.

### Alignment-only

Mentioned entity receives semantic alignment but is not the demanded causal source.

### Retrieval-only

Demanded source is causal without corresponding local lexical mention/alignment.

### Neither

Matched baseline.

---

# 33. Primary Question

At matched visual-attention levels, ask whether:

```text
QK
alphaV
causal VSD
counterfactual CE
trigger effect
sink behavior
```

distinguish alignment from retrieval.

This is more important than whether mean attention differs.

---

# 34. Attention-Matched Analysis

Prospectively form matched pairs or strata with similar:

```text
visual attention density
ROI size
reasoning progress
```

but different causal labels.

Primary target comparison:

```text
high-attention alignment-only
vs
high-attention genuine retrieval
```

If these states differ causally/internally despite similar attention magnitude, this directly supports:

> **High visual attention is not a unitary computational state.**

---

# PHASE G — MIRAGE ANALYSIS

## 35. Discovery and Confirmation Split

Mirage requires an attention threshold, so avoid defining it on the same cases used for confirmation.

Use:

```text
historical anchor + first 32 causal-atlas bases
```

as discovery only.

Freeze a high-attention criterion.

Then confirm on the remaining fresh causal-atlas bases.

---

# 36. Strict Mirage Candidate

A candidate strict mirage event satisfies:

```text
high matched visual-attention criterion
+
weak claimed/demanded ROI VSD
+
weak counterfactual semantic control where available
```

and may be correct or incorrect.

If the local visual claim is incorrect, classify additionally as:

```text
hallucinatory mirage
```

If correct:

```text
benign mirage
```

This distinction tests whether apparent grounding can be causally unnecessary even when the answer happens to be correct.

---

# 37. Mirage Controls

Compare mirage vs genuine retrieval matched on:

```text
attention magnitude
ROI size
event position
local claim type
```

Primary differentiators:

```text
VSD
CE
QK
alphaV
trigger effect
sink release
```

---

# PHASE H — HALLUCINATION / FAILURE CAUSAL DECOMPOSITION

## 38. Hallucination Eligibility

A hallucination analysis event must contain an objectively checkable local visual claim.

Do not infer hallucination from final-answer wrongness alone.

---

# 39. Failure Decision Tree

For an incorrect visual claim:

### Step 1 — Is demanded/correct ROI causally relevant?

If no:

```text
H-NR candidate
```

unless another source dominates.

### Step 2 — Does an alternative/wrong ROI dominate?

If yes:

```text
H-MR
```

### Step 3 — Does correct ROI have strong VSD and counterfactual semantic control?

If yes:

```text
H-SC source-coupled extraction error
```

### Step 4 — Was the local visual claim actually correct but later reasoning wrong?

If yes:

```text
H-INT / integration failure
```

not visual hallucination.

### Step 5 — In multi-evidence refresh events, does stale prior source dominate?

If yes:

```text
H-ST
```

---

# 40. Confidence Hierarchy for Failure Labels

## Tier 1 — Strong causal diagnosis

Requires convergent:

```text
suppression
counterfactual semantic control
matched controls
```

## Tier 2 — Causal source diagnosis

Suppression-based source profile without counterfactual confirmation.

## Tier 3 — Semantic-only candidate

Incorrect/unsupported claim but causal source profile unavailable.

Paper-level mechanistic claims should rely primarily on Tier 1/2.

---

# PHASE I — STATE SEPARABILITY ANALYSIS

## 41. Why This Is Secondary

A classifier can show that states are separable, but classifier accuracy is not itself a mechanism.

Use it only to quantify whether internal signatures contain enough information to distinguish causal states.

---

# 42. Frozen Feature Families

Compare predictive value of:

## F1 — Attention only

```text
attention mass/density
attention ratios
```

## F2 — Attention + QK

## F3 — Attention + QK + Value

```text
alphaV
post-W_O
```

## F4 — Causal features

```text
VSD
CE
trigger effects
```

## F5 — Full internal signature

Includes:

```text
sink
entropy
residual norms
```

---

# 43. Held-Out Evaluation

Use grouped splits by:

```text
base_problem_id
and
template/geometry family where possible
```

No token/event leakage across train/test.

Primary tasks:

```text
alignment vs retrieval
retrieval vs mirage
grounded-correct vs hallucination
failure subtype classification
```

Report:

```text
balanced accuracy
macro F1
AUROC where binary
calibration
```

The key scientific comparison is:

> **How much does attention-only lag behind causally informed features?**

---

# 44. Unsupervised Geometry

Secondary only.

Use frozen normalized features to examine whether causal labels occupy different neighborhoods.

Acceptable analyses:

```text
PCA
UMAP for visualization only
hierarchical clustering
silhouette / neighborhood purity
```

Do not discover the taxonomy solely from clusters.

---

# PHASE J — STATE-SPECIFIC NEXT-TOKEN UTILITY

## 45. Why This Matters

A high-attention aligned ROI may be:

```text
useful
neutral
or actively interfering
```

Stage 5A should obtain a first causal utility profile without performing the full Stage 6 attention-mechanism study.

---

# 46. Alignment-Only Utility Arm

On a frozen subset of:

```text
48 alignment-only events target
minimum 32
```

remove the aligned-but-nondemanded ROI contribution under the same local W2 assay.

Measure:

```text
correct local-token NLL
demanded evidence preference
final candidate margin
```

Possible outcomes:

### Helpful alignment

Removal worsens prediction.

### Benign alignment

Removal has negligible effect.

### Interfering alignment

Removal improves demanded prediction.

This is a bounded causal utility test, not a full explanation of why alignment attention exists.

---

# 47. Why Stage 5A Stops Before Text↔Visual Representation Translation

The deeper hypothesis:

> **visual `"AB"` may become text-like and enter the same semantic addressing space as textual `"AB"`**

is important but belongs to the next dedicated stage:

```text
Causal Meaning of Visual Attention
```

Stage 5A should save the necessary alignment events but should **not** yet run:

```text
visual-token ↔ text-token state substitution
text-text vs visual-text pathway equivalence
layer-wise semantic translation tracing
```

Those experiments should be designed after the taxonomy tells us which alignment states are functionally meaningful.

---

# PHASE K — SINK AS A TAXONOMY FEATURE, NOT YET A CAUSAL TARGET

## 48. Sink Analysis

Measure candidate sink behavior across:

```text
alignment
retrieval
verification
refresh
mirage
misretrieval
hallucination
integration failure
```

Primary question:

> **Is sink release state-specific enough to justify a later causal sink experiment?**

Report:

```text
sink mass
sink release
target-gain vs sink-loss correlation
matched-state differences
```

No sink intervention occurs in Stage 5A.

---

# 49. Sink-Causality Gate for a Future Stage

Recommend sink causality only if all are satisfied:

1. sink behavior differs robustly between causal states after matched controls;
2. sink effect is not explained by generic visual-attention magnitude;
3. sink pattern is reproduced in fresh held-out cases;
4. a causal sink mechanism would materially improve the paper explanation;
5. there is a clear predicted behavioral consequence of manipulating the sink.

Otherwise keep sink as descriptive supporting evidence.

---

# 50. Primary Statistical Unit

Primary independent unit:

```text
base_problem_id
```

Events are nested repeated observations.

Use:

```text
per-base state summaries
cluster/bootstrap by base
mixed-effects models as secondary
```

Do not treat hundreds of event rows as independent samples.

---

# 51. Multiple-Comparison Families

Predeclare separate families for:

```text
alignment vs retrieval
mirage vs retrieval
hallucination subtype causal contrasts
sink descriptive contrasts
alignment-utility arm
```

Do not create one giant family across unrelated analyses.

Use the project's standard:

```text
paired/nonparametric tests
Holm correction
base bootstrap
```

where applicable.

---

# 52. Template / Geometry Robustness

Because MathVerse can contain repeated geometry templates:

1. record template/geometry family;
2. report leave-one-template-family-out sensitivity;
3. use grouped train/test splits for classifiers;
4. do not claim broad population generality if one template dominates a state class.

---

# 53. Correctness Stratification

Report every major state comparison separately for:

```text
locally correct events
locally incorrect events
globally correct bases
globally wrong bases
```

This distinguishes:

```text
visual grounding state
```

from:

```text
final task success
```

---

# 54. Primary Scientific Outcomes

## O1 — Multi-State Visual Attention

If matched high-attention events separate into alignment/retrieval/mirage causal profiles:

> **High visual attention is not a unitary computational state.**

## O2 — Causal Retrieval Signature

If retrieval is characterized by:

```text
target-specific VSD
semantic counterfactual control
QK / Value transport
```

beyond attention magnitude:

> **Genuine visual retrieval has a distinct causal signature from semantic alignment.**

## O3 — Mirage

If high-attention events with weak causal grounding reproduce on fresh confirmation cases:

> **Some visually grounded-looking attention events are causal mirages.**

## O4 — Hallucination Subtypes

If wrong visual claims decompose into multiple robust causal patterns:

> **Visual hallucination is mechanistically heterogeneous rather than a single failure mode.**

## O5 — Integration Failure Separation

If many wrong final answers retain correct, causally grounded local visual evidence:

> **A substantial class of apparent multimodal failures occurs downstream of visual retrieval rather than during grounding.**

## O6 — Alignment Interference

If removing nondemanded aligned ROI improves demanded prediction in a reproducible subset:

> **Semantic alignment can sometimes compete with task-relevant visual computation.**

## O7 — Sink-State Association

If sink release distinguishes causal states robustly:

> **Sink dynamics are a candidate state-specific routing mechanism worth causal testing.**

This alone is not a sink-causality claim.

---

# 55. What Would Make This Stage Insightful?

The strongest outcome is not:

```text
retrieval has higher attention than hallucination
```

The strong outcome is something like:

> **Two events can exhibit equally high visual attention, yet one is causally grounded and semantically controlled by the image while the other is alignment-only or a causal mirage.**

Or:

> **Wrong visual claims arise from distinct causal failures: failure to retrieve, wrong-source retrieval, source-coupled extraction error, stale-source use, and downstream integration error.**

Those results change how visual attention and hallucination should be interpreted.

---

# 56. What Would Not Be Enough

Do not build the paper headline around:

```text
mean attention differs across correct/wrong answers
```

or:

```text
a classifier predicts hallucination from hidden states
```

without causal grounding.

Do not call a wrong answer:

```text
hallucination
```

unless the local visual claim is semantically checkable.

Do not call high attention:

```text
retrieval
```

without causal source evidence.

---

# 57. Decision for the Next Stage

Stage 5A must recommend exactly one next scientific action.

## GO — Stage 5B Mechanism-Guided Failure Rescue

Use if:

- at least one failure class has sufficient yield;
- its causal diagnosis is coherent;
- there is a mechanism-specific intervention with a falsifiable rescue prediction.

Recommended practical minimum:

```text
>= 24 Tier-1/2 events
```

for one failure class, or a smaller clearly justified pilot followed by fresh confirmation.

## GO — Stage 6 Causal Meaning of Visual Attention

Use if:

- alignment/retrieval/mirage states are clearly separable;
- the largest unanswered question becomes why visual-text alignment occurs and what its attention contribution computes.

## GO — Sink Causality

Use only if the sink gate passes and sink causality is more paper-critical than the two options above.

Do not choose the next stage merely because it was previously listed on the roadmap.

---

# 58. Expected Stage 5B Intervention Candidates

Do not run these in Stage 5A.

Possible future mapping:

```text
H-NR / missed retrieval
→ demand-triggered visual refresh

H-MR / misretrieval
→ demand-consistent source rerouting

H-ST / stale source
→ stale-carrier suppression + demanded-source refresh

Mirage
→ suppress alignment-only source or induce genuine causal retrieval

H-SC source-coupled extraction error
→ retrieval strengthening may not help; investigate value/extraction

H-INT integration failure
→ visual retrieval intervention predicted to have little benefit
```

The point of Stage 5A is to determine which of these is actually worth testing.

---

# 59. Passive Data to Preserve for Stage 6

For all suitable events retain:

```text
visual ROI token identities
text entity token identities
tokenization spans
text↔visual QK features
visual↔visual controls
text↔text repeated-entity controls where naturally available
layer-wise residual summaries
```

These data support the future question:

> **Do visual symbols become functionally text-like inside the language stack?**

No representation-substitution intervention occurs yet.

---

# 60. Output Structure

```text
outputs/stage5a/
  config/
    stage5a_config.json
    cohort_rules.json
    annotation_ontology.json
    derived_taxonomy_rules.json
    source_windows.json
    mirage_discovery_rule.json
    statistical_families.json

  cohort/
    screening_accounting.json
    historical_anchor_manifest.jsonl
    natural_prevalence_manifest.jsonl
    causal_atlas_manifest.jsonl
    exclusions.jsonl
    template_families.json

  annotations/
    events.jsonl
    semantic_roles.jsonl
    claim_correctness.jsonl
    temporal_roles.jsonl
    roi_t_m_x_i.jsonl
    local_and_final_correctness.jsonl

  audit/
    canonical_path_audit.json
    event_index_audit.json
    roi_audit.json
    source_suppression_selectivity.json
    counterfactual_edit_audit.json
    trigger_intervention_audit.json
    telemetry_reconstruction.json
    self_patch_validation.json
    deterministic_replay.json

  phase_a_census/
    semantic_prevalence.json
    event_prevalence.json
    correctness_strata.json

  phase_b_causal/
    w2_source_profiles.jsonl
    w8_source_profiles.jsonl
    mixed_support_controls.jsonl
    causal_state_classification.json

  phase_c_counterfactual/
    subset_manifest.jsonl
    semantic_effects.jsonl
    sham_effects.jsonl
    factorial_source_controls.jsonl

  phase_d_trigger/
    trigger_subset_manifest.jsonl
    trigger_effects.jsonl

  phase_e_internal/
    attention_features.jsonl
    qk_features.jsonl
    value_features.jsonl
    sink_features.jsonl
    state_uncertainty_features.jsonl

  phase_f_alignment_retrieval/
    two_by_two_cells.json
    attention_matched_pairs.jsonl
    matched_state_statistics.json

  phase_g_mirage/
    discovery.json
    frozen_rule.json
    confirmation.jsonl
    mirage_statistics.json

  phase_h_failure/
    hallucination_events.jsonl
    failure_decision_tree.jsonl
    subtype_statistics.json
    integration_failures.jsonl

  phase_i_separability/
    feature_sets.json
    grouped_splits.json
    classifier_results.json
    feature_ablation.json
    unsupervised_geometry.json

  phase_j_alignment_utility/
    subset_manifest.jsonl
    alignment_removal_results.jsonl
    utility_statistics.json

  phase_k_sink/
    state_sink_statistics.json
    sink_gate.json

  analysis/
    taxonomy_summary.json
    paper_claim_assessment.json
    template_robustness.json
    correctness_stratification.json
    next_intervention_target.json
    figures/

  summaries/
    stage5a_summary.md
    stage5a_acceptance.json
    next_stage_recommendation.md
```

---

# 61. Required Figures

At minimum:

1. taxonomy overview diagram;
2. semantic/correctness prevalence in the natural cohort;
3. demanded/alternative/irrelevant causal-source profiles;
4. alignment vs retrieval at matched attention;
5. attention-only vs causal-feature separation;
6. QK / alphaV / VSD profiles by state;
7. verification/refresh vs first retrieval;
8. mirage vs genuine retrieval at matched attention;
9. hallucination causal decision tree;
10. hallucination subtype frequencies in the natural cohort;
11. causal profiles of H-NR / H-MR / H-SC / H-ST / H-INT;
12. locally correct but globally wrong integration failures;
13. sink behavior by state;
14. trigger effect by state;
15. alignment-only removal utility distribution;
16. helpful / benign / interfering alignment examples;
17. template-family robustness;
18. held-out state-classification feature ablation;
19. representative high-attention states with different causal meanings;
20. final conceptual figure:
    ```text
    same high visual attention
       ├─ semantic alignment
       ├─ causal retrieval
       ├─ verification / refresh
       ├─ mirage
       └─ hallucination / misretrieval
    ```

---

# 62. Acceptance Criteria

Stage 5A technically passes if:

1. ontology is frozen before causal/internal-state results;
2. natural-prevalence cohort is selected without correctness balancing;
3. causal-atlas cohort composition is frozen without attention/causal-effect selection;
4. at least 160 natural-cohort bases are retained;
5. at least 96 causal-atlas bases are retained;
6. local visual claims are annotated independently of final correctness;
7. ROI T/M/X/I definitions are attention-independent;
8. all causal arms use the canonical A6000 path;
9. W2 is primary and W8 is frozen sensitivity;
10. wrong final answer is never automatically labeled hallucination;
11. hallucination subtypes use causal source evidence where available;
12. counterfactual subset is frozen before semantic-effect scoring;
13. internal attention features are extracted only after causal labels freeze;
14. mirage threshold is frozen on discovery and confirmed on held-out fresh cases;
15. classifier splits are grouped by base and template family where feasible;
16. classifier accuracy is not treated as a mechanism;
17. sink is descriptive only;
18. no full failure-rescue intervention is run;
19. no text↔visual representation-substitution experiment is run;
20. exactly one next-stage recommendation is produced.

Technical PASS does not require every proposed failure class to have sufficient yield.

---

# 63. Stop Condition

After:

```text
broad natural census
→ frozen causal-atlas cohort
→ causal source profiles
→ counterfactual semantic control
→ retrieval-trigger signatures
→ internal attention/QK/Value/sink atlas
→ alignment-vs-retrieval matched analysis
→ mirage confirmation
→ hallucination/failure decomposition
→ held-out state separability
→ bounded alignment-utility assay
→ sink-causality gate
→ next intervention target selection
→ exactly one recommendation
```

**STOP.**

Do not start:

```text
Stage 5B failure rescue
Stage 6 text↔visual causal-attention mechanism
Sink Causality
new training experiments
failure-specific deep dives
```

Return the complete Stage 5A result for review.

The next stage must be chosen according to which result most materially strengthens the paper's conceptual story and enables a falsifiable mechanism-guided intervention.
