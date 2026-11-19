# Stage 7A Plan — Causal Visual Grounding States
## Distinguishing Faithful Reads, Prior-Filled Reads, Wrong-Source Reads, Extraction Errors, and Integration Errors

## 0. Purpose

The paper's strongest current discovery is:

\[
\boxed{\text{reasoning state}\rightarrow\text{visual retrieval demand}\rightarrow\text{target-specific visual retrieval}}
\]

with dynamic retargeting:

```text
reasoning demand: A → B → A
causal visual dependence: A → B → A
```

Stage 7A asks the next actionable question:

> **When reasoning demands a visual fact, what actually supplies the evidence that the model then verbalizes and uses?**

The central goal is to causally distinguish:

```text
FAITHFUL_READ
PRIOR_FILL / UNSATISFIED_RETRIEVAL
WRONG_SOURCE_READ
STALE_SOURCE_READ
SOURCE_COUPLED_EXTRACTION_ERROR
DOWNSTREAM_INTEGRATION_ERROR
```

using a unified causal framework.

This stage does **not** yet train an online monitor and does **not** yet run rollback/decoding interventions. Its job is to create **high-confidence causal ground-truth labels** that later make those interventions scientifically defensible.

---

# 1. Why This Stage Is Necessary for the Paper

Current results establish that reasoning can create demand for visual evidence and that the model dynamically re-engages relevant image sources.

But they do not yet establish whether an emitted visual fact is:

```text
actually read from the demanded source,
filled by language/reasoning prior,
read from a confusable wrong source,
carried over from stale earlier evidence,
mis-extracted from the correct source,
or correctly grounded but misused later.
```

A paper-level mechanistic contribution becomes much stronger if it can say:

> **A visual claim is not faithful merely because the model attends to the image or because the claim is correct. Faithfulness depends on whether the emitted evidence is causally supplied by the source that reasoning demanded.**

This creates a direct bridge from mechanistic interpretability to:

```text
faithfulness diagnosis
online detection
grounding-aware intervention
```

---

# 2. Core Representation: Demand → Source → Evidence

For each visual evidence-emission event at reasoning step \(t\), define:

\[
D_t = \text{the visual source demanded by current reasoning}
\]

\[
S_t = \text{the source that causally supports the emitted evidence}
\]

\[
E_t = \text{the evidence claim emitted/used by the model}
\]

and a prior-support quantity:

\[
P_t = \text{degree to which the same evidence persists without valid visual support}
\]

The canonical faithful case is:

\[
\boxed{D_t = S_t\quad\text{and}\quad E_t = \text{true content of }S_t}
\]

Example:

```text
Image:
AB = 5
AD = 8

Reasoning demand:
need AB

Causal source:
AB

Emitted evidence:
"AB = 5"
```

---

# 3. Primary Paper Claim If Positive

The strongest possible Stage 7A claim is:

> **Visual evidence use in thinking models decomposes into distinct causal grounding states. A demanded visual fact can be faithfully retrieved, filled by prior knowledge without genuine grounding, read from the wrong source, inherited from stale evidence, mis-extracted from the correct source, or correctly retrieved and only later misused.**

A stronger source-specific claim is:

> **Faithful visual reasoning requires agreement between reasoning demand, causal source identity, and emitted evidence identity.**

---

# 4. State Taxonomy

## 4.1 FAITHFUL_READ

Requirements:

```text
D = target source T
T is causally important for emitted evidence
T dominates plausible alternative sources
counterfactual edit of T moves E in the expected semantic direction
E matches the true content of T
```

Canonical pattern:

```text
Demand = AB
Source = AB
Evidence = AB's true value
```

## 4.2 PRIOR_FILL / UNSATISFIED_RETRIEVAL

Requirements:

```text
visual demand is present
demanded source is unavailable / masked / semantically insufficient
no visual source provides strong semantic causal support
emitted evidence resembles masked / unrelated / no-image behavior
counterfactual demanded-source semantic control is weak or absent
```

