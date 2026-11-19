#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
source .venv/bin/activate
export PYTHONPATH=code
python scripts/piqd/phase1_fastv_generation.py "$@"

