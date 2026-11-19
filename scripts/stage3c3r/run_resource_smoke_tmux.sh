#!/usr/bin/env bash
set -o pipefail
cd /data/projects/hyunjin/MLLM/reasoning_steps || exit 1
export PYTHONPATH=code:.
.venv/bin/python scripts/stage3c3r/run_gain_scoring.py \
  --mode validation \
  --manifest outputs/stage3c3r/cohort/validation_manifest.jsonl \
  --dataset-root /data/dataset/MathVerse \
  --model-checkpoint /data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e \
  --output-dir outputs/stage3c3r/raw/resource_smoke \
  --max-bases 1 \
  2>&1 | tee runs/stage3c3r_tmux/resource_smoke.log
status=${PIPESTATUS[0]}
echo "__STAGE3C3R_RESOURCE_EXIT__${status}"
exit "${status}"
