#!/usr/bin/env bash
set -euo pipefail

cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONPATH=code

mkdir -p runs/stage3b6_tmux
exec > >(tee -a runs/stage3b6_tmux/pipeline.log) 2>&1

echo "Stage 3B.6 pipeline started at $(date --iso-8601=seconds)"
echo "Slurm job: ${SLURM_JOB_ID:-unknown}; node: $(hostname); visible GPUs: ${CUDA_VISIBLE_DEVICES:-Slurm-default}"
nvidia-smi --query-gpu=index,name,uuid,memory.total --format=csv,noheader

.venv/bin/python scripts/stage3b6/run_head_path_scoring.py \
  --manifest outputs/stage3b6/config/shards/discovery/discovery_00.jsonl \
  --annotations outputs/stage3b2/annotations/discriminative_event_annotations.jsonl \
  --config outputs/stage3b6/config/stage3b6_config.json \
  --dataset-root /data/dataset/MathVerse \
  --model-checkpoint /data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e \
  --stage3b5-raw-root outputs/stage3b5 \
  --output-dir outputs/stage3b6/discovery/raw/mechanics_smoke \
  --phase discovery \
  --required-gpu-class A5000 \
  --discovery-head-count 1 \
  --max-bases 1 \
  --repeat-first

.venv/bin/python -c 'import json; p=json.load(open("outputs/stage3b6/discovery/raw/mechanics_smoke/result.json")); assert p["all_mechanical_controls_passed"] and p["determinism_repeat"]["exact_public_result_match"]'

.venv/bin/torchrun --standalone --nproc_per_node=2 scripts/stage3b6/launch_two_shards.py \
  --phase discovery \
  --manifest-dir outputs/stage3b6/config/shards/discovery \
  --output-root outputs/stage3b6/discovery/raw

.venv/bin/python scripts/stage3b6/aggregate_discovery.py

.venv/bin/torchrun --standalone --nproc_per_node=2 scripts/stage3b6/launch_two_shards.py \
  --phase primary \
  --manifest-dir outputs/stage3b6/config/shards/primary \
  --output-root outputs/stage3b6/scoring/raw \
  --candidate-freeze outputs/stage3b6/config/frozen_head_candidates.json

.venv/bin/torchrun --standalone --nproc_per_node=2 scripts/stage3b6/launch_two_shards.py \
  --phase upstream \
  --manifest-dir outputs/stage3b6/config/shards/upstream \
  --output-root outputs/stage3b6/scoring/raw \
  --candidate-freeze outputs/stage3b6/config/frozen_head_candidates.json

.venv/bin/python scripts/stage3b6/aggregate_primary.py

if .venv/bin/python -c 'import json,sys; p=json.load(open("outputs/stage3b6/analysis/source_path_targets.json")); sys.exit(0 if p["gate_passed"] else 1)'; then
  .venv/bin/torchrun --standalone --nproc_per_node=2 scripts/stage3b6/launch_two_shards.py \
    --phase source \
    --manifest-dir outputs/stage3b6/config/shards/source \
    --output-root outputs/stage3b6/scoring/raw \
    --candidate-freeze outputs/stage3b6/config/frozen_head_candidates.json \
    --source-targets outputs/stage3b6/analysis/source_path_targets.json
fi

.venv/bin/python scripts/stage3b6/aggregate_source_and_report.py
.venv/bin/python scripts/stage3b6/validate_artifacts.py
echo "Stage 3B.6 pipeline completed at $(date --iso-8601=seconds)"
