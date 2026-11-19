# Phase: A6000 Platform Calibration

## Current Objective

Calibration is complete with a prospective F1 stop. Review the scoring-path failure before selecting any redesign; Stage 3C.9 remains unauthorized.

## Active Constraints

- Use only the four A6000 GPUs already allocated in tmux session 9 / Slurm job 108085 on node07.
- Change hardware only; preserve model, dtype, eager attention, software stack, generation, seed, scoring, cache, intervention, and Stage 3C.9 scientific definitions.
- Never mix partial A5000 Stage 3C.9 trajectories into a future A6000 primary cohort.
- Cross-hardware bit equality is not required; A6000 internal parity and qualitative continuity of strong effects are required.
- Do not start Stage 3C.9 or any new scientific experiment during calibration.

## Current State

- Done: Stage 3C.9 A5000 screening stopped after a valid long-prefix OOM; partial artifacts are preserved.
- Done: user explicitly authorized the A6000 calibration and designated tmux session 9 as the persistent four-GPU allocation.
- Done: job 108085 was verified running on node07 with four 49,140 MiB NVIDIA RTX A6000 devices.
- Done: pre-score amendment, cohort, device-pool, software, and tolerance freeze occurred before any A6000 score.
- Done: a risk-first three-repeat base-74 A6000 smoke passed deterministic replay, full-path K/V/KV/residual self patches, architecture checks, and finite scoring.
- Failed: native full-prefix versus bounded-cache scoring exceeded the frozen `1e-5` parity tolerance in both O and C conditions.
- Done: one focused diagnostic showed the historical one-shot cache path also differs from full recomputation and that cache chunk size can change BF16 scores.
- Stopped: Layers B--D and Stage 3C.9 were not run under the plan's F1 rule.
- Blocked: project-local `research-control` skill is absent; the explicit plan and user authorization define this bounded methods action.
- Most recent useful observation: prior A6000/A5000 drift was small relative to strong effects but material near the 0.05 Stage 3C.9 floor, so within-cohort hardware mixing is invalid.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| A5000 long-prefix OOM | `workspace/phase_memory/phase_3c9_long_horizon_checkpoints.md` | Motivates migration without changing scientific protocol | confirmed |
| Historical hardware drift | `outputs/stage3b3_redesign/config/node03_drift_analysis.json` | Defines the prospective 0.25 sensitivity band | confirmed |
| Frozen Stage 3C.9 protocol | `outputs/stage3c9/config/` | Must remain scientifically unchanged | confirmed |
| Existing bounded-cache runtime | `code/visual_reasoning/stage3c9/streaming.py` | Supplies the memory-bounded eager-attention path | confirmed |
| Existing intervention runtimes | `code/visual_reasoning/stage3c7/runtime.py`; `code/visual_reasoning/stage3c9/runtime.py` | Supply previously validated cache/residual/source mechanics | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| A5000 Stage 3C.9 screen | OOM on a valid large-image/long-prefix case | supported VRAM limitation | calibrate and restart entirely on A6000 | do not mix A5000 and A6000 Stage 3C.9 samples |
| Earlier one-base A6000 reproduction | median 0.125 and max 0.250 D drift versus A5000 | supported hardware-sensitive floating drift | require internal parity and qualitative strong-effect continuity, not bit equality | do not retune the 0.05 scientific floor |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| A6000 platform ready | Larger VRAM with same architecture/software may preserve mechanics and strong effects | execute all four calibration layers | open |
| Scoring-path mismatch | Chunked and full execution use different BF16 matrix shapes | full, one-shot-cache, and streaming comparison on base 74 | confirmed; exceeds frozen tolerance |
| Device anomaly | Future work spans physical cards | fixed four-base replay on all four UUIDs | open |

## Next-Step Decision

- Current bottleneck: the existing BF16 full and cache execution paths do not satisfy the prospectively frozen `1e-5` equivalence criterion.
- Relevant evidence: on base 74, one-shot-cache versus full |ΔD| was `0.0998` (O) and `0.0342` (C); streaming/full discrepancies were larger for some intervention arms.
- Chosen next action: none. A redesign choice would amend the calibration protocol and requires review.
- Candidate for review: compare all causal contrasts within one frozen matched cache/chunk path, with new prospective deterministic, self-patch, selectivity, and chunk-sensitivity validation.
- What not to repeat: do not loosen `1e-5` post hoc, mix hardware, call cached/full mismatch an A6000 scientific effect, or restart Stage 3C.9.
- Stop condition: met with explicit F1 failure and restart denial.

### Step Result

- Action taken: froze and ran the risk-first A6000 calibration smoke, then one focused parity diagnostic.
- Result: **FAIL — F1 full/cached parity**; Stage 3C.9 restart not authorized.
- Evidence saved: `outputs/a6000_calibration/`.
- Failure or issue: full-versus-bounded aggregate |ΔD| ranged `0.0203`--`2.9393` and token-log-probability maxima ranged `0.1481`--`8.8680`, above `1e-5`.
- Lesson learned: deterministic BF16 execution is path- and matrix-shape-sensitive; deterministic replay does not imply full/cache equivalence.
- Next implication: review a prospective scoring-path calibration amendment before any Layer-B/C/D run or Stage 3C.9 restart.