This is the main mechanistic analogue of mirage-like reasoning.

Do not claim that all no-image success is prior-fill.

## 4.3 WRONG_SOURCE_READ

Requirements:

```text
Demand = T
Alternative source X exists
X, not T, causally supports the emitted wrong evidence
X suppression reduces wrong-token / wrong-claim preference
counterfactual X editing moves the wrong evidence in the X-consistent direction
```

A simple `VSD_X > VSD_T` is **not sufficient**. This state requires an error-oriented causal readout.

## 4.4 STALE_SOURCE_READ

Requirements:

```text
current demand = T
previously demanded source = P
P remains causally important after demand switches
T fails to become adequately causal
emitted evidence is consistent with P or an old P-conditioned claim
```

Where possible, require error-oriented support from stale P before calling it harmful.

## 4.5 SOURCE_COUPLED_EXTRACTION_ERROR

Requirements:

```text
Demand = T
T is genuinely causally important
counterfactual T edits move the output
but emitted evidence is objectively incorrect for T
```

Interpretation:

```text
the model is using the correct visual source
but extracting/decoding its content incorrectly
```

## 4.6 DOWNSTREAM_INTEGRATION_ERROR

Requirements:

```text
Demand = T
T is causally grounded
E is locally correct
later reasoning or final answer is wrong
review confirms a downstream error after the grounded event
```

This is not a visual grounding failure.

---

# 5. Key Distinction From MIRAGE-Style Output Diagnostics

Output behavior alone cannot establish source faithfulness.

For example:

```text
image present → "AB=5"
image absent  → "AB=5"
```

suggests prior dependence, but does not identify what happened internally.

Stage 7A upgrades this to a source-specific causal diagnosis:

```text
Demand = AB
Causal source = AB / AD / none / stale source
Evidence = emitted claim
```

The paper should distinguish behavioral mirage-like output from causally diagnosed prior-filled retrieval demand.

---

# 6. Experimental Architecture

Stage 7A has five primary arms:

```text
A — Faithful-Read Positive Controls
B — Unsatisfied Retrieval / Prior-Fill Stress
C — Confusable Wrong-Source Stress
D — Stale-Source / Re-demand Stress
E — Error Localization: Extraction vs Integration
```

A final synthesis phase assigns causal state labels.

---

# 7. Cohort Strategy

Use **controlled conditions first** because state identifiability is the priority.

Reuse compatible Stage 6A assets where possible.

Preferred data sources:

```text
C1 diagram stress:
MathVerse / MathVision / MathVista

C2 alignment/retrieval factorial:
DocVQA

C3 object stress:
POPE + COCO

Historical anchors:
Stage 3A / 3C / 4A / 5A / 6B
```

Historical examples are calibration/reference only.

Fresh confirmatory state labels must come from newly frozen Stage 7A splits or previously untouched Stage 6A confirmation material where available.

---

# 8. Target Sample Size

Target fresh exact-causal events:

```text
FAITHFUL_READ                  >= 64
PRIOR_FILL                     >= 48
WRONG_SOURCE_READ candidate    >= 48 screened
STALE_SOURCE_READ candidate    >= 32 screened
EXTRACTION_ERROR candidate     >= 32 screened
INTEGRATION_ERROR              >= 32
```

Because strict failure classes may have low yield, do not require all to reach target.

For a class to support a cohort-level mechanism claim:

```text
>= 24 fresh Tier-1/strong Tier-2 events
```

For a class with fewer than 24:

```text
report as case-level / pilot-level only
```

Do not keep searching until a desired class appears.

---

# 9. Discovery / Confirmation Split

Within each controlled arm:

```text
1/3 discovery
2/3 confirmation
```

Use discovery only to freeze:

```text
effect floors
source-dominance margins
prior-similarity thresholds
state decision rules
matching tolerances
```

Confirmation receives the rules unchanged.

---

# 10. Event Selection

Select evidence-emission events before causal scoring.

