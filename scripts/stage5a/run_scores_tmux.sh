#!/usr/bin/env bash
set -euo pipefail
cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONPATH=code:. PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
test -n "${SLURM_JOB_ID:-}"
.venv/bin/torchrun --standalone --nproc_per_node=4 scripts/stage5a/run_scores.py "$@"
