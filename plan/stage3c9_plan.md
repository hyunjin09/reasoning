# Stage 3C.9 Plan — Dedicated Long-Horizon Causal-Checkpoint Cohort

## 0. Purpose

Stage 3C.9 follows the Stage 3C.8 result:

> **Late reasoning carrier effects are strongly recency-dominant, but the carrier taxonomy is phase-specific and semantically modulated.**

Stage 3C.8 showed that the immediate prior token is a robust carrier, distance-2 retains smaller effects, and distances 4–16 are largely null. The planned long-horizon extension could not run because only 15/64 fresh bases met the frozen long-reasoning cohort gate.

This is a **cohort-feasibility failure, not a scientific null**.

Stage 3C.9 constructs a dedicated cohort whose primary purpose is to answer:

> **During genuinely long-form multimodal reasoning, does visual information repeatedly consolidate into short-lived causal reasoning checkpoints as subgoals and evidence-use events unfold?**

The main alternatives are:

```text
H1 — Repeated dynamic checkpoints
Visual evidence is repeatedly re-established in local reasoning-side carriers.

H2 — Persistent long-range carrier
A small number of earlier token states remain useful over long horizons.

H3 — Mostly direct refresh
Later evidence-use events depend primarily on renewed direct visual retrieval,
with little causal propagation from earlier checkpoints.

H4 — Distributed state
No sparse checkpoint span cleanly mediates the relevant information.
```

---

## 1. Why This Experiment Is Important

This stage directly advances the central project question:

> **How does visual evidence causally enter, move through, remain available within, and get retrieved/refreshed during long-form reasoning?**

Stages 3C.4–3C.8 established a strong local story:

```text
visual retrieval
→ very recent reasoning-token K/V
+ current residual
→ next evidence use
```

What remains unknown is whether this local mechanism occurs only once near the final evidence decision or is **repeated throughout a long reasoning trajectory**.

A positive result would elevate the paper story from one local handoff mechanism to a recurring visual-evidence lifecycle. A negative result is still useful if it cleanly distinguishes persistent memory, renewed direct refresh, and distributed non-token-local state.

---

## 2. Claim-Identifiability Check

Stage 3C.9 must not reduce to a keyword-ranking or attention-peak experiment.

A valid causal-checkpoint claim requires at least:

### A. Source sensitivity
Removing the relevant visual source before a candidate checkpoint creates a measurable downstream evidence deficit or checkpoint-state deficit.

### B. Checkpoint rescue
Restoring the native checkpoint token/span cache into that source-deficient run causally improves the downstream evidence readout.

A stronger checkpoint additionally has:

### C. Necessity support
Replacing the native checkpoint state with its source-deficient counterpart harms downstream evidence use.

Necessity is supporting evidence only, not a required condition, because redundancy can mask necessity.

---

## 3. What a Null Does NOT Establish

A weak checkpoint-rescue effect does not by itself imply that the token/span is irrelevant or that visual information is not propagated through reasoning.

Surviving alternatives include:

- wrong acquisition window;
- state distributed across several nearby tokens;
- residual-stream rather than cache carriage;
- direct visual refresh at the downstream event;
- redundant checkpoints;
- checkpoint lifetime shorter than the chosen readout horizon;
- a semantic event not aligned to a single token.

Therefore Stage 3C.9 includes two source-window sizes, span-level rescue, matched neighboring controls, local and longer-horizon readouts, and gated route decomposition.

---

## 4. Cohort Strategy

This is a **dedicated long-horizon cohort**, not a filtered subset of the Stage 3C.8 atlas.

### Target size

```text
48 unique valid long-horizon bases
```

Minimum:

```text
40
```

Mechanical validation:

```text
8 disjoint bases
```

Optional route-decomposition subset:

```text
16–24 high-quality bases
```

selected by frozen annotation/feasibility rules, never by checkpoint effect size.

---

## 5. Screening Budget

Recommended initial budget:

```text
600 completed model trajectories
```

If yield is lower than expected, extend prospectively up to:

```text
1000 trajectories
```

Do not relax inclusion criteria merely to hit N.

Record:

```text
attempted
completed
correct
long-enough
multi-segment
multi-event
edit-valid
ROI-valid
retained
```

---

## 6. Long-Horizon Inclusion Criteria

A primary base must satisfy all of the following before causal checkpoint scoring:

1. correct completed Qwen3-VL-4B-Thinking trajectory;
2. at least `160` generated reasoning tokens before the final discriminative evidence-use coordinate;
3. at least `3` independently annotated reasoning/subgoal segments;
4. at least `3` candidate evidence-use / integration events;
5. at least `2` candidate events separated by `>= 24` reasoning tokens;
6. valid localized target visual evidence and ROI T;
7. valid O/O_sham/C/C_sham semantic quartet;
8. exact prompt/image token layout across semantic conditions;
9. at least one event before the final 25% of reasoning;
10. no attention-based inclusion.

The key inclusion criterion is **multiple separated reasoning/evidence events**, not raw token length alone.

---

## 7. Event Taxonomy

Candidate events are annotated before causal scoring.

Each event receives orthogonal labels.

### Event role

```text
TARGET_ENTITY_REFERENCE
VISUAL_FACT_REFERENCE
INTERMEDIATE_RESULT
SUBGOAL_START
SUBGOAL_END
DISCOURSE_TRANSITION
ENTITY_SWITCH
RESULT_COMMIT
FINAL_INTEGRATION
OTHER
```

### Evidence relation

```text
SAME_TARGET_EVIDENCE
NEW_VISUAL_ENTITY
NEW_VISUAL_FACT
COMBINATION_OF_PRIOR_FACTS
NO_EXPLICIT_VISUAL_REFERENCE
```

### Temporal location

```text
EARLY
MIDDLE
LATE
```

### Local anchor span

For each event, freeze a semantic span of:

```text
1–8 tokenizer positions
```

Examples:

```text
"AB"
"AB = 3"
"therefore"
"now consider CD"
"the angle is 40"
```

Do not choose the span from attention or causal rescue.

---

## 8. Event Readouts

A long-horizon checkpoint may be useful locally even if later reasoning refreshes the same evidence.

Every event therefore has two readouts.

### Local-use readout
The first independently annotated downstream token/span where the event's visual evidence is behaviorally used.

Preferred distance:

```text
1–32 tokens after the candidate checkpoint
```

### Final-use readout
The frozen final evidence-preference coordinate:

```text
E_d
```

Primary checkpoint inference uses the **local-use readout**. Final-use is secondary and measures persistence.

---

## 9. Evidence Scoring

For each event `e`, store:

```text
D_native(e)
D_supp(e)
D_rescue(e)
```

for both local-use and final-use readouts.

O and C are scored separately and sign-aligned only before within-base aggregation.

Unnormalized score change remains primary. Rescue ratios are descriptive and unclipped.

---

# PHASE A — EVENT-LOCAL SOURCE SENSITIVITY

## 10. Core Question

> **Was visually derived information causally acquired or refreshed shortly before this candidate checkpoint?**

For every annotated event span starting at position `p`, create two source-deficient runs.

### W8

```text
queries [p-8, p-1]
all language layers
all logical heads
target ROI T contribution → 0
```

### W16

```text
queries [p-16, p-1]
all language layers
all logical heads
target ROI T contribution → 0
```

when available.

These windows are frozen prospectively. Do not choose W8 vs W16 per event based on the larger effect.

---

## 11. Source-Sensitivity Metrics

For each event:

```text
L8_local
L16_local
L8_final
L16_final
```

where:

```text
L = D_native - D_supp
```

Primary source-sensitivity status is based on local-use loss.

Events with negligible local loss are classified as:

```text
SOURCE-INSENSITIVE UNDER TESTED WINDOW
```

not automatically “non-visual.”

---

## 12. Why Two Windows Matter

Stage 3C.8 showed strong recency effects, but acquisition timing can vary.

```text
W8  = local acquisition / refresh assay
W16 = broader nearby-source assay
```

Neither is treated as a unique acquisition interval.

---

# PHASE B — CAUSAL CHECKPOINT RESCUE

## 13. Core Question

> **Does the candidate event span functionally carry the consequence of the preceding visual-source manipulation?**

For each event and source window, patch the matching native event-span K/V cache into the source-deficient recipient.

Primary rescue:

```text
full-depth native K+V
for all tokenizer positions in the frozen event span
```

All other caches remain source-deficient recipient-native. Visual caches are never donor-patched.

---

## 14. Single-Token Localization

After span-level rescue is scored, exhaustively patch each constituent token position separately.

This is secondary localization.

Do not redefine the event span from the best-performing token.

Report:

```text
best single token
cumulative constituent-token rescue
full span
```

with appropriate caution.

---

## 15. Matched Neighbor Controls

For every event span, freeze a matched control span:

- same number of tokenizer positions;
- within `±8` reasoning tokens where possible;
- not part of the annotated event;
- same stream;
- no attention-based matching.

Compare:

```text
event-span rescue
vs
neighbor-span rescue
```

This separates checkpoint identity from pure recency.

---

## 16. Checkpoint Classification

For source window `W`:

### C0 — Not source-sensitive
No meaningful local-use deficit under source suppression.

### C1 — Source-sensitive, no span rescue
Visual source matters locally, but the tested event span does not cleanly carry the deficit.

### C2 — Functional checkpoint
Source-sensitive and native event-span rescue robustly improves the local-use readout.

### C3 — Persistent checkpoint
C2 plus meaningful rescue remains at final `E_d`.

Primary long-horizon claims use C2/C3.

---

# PHASE C — CHECKPOINT LIFETIME AND REPEATED FORMATION

## 17. Why This Phase Is Central

Stage 3C.8 found that reasoning-token carriage is sharply recency-dominant.

Therefore the key long-horizon hypothesis is not:

```text
one early checkpoint persists forever
```

but:

```text
short-lived checkpoints are repeatedly re-established
```

Stage 3C.9 must directly test this.

---

## 18. Lifetime Readouts

For each confirmed C2 checkpoint, evaluate rescue at the next available independently annotated downstream event/readout in bins:

```text
1–8 tokens
9–16
17–32
33–64
65+
```

Also evaluate at:

```text
next visual-evidence event
final E_d
```

Do not create arbitrary pseudo-readouts with no semantic evidence target.

---

## 19. Lifetime Phenotypes

### L-Short
Strong local rescue, little/no rescue beyond the next 16–32 tokens.

### L-Medium
Rescue survives 33–64 tokens.

### L-Persistent
Rescue remains useful at 65+ tokens or final `E_d`.

### L-Replaced
Early checkpoint effect decays, but a later checkpoint for the same evidence becomes strong.

The L-Replaced phenotype is especially important for the repeated-refresh hypothesis.

---

## 20. Repeated-Checkpoint Criterion

A trajectory is classified as:

```text
REPEATED_CHECKPOINT
```

if it contains at least:

```text
2 distinct C2/C3 checkpoints
```

that are:

- separated by `>= 24` reasoning tokens;
- associated with independently annotated events;
- non-overlapping token spans.

Report the fraction of fresh bases satisfying this criterion, plus:

```text
0 checkpoint
1 checkpoint
2 checkpoints
3+ checkpoints
```

Do not require repeated checkpoints as a technical pass condition.

---

## 21. Same-Evidence Reinstatement

For trajectories with two separated checkpoints tied to:

```text
SAME_TARGET_EVIDENCE
```

test whether the earlier checkpoint has decayed before the later one becomes active.

A strong pattern would be:

```text
checkpoint A:
local rescue strong
long-horizon rescue weak

checkpoint B:
local rescue strong again
```

This supports **reinstantiation / refresh rather than persistent long-range token storage**.

---

# PHASE D — ROUTE DECOMPOSITION BETWEEN CHECKPOINTS

## 22. Gate

Run only if at least:

```text
16 fresh bases
```

contain two confirmed separated checkpoints.

Freeze the first eligible pair per base by annotation order, not rescue magnitude.

---

## 23. Core Question

For a later checkpoint `B`, how does visual information reach it?

Candidate routes:

```text
Direct visual refresh:
V → B

Prior-checkpoint propagation:
A → B

Mixed:
V → B + A → B
```

This adapts the direct-vs-indirect information-flow idea from the user-provided VideoLLM excerpt to long-form reasoning without assuming that the same route structure must hold here.

---

## 24. Direct-Route Intervention

Immediately before checkpoint B:

```text
suppress target-ROI contribution
over frozen W8
```

while leaving checkpoint A and intervening reasoning caches native.

Measure:

```text
B local-use deficit
B checkpoint-state divergence
```

---

## 25. Prior-Checkpoint Route Intervention

Keep visual access before B native.

Replace checkpoint A's native K+V span cache with its matching W8-source-deficient version.

All other caches remain native.

Measure the effect on:

```text
checkpoint B local-use score
and
B native-vs-perturbed cache/state
```

