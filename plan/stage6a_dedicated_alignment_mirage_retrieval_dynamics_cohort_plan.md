# Stage 6A Cohort Plan — Dedicated Alignment / Mirage / Retrieval-Dynamics Stress Cohort
## Controlled Causal Grounding Stress + Natural Failure Validation

## 0. Stage Purpose

Stage 5A showed that the previous MathVerse-centric natural sampling scheme was excellent for finding genuine demanded-source retrieval, but poor for producing the states we now need to study:

```text
strict alignment-only
strict mirage
clean wrong-source error promotion
stale-source hallucination
natural hallucination subclasses
```

The next cohort should therefore **not wait for these states to occur naturally in the same selected-event distribution**.

Instead, Stage 6A deliberately constructs and freezes a set of cohorts in which the following factors can be varied independently:

\[
\boxed{
\text{semantic alignment}
\times
\text{reasoning demand}
\times
\text{evidence availability}
}
\]

and, separately,

\[
\boxed{
\text{correctness / failure type}
\times
\text{visual-state dynamics over reasoning time}
}
\]

The cohort is inspired by the trajectory viewpoint of **Real-Time Visual Attribution Streaming in Thinking Model (vSTREAM)**:

> reasoning should be analyzed not only at one token/event, but as a trajectory through visual-attribution / grounding state.

However, Stage 6A must go beyond a generic “correct trajectories are smoother” analysis.

Stage 4A already established that **successful reasoning can intentionally switch causal visual source**:

```text
demand: A → B → A
visual causal dependence: A → B → A
```

Therefore the new hypothesis is not:

```text
less visual switching = better reasoning
```

but:

\[
\boxed{
\text{successful reasoning exhibits demand-aligned visual-state change}
}
\]

while failures may exhibit at least two distinct dynamic pathologies:

\[
\boxed{
\text{Wandering}
=
\text{visual state changes without a matching reasoning-demand change}
}
\]

\[
\boxed{
\text{Fixation / Staleness}
=
\text{visual state fails to change when reasoning demand changes}
}
\]

A third state family is:

\[
\boxed{
\text{Mirage}
=
\text{visual-looking routing persists after causal evidential grounding collapses}
}
\]

This stage builds the cohort needed to test those claims rigorously.

---

# 1. Paper-Level Motivation

The current main paper story is:

> **Thinking MLLMs perform reasoning-conditioned dynamic visual retrieval.**

The next conceptual question is:

> **How does this dynamic retrieval process differ when reasoning succeeds, wanders, fixates, hallucinates, or only appears visually grounded?**

A strong later result from this cohort could support:

> **Successful multimodal reasoning is characterized not by static visual grounding, but by demand-aligned changes in causal visual state. Failures arise when visual state changes without demand, fails to change with demand, or remains visually active after evidence has disappeared.**

This is a stronger and more mechanistic extension of generic correct-vs-wrong PCA separation.

---

# 2. Scope of Stage 6A

Stage 6A is primarily a **cohort construction, native-generation, annotation, manipulation, and freeze stage**.

It may run only the minimum diagnostics needed to establish that each cohort is mechanically valid and has sufficient semantic/failure yield.

It must **not** yet run the full causal-attention interpretation study.

Specifically, do not yet run:

```text
full causal state comparisons
full text↔visual representation substitution
full failure-rescue intervention
sink causality
mechanism-specific rerouting rescue
new head/layer discovery searches
```

Those belong to the next approved analysis/intervention stage.

---

# 3. Existing Model / Execution Protocol

Primary model:

```text
Qwen3-VL-4B-Thinking
```

Use the frozen canonical A6000 path for all new model execution:

```text
A6000 only
BF16
fixed repaired cached/streaming execution
max generated-token chunk = 2048
allocator-cache release between chunks
same tokenizer/model revision
same GQA/RoPE semantics
same official-style thinking sampling
EOS normal stop
max_new_tokens = 40960 safety ceiling
```

Do not pool absolute scores produced under different BF16 execution shapes.

---

# 4. Dataset Discovery and Download Policy

## 4.1 Search roots

Before downloading anything, inventory:

```text
/data/dataset
/home/hyunjin/.cache/huggingface/datasets
```

Search recursively for candidate dataset names, aliases, image roots, annotations, and cached Hugging Face builders.

Produce:

```text
outputs/stage6a/cohort/dataset_inventory.json
outputs/stage6a/cohort/dataset_inventory.md
```

with:

```text
dataset
version/revision if available
split
local path
annotation path
image path
sample count
license/readme found
usable yes/no
reason
```

## 4.2 Candidate datasets

Inspect in this priority order:

```text
MathVerse
MathVision
MathVista
DocVQA
POPE
COCO 2014/2017
GQA
```

Also record any already-local compatible alternatives, but do not silently substitute them.

## 4.3 Missing datasets

If a required dataset is absent:

1. prefer an existing Hugging Face `datasets`/hub-compatible source;
2. otherwise use the official project/data release;
3. download only the splits/assets needed for this stage;
4. store persistent raw assets under:

```text
/data/dataset/<dataset_name>/
```

or reuse the existing Hugging Face cache when that is the canonical downloaded representation.

Do not install or upgrade global packages.

Use the project virtual environment and existing libraries where possible.

Every download must record:

```text
source
revision / commit / version if available
timestamp
files
checksums where practical
license/readme
```

in:

```text
outputs/stage6a/cohort/download_manifest.json
```

## 4.4 Download failure

If one dataset cannot be obtained, do not silently replace it.

Use the predeclared fallback hierarchy in the relevant cohort section and report the missing stratum.

---

# 5. Cohort Architecture

Stage 6A contains four complementary cohort families.

```text
C1 — Controlled Diagram Grounding-Stress Cohort
C2 — Alignment × Retrieval-Demand Factorial Cohort
C3 — Object Hallucination / Occlusion Stress Cohort
C4 — Natural Open-Ended Failure Validation Cohort
```

They serve different inferential roles.

## Controlled cohorts

Purpose:

```text
mechanism identification
within-base causal comparison
mirage induction
demand/source transition control
```

## Natural cohorts

Purpose:

```text
ecological validation
failure diversity
trajectory phenotype replication
```

Do not use a case-control cohort to estimate natural prevalence.

---

# 6. C1 — Controlled Diagram Grounding-Stress Cohort

## 6.1 Preferred datasets

Target datasets:

```text
MathVerse
MathVision
MathVista
```

Priority:

```text
MathVerse > MathVision > MathVista
```

because the existing intervention machinery is strongest on diagrammatic localized numeric facts.

## 6.2 Target size

Target:

```text
120 unique base problems
```

Preferred balanced composition:

```text
40 MathVerse
40 MathVision
40 MathVista
```

Minimum total:

```text
90 bases
```

Minimum per available dataset stratum:

```text
24
```

If only two datasets are usable, target:

```text
48–60 bases per dataset
```

Do not duplicate exact stimuli across datasets/templates.

## 6.3 Required base properties

Each retained base must have:

1. at least one objectively checkable localized visual fact `T`;
2. exact or high-confidence ROI localization;
3. a local reasoning event whose candidate preference depends on `T`;
4. an editable target detail;
5. a semantically meaningful counterfactual value;
6. enough surrounding visual structure to create a matched background sham;
7. no prior use in a confirmatory subset when avoidable;
8. intact native generation with a resolvable local claim.

Prefer:

```text
length labels
angle labels
radius labels
numeric diagram annotations
formula labels
table/chart values if spatially clean
```

---

# 7. C1 Image Conditions

Each base should support as many of the following within-base conditions as mechanically valid.

## C1.0 — Intact

Original image.

Purpose:

```text
native grounding baseline
```

## C1.1 — Counterfactual semantic edit

Change only target fact:

```text
T = x
→
T = x'
```

with same rendering pipeline.

Purpose:

```text
semantic causal-control baseline
```

## C1.2 — Full target-detail mask

Preserve surrounding geometry/entity identity but remove the evidential detail.

Example:

```text
AB = 3
→
AB = [masked]
```

or preserve `AB` while removing the value glyph.

Purpose:

```text
hard evidence-removal / mirage stress
```

## C1.3 — Partial degradation 1

Mild degradation of the evidential detail.

Examples:

```text
low blur
light pixelation
partial occlusion
```

## C1.4 — Partial degradation 2

Stronger degradation, still preserving the entity/context cue.

Purpose of C1.3/C1.4:

```text
evidence-availability dose response
```

## C1.5 — Aligned distractor

Preserve a semantically matching label/entity cue but make the associated evidence irrelevant to the current answer.

Examples:

```text
same entity label with non-task evidence
same semantic label in a distractor region
```

Purpose:

```text
alignment without evidential support
```

## C1.6 — Unrelated-image control

Pair the prompt with a different image matched as closely as practical on broad visual complexity but unrelated to the target fact.

Purpose:

```text
generic image baseline
```

## C1.7 — No-image baseline

Run the text-only equivalent if the model interface permits a valid no-image input.

Purpose:

```text
language/reasoning prior baseline
```

No-image is **not** itself a mirage condition because visual attention does not exist.

---

# 8. C1 Manipulation Validity

Every manipulation must preserve:

```text
image dimensions
model visual-token layout where possible
non-target geometry
target entity identity for mask/degradation conditions where intended
```

For target masks/degradation, create a matched sham:

```text
same operation
same area
nearby irrelevant/background region
```

Store:

```text
target mask
sham mask
pixel bounding box
visual-token mapping
edit provenance
```

Do not use an image manipulation that changes task semantics outside the declared target unless it is the explicit unrelated-image condition.

---

# 9. C1 Grounding-Collapse Ladder

The intended within-base evidence ladder is:

```text
Intact
→ Mild degradation
→ Strong degradation
→ Full detail mask
→ Unrelated image
→ No image
```

Counterfactual semantic edit is a separate semantic-control branch.

The later analysis should be able to ask whether:

```text
visual attention remains high
while
semantic causal grounding collapses
```

as evidence availability decreases.

Stage 6A only constructs/freeze-validates this ladder.

---

# 10. C2 — Alignment × Retrieval-Demand Factorial Cohort

## 10.1 Scientific purpose

The Stage 5A natural cohort yielded almost no strict alignment-only cases.

C2 therefore deliberately orthogonalizes:

```text
semantic/lexical alignment
```

and:

```text
task-required visual retrieval
```

The intended 2×2 design is:

| Cell | Alignment to ROI | ROI actually needed |
|---|---:|---:|
| AR | yes | yes |
| A-only | yes | no |
| R-only | no/weak | yes |
| Neither | no/weak | no |

The key comparison is:

```text
high-attention A-only
vs
high-attention genuine retrieval
```

but attention is never used to select the cohort.

---

# 11. C2 Preferred datasets

Primary:

```text
DocVQA
MathVerse
```

Secondary/fallback:

```text
MathVision
MathVista
```

Why DocVQA is valuable:

```text
repeated textual labels
headers
field names
table cells
semantically similar strings
multiple spatially distinct text blocks
```

This increases the chance of independently manipulating lexical/semantic match and actual answer relevance.

---

# 12. C2 Target size

Target:

```text
128 base-condition families
```

or enough paired events to provide:

```text
32 confirmed semantic-design events per 2×2 cell
```

Minimum:

```text
24 per cell
96 total usable events
```

Where possible, construct all four cells from the same base image through controlled prompt/question variants.

If all four cells cannot be constructed from one image, use matched base families.

---

# 13. C2 Prompt/Task Construction Rules

C2 may use controlled prompt variants, but they must remain natural enough for ordinary reasoning.

## AR — Alignment + Retrieval

The target ROI/entity is explicitly named or semantically cued and is needed for the answer.

Example pattern:

```text
Using the value for segment AB, ...
```

## A-only — Alignment without Retrieval

The same visual entity is mentioned/cued but its evidence is not required for the target inference.

Preferred constructions:

```text
neutral reference to AB while the actual computation uses CD
question contains an irrelevant repeated field/header
current subgoal mentions M while T determines the answer
```

Avoid blatantly adversarial wording such as:

```text
look at AB even though it is useless
```

unless used only in a clearly labeled stress subset.

## R-only — Retrieval without local lexical alignment

The visual fact is required, but the immediate text avoids the exact matching label.

Examples:

```text
"the upper horizontal segment"
instead of
"AB"
```

or a question that requires a table cell without repeating its exact header/entity token locally.

## Neither

Matched control with neither strong semantic alignment to the ROI nor need for its content.

---

# 14. C2 Pairing Constraints

Within a paired family, match as much as possible:

```text
answer format
candidate-token length
reasoning depth
image
target ROI size
question length
task difficulty
```

Record which properties cannot be matched.

Prompt authoring/selection must occur before any attention or causal score is observed.

---

# 15. C3 — Object Hallucination / Occlusion Stress Cohort

## 15.1 Scientific purpose

C3 targets:

```text
object hallucination
fixation
wrong-source reliance
evidence disappearance
object-level mirage
```

and provides a real-image complement to diagrammatic C1.

---

# 16. C3 Preferred data stack

Preferred:

```text
POPE questions
+
COCO images/instance annotations
```

because object presence/absence can be objectively checked and COCO provides object annotations.

Secondary:

```text
GQA
```

for more compositional object/spatial reasoning.

Use GQA only if the local object/source mapping is sufficiently recoverable from available annotations.

---

# 17. C3 Target size

Target:

```text
160 unique object-question base families
```

Preferred:

```text
80 object-present
80 object-absent / negative
```

Minimum:

```text
120 total
```

For the object-present half, construct target-occlusion variants.

For the object-absent half, retain natural negative examples and matched distractor structures.

---

# 18. C3 Object-Present Conditions

For each selected present-object example:

```text
O0 intact
O1 target object strongly degraded/occluded
O2 target object fully masked where valid
O3 matched-background sham
O4 unrelated-image control
O5 no-image baseline
```

Optional, only if mechanically clean:

```text
O6 object-semantic counterfactual / replacement
```

Do not require generative inpainting.

Simple controlled masking/occlusion is preferred over unconstrained image synthesis for primary causal claims.

---

# 19. C3 Object ROI Requirements

Preferred ROI source:

```text
COCO instance segmentation mask
```

Fallback:

```text
COCO bounding box
```

If only a bounding box is available, record contamination risk from nearby objects.

For each object ROI store:

```text
category
instance id
mask/bbox
area
image fraction
overlap with other instances
visual-token map
```

Exclude extremely tiny or heavily overlapping objects from the primary occlusion cohort.

