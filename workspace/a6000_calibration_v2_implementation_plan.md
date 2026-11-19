# A6000 Calibration v2 + Stage 3C.9 Restart — Implementation Plan

## Objective

Freeze and validate one A6000 cached execution path. Restart Stage 3C.9 from 0/600 only after all 17 v2 readiness criteria pass, then finish the already approved Stage 3C.9 plan and stop.

## Slice 1 — Prospective v2 freeze and P1 feasibility

- Write the immutable v2 amendment, environment/tolerance freeze, and six-case memory-only stress manifest before any v2 score.
- Implement a one-process-per-case historical one-shot-cache stress runner with explicit OOM persistence.
- Acceptance: the manifest is independent of attention/causal effects; P1 is selected only if all six cases are finite, deterministic, and at or below 90% reserved VRAM.
- Verification: unit tests for stress selection/decision logic, JSON validation, and live A6000 stress evidence.

## Slice 2 — P2 only if P1 fails

- Freeze one chunk size from stress-memory feasibility alone.
- Validate one fixed streaming path, first-divergence tensors, deterministic replay, self patches, and selectivity.
- Acceptance: no coordinate, GQA, RoPE, ownership, or condition-dependent chunking mismatch.
- Verification: focused Stage 3C.9 streaming tests plus live stress/mechanics outputs.

## Slice 3 — Internal and historical-contrast calibration

- Reuse the immutable v1 12-base cohort and run the canonical path three times.
- Validate W8/W16, event/neighbor patching, local/final readouts, and historical strong/medium causal signs.
- Acceptance: exact/same-path tolerance mechanics and at least 90% strong/medium sign agreement with no systematic reversal.
- Verification: complete raw manifests, recomputed summaries, and frozen 0.025/0.05/0.10/0.15 threshold table.

## Slice 4 — Device pool and readiness

- Replay four frozen bases on all four tmux-9 A6000s.
- Produce the 17-point readiness decision and required figures/tables.
- Acceptance: every applicable criterion passes on the intended device pool.
- Verification: artifact validator, regression suites, and explicit restart authorization.

## Slice 5 — Conditional Stage 3C.9 clean restart

- Only after `PASS — A6000 CANONICAL PATH READY`, archive the A5000 screen as provenance and create a fresh A6000 output namespace.
- Rerun the eight-base Stage 3C.9 validation, then restart screening at 0/600 using the four frozen A6000s.
- Finish cohort construction and all gated Stage 3C.9 phases under the original scientific thresholds.
- Verification: Stage 3C.9 acceptance report, exactly one recommendation, and no prohibited follow-on.

## Risks

- P1 is expected to stress quadratic one-shot query attention; fail fast on the longest completed case.
- P2 chunk choice may fit ordinary long prefixes but fail the 2,550-visual-token case; the six-case stress set controls this before causal validation.
- The existing partial A5000 namespace must remain immutable and cannot supply A6000 primary outcomes.
- This workspace is not a Git worktree; tests, immutable manifests, hashes, and create-once output trees are the save-point mechanism.
