# A6000 Platform Calibration Summary

## Decision

**FAIL — A6000 PLATFORM NOT READY (F1 scoring-path parity failure).** Stage 3C.9 restart is not authorized.

This is an implementation/methods result, not a scientific finding about the model or hardware.

## What was frozen before scoring

The hardware migration amendment, 12-base historical cohort, four-device pool, software/model configuration, and `1e-5` token/aggregate parity tolerances were persisted before any A6000 calibration score. The partial A5000 Stage 3C.9 screen remains provenance-only and was not mixed into this calibration.

## Risk-first Layer A result

Base 74 was run first on A6000 GPU UUID `GPU-d2516130-3b52-5a2b-afd5-77efd3c612c1` with three deterministic repeats in original and counterfactual image conditions.

- Deterministic full-path replay: passed for native, source-suppressed, and K+V rescue scores and captured states.
- Full-path K-only, V-only, K+V, and residual self patches: passed in native→native and suppressed→suppressed controls.
- Architecture: 36 language layers, 32 logical query heads, 8 KV heads, 4 query heads per KV group, head dimension 128.
- All executed scores: finite.
- Peak allocated GPU memory: 9,150,241,792 bytes.

The mandatory parity gate failed. Across original/counterfactual conditions and native/suppressed/KV-rescue paths, full-versus-bounded differences ranged from `0.0203` to `2.9393` in aggregate D and from `0.1481` to `8.8680` in token log probability, far above `1e-5`.

## Focused diagnosis

A single predeclared follow-up compared full recomputation, the historical one-shot cache path, and streaming cache paths on the same frozen base.

- One-shot cache versus full also failed: aggregate |ΔD| was `0.0998` (O) and `0.0342` (C).
- Streaming chunk-size sensitivity was nonzero: aggregate |ΔD| was `0.1018` (O) and `0.000042` (C) between full-prefix and one-token chunks.
- This reproduces the already documented Stage 3B.0 observation that BF16 full and cached execution use different matrix shapes and are deterministic but not numerically identical.

Thus the result does not support a simple stochastic-device or token-coordinate failure. It does show that the current frozen `1e-5` full/cache equivalence criterion is not met by the existing BF16 implementation.

## Stop handling

The plan's F1 rule says to stop before Stage 3C.9 and fix scoring implementation. Therefore Layers B, C, and D were not run; their required paths contain explicit `NOT_RUN` records. No device pool was accepted, no cross-hardware scientific continuity claim was made, and Stage 3C.9 was not restarted.

## Required next decision

The next action needs review because it would amend the calibration design. The cleanest candidate is to define all Stage 3C.9 causal contrasts against matched recipient/source baselines within one fixed cached/chunked execution path, then prospectively validate deterministic replay, self-patch exactness, selectivity, and chunking sensitivity. Another option is a different scoring implementation that genuinely matches full recomputation under the frozen dtype. Neither change was made here.
