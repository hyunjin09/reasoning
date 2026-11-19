# Stage 3C.9R Plan — Same-Path Validity Repair for Long-Horizon Causal Checkpoints

## 0. Purpose

Stage 3C.9 is an immutable technical PASS with an important post-hoc validity concern:

```text
Phase A source scoring
vs
Phase B source/rescue scoring
```

used different effective execution shapes, and the frozen source-sensitive gate was unstable across those paths.

Observed instability:

```text
33 rescored event-window combinations
median absolute per-condition source-loss difference = 0.12363
24 / 33 source gates changed at the frozen 0.05 threshold
```

At the same time, several results were stable:

```text
same-path replay: exact
mechanical validation: PASS
0 / 48 repeated-checkpoint bases
under effect floors 0.025, 0.05, 0.10, 0.15
```

Therefore Stage 3C.9R is **not a new cohort expansion** and does not introduce a new scientific hypothesis.

Its purpose is:

> **Recompute the entire frozen long-horizon checkpoint assay under one canonical A6000 execution path so that source deficit and checkpoint rescue are numerically comparable within the same execution semantics.**

The main scientific question is unchanged:

> **Do sparse semantic event spans repeatedly function as causal visual-information checkpoints over long-form reasoning?**

---

## 1. Why This Repair Is Necessary for the Paper

The exact number of Stage 3C.9 C2/C3 checkpoints is currently path-sensitive.

That means the paper should not rely on:

```text
"exactly two checkpoints"
```

until the source-deficit and rescue measurements are evaluated under one fixed execution path.

However, Stage 3C.9 already provides a potentially important negative result:

```text
0 / 48 repeated sparse checkpoint bases
```

The repair is necessary to determine whether this negative remains stable when:

```text
source loss
and
span rescue
```

are computed in the same numerical execution regime.

This is a validity repair, not a search for more positives.

---

## 2. What This Experiment Can Establish

Stage 3C.9R can establish whether, on the exact frozen long-horizon cohort:

1. source-sensitive event windows remain source-sensitive under one canonical path;
2. frozen semantic event spans causally rescue those source deficits;
3. any base contains two separated causal checkpoints;
4. sparse event-span checkpoints are common, rare, or absent under same-path scoring;
5. isolated checkpoints are short-lived or persistent where downstream readouts exist.

---

## 3. What a Null Does NOT Establish

If event-span rescue remains weak, do **not** conclude:

```text
visual information is absent from long reasoning
```

or:

```text
reasoning-side propagation does not exist
```

Surviving alternatives include:

- visual information is distributed across multiple nearby tokens;
- residual-stream state matters more than semantic event-span cache;
- the relevant acquisition window is not W8/W16;
- the model refreshes visual evidence directly rather than propagating sparse token checkpoints;
- checkpoints are redundant and necessity is masked;
- local state is causal but not aligned to annotated semantic spans.

The repair only tests the sparse semantic checkpoint hypothesis under the frozen Stage 3C.9 design.

---

## 4. Immutable Inputs

Do not change any of the following:

```text
48 frozen primary bases
8 mechanical validation bases
3 frozen semantic events per primary base
event ordering
event spans
event taxonomy
local-use readouts
final E_d readouts
O/O_sham/C/C_sham image quartets
target ROI mappings
W8 source window
W16 source window
matched-neighbor spans
0.05 primary effect floor
checkpoint classification rules
repeated-checkpoint separation >= 24 reasoning tokens
```

No new event may be added.

No event span may be edited.

No base may be excluded because of Stage 3C.9R effect size.

---

## 5. Canonical Numerical Environment

Use the A6000 platform validated by calibration v2:

```text
hardware: frozen A6000 pool
canonical path: fixed repaired streaming cached execution
generated-token chunk size: 2048
allocator-cache release between chunks: fixed
dtype: BF16
attention implementation: unchanged
model/tokenizer: unchanged
```

Every scientific condition in Stage 3C.9R must use this exact path.

No per-example or per-arm chunk switching is allowed.

---

## 6. Core Repair Principle

For every frozen:

