#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=code:.:infra
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TMPDIR="$PWD/runs/stage9a/v1/tmp"
export MPLCONFIGDIR="$PWD/outputs/stage9a/v1/audit/mplconfig"
mkdir -p "$TMPDIR" "$MPLCONFIGDIR"
.venv/bin/python "$@"
