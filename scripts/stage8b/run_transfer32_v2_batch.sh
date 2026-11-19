#!/usr/bin/env bash
set -euo pipefail
cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=code:.:infra
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export TMPDIR="$PWD/runs/stage8b/tmp" MPLCONFIGDIR="$PWD/outputs/stage8b/audit/matplotlib_cache"
on_exit() {
  local stage8b_rc=$?
  trap - EXIT
  .venv/bin/python scripts/stage8b/finish_batch_v2.py --exit-code "$stage8b_rc"
  exit "$stage8b_rc"
}
trap on_exit EXIT
srun --kill-on-bad-exit=1 --nodes=1 --ntasks=2 --cpus-per-task=8 --cpu-bind=none --gres=gpu:2 --gpus-per-task=1 --gpu-bind=single:1 --output=runs/stage8b/v2/preflight_%t.log --error=runs/stage8b/v2/preflight_%t.log .venv/bin/python scripts/stage8b/run_native_v2.py --config outputs/stage8b/v2/config/transfer32_t1_v1.json --phase preflight
srun --kill-on-bad-exit=1 --nodes=1 --ntasks=2 --cpus-per-task=8 --cpu-bind=none --gres=gpu:2 --gpus-per-task=1 --gpu-bind=single:1 --output=runs/stage8b/v2/census32_%t.log --error=runs/stage8b/v2/census32_%t.log .venv/bin/python scripts/stage8b/run_native_v2.py --config outputs/stage8b/v2/config/transfer32_t1_v1.json --phase census
