# Stage 3C.8 Plan — Token-Type Carrier Atlas

## 0. Purpose

Stage 3C.8 follows the Stage 3C.7 result:

> **The exact immediately preceding reasoning token (`t_pre`) has a behaviorally useful native K/V cache: restoring its native cache after a target-ROI visual-acquisition deficit repairs the deficit completely when K+V is restored across the full P4 depth.**

Stage 3C.7 established:

```text
Target A:
K-only RR ≈ -0.139
V-only RR ≈ 0.640
K+V RR = 1.000

Target B:
K-only RR ≈ -0.089
V-only RR ≈ 0.600
K+V RR = 1.000
```

and:

```text
Target A:
current residual + downstream t_pre cache
→ near-complete rescue

Target B:
full-depth t_pre cache
→ exact rescue
```

Thus token-local cache carriage is no longer merely speculative.

The next question is:

> **Which kinds of text/reasoning tokens functionally carry visual evidence?**

Examples of interest include:

```text
"What is AB ?"

what   → interrogative / task operator?
is     → function / copula?
AB     → visually aligned entity?
?      → boundary / integration position?
```

Stage 3C.8 builds a **large-sample causal carrier atlas** that separates:

1. token lexical/semantic type
2. sequence/structural position
3. visual alignment
4. reasoning role
5. K vs V cache function
6. prefill carrier vs late-reasoning carrier

The goal is not to find one universally “special token.”

The goal is to determine whether visual residual carriage is:

```text
sparse and token-type-specific
position/boundary-specific
visual-entity-aligned
reasoning-role-specific
or broadly distributed / item-specific
```

---

# 1. Why This Stage Is Important

This experiment is worth doing because it addresses an unresolved part of the central visual-evidence lifecycle:

```text
visual acquisition
→ text/reasoning-side state
→ later evidence use
```

Stage 3C.7 established that a reasoning-token cache can be a functional carrier.

What remains unknown is whether this is:

- a generic property of the immediately preceding position;
- preferentially associated with visually aligned entity tokens;
- associated with task/relation/operator tokens;
- concentrated at punctuation or sequence boundaries;
- distributed over many recent reasoning tokens;
- different between prefill and late reasoning.

---

# 2. What This Stage Can and Cannot Establish

## It can establish

- whether certain token categories show reproducibly stronger causal carrier effects;
- whether carrier strength is better predicted by token type or by distance/position;
- whether visually aligned entity tokens are privileged carriers;
- whether punctuation/boundary positions behave like integration states;
- whether late reasoning carriers differ from prompt/prefill carriers;
- whether prior-token K and V have different carrier roles.

## A null does NOT establish

If one token type is weak, do **not** conclude that token type never carries visual information.

Possible surviving explanations:

- the carrier may be distributed over multiple positions;
- span-level rather than single-token state may matter;
- tokenization may split semantic units;
- different reasoning coordinates may use different carriers;
- state interactions can make single-position rescue weak.

Therefore Stage 3C.8 includes:

```text
single-position
semantic-span
token-type group
recent-window group
```

analyses.

One weak assay must not kill the entire direction.

---

# 3. Stage Structure

Stage 3C.8 has three primary causal atlases plus one gated long-horizon anchor extension.

## Phase A — Natural `t_pre` Carrier-Type Atlas

Across many fresh examples, classify the exact behaviorally relevant `t_pre` token and test whether its full-depth cache rescue depends systematically on token type.

## Phase B — Recent-Reasoning Position/Type Atlas

Create a multi-query target-ROI suppression deficit, then restore recent reasoning-token caches one position at a time and by token-type groups.

## Phase C — Prefill / Question-Token Carrier Atlas

Use the Stage 3B.0 generation-start vision-cutoff paradigm and decompose the Q-side prefill visual residual across individual question/prompt tokens and token types.

## Phase D — Long-Horizon Dynamic Anchor Checkpoints (gated extension)

If Phases A/B establish reliable token-local or token-group carrier signal, extend the analysis beyond the immediate `t_pre` neighborhood and ask whether long reasoning contains **repeated causal information-integration checkpoints**.

These phases answer related but different questions and must not be pooled into one carrier score.

---


---

# 3A. Conceptual Extension — Carrier, Integration Checkpoint, Retrieval-Control Anchor

The user-provided discussion of *MAP THE FLOW: REVEALING HIDDEN PATHWAYS OF INFORMATION IN VIDEOLLMS* motivates a broader question than token storage alone.

The supplied excerpt argues that, in VideoQA, certain temporal-keyword-containing option tokens can behave as information-integration checkpoints, and that video information may reach them through task-dependent direct or indirect routes.

Stage 3C.8 does **not** assume the same mechanism in Thinking MLLMs. Instead, it uses that observation as a hypothesis generator and distinguishes three roles.

## 3A.1 Carrier token

A token cache contains a behaviorally useful consequence of visual evidence acquisition that can be restored into a deficient run.

Operational signature:

```text
visual-acquisition deficit
+
native token K/V rescue
→ downstream evidence recovery
```

