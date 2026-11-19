#!/usr/bin/env bash
set -euo pipefail

cd /data/projects/hyunjin/MLLM/reasoning_steps
mkdir -p runs/stage3c2_passive_full
export PYTHONPATH=code
.venv/bin/torchrun --standalone --nproc_per_node=2 \
  scripts/stage3c2/run_extraction.py \
  --config outputs/stage3c2/config/stage3c2_config.json \
  --manifest outputs/stage3c2/cohort/primary_dissociation_manifest.jsonl \
  --events outputs/stage3b2/annotations/discriminative_event_annotations.jsonl \
  --roi-mapping outputs/stage3b7/roi_audit/roi_token_mapping.jsonl \
  --mention-annotations outputs/stage3c2/annotations/mention_roi_annotations.jsonl \
  --semantic-labels outputs/stage3c2/annotations/semantic_state_labels.jsonl \
  --dataset-root /data/dataset/MathVerse \
  --model-checkpoint /data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e \
  --output-dir outputs/stage3c2/extraction \
  2>&1 | tee runs/stage3c2_passive_full/tmux.log