---

# 20. C3 Natural Negative / Absent-Object Events

For negative POPE-style questions, record:

```text
queried absent object
visually/semantically related present objects
plausible distractor ROIs
```

These events are useful for distinguishing:

```text
language-prior hallucination
semantically related fixation
wrong-source grounding
generic image-induced yes bias
```

Do not invent a nonexistent target ROI.

For absent objects, the relevant visual causal analysis later must focus on:

```text
present distractor sources
global/no-image comparison
semantic alignment signals
```

rather than pretending the absent object has a true ROI.

---

# 21. C4 — Natural Open-Ended Failure Validation Cohort

## 21.1 Scientific purpose

Controlled stress cohorts can be criticized as artificial.

C4 asks whether the trajectory signatures discovered in C1–C3 occur naturally.

Primary target:

```text
COCO open-ended description/caption generation
```

using object-hallucination labeling compatible with CHAIR-style object inventories.

Optional secondary:

```text
GQA naturally wrong reasoning traces
```

if sufficient compatible annotations are available.

---

# 22. C4 Native COCO Sample

Initial random/native sample:

```text
600 images
```

Prospective extension:

```text
up to 1000
```

only if needed to obtain sufficient natural hallucination cases.

Do not oversample based on attention.

Use a fixed neutral accuracy-focused description prompt compatible with Qwen3-VL-Thinking.

Freeze the prompt before generation.

---

# 23. C4 Natural Failure Case-Control Atlas

From the unbiased native COCO sample, create a separate mechanism-comparison atlas.

Target:

```text
100 hallucination-containing bases
100 matched non-hallucination bases
```

Minimum:

```text
60 + 60
```

Match on:

```text
object count
image complexity
caption/reasoning length
dominant object categories
generation length
```

where feasible.

This balanced atlas is **not** used to estimate hallucination prevalence.

---

# 24. C4 Hallucination Labeling

Use objective image annotations and a CHAIR-compatible object normalization procedure.

Separate:

```text
object hallucination
attribute hallucination if reliably annotatable
relation/spatial error
non-visual reasoning error
```

Primary C4 label is object hallucination.

Do not call any wrong sentence a hallucination if it is not objectively image-inconsistent.

---

# 25. Native Reasoning Trace Segmentation

All cohorts use the same attention-independent reasoning segmentation.

Freeze reasoning spans using textual structure only.

Preferred hierarchy:

```text
newline-delimited thinking step
sentence boundary
semicolon/major clause boundary
```

with deterministic fallback rules.

Store:

```text
span_id
token_start
token_end
text
normalized reasoning progress
```

No span boundary may depend on attention or causal effects.

---

# 26. Demand-State Annotation

For controlled cohorts, annotate each reasoning span with:

```text
current demanded visual source(s)
mentioned/aligned source(s)
previous demanded source
whether demand changed from prior span
whether visual evidence is already explicit in prior reasoning
whether this is first use / reuse / refresh
```

For natural COCO captions, demand annotation may be coarser:

```text
object currently being described
attribute/relation currently asserted
no explicit visual demand
```

Do not force precise demand labels when semantics are ambiguous.

Use:

```text
UNRESOLVED
```

rather than guessing.

---

# 27. Required Dynamic Phenotypes

The cohort should be capable of containing the following trajectory types.

## D1 — Demand-aligned switching

```text
demand changes
visual source changes accordingly
```

Stage 4A provides historical positive anchors.

## D2 — Wandering candidate

```text
demand stable
visual state/source changes repeatedly
```

## D3 — Fixation / stale candidate

```text
demand changes
visual state/source fails to change
```

## D4 — Mirage candidate

```text
visual-looking routing remains strong
after evidential content is removed/degraded
```

## D5 — Disconnected/prior candidate

```text
prediction under masked/unrelated image approaches no-image behavior
```

while image-directed attention may persist.

## D6 — Integration failure

```text
correct grounded local evidence
followed by later wrong reasoning
```

---

# 28. Future Visual-State Representation

Stage 6A must preserve the data needed for two complementary future trajectory representations.

## 28.1 Identity-aware within-example state

For controlled multi-source images:

\[
v_s =
[
VSD_A,
VSD_B,
VSD_T,
VSD_X,
\text{other relevant source effects}
]
\]

or the available source set.

This supports direct demand-source coupling.

## 28.2 Canonical region-profile state

For variable-region natural images:

\[
e_s \in \mathbb{R}^{K_i}
\]

where each dimension corresponds to a semantic image region.

For cross-example visualization, later canonicalize profiles only after primary identity-aware analyses are frozen.

A vSTREAM-like option is:

```text
retain/sort top-R region effects
R = 32
```

for PCA visualization.

This is descriptive and must not replace source-identity analyses.

---

# 29. Dense vs Causal Trajectory Data

Exact causal region ablation at every reasoning span and every region may be too expensive.

Therefore Stage 6A preserves a two-tier design for the next stage.

