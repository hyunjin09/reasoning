#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname -- "${BASH_SOURCE[0]}")/../.."
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=code:.:infra
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export TMPDIR="$PWD/runs/stage8b1a/tmp" MPLCONFIGDIR="$PWD/outputs/stage8b1a/audit/matplotlib_cache"
stage8b1a_config=outputs/stage8b1a/config/census224_node02_v1.json
on_exit() {
  local stage8b1a_rc=$?
  trap - EXIT
  .venv/bin/python scripts/stage8b/finish_census224.py --config "$stage8b1a_config" --exit-code "$stage8b1a_rc"
  exit "$stage8b1a_rc"
}
trap on_exit EXIT
srun --kill-on-bad-exit=1 --nodes=1 --ntasks=4 --cpus-per-task=8 --cpu-bind=none --gres=gpu:4 --gpus-per-task=1 --gpu-bind=single:1 --output=runs/stage8b1a/node02/preflight_%t.log --error=runs/stage8b1a/node02/preflight_%t.log .venv/bin/python scripts/stage8b/run_native_v2_four.py --config "$stage8b1a_config" --phase preflight
srun --kill-on-bad-exit=1 --nodes=1 --ntasks=4 --cpus-per-task=8 --cpu-bind=none --gres=gpu:4 --gpus-per-task=1 --gpu-bind=single:1 --output=runs/stage8b1a/node02/census224_%t.log --error=runs/stage8b1a/node02/census224_%t.log .venv/bin/python scripts/stage8b/run_native_v2_four.py --config "$stage8b1a_config" --phase census