Stage 3C.7 `t_pre` is the current positive example.

## 3A.2 Integration checkpoint / anchor token

A token acts as a point where visually derived information and ongoing linguistic/reasoning state become jointly consolidated for later use.

A strong checkpoint should ideally show both:

```text
receives a visual-acquisition consequence
and
supports later reasoning behavior
```

A checkpoint can be a visual entity, numeric result, operator, discourse marker, punctuation/boundary token, or some other reasoning-dependent position.

## 3A.3 Retrieval-control anchor

A token may not store much evidence content itself, but its state can help determine where later queries retrieve visual evidence from.

Potential examples:

```text
"AB"
"Now"
"need"
"which"
"left"
```

This is conceptually distinct from content carriage.

Stage 3C.8 primarily tests **carrier/checkpoint behavior** through cache rescue. It does not yet establish a retrieval-control mechanism unless a separate routing intervention is performed.

## 3A.4 Why long reasoning matters

A Thinking MLLM may not use one fixed text position as a visual memory slot.

A plausible lifecycle is:

```text
visual evidence A
→ anchor/checkpoint A
→ intermediate reasoning
→ new subgoal
→ visual evidence B
→ anchor/checkpoint B
→ later integration
→ answer
```

Thus a major long-term hypothesis is:

> **Long-form multimodal reasoning dynamically forms a sequence of visual-information checkpoints rather than continuously broadcasting visual evidence to every reasoning token.**

Stage 3C.8 Phase D provides a first gated test of this idea.


# 4. Cohort Design — Larger Sample

Use three disjoint sets.

## 4.1 Mechanical validation

Target:

```text
8 unique bases
```

Used only for patch mechanics, cache alignment, tokenizer/span annotation audit, and deterministic replay.

## 4.2 Historical anchor cohort

Reuse the exact:

```text
24 Stage 3C.3–3C.7 primary bases
```

Purpose:

- reproduce the established t_pre full-cache rescue;
- anchor new atlas results to the historical mechanism.

These are not fresh confirmation cases.

## 4.3 Fresh atlas cohort

Target:

```text
64 unique fresh valid bases
```

Minimum:

```text
56
```

Screen prospectively until the target is reached.

Must be disjoint from prior validation/discovery/geometry cohorts.

Primary inferential claims use the fresh atlas cohort.

Combined reporting may show:

```text
24 historical anchors
+
64 fresh atlas bases
=
88 total mechanistically annotated bases
```

but historical and fresh results must remain separately visible.

---

# 5. Fresh-Base Requirements

Each fresh base must have:

1. completed-correct Qwen3-VL-4B-Thinking trajectory;
2. clean localized numeric visual evidence;
3. valid O/O_sham/C/C_sham image quartet;
4. strict discriminative evidence decision `E_d`;
5. valid Stage 3A-style semantic fact pair;
6. manually validated target ROI T;
7. exact visual-token layout matching across four conditions;
8. at least 16 reasoning-token positions before tested `t*` where required for Phase B;
9. exact prompt/question tokenization preserved across image conditions;
10. no attention-based inclusion.

Selection must not use token-carrier rescue outcomes.

---

# 6. Target Coordinates

For historical anchors, retain exact A/B target definitions.

For fresh atlas examples, define two standardized coordinates where possible:

```text
A-like:
t* = E_d

B-like:
t* = E_d - 1
```

with:

```text
t_pre = t* - 1
```

If a fresh base cannot support both coordinates cleanly, retain the valid coordinate and record availability.

Do not manufacture artificial timing matches.

Primary fresh analysis reports A-like and B-like coordinates separately.

---

# 7. Token Annotation Framework

Token role must be annotated **before causal token-level results are inspected**.

Use orthogonal labels.

Each token receives:

## 7.1 Stream

```text
PROMPT_QUESTION
SPECIAL_CONTROL
PREVIOUS_REASONING
```

## 7.2 Lexical / semantic class

```text
VISUAL_ENTITY
INTERROGATIVE
RELATION_OPERATOR
MATH_OPERATOR
NUMERIC_LITERAL
FUNCTION_WORD
DISCOURSE_MARKER
PUNCTUATION
SPECIAL_TOKEN
OTHER_CONTENT
```

Examples:

```text
AB        → VISUAL_ENTITY
what      → INTERROGATIVE
left      → RELATION_OPERATOR
is/of     → FUNCTION_WORD
=,+       → MATH_OPERATOR
therefore → DISCOURSE_MARKER
?,.,:     → PUNCTUATION
```

## 7.3 Visual alignment

```text
TARGET_ALIGNED
MENTION_ALIGNED
OTHER_VISUAL_ENTITY
NO_DIRECT_VISUAL_ALIGNMENT
```

Visual alignment is manually tied to annotated image entities, not attention.

## 7.4 Structural role

```text
QUESTION_INITIAL
QUESTION_FINAL
CLAUSE_FINAL
SENTENCE_FINAL
SPAN_FINAL
NONE
```

## 7.5 Reasoning role

For previous reasoning tokens:

