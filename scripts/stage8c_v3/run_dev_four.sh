#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=code:.:infra
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TMPDIR="$PWD/runs/stage8c_v3/tmp"
mkdir -p "$TMPDIR"
record_exit() {
  run_exit_code=$?
  .venv/bin/python scripts/stage8c_v3/record_exit_four.py --exit-code "$run_exit_code" || true
}
trap record_exit EXIT
srun --nodes=1 --ntasks=4 --gpus-per-task=1 --cpus-per-task=4 --gpu-bind=single:1 --kill-on-bad-exit=1 \
  .venv/bin/python scripts/stage8c_v3/run_arm_four.py --config outputs/stage8c_v3/v1/audit/resume_four_v1/dev_config.json
.venv/bin/python scripts/stage8c_v3/finish_dev_four.py
