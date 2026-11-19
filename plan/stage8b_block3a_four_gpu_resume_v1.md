# Block3A user-approved four-GPU continuation

2026-09-19 UTC. User explicitly requests cancellation of the active two-node02-GPU job and resumption on four node02 GPUs. This supersedes the two-GPU resource constraint only; the scientific plan,128 item/seed tasks, thresholds, anchors and family clarification remain frozen.

Slurm118099 was cancelled at the user's request. Verify and reuse every complete result receipt after terminal cancellation; preserve all partial directories/logs unchanged. Unfinished tasks restart from their original item/seed because this runner has no saved generation KV checkpoint. Never regenerate a completed task.

Use scheduler-managed sbatch on node02 only:4 A6000 GPUs,16 CPUs,160G host memory (within200G policy cap),36-hour ceiling, no tmux. Reuse the same-node validated two-processes/GPU layout; eight workers each pass baseline-versus-observed128-token parity and comparison against the existing same-seed technical reference before any continuation sample. Verify four distinct GPU UUIDs with two workers each. A failed gate stops the job.

Freeze the remaining task list and balance the eight worker queues by discovery trajectory length (timing information only). No outcome-based resampling or extra seeds. New outputs live in a separate continuation directory; a receipt index combines the14 preserved and114 resumed tasks for subsequent review. The batch releases its allocation on exit. Review/replication gates and conditional causal work remain unchanged.

Acceptance: previous allocation terminal and released; all reused artifacts hash-valid; resumed and reused IDs form the exact128-task freeze without overlap; four-node02-GPU Slurm job starts, all eight checks pass and native token progress is observed.
