# Implementation Plan: A6000 Platform Calibration

## Objective

Execute `plan/a6000_platform_calibration_plan.md` as one bounded methods action on the four A6000 GPUs already assigned to tmux session 9. Establish internal numerical/mechanical validity, cross-device consistency, historical qualitative continuity, and Stage 3C.9 long-prefix readiness. Stop after the 20-point platform decision; do not restart Stage 3C.9 in this action.

## Material assumptions

- The historical bridge cell is one frozen `(base_problem_id, target_id)` pair per base; this avoids counting Target A and Target B from one problem as independent calibration examples.
- Archived Stage 3C.7 sign-aligned `t_pre` target-ROI suppression loss is the prospective stratification statistic. It is used only to select strong, medium, and small calibration cells.
- The long-prefix cases use preserved, completed-correct Stage 3C.9 A5000 trajectories for mechanics/provenance only. Their A5000 generations are never eligible for a future A6000 Stage 3C.9 primary cohort.
- Base 751 is the longest mechanically usable preserved Stage 3C.9 trajectory among the 12 historical bridge bases.
- The frozen numerical tolerances are `1e-5` for token log probabilities, aggregate preference scores, and self-patch recipient reproduction. They will not be relaxed after observing A6000 results.

## Dependency order

Configuration freeze → pure validation utilities → one-device risk-first smoke → full Layer A → cross-device Layer B → historical Layer C → long-prefix Layer D → independent artifact validation and reports.

## Task 1: Freeze provenance, cohort, devices, and tolerances

Acceptance criteria:

- Hardware migration amendment contains all nine required declarations.
- Exactly 12 unique bases are frozen as 4 strong, 4 medium, and 4 small cells.
- Three preserved long-prefix cases and four cross-device replay cells are identified.
- Model/runtime hashes, software versions, device UUIDs, and tolerances are persisted before A6000 scoring.

Verification:

- JSON schema/invariant tests fail before preparation logic exists, then pass.
- A pre-score freeze audit records zero A6000 result files at freeze time.

## Task 2: Implement and test calibration metrics/audits

Acceptance criteria:

- Pure functions compute exact replay deltas, parity maxima, effect direction/class, and continuity statistics.
- Selectivity and GQA/RoPE audits reject malformed layouts or unintended position changes.
- Acceptance aggregation exposes every one of the 20 plan criteria.

Verification:

- Focused unit tests pass under `.venv`.

## Task 3: Risk-first one-device scoring smoke

Acceptance criteria:

- One short calibration cell runs on A6000 GPU 0 with the frozen eager/bfloat16/runtime stack.
- Full and bounded-cache native, suppressed, and K+V-rescue scores are finite.
- Full-versus-bounded deltas satisfy the prospective `1e-5` tolerance.

Verification:

- Stop before scaling on any parity, cache-layout, self-patch, or selectivity failure.

## Task 4: Complete Layer A

Acceptance criteria:

- All 12 cells have three deterministic native/suppressed/K+V replay measurements.
- Every cell that fits both execution paths has token and aggregate parity results.
- Native and suppressed self patches cover K, V, K+V, residual, and event-span mechanics on the validation subset.
- Selectivity, 36-layer/32-head/8-KV-head layout, post-RoPE K, projected V, and finiteness are audited.

Verification:

- Layer A output validator passes every mandatory internal criterion.

## Task 5: Complete Layer B

Acceptance criteria:

- The frozen strong, medium, adjacent, and long cells are replayed on all four assigned A6000 devices.
- No device-specific mechanical failure or OOM occurs.
- Strong effects preserve sign and broad class across devices.

Verification:

- Device UUIDs and per-device comparisons are persisted; anomalous-device decisions are explicit.

## Task 6: Complete Layer C

Acceptance criteria:

- Archived A5000 and new A6000 scores are paired for visual-content direction, target-versus-irrelevant ROI specificity, prior-token K+V rescue, and the frozen residual subset.
- Median/max absolute drift, Spearman correlation, sign agreement, and strong-class agreement are reported.
- The pre-frozen 0.25 nats/token sensitivity band remains descriptive and does not alter Stage 3C.9 thresholds.

Verification:

- Strong/medium continuity is evaluated over independent frozen cells and no threshold is tuned post hoc.

## Task 7: Complete Layer D

Acceptance criteria:

- Three preserved long trajectories, including base 751, run without OOM, truncation, or backend fallback.
- W8/W16 suppression, event-span K+V rescue, equal-width neighbor control, and both local/final readouts are mechanically validated on at least four annotated events.
- Route ordering is dry-run on two to three mechanically eligible cases.

Verification:

- Exact coordinate, state-ownership, and non-target invariance audits pass.

## Task 8: Review, figures, and stop

Acceptance criteria:

- All required output files and at least ten required figures/tables exist.
- The final acceptance file reports PASS/FAIL for exactly 20 criteria.
- `stage3c9_restart_authorization.md` contains exactly one platform outcome and explicitly confirms Stage 3C.9 was not started.

Verification:

- Focused and inherited regression tests pass.
- A five-axis code/artifact review records no unresolved correctness issue.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Full versus bounded execution differs beyond tolerance | Run this as the first GPU gate and stop immediately if it fails. |
| Historical scripts hard-code A5000 | Use calibration-local runners that call the validated runtime primitives without modifying historical outputs or configs. |
| Long traces create temporary memory spikes | Keep eager attention, DynamicCache, and 128-query chunks; record peak allocated/reserved VRAM. |
| Cross-device comparison accidentally shares one GPU | Pin one process to each of CUDA devices 0–3 and persist UUIDs. |
| Calibration drifts into scientific inference | Report only methods continuity and mechanics; stop before Stage 3C.9 restart. |