```text
TARGET_ENTITY_MENTION
NON_TARGET_ENTITY_MENTION
INTERMEDIATE_RESULT
SUBGOAL_OPERATOR
DISCOURSE_TRANSITION
BOUNDARY
OTHER
```

## 7.6 Relative position

```text
distance_to_t*
distance_to_t_pre
absolute sequence position
```

This allows token type to be separated from recency.

---

# 8. Tokenization and Span Audit

Raw tokenizer pieces are not always semantic words.

Store both:

```text
token-level position
lexical-span grouping
```

A semantic span may contain multiple tokenizer positions.

For every annotated span record:

- constituent token IDs;
- decoded text;
- start/end position;
- taxonomy labels.

Primary single-token atlas remains position-level.

A separate span-level rescue prevents split-token artifacts.

---

# PHASE A — NATURAL t_pre CARRIER-TYPE ATLAS

## 9. Core Question

Stage 3C.7 showed that the exact `t_pre` cache can repair the visual-acquisition deficit.

Now ask:

> **Across many problems, does the strength/mechanism of that `t_pre` cache depend on what kind of token `t_pre` is?**

This is the cleanest token-type analysis because the causal role of `t_pre` is already independently established.

---

# 10. Phase-A Deficit

Use the exact Stage 3C.7 within-condition logic.

For each coordinate:

```text
Native-O vs Suppressed-O
Native-C vs Suppressed-C
```

Suppression:

```text
at t_pre
target ROI T contribution removed
P4 = layers 16–35
```

Do not retune layer scope per token type.

---

# 11. Phase-A Rescue Arms

Restore only the exact `t_pre` cache entry.

Run:

```text
K-only
V-only
K+V
```

across P4 layers 16–35.

Measure:

```text
unnormalized rescue gain
RR_K
RR_V
RR_KV
```

as in Stage 3C.7.

---

# 12. Phase-A Primary Analysis

For each base/coordinate, associate `t_pre` rescue with its frozen token labels.

Primary questions:

1. Are VISUAL_ENTITY t_pre tokens stronger carriers?
2. Are FUNCTION_WORD tokens weak or unexpectedly strong?
3. Are PUNCTUATION / boundary tokens strong integration carriers?
4. Do INTERROGATIVE / RELATION_OPERATOR tokens show a routing-like cache phenotype?
5. Does K/V mechanism differ by token type?
6. Is token type predictive after controlling for position?

---

# 13. Phase-A Type Statistics

For every token class with at least:

```text
12 fresh base-level observations
```

report:

- median K+V rescue gain;
- median RR;
- bootstrap 95% CI;
- positive fraction;
- median V-only / K+V relationship;
- median K-only / K+V relationship.

Sparse classes are descriptive only.

No class is dropped because its effect is weak.

---

# PHASE B — RECENT-REASONING TOKEN CARRIER ATLAS

## 14. Why Phase B

`t_pre` is a special temporal position.

A strong `t_pre` token-type association could really mean:

```text
the immediately preceding position is special
```

rather than:

```text
this lexical token type is special
```

Phase B separates token type from recency by scanning several recent reasoning positions.

---

# 15. Phase-B Deficit

Use an all-layer recent target-ROI suppression window:

```text
[t*-16, t*]
```

reusing Stage 3C.4 T16 semantics.

At every query in the window:

```text
all language layers
all heads
target ROI contribution
c_T → 0
```

This creates a robust late visual-evidence deficit and allows recent reasoning-token caches to diverge from native.

All earlier queries remain native.

---

# 16. Phase-B Positive Reference

Before single-position scanning run:

```text
ALL_RECENT_CACHE_RESCUE
```

Restore native K+V caches for every generated reasoning-token position:

```text
t*-16 ... t*-1
```

across all layers.

Current query `t*` remains suppressed.

This provides an upper reference for how much recent token-cache state can rescue.

If all-recent cache rescue is weak:

> do not interpret weak single-token effects as evidence against token carriers.

---

# 17. Exhaustive Recent-Position Rescue

For every position:

```text
p in [t*-16, t*-1]
```

restore only that reasoning token's native:

```text
K+V cache
```

across all layers.

All other recent cache positions remain suppressed.

Measure:

```text
G_position(p)
RR_position(p)
```

within semantic condition.

This produces an exhaustive 16-position causal carrier profile per base.

No attention is used to select positions.

---

# 18. Fixed Recent-Position K/V Decomposition

Do not run K/V decomposition on all 16 positions automatically.

Prospectively run K-only/V-only/K+V for:

```text
t*-1
t*-2
t*-4
t*-8
t*-16
```

when available.

This gives a fixed temporal mechanism profile without outcome-based selection.

---

# 19. Semantic-Span Rescue

For any lexical span containing multiple tokenizer positions, patch all constituent token-cache entries jointly.

Examples:

```text
AB
angle A
therefore
```

Analyze span rescue separately from single-position rescue.

---

# 20. Token-Type Group Rescue

Within each recent window and base, jointly restore all positions belonging to a frozen token class.

Examples:

```text
all VISUAL_ENTITY positions
all FUNCTION_WORD positions
all PUNCTUATION positions
all DISCOURSE_MARKER positions
all NUMERIC_LITERAL positions
```

Primary group metric:

```text
G_type_group
RR_type_group
```

This tests whether a type has a distributed carrier role even if no single position is sufficient.

---

# 21. Recency-Matched Controls

Token type is confounded with distance to `t*`.

For every class-level comparison:

- match token positions by relative distance bucket;
- preserve stream (`PREVIOUS_REASONING`);
- preserve approximately equal token count.

Use within-base matched comparisons when available.

Do not claim a token-type effect from unmatched raw averages.

---

# 22. Phase-B Primary Questions

1. Is rescue mostly determined by recency?
2. After recency matching, do specific token types remain stronger?
3. Are boundary tokens stronger than non-boundary tokens at similar positions?
4. Are visually aligned entity tokens privileged?
5. Do intermediate numeric results act as carriers?
6. Does the recent window contain sparse carriers or distributed group-level carriers?
7. Does K/V mechanism change with distance from `t*`?

---

# PHASE C — PREFILL / QUESTION-TOKEN CARRIER ATLAS

## 23. Why Phase C

Stage 3B.0 showed:

> a small but real prefill visual residual exists in Q-side cached states.

But Q was treated as one coarse group.

Stage 3C.8 decomposes that residual into individual question/prompt tokens.

This directly addresses examples such as:

```text
What | is | AB | ?
```

---

# 24. Phase-C Readout Condition

Use the exact Stage 3B.0-style generation-start vision cutoff.

Procedure:

1. prefill normally with O or C image;
2. preserve exact prompt/question cache;
3. from first generated reasoning query onward, block direct generated-query → visual-token access;
4. score the frozen evidence fact preference.

Thus remaining O/C evidence difference is a **prefill nonvisual residual**.

---

# 25. Phase-C Positive Reference

Run:

```text
FULL_Q_PATCH
```

using the Stage 3B.0-compatible Q-side K/V patch.

This must reproduce source-like transfer of the remaining cutoff residual.

If full-Q transfer is absent on the fresh cohort:

> individual token nulls cannot be interpreted as evidence that Q token types do not carry visual residual.

This positive-control gate is mandatory.

---

# 26. Exhaustive Prompt/Question Position Scan

For every eligible nonvisual prompt/question position `q_i`:

```text
C recipient + O q_i K/V
O recipient + C q_i K/V
```

with future direct vision blocked.

Run bidirectionally.

Use:

```text
K+V patch
```

as the primary single-position carrier assay.

Self:

```text
O→O
C→C
```

must be exact.

---

# 27. Prompt Span and Type Group Rescue

Run joint patches for:

## Semantic spans

```text
visual entity spans
relation phrases
interrogative phrases
numeric literals
```

## Frozen token classes

```text
VISUAL_ENTITY
INTERROGATIVE
RELATION_OPERATOR
MATH_OPERATOR
FUNCTION_WORD
PUNCTUATION
SPECIAL_TOKEN
OTHER_CONTENT
```

This tests whether prefill residual is sparse or distributed across a token category.

---

# 28. Prompt Structural Controls

To separate token semantics from position:

## Question-final comparison

```text
question-final punctuation
vs
question-final non-punctuation where available
```

## Visual entity comparison

```text
visually aligned entity
vs
nonvisual content token at matched question position
```

## Function-word comparison

```text
is/of/the
vs
matched neighboring content token
```

## Special/control comparison

Keep separate from lexical tokens.

---

# 29. Phase-C K/V Decomposition

K/V decomposition is gated.

For token classes with robust K+V group transfer on fresh bases, run:

```text
K-only
V-only
K+V
```

for the full type group.

Do not run K/V decomposition for every individual prompt token.

---


# PHASE D — LONG-HORIZON DYNAMIC ANCHOR CHECKPOINTS

## D0. Motivation

Phases A–C characterize **which token types and nearby positions can act as carriers**.

Phase D asks a different question:

> **Across a long chain of reasoning, are there repeated reasoning tokens that serve as causal visual-information integration checkpoints?**

This is motivated by the possibility that long reasoning contains multiple successive anchors such as:

```text
"We need AB."
"AB = 3."
"Therefore ..."
"Now consider CD."
"CD = 7."
"Using these values ..."
"Thus ..."
```

The important question is not whether these literal strings are special.

The question is whether the model repeatedly consolidates visually derived information at particular reasoning positions and then uses those positions downstream.

---

## D1. Gate

Run Phase D only if at least one of the following is true on the fresh cohort:

1. Phase A shows robust `t_pre` token-cache rescue across fresh bases;
2. Phase B all-recent-cache rescue is substantial and at least some individual or type-group rescue is reproducibly nonzero;
3. Phase B shows a clear sparse or type-distributed carrier phenotype.

If all token-cache carrier assays are weak:

```text
do not force a long-horizon checkpoint story
```

Stop Phase D and report that the current residual/distributed-state explanation remains stronger.

---

## D2. Phase-D Cohort

