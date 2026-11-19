#!/usr/bin/env bash
set -euo pipefail
bash scripts/stage9a3/run.sh scripts/stage9a3/postprocess.py score --model "$1"
bash scripts/stage9a3/run.sh scripts/stage9a3/figures.py "$1"
