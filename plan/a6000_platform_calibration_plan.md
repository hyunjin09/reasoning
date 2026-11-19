# A6000 Platform Calibration Plan
## Hardware Migration Before Stage 3C.9

## 0. Purpose

From Stage 3C.9 onward, the project will use **NVIDIA RTX A6000** GPUs as the frozen primary hardware platform because the long-prefix Stage 3C.9 workload can exceed the 24 GB VRAM available on the prior A5000 environment.

This calibration is **not a new scientific stage** and does not test a new mechanistic hypothesis.

Its purpose is to establish a clean experimental boundary:

```text
Stages ≤ 3C.8:
primary hardware = A5000

Stage 3C.9 onward:
primary hardware = A6000
```

The calibration must answer four questions before Stage 3C.9 restarts:

1. **Is the A6000 implementation internally deterministic and mechanically correct?**
2. **Do full and cached/memory-bounded scoring paths agree on A6000?**
3. **Do previously established strong causal effects preserve their direction and qualitative interpretation after hardware migration?**
4. **Can the A6000 safely execute the long-prefix Stage 3C.9 workload without OOM or hidden protocol changes?**

The goal is **not** to force exact A5000↔A6000 numerical equality.

---

# 1. Why This Calibration Is Necessary

The observed A5000→A6000 score drift was approximately:

```text
median absolute D difference ≈ 0.125 nats/token
maximum observed difference ≈ 0.250
```

For earlier large causal effects this is small relative to effect size, but it can be material for Stage 3C.9 threshold-adjacent events.

Stage 3C.9 also contains:

```text
classification floor = 0.05 nats/token
```

Therefore mixing hardware inside one Stage 3C.9 cohort would create unnecessary ambiguity.

The clean solution is:

> **Freeze A6000 as a new platform, validate it once, then rerun Stage 3C.9 entirely on A6000.**

---

# 2. Paper-Level Importance

This calibration exists to protect the interpretability of the paper, not to create a hardware result.

The paper should be able to state:

> Earlier mechanistic stages were run on the frozen A5000 platform. Beginning with the long-horizon Stage 3C.9 experiments, the project migrated to A6000 GPUs because of VRAM requirements. A pre-scoring calibration verified deterministic replay, scoring-path parity, intervention fidelity, and qualitative continuity of previously established causal effects.

The calibration should remain an implementation/methods appendix item.

Do not turn small cross-hardware numerical drift into a scientific claim.

---

# 3. Frozen Hardware Amendment

Before running any calibration scores, write:

```text
outputs/a6000_calibration/config/hardware_migration_amendment.md
```

The amendment must state:

1. Stage 3C.9 encountered A5000 OOM on valid long-prefix examples.
2. A6000 is required for the frozen Stage 3C.9 protocol.
3. Stage 3C.9 will restart from trajectory 0 on A6000.
4. Existing partial A5000 Stage 3C.9 screening outputs are preserved for provenance only.
5. A5000 and A6000 Stage 3C.9 trajectories will never be mixed in the primary cohort.
6. Model weights, dtype, generation parameters, attention implementation, intervention semantics, seed policy, and scoring definitions remain unchanged.
7. Frozen Stage 3C.9 scientific thresholds remain unchanged.
8. Cross-hardware equality is not a calibration acceptance criterion.
9. A6000 becomes the default primary hardware for subsequent stages unless a later amendment is explicitly frozen.

---

# 4. What Must Not Change During Migration

The migration should change **hardware only** wherever technically possible.

Freeze:

```text
model checkpoint
tokenizer
transformers / torch versions
CUDA software environment
model dtype
attention implementation
generation parameters
sampling parameters
seed schedule
EOS behavior
max_new_tokens
teacher-forced scoring code
memory-bounded scoring code
cache representation
GQA K/V semantics
RoPE handling
intervention hook locations
FP32 contribution partition
evidence-preference metric
Stage 3C.9 event rules
Stage 3C.9 W8/W16 definitions
Stage 3C.9 classification floor
```

