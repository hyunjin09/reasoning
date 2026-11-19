#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 DATASET_ROOT MODEL_CHECKPOINT OUTPUT_DIR" >&2
  exit 2
fi

dataset_root=$1
model_checkpoint=$2
output_dir=$3

source .venv/bin/activate
export PYTHONPATH=code
python scripts/stage0/run_stage0.py \
  --mode smoke \
  --num-examples 3 \
  --dataset-root "$dataset_root" \
  --model-checkpoint "$model_checkpoint" \
  --output-dir "$output_dir" \
  --max-new-tokens 2048 \
  --plot-examples 3
