#!/usr/bin/env bash
set -euo pipefail
cd /data/projects/hyunjin/MLLM/reasoning_steps
test "$(hostname -s)" = node02
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python - <<'PY'
import json,os,platform,subprocess
from pathlib import Path
from datetime import datetime,timezone
p=Path('runs/stage7a_bench/mmlong_node02_2gpu_20260915/allocation.json')
assert not p.exists()
gpus=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,memory.total,uuid','--format=csv,noheader'],text=True)
p.write_text(json.dumps(dict(at_utc=datetime.now(timezone.utc).isoformat(),slurm_job_id=os.environ['SLURM_JOB_ID'],slurm_step_id=os.environ.get('SLURM_STEP_ID'),node=platform.node(),job_gpus=os.environ.get('SLURM_JOB_GPUS'),cpus=os.environ.get('SLURM_CPUS_PER_TASK'),node_gpu_inventory=gpus,authorized_gpus=2,scope='Allocation metadata only; no CUDA workload.'),indent=2)+'\n')
print(p.read_text(),flush=True)
PY
exec bash --noprofile --norc
