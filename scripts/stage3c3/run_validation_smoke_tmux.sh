#!/usr/bin/env bash
set -euo pipefail

cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONPATH=code:.
mkdir -p runs/stage3c3

.venv/bin/torchrun --standalone --nproc_per_node=2 \
  scripts/stage3c3/run_query_scoring.py \
  --config outputs/stage3c3/config/stage3c3_config.json \
  --manifest outputs/stage3c3/cohort/validation_manifest.jsonl \
  --dataset-root /data/dataset/MathVerse \
  --model-checkpoint /data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e \
  --output-dir outputs/stage3c3/smoke/query_forms \
  --forms both \
  --conditions O \
  --max-bases 1 \
  --baseline-audit \
  --repeat-first \
  2>&1 | tee runs/stage3c3/validation_smoke.log
