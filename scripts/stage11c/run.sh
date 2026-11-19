#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=code:.:infra
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TMPDIR="$PWD/runs/stage11c/v1/tmp" MPLCONFIGDIR="$PWD/outputs/stage11c/v1/audit/mplconfig"
mkdir -p "$TMPDIR" "$MPLCONFIGDIR"
exec .venv/bin/python "$@"
