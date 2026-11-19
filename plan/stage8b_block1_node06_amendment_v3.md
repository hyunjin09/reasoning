# Block1 resource amendment v3: both logical workers on node06

2026-09-19T07:20:08.666996+00:00: user explicitly requests two GPUs from node06, then specifies
launch rank0 there and preserve rank1. This supersedes only v2 placement.

- Cancel node03 pending job118034 with zero runtime; no rank0 outputs existed.
- Preserve node06 rank1 job118035, completed35/35 tasks with GPU parity passing.
  Its GPU was automatically released after29s; do not rerun it or reserve a
  second idle GPU now that it has completed.
- Run the unchanged rank0 shard (36 tasks) on one node06 GPU through the project
  scheduler/Slurm:4CPU,16G,2h maximum. The v3 entry changes only expected node
  and execution-manifest path; all original scientific files remain immutable.
- Assemble on a dependent CPU-only Slurm job (0GPU/2CPU/8G/30min), using the
  v3 rank0 receipt and preserved v2 rank1 receipt. Release GPUs at shard exit.
- Cohort, definitions,4000 bootstrap resamples,seed1234,task order and statistics
  unchanged. Preserve all original v1/v2 freezes and cancellation evidence.