```text
base
event
source window
semantic condition
```

compute all quantities in one execution family:

```text
Native
Source-suppressed
Event-span rescued
Matched-neighbor rescued
```

The same source-suppressed recipient state must be used as the baseline for both:

```text
source loss
and
rescue gain
```

Thus:

```text
L = D_native - D_suppressed
G_event = D_event_rescue - D_sressed
G_neighbor = D_neighbor_rescue - D_suppressed
```

must all be produced with the same canonical path.

Do not import Phase A source denominators from Stage 3C.9.

Do not mix Stage 3C.9 Phase A and Phase B scores in any primary Stage 3C.9R result.

---

## 7. Score All Frozen Events — No Source Pre-Gate

Stage 3C.9 used a source-sensitive gate before checkpoint rescue scoring.

Stage 3C.9R should instead score the full frozen event set prospectively:

```text
48 bases × 3 events = 144 events
```

For both:

```text
W8
W16
```

when mechanically valid.

For every event-window pair, compute:

```text
native
suppressed
event-span rescue
neighbor rescue
```

before applying any scientific classification.

This prevents numerical gate instability from changing which events receive rescue scoring.

---

## 8. Why Removing the Computational Pre-Gate Is Valid

This does **not** change the scientific checkpoint definition.

The original checkpoint rule still requires a meaningful source deficit.

The change is only:

```text
score first
classify later
```

instead of:

```text
gate first
score selected events later
```

The scientific rule remains frozen.

This is a repair of numerical comparability, not a post-hoc search.

---

# PHASE A — SAME-PATH SOURCE SENSITIVITY

## 9. Source Conditions

For every frozen event `e`, run:

### W8

```text
queries [p-8, p-1]
target ROI contribution removed
all 36 language layers
all 32 logical heads
```

### W16

```text
queries [p-16, p-1]
same suppression semantics
```

where valid.

---

## 10. Source Metrics

For O and C separately:

```text
L_O(W) = D_native_O - D_suppressed_O
L_C(W) = sign-aligned(D_native_C - D_suppressed_C)
```

Then compute the frozen within-event aggregate.

Store:

```text
mean source loss
median/sign-aligned source loss
O/C directionality
```

Primary source floor remains:

```text
0.05 nats / candidate token
```

---

## 11. Same-Path Source Stability

Compare Stage 3C.9R same-path source losses with:

```text
Stage 3C.9 Phase A
Stage 3C.9 Phase B
```

for diagnosis only.

Primary Stage 3C.9R classification uses Stage 3C.9R scores only.

Report:

```text
gate agreement
absolute score difference
sign agreement
```

This comparison is descriptive and must not alter the classification rule.

---

# PHASE B — SAME-PATH CHECKPOINT RESCUE

## 12. Event-Span Rescue

For every frozen event-window pair:

```text
source-suppressed recipient
+
matching native event-span full-depth K+V
```

Patch only the frozen semantic event span.

All other caches remain recipient-native.

Visual K/V remain source-suppressed recipient-native.

---

## 13. Matched-Neighbor Rescue

Using the exact predeclared neighbor span:

```text
source-suppressed recipient
+
native matched-neighbor full-depth K+V
```

Same number of tokenizer positions as event span where originally defined.

No new neighbor may be selected based on Stage 3C.9R results.

---

## 14. Rescue Metrics

For every event-window pair:

```text
G_event = D_event_rescue - D_suppressed
G_neighbor = D_neighbor_rescue - D_suppressed
```

Descriptive rescue ratio:

```text
RR_event = G_event / L
```

Do not clip.

Do not interpret RR as a unique information fraction.

---

## 15. Frozen Checkpoint Rule

Retain the original Stage 3C.9 C2/C3 rule.

A frozen event span is a causal checkpoint only if all required conditions hold under the same Stage 3C.9R path, including:

```text
1. same-window source deficit satisfies frozen source criterion
2. event-span rescue is positive in both O and C
3. mean rescue >= 0.05 nats / candidate token
4. median unclipped RR >= 0.25
5. event-span rescue > matched-neighbor rescue
```