Preferred events:

```text
explicit visual fact claim
numeric evidence claim
object-presence claim
entity-value binding claim
re-use / refresh evidence claim
wrong local visual claim
```

Each event stores:

```text
reasoning prefix
demanded source
plausible alternative sources
previous demanded source
emitted evidence
ground-truth evidence
local correctness
later correctness
```

Selection may not use attention, QK, VSD, counterfactual effect, or monitor-like hidden-state features.

---

# 11. Demand Annotation

Demand must be derived from reasoning semantics, not from visual attention.

For each event:

```text
D = demanded source set
```

Allowed:

```text
single source
compound source set
none
unresolved
```

Primary state classification uses single-source demand first.

---

# 12. Source Candidates

For each event freeze:

```text
T = demanded source
X1 = closest confusable alternative
X2 = optional second alternative
P = previous/stale source if applicable
I = irrelevant control
```

Confusable sources should be selected by semantic/visual structure before causal scoring.

Examples:

```text
AB vs AD
radius vs diameter
upper vs lower segment
two nearby numeric labels
two table rows with similar headers
two semantically similar objects
```

---

# 13. Readout Types

Every event should have one or more frozen readouts.

## Value readout

```text
correct value vs plausible foil
```

## Binding readout

```text
correct source/entity assignment vs wrong assignment
```

## Error-oriented readout

```text
wrong token probability
wrong-vs-correct token margin
```

## Final downstream readout

```text
later reasoning/final answer
```

Do not use one readout type as a substitute for another.

---

# 14. Primary Causal Source Assay

Use the frozen source-suppression intervention:

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

on the confirmation subset for T and the primary alternative/stale source.

For each source \(R\):

\[
VSD_R = D_{\text{native}} - D_{\text{suppress }R}
\]

Unnormalized signed effect is primary.

---

# 15. Error-Oriented Source Effect

For observed wrong evidence \(w\):

\[
EP_R^{token} = \log p(w)_{native} - \log p(w)_{R-off}
\]

and:

\[
EP_R^{margin} = [\log p(w)-\log p(c)]_{native} - [\log p(w)-\log p(c)]_{R-off}
\]

where `c` is the correct alternative.

A source is called `error-promoting` only if the wrong evidence is reduced in the predicted direction.

This is mandatory for WRONG_SOURCE_READ and harmful STALE_SOURCE_READ.

---

# 16. Counterfactual Source-Semantic Assay

For target T and, where relevant, alternative X:

```text
Original
Counterfactual semantic edit
Matched render sham
```

Example:

```text
AB = 5 → AB = 7
AD unchanged
```

or:

```text
AD = 8 → AD = 9
AB unchanged
```

A source-semantic coupling requires:

```text
output evidence moves in the corresponding edited direction
and exceeds matched sham
```

---

# 17. Arm A — Faithful-Read Positive Controls

Purpose:

> establish high-confidence faithful retrieval events against which failure states are compared.

Eligibility:

```text
demanded source T is available
emitted evidence is correct
T is independently editable
plausible alternative source exists where possible
```

Confirmatory faithful-read rule should require:

1. `VSD_T` substantial;
2. `VSD_T > VSD_X/I`;
3. T counterfactual changes emitted evidence in expected direction;
4. sham effect small relative to semantic edit;
5. local claim correct.

---

# 18. Arm B — Unsatisfied Retrieval / Prior-Fill Stress

Use controlled evidence-availability conditions.

Preferred within-base sequence:

```text
intact
strong degradation
full target mask
unrelated image
no image
```

Optional:

```text
explicit guess-mode no-image prompt
```

if a matched prompt can be defined without altering the semantic task.

The key comparison is:

```text
same visual demand
different availability of valid visual evidence
```

---

# 19. Prior-Fill Diagnostic Features

A strict PRIOR_FILL candidate should show:

```text
demand is present
target evidence unavailable/insufficient
T semantic causal control weak
no alternative source strongly supports the claim
claim remains similar across mask / unrelated / no-image
```