Do not change batch size, attention backend, dtype, or scoring code merely because A6000 has more VRAM unless absolutely required.

Any unavoidable code change must receive a separate mechanical parity test before continuing.

---

# 5. Calibration Cohort

Use a **fixed historical calibration cohort**.

Target:

```text
12 base problems
```

Minimum:

```text
10
```

These are calibration examples only, not new confirmatory scientific data.

## 5.1 Composition

Freeze the 12 before A6000 scoring using archived A5000 results:

```text
4 strong-effect examples
4 medium-effect examples
4 threshold-adjacent / small-effect examples
```

Include, where available:

```text
Target A-like examples
Target B-like examples
long-prefix examples
shorter reference examples
```

The threshold-adjacent cases are included to characterize sensitivity, **not** to determine PASS/FAIL of strong-mechanism continuity.

## 5.2 Long-prefix stress cases

At least:

```text
3 examples
```

must be long enough to exercise the memory-bounded path that motivated migration.

Include the longest mechanically valid example available.

---

# 6. Calibration Layers

The calibration has four layers.

```text
Layer A — A6000 internal numerical/mechanical validation
Layer B — A6000 device-to-device reproducibility
Layer C — A5000→A6000 continuity bridge
Layer D — Stage 3C.9-specific long-prefix validation
```

All four must be reviewed before Stage 3C.9 restart.

---

# LAYER A — A6000 INTERNAL VALIDATION

## 7. Deterministic Replay

On one primary A6000, repeat each fixed calibration example at least:

```text
3 times
```

for deterministic teacher-forced scoring.

Compare:

```text
native D
suppressed D
patched D
cache tensors where relevant
```

Expected:

```text
token-exact generation where deterministic generation is invoked
and
numerically identical or within frozen floating-point tolerance for scoring
```

Record maximum absolute differences.

---

# 8. Full vs Cached / Memory-Bounded Scoring Parity

For all calibration examples that fit both paths, compare:

```text
reference full scoring
vs
memory-bounded native eager-attention scoring
```

Required outputs:

```text
candidate token log-probabilities
aggregate D
intermediate intervention scores
```

This is mandatory because Stage 3C.9 relies on memory-bounded scoring for long prefixes.

Freeze a strict numerical tolerance before comparison.

Recommended:

```text
max |Δ token logprob| <= 1e-5
max |Δ aggregate D| <= 1e-5
```

If the historical implementation already has a tighter established tolerance, use that.

Do not loosen tolerance after inspecting failures.

---

# 9. Cache Replay Parity

Validate:

```text
cached autoregressive replay
vs
equivalent full-prefix recomputation
```

for:

- native scoring;
- one source-suppressed condition;
- one cache-rescue condition.

Check:

```text
post-RoPE K
projected V
current residual
final token scores
```

where available.

---

# 10. Self-Patch Exactness

Run:

```text
native → native
suppressed → suppressed
```

for:

- K-only patch hooks;
- V-only patch hooks;
- K+V patch hooks;
- residual patch hooks;
- event-span cache hooks.

All self patches must reproduce the unpatched recipient within frozen tolerance.

---

# 11. Intervention Selectivity

Audit that each intervention alters only its intended tensor positions.

Check:

```text
target ROI contribution deletion
event-span K/V replacement
single-token K/V replacement
current residual replacement
```

Verify invariance of:

```text
visual prompt K/V unless intentionally modified
non-target visual positions
non-event reasoning cache positions
prompt/question cache positions
current-query cache where not targeted
```

---

# 12. GQA / RoPE Layout

Explicitly validate on A6000:

```text
native KV head count = 8
logical query heads = 32
post-RoPE K layout
projected V layout
token-position indexing
visual-token indexing
```

Store shape and index audits.

---

