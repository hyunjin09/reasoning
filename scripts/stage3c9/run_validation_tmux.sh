#!/usr/bin/env bash
set -euo pipefail

cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONPATH=code:.

.venv/bin/torchrun --standalone --nproc_per_node=4 \
  scripts/stage3c9/run_source_sensitivity.py \
  --manifest outputs/stage3c9/cohort/validation_manifest.jsonl \
  --output-dir outputs/stage3c9/audit/raw_source \
  --mode validation --resume --repeat-first

.venv/bin/python scripts/stage3c9/analyze_source_sensitivity.py \
  --raw-root outputs/stage3c9/audit/raw_source \
  --manifest outputs/stage3c9/cohort/validation_manifest.jsonl \
  --role validation

.venv/bin/torchrun --standalone --nproc_per_node=4 \
  scripts/stage3c9/run_checkpoint_rescue.py \
  --manifest outputs/stage3c9/cohort/validation_manifest.jsonl \
  --source-classification outputs/stage3c9/audit/validation_source_sensitive_events.jsonl \
  --output-dir outputs/stage3c9/audit/raw_checkpoint \
  --mode validation --resume --repeat-first --force-all-windows \
  --max-scored-events-per-base 1

.venv/bin/python scripts/stage3c9/analyze_checkpoint_rescue.py \
  --raw-root outputs/stage3c9/audit/raw_checkpoint \
  --manifest outputs/stage3c9/cohort/validation_manifest.jsonl \
  --w8-source outputs/stage3c9/audit/validation_source_sensitivity.jsonl \
  --w16-source outputs/stage3c9/audit/validation_source_sensitivity.jsonl \
  --role validation

.venv/bin/torchrun --standalone --nproc_per_node=4 \
  scripts/stage3c9/run_routes.py \
  --manifest outputs/stage3c9/cohort/validation_manifest.jsonl \
  --output-dir outputs/stage3c9/audit/raw_routes \
  --mode validation --resume --repeat-first

.venv/bin/python scripts/stage3c9/analyze_routes.py \
  --raw-root outputs/stage3c9/audit/raw_routes \
  --role validation

.venv/bin/python scripts/stage3c9/validate_mechanics.py \
  --source-root outputs/stage3c9/audit/raw_source \
  --checkpoint-root outputs/stage3c9/audit/raw_checkpoint \
  --route-root outputs/stage3c9/audit/raw_routes
