#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=code:. PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export TMPDIR="$PWD/runs/stage7a_bench/tmp"
export MPLCONFIGDIR="$PWD/outputs/stage7a_bench_v2/analysis/matplotlib_cache"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
mkdir -p "$TMPDIR" "$MPLCONFIGDIR"
test "${SLURM_JOB_ID:-}" = 111485
test "${SLURM_JOB_NODELIST:-}" = node06
.venv/bin/python scripts/stage7a_bench/queue_worker_images_v2.py "$@"
