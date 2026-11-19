#!/usr/bin/env bash
# Reuse each existing GPU after its controlled-intact rank exits.
set -euo pipefail
cd /data/projects/hyunjin/MLLM/reasoning_steps
test "${SLURM_JOB_ID:-}" = 109385
test -f outputs/stage6a/cohort/c4_extension_activation.json
export PYTHONPATH=code:. PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export TMPDIR="$PWD/runs/stage6a/tmp"
worker_pids=()
for worker_rank in 0 1 2 3; do
  (
    printf -v shard_name 'shard_%02d' "$worker_rank"
    until test -f "outputs/stage6a/native/controlled_intact/$shard_name/result.json"; do sleep 5; done
    while true; do
      used_mb=$(nvidia-smi --id="$worker_rank" --query-gpu=memory.used --format=csv,noheader,nounits)
      if test "$used_mb" -lt 1000; then break; fi
      sleep 5
    done
    echo "Starting C4 extension rank $worker_rank after controlled GPU release"
    LOCAL_RANK="$worker_rank" WORLD_SIZE=4 .venv/bin/python scripts/stage6a/run_generation.py \
      --manifest outputs/stage6a/cohort/c4_extension_manifest.jsonl --run c4_extension
  ) &
  worker_pids+=("$!")
done
worker_failed=0
for worker_pid in "${worker_pids[@]}"; do
  wait "$worker_pid" || worker_failed=1
done
exit "$worker_failed"
