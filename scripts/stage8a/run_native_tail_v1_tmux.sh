#!/usr/bin/env bash
set -euo pipefail
cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=code:.:infra
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export TMPDIR="$PWD/runs/stage8a/tmp"
export MPLCONFIGDIR="$PWD/outputs/stage8a/analysis/matplotlib_cache"
set +e
srun --overlap --jobid=115046 --nodes=1 --ntasks=2 --cpus-per-task=8 --cpu-bind=none --mem=96G --gres=gpu:2 --gpus-per-task=1 --gpu-bind=single:1 --output=runs/stage8a/main_native_tail_v1_worker_%t.log --error=runs/stage8a/main_native_tail_v1_worker_%t.log .venv/bin/python -u scripts/stage8a/run_native_tail.py --config outputs/stage8a/config/main_native_tail_v1.json
stage8a_tail_exit=$?
set -e
.venv/bin/python scripts/stage8a/finish_native_tail.py "$stage8a_tail_exit"
