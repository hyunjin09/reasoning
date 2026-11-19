# Phase: A6000 Calibration v2 + Stage 3C.9 Restart

## Current Objective

Validate one canonical A6000 cached execution path, then restart and complete Stage 3C.9 from 0/600 only if all v2 readiness gates pass.

## Active Constraints

- Preserve `outputs/a6000_calibration/` as immutable v1 FAIL evidence.
- Use only the four A6000 GPUs in tmux session 9 / Slurm job 108085; request no new allocation.
- P1 historical one-shot cache is preferred; P2 fixed streaming is allowed only if P1 fails memory feasibility.
- Choose P1/P2 and any P2 chunk size from memory/mechanics only, never scientific effects.
- Use one canonical path for every within-event causal condition.
- Preserve model, BF16 dtype, eager language attention, software, seeds, score D, event taxonomy, W8/W16, and the 0.05 Stage 3C.9 threshold.
- Never mix partial A5000 Stage 3C.9 trajectories with the A6000 restart.
- No new scientific mechanism experiment beyond the already approved Stage 3C.9 plan.

## Current State

- Done: v1 calibration is immutable FAIL under its full/cache `1e-5` equality gate.
- Done: v1 deterministic full replay, full-path self patches, GQA architecture, finite scoring, and base-74 memory fit passed.
- Done: historical one-shot cache and full BF16 recomputation were confirmed deterministically non-identical.
- Done: user explicitly approved `plan/a6000_calibration_v2_stage3c9_restart_plan.md`.
- Done: four A6000s on node07 are idle and available through tmux session 9.
- Done: P1 was rejected after the frozen longest-prefix base 351 OOMed.
- Done: P2 selected fixed 2,048-token streaming with allocator-cache release; all six memory stresses passed below 90% reserved VRAM.
- Done: corrected authoritative 12-base validation passed deterministic replay, K/V/KV/event/residual self patches, selectivity, W8/W16, event/neighbor, local/final, GQA/RoPE/indexing, and finite-output checks.
- Done: 24/24 strong/medium suppression/KV-rescue/residual-rescue signs were preserved; target suppression exceeded irrelevant-ROI suppression on 8/8 bases.
- Done: all four allocated A6000s passed strong, medium, small, and 30,574-token long-prefix probes; short-probe values were identical across devices.
- Done: calibration v2 is `PASS — A6000 CANONICAL PATH READY` on 17/17 criteria.
- In progress: freeze the Stage 3C.9 A6000 implementation and cleanly restart prospective generation from 0/600.
- Blocked tooling: project-local `research-control` skill is absent; the explicit plan supplies this bounded action.

## Evidence That Matters

| Evidence | Source | Relevance |
|---|---|---|
| v1 immutable failure | `outputs/a6000_calibration/summaries/a6000_calibration_summary.md` | Prevents retroactive relabeling |
| BF16 path diagnosis | `outputs/a6000_calibration/layer_a_internal/cached_vs_full.json` | Justifies fixed-path contrasts |
| A5000 OOM | `workspace/phase_memory/phase_3c9_long_horizon_checkpoints.md` | Requires A6000 memory feasibility |
| frozen historical cohort | `outputs/a6000_calibration/config/calibration_cohort.json` | Defines v2 continuity set without v1 effect selection |
| original Stage 3C.9 rules | `outputs/stage3c9/config/` | Scientific protocol must remain unchanged |

## Next-Step Decision

- Bottleneck: the existing Stage 3C.9 tree contains 54 A5000 outcomes and its launch/scoring scripts were frozen for three A5000 ranks and 128-token chunks.
- Selected action: preserve that tree as A5000 provenance, initialize a clean A6000 tree with the same outcome-blind 600-example prospective selection, freeze four A6000 ranks and the validated 2,048-token scorer, then regenerate all 600 trajectories.
- Selection basis: retain the prospectively frozen static MathVerse order; do not reuse any A5000 generation outcome or carrier result.
- Pre-screen validity: calibration v2 supplies the required A6000 mechanics, deterministic replay, cross-device, and long-prefix validation; cross-path full/cached equality remains diagnostic only.
- Stop condition: any clean-restart provenance mismatch, runtime drift, failed rank, or later original Stage 3C.9 gate stops execution without mixing A5000 evidence.

### Step Result

- Action taken: completed calibration-v2 canonical-path selection and readiness validation.
- Result: `PASS — A6000 CANONICAL PATH READY` (17/17).
- Evidence saved: `outputs/a6000_calibration_v2/`.
- Next implication: the plan authorizes exactly the clean A6000 Stage 3C.9 restart from 0/600; no new mechanism stage is authorized.
