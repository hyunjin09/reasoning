# A6000 Calibration v2 + Stage 3C.9 Clean-Restart Plan
## Canonical Execution-Path Selection, Fixed-Path Validation, and A6000-Only Restart

## 0. Decision Context

The original A6000 calibration is an **immutable technical FAIL**:

```text
FAIL — A6000 PLATFORM NOT READY
Reason: F1 full-vs-bounded scoring-path parity failure
```

That result must not be overwritten or retroactively relabeled.

However, the failure does **not** establish that A6000 hardware is unsuitable.

The executed A6000 checks already showed:

```text
deterministic full-path replay: PASS
self patches: PASS
architecture / GQA layout: PASS
finite outputs: PASS
memory availability on tested case: PASS
```

The failed requirement was:

```text
full recomputation ≈ cached / bounded execution within 1e-5
```

The focused diagnosis further showed that:

```text
historical one-shot cached execution != full recomputation
```

under BF16, consistent with previously documented matrix-shape-dependent numerical behavior.

Therefore the next task is not to relax the failed test until it passes.

The next task is to define and validate **one canonical A6000 execution path** for all Stage 3C.9 causal contrasts.

---

# 1. Why This Plan Is Necessary for the Paper

Stage 3C.9 is currently the key experiment deciding whether the local carrier mechanism discovered in Stages 3C.4–3C.8 becomes:

```text
repeated short-lived checkpoints / refresh
vs
persistent reasoning-side memory
vs
distributed state
```

The experiment is important enough that its numerical protocol must be unambiguous.

The paper does **not** require:

```text
BF16 full recomputation
==
BF16 cached execution
```

if these are known to use different matrix shapes.

The paper **does** require:

1. every scientific contrast to use one fixed execution semantics;
2. deterministic replay within that path;
3. exact self-patch/selectivity mechanics;
4. strong prior causal conclusions to remain qualitatively stable;
5. Stage 3C.9 to be run entirely on one frozen A6000 protocol.

---

# 2. Core Principle

The primary scientific quantities in Stage 3C.9 are matched causal contrasts such as:

```text
L = D_native - D_suppressed
G = D_rescued - D_suppressed
C = G_event - G_neighbor
```

These contrasts must be computed with:

```text
the same hardware
the same dtype
the same cache semantics
the same chunking convention
the same tensor shapes whenever possible
the same scoring path
```

within every comparison.

Do not mix:

```text
full native
with
cached suppressed
```

or any analogous cross-path contrast.

---

# 3. Main Strategy

Use a two-branch canonical-path decision.

## Preferred branch — P1

```text
Historical one-shot cached path on A6000
```

If this path fits the long Stage 3C.9 prefixes on A6000 without OOM, use it as the canonical Stage 3C.9 scorer.

This is preferred because it:

- already has historical mechanistic usage;
- preserves familiar cache semantics;
- avoids introducing a new chunked numerical path;
- requires the smallest methodological change.

## Fallback branch — P2

If P1 still OOMs on legitimate Stage 3C.9 stress cases:

```text
Fixed streaming cached path
```

Use one prospectively frozen chunking convention for **all** Stage 3C.9 conditions.

Do not switch chunk size by example or intervention.

---

# 4. Immutable Records

Preserve:

```text
outputs/a6000_calibration/
```

from calibration v1 unchanged.

Create a new tree:

```text
outputs/a6000_calibration_v2/
```

The v2 report must explicitly reference:

```text
v1 status = FAIL
reason = unmet/invalid cross-path parity gate for the intended migration
```

without erasing the result.

---

# 5. Freeze Amendment v2 Before New Scores

Write:

```text
outputs/a6000_calibration_v2/config/calibration_v2_amendment.md
```

before any new v2 scoring.

The amendment must state:

