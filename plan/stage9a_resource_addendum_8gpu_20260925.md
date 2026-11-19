# Stage9A resource addendum: eight GPUs

Timestamp: 2026-09-25T01:31:38.249474+00:00

Explicit user instruction: "run with 4 more gpus from node02. so 8 total gpus."
This supersedes only the four-GPU resource ceiling in the active Stage9A compute amendment. The original amendment and historical resource estimates remain preserved.

Retain workers121805/121806(node07),121814(node02),121996(node06). Add four independent node02 workers122753–122756 through the project scheduler, each1GPU/4CPUs/30G, seven-day maximum walltime. Total ceiling8 includes pending GPU reservations; each worker exits when its queue is finished. No tmux or idle keepalive.

Coordinator122749 stopped cleanly for this configuration change;122752 replaces it with `--max-gpus 8 --worker-node node02`, the same2026-10-24T08:19:45.705104+00:00 horizon and frozen main task inventory. Future new workers are restricted to node02. Existing workers continue uninterrupted. Seven focused scheduler/manifest/timeout tests pass.

The added workers prefer three Direct tasks and one Thinking task, based only on frozen-native estimated remaining costs (Direct86GPUh,Thinking70,CoT40) and existing twoCoT/twoThinking workers. Atomic task-directory claims and completed receipts prevent duplicate work. Workers fall back to other arms when their preferred arm is exhausted.

Main64 families/1904 continuations, all128 original families,384 native trajectories,539 demands,50 original readouts,87 deferred controls, reserve gates and all scientific semantics are unchanged. All50 readouts have completed. Added capacity does not authorize reserve execution, an expanded grid, deferred controls before main results, or Stage9B. All frozen configuration/selection/condition hashes verified unchanged.

At this checkpoint 467/1904 main continuations are complete. Estimated remaining compute is230.9GPU-hours, approximately28.9hours with all8 GPUs busy (planning20–43hours). Review/queue/startup time is additional. Method and fit assumptions are in `audit/gpu_scale8_20260925/resource_estimate.json`.

Evidence: `outputs/stage9a_dynamics/amendment_v1/audit/gpu_scale8_20260925/` (authorization, archived coordinator, test log, launch receipts and resource estimate).
