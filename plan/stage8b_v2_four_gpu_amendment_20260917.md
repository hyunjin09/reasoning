# Stage8B v2 four-GPU amendment —2026-09-17

The user explicitly requests cancellation of the single-GPU run and replacement with four GPUs on node02. Slurm116487 was cancelled at21:41:59KST after43m12s. Item2579 completed (28,346 tokens, normalEOS) and its five artifacts were hash-verified; item2433 was interrupted with only input/manifest artifacts persisted. Preserve all original artifacts/logs and wasted-compute accounting.

Replacement Slurm116610:4GPUs/node02,32CPUs,120G host RAM,24-hour hard limit, project scheduler + direct sbatch, no tmux. Batch releases immediately on completion. The completed item is copied byte-for-byte into the new aggregate output with an explicit source receipt/hash; it is not regenerated. The interrupted item restarts with original seed1234. Remaining31 items are assigned in frozen order to four workers (8/8/8/7), with no omissions or duplicates.

Science unchanged: same32 audit identities, model, T=1.0/BF16 generation, prompt/pixel limits, max40,960/EOS, per-item seed, detector/threshold, semantic audit protocol and scoring.26 focused CPU tests pass. Each of the four GPUs must pass native-token/raw-logit/frozen-feature parity before full-native work. No census, paired or causal jobs prequeued.

Provisional remaining generation estimate4–6h after launch, based on the earlier15.55 native GPUh/4 reference and observed22-minute firstT=1.0 item; only one revised-protocol item completed, so this is not a reliable whole-stage ETA. Interrupted/reused costs remain separately accounted.

Config: `outputs/stage8b/v2/config/transfer32_t1_node02_four_v1.json`. Freeze/reuse receipt: `outputs/stage8b/v2/audit/four_gpu_migration_freeze_v1.json`. Logs: `runs/stage8b/v2/node02_four/`.

After completion use `scripts/stage8b/review_transfer_v2_four.py`; score with `scripts/stage8b/score_native_v2.py --config outputs/stage8b/v2/config/transfer32_t1_node02_four_v1.json --output <new-analysis-path>` after the new semantic reviews are sealed. Historical single-/two-GPU requests remain preserved.