1. Calibration v1 remains FAIL.
2. Full-vs-cached exact equality is no longer a platform-readiness criterion.
3. The reason is that historical BF16 cached/full execution is already deterministically non-identical because execution shapes differ.
4. Stage 3C.9 will use exactly one canonical cached execution path.
5. P1 one-shot cached execution is preferred if it fits the long-prefix workload.
6. P2 fixed streaming execution is allowed only if P1 OOMs.
7. The chosen path is frozen before primary Stage 3C.9 scoring.
8. Stage 3C.9 remains A6000-only and will restart from trajectory 0.
9. All original Stage 3C.9 scientific thresholds remain primary and unchanged.
10. Cross-path comparisons are diagnostics, not primary scientific contrasts.

---

# 6. Software / Model Freeze

Keep unchanged from the failed calibration:

```text
model checkpoint
tokenizer
torch / transformers environment
CUDA software stack
BF16 dtype
attention implementation
generation parameters
sampling parameters
seed schedule
EOS behavior
max_new_tokens
teacher-forced scoring definitions
GQA cache representation
RoPE handling
intervention hooks
FP32 target-contribution partition
evidence-preference score D
Stage 3C.9 event taxonomy
W8/W16 source windows
Stage 3C.9 classification floor
```

Any unavoidable change must be documented and separately parity-tested.

---

# PHASE 1 — CANONICAL PATH FEASIBILITY

## 7. Risk-First Question

Before repairing or adopting a streaming scorer, ask:

> **Does the historical one-shot cached path already fit the actual Stage 3C.9 workload on A6000?**

If yes, there is no scientific reason to introduce a new bounded execution semantics.

---

# 8. P1 Long-Prefix Stress Set

Freeze:

```text
6 stress examples
```

before execution.

Include:

```text
the longest valid available prefix
the largest visual-token case
the prior A5000 OOM-type case if reproducible
four additional high-memory long-horizon cases
```

Use the historical one-shot cached path.

Record:

```text
prefix tokens
reasoning tokens
visual tokens
candidate length
peak allocated VRAM
peak reserved VRAM
wall time
```

Run:

```text
native
one W16 suppression
one event-span K+V rescue
```

where mechanically available.

---

# 9. P1 Acceptance

Select P1 as canonical if all six stress examples satisfy:

```text
no OOM
no silent truncation
no attention-backend fallback
finite scores
deterministic replay
```

and maximum peak memory leaves a predeclared operational margin.

Recommended margin:

```text
peak reserved VRAM <= 90% of physical A6000 VRAM
```

If P1 passes, **do not develop or use the streaming scorer for Stage 3C.9**.

Proceed directly to Phase 3.

---

# 10. P1 Failure

If at least one legitimate frozen stress example OOMs or exceeds the operational memory margin:

```text
P1 = NOT FEASIBLE
```

Then proceed to Phase 2.

Do not change the Stage 3C.9 scientific protocol to make P1 fit.

---

# PHASE 2 — FIXED STREAMING PATH, ONLY IF P1 FAILS

## 11. Goal

The streaming path does not need to equal full recomputation.

It must provide a **single deterministic execution semantics** for every Stage 3C.9 condition.

The important requirement is:

```text
native / suppressed / rescued / neighbor / route controls
all use the exact same streaming convention
```

---

# 12. Freeze One Chunking Convention

Before causal validation, choose exactly one streaming convention from memory requirements alone.

Preferred order:

```text
1. largest fixed chunk size that safely fits all stress examples
2. otherwise smaller fixed chunk size
3. token-by-token only if necessary
```

Do not choose chunk size using scientific effect agreement.

Do not vary chunk size by example.

Write:

```text
outputs/a6000_calibration_v2/config/canonical_chunking.json
```

---

# 13. First-Divergence Diagnostic

On the frozen calibration base used in v1 and at least two additional bases, compare:

```text
historical one-shot cached path
vs
candidate fixed streaming path
```

Capture the earliest available matching tensors:

```text
prefill residual
per-layer post-RoPE K
per-layer projected V
first continuation-token residual
first continuation-token attention output
first continuation-token logits
candidate log probabilities
```

The goal is to determine whether any large discrepancy reflects:

```text
a genuine implementation bug
or
expected fixed-shape BF16 execution drift
```

---

