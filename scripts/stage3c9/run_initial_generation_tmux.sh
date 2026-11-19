#!/usr/bin/env bash
set -euo pipefail

cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONPATH=code:.
exec .venv/bin/torchrun \
  --standalone \
  --nproc_per_node=4 \
  scripts/stage3c9/run_initial_generation.py
