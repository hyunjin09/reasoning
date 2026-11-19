#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=code:. PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
test "${SLURM_JOB_ID:-}" = 110860
.venv/bin/torchrun --standalone --nproc_per_node=2 scripts/stage6b/run_events.py "$@"
