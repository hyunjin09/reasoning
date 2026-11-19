#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=code:. PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export TMPDIR="$PWD/runs/stage7a_bench/tmp"
export MPLCONFIGDIR="$PWD/outputs/stage7a_bench_v2/analysis/matplotlib_cache"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
mkdir -p "$TMPDIR" "$MPLCONFIGDIR"
test "${SLURM_JOB_ID:-}" = 114451
test "${SLURM_JOB_NODELIST:-}" = node02
workers=2
step_memory=90G
for argument in "$@"; do
  if [[ "$argument" == --mechanics ]]; then workers=1; step_memory=50G; fi
done
srun --overlap --jobid=114451 --nodes=1 --ntasks="$workers" --cpus-per-task=8 --cpu-bind=none \
  --mem="$step_memory" --gres="gpu:$workers" --gpus-per-task=1 --gpu-bind=single:1 --kill-on-bad-exit=1 \
  .venv/bin/python scripts/stage7a_bench/queue_worker_causal_v15.py "$@"