Useful measures:

```text
candidate-margin similarity
JS divergence of local output distributions
top-k overlap
same emitted evidence identity
```

Do not define prior-fill from no-image similarity alone.

---

# 20. Optional Mirage-Mode vs Guess-Mode Contrast

Where no-image interface supports it:

## Mirage-mode

```text
image omitted
model is not explicitly told that visual evidence is absent
```

## Guess-mode

```text
image omitted
prompt explicitly states that no image is available and asks the model to infer/guess from text only
```

This arm is secondary.

Question:

> **Does epistemic awareness of missing vision change the internal evidence-production regime?**

---

# 21. Arm C — Confusable Wrong-Source Stress

Construct cases where:

```text
Demand = T
Confusable source X is nearby / semantically similar
T and X have different values/content
```

Preferred controlled designs:

```text
AB vs AD
AB vs AC
radius vs diameter
left vs right label
same keyword in different DocVQA fields
similar object categories
```

The purpose is not to induce errors at all costs. The purpose is to make wrong-source reads **identifiable when they occur**.

---

# 22. Wrong-Source State Gate

A strict WRONG_SOURCE_READ requires:

1. demand = T;
2. emitted evidence is wrong for T;
3. X is causally stronger than T for the emitted evidence;
4. suppressing X reduces wrong-evidence probability/margin;
5. counterfactual X edit moves wrong evidence in the X-consistent direction;
6. counterfactual T edit does not explain the wrong evidence;
7. controls rule out generic image corruption.

Without 4–5, classify only as `SOURCE_ANOMALY`, not wrong-source read.

---

# 23. Arm D — Stale-Source / Re-demand Stress

Reuse multi-evidence trajectories:

```text
A → B → A
```

and other source-switch traces.

At the second A demand, test:

```text
current source A
intervening source B
```

Potential states:

```text
A causally re-engaged → faithful refresh
B remains causal       → stale-source candidate
neither strong         → prior-fill / unresolved
```

Where the emitted A-related evidence is wrong, require error-oriented B support before calling stale B error-promoting.

---

# 24. Arm E — Extraction vs Integration Error

This arm separates failures after source identity is already known.

## Source-coupled extraction error

```text
T is causal
T counterfactual controls output
local claim wrong
```

## Downstream integration error

```text
T is causal
local claim correct
later reasoning/final answer wrong
reviewed downstream error occurs after the grounded event
```

This arm is crucial because not every multimodal failure should trigger a retrieval intervention.

---

# 25. Causal State Decision Tree

For every eligible event:

```text
Step 1: Is there a valid visual demand D?
  no → outside primary Stage 7A taxonomy
  yes → continue

Step 2: Is the emitted evidence locally correct?
  yes → test source faithfulness
  no  → test failure source

Step 3: Does demanded source T have strong causal support?
  yes → continue
  no  → test alternatives/prior

Step 4: Does counterfactual T control the evidence?
  yes + correct → FAITHFUL_READ
  yes + wrong   → SOURCE_COUPLED_EXTRACTION_ERROR

Step 5: Does alternative source X causally promote wrong evidence?
  yes + semantic X followability → WRONG_SOURCE_READ

Step 6: Does previous source P remain harmful after a demand switch?
  yes → STALE_SOURCE_READ

Step 7: Are all visual sources weak and behavior close to no-image/prior?
  yes → PRIOR_FILL / UNSATISFIED_RETRIEVAL

Step 8: Was local evidence faithful but later reasoning wrong?
  yes → DOWNSTREAM_INTEGRATION_ERROR

Otherwise:
  UNRESOLVED
```

Do not force every event into a named state.

---

# 26. Confidence Tiers

## Tier 1 — Strong causal state

Requires:

```text
semantic demand
source suppression
counterfactual semantic control
matched controls
correctly oriented readout
```

## Tier 2 — Causal source state

Requires:

