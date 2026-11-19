# Block1 operational amendment: one GPU per node

2026-09-19, explicitly requested by the user. Replace pending Slurm118016
(two GPUs/node06) with independent single-GPU jobs on node03 and node06.
The old job was cancelled with zero runtime and no analysis outputs.

- Global worker0 runs the original even-indexed tasks on node03 (36 tasks).
- Global worker1 runs the original odd-indexed tasks on node06 (35 tasks).
- Each requests1GPU/4CPU/16G/2h through the project scheduler and Slurm.
- Original task order, input tables,4000 bootstrap resamples, seed1234,
  statistical code, metric definitions and source scientific freeze are unchanged.
- The new entry point differs only in explicit global rank, expected node and
  extended execution manifest. Slurm's own rank/device variables are not altered.
- Each worker performs CPU/GPU parity, records its actual device and releases
  its GPU immediately after its own shard. Neither waits on an allocated GPU.
- A dependent CPU-only scheduler job (0GPU/2CPU/8G/30min) assembles reports and
  five figures after both GPU jobs succeed. It cannot run on partial results.
- Preserve original pending/cancellation evidence and the original frozen worker.
  `execution_freeze_split_v2.json` extends the original source/input freeze;
  `split_result_provenance.json` links the result freeze to actual worker jobs.

At amendment time node06 has one Slurm-free GPU and node03 has none; a node03
queue wait is possible. Do not substitute nodes or use GPUs outside allocations.
This is a placement change only, not a scientific or cohort amendment.