Do not loosen any criterion because the original checkpoint yield was small.

---

## 16. Primary Two-Dimensional Causal Profile

Do not rely only on binary classes.

For every event-window pair, report:

```text
x-axis: same-path source loss L
y-axis: same-path event-span rescue G_event
```

with matched-neighbor rescue shown separately.

This distinguishes:

### Type A

```text
source loss high
rescue high
```

Strong checkpoint candidate.

### Type B

```text
source loss high
rescue low
```

Visual source matters, but the frozen event span is not a sufficient sparse carrier.

### Type C

```text
source loss low
rescue high
```

Potential intervention/state mismatch; interpret cautiously.

### Type D

```text
source loss low
rescue low
```

No evidence under the tested local assay.

This profile is scientifically more informative than checkpoint count alone.

---

# PHASE C — REPEATED CHECKPOINT CLASSIFICATION

## 17. Repeated-Checkpoint Rule

Keep the original frozen definition:

A base is:

```text
REPEATED_CHECKPOINT
```

if it contains at least:

```text
2 distinct C2/C3 event spans
```

that are:

```text
non-overlapping
separated by >= 24 reasoning tokens
```

Do not change the rule to increase pair yield.

---

## 18. Primary Long-Horizon Result

Report:

```text
0 checkpoint bases
1 checkpoint bases
2 checkpoint bases
3 checkpoint bases
repeated-checkpoint bases
```

The main question is:

> **Does the same-path repair change the Stage 3C.9 conclusion of zero repeated sparse checkpoints?**

---

# PHASE D — CHECKPOINT LIFETIME

## 19. Local vs Long-Horizon Readout

For every confirmed checkpoint with a distinct downstream readout, evaluate the frozen:

```text
local-use readout
next independently annotated downstream readout
final E_d readout
```

No arbitrary pseudo-readouts may be introduced.

---

## 20. Lifetime Classes

Retain:

```text
L-Short
L-Medium
L-Persistent
L-Replaced
```

using the original Stage 3C.9 semantics.

A checkpoint with no distinct downstream/final readout must be:

```text
RIGHT-CENSORED
```

and not automatically called L-Short.

This explicitly corrects the interpretive issue noted for base 149.

---

## 21. Base 38 as Frozen Positive Reference

Base 38 is not used to tune the repair.

Report it as a frozen positive reference because Stage 3C.9 found:

```text
confirmed local checkpoint
downstream readout 2342 tokens later
rescue = 0.03095
final rescue = -0.09374
```

Stage 3C.9R should determine whether its checkpoint classification and short-lifetime interpretation survive the same-path repair.

Do not require base 38 to remain positive as a technical PASS criterion.

---

# PHASE E — THRESHOLD SENSITIVITY

## 22. Primary Threshold

Primary checkpoint classification remains:

```text
0.05 nats / candidate token
```

No threshold tuning is allowed.

---

## 23. Frozen Sensitivity Grid

After primary results freeze, report checkpoint and repeated-checkpoint counts at:

```text
0.025
0.05   ← primary
0.10
0.15
```

Only the effect floor changes.

All other classification rules remain identical.

The most important robustness question is:

```text
Does repeated-checkpoint count remain stable?
```

---

# PHASE F — OPTIONAL NECESSITY RECHECK

## 24. Gate

Run necessity rechecks only if Stage 3C.9R yields at least:

```text
4 robust C2/C3 checkpoints
```

across the cohort.

If fewer than 4:

```text
do not run necessity
```

because it will not materially affect the paper story.

---

## 25. Necessity Intervention

For frozen confirmed checkpoint spans:

```text
native trajectory
+
replace event-span K+V with matching source-suppressed span K+V
```

Measure local-use effect.

Interpretation:

- positive harm strengthens checkpoint evidence;
- null may reflect redundancy;
- necessity is not required for checkpoint status.

---

## 26. Route Decomposition Gate

Do **not** run Stage 3C.9 route decomposition merely because one or two checkpoints survive.

Run only if:

```text
>= 16 bases
```