# 14. Streaming Path Repair Gate

A candidate streaming implementation is rejected if any of the following occurs:

```text
wrong cache positions
wrong RoPE coordinates
wrong K/V head layout
state ownership mismatch
non-deterministic replay
self-patch failure
intervention selectivity failure
condition-dependent chunking
```

Large numerical differences alone do not identify a bug if all mechanics are correct, but they trigger the causal-contrast stability tests below.

---

# PHASE 3 — CANONICAL-PATH INTERNAL VALIDATION

## 15. Calibration Cohort

Reuse the frozen 12-base historical calibration cohort from v1.

Do not select a new cohort based on v1 numerical discrepancies.

Use:

```text
4 strong-effect
4 medium-effect
4 threshold-adjacent / small-effect
```

historical examples.

---

# 16. Deterministic Replay

Using the chosen canonical path, repeat at least:

```text
3 times
```

for each selected condition.

Required:

```text
identical tokenization
identical cache indexing
identical execution path
identical scores within frozen same-path tolerance
```

Set the same-path numerical tolerance before review.

Because the same execution graph is being repeated, use a strict tolerance.

Recommended:

```text
max |ΔD| <= 1e-6
```

or exact equality if historically observed.

---

# 17. Self-Patch Exactness

Test:

```text
native → native
suppressed → suppressed
```

for:

```text
K-only
V-only
K+V
event-span K+V
residual patch
```

Require exact or frozen same-path tolerance reproduction.

---

# 18. Intervention Selectivity

Audit:

```text
target ROI source suppression
single-token cache rescue
event-span cache rescue
matched-neighbor cache rescue
current residual rescue
```

Verify that no untargeted:

```text
visual K/V
prompt cache
other reasoning-token cache
current-query cache
```

is modified.

---

# 19. Stage 3C.9 W8 / W16 Validation

Run both:

```text
W8
W16
```

on at least:

```text
8 validation events
```

Verify:

```text
correct query windows
all 36 language layers
all logical heads
target ROI T only
FP32 contribution partition
finite downstream readouts
```

Effect magnitude is not a mechanical PASS criterion.

---

# 20. Event / Neighbor Patch Validation

For at least:

```text
8 event spans
```

validate:

```text
native event-span K+V rescue
matched-neighbor K+V rescue
```

with equal token counts.

Require exact patch-position isolation.

---

# 21. Local / Final Readout Validation

For at least:

```text
8 events
```

compute both:

```text
local-use readout
final E_d readout
```

under:

```text
native
W8 suppressed
W16 suppressed
event rescued
neighbor rescued
```

All must use the canonical path.

---

# PHASE 4 — SCIENTIFIC CONTRAST STABILITY

## 22. Why Contrast Stability Matters

A fixed BF16 cached path may differ in absolute `D` from another execution shape.

The main paper conclusions depend on matched causal contrasts.

Therefore compare, on short examples where all paths are feasible:

```text
full
historical one-shot cached
canonical A6000 path
```

for:

```text
L = D_native - D_suppressed
G = D_rescued - D_suppressed
target-minus-control contrast
```

This is a diagnostic bridge, not a requirement of numerical equality.

---

# 23. Frozen Strong-Effect Bridge

Use the same historical strong/medium cells from v1.

Include at least:

```text
visual-content causal direction
target ROI > irrelevant ROI
t_pre K+V rescue
current residual partial rescue
```

where archived implementations are available.

---

# 24. Contrast Acceptance

For strong/medium historical effects require:

```text
>= 90% sign agreement
no systematic sign reversal
same broad target-vs-control ordering
same qualitative scientific interpretation
```

Threshold-adjacent cells may change classification.

Do not use those cells to tune the canonical path.

---

# 25. Absolute D Drift

Report:

```text
full vs canonical ΔD
historical-cache vs canonical ΔD
```

but do not use absolute cross-path D equality as the readiness gate.

The primary requirement is fixed-path internal validity plus causal-contrast continuity.

---

# 26. Stage 3C.9 Threshold Sensitivity

Keep the original primary threshold:

