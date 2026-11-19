#!/usr/bin/env bash
set -euo pipefail
bash scripts/stage9a3/run.sh scripts/stage9a3/postprocess.py score --model qwen25 --split reserve
bash scripts/stage9a3/run.sh scripts/stage9a3/reserve.py combine
bash scripts/stage9a3/run.sh scripts/stage9a3/figures.py qwen25_extended
