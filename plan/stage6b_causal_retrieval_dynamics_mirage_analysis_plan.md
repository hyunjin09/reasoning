# Stage 6B Plan — Causal Retrieval-Dynamics and Mirage Analysis
## Demand-Aligned Switching, Wandering, Fixation, and Apparent Grounding Without Evidence

## 0. Purpose

Stage 6A successfully built the controlled cohorts needed to stop treating visual attention and visual-state movement as unitary phenomena.

Frozen Stage 6A resources:

```text
C1 Controlled Diagram Grounding-Stress
- 109 retained bases
- MathVerse 34 / MathVision 31 / MathVista 44
- 109 counterfactual assets
- 109 full-mask assets
- mild/strong degradation + matched shams
- unrelated-image and no-image controls
- 1,385 SOURCE_TO_SOURCE demand transitions
- 3,683 matched no-transition candidates
- 377 refresh anchors
- 97 reviewed wrong-claim anchors

C2 Alignment × Retrieval-Demand Factorial
- 31 same-image families
- 4/4 cells complete for every family
- AR / A_only / R_only / Neither
- 31 natural EOS traces per cell

C3 Object Hallucination / Occlusion Stress
- 136 families
- 63 present-object
- 73 absent-object
- 63 polygon/RLE target-object families with full-mask variants
- intact yes 61/63
- strong yes 50/63
- mask yes 41/63
- matched sham behavior largely preserved

C4 Natural COCO Validation
- 1,000 unbiased native generations
- 10 confirmed conservative COCO80 object hallucinations
- 50 unresolved
- natural matched atlas too small for a primary confirmation claim
```

Stage 6A therefore passed the controlled-cohort goal but not the planned natural-failure atlas size.

Stage 6B should **not delay the controlled causal analysis merely to collect more natural hallucinations**.

The central question is now:

> **When reasoning demand changes, does the causal visual state change when it should — and when apparent visual engagement persists, is the evidence still causally controlling the computation?**

This stage tests two linked paper-level insights:

\[
\boxed{\text{successful visual-state movement is demand-aligned, not merely small}}
\]

and

\[
\boxed{\text{apparent visual engagement can outlive causal evidential grounding}}
\]

---

# 1. Why This Experiment Is Necessary for the Paper

The current core result is:

> **Thinking MLLMs perform reasoning-conditioned dynamic visual retrieval.**

Stage 4A established:

```text
reasoning demand: A → B → A
causal visual dependence: A → B → A
```

This immediately creates a limitation for generic trajectory analyses such as:

```text
correct = stable
wrong = wandering
```

because successful reasoning itself can require large source changes.

The more mechanistic hypothesis is:

> **The important variable is whether visual-state change is synchronized with reasoning demand.**

Separately, Stage 5A could not obtain a strict alignment-only/mirage confirmation cohort naturally.

Stage 6A now supplies controlled conditions in which:

```text
semantic alignment
reasoning demand
evidence availability
```

are deliberately dissociated.

Stage 6B can therefore test a second question that attention-only studies cannot answer:

> **Can the model continue to look visually grounded after the evidence that should ground the reasoning has been removed?**

---

# 2. Paper Claims This Stage Is Designed to Identify

## Claim A — Demand-Aligned Retrieval Dynamics

Positive result:

> **Successful multimodal reasoning is characterized by visual-source changes that are aligned with changes in reasoning demand.**

This is stronger than:

```text
successful trajectories move less
```

## Claim B — Wandering Failure

Positive result:

> **Some reasoning failures reassign causal visual support even when the demanded evidence has not changed.**

Operational shorthand:

```text
switch without demand
```

## Claim C — Fixation / Staleness Failure

Positive result:

> **Some failures preserve an outdated visual source after reasoning demand has switched.**

Operational shorthand:

```text
demand changes without source refresh
```

## Claim D — Causal Mirage

Positive result:

> **As visual evidence is degraded or removed, causal semantic grounding can collapse before apparent visual engagement disappears.**

## Claim E — Alignment Is Not Retrieval

Positive result:

> **Semantic/lexical alignment can recruit visual routing without making the aligned source behaviorally necessary for the current inference.**

Together these support the broader conceptual claim:

\[
\boxed{\text{visual attention/state must be interpreted relative to both reasoning demand and causal evidence}}
\]

---

# 3. What Null Results Do NOT Rule Out

## 3.1 No controlled mirage

Does not establish:

```text
high attention always means causal grounding
```

Possible alternatives:

```text
mask is too salient
model abandons the visual route immediately
the selected tasks are unusually evidence-sensitive
apparent engagement is expressed in a feature not measured here
```

## 3.2 No wandering

Does not establish:

```text
reasoning failure is never a retrieval-dynamics failure
```

Possible alternatives:

```text
failures are mostly integration errors
demand annotation is too coarse
source identity is redundant
failure occurs outside reviewed source spans
```

## 3.3 No fixation

Does not establish:

```text
stale evidence never occurs
```

Possible alternatives:

```text
few source transitions have sufficient local readouts
visual refresh occurs through broader state than the local assay
the model falls back to language priors rather than an old ROI
```

## 3.4 C2 weak alignment effect

Does not establish:

```text
text–visual semantic alignment does not exist
```

