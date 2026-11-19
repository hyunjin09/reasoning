# Stage8B v2 resource amendment — 2026-09-17

User explicitly requested cancellation of pending116063 and execution on one GPU on node02, then a progress/ETA check. The previous node03 two-GPU request was cancelled before any native output. Latest resource scope is one GPU/node02 via the project scheduler and direct sbatch, no tmux.

Replacement116487 requests1 RTX A6000,8CPUs,50G host RAM and a48-hour hard limit. It releases immediately after the32-item batch or a fatal error. The limit provides headroom over the historical15.55 native GPU-hour serial reference; it is not an expected duration or an idle reservation.

Same32 frozen items, exact order, per-item seed1234, T=1.0, BF16, pixel limits, model, passive features, detector and threshold. One worker processes all32 (not the former rank-zero half). Versioned execution code/config preserve the cancelled two-worker artifacts.23 focused CPU tests pass. Score-blind token-count/time logging is included in actual-device no-op validation.

Actual-device technical parity precedes full-native work; frozen transfer still requires fresh semantic review after generation. No census, paired seeds or causal assay is prequeued. The oldT=0.6 batch remains excluded from the v2 primary cohort.

Evidence: `outputs/stage8b/v2/audit/node03_cancelled_for_single_node02.json`, `outputs/stage8b/v2/audit/single_gpu_release_v1.json`; configuration: `outputs/stage8b/v2/config/transfer32_t1_node02_single_v1.json`. Logs: `runs/stage8b/v2/node02_single/`.

After native completion, use `scripts/stage8b/review_transfer_v2_single.py` for the new sealed review; score with `scripts/stage8b/score_native_v2.py --config outputs/stage8b/v2/config/transfer32_t1_node02_single_v1.json --output <new-analysis-path>`.
