#!/usr/bin/env bash
set -euo pipefail
cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONPATH=code:. PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export MPLCONFIGDIR=workspace/matplotlib_cache
test "${SLURM_JOB_ID:-}" = 108548
for phase in temporal layers mediation hpre; do
  run_phase=yes
  if [ "$phase" != mediation ]; then
    run_phase=$(.venv/bin/python -c 'import json,sys; print("yes" if json.load(open("outputs/stage3c10/analysis/"+sys.argv[1]+"_tasks.json"))["tasks"] else "no")' "$phase")
  fi
  if [ "$run_phase" = yes ]; then
    bash scripts/stage3c10/run_tmux.sh "$phase"
  fi
  .venv/bin/python scripts/stage3c10/analyze.py --phase "$phase"
done
if [ ! -f outputs/stage3c10/annotations/annotation_freeze.json ]; then
  .venv/bin/python scripts/stage3c10/secondary.py --phase annotations
fi
bash scripts/stage3c10/run_tmux.sh positions
.venv/bin/python scripts/stage3c10/secondary.py --phase analyze