A null here does not prove no indirect route because information may already have propagated into intervening states.

---

## 26. Short Prior-History Route Intervention

To reduce the limitation above, include a broader fixed route intervention:

```text
previous confirmed checkpoint A
through the next 8 reasoning-token cache positions
```

replace with the corresponding source-deficient caches where mechanically valid.

This is a stronger test of recent propagated state.

Do not expand the history window post hoc.

---

## 27. Joint Route Intervention

Combine:

```text
Direct W8 visual suppression before B
+
Prior-history source-deficient cache replacement
```

Compare:

```text
Direct only
Prior route only
Joint
Native
```

Primary inference uses unnormalized score changes.

Do not interpret algebraic differences as unique path fractions.

---

## 28. Route Phenotypes

### R-Direct
Direct visual suppression strongly affects B; prior-route perturbation is weak.

### R-Inherited
Prior-route perturbation strongly affects B; direct suppression is weak.

### R-Mixed
Both have robust effects.

### R-Redundant
Single perturbations are weak but joint perturbation is large.

### R-Unresolved
No clean route decomposition under tested interventions.

R-Unresolved is a valid scientific outcome.

---

# PHASE E — ANCHOR TYPE AND STRUCTURE ENRICHMENT

## 29. Why This Comes After Causal Checkpoint Identification

Stage 3C.8 showed that no universal token taxonomy should be assumed.

Therefore Stage 3C.9 first identifies causal checkpoints and only then asks what types they are.

---

## 30. Enrichment Labels

Use the frozen Stage 3C.8 taxonomy:

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

plus reasoning roles:

```text
TARGET_ENTITY_MENTION
INTERMEDIATE_RESULT
SUBGOAL_OPERATOR
DISCOURSE_TRANSITION
BOUNDARY
RESULT_COMMIT
OTHER
```

---

## 31. Matched Enrichment Controls

Every checkpoint type comparison must control for:

- distance to local-use readout;
- normalized reasoning progress;
- span length;
- local token density;
- boundary position.

Do not claim “punctuation is an anchor” from raw counts.

---

## 32. Primary Long-Horizon Questions

Stage 3C.9 should answer:

1. Do causal checkpoints appear repeatedly within one long reasoning trajectory?
2. Are checkpoint effects mostly local/short-lived or persistent?
3. Does the same visual evidence get re-instantiated at later checkpoints?
4. Are later checkpoints driven by direct visual refresh, prior reasoning propagation, or both?
5. After recency/structure controls, are any token or reasoning-role classes enriched?
6. Does the mechanism differ across early, middle, and late reasoning?

---

## 33. Primary Statistical Unit

Primary independent unit:

```text
base_problem_id
```

Events are repeated observations within a base.

Do not treat hundreds of event tokens as independent samples.

For event-level analyses:

- compute per-base summaries;
- use clustered/bootstrap inference over bases;
- report mixed-effects models only as secondary descriptive analysis.

---

## 34. Primary Metrics

Per base report:

```text
number of annotated events
number of source-sensitive events
number of C2/C3 checkpoints
repeated-checkpoint status
median local checkpoint rescue
median final checkpoint rescue
checkpoint lifetime distribution
```

Across bases report median, mean, bootstrap 95% CI, and positive fraction.

---

## 35. Main Scientific Outcomes

### O1 — Repeated Short-Lived Checkpoints
Multiple separated C2/C3 checkpoints occur within many trajectories, with predominantly short local lifetimes.

Interpretation:

> **Visual evidence is repeatedly consolidated into transient reasoning-side checkpoints.**

### O2 — Persistent Checkpoint Memory
Earlier checkpoints remain causally useful over long horizons.

Interpretation:

> **Some reasoning-token states act as longer-lived visual memory carriers.**

### O3 — Direct Visual Refresh Dominance
Later checkpoints are source-sensitive to renewed local visual access but insensitive to earlier checkpoint perturbation.

Interpretation:

> **Long reasoning repeatedly refreshes visual evidence directly rather than propagating one persistent token memory.**

### O4 — Mixed Direct + Propagated Flow
Both direct visual access and prior reasoning state contribute to later checkpoints.

Interpretation:

> **Checkpoint formation combines renewed retrieval with propagated reasoning state.**

### O5 — Distributed / No Clean Checkpoint
Visual suppression matters, but no small annotated span reliably rescues the deficit.

Interpretation:

> **Behaviorally relevant visual information is distributed across broader state rather than discrete token checkpoints.**

---

## 36. What Would Be a Strong Paper-Level Result?

A particularly strong pattern would be:

```text
early checkpoint:
local rescue strong, long-horizon rescue decays

later same-evidence checkpoint:
local rescue becomes strong again

direct visual suppression before later checkpoint:
large effect

prior-checkpoint perturbation:
smaller but nonzero effect
```

This would support:

> **Visual evidence is not continuously broadcast through long-form reasoning. It is locally retrieved, consolidated into short-lived reasoning-side carriers, and re-established at later causal checkpoints as reasoning demands change.**

This claim is stronger and more specific than showing repeated attention peaks.

---

## 37. Important Alternative Result

If instead:

```text
early checkpoint rescue remains strong at distant readouts
and
later direct visual suppression has little effect
```

then the project should update toward:

> **persistent reasoning-side visual memory**

rather than forcing a refresh story.

The plan must allow this result.

---

## 38. Technical Validation

Before primary scoring validate:

1. exact event/span indices;
2. exact local-use readout indices;
3. exact O/C sign alignment;
4. W8/W16 suppression isolation;
5. target ROI only;
6. all-layer/all-head contribution partition;
7. exact event-span K/V positions;
8. GQA cache layout;
9. visual K/V invariance during cache rescue;
10. non-event cache invariance;
11. matched-neighbor isolation;
12. route-intervention ordering;
13. native→native self patches;
14. suppressed→suppressed self patches;
15. deterministic replay;
16. finite scores.

---

## 39. Validation Cohort

Use:

```text
8 disjoint validation bases
```

with at least:

```text
2 annotated events per base
```

Validation must cover W8 suppression, W16 suppression, event-span rescue, single-token rescue, matched-neighbor rescue, local-use scoring, final-use scoring, and route intervention on at least 3 eligible examples.

Do not use validation effect sizes to select primary event types.

---

## 40. Sample Feasibility Rule

If fewer than 40 valid long-horizon bases are obtained after the full screening budget:

- do not reinterpret this as a mechanistic null;
- stop the primary Stage 3C.9 inference;
- report cohort feasibility;
- preserve all annotation/screening outputs.

If `N >= 40`, proceed.

---

## 41. Phase-D Feasibility Rule

If fewer than 16 bases contain two confirmed separated checkpoints:

```text
do not run route decomposition
```

This is a gated feasibility outcome only.

Do not infer that direct/indirect routes do not exist.

---

## 42. Relationship to Stage 3C.8

Stage 3C.8 established:

```text
late token carriage is strongly recency-dominant
```

Stage 3C.9 asks whether long reasoning solves that limitation by:

```text
repeatedly creating new local checkpoints
```

rather than maintaining one distant token carrier.

This is the key cross-stage link.

---

## 43. Relationship to the VideoLLM Checkpoint Idea

The user-provided VideoLLM excerpt motivates the hypothesis that specific textual positions can act as information-integration checkpoints and that different prompt structures may induce direct or indirect routes.

Stage 3C.9 does not assume temporal keywords/options are the relevant mechanism in Thinking MLLMs.

Instead it asks:

> **Does long reasoning dynamically establish reasoning-dependent multimodal checkpoints, and are later checkpoints reached through direct visual refresh, propagated reasoning state, or both?**

---

## 44. Attention Boundary

Attention is never used to:

- select the cohort;
- define events;
- choose checkpoint spans;
- rank checkpoint candidates;
- choose route pairs.

After all causal results freeze, attention/QK/sink measurements may be overlaid descriptively.

No sink manipulation occurs in Stage 3C.9.

---

## 45. Optional Descriptive Overlay

After causal checkpoint labels freeze, compare checkpoints vs matched non-checkpoints on:

```text
target ROI attention density
target QK cosine
alphaV norm
candidate <|im_start|> sink mass
```

This asks whether the Stage 3C.1/3C.2 retrieval phenotype recurs at confirmed long-horizon checkpoints.

Secondary only.

---

## 46. Output Structure