## Dense passive trajectory

At every reasoning span save:

```text
ROI/region attention
QK summaries
alphaV
post-WO summaries
sink mass
entropy
candidate margins
residual norms
```

## Sparse exact causal anchors

Future causal scoring should prioritize:

```text
demand-transition spans
matched no-transition spans
incorrect visual-claim spans
refresh spans
high-risk stress-condition spans
```

The cohort freeze must record these semantic anchor types without using attention.

---

# 30. Optional Fast Attribution Surrogate

Do not make this primary.

If later compute requires dense region-level causal trajectories, a vSTREAM-inspired lightweight estimator may be trained on exact source-ablation labels from a dedicated training subset.

Rules:

1. train only after cohort/split freeze;
2. training and confirmation bases must be disjoint;
3. train on both correct and incorrect/stress conditions, not correct-only;
4. validate against exact causal effects separately in each state family;
5. never use surrogate predictions as the sole ground truth for mirage/hallucination labels;
6. all paper-level causal claims require exact causal anchors.

Stage 6A only preserves the split needed for this option.

---

# 31. PCA / Trajectory Geometry Split

To avoid using the same data to define and confirm trajectory geometry:

## Discovery split

Use approximately:

```text
1/3 of each controlled cohort family
```

and:

```text
first 1/3 of the natural validation sample after random seed freeze
```

for PCA basis/normalization discovery.

## Confirmation split

Remaining:

```text
2/3
```

is projection-only.

Do not refit PCA on confirmation data.

---

# 32. Future Trajectory Metrics to Enable

The cohort must support these predeclared metrics.

## 32.1 Path length

\[
L = \sum_s \|z_{s+1}-z_s\|_2
\]

## 32.2 Tortuosity

\[
\tau =
\frac{\sum_s \|z_{s+1}-z_s\|_2}
{\|z_S-z_1\|_2+\epsilon}
\]

## 32.3 Demand–visual coupling

Primary new metric.

At span `s`:

```text
Does the causally dominant visual source match the semantically demanded source?
```

Aggregate:

```text
coupling rate
demanded-source causal margin
transition-alignment score
```

## 32.4 Unnecessary switching

\[
U =
\#\{s:
d_s=d_{s+1}
\land
v_s\neq v_{s+1}
\}
\]

Interpretation:

```text
wandering-like source reassignment
```

## 32.5 Failed switching

\[
F =
\#\{s:
d_s\neq d_{s+1}
\land
v_s=v_{s+1}
\}
\]

Interpretation:

```text
fixation/staleness
```

## 32.6 Transition latency

Number of reasoning spans/tokens between:

```text
demand change
```

and:

```text
causal visual-source change
```

## 32.7 Mirage gap

A future metric such as:

\[
G_{\text{mirage}}
=
\text{normalized apparent visual-routing strength}
-
\text{normalized causal semantic grounding}
\]

The exact formula must be frozen only after discovery and confirmed on held-out data.

---

# 33. Important Conceptual Boundary

Do not equate:

```text
high path length
```

with:

```text
failure
```

because Stage 4A already shows legitimate A→B→A switching.

The key future comparison is:

```text
purposeful demand-aligned switching
vs
wandering switching
```

Similarly, do not equate:

```text
low path length
```

with:

```text
success
```

because pathological fixation may also be geometrically stable.

Therefore path length/tortuosity are supporting features, not mechanistic labels.

---

# 34. Mirage Induction Logic

A strict future mirage should require evidence along three axes.

## Apparent visual engagement

Examples:

```text
high matched ROI attention
high QK alignment
high visual attention share
```

## Weak causal evidential grounding

Examples:

```text
weak ROI necessity
weak counterfactual semantic control
masked condition resembles no-image prediction
```

## Evidence unavailability / corruption known by construction

Examples:

```text
target value masked
object occluded
aligned distractor irrelevant
```

The controlled cohort makes the third criterion explicit.

---

# 35. No-Image Similarity

For every stress family where a valid no-image condition exists, preserve future comparison of local output distributions.

Potential measure:

```text
KL(P_stress || P_no_image)
JS(P_stress, P_no_image)
candidate-margin correlation
top-k overlap
```

A masked condition that retains strong visual attention but behaves distributionally like no-image is a strong prior-driven/mirage candidate.

No-image similarity is supporting evidence, not proof of zero visual use.

---

# 36. Counterfactual Followability

For every clean semantic edit, store the information needed to test:

```text
does the local prediction move with the edited visual fact?
```

A future strong retrieval pattern is:

```text
native value x → favors x
counterfactual x' → favors x'
```

A future prior/mirage candidate is:

```text
native x → favors x
counterfactual x' → remains near x
masked → remains near x
no image → remains near x
```

---

# 37. Success / Failure Labels

Maintain separate labels:

```text
local visual claim correctness
local reasoning-step correctness
final answer correctness
hallucination presence
```

Do not collapse them into one `success` boolean.