Use a fixed subset of:

```text
32 fresh atlas bases
```

selected **before Phase-D causal outcomes**.

Selection should maximize annotation validity and long-reasoning coverage, not carrier effect size.

Minimum:

```text
28 valid bases
```

Prefer trajectories with:

- at least 128 reasoning tokens before `E_d`;
- at least two identifiable reasoning/subgoal segments;
- valid target ROI T;
- exact O/C semantic quartet;
- no attention-based selection.

Historical bases may be shown only as secondary examples.

---

## D3. Long-Horizon Token Annotation

For every reasoning token before `E_d`, retain the Stage 3C.8 taxonomy and add:

```text
SUBGOAL_START
SUBGOAL_END
EVIDENCE_REFERENCE
INTERMEDIATE_CONCLUSION
ENTITY_SWITCH
RESULT_COMMIT
DISCOURSE_TRANSITION
BOUNDARY
NONE
```

These labels are semantic/structural annotations and are frozen before Phase-D causal rescue scores.

Do not define anchors from attention peaks.

---

## D4. Fixed Temporal Landmark Scan

To avoid cherry-picking arbitrary keywords, define prospective landmark families.

### D4.1 Relative-to-decision landmarks

```text
E_d - 128
E_d - 64
E_d - 32
E_d - 16
E_d - 8
E_d - 4
E_d - 2
E_d - 1
```

when available.

### D4.2 Reasoning-structure landmarks

```text
first subgoal boundary
first target-entity mention
first explicit target-fact mention
first intermediate result
first discourse transition after target evidence
last subgoal boundary before E_d
```

These are annotation-derived, not causal-effect-derived.

---

## D5. Local Acquisition-to-Anchor Assay

For each frozen landmark token `p`, create a local source deficit:

```text
remove target-ROI contribution
over the preceding fixed 4-query window:
[p-4, p-1]
```

using:

```text
all language layers
all heads
target ROI T
```

where the window is valid.

Then at token `p`, restore only its native full-depth K+V cache into the matching suppressed run.

Measure:

```text
local suppression loss
anchor rescue gain
anchor rescue ratio
```

This asks:

> **Does token p consolidate behaviorally useful consequences of visual evidence acquired immediately before it?**

If the local suppression produces essentially no deficit/state divergence, the token is classified as **not evaluable for this local assay**, not as a negative anchor.

---

## D6. Future-Use Assay

A token should not be called a strong checkpoint merely because its state changes.

For each evaluable token `p`, test whether its cache supports a later readout.

Primary downstream readout:

```text
evidence preference at E_d
```

Secondary readouts may include frozen intermediate evidence-use coordinates if already independently annotated.

Restore:

```text
native K+V of p
```

into the locally suppressed run while leaving other token caches suppressed-native.

A token with robust downstream rescue is a **functional carrier candidate**.

---

## D7. Necessity Complement

For the strongest **pre-frozen token categories/landmarks**, run the reverse direction:

```text
native trajectory
+
replace token p cache with matching suppressed cache
```

while leaving the rest of the native trajectory unchanged.

This is a token-cache necessity perturbation.

Run only for frozen categories, not effect-ranked individual positions.

Interpret carefully:

- a null can reflect redundancy/rerouting;
- a positive effect strengthens the checkpoint claim;
- necessity is not required for a token to be a sufficient functional carrier.

---

## D8. Operational Anchor Definition

Do not create one opaque scalar score.

Classify a reasoning token using separate causal criteria.

### A — Acquisition-receiving

The local visual suppression creates a reproducible native-vs-suppressed cache/state difference at the token.

### B — Future-supporting

Native token-cache rescue improves downstream evidence preference.

### C — Necessity-supported

Replacing that token's native cache with its suppressed cache harms downstream evidence.

A strong causal checkpoint satisfies:

```text
A + B
```

with C as additional support.

Do not require C, because redundancy can hide necessity.

---

## D9. Dynamic-Anchor Phenotypes

Classify trajectories prospectively into:

### D-Sparse

A few checkpoint tokens carry most recoverable evidence support.

### D-Repeated

Multiple checkpoint tokens appear at different reasoning/subgoal transitions.

### D-Boundary-Linked

Checkpoints cluster around clause/sentence/subgoal boundaries.

### D-Entity-Linked

Checkpoints cluster around visual-entity or target-entity mentions.

### D-Result-Linked

Checkpoints cluster around numeric/intermediate-result commits.

### D-Recency-Only

Apparent anchors are explained mostly by distance to E_d.

### D-Distributed

No small set of positions behaves as a clean checkpoint, but broad token groups carry evidence.

---

## D10. Direct vs Indirect Route Hypothesis

The VideoLLM excerpt motivates asking whether a checkpoint receives visual information through different routes.

For a confirmed checkpoint `A`, conceptually separate:

```text
Direct:
V → A

Prompt-mediated:
V → Q → A

Prior-reasoning-mediated:
V → R_<A → A

Mixed:
multiple routes
```

Stage 3C.8 does not attempt a complete path decomposition for every anchor.