```text
semantic demand
source suppression
readout validity
```

but lacks full counterfactual confirmation.

## Tier 3 — Behavioral candidate

Based on:

```text
mask/no-image behavior
wrong claim
passive features
```

without sufficient source causality.

Main paper claims should rely primarily on Tier 1.

---

# 27. Passive Feature Extraction for Future Stage 7B

After causal state labels freeze, extract:

```text
recent reasoning state summaries
QK features
ROI attention mass/density
visual attention share
alphaV
post-W_O contribution
late residual state
entropy
candidate margin
sink mass
sink release
source-relative attention features
distance from no-image / masked logit distributions where available
```

Do not use passive features to define the causal state labels.

---

# 28. Source-Specific Passive Features

For monitor-readiness analysis, preserve:

```text
feature(T)
feature(X)
feature(P)
feature(I)
```

rather than only pooled visual features.

Examples:

```text
QK_T - QK_X
alphaV_T - alphaV_X
attention_T - attention_X
postWO_T - postWO_X
```

This is necessary for future `which source actually supports this claim?` monitoring.

---

# 29. Stage 7A Does Not Yet Train the Final Monitor

A small separability analysis is allowed only to assess whether Stage 7B is plausible.

Allowed:

```text
simple linear/logistic probes
grouped held-out evaluation
feature-family ablations
```

Not allowed:

```text
large model training
aggressive hyperparameter search
monitor-guided decoding
rollback
intervention based on predicted state
```

If separability is weak, preserve the result. Do not tune until a positive classifier appears.

---

# 30. Probe Tasks

Secondary feasibility tasks:

```text
FAITHFUL_READ vs PRIOR_FILL
FAITHFUL_READ vs WRONG_SOURCE_READ
correct-source vs wrong-source identity
grounded vs ungrounded evidence
```

Use grouped splits by:

```text
base
dataset
template family where possible
```

No event leakage across folds.

Primary metrics:

```text
balanced accuracy
macro F1
AUROC where binary
calibration
```

Probe performance is not itself a mechanistic claim.

---

# 31. Faithfulness Metrics

Define the following descriptive/causal metrics.

## Demand–Source Consistency

\[
DSC = P(S=D \mid D \neq \varnothing)
\]

## Grounded Evidence Rate

Fraction of emitted visual claims with substantial causal visual support.

## Wrong-Source Read Rate

\[
WSR = P(S\neq D,\; S\neq\varnothing)
\]

## Prior-Fill Rate

\[
PFR = P(S\approx\varnothing \mid D\neq\varnothing)
\]

## Counterfactual Followability

Fraction of events where changing demanded visual content moves the evidence accordingly.

Do not estimate natural prevalence from deliberately balanced stress cohorts.

---

# 32. Correctness and Faithfulness Must Remain Separate

Report separately:

```text
faithful + correct
faithful + wrong
unfaithful + correct
unfaithful + wrong
```

Examples:

```text
correct answer produced by prior fill
wrong answer after faithful retrieval
```

are both scientifically important.

---

# 33. Primary Statistical Unit

Independent unit:

```text
base / image-question family
```

Repeated conditions/events are nested.

Use:

```text
paired within-base analysis
base bootstrap
cluster-aware confidence intervals
```

Do not treat all event rows as independent.

---

# 34. Primary Confirmatory Families

Keep separate:

## Family 1 — Faithful-read validation

```text
T > X/I source causality
T semantic followability
```

## Family 2 — Prior-fill / unsatisfied retrieval

```text
mask/unrelated/no-image convergence
loss of T semantic control
```

## Family 3 — Wrong-source read

```text
X error-promoting effect
X semantic followability
T-vs-X source identity
```

## Family 4 — Stale-source read

```text
P persistence after demand switch
error-promoting stale-source effect
```

## Family 5 — Extraction vs integration

```text
local source grounding
local correctness
later correctness
```

Use Holm correction within family.

---

# 35. Robustness Rule