contain two confirmed separated same-path checkpoints, preserving the original feasibility logic.

If not:

```text
route decomposition = NOT RUN
```

Do not lower the gate.

---

## 27. Critical Outcome Branches

### R1 — Repeated sparse checkpoints remain absent

If:

```text
0 or near-zero repeated-checkpoint bases
```

remain stable under same-path scoring and threshold sensitivity:

> **The long-horizon sparse semantic-checkpoint hypothesis is not supported under the tested W8/W16 event-span assay.**

This does not imply absence of visual processing.

The next scientific priority should be **Retrieval Trigger**, not cohort expansion.

### R2 — Source-sensitive events are common but span rescue is rare

Interpretation:

> **Visual evidence is causally relevant around long-horizon events, but it is not generally consolidated into the tested sparse semantic event-span K/V representation.**

This favors:

```text
distributed local state
direct visual refresh
or broader recent-token/residual carriage
```

Again, next priority should be **Retrieval Trigger / local state mechanism**, not pair-yield hunting.

### R3 — Robust repeated checkpoints emerge

If same-path scoring reveals multiple repeated-checkpoint bases:

> **Repeated sparse causal checkpoints are supported.**

Before expanding the cohort, first run the already-defined route decomposition on eligible pairs.

### R4 — Checkpoint classification remains highly threshold-sensitive

If source/rescue classifications remain unstable even within one canonical path:

> **The sparse checkpoint assay itself is too numerically fragile for a central paper claim.**

Do not expand the cohort.

Move the long-horizon story to a more continuous/window-level causal measure.

---

## 28. Why Cohort Expansion Is Not the Default Next Step

Stage 3C.9R must explicitly prevent:

```text
few checkpoint pairs
→ collect more data until pairs appear
```

Only consider expansion if:

1. same-path checkpoint classification is stable;
2. repeated checkpoints are already present but pair yield is too small for route statistics;
3. expansion rules can remain score-blind.

Otherwise expansion has low marginal scientific value.

---

## 29. Relationship to the Paper Story

If R1/R2 occurs, the Stage 3C story becomes:

```text
visual retrieval is causal
→ target evidence is routed through QK/Value mechanisms
→ local visual support is redundant across layers/time
→ evidence enters very recent reasoning K/V + residual
→ carrier role is recency-dominant
→ sparse semantic token checkpoints do not generally persist/recur over long reasoning
```

This motivates the next missing mechanism:

```text
What in reasoning state triggers renewed visual retrieval?
```

That is the Retrieval Trigger question.

---

## 30. Retrieval Trigger Deferral

Do not run the Retrieval Trigger experiment inside Stage 3C.9R.

If R1/R2 is obtained, recommend:

```text
GO — Retrieval Trigger
```

for review.

---

## 31. Sink Causality Deferral

Do not manipulate the candidate `<|im_start|>` sink.

Sink causality remains secondary unless the checkpoint/trigger story later shows that sink release is repeatedly aligned with behaviorally necessary retrieval.

---

## 32. Statistical Unit

Primary independent unit:

```text
base_problem_id
```

Events are repeated observations within bases.

Do not treat 144 event rows as independent samples.

Use:

- per-base summaries;
- base-clustered bootstrap;
- event-level descriptive plots.

---

## 33. Primary Summary Statistics

Report per base:

```text
number of source-sensitive events
number of C2/C3 checkpoints
repeated-checkpoint status
median source loss
median event-span rescue
median event-minus-neighbor rescue
```

Across bases report:

```text
median
mean
bootstrap 95% CI
positive fraction
```

---

## 34. Mechanical Validation

Before primary rerun, validate on the frozen 8-base mechanical set:

1. canonical A6000 path = calibration-v2 frozen path;
2. 2048 generated-token chunking is fixed;
3. native/suppressed/rescue/neighbor all use same path;
4. W8/W16 indices exact;
5. target ROI contribution suppression isolated;
6. event-span K/V positions exact;
7. neighbor-span positions exact;
8. GQA K/V layout exact;
9. visual K/V invariant during cache rescue;
10. non-target caches invariant;
11. self native→native exact;
12. self suppressed→suppressed exact;
13. deterministic replay exact/within frozen tolerance;
14. local/final readout indices exact;
15. all outputs finite.

