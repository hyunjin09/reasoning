#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=code:. PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export TMPDIR="$PWD/runs/stage7a/tmp"
export MPLCONFIGDIR="$PWD/outputs/stage7a/analysis/matplotlib_cache"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
mkdir -p "$TMPDIR" "$MPLCONFIGDIR"
test "${SLURM_JOB_ID:-}" = 111485
test "${SLURM_JOB_NODELIST:-}" = node06
runner="$1"
shift
case "$runner" in mechanics|generation|events|passive|probes|prepare_objects|prepare_cohort|utilization) ;; *) exit 2 ;; esac
.venv/bin/python "scripts/stage7a/run_${runner}.py" "$@"
