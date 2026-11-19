# MMLong launch and bounded startup monitoring

User authorization recorded 2026-09-14T15:01:17.692746+09:00: launch MMLong, monitor a few samples to verify execution, then stop monitoring and leave the native run active. User will return when it finishes. Supersedes the previous prelaunch pause only for this action.

Use existing Slurm113280/node02/tmux10 four A6000 GPUs,32 CPUs,120G. Frozen request `outputs/stage7a_bench_v2/config/mmlongbench_doc_prelaunch_request_20260914_v2.json`, execution_v6b, selection_v6:200 accounted rows/195 ready/5 preserved exclusions in50 four-row batches. No scientific settings or source changes.

1. Verify existing allocation, pinned artifacts/source hashes, no duplicate runs and scheduler availability.
2. Register exact50 prepared jobs through project scheduler, initialize exclusive dispatch and launch within existing allocation.
3. Verify four unique allocated GPUs and exact128-token full-document mechanics; inspect at least four complete native results across workers, including source/input page order, result/generation/token hashes, native cap/settings and progress. Record any runtime failure and bounded repair if necessary. No full semantic-screen or causal-pilot work this action.
4. Save launch/startup evidence, update current state and stop monitoring while the single-benchmark dispatcher continues. Do not automatically start another benchmark or a pilot when native generation finishes.

## Completed 2026-09-14T15:40:20.433983+09:00

All four bounded tasks completed after documented reference-only memory repair. Four GPU preflights pass and five complete native samples across allfour workers verified. Leave MMLong v8 active in113280 step12; stop agent monitoring. No new allocation, dataset, causal pilot or automatic next benchmark. [Handoff](../outputs/stage7a_bench_v2/summaries/mmlong_v8_launch_handoff_20260914.md).
