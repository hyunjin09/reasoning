#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
source .venv/bin/activate
export PYTHONPATH=code
python scripts/piqd/phase2_query_extraction.py "$@"