```text
0.05 nats/token
```

unchanged.

Because v1 revealed path-sensitive absolute scoring near small effects, predeclare a **secondary sensitivity table** at:

```text
0.025
0.05  ← primary
0.10
0.15
```

This is robustness analysis only.

The paper's primary classification remains the frozen `0.05` rule.

Do not select the threshold producing the preferred checkpoint frequency.

---

# PHASE 5 — CROSS-A6000 DEVICE VALIDATION

## 27. Device Pool

If Stage 3C.9 will use multiple A6000 GPUs, validate every device intended for the pool or at least a representative minimum of:

```text
2 devices
```

Preferred:

```text
all devices used in the 600-trajectory screen
```

---

# 28. Fixed Cross-Device Replay

Use:

```text
4 bases
```

including:

```text
1 strong
1 medium
1 threshold-adjacent
1 long-prefix stress case
```

Run the canonical path unchanged.

Require:

```text
same strong-effect sign
same deterministic behavior per device
no device-specific OOM
no intervention-mechanics failure
```

Document small numerical device differences if present.

---

# PHASE 6 — A6000 PLATFORM v2 READINESS

## 29. PASS Criteria

Classify:

```text
PASS — A6000 CANONICAL PATH READY
```

only if all applicable criteria pass.

### Canonical path

1. P1/P2 choice is frozen from memory feasibility, not scientific effects.
2. One execution path is used for every Stage 3C.9 causal condition.
3. No per-example chunk-size switching occurs.

### Internal validity

4. deterministic replay passes;
5. self patches pass;
6. intervention selectivity passes;
7. GQA/RoPE/cache indexing passes;
8. W8/W16 mechanics pass;
9. event/neighbor cache patching passes;
10. local/final readout scoring passes;
11. all outputs are finite.

### Scientific continuity

12. >=90% strong/medium historical causal-sign agreement;
13. no systematic sign reversal;
14. target-vs-control ordering is qualitatively preserved where tested.

### Hardware

15. long-prefix stress set fits the frozen A6000 path;
16. no silent truncation/backend fallback;
17. intended A6000 device pool passes cross-device replay.

---

# 30. What Does NOT Fail v2

The following alone do not fail readiness:

```text
full and cached absolute D differ
historical one-shot and streaming absolute D differ
threshold-adjacent classifications change
near-zero effects reorder
```

provided that:

```text
one canonical path is fixed
same-path mechanics are correct
strong causal contrasts remain qualitatively stable
```

---

# 31. Failure Branches

## F2.1 — P1 fits

This is the preferred result.

Use:

```text
historical one-shot cached path
```

as Stage 3C.9 canonical execution.

Do not use the bounded scorer.

## F2.2 — P1 OOM, P2 mechanics pass

Use the fixed streaming path.

All Stage 3C.9 conditions must use that path.

## F2.3 — P2 shows mechanical mismatch

Stop and repair implementation.

Do not start Stage 3C.9.

## F2.4 — Strong causal signs systematically reverse

Stop and diagnose.

Do not explain this away as BF16 drift.

## F2.5 — Threshold-adjacent effects are unstable but strong effects stable

Proceed.

Retain the primary threshold and report sensitivity analysis.

---

# PHASE 7 — STAGE 3C.9 CLEAN RESTART

## 32. Authorization

Stage 3C.9 may restart only after:

```text
PASS — A6000 CANONICAL PATH READY
```

is written to:

```text
outputs/a6000_calibration_v2/summaries/stage3c9_restart_authorization.md
```

---

# 33. Clean Restart Rule

Discard partial A5000 Stage 3C.9 outputs from primary inference.

Preserve them only as provenance.

Restart:

```text
Stage 3C.9
0 / 600
```

on the frozen A6000 canonical path.

Do not reuse A5000-screened outcomes as part of the A6000 cohort.

---

# 34. Stage 3C.9 A6000 Validation

Before the 600-screen begins, rerun the frozen Stage 3C.9 validation set entirely using the canonical A6000 path.

Require:

