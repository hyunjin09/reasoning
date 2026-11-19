**MAIN GENERATION COMPLETE — 2026-09-26T12:07:28.611200+00:00.** Review,primary inference,87 deferred controls and final reporting remain. AllGPUs released.

Earlier resource checkpoints below are historical.

**Resource amendment — 2026-09-25T01:32:39.039435+00:00.** Stage9A resource amendment:8 main GPUs RUNNING. Added node02 workers122753–122756; retained121814(node02),121805/121806(node07),121996(node06). Coordinator122752 enforces8 including pending and restricts future added workers to node02. All50 readouts complete; same frozen1904 main queue and87 deferred controls. Remaining compute estimate231GPU-hours /29h with8GPUs (planning20–43h), plus review/queue time. [Resource addendum](stage9a_resource_addendum_8gpu_20260925.md).

Earlier entries below are historical.

# Active checklist — Stage9A compute amendment v1

Updated 2026-09-24T08:23:11.658176+00:00. [Frozen amendment](stage9a_compute_amendment_v1.md).

- [x] Stop old coordinator and all four workers at durable rollout boundaries; preserve78 outputs.
- [x] Freeze64 main/64 reserve families without masked outcomes; freeze next32/final32 reserve tiers.
- [x] Materialize1904 main continuations,8 exact reuse references,87 deferred controls; retain50 readouts.
- [x] Five amendment artifacts, timing-based compute estimate, four amendment checks; original GPU validation unchanged.
- [x] Report seven requested items before relaunch; start only amended main/readout work.
- [x] Finish1896 new main continuations and50 local readouts; all1904 results/192 bundles hash-verified2026-09-26.
- [ ] Freeze literal answer extraction review; fixed-adapter scores and three primary scientific groups.
- [ ] Run87 bounded null-sink controls after main results; query-text only if its positive-effect gate passes.
- [ ] Assess optional next32 extension only against all frozen criteria; do not launch it automatically.
- [ ] Final required artifacts, five figures, exactly one recommendation, release GPUs and STOP.

Initial estimate277GPU-hours, planning194–415; currentthree-GPU compute ETA roughlyfour days. No allocation held for keepalive. No Stage9B.

## Historical exhaustive checklist — superseded

# Stage9A direct visual-access dynamics: execution checklist

Active approved plan: `stage9a_direct_cot_thinking_visual_access_dynamics_plan.md`.
Frozen implementation specification: `stage9a_dynamics_execution_protocol_v1.md`.
This replaces the cancelled VAB reproduction; historical artifacts stay preserved.

- [x] Reuse128 MathVision families,384 native trajectories,539 accepted demands and50 reviewed local readouts; verify provenance; no download.
- [x] Freeze10,571 condition rows:9,874 unique rollouts,599 proven native identities,98 aliases. No selection using causal outcomes.
- [x] Eight focused CPU tests (seven mask/manifest checks plus one recovery check); all12 actual-model V1–V6/no-op/cache/RNG tests pass on node06.
- [x] Main cumulative,local,demand and null-sink continuations launched on4 Slurm GPUs; exact native prefixes checked for every branch.
- [ ] Finish all9,874 distinct continuations and50 secondary local readout events.
- [ ] Complete literal outcome-masked answer extraction review; preserve raw and reviewed adapter scores.
- [ ] Family-equal4000-draw primary inference with12-contrast multiplicity control; completion/length, subject and readout sensitivities.
- [ ] Produce12 final artifacts and five figures; jointly interpret with the preserved native-use null.
- [ ] If and only if the frozen positive gate is met, perform bounded query-text bypass control; no full grid.
- [ ] Verify all final artifacts, report exactly one recommendation, release GPUs and STOP. No Stage9B launch.

## Resource estimate and continuation

Initial estimate:1,371 GPU-hours,14.3days at4GPUs, excluding queues and review.
It assumes masked lengths resemble native lengths; early masked continuations
already show variable lengths, so this remains provisional. The GPU workload
includes10,220 primary condition rows and351 null-sink rows before deduplication.

Initial workers121703–121705/node06 and121706/node07 each request1GPU/4CPUs/30G
and have a7-day walltime. A zero-GPU Slurm coordinator continues only remaining
conditions after a genuine timeout with verified completed units. It never retries
runtime/model failures or user cancellations automatically. Completed evidence is
immutable; interrupted writes are archived. Its overall submission horizon is30days,
not a claim about completion time or scientific stopping. Maximum simultaneous GPUs4.

The coordinator also launches the frozen50 local readouts when a GPU slot opens.
When GPU assays finish, it exits at the extraction-review/analysis boundary.
It does not fabricate annotations or choose another experiment. Each compute job
releases its allocation at exit; no tmux or keepalive. Stop future submissions by
creating `outputs/stage9a_dynamics/v1/audit/STOP_DISPATCH` before cancelling workers.

Progress: `bash scripts/stage9a_dynamics/run.sh scripts/stage9a_dynamics/status.py`.
Evidence and run receipts: `outputs/stage9a_dynamics/v1`, `runs/stage9a_dynamics/v1`.