This is essential because Stage 5A already identified correct local visual grounding followed by later integration errors.

---

# 38. Correct / Failure Matching

For every natural failure atlas, build matched correct controls without attention-based matching.

Preferred matching variables:

```text
dataset
template/image family
object count / diagram complexity
evidence type
reasoning progress
reasoning length
answer format
target ROI size
```

Do not use hidden-state features to select matches.

---

# 39. Template and Stimulus Independence

Record:

```text
exact image hash
problem id
template/geometry family
near-duplicate perceptual hash
question family
```

Prevent:

```text
same underlying image
same template
same prompt variant family
```

from crossing discovery/confirmation folds where feasible.

---

# 40. Dataset-Specific Fallbacks

## C1 fallback

If MathVision or MathVista is unavailable or not cleanly editable:

```text
increase MathVerse count
```

but preserve explicit dataset-stratum limitation.

## C2 fallback

If DocVQA is unavailable:

```text
MathVerse/MathVista controlled prompt variants
```

remain valid, but do not claim document-domain replication.

## C3 fallback

If POPE annotations are unavailable but COCO is present:

construct a frozen object-presence question set from COCO annotations before model scoring.

Do not use model outputs to choose positive/negative object questions.

## C4 fallback

If CHAIR tooling/annotations are unavailable:

use COCO object annotations with a frozen synonym-normalization dictionary and independently audit a sample.

Do not silently substitute a different hallucination metric.

---

# 41. Pre-Score Human / Programmatic Review

Before any attention or causal scoring, every controlled base family must pass:

```text
semantic target validity
ROI validity
counterfactual validity
mask validity
sham validity
prompt-factorial validity
answer/readout validity
dataset/stimulus independence
```

Store all exclusions with reason codes.

---

# 42. Mechanical Validation Set

Freeze:

```text
12 validation base families
```

covering:

```text
3 C1 diagram
3 C2 alignment factorial
3 C3 object stress
3 C4 natural generation
```

where feasible.

Validation must confirm:

1. deterministic native replay;
2. correct image variant routing;
3. exact ROI visual-token mapping;
4. no-op self condition;
5. target vs sham mask isolation;
6. counterfactual source isolation;
7. no-image path validity;
8. unrelated-image condition does not reuse the original visual cache;
9. trace segmentation exactness;
10. annotation indices exact;
11. discovery/confirmation split integrity;
12. no attention/causal score enters cohort membership.

---

# 43. Native Generation Budget

Recommended initial acquisition:

```text
C1: 120 intact native trajectories + stress variants after base freeze
C2: 128 base-condition families
C3: 160 base families
C4: 600 native COCO generations
```

Because each controlled base has multiple image/prompt conditions, do not launch all variants before a small mechanical pilot passes.

Use a staged acquisition:

```text
12-base mechanics
→ 24-base pilot
→ freeze rules
→ full cohort
```

Do not change cohort rules based on observed attention/causal effects.

---

# 44. Stress-Variant Generation Order

For each controlled base, use a deterministic condition order only for scheduling/logging; each generation starts from an independent model state.

Recommended logical order:

```text
intact
counterfactual
mild degradation
strong degradation
full mask
matched sham
aligned distractor
unrelated image
no image
```

No KV/cache state may leak across conditions.

---

# 45. Cohort Freeze Rules

Cohort membership may depend only on:

```text
dataset/stimulus identity
semantic validity
ROI editability
ground-truth availability
prompt/task construction validity
native trace interpretability
local readout validity
stress-asset validity
```

It may not depend on:

```text
attention magnitude
QK
alphaV
sink
VSD
counterfactual effect size
PCA location
path length
tortuosity
model confidence
```

Correctness may be used only where a cohort is explicitly defined as a case-control failure cohort; natural prevalence cohorts remain unbalanced.

---

# 46. Historical Anchors

Preserve but keep separate:

```text
Stage 3C.2 alignment/retrieval events
Stage 3C.10 retrieval-trigger events
Stage 4A A→B→A dynamic cases
Stage 4A stale-B examples
Stage 5A demanded-source-dominant events
Stage 5A integration failures
Stage 5A H-MR candidates
Stage 5A H-SC example
```

Historical anchors can guide interpretation and calibration.

They do not count as fresh confirmation samples.

---

# 47. H-MR Feasibility Review Boundary

The existing nine H-MR candidate bases require a separate readout-orientation/source-identity review.

That review may proceed independently.

Stage 6A cohort membership must not depend on whether the H-MR review validates or rejects those cases.

Do not start a wrong-source rescue intervention during this cohort stage.

---

# 48. Data to Save for Future Dense Trajectory Analysis

At native generation time, save enough state to reproduce or extract later:

```text
full token ids
full generated reasoning text
attention summaries by layer/head/source
visual token positions
KV-cache indexing metadata
query positions
candidate logits at frozen events
reasoning-span boundaries
```

Where storage permits, save selected late-layer residual and attention outputs at frozen span endpoints.

