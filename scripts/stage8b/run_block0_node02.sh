#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname -- "${BASH_SOURCE[0]}")/../.."
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=code:.:infra
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export TMPDIR="$PWD/runs/stage8b_block0/tmp"
on_exit() {
  local block0_rc=$?
  trap - EXIT
  .venv/bin/python scripts/stage8b/finish_block0_job.py --exit-code "$block0_rc"
  exit "$block0_rc"
}
trap on_exit EXIT
srun --kill-on-bad-exit=1 --nodes=1 --ntasks=4 --cpus-per-task=4 --cpu-bind=none --gres=gpu:4 --gpus-per-task=1 --gpu-bind=single:1 .venv/bin/python scripts/stage8b/run_block0.py extract
.venv/bin/python scripts/stage8b/assemble_block0.py moments
srun --kill-on-bad-exit=1 --nodes=1 --ntasks=4 --cpus-per-task=4 --cpu-bind=none --gres=gpu:4 --gpus-per-task=1 --gpu-bind=single:1 .venv/bin/python scripts/stage8b/run_block0.py geometry
.venv/bin/python scripts/stage8b/assemble_block0.py tables
