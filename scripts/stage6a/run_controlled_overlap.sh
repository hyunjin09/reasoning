#!/usr/bin/env bash
# Use idle ranks in the existing allocation; never interrupt a native response.
set -euo pipefail
cd /data/projects/hyunjin/MLLM/reasoning_steps
test "${SLURM_JOB_ID:-}" = 109385
export PYTHONPATH=code:. PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export TMPDIR="$PWD/runs/stage6a/tmp"
mkdir -p "$TMPDIR"
worker_pids=()
for worker_rank in 0 1 2 3; do
  (
    # Each C4 rank owns this GPU until both its completion record exists and
    # its model process has released memory. No device visibility is reassigned.
    printf -v shard_name 'shard_%02d' "$worker_rank"
    until test -f "outputs/stage6a/native/c4_primary/$shard_name/result.json"; do sleep 5; done
    while true; do
      used_mb=$(nvidia-smi --id="$worker_rank" --query-gpu=memory.used --format=csv,noheader,nounits)
      if test "$used_mb" -lt 1000; then break; fi
      sleep 5
    done
    echo "Starting controlled rank $worker_rank after C4 GPU release"
    LOCAL_RANK="$worker_rank" WORLD_SIZE=4 .venv/bin/python scripts/stage6a/run_generation.py \
      --manifest outputs/stage6a/cohort/controlled_intact_manifest.jsonl --run controlled_intact
  ) &
  worker_pids+=("$!")
done
worker_failed=0
for worker_pid in "${worker_pids[@]}"; do
  wait "$worker_pid" || worker_failed=1
done
exit "$worker_failed"
