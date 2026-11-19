#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 5 || $# -gt 7 ]]; then
  echo "usage: $0 DATASET_ROOT MODEL_CHECKPOINT MANIFEST OUTPUT_DIR MAX_NEW_TOKENS [PROTOCOL] [SEED]" >&2
  exit 2
fi

source .venv/bin/activate
export PYTHONPATH=code
python scripts/stage1/run_generation.py \
  --manifest "$3" \
  --dataset-root "$1" \
  --model-checkpoint "$2" \
  --output-dir "$4" \
  --max-new-tokens "$5" \
  --mode faithfulness \
  --protocol "${6:-greedy}" \
  --seed "${7:-0}" \
  --max-example-output-mb 512