# LAYER B — A6000 DEVICE-TO-DEVICE REPRODUCIBILITY

## 13. Why This Matters

If future experiments use multiple A6000 cards, the platform should be validated across more than one physical GPU.

Use:

```text
minimum 2 A6000 devices
preferred 3
```

if available.

---

# 14. Cross-A6000 Replay Set

Run a compact fixed subset:

```text
4 calibration bases
```

on every selected A6000 device.

Include:

```text
1 strong
1 medium
1 threshold-adjacent
1 long-prefix stress case
```

Compare:

```text
native D
suppressed D
causal gain
deterministic replay
memory-bounded score
```

The key requirements are:

- same causal sign for strong effects;
- same qualitative strong-effect classification;
- no device-specific mechanical failures;
- no device-specific OOM for the frozen workload.

If one A6000 behaves anomalously, exclude that device from the frozen pool and document why.

---

# LAYER C — A5000 → A6000 CONTINUITY BRIDGE

## 15. Purpose

This layer checks whether previously established mechanisms remain qualitatively intact.

It is **not** a new replication study and does not require exact score equality.

Use archived A5000 outputs from the same fixed 12 cases.

Compare with new A6000 results.

---

# 16. Bridge Effects to Reproduce

Choose a compact set of already-established causal effects spanning the mechanism story.

## 16.1 Visual-content causal control

From Stage 3A / 3B:

```text
O vs C evidence-preference direction
```

Expected:

```text
counterfactual visual content still moves evidence preference in the expected direction
```

## 16.2 Target-ROI source specificity

From Stage 3B.7-R / 3C:

```text
target ROI manipulation > irrelevant ROI manipulation
```

on fixed examples.

## 16.3 Prior-token cache rescue

From Stage 3C.7 / 3C.8:

```text
t_pre K+V rescue > suppressed
```

with strong positive direction.

## 16.4 Current-residual partial rescue

From Stage 3C.6:

```text
native current residual partially rescues source-deficient behavior
```

on a small fixed subset.

Do not rerun every prior stage.

---

# 17. Continuity Metrics

For each bridge effect report:

```text
A5000 score
A6000 score
absolute difference
relative difference
effect sign
qualitative classification
```

Across cases report:

```text
median |ΔD|
max |ΔD|
Spearman rank correlation
sign agreement
strong-effect classification agreement
```

---

# 18. Hardware-Sensitive Band

Because cross-hardware score drift can exceed the Stage 3C.9 floor, define **before A6000 calibration scoring** a descriptive hardware-sensitive band.

Recommended:

```text
hardware-sensitive if
|effect magnitude| <= 2 × historical median cross-hardware |ΔD|
```

Using the currently observed drift:

```text
≈ 0.25 nats/token
```

This is a **sensitivity label only**.

It must not change the frozen Stage 3C.9 primary threshold.

Do not exclude future Stage 3C.9 examples merely because they lie in this band.

---

# 19. Continuity Acceptance Logic

## Strong historical effects

Require:

```text
same causal direction
same broad scientific interpretation
```

on at least:

```text
90% of evaluable strong/medium bridge cells
```

and no systematic sign reversal.

## Threshold-adjacent effects

No exact classification agreement is required.

Report instability transparently.

A threshold-adjacent mismatch does **not** fail the platform calibration by itself.

---

# LAYER D — STAGE 3C.9-SPECIFIC VALIDATION

## 20. Why This Layer Is Necessary

The A6000 migration was triggered by Stage 3C.9 long-prefix memory demands.

Therefore the calibration must test the actual Stage 3C.9 mechanics before restarting the 600-trajectory screen.

---

# 21. Long-Prefix Memory Stress Test

Run at least:

```text
3 long-prefix cases
```

including the longest available valid case.

Record:

```text
allocated VRAM
reserved VRAM
peak VRAM
wall-clock time
prefix length
visual-token count
reasoning-token count
```

Required:

```text
no OOM
no silent truncation
no fallback to a different attention implementation
```

---

# 22. Stage 3C.9 W8 / W16 Source Suppression

On the validation subset, run:

```text
W8 target-ROI suppression
W16 target-ROI suppression
```

and verify:

- exact query windows;
- all 36 language layers;
- all logical heads;
- target ROI T only;
- FP32 contribution partition;
- no unrelated cache mutation.

The goal is mechanical correctness, not effect-size replication.

---

# 23. Event-Span Cache Rescue

Validate one or more frozen event spans per example.

Check:

```text
full-depth native event-span K+V
→ matching source-deficient recipient
```

Verify:

- exact token positions;
- exact GQA K/V entries;
- all non-event positions remain recipient-native;
- visual K/V unchanged;
- current readout finite.

---

# 24. Matched-Neighbor Rescue

Validate the matched-neighbor control implementation.

Event span and neighbor span must:

```text
have equal tokenizer-position count
remain within frozen positional rule
alter only their intended cache positions
```

No effect-size criterion is required.

---

# 25. Local-Use and Final-Use Readout Parity

For at least:

```text
4 annotated events
```

verify both:

```text
local-use evidence score
final E_d evidence score
```

under:

```text
native
W8 suppressed
W16 suppressed
event-span rescued
```

This ensures the two-readout Stage 3C.9 analysis is implemented correctly on A6000.

---

# 26. Route-Intervention Dry Run

If mechanically possible, run the Stage 3C.9 route-intervention ordering on:

```text
2–3 calibration examples
```

without making any scientific inference.

Validate:

```text
direct W8 source suppression
prior-checkpoint cache replacement
short-history cache replacement
joint intervention
```

The objective is only to ensure patch ordering and state ownership are correct before future gated route analysis.

---

# 27. Stage 3C.9 Threshold Policy

The frozen Stage 3C.9 scientific thresholds remain unchanged.

Do not alter:

```text
0.05 nats/token classification floor
robustness thresholds
directionality rules
bootstrap rules
event inclusion rules
```

because of hardware migration.

All Stage 3C.9 primary inference will be internally A6000-only.

Thus cross-hardware drift is a provenance/sensitivity issue, not a reason to retune primary thresholds.

---

# 28. Calibration PASS Criteria

The A6000 platform calibration passes only if all of the following hold.

## A. Internal mechanics

1. deterministic replay passes;
2. full vs memory-bounded scoring parity passes;
3. cached vs full recomputation parity passes;
4. self patches reproduce recipients;
5. intervention selectivity passes;
6. GQA / RoPE layouts are correct;
7. all outputs are finite.

## B. A6000 pool consistency

8. at least two A6000 devices pass the fixed cross-device replay;
9. no device-specific intervention failure occurs;
10. long-prefix workload fits without OOM on the frozen device pool.

## C. Historical continuity

11. strong prior causal effects preserve direction on >=90% of evaluable strong/medium cells;
12. no systematic sign reversal appears;
13. target-vs-control ordering remains qualitatively intact where tested;
14. threshold-adjacent disagreement is documented rather than used to tune thresholds.

## D. Stage 3C.9 readiness

15. long-prefix stress test passes;
16. W8/W16 mechanics pass;
17. event-span rescue mechanics pass;
18. matched-neighbor mechanics pass;
19. local/final readout scoring passes;
20. route-intervention dry run passes if mechanically eligible.

---

# 29. What Does NOT Fail Calibration

The following alone do not fail migration:

```text
A5000 and A6000 D scores differ numerically
threshold-adjacent classifications change
small historical effects change magnitude
cross-hardware rank ordering changes among near-zero effects
```

provided:

```text
A6000 internal mechanics are correct
and
strong causal conclusions remain qualitatively stable
```

---

# 30. Failure Handling

## F1 — Full/cached parity failure

Stop.

Fix scoring implementation before any Stage 3C.9 restart.