Instead, for a small frozen set of confirmed checkpoint categories, run **route ablation controls**:

### Direct-access reduction

During the local acquisition window, suppress:

```text
current generated-query → target visual ROI contribution
```

while leaving prior reasoning caches available.

### Prior-reasoning-route reduction

Keep visual access native but replace the frozen immediately preceding reasoning-cache window with its suppressed counterpart where mechanically valid.

### Prompt-route reduction

Only if a checkpoint is in early reasoning and Stage 3B.0-style Q carry is relevant, replace/ablate the relevant Q-side cached source under a frozen rule.

The purpose is to distinguish broad route phenotypes, not to claim a complete causal graph.

Run these only on a small preregistered subset if Phase-D anchor rescue is strong.

---

## D11. Long-Horizon Anchor Density

For each trajectory, report checkpoint locations over normalized reasoning progress:

```text
0–25%
25–50%
50–75%
75–100%
```

and relative to semantic events:

```text
before target mention
at target mention
after target fact
subgoal transition
intermediate result
final evidence use
```

This asks whether anchors are:

- early handoff points;
- repeated refresh points;
- late integration points.

Do not define LOOK/THINK states from anchor density alone.

---

## D12. Anchor-Type Enrichment

After causal checkpoint labels are frozen, test enrichment over:

```text
VISUAL_ENTITY
NUMERIC_LITERAL
INTERROGATIVE
RELATION_OPERATOR
FUNCTION_WORD
DISCOURSE_MARKER
PUNCTUATION
BOUNDARY
SPECIAL_TOKEN
OTHER_CONTENT
```

Also test reasoning-role enrichment:

```text
TARGET_ENTITY_MENTION
INTERMEDIATE_RESULT
SUBGOAL_OPERATOR
DISCOURSE_TRANSITION
BOUNDARY
OTHER
```

Use matched controls for:

- distance to E_d;
- local token density;
- sequence-boundary position;
- token-count/span length.

A raw frequency difference is not sufficient.

---

## D13. What a Positive Result Would Mean

A convincing repeated-anchor result would support:

> **Visual information in long-form reasoning is repeatedly consolidated into dynamically formed textual/reasoning checkpoints whose identities depend on reasoning structure.**

This would extend the current lifecycle from:

```text
visual ROI
→ local retrieval
→ t_pre cache / residual
→ evidence decision
```

to:

```text
visual evidence
→ checkpoint 1
→ intermediate reasoning
→ checkpoint 2
→ later retrieval/integration
→ decision
```

---

## D14. What a Null Would NOT Mean

If no sparse long-horizon anchors appear, do not conclude:

```text
reasoning tokens do not carry visual information
```

Surviving alternatives include:

- carrier information is distributed across spans;
- broad residual state dominates;
- checkpoints are task-specific and not aligned to chosen landmarks;
- the local 4-query suppression misses the relevant acquisition window;
- multiple redundant checkpoints make necessity weak;
- the relevant information is refreshed directly from vision rather than propagated through text.

A null therefore redirects the mechanism; it does not erase the positive Stage 3C.7 carrier result.

---

## D15. Importance Check

Phase D should be retained only if it advances the central paper claim.

It is scientifically valuable if it distinguishes:

```text
single local handoff
vs
repeated dynamic checkpoints over long reasoning
```

It should be dropped or deferred if it becomes only a descriptive keyword-ranking exercise.

The causal anchor claim must remain grounded in source suppression and downstream cache rescue.

---


# 30. Unified Token Carrier Metrics

Use distinct references for each phase.

## Phase A

Reference:

```text
native vs P4-suppressed t_pre deficit
```

## Phase B

Reference:

```text
native vs T16-suppressed deficit
```

## Phase C

Reference:

```text
full-Q cutoff residual gap
```

For carrier `S`:

```text
G_S = rescue / semantic transfer gain
```

Descriptive:

```text
CRR_S = G_S / phase-specific reference
```

Do not clip.

Do not compare CRR numerically across phases as if denominators were identical.

---

# 31. Sparse-vs-Distributed Carrier Analysis

For Phase B and C separately compare:

```text
best single position
top-2 positions
top-4 positions
all positions of a token type
full carrier group
```

Outcome categories:

## Sparse carrier

A small number of positions explain most group rescue.

## Type-distributed carrier

No one position is large, but joint same-type rescue is substantial.

## Broad distributed carrier

Only broad recent/Q group rescue is strong.

## No token-local sufficiency

Even broad token-cache rescue is weak.

This is a valid null and does not negate residual-state mechanisms.

---

# 32. Avoiding Outcome-Based Top-k Overfitting

Do not select top positions on the same bases used for confirmatory top-k claims.

If top-k cumulative rescue is desired:

- use historical 24 as discovery;
- freeze type/position rules;
- confirm on fresh 64.

Primary token-type claims should rely on taxonomy groups and matched controls, not data-mined positions.

---

# 33. Statistical Plan

Primary independent unit:

```text
base_problem_id
```

Tokens are repeated observations, not independent samples.

For each token type:

1. compute per-base type summary;
2. perform cohort inference across bases.

Primary per-base summaries:

```text
mean single-position rescue
max single-position rescue (secondary)
joint type-group rescue
recency-matched type-minus-control rescue
```

Report:

- median;
- mean;
- bootstrap 95% CI;
- positive fraction.

Use Holm correction within each phase's frozen token-type family.

Historical and fresh cohorts are reported separately.

Primary inferential claims require the fresh cohort.

---

# 34. Hierarchical Descriptive Model

As a secondary analysis, fit a mixed/hierarchical model predicting position-level rescue from:

```text
token type
distance to t*
stream
boundary status
visual alignment
reasoning role
```

with:

```text
base_problem_id grouping/random intercept
```

This model is descriptive.

Primary causal claims come from cache-rescue interventions, not regression coefficients.

---

# 35. Main Scientific Outcomes

## O1 — Visual-Entity Carrier Bias

If visually aligned entity tokens show stronger rescue after recency/position controls:

> **Visual evidence preferentially resides in semantically aligned textual anchors.**

## O2 — Boundary / Punctuation Integration

If `?`, `.`, `:`, clause-final, or sentence-final positions are consistently strong:

> **Multimodal information preferentially accumulates at sequence integration boundaries rather than only at lexical entity tokens.**

Do not claim punctuation semantics itself is causal without position controls.

## O3 — Task/Operator Carrier

If interrogatives/relation/subgoal operators are strong:

> **Task-state/operator tokens act as visual-information carriers or access points.**

## O4 — Recency-Dominant Carrier

If distance to `t*` explains rescue and token type adds little:

> **Carrier role is primarily temporal/positional rather than lexical.**

## O5 — Distributed Token Cache

If no class dominates but group rescue is strong:

> **Visual residual is distributed across many token-cache positions.**

## O6 — Phase-Specific Carrier Taxonomy

If prompt/prefill and late-reasoning token types differ:

> **The token positions carrying visual information change across the visual-evidence lifecycle.**

---

# 36. Important Null Interpretation

If `AB` tokens are not stronger than `is` or `?`, do not conclude:

```text
visual alignment is irrelevant
```

Possible explanations include:

- token-span splitting;
- boundary integration;
- distributed group carriage;
- target-specific mechanisms;
- cache interaction.

If punctuation is weak, do not conclude:

```text
boundary states are irrelevant
```

because integrated information may live in residual rather than cache.

Every major null must retain plausible alternative explanations.

---

# 37. Relationship to Attention

Attention is not used for:

- token selection;
- token taxonomy;
- cohort selection;
- carrier ranking.

After causal results freeze, optionally compare carrier strength with natural attention received by that token.

Secondary only.

Do not convert attention into a causal carrier score.

---

# 38. Relationship to Sink

Special/control tokens, including `<|im_start|>`, may appear in the atlas as token classes.

However Stage 3C.8 tests whether their **cached states carry evidence**.

It does **not** manipulate sink attention probability or test sink causality.

A special token can be:

```text
high-attention sink + weak semantic carrier
```

or:

```text
high-attention + strong carrier
```

These are separate questions.

---

# 39. Mechanical Validation

Required checks before fresh primary scoring:

1. exact token indices;
2. exact lexical-span mapping;
3. exact token-type annotations;
4. exact GQA cache layout;
5. exact single-position cache isolation;
6. exact group-cache isolation;
7. visual K/V invariance;
8. current-query invariance where required;
9. future-vision cutoff correctness in Phase C;
10. T16 suppression correctness in Phase B;
11. full-Q positive control;
12. all-recent-cache positive/reference control;
13. self patches exact;
14. deterministic repeats exact;
15. all scores finite.

---

# 40. Prospective Sample Accounting

Record:

```text
screened
edit-valid
completed-correct
strict-E_d valid
ROI valid
prompt-token annotation valid
recent-window valid
retained
```

No retention decision may depend on token carrier effects.

If 64 fresh bases cannot be reached after the frozen screening budget, stop at attained N if:

```text
N >= 56
```

and report the shortfall.

Do not relax inclusion rules to hit N.

---

# 41. Output Structure