```text
event annotation/index audit
W8/W16 mechanics
event-span rescue mechanics
neighbor control
local/final scoring
deterministic replay
long-prefix memory fit
```

No scientific effect-size gate is added beyond the original Stage 3C.9 plan.

---

# 35. Stage 3C.9 Primary Execution Rule

All primary conditions use the same canonical A6000 path:

```text
native
W8 suppressed
W16 suppressed
event-span rescued
single-token localization
neighbor rescued
necessity arm if gated
route arms if gated
```

Never compare conditions generated with different chunking/execution semantics.

---

# 36. Why This Is Scientifically Sufficient

The central Stage 3C.9 claim concerns **within-path causal changes**:

```text
Does removing visual source support change later evidence use?

Can restoring a candidate checkpoint cache rescue that deficit?

Does the same phenomenon repeat across long reasoning?
```

These questions do not require cross-execution-shape numerical identity.

They require:

```text
matched execution
mechanically isolated interventions
deterministic causal contrasts
proper controls
```

That is the v2 calibration target.

---

# 37. Paper Reporting Boundary

Methods should report:

1. A5000 was used through Stage 3C.8.
2. Stage 3C.9 required A6000 due long-prefix VRAM.
3. BF16 full/cached execution showed deterministic matrix-shape-dependent differences.
4. Stage 3C.9 therefore used one frozen cached execution path for every causal condition.
5. Strong prior causal effects were checked for qualitative continuity before restart.
6. No A5000 and A6000 Stage 3C.9 examples were mixed.

Do not frame this as a model-behavior result.

---

# 38. Output Structure

```text
outputs/a6000_calibration_v2/
  config/
    calibration_v2_amendment.md
    environment_freeze.json
    canonical_path_decision.json
    canonical_chunking.json
    tolerances.json

  phase1_path_feasibility/
    stress_manifest.jsonl
    one_shot_memory_stress.jsonl
    path_decision.json

  phase2_streaming_if_needed/
    first_divergence.json
    tensor_comparisons.jsonl
    streaming_mechanics.json
    canonical_streaming_freeze.json

  phase3_internal/
    deterministic_replay.json
    self_patch_validation.json
    intervention_selectivity.json
    w8_w16_validation.json
    event_neighbor_patch_validation.json
    local_final_readout_validation.json

  phase4_contrast_bridge/
    full_path_diagnostics.jsonl
    historical_cache_diagnostics.jsonl
    canonical_path_scores.jsonl
    causal_contrast_agreement.json
    threshold_sensitivity.json

  phase5_devices/
    device_pool.json
    cross_device_replay.jsonl
    device_acceptance.json

  analysis/
    canonical_path_readiness.json
    numerical_drift_characterization.json
    causal_continuity.json
    figures/

  summaries/
    a6000_calibration_v2_summary.md
    a6000_calibration_v2_acceptance.json
    stage3c9_restart_authorization.md
```

---

# 39. Required Tables / Figures

At minimum:

1. P1 one-shot cached memory usage vs prefix length;
2. canonical-path decision table;
3. if P2 is required, earliest-divergence localization;
4. same-path deterministic replay table;
5. self-patch/selectivity audit;
6. W8/W16 Stage 3C.9 mechanical audit;
7. full vs historical-cache vs canonical absolute D diagnostic;
8. causal suppression-loss agreement across paths;
9. causal rescue-gain agreement across paths;
10. strong/medium sign-agreement table;
11. threshold sensitivity at 0.025/0.05/0.10/0.15;
12. cross-A6000 device replay;
13. final readiness checklist.

---

# 40. Stop Condition

First complete:

```text
canonical path selection
→ internal validation
→ causal-contrast bridge
→ device validation
→ readiness classification
```

If and only if:

```text
PASS — A6000 CANONICAL PATH READY
```

then proceed to:

```text
Stage 3C.9 A6000-only clean restart from 0/600
```

Do not start any new scientific mechanism experiment during this repair/calibration stage.

The objective is only to place Stage 3C.9 on a single, defensible numerical execution protocol.
