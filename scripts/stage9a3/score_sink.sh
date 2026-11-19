#!/usr/bin/env bash
set -euo pipefail
bash scripts/stage9a3/run.sh scripts/stage9a3/postprocess.py score --model "$1" --stage sink
bash scripts/stage9a3/run.sh scripts/stage9a3/bounded_controls.py analyze --model "$1"
