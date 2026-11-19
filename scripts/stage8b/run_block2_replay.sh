#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=code:.:infra
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export NCCL_P2P_DISABLE=1
export NCCL_CUMEM_ENABLE=0
export NCCL_IB_DISABLE=1
export NCCL_SOCKET_IFNAME=eth2
export TORCH_NCCL_ASYNC_ERROR_HANDLING=1
srun --nodes=1 --ntasks=2 --gpus-per-task=1 --cpus-per-task=4 --gpu-bind=single:1 \
  .venv/bin/python scripts/stage8b/run_block2_replay.py