For a directional cohort-level contrast to be called robust:

```text
expected-direction median
bootstrap 95% mean CI excludes zero
>= 75% expected-direction bases where meaningful
Holm-corrected p < .05
```

For rare failure classes, report exact counts and effect-size distributions even if cohort-level robustness is not applicable.

---

# 36. Dataset Robustness

Report results separately for:

```text
MathVerse
MathVision
MathVista
DocVQA if used
POPE/COCO if used
```

Do not pool all datasets into one headline if source semantics differ materially.

---

# 37. Mechanism-Guided Intervention Readiness Gate

Stage 7A does not run intervention.

It only asks whether a future Stage 7C is justified.

A state class is intervention-ready if:

1. at least 24 fresh Tier-1/strong Tier-2 events exist;
2. the causal direction is coherent;
3. the failure readout is correctly oriented;
4. there is a clear predicted corrective action;
5. matched faithful controls predict little or opposite effect.

Example mappings:

```text
PRIOR_FILL
→ force visual verification / abstain / source-grounded decoding

WRONG_SOURCE_READ
→ demand-consistent source-specific decoding

STALE_SOURCE_READ
→ stale-source suppression + refresh

EXTRACTION_ERROR
→ retrieval strengthening may not help; investigate decoding/content readout

INTEGRATION_ERROR
→ visual retrieval intervention should not help
```

---

# 38. Expected Stage 7B Monitor Readiness Gate

Recommend an online monitor only if:

```text
at least two causal grounding states have sufficient fresh N
and
held-out passive features separate them meaningfully
and
source identity can be predicted above matched baselines
```

A monitor should ideally predict both:

```text
is this claim grounded?
which source supports it?
```

Binary mirage detection alone is not the preferred endpoint.

---

# 39. Null Interpretation Discipline

## Few PRIOR_FILL cases

Does not prove mirage-like reasoning is absent.

Possible reasons:

```text
model abstains under missing evidence
mask conditions are too salient
selected tasks strongly constrain values
```

## Few WRONG_SOURCE_READ cases

Does not prove wrong-source hallucination is absent.

Possible reasons:

```text
confusable source construction too weak
model errors arise from extraction/integration instead
```

## Weak probe separability

Does not invalidate causal state taxonomy.

It means passive online detection may require better features or may not be feasible.

## Strong no-image similarity

Does not prove zero visual use.

Causal source evidence remains primary.

---

# 40. Historical Result Integration

Stage 7A should explicitly position prior stages as follows:

```text
Stage 3C.10:
reasoning context can create visual retrieval demand

Stage 4A:
demand retargets causal visual source dynamically

Stage 5A:
final/wrong-answer labels alone do not localize failure;
integration failures exist

Stage 6B:
evidence degradation strongly reduces causal grounding;
strict mirage-like cases exist but are not broad enough for a generic taxonomy

Stage 6B-R:
wandering/fixation comparison remained underidentified
```

Stage 7A therefore changes the question from:

```text
What generic failure state does this trajectory resemble?
```

to:

```text
Was this particular emitted visual evidence causally supplied by the source that reasoning demanded?
```

---

# 41. Required Figures

At minimum:

1. Demand–Source–Evidence triangle;
2. six-state causal taxonomy;
3. faithful-read example with target counterfactual;
4. prior-fill example;
5. wrong-source example with error-oriented source suppression;
6. wrong-source counterfactual followability;
7. stale-source example;
8. source-coupled extraction error;
9. downstream integration error;
10. target vs wrong-source VSD by state;
11. error-promoting source effects;
12. masked/unrelated/no-image similarity;
13. counterfactual followability by state;
14. correctness × faithfulness matrix;
15. demand–source consistency by condition;
16. grounded evidence rate by condition;
17. wrong-source/prior-fill rates in controlled stress;
18. source-specific passive signatures;
19. probe feasibility by feature family;
20. intervention-readiness by state class;
21. dataset-stratified state yields;
22. final conceptual figure:

```text
Reasoning Demand
      ↓
Need source T
      ↓
┌───────────────┬────────────────┬────────────────┐
│               │                │                │
T causally      no source        wrong/stale      T causally
supports E      supports E       source supports E supports wrong E
│               │                │                │
Faithful        Prior Fill       Wrong/Stale      Extraction Error
Read            / Mirage-like    Read
                                  \
                                   \
                                    correct local E
                                          ↓
                                   downstream wrong
                                   Integration Error
```

---

# 42. Output Structure

```text
outputs/stage7a/
  config/
    stage7a_config.json
    demand_rules.json
    source_role_rules.json
    readout_rules.json
    state_taxonomy.json
    causal_windows.json
    counterfactual_rules.json
    statistical_families.json

  cohort/
    faithful_manifest.jsonl
    prior_fill_manifest.jsonl
    wrong_source_manifest.jsonl
    stale_source_manifest.jsonl
    extraction_error_manifest.jsonl
    integration_error_manifest.jsonl
    discovery_confirmation_split.json
    exclusions.jsonl
    screening_accounting.json

  annotations/
    demand.jsonl
    source_candidates.jsonl
    evidence_claims.jsonl
    value_readouts.jsonl
    binding_readouts.jsonl
    error_readouts.jsonl
    downstream_error_review.jsonl

  audit/
    canonical_path_audit.json
    event_index_audit.json
    roi_source_audit.json
    counterfactual_edit_audit.json
    readout_orientation_audit.json
    no_image_audit.json
    source_suppression_audit.json
    deterministic_replay.json
    split_integrity.json
    resource_summary.json

  causal/
    w2_source_scores.jsonl
    w8_sensitivity.jsonl
    error_oriented_scores.jsonl
    target_counterfactuals.jsonl
    alternative_counterfactuals.jsonl
    sham_controls.jsonl

  prior_fill/
    masked_scores.jsonl
    unrelated_scores.jsonl
    no_image_scores.jsonl
    guess_mode_scores.jsonl
    distribution_similarity.json

  labels/
    tier1_states.jsonl
    tier2_states.jsonl
    unresolved.jsonl
    state_counts.json
    faithfulness_metrics.json

  passive/
    source_specific_features.jsonl
    residual_features.jsonl
    routing_features.jsonl
    sink_features.jsonl

  monitor_feasibility/
    grouped_splits.json
    probe_results.json
    feature_ablation.json
    calibration.json

  analysis/
    primary_statistics.json
    correctness_faithfulness_matrix.json
    dataset_robustness.json
    paper_claim_assessment.json
    intervention_readiness.json
    monitor_readiness.json
    figures/

  summaries/
    stage7a_summary.md
    stage7a_acceptance.json
    next_stage_recommendation.md
```

---

# 43. Technical Acceptance Criteria

Stage 7A technically passes if:

1. demand/source/evidence taxonomy is frozen before causal scoring;
2. event selection is attention-blind;
3. source candidates are frozen before causal effects;
4. readout orientation is audited;
5. W2 remains primary;
6. W8 is predeclared sensitivity;
7. wrong-source claims require error-oriented source effects;
8. wrong-source claims require source-semantic followability where available;
9. prior-fill is not defined from no-image similarity alone;
10. local correctness and faithfulness remain separate;
11. extraction and integration errors remain separate;
12. historical anchors are not counted as fresh confirmation;
13. discovery rules are not tuned on confirmation;
14. passive features do not define causal labels;
15. probe performance is treated as feasibility, not mechanism;
16. no rollback/decoding intervention is run;
17. no sink intervention is run;
18. no new head/layer discovery search is run;
19. unresolved cases remain unresolved;
20. exactly one next-stage recommendation is produced.

Technical PASS does not require every state class to reach its target sample size.

---

# 44. Scientific Outcome Map

## O1 — Causal Grounding State Taxonomy

If multiple states are observed with convergent causal evidence:

> **Visual reasoning contains distinct source-specific grounding states rather than a single correct/wrong or grounded/hallucinated dichotomy.**

## O2 — Faithful Read

If demanded source and emitted evidence align causally:

> **A visual claim can be certified as source-faithful.**

## O3 — Prior-Filled Retrieval Demand

If demand remains but no visual source semantically controls the claim:

> **Some visual evidence emissions fill an unsatisfied retrieval demand without genuine visual grounding.**

## O4 — Wrong-Source Read

If a confusable wrong source causally promotes and semantically controls the wrong evidence:

> **Some hallucinated visual claims are genuine reads from the wrong source rather than absence of visual processing.**

This is a high-value outcome.

## O5 — Extraction Error

If correct source is causal but emitted evidence is wrong:

> **Source selection and content extraction are separable failure points.**

## O6 — Integration Error

If local grounding is faithful but later reasoning fails:

> **Not all multimodal failures should be repaired by stronger visual retrieval.**

## O7 — Monitor Feasibility

If passive source-specific features separate causal states:

> **Causal grounding faithfulness may be detectable online without running the full causal intervention at inference time.**

This is a bridge to Stage 7B, not yet a deployment claim.

---

# 45. What Would Make Stage 7A Insightful?

The strongest result is not:

```text
wrong answers have different hidden states
```

It is:

> **Two identical-looking evidence claims can arise from different causal sources: the demanded ROI, a wrong ROI, or no meaningful visual source at all.**

Even stronger:

> **The model can satisfy a visual retrieval demand with evidence causally read from the wrong source.**

That would directly motivate source-aware monitoring and intervention.

---

# 46. What Would Not Be Enough

Do not claim:

```text
correct answer = faithful
high attention = grounded
mask persistence = mirage
VSD_X > VSD_T = wrongful read
hidden-state separability = causal mechanism
```

Do not force a rare failure class to justify intervention.

---

# 47. Next-Stage Decision

Produce exactly one recommendation.

## GO — Stage 7B Online Grounding / Faithfulness Monitor

Use if:

```text
at least two causal state classes have sufficient fresh N
+
passive source-specific features provide held-out discrimination
```

Preferred monitor outputs:

```text
P(faithful)
P(prior-fill)
P(wrong-source)
predicted source identity
```

## GO — Stage 7C Mechanism-Guided Grounding Intervention

Only if a state class is already both:

```text
causally coherent
and
detectable online
```

Normally Stage 7B should precede Stage 7C.

## GO — Targeted Failure Cohort

Use only if one scientifically important state is clearly identifiable but too rare for confirmatory inference.

The new cohort must target the missing state by construction rather than generic error oversampling.

## GO — Causal Meaning of Text↔Visual Alignment

Use if causal grounding states are mostly faithful and failure classes are too rare, making shared semantic addressing the higher-value unresolved mechanism.

## STOP / REPORT

Use if causal states are identifiable but no passive monitor/intervention path is justified.

---

# 48. Stop Condition

After:

```text
freeze demand/source/evidence ontology
→ freeze event/readout/source candidates
→ score faithful controls
→ score unsatisfied retrieval/prior-fill stress
→ score confusable wrong-source cases
→ score stale-source/re-demand cases
→ separate extraction vs integration errors
→ assign causal state tiers
→ extract passive monitor features
→ run bounded monitor-feasibility analysis
→ assess intervention readiness
→ assess paper claims
→ produce exactly one recommendation
```

**STOP.**

Do not start Stage 7B or Stage 7C automatically.

---

# 49. Final Research Principle

Stage 7A should answer:

\[
\boxed{\text{When the model says it "read" a visual fact, what causal source actually supplied that fact?}}
\]

The core faithfulness criterion is:

\[
\boxed{\text{reasoning demand}\;\approx\;\text{causal source}\;\approx\;\text{emitted evidence}}
\]

This is the bridge from reasoning-conditioned visual retrieval to source-specific faithfulness monitoring and intervention.