Possible alternatives:

```text
prompt variants did not induce strong local alignment
alignment occurs at a different layer/head scope
alignment is distributed across multiple visual text regions
```

---

# 4. Scope and Boundaries

Stage 6B runs:

```text
controlled causal source scoring
controlled fixed-prefix stress analysis
native-condition passive trajectory extraction
exact causal demand-transition anchors
alignment × retrieval factorial analysis
mirage discovery + held-out confirmation
wandering/fixation causal classification
PCA/trajectory visualization after causal labels freeze
C3 object-stress replication
small exploratory C4 natural validation
```

Stage 6B does **not** run:

```text
mechanism-guided rescue
new training
new head/layer discovery search
text↔visual representation substitution
sink intervention
large natural-failure extension
```

---

# 5. Canonical Execution

All new exact scoring uses the frozen A6000 protocol:

```text
Qwen3-VL-4B-Thinking
A6000
BF16
fixed repaired cached/streaming path
2048-token generated chunk maximum
fixed allocator-cache release
same model/tokenizer revision
same GQA/RoPE semantics
```

Within a scientific contrast, all arms must use the same execution shape/path.

Do not pool absolute BF16 scores from different execution shapes.

---

# 6. Frozen Stage 6A Splits

Respect the existing discovery/confirmation assignment.

```text
C1: discovery 47 / confirmation 62
C2: discovery 12 / confirmation 19
C3: discovery 46 / confirmation 90
C4: discovery 326 / confirmation 674
```

The split may not be changed based on Stage 6B effects.

Where a subset is required inside a split:

```text
use semantic/mechanical eligibility only
then first eligible frozen order
```

Do not sample by attention, VSD, correctness, or PCA position unless the analysis is explicitly a correctness case-control comparison.

---

# 7. Analysis Architecture

Stage 6B has six primary phases.

```text
Phase A — C2 Alignment × Retrieval-Demand Causal Dissociation
Phase B — C1 Grounding-Collapse / Mirage Stress Analysis
Phase C — C1 Demand-Aligned Dynamics vs Wandering / Fixation
Phase D — Trajectory-State Geometry and PCA
Phase E — C3 Object Occlusion / Hallucination Replication
Phase F — C4 Small Natural Validation
```

A final synthesis phase selects one next intervention/mechanism stage.

---

# PHASE A — ALIGNMENT × RETRIEVAL-DEMAND CAUSAL DISSOCIATION

# 8. Scientific Question

C2 contains 31 same-image families with four prompt conditions:

```text
AR       = aligned + retrieval-needed
A_only   = aligned + retrieval-not-needed
R_only   = weak/no local lexical alignment + retrieval-needed
Neither  = weak/no alignment + retrieval-not-needed
```

The question is:

> **Does semantic alignment primarily change apparent routing, while retrieval demand changes causal dependence?**

---

# 9. C2 Source Roles

For each family freeze:

```text
A = visually/textually aligned source
T = task-required source
X = alternative source if distinct
I = irrelevant ROI if validated
```

Depending on the cell:

```text
AR:      A = T
A_only:  A != T
R_only:  T exists; exact A cue absent/weak
Neither: no designated aligned-needed overlap
```

Do not redefine A/T after observing attention.

---

# 10. C2 Exact Causal Assay

Use the Stage 4A-compatible local source assay.

Primary:

```text
W2 = [t-1, t]
all 36 layers
all 32 heads
selected ROI contribution → 0
no attention renormalization
```

Sensitivity:

```text
W8 = [t-7, ..., t]
```

for the task-required source T.

Where A != T, score both:

```text
Suppress A
Suppress T
```

Where validated, score:

```text
Suppress I
```

---

# 11. C2 Local Readout

Freeze the same semantic answer/readout family across the four prompts whenever mechanically possible.

Primary quantity:

\[
VSD_R = D_{\text{native}} - D_{\text{suppress }R}
\]

where `D` is the correct-vs-foil local candidate preference.

Also record raw candidate log-probabilities.

Do not infer "wrong-source error promotion" solely from a signed correct-vs-wrong margin.

---

# 12. C2 Passive Routing Features

At the frozen local event extract:

```text
ROI attention mass/density
matched attention percentile
QK cosine
scaled QK logit
alphaV norm
post-W_O contribution norm
visual attention share
sink mass
entropy
```

Use:

```text
layers 28–29 all heads
```

plus historical selected-head summaries as descriptive secondary coordinates.

---

# 13. C2 Primary Factorial Contrasts

## 13.1 Alignment effect on apparent engagement

Compare within family:

```text
(AR + A_only)/2
vs
(R_only + Neither)/2
```

for aligned-source attention/QK features.

## 13.2 Retrieval-demand effect on causal grounding

Compare:

```text
(AR + R_only)/2
vs
(A_only + Neither)/2
```

for demanded-source VSD.

## 13.3 Dissociation contrast

Primary conceptual target:

```text
Alignment increases apparent engagement
without a commensurate increase in aligned-source causal necessity.
```

Operationally report the interaction between:

```text
feature family: apparent engagement vs causal grounding
factor: alignment vs retrieval demand
```

Do not force a single scalar "dissociation score" as the only result.

