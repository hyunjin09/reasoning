#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=code:. PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export TMPDIR="$PWD/runs/stage7a_bench/tmp"
export MPLCONFIGDIR="$PWD/outputs/stage7a_bench_v2/analysis/matplotlib_cache"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
test "${SLURM_JOB_ID:-}" = 113280
test "${SLURM_JOB_NODELIST:-}" = node02
srun --overlap --jobid=113280 --nodes=1 --ntasks=4 --cpus-per-task=8 \
  --mem=120G --gres=gpu:4 --gpus-per-task=1 --gpu-bind=single:1 \
  --kill-on-bad-exit=0 .venv/bin/python scripts/stage7a_bench/parallel_native_v4.py
