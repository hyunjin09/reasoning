#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 5 ]]; then
  echo "usage: $0 CONDITION DATASET_ROOT MODEL_CHECKPOINT MANIFEST OUTPUT_DIR" >&2
  exit 2
fi

source .venv/bin/activate
export PYTHONPATH=code
python scripts/stage1/run_protocol_40960.py \
  --condition "$1" \
  --dataset-root "$2" \
  --model-checkpoint "$3" \
  --manifest "$4" \
  --output-dir "$5"
