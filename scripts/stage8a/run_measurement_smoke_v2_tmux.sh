#!/usr/bin/env bash
set -euo pipefail
cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=code:.:infra
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export TMPDIR="$PWD/runs/stage8a/tmp"
export MPLCONFIGDIR="$PWD/outputs/stage8a/analysis/matplotlib_cache"
set +e
srun --overlap --jobid=115046 --nodes=1 --ntasks=2 --cpus-per-task=8 --cpu-bind=none --mem=96G --gres=gpu:2 --gpus-per-task=1 --gpu-bind=single:1 --output=runs/stage8a/measurement_smoke_v2_worker_%t.log --error=runs/stage8a/measurement_smoke_v2_worker_%t.log .venv/bin/python -u scripts/stage8a/run_measurement_smoke.py --config outputs/stage8a/config/measurement_smoke_v2.json
stage8a_exit=$?
set -e
.venv/bin/python - "$stage8a_exit" <<'PY'
import json,sys
from pathlib import Path
from datetime import datetime,timezone
from harness_state import mutate_gpu_queue
exit_code=int(sys.argv[1]);out=Path('outputs/stage8a/measurement/smoke_v2')
workers=[out/f'worker{rank}/completed.json' for rank in range(2)]
completed=exit_code==0 and all(p.is_file() and json.loads(p.read_text()).get('completed') for p in workers)
record={'completed':completed,'exit_code':exit_code,'finished_at':datetime.now(timezone.utc).isoformat(),'slurm_job_id':'115046'}
target=out/'wrapper.json';assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(record,indent=2)+'\n')
def update(queue):
    job=next(j for j in queue['jobs'] if j['id']=='stage8a_measurement_smoke_v2')
    job.update(status='succeeded' if completed else 'failed',**record)
mutate_gpu_queue(Path.cwd(),update)
print(json.dumps(record),flush=True)
PY
exit "$stage8a_exit"