Do not sacrifice raw reproducibility for only aggregated plots.

---

# 49. DINO / Semantic Region Option for Natural Images

For C3/C4 variable-region images, it is useful to create a semantic region partition similar in spirit to vSTREAM.

If the required vision foundation model and code are already available locally, create:

```text
16–128 semantic regions/image
```

with deterministic settings and store masks.

If not locally available, do **not** block the core cohort on downloading a new segmentation stack unless separately justified.

Primary object/diagram ROIs should use ground-truth/hand-validated source regions where available.

Semantic clustering is supplemental for dense natural-trajectory visualization.

---

# 50. Future PCA Rules

The later analysis may use PCA for visualization, but Stage 6A must pre-freeze these safeguards:

1. fit PCA only on the discovery split;
2. confirmation data are projection-only;
3. report explained variance;
4. compute key path metrics in the original normalized feature space as well as PCA space;
5. do not infer mechanism from cluster separation alone;
6. never use PCA location to define hallucination/mirage labels;
7. preserve source identity metrics separately from sorted/canonical region profiles.

---

# 51. Future Failure-Dynamics Hypotheses

The cohort is specifically designed to distinguish:

## H-DYN1 — Demand-aligned success

```text
demand transition
→ matching causal visual-source transition
```

## H-DYN2 — Wandering reasoning failure

```text
visual source transitions
without corresponding semantic demand transitions
```

## H-DYN3 — Fixation/stale failure

```text
semantic demand transitions
without matching visual-source transitions
```

## H-DYN4 — Mirage under evidence collapse

```text
apparent visual routing persists
while causal semantic control collapses
```

## H-DYN5 — Prior-driven hallucination

```text
stress-condition prediction approaches no-image behavior
while the model may still show image-directed attention
```

## H-DYN6 — Integration failure

```text
correct demand-aligned grounding
followed by downstream reasoning error
```

---

# 52. What a Null Would Not Rule Out

## No mirage under target masking

Does not prove visual attention is always causal.

Possible explanations:

```text
mask too salient
model uncertainty increases instead
model abandons visual alignment
selected task family too strongly grounded
```

## No wandering in natural failures

Does not prove failures are not dynamic.

Possible explanations:

```text
span segmentation too coarse
failure occurs after visual reasoning
dense passive state misses causal source identity
dataset has mostly integration errors
```

## No fixation

Does not prove stale retrieval does not exist.

Possible explanations:

```text
few demand transitions
object task lacks multi-source structure
occlusion causes immediate fallback to prior
```

## Dataset differences

Do not average away domain-specific mechanisms.

Report dataset/condition interactions explicitly.

---

# 53. Primary Cohort Acceptance Gates

Stage 6A cohort construction is considered successful if:

## C1

```text
>= 90 valid controlled diagram bases
>= 3 evidence-availability conditions/base on average
counterfactual + full-mask available on >= 72 bases
```

## C2

```text
>= 96 usable factorial events
>= 24 events in each 2×2 cell
```

## C3

```text
>= 120 valid object-stress families
>= 50 target-occlusion present-object cases
>= 50 natural negative/absent-object cases
```

## C4

```text
>= 600 unbiased native COCO generations
or
a documented stop after 1000 if hallucination yield remains insufficient
```

For the natural case-control atlas:

```text
target >= 60 hallucination + 60 matched non-hallucination bases minimum
```

If one cohort misses its gate, do not relax semantic definitions after observing internal-state features.

---

# 54. Output Structure

```text
outputs/stage6a/
  config/
    stage6a_config.json
    dataset_priority.json
    cohort_rules.json
    split_rules.json
    prompt_factorial_rules.json
    stress_condition_rules.json
    trace_segmentation_rules.json
    annotation_ontology.json

  cohort/
    dataset_inventory.json
    dataset_inventory.md
    download_manifest.json
    screening_accounting.json
    exclusions.jsonl
    historical_anchor_manifest.jsonl
    discovery_confirmation_split.json

  c1_diagram_stress/
    base_manifest.jsonl
    intact_manifest.jsonl
    counterfactual_manifest.jsonl
    degradation_manifest.jsonl
    mask_manifest.jsonl
    sham_manifest.jsonl
    aligned_distractor_manifest.jsonl
    unrelated_manifest.jsonl
    no_image_manifest.jsonl
    roi_maps.jsonl
    readouts.jsonl

  c2_alignment_factorial/
    base_families.jsonl
    ar_events.jsonl
    alignment_only_events.jsonl
    retrieval_only_events.jsonl
    neither_events.jsonl
    prompt_pairs.jsonl
    roi_maps.jsonl

  c3_object_stress/
    pope_manifest.jsonl
    coco_object_annotations.jsonl
    present_object_manifest.jsonl
    absent_object_manifest.jsonl
    occlusion_manifest.jsonl
    sham_manifest.jsonl
    distractor_rois.jsonl
    roi_maps.jsonl

  c4_natural_failure/
    coco_native_manifest.jsonl
    generations.jsonl
    object_claims.jsonl
    hallucination_labels.jsonl
    unbiased_prevalence.json
    case_control_manifest.jsonl
    matching_diagnostics.json

  traces/
    reasoning_spans.jsonl
    demand_annotations.jsonl
    local_correctness.jsonl
    final_correctness.jsonl
    transition_annotations.jsonl
    future_causal_anchor_manifest.jsonl

  regions/
    ground_truth_rois.jsonl
    optional_semantic_regions.jsonl
    region_provenance.json

  audit/
    mechanical_validation.json
    deterministic_replay.json
    roi_audit.json
    manipulation_audit.json
    no_image_audit.json
    unrelated_image_audit.json
    split_integrity.json
    stimulus_duplicate_audit.json
    cohort_selection_blindness.json
    resource_summary.json

  summaries/
    stage6a_cohort_summary.md
    stage6a_acceptance.json
    next_analysis_recommendation.md
```