---

## 35. Acceptance Criteria

Stage 3C.9R technically passes if:

1. original 48-base cohort is reused exactly;
2. original 144 semantic events are reused exactly;
3. no new event/span is selected;
4. all W8/W16 source scores use one canonical path;
5. all event/neighbor rescues use the same canonical path;
6. all frozen event-window pairs are scored before classification;
7. no Phase A pre-gate controls whether rescue is computed;
8. source and rescue denominators come from the same recipient execution;
9. checkpoint rules remain frozen;
10. repeated-checkpoint rule remains frozen;
11. primary 0.05 threshold remains frozen;
12. sensitivity grid is secondary only;
13. base_problem_id is the independent unit;
14. right-censored lifetime cases are labeled explicitly;
15. no attention-based selection occurs;
16. no new cohort expansion occurs;
17. no route decomposition runs unless the original gate passes;
18. no retrieval-trigger experiment runs;
19. no sink intervention runs;
20. exactly one next-stage recommendation is produced.

Technical PASS does not require any checkpoint to survive.

---

## 36. Output Structure

```text
outputs/stage3c9r/
  config/
    stage3c9r_config.json
    immutable_inputs.json
    canonical_path.json
    checkpoint_rules.json
    sensitivity_grid.json

  cohort/
    primary_manifest.jsonl
    validation_manifest.jsonl
    frozen_events.jsonl
    frozen_event_spans.jsonl
    frozen_neighbors.jsonl
    frozen_readouts.jsonl

  audit/
    canonical_path_audit.json
    source_window_audit.json
    event_patch_selectivity.json
    neighbor_patch_selectivity.json
    cache_invariance.json
    self_patch_validation.json
    deterministic_replay.json
    readout_index_audit.json

  same_path_scores/
    w8_all_events.jsonl
    w16_all_events.jsonl
    event_rescue_all.jsonl
    neighbor_rescue_all.jsonl

  analysis/
    source_sensitivity.json
    checkpoint_classification.json
    source_vs_rescue_2d.json
    repeated_checkpoint_analysis.json
    lifetime_analysis.json
    threshold_sensitivity.json
    stage3c9_phase_comparison.json
    base38_reference.json
    target_heterogeneity.json
    figures/

  optional_necessity/
    gate.json
    necessity_results.jsonl

  route/
    gate.json
    route_status.json

  summaries/
    stage3c9r_summary.md
    stage3c9r_acceptance.json
    next_stage_recommendation.md
```

Do not overwrite Stage 3C.9 artifacts.

---

## 37. Required Figures

At minimum:

1. Stage 3C.9 Phase A vs Phase B vs 3C.9R source-loss comparison;
2. same-path W8 source-loss distribution;
3. same-path W16 source-loss distribution;
4. source loss vs event-span rescue scatter;
5. source loss vs matched-neighbor rescue scatter;
6. event-minus-neighbor rescue distribution;
7. checkpoint count per base;
8. repeated-checkpoint count at primary threshold;
9. threshold-sensitivity checkpoint counts;
10. threshold-sensitivity repeated-checkpoint counts;
11. local-use vs final-use rescue for surviving checkpoints;
12. base 38 same-path replication;
13. right-censored lifetime cases;
14. source-sensitive-but-nonrescued event examples;
15. final scientific outcome decision table.

---

## 38. Stop Condition

After:

```text
same-path validation
→ full frozen-event rescoring
→ source sensitivity
→ event/neighbor rescue
→ checkpoint classification
→ repeated-checkpoint analysis
→ lifetime analysis
→ threshold sensitivity
→ exactly one recommendation
```

**STOP.**

Do not:

```text
expand the cohort
search for new event spans
run route analysis below the original gate
start Retrieval Trigger
start sink causality
start Stage 4
```

Return the complete Stage 3C.9R result for review.

The next experiment must be selected by paper-level information value, not by the desire to recover more positive checkpoint examples.