```text
outputs/stage3c9/
  config/
    stage3c9_config.json
    cohort_rules.json
    event_taxonomy.json
    source_windows.json
    route_rules.json
    primary_family.json

  cohort/
    screening_accounting.json
    validation_manifest.jsonl
    primary_manifest.jsonl
    exclusions.jsonl

  annotations/
    reasoning_segments.jsonl
    events.jsonl
    event_spans.jsonl
    local_use_readouts.jsonl
    evidence_relation_labels.jsonl

  audit/
    event_index_audit.json
    readout_index_audit.json
    suppression_partition_audit.json
    cache_layout.json
    span_patch_selectivity.json
    neighbor_patch_selectivity.json
    route_patch_order.json
    self_patch_validation.json
    reproducibility.json

  phase_a_source/
    w8_source_sensitivity.jsonl
    w16_source_sensitivity.jsonl
    source_statistics.json

  phase_b_checkpoint/
    event_span_rescue.jsonl
    single_token_localization.jsonl
    neighbor_controls.jsonl
    checkpoint_classification.json

  phase_c_lifetime/
    lifetime_readouts.jsonl
    repeated_checkpoint_classification.json
    same_evidence_reinstatement.jsonl

  phase_d_routes/
    gate.json
    direct_route.jsonl
    prior_checkpoint_route.jsonl
    short_history_route.jsonl
    joint_route.jsonl
    route_classification.json

  phase_e_enrichment/
    checkpoint_type_enrichment.json
    reasoning_role_enrichment.json
    matched_enrichment_controls.jsonl

  secondary/
    attention_qk_overlap.json
    sink_overlap.json

  analysis/
    long_horizon_checkpoint_summary.json
    repeated_checkpoint_analysis.json
    lifetime_analysis.json
    route_analysis.json
    target_heterogeneity.json
    figures/

  summaries/
    stage3c9_summary.md
    stage3c9_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3C.8 or earlier artifacts.

---

## 47. Required Figures

At minimum:

1. cohort screening funnel;
2. event locations over normalized reasoning time;
3. W8/W16 source sensitivity by event;
4. checkpoint span rescue vs matched neighbor;
5. local-use vs final-use rescue;
6. checkpoint count per trajectory;
7. repeated-checkpoint fraction;
8. checkpoint lifetime distribution;
9. same-evidence reinstatement examples;
10. early/middle/late checkpoint rescue;
11. checkpoint type enrichment after matching;
12. reasoning-role enrichment;
13. direct vs prior-route vs joint effects if Phase D runs;
14. route phenotype distribution;
15. representative long reasoning timelines with 2–3 causal checkpoints;
16. optional causal-checkpoint vs attention/QK phenotype overlay.

---

## 48. Acceptance Criteria

Stage 3C.9 technically passes if:

1. cohort rules are frozen before causal scoring;
2. at least 40 valid long-horizon bases are retained;
3. event taxonomy and spans are frozen before checkpoint rescue;
4. local-use readouts are frozen before causal scoring;
5. no attention-based selection occurs;
6. W8 and W16 source windows are both prospectively scored;
7. source suppression alters only target-ROI contribution;
8. event-span rescue patches only the frozen span cache;
9. matched-neighbor controls are predeclared;
10. single-token localization does not redefine event spans;
11. local-use readout is primary;
12. final-use readout is secondary;
13. repeated-checkpoint classification requires two separated causal checkpoints;
14. route decomposition runs only if its feasibility gate passes;
15. route pairs are selected by annotation order, not effect size;
16. necessity nulls are not overinterpreted under redundancy;
17. rescue ratios are unclipped and not unique fractions;
18. event/target heterogeneity remains visible;
19. no sink intervention or Stage 4/failure experiment is started;
20. exactly one next-stage recommendation is written.

Technical PASS does not require repeated checkpoints or a strong route effect.

---

## 49. Stop Condition

After:

- dedicated long-horizon cohort construction;
- frozen segment/event annotation;
- W8/W16 source sensitivity;
- event-span checkpoint rescue;
- matched-neighbor controls;
- checkpoint lifetime analysis;
- repeated-checkpoint classification;
- gated route decomposition if feasible;
- type/role enrichment;
- final scientific classification;
- exactly one next-stage recommendation;

**STOP.**

Do not start:

- attention-sink causality;
- residual-feature/subspace learning;
- unconstrained whole-history search;
- Stage 4 multi-evidence refresh;
- failure analysis.

Return the complete Stage 3C.9 result for review.

The next experiment must be chosen only after jointly considering Stage 3C.9 with Stages 2A–3C.8, and a weak result in one intervention must not be treated as sufficient reason to abandon the broader long-horizon checkpoint hypothesis.