---

# 14. C2 High-Attention Matched Confirmation

Use discovery C2 only to freeze:

```text
high-attention criterion
matching tolerances
```

Then apply to the 19 confirmation families.

Primary matched comparison:

```text
high-attention A_only
vs
high-attention AR or R_only retrieval event
```

Match where possible on:

```text
ROI size
reasoning progress
attention density
answer length
```

If too few pairs exist:

```text
report insufficient
```

Do not weaken the criterion post hoc.

---

# 15. C2 Positive Claim Gate

Strong support for:

```text
Alignment != Retrieval
```

requires:

1. retrieval-needed cells have robustly larger demanded-source VSD than retrieval-not-needed cells;
2. alignment affects at least one apparent-routing feature in the expected direction;
3. the causal difference survives W8 sensitivity;
4. confirmation-family direction is consistent;
5. high-attention matched analysis, if sufficiently powered, shows unequal causal grounding despite similar attention.

Condition 5 is strengthening evidence, not required if yield is insufficient.

---

# PHASE B — C1 GROUNDING-COLLAPSE / MIRAGE STRESS

# 16. Scientific Question

The key question is:

> **As actual target evidence is weakened, does causal grounding disappear before the model stops visually engaging with the source?**

C1 provides within-base conditions:

```text
intact
counterfactual
mild
strong
mask
matched shams
unrelated image
no image
```

---

# 17. Two Complementary C1 Analyses

Run both.

## B1 — Fixed-Prefix Controlled Stress

Purpose:

```text
isolate image evidence availability
while holding textual reasoning state fixed
```

Use a frozen intact-trajectory prefix immediately before the independently annotated local target readout.

Replay that same text prefix under:

```text
intact
mild
strong
mask
matched sham_mild
matched sham_strong
matched sham_mask
counterfactual
counterfactual_render_sham
unrelated
no_image
```

Where no-image cannot legally reuse an image-containing token layout, use the validated no-image interface and compare output distributions, not KV identity.

## B2 — Native-Condition Trajectory Analysis

Purpose:

```text
observe how the model naturally adapts its reasoning trajectory to evidence degradation
```

Use each condition's own Stage 6A native trace.

Do not mix B1 and B2 as if they answered the same question.

---

# 18. C1 Fixed-Prefix Readout

For each base define:

```text
x  = intact target semantic value
x' = counterfactual target value
```

Primary semantic margin:

\[
D_x = \log p(x) - \log p(x')
\]

using candidate-token normalization consistent with prior stages.

For counterfactual image condition also compute the reversed semantic margin.

Store:

```text
P(x)
P(x')
entropy
top-k distribution
```

for all stress conditions.

---

# 19. C1 Exact Target VSD Across Evidence Levels

For:

```text
intact
mild
strong
mask
sham_mild
sham_strong
sham_mask
```

compute target ROI W2 source dependence.

Primary:

\[
VSD_T(c) = D_c^{native} - D_c^{T-suppressed}
\]

for condition `c`.

W8 sensitivity on:

```text
intact
strong
mask
```

for the confirmation cohort.

No-image has no visual VSD.

Unrelated-image source suppression is descriptive only unless a semantically matched source ROI exists.

---

# 20. C1 Counterfactual Source-Semantic Validation

Use:

```text
intact vs counterfactual
```

to confirm that the target source actually carries the intended semantics.

Primary counterfactual followability:

\[
CF = D_x(\text{intact}) - D_x(\text{counterfactual})
\]

plus direction-specific reporting.

Compare with:

```text
counterfactual_render_sham
```

Strong positive CF is a prerequisite for calling a base a strict semantic-grounding/mirage confirmation base.

---

# 21. Apparent Visual Engagement

At the same fixed-prefix query, record:

```text
target ROI attention density
target visual-attention share
target QK cosine
target scaled QK logit
target alphaV
target post-W_O contribution
sink mass
```

These are **phenotypes**, not causal labels.

---

# 22. Grounding-Collapse Curve

For each evidence level:

```text
intact
mild
strong
mask
```

estimate:

```text
causal grounding:
- VSD_T
- semantic candidate margin
- counterfactual-validated source status

apparent engagement:
- attention density
- QK
- alphaV
```

Primary statistical question:

> **Does causal grounding decline more strongly/earlier than apparent visual engagement as evidence is degraded?**

Use within-base sham-controlled differences.

Do not rely only on a binary mirage threshold.

---

# 23. Sham-Controlled Degradation Effect

For degradation level `k`:

\[
\Delta^{target}_k = M_k - M_{intact}
\]

\[
\Delta^{sham}_k = M_{sham,k} - M_{intact}
\]

and:

\[
DiD_k = \Delta^{target}_k - \Delta^{sham}_k
\]

where `M` is separately:

```text
VSD
candidate margin
attention
QK
alphaV
```

This separates target-evidence degradation from generic visual corruption.

---

# 24. No-Image / Unrelated Similarity

For each base compare output distributions under:

```text
mask
strong
unrelated
no_image
```

using:

```text
JS divergence
top-k overlap
candidate-margin distance
```

Primary interpretive use:

```text
Does degraded-image behavior move toward the no-image prior?
```

No-image similarity is supporting evidence.

It is not by itself proof that the image has zero causal influence.

---

# 25. Mirage Discovery Rule

Use **C1 discovery bases only** to freeze a strict mirage rule.

The rule must require all three families:

## A. Apparent engagement remains substantial

Example feature family:

```text
attention/QK/alphaV retention
```

## B. Causal grounding collapses

Example:

```text
VSD_T reduction
semantic-margin collapse
```

## C. Evidence removal is mechanically verified

```text
strong/mask target manipulation
with matched sham
```

A candidate rule may use normalized within-base retention, but thresholds must be chosen/frozen on discovery only.

Do not use correctness to define mirage.

---

# 26. Mirage Confirmation

Apply the frozen rule unchanged to C1 confirmation bases.

Report:

```text
strict mirage count
base fraction
condition of first mirage transition
correct vs incorrect local output
no-image similarity
```

Separate:

```text
benign mirage
hallucinatory/error-associated mirage
```

based on local semantic correctness after the causal label is assigned.

---

# 27. Strong Mirage Claim Gate

Strong support for:

```text
apparent grounding without causal grounding
```

requires:

1. target degradation reduces VSD/semantic grounding beyond matched sham;
2. at least one apparent-routing feature remains substantially preserved;
3. the divergence replicates in the held-out confirmation split;
4. intact/counterfactual conditions verify that the original source is semantically meaningful;
5. the effect is not explained only by complete image removal.

A strict mirage count is secondary to the continuous grounding-vs-engagement divergence.

---

# PHASE C — DEMAND-ALIGNED DYNAMICS VS WANDERING / FIXATION

# 28. Scientific Question

The trajectory question is not:

```text
How much does the visual state move?
```

It is:

> **Does the causal visual state change when reasoning demand changes, and remain stable when demand does not change?**

---

# 29. Dynamic Panel Eligibility

Use C1 semantic annotations only.

A base enters the exact causal dynamic panel if it has:

```text
>= 2 independently localized source ROIs
>= 1 reviewed source-to-source demand transition
valid pre/post span boundaries
valid causal readout at or immediately after both sides of the transition
```

Where possible also require:

```text
>= 1 matched reviewed no-change interval
```

Selection is blind to attention and causal effect.

---

# 30. Transition Sampling Rule

Within each eligible base:

```text
retain the first up to 2 source-to-source transitions
retain the first up to 2 matched no-change intervals
retain the first refresh event if available
```

This avoids overweighting long traces with many annotations.

Match no-change intervals on:

```text
reasoning progress
source identity
span length
```

where feasible.

---

# 31. Dynamic Panel Gate

Target:

```text
>= 64 bases
>= 96 source-transition pairs
>= 96 matched no-change pairs
>= 32 refresh events
```

Minimum for confirmatory inference:

```text
>= 48 bases
>= 64 transition pairs
>= 64 no-change pairs
```

If the gate fails:

```text
run descriptive exact anchors only
do not claim cohort-level wandering/fixation rates
```

---

# 32. Exact Causal Source State

At every selected pre/post anchor score:

```text
current demanded source T
previous demanded source P
one semantically plausible alternative X where available
irrelevant control I where available
```

Primary local assay:

```text
W2 all-layer/all-head source suppression
```

W8 sensitivity for demanded/previous source on a frozen subset.

Define:

\[
C_s(R)=VSD_R(s)
\]

for source `R` at semantic state `s`.

---

# 33. Causal Dominant Source

A source is considered causally active only if:

```text
VSD_R > frozen minimum effect floor
```

and dominance over the runner-up exceeds a frozen margin.

Use discovery data to freeze the dominance margin.

Recommended initial effect floor inherited from prior work:

```text
0.05 nats / candidate token
```

If readout scale differs, justify and freeze an adjusted floor before confirmation scoring.

Allow:

```text
MIXED
NONE
UNRESOLVED
```

Do not force one source to win.

---

# 34. Demand–Visual Coupling

For a single-source demand state:

\[
Coupled_s =
1[
\text{causal dominant source}
=
\text{demanded source}
]
\]

Also report a continuous demanded-source margin:

\[
DCM_s =
VSD_{demanded}
-
\max_{R\neq demanded} VSD_R
\]

Primary trajectory-level quantity:

```text
mean DCM / coupling rate
```

over reviewed causal anchors.

---

# 35. Demand-Aligned Switch

At a reviewed transition:

```text
demand P → T
```

a clean demand-aligned switch requires:

```text
pre:  P causally dominant
post: T causally dominant
```

with positive source margins.

This is the Stage 4A principle generalized beyond A→B→A.

---

# 36. Wandering

A strict wandering transition candidate is:

```text
semantic demand is unchanged
but
causal dominant visual source changes
```

Requirements:

1. same demanded source before/after;
2. both causal states are substantial;
3. dominant source identity changes;
4. new source is not semantically required by a newly introduced subgoal;
5. annotation is not UNRESOLVED.

Report separately:

```text
benign wandering
error-associated wandering
```

depending on downstream local correctness.

---

# 37. Fixation / Staleness

A strict fixation candidate is:

```text
demand source changes P → T
but
causal state remains P-dominant
```

or:

```text
new demanded T fails to gain causal dominance within the frozen transition window
while P remains substantial
```

A weaker:

```text
NO_SWITCH / unresolved
```

category should be kept separate from strict stale-source fixation.

---

# 38. Refresh

At:

```text
A → B → A
```

or any previously used source becoming demanded again, measure:

```text
does the returning source regain causal dominance?
```

Report:

```text
successful refresh
delayed refresh
failed refresh/stale prior source
mixed support
```

Do not assume every reuse is a refresh.

---

# 39. Transition Latency

For transitions with enough annotated adjacent spans, score up to:

```text
2 spans before
transition span
2 spans after
```

where causal readouts are valid.

Define:

```text
latency = first post-demand-change anchor
where new demanded source becomes causally dominant
```

Right-censor if no switch occurs within the window.

This distinguishes:

```text
immediate refresh
delayed refresh
persistent fixation
```

---

# 40. Correctness Association

Do not define dynamic states by correctness.

After dynamic labels freeze, compare:

```text
demand-aligned
wandering
fixation/stale
mixed
none/unresolved
```

against:

```text
local claim correctness
downstream reasoning correctness
final correctness
```

Primary claim should be:

```text
mechanism/state difference
```

not merely a predictive correlation with final answer.

---

# 41. Error-Promoting Source Readout

For any event interpreted as failure-causing, do **not** rely only on a correct-vs-wrong candidate margin.

Also compute error-oriented quantities where an explicit wrong token/claim exists:

\[
\Delta \log p(w_{wrong})
\]

and:

\[
\Delta[
\log p(w_{wrong})
-
\log p(w_{correct})
]
\]

under source suppression.

A source may be called:

```text
error-promoting
```

only if removal reduces wrong-token/claim preference in the predicted direction.

This guards against the Stage 5A H-MR readout-orientation problem.

---

# PHASE D — TRAJECTORY STATE GEOMETRY / PCA

# 42. Role of PCA

PCA is **descriptive visualization after semantic and causal labels freeze**.

It must not define:

```text
retrieval
wandering
fixation
mirage
hallucination
```

The key scientific comparison remains demand–causal coupling.

---

# 43. Passive Dense State Vector

At every semantically reviewed native span endpoint, construct:

\[
z^{passive}_s
\]

from predeclared features:

```text
source-specific attention density
source-specific visual attention share
source-specific QK cosine/logit
source-specific alphaV
source-specific post-W_O norm
sink mass
entropy
candidate margin where available
late residual norms
```

Use fixed feature normalization fitted on discovery only.

---

# 44. Causal Anchor State Vector

At exact causal anchors construct:

\[
z^{causal}_s
\]

from:

```text
VSD demanded source
VSD previous source
VSD alternative source
VSD irrelevant source
demanded-source causal margin
counterfactual semantic effect where available
```

Do not impute causal source identity for unscored spans.

---

# 45. PCA Fit Rule

Fit PCA only on discovery split.

Two optional visualizations:

```text
PCA-passive
PCA-causal-anchor
```

Confirmation data are projection-only.

Report:

```text
explained variance
feature loadings
dataset/condition composition
```

No PCA hyperparameter may be tuned on confirmation separation.

---

# 46. Trajectory Metrics

Compute in both:

```text
original normalized feature space
PCA projection
```

where valid.

## Path length

\[
L=\sum_s ||z_{s+1}-z_s||_2
\]

## Tortuosity

\[
\tau=
\frac{\sum_s ||z_{s+1}-z_s||_2}
{||z_{S}-z_1||_2+\epsilon}
\]

## Demand coupling

Primary mechanistic metric.

## Unnecessary switching

\[
U=
\#\{d_s=d_{s+1}, v_s\neq v_{s+1}\}
\]

## Failed switching

\[
F=
\#\{d_s\neq d_{s+1}, v_s=v_{s+1}\}
\]

## Transition latency

As defined above.

---

# 47. vSTREAM-Inspired Comparison

Replicate the descriptive question:

```text
successful vs unsuccessful path length/tortuosity
```

but treat it as secondary.

Then test the stronger hypothesis:

> **Once demand transitions are accounted for, demand–visual coupling explains failure state more directly than path length alone.**

Useful comparisons:

```text
correct high-movement but demand-aligned
wrong high-movement wandering
wrong low-movement fixation
correct low-movement stable
```

This directly prevents:

```text
movement = failure
```

from becoming the paper conclusion.

---

# 48. Optional Causal Surrogate

Do not use unless exact-anchor coverage is insufficient for useful trajectory visualization.

If used:

1. train on discovery exact causal anchors only;
2. include correct, incorrect, stress, and intact conditions;
3. validate separately on confirmation:
   - intact retrieval
   - degradation/mask
   - correct
   - wrong
   - transition
   - no-transition;
4. require strong exact-effect prediction before use;
5. never use surrogate output as the sole causal label;
6. paper causal claims remain based on exact anchors.

If the surrogate fails any major state stratum:

```text
drop it
```

rather than tuning until it works.

---

# PHASE E — C3 OBJECT OCCLUSION / HALLUCINATION REPLICATION

# 49. Purpose

C3 provides a real-image object-level stress test for the controlled mirage/fixation story.

It is secondary to C1 because:

```text
masking may preserve silhouette/context/boundary evidence
```

and object presence can be spatially redundant.

---

# 50. C3 Present-Object Analysis

Use all 63 present-object families.

Compare:

```text
intact
strong
mask
sham
sham_strong
unrelated
no_image
```

Primary behavioral readouts:

```text
yes/no logit margin
final yes/no answer
entropy
```

Primary source readout:

```text
target-object ROI W2 source dependence
```

where the ROI/token map remains valid.

---

# 51. C3 Object Stress Interpretation

Do not call:

```text
mask + yes
```

a hallucination automatically.

Classify later as one of:

```text
residual evidence-supported
apparent-engagement / weak-causal-grounding candidate
prior-like
unresolved
```

using:

```text
target ROI VSD
attention/QK/alphaV
sham controls
unrelated/no-image behavior
```

---

# 52. C3 Absent-Object Analysis

For 73 natural-negative families:

```text
no true target ROI exists
```

Therefore do not fabricate one.

Analyze:

```text
semantically related present distractor ROIs
global visual engagement
unrelated/no-image baselines
```

Where an incorrect yes occurs, test whether a present distractor source is error-promoting using the explicit error-oriented readout.

---

# 53. C3 Replication Claim Gate

C3 may strengthen the mirage story if:

1. target evidence degradation reduces object-source VSD;
2. visual engagement to the target/masked region persists in a subset;
3. this is not reproduced by matched sham;
4. behavior remains different from unrelated/no-image in a way consistent with residual visual engagement.

C3 alone is insufficient to establish complete evidence removal.

---

# PHASE F — C4 SMALL NATURAL VALIDATION

# 54. Scope

Do not extend C4 yet.

Use the frozen:

```text
10 confirmed hallucination cases
10 matched controls
```

plus the predeclared wrong-claim anchors only for exploratory validation.

No prevalence claim beyond the Stage 6A frozen census.

---

# 55. C4 Question

Ask only:

> **Do the controlled-state signatures discovered in C1/C3 show the same directional tendency in naturally hallucinating traces?**

Potential signatures:

```text
low demand–visual coupling
high unnecessary switching
fixation
high apparent engagement / low source grounding
high no-image-like behavior where comparable
```

Because N is small:

```text
report effect sizes and individual cases
avoid confirmatory p-value headline
```

If controlled signatures are strong and C4 trends match but N remains insufficient, a targeted Natural Failure Extension may become the next stage.

---

# 56. Sink Is Passive Only

Across all phases save:

```text
sink mass
sink release
target-gain vs sink-loss
```

Analyze whether sink behavior differs across:

```text
retrieval
alignment-only
mirage
wandering
fixation
```

Do not intervene on sink.

Sink causality should be recommended later only if:

1. differences reproduce in confirmation;
2. they remain after controlling for generic attention magnitude;
3. a causal behavioral prediction becomes clear.

---

# 57. Statistical Unit

Primary independent unit:

```text
base/family
```

Repeated conditions/events are nested.

Use:

```text
paired within-base contrasts
base bootstrap
cluster-aware confidence intervals
```

Do not treat spans as independent samples.

---

# 58. Statistical Families

Keep separate confirmatory families.

## Family 1 — C2 Alignment vs Retrieval

```text
alignment effect on attention/QK
retrieval effect on VSD
AR vs A_only causal contrast
R_only vs Neither causal contrast
```

## Family 2 — C1 Grounding Collapse

```text
intact→mild
intact→strong
intact→mask
target-vs-sham DiD
engagement-vs-grounding slope difference
```

## Family 3 — Mirage Confirmation

Frozen strict rule on confirmation only.

## Family 4 — Dynamic Coupling

```text
transition demand-alignment
no-change unnecessary switching
refresh success
fixation
```

## Family 5 — C3 Replication

Secondary.

Use:

```text
paired Wilcoxon where appropriate
Holm correction within family
10,000 base-bootstrap resamples
```

Report raw and corrected values.

---

# 59. Robustness Rule

For a planned directional contrast to be called robust, require:

```text
expected-direction median
bootstrap 95% mean CI excluding zero
>= 75% expected-direction bases where binary direction is meaningful
Holm-corrected p < .05
```

If one component is structurally inapplicable, predeclare the alternative before confirmation scoring.

Do not alter the rule after seeing confirmation results.

---

# 60. Dataset / Template Robustness

For C1 report separately:

```text
MathVerse
MathVision
MathVista
```

and pooled.

Also report:

```text
leave-one-dataset-out
leave-one-template-family-out where possible
```

A pooled effect driven entirely by one dataset cannot support a broad domain-general claim.

---

# 61. Correctness Stratification

After causal state labels freeze, report major results for:

```text
locally correct
locally incorrect
final correct
final incorrect
```

This is critical because:

```text
correct retrieval can precede downstream reasoning failure
```

as Stage 5A already showed.

---

# 62. Failure-State Hierarchy

Use a hierarchy that prevents overclaiming.

## Tier 1 — Causal dynamic failure

Requires:

```text
semantic demand state
+
source-specific causal scores
+
mechanically valid controls
```

Examples:

```text
strict wandering
strict fixation
strict mirage
```

## Tier 2 — Causal source anomaly

Source dependence is abnormal but the failure linkage is not fully established.

## Tier 3 — Passive candidate

Attention/QK/trajectory looks unusual without sufficient exact causal anchor.

Paper-level mechanism claims should use Tier 1 primarily.

---

# 63. Mechanism-Guided Rescue Gate

At the end of Stage 6B, identify whether one failure class is suitable for intervention.

A class is rescue-ready only if:

1. at least 24 fresh Tier-1/strong Tier-2 confirmation events exist;
2. the causal direction is coherent;
3. the error readout is correctly oriented;
4. there is a specific intervention predicted to improve the local readout;
5. matched non-failure controls predict little or opposite effect.

Possible mappings:

```text
Fixation / stale source
→ suppress stale carrier/source + demand-triggered refresh

Wandering
→ stabilize currently demanded source / suppress unnecessary switch

Alignment interference
→ suppress aligned-but-nondemanded contribution

Mirage
→ evidence-sufficiency gating or demand-triggered re-retrieval
```

Do not run the rescue in Stage 6B.

---

# 64. What Would Make Stage 6B Insightful?

The strongest outcome is **not**:

```text
wrong trajectories have longer PCA paths
```

It is:

> **Large visual-state changes can be correct when demand changes, while small changes can be pathological when the model should have refreshed.**

And:

> **As evidence is degraded, causal semantic grounding can collapse while visual routing remains apparently active.**

Together:

\[
\boxed{\text{visual-state magnitude and movement are meaningful only relative to reasoning demand and causal evidence}}
\]

This is the conceptual target.

---

# 65. What Would Not Be Enough

Do not headline:

```text
correct vs wrong PCA separation
```

alone.

Do not call:

```text
high attention = retrieval
```

Do not call:

```text
mask + persistent answer = hallucination
```

Do not call:

```text
source dominance in a correct-vs-wrong margin = error-promoting source
```

without the error-oriented readout.

Do not claim:

```text
no-image similarity = zero visual use
```

without causal source evidence.

---

# 66. Required Figures

At minimum:

1. C2 2×2 alignment × retrieval design;
2. C2 attention/QK by factorial cell;
3. C2 demanded/aligned ROI VSD by cell;
4. same-attention alignment-only vs retrieval examples;
5. C1 evidence-degradation ladder;
6. C1 causal grounding vs evidence level;
7. C1 apparent engagement vs evidence level;
8. target-vs-sham degradation DiD;
9. continuous engagement-grounding divergence;
10. strict mirage confirmation examples;
11. no-image/unrelated distribution similarity;
12. counterfactual followability;
13. causal source state at demand transitions;
14. demand-aligned switch examples;
15. wandering examples;
16. fixation/stale examples;
17. refresh/transition-latency plot;
18. correctness by causal dynamic state;
19. passive PCA discovery + confirmation projection;
20. path length/tortuosity vs demand coupling;
21. C3 object occlusion response/VSD curves;
22. C3 residual-evidence vs mirage-like examples;
23. exploratory C4 natural cases;
24. final conceptual figure:

```text
                   reasoning demand
                         ↓
          ┌──────────────┴──────────────┐
          │                             │
     demand changes                demand stable
          │                             │
visual source changes            source stays stable
     = healthy switch              = healthy hold

Failure modes:
demand changes + source stays old     → fixation/staleness
demand stable + source changes        → wandering
visual engagement persists
after grounding collapses             → mirage
```

---

# 67. Output Structure

```text
outputs/stage6b/
  config/
    stage6b_config.json
    causal_windows.json
    c2_factorial_rules.json
    c1_stress_rules.json
    mirage_discovery_rule.json
    dynamic_state_rules.json
    dominance_thresholds.json
    statistical_families.json

  audit/
    canonical_path_audit.json
    fixed_prefix_replay_audit.json
    roi_source_audit.json
    stress_condition_audit.json
    no_image_interface_audit.json
    causal_score_replay.json
    split_integrity.json
    readout_orientation_audit.json
    resource_summary.json

  c2_alignment_retrieval/
    source_roles.jsonl
    w2_scores.jsonl
    w8_scores.jsonl
    passive_features.jsonl
    factorial_statistics.json
    matched_high_attention.json
    claim_assessment.json

  c1_mirage/
    fixed_prefix_manifest.jsonl
    fixed_prefix_scores.jsonl
    native_condition_features.jsonl
    target_vsd_by_condition.jsonl
    sham_did.json
    counterfactual_followability.json
    no_image_similarity.json
    mirage_discovery.json
    mirage_confirmation.json
    claim_assessment.json

  c1_dynamics/
    dynamic_panel_manifest.jsonl
    transition_pairs.jsonl
    no_change_pairs.jsonl
    refresh_events.jsonl
    exact_source_scores.jsonl
    demand_coupling.json
    wandering_fixation_classes.jsonl
    transition_latency.json
    correctness_association.json
    error_readout_diagnostics.json

  trajectory/
    passive_state_vectors.jsonl
    causal_anchor_vectors.jsonl
    normalization.json
    pca_discovery.json
    pca_confirmation_projection.jsonl
    trajectory_metrics.jsonl
    vstream_style_comparison.json
    demand_aligned_comparison.json

  c3_object_stress/
    present_object_scores.jsonl
    absent_object_scores.jsonl
    target_vsd.jsonl
    passive_features.jsonl
    prior_similarity.json
    replication_assessment.json

  c4_natural_validation/
    frozen_cases.jsonl
    controlled_signature_projection.jsonl
    exploratory_effects.json
    individual_cases.md

  sink/
    state_sink_features.jsonl
    sink_descriptive_statistics.json
    future_sink_gate.json

  analysis/
    paper_claim_assessment.json
    dataset_robustness.json
    template_robustness.json
    correctness_stratification.json
    rescue_readiness.json
    figures/

  summaries/
    stage6b_summary.md
    stage6b_acceptance.json
    next_stage_recommendation.md
```

---

# 68. Technical Acceptance Criteria

Stage 6B technically passes if:

1. all new exact scoring uses the canonical A6000 path;
2. Stage 6A discovery/confirmation splits remain unchanged;
3. C2 source roles are frozen before causal/passive scoring;
4. all 31 C2 families are retained unless a mechanical/readout failure is documented;
5. C1 fixed-prefix stress uses the same textual prefix across image conditions where interface-valid;
6. target/sham degradation arms are mechanically isolated;
7. counterfactual source semantics are validated independently of attention;
8. W2 is the primary source assay;
9. W8 is a predeclared sensitivity assay;
10. mirage rule is frozen on discovery and applied unchanged to confirmation;
11. dynamic panel selection uses semantic annotations only;
12. transition/no-change sampling is frozen before causal scoring;
13. wandering/fixation labels use causal source state, not PCA;
14. error-promoting claims use error-oriented readouts;
15. PCA is fit on discovery only;
16. confirmation is projection-only;
17. key trajectory metrics are also reported outside PCA space;
18. C3 mask+yes is never automatically labeled hallucination;
19. C4 remains exploratory at current sample size;
20. no rescue, representation substitution, or sink intervention is started;
21. exactly one next-stage recommendation is produced.

Technical PASS does not require mirage, wandering, or fixation to be common.

---

# 69. Scientific Outcome Map

## O1 — Alignment/Retrieval Dissociation

If C2 shows routing alignment without corresponding causal necessity:

```text
semantic alignment != task-conditioned retrieval
```

at a new dedicated factorial scale.

## O2 — Grounding-to-Mirage Transition

If C1 shows:

```text
causal grounding ↓ sharply
apparent engagement remains
```

under target-specific evidence degradation beyond sham:

> **apparent visual grounding outlives evidential grounding.**

## O3 — Demand-Aligned Dynamic Retrieval

If source changes match demand changes and stable demand predicts source stability:

> **healthy visual-state movement is demand-aligned.**

## O4 — Wandering

If stable demand exhibits unnecessary causal source switching enriched in local errors:

> **some failures wander across visual sources without an information-demand change.**

## O5 — Fixation / Staleness

If changed demand fails to recruit the new source while the old source remains causal:

> **some failures persist on stale visual evidence.**

## O6 — Path-Length Reinterpretation

If path length/tortuosity alone mixes healthy switching and failure, while demand coupling separates them:

> **visual-state movement is not intrinsically pathological; demand misalignment is the more mechanistic variable.**

## O7 — C3 Replication

If object occlusion reproduces the C1 engagement/grounding divergence:

> controlled mirage-like behavior extends beyond diagrams.

## O8 — Natural Trend Only

If C4 is directionally compatible but underpowered:

> report ecological consistency only and decide whether targeted natural extension is worth the compute.

---

# 70. Next-Stage Decision

Produce exactly one recommendation.

## GO — Mechanism-Guided Failure Rescue

Preferred if:

```text
>= 24 coherent fresh failure events
+
clear causal direction
+
mechanism-matched intervention prediction
```

This is the ideal route if Stage 6B yields a real fixation, wandering, alignment-interference, or mirage failure class.

## GO — Causal Meaning of Text↔Visual Alignment

Use if:

```text
C2 strongly establishes alignment ≠ retrieval
but
no failure class is rescue-ready
```

Next question:

> Why do text and semantically matching visual regions enter similar routing geometry, and are they causally interchangeable?

## GO — Targeted Natural Failure Extension

Use if:

```text
controlled mirage/dynamic signatures are strong
but
natural validation remains the main missing paper-level evidence
```

The extension should target the discovered failure signature, not simply run more generic COCO captions.

## GO — Cohort/Assay Repair

Use only if a primary controlled assay is mechanically underidentified.

Do not recommend sink causality merely because sink correlates with a state.

---

# 71. Stop Condition

After:

```text
C2 factorial causal dissociation
→ C1 fixed-prefix grounding-collapse curves
→ mirage discovery/confirmation
→ C1 exact demand-transition causal panel
→ wandering/fixation/refresh classification
→ trajectory/PCA analysis
→ C3 object-stress replication
→ C4 exploratory natural validation
→ sink descriptive gate
→ rescue-readiness assessment
→ paper-claim assessment
→ exactly one next-stage recommendation
```

**STOP.**

Do not start the next stage automatically.

The next experiment must be chosen according to which result most materially strengthens the paper's conceptual contribution.
