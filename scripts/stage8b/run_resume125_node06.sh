#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname -- "${BASH_SOURCE[0]}")/../.."
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=code:.:infra
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export TMPDIR="$PWD/runs/stage8b1a/tmp" MPLCONFIGDIR="$PWD/outputs/stage8b1a/audit/matplotlib_cache"
export NCCL_P2P_DISABLE=1 NCCL_CUMEM_ENABLE=0 NCCL_IB_DISABLE=1
export NCCL_SOCKET_IFNAME=eth2 TORCH_NCCL_ASYNC_ERROR_HANDLING=1
stage8b1a_resume_config=outputs/stage8b1a/config/resume125_node06_v1.json
on_exit() {
  local stage8b1a_rc=$?
  trap - EXIT
  .venv/bin/python scripts/stage8b/finish_resume125.py --config "$stage8b1a_resume_config" --exit-code "$stage8b1a_rc"
  exit "$stage8b1a_rc"
}
trap on_exit EXIT
# Two Slurm parents, each bound to one GPU. Children inherit binding; no NCCL group.
for stage8b1a_phase in benchmark_single benchmark_double; do
  srun --kill-on-bad-exit=1 --nodes=1 --ntasks=2 --cpus-per-task=8 --cpu-bind=none --gres=gpu:2 --gpus-per-task=1 --gpu-bind=single:1 .venv/bin/python scripts/stage8b/run_node06_parent.py --config "$stage8b1a_resume_config" --phase "$stage8b1a_phase"
done
.venv/bin/python scripts/stage8b/select_shared_layout.py --config "$stage8b1a_resume_config"
srun --kill-on-bad-exit=1 --nodes=1 --ntasks=2 --cpus-per-task=8 --cpu-bind=none --gres=gpu:2 --gpus-per-task=1 --gpu-bind=single:1 .venv/bin/python scripts/stage8b/run_node06_parent.py --config "$stage8b1a_resume_config" --phase census
