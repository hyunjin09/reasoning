#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname -- "${BASH_SOURCE[0]}")/../.."
block1_part="${1:?expected worker 0, worker 1, or assemble}"
case "$block1_part" in 0|assemble) ;; *) exit 2;; esac
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=code:.:infra
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export TMPDIR="$PWD/runs/stage8b_block1/tmp"
export MPLCONFIGDIR="$PWD/outputs/stage8b_block1/v1/audit/matplotlib_cache"
export NCCL_P2P_DISABLE=1 NCCL_CUMEM_ENABLE=0 NCCL_IB_DISABLE=1
export NCCL_SOCKET_IFNAME=eth2 TORCH_NCCL_ASYNC_ERROR_HANDLING=1
on_exit() {
  local block1_rc=$?
  trap - EXIT
  .venv/bin/python scripts/stage8b/finish_block1_node06_v3.py --part "$block1_part" --exit-code "$block1_rc"
  exit "$block1_rc"
}
trap on_exit EXIT
if [[ "$block1_part" == assemble ]]; then
  .venv/bin/python scripts/stage8b/assemble_block1.py
else
  export STAGE8B_BLOCK1_WORKER_RANK="$block1_part"
  srun --kill-on-bad-exit=1 --nodes=1 --ntasks=1 --cpus-per-task=4 --cpu-bind=none --gres=gpu:1 --gpus-per-task=1 --gpu-bind=single:1 .venv/bin/python scripts/stage8b/run_block1_node06_v3.py
fi