```text
outputs/stage3c8/
  config/
    stage3c8_config.json
    cohort_plan.json
    token_taxonomy.json
    span_rules.json
    primary_family.json

  cohort/
    validation_manifest.jsonl
    historical_anchor_manifest.jsonl
    fresh_atlas_manifest.jsonl
    exclusions.jsonl
    sample_accounting.json

  annotations/
    per_token_annotations.jsonl
    lexical_spans.jsonl
    visual_alignment_annotations.jsonl
    reasoning_role_annotations.jsonl

  audit/
    tokenizer_span_audit.json
    cache_layout.json
    position_patch_selectivity.json
    group_patch_selectivity.json
    visual_cache_invariance.json
    phase_b_t16_validation.json
    phase_c_cutoff_validation.json
    self_patch_validation.json
    reproducibility.json

  phase_a_tpre/
    per_base_tpre_rescue.jsonl
    k_only_results.jsonl
    v_only_results.jsonl
    kv_results.jsonl
    token_type_statistics.json

  phase_b_recent/
    all_recent_cache_reference.jsonl
    per_position_rescue.jsonl
    fixed_position_kv_decomposition.jsonl
    span_rescue.jsonl
    type_group_rescue.jsonl
    recency_matched_controls.jsonl

  phase_c_prompt/
    full_q_reference.jsonl
    per_prompt_position_rescue.jsonl
    prompt_span_rescue.jsonl
    prompt_type_group_rescue.jsonl
    structural_controls.jsonl
    gated_type_kv_decomposition.jsonl

  phase_d_anchor/
    gate.json
    long_horizon_manifest.jsonl
    landmark_annotations.jsonl
    local_acquisition_deficits.jsonl
    per_landmark_anchor_rescue.jsonl
    future_use_results.jsonl
    gated_necessity_results.jsonl
    route_ablation_results.jsonl
    anchor_classification.json
    anchor_density.json
    anchor_type_enrichment.json

  analysis/
    historical_vs_fresh_replication.json
    token_type_atlas.json
    position_vs_type_analysis.json
    visual_alignment_analysis.json
    boundary_analysis.json
    sparse_vs_distributed_analysis.json
    phase_specificity_analysis.json
    hierarchical_descriptive_model.json
    figures/

  summaries/
    stage3c8_summary.md
    stage3c8_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3C.7 or earlier artifacts.

---

# 42. Required Figures

At minimum:

1. fresh-cohort `t_pre` rescue by lexical token type;
2. `t_pre` rescue by visual-alignment class;
3. K/V/K+V mechanism by `t_pre` token type;
4. recent-reasoning rescue vs distance to `t*`;
5. recent-reasoning rescue by token type after recency matching;
6. recent-reasoning type-group rescue;
7. semantic-span vs single-token rescue;
8. question-token position carrier heatmap;
9. question-token rescue by token type;
10. visually aligned entity vs matched non-entity prompt tokens;
11. punctuation/boundary vs matched controls;
12. `what / function word / entity / ?` representative examples;
13. sparse-vs-distributed cumulative rescue;
14. prefill vs late-reasoning token-type comparison;
15. historical 24 vs fresh 64 replication;
16. special/control token carrier effects, separately from sink interpretation;
17. long-horizon reasoning timeline with causal checkpoint locations;
18. checkpoint density over normalized reasoning progress;
19. checkpoint enrichment by token type and reasoning role;
20. acquisition-receiving vs future-supporting checkpoint scatter;
21. representative repeated-anchor trajectories;
22. direct/prior-reasoning/prompt route phenotype comparison if the Phase-D route gate is run.

---

# 43. Acceptance Criteria

Stage 3C.8 technically passes if:

1. token taxonomy is frozen before causal token results;
2. lexical-span rules are frozen before scoring;
3. 8-base mechanical validation passes;
4. historical 24 remain anchor/replication only;
5. fresh primary target is 64 and minimum is 56;
6. fresh selection uses no token-carrier effect;
7. exact `t_pre` cache-rescue semantics from Stage 3C.7 are reproduced;
8. Phase-B T16 suppression semantics reproduce Stage 3C.4;
9. Phase-C generation-start cutoff reproduces Stage 3B.0 semantics;
10. full-Q positive control is run;
11. all-recent-cache reference is run;
12. single-position patches are cache-position selective;
13. group patches alter only frozen positions;
14. visual K/V are never donor-patched in token-carrier assays;
15. `base_problem_id` remains the independent unit;
16. recency/position controls are included before token-type claims;
17. split-token semantic spans are analyzed separately;
18. no attention-based token selection occurs;
19. no sink-probability intervention or Stage 4 experiment is started;
20. Phase D runs only if its carrier-signal gate passes;
21. Phase-D landmark definitions are frozen before anchor rescue scores;
22. no attention peak is used to select long-horizon anchor candidates;
23. a checkpoint claim requires causal source-deficit plus downstream token-cache rescue evidence;
24. checkpoint necessity nulls are not interpreted as absence under redundancy;
25. exactly one next-stage recommendation is produced.

Technical PASS does not require one dominant token type.

---

# 44. Stop Condition

After:

- fresh cohort construction;
- complete token/span annotation;
- Phase-A large-sample `t_pre` carrier atlas;
- Phase-B recent-reasoning exhaustive position/type atlas;
- Phase-C prompt/question token atlas;
- matched position/recency controls;
- phase-specific carrier comparison;
- gated Phase-D long-horizon checkpoint analysis if eligible;
- final carrier-taxonomy / anchor classification;
- exactly one recommendation;

**STOP.**

Do not start:

- attention-sink intervention;
- an unconstrained whole-history token search outside the frozen Phase-D landmark design;
- residual feature learning;
- Stage 4 multi-evidence refresh;
- failure analysis.

Return the complete Stage 3C.8 results for review.

The next stage must be chosen only after jointly considering Stage 3C.8 with all prior Stage 2A–3C.7 evidence.