## F2 — Self-patch / selectivity failure

Stop.

Fix hook/cache indexing before any scientific run.

## F3 — Strong-effect sign reversals

Investigate software/environment mismatch before accepting A6000.

Do not dismiss repeated strong sign reversals as harmless hardware drift.

## F4 — One anomalous A6000 device

Exclude the device from the frozen hardware pool if the anomaly is reproducible.

Document the exclusion.

## F5 — Long-prefix OOM still occurs

Do not change scientific protocol immediately.

First profile:

```text
memory-bounded path
KV cache retention
temporary tensor lifetime
batching
```

Any protocol-changing optimization requires a separate parity validation.

---

# 31. After Calibration PASS

Once the calibration passes:

```text
A6000 = frozen primary hardware platform
```

Then:

1. archive the partial A5000 Stage 3C.9 screen;
2. preserve it as provenance only;
3. restart Stage 3C.9 from:
   ```text
   0 / 600
   ```
   on A6000;
4. rerun Stage 3C.9 validation on A6000;
5. complete all Stage 3C.9 screening, cohort freezing, and causal scoring on A6000 only.

Do not combine partial A5000 Stage 3C.9 trajectories with the A6000 cohort.

---

# 32. Future Stages

After this calibration, later stages do **not** need a new A5000↔A6000 bridge every time.

They only require normal stage-specific validation as long as:

```text
hardware remains within the frozen A6000 pool
software stack remains frozen
dtype remains frozen
attention/scoring implementation remains frozen
```

A new platform calibration is required only if one of those conditions materially changes.

---

# 33. Output Structure

```text
outputs/a6000_calibration/
  config/
    hardware_migration_amendment.md
    environment_freeze.json
    calibration_cohort.json
    device_pool.json
    tolerances.json

  layer_a_internal/
    deterministic_replay.json
    full_vs_memory_bounded.json
    cached_vs_full.json
    self_patch_validation.json
    intervention_selectivity.json
    gqa_rope_layout.json

  layer_b_cross_device/
    device_replay_results.jsonl
    device_comparison.json
    anomalous_devices.json

  layer_c_bridge/
    a5000_reference_scores.jsonl
    a6000_bridge_scores.jsonl
    continuity_statistics.json
    hardware_sensitive_band.json
    strong_effect_agreement.json

  layer_d_stage3c9/
    long_prefix_stress.jsonl
    w8_w16_validation.json
    event_span_rescue_validation.json
    neighbor_control_validation.json
    local_final_readout_validation.json
    route_dry_run.json

  analysis/
    platform_readiness.json
    cross_hardware_drift.json
    figures/

  summaries/
    a6000_calibration_summary.md
    a6000_calibration_acceptance.json
    stage3c9_restart_authorization.md
```

---

# 34. Required Figures / Tables

At minimum:

1. A5000 vs A6000 native D scatter;
2. A5000 vs A6000 causal-gain scatter;
3. absolute cross-hardware drift distribution;
4. strong/medium/threshold-adjacent agreement table;
5. A6000 full vs memory-bounded scoring parity;
6. cross-A6000 device comparison;
7. long-prefix VRAM usage vs prefix length;
8. intervention self-patch/selectivity audit table;
9. Stage 3C.9 W8/W16 mechanical validation table;
10. final PASS/FAIL checklist.

---

# 35. Stop Condition

After:

- hardware amendment freeze;
- fixed cohort selection;
- A6000 deterministic validation;
- scoring-path parity;
- cross-device replay;
- historical continuity bridge;
- long-prefix stress test;
- Stage 3C.9-specific intervention validation;
- final 20-point acceptance review;

**STOP.**

Do not start Stage 3C.9 automatically unless the calibration report is explicitly classified:

```text
PASS — A6000 PLATFORM READY
```

After review, Stage 3C.9 should be restarted from zero on the frozen A6000 platform.
