#!/usr/bin/env bash
set -euo pipefail
cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONPATH=code:.
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
test "${SLURM_JOB_ID:-}" = 108548
for role in lifetime necessity; do
  count=$(.venv/bin/python -c 'import json,sys; print(len(json.load(open("outputs/stage3c9r/analysis/" + sys.argv[1] + "_tasks.json"))["tasks"]))' "$role")
  if [ "$count" -gt 0 ]; then
    .venv/bin/torchrun --standalone --nproc_per_node=4 scripts/stage3c9r/run_scores.py --role "$role" --resume
  else
    echo "$role: NOT RUN, no gate-eligible tasks"
  fi
done
.venv/bin/python scripts/stage3c9r/finish_analysis.py
.venv/bin/python scripts/stage3c9r/make_figures.py
.venv/bin/python scripts/stage3c9r/validate_outputs.py
.venv/bin/python scripts/stage3c9r/write_reports.py