---

# 55. Required Cohort Summary Tables

At minimum report:

1. dataset availability/inventory;
2. downloaded vs reused assets;
3. per-dataset base counts;
4. C1 manipulation-validity counts;
5. C1 counterfactual/mask/sham coverage;
6. C2 2×2 cell counts;
7. C2 within-base pairing coverage;
8. C3 object present/absent counts;
9. C3 segmentation/bbox ROI quality;
10. C4 unbiased hallucination yield;
11. C4 matched case-control composition;
12. reasoning-span counts;
13. demand-transition counts;
14. first-use/reuse/refresh counts;
15. local-vs-final correctness matrix;
16. discovery/confirmation split composition;
17. template/stimulus duplication audit;
18. future causal-anchor counts.

No PCA or attention plot is required to accept the cohort.

---

# 56. Minimal Feasibility Diagnostics Allowed

Before freezing the full analysis stage, Stage 6A may compute only diagnostics that do not contaminate cohort selection.

Allowed after cohort membership is already frozen:

```text
native correctness distribution
hallucination yield
reasoning length
demand-transition frequency
mask success/failure from image semantics
counterfactual semantic validity by human/programmatic review
```

If passive attention is extracted for storage validation, it must not be used to drop/replace cohort members.

---

# 57. Stop Condition

After:

```text
dataset inventory/download
→ controlled cohort construction
→ native generation
→ stress image/prompt construction
→ semantic/ROI/readout review
→ reasoning-span segmentation
→ demand/transition annotation
→ natural hallucination labeling
→ discovery/confirmation freeze
→ duplicate/template audit
→ mechanical validation
→ final cohort acceptance
```

**STOP.**

Do not start:

```text
PCA trajectory analysis
exact causal trajectory scoring
mirage confirmation statistics
wandering/fixation causal classification
full Stage5B rescue
text↔visual representation substitution
sink intervention
```

Return the complete Stage 6A cohort summary for review.

---

# 58. Decision After Cohort Freeze

Recommend exactly one next analysis stage based on cohort yield.

## GO — Stage 6B Causal Retrieval-Dynamics Analysis

Use if:

```text
C1/C2/C3 gates pass
and
there are sufficient demand transitions + stress conditions
```

Primary future targets:

```text
demand-aligned switching
wandering
fixation
mirage
no-image/prior collapse
```

## GO — Natural Failure Extension

Use only if controlled cohorts pass but C4 hallucination yield is insufficient.

## GO — Cohort Repair

Use only if a specific semantic/ROI construction failed before internal-state analysis.

Do not choose the next step from observed attention patterns during Stage 6A.

---

# 59. Expected Stage 6B Paper Claims if the Cohort Works

The cohort is designed to make the following claims identifiable.

### Claim A — Demand-aligned dynamics

> **Successful multimodal reasoning changes causal visual state when reasoning demand changes, rather than simply minimizing visual-state movement.**

### Claim B — Wandering

> **Some reasoning failures repeatedly reassign visual support despite stable information demand.**

### Claim C — Fixation / staleness

> **Some failures preserve an outdated visual source after the reasoning demand has changed.**

### Claim D — Mirage

> **Visual-looking attention/routing can persist even after task-relevant evidential content has been removed, producing apparent grounding without causal semantic grounding.**

### Claim E — Hallucination heterogeneity

> **Hallucinations can arise from distinct dynamic failures, including prior-driven disconnection, wrong-source fixation, stale evidence, and downstream integration errors.**

These claims are the reason to build this cohort.

---

# 60. Final Research Principle

The analysis enabled by this cohort should not ask only:

```text
How much does the model look at the image?
```

It should ask:

\[
\boxed{
\text{Does the visual state change when the reasoning demand says it should?}
\]

and:

\[
\boxed{
\text{When visual-looking activity remains, is the underlying evidence still causally controlling the reasoning?}
\]

That distinction is the central design principle for Stage 6A.
