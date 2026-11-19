#!/usr/bin/env bash
set -euo pipefail
cd /data/projects/hyunjin/MLLM/reasoning_steps
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=code:.:infra
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export TMPDIR="$PWD/runs/stage8a/tmp"
export MPLCONFIGDIR="$PWD/outputs/stage8a/analysis/matplotlib_cache"
# Wait only for the already-authorized calibration; never start a new cohort.
.venv/bin/python - <<'PY'
import json, subprocess, time
from pathlib import Path
from harness_state import mutate_gpu_queue,now_iso
p=Path('outputs/stage8a/native/calibration_v2/wrapper.json')
while not p.exists():
    status=subprocess.check_output(['squeue','-h','-j','115046','-o','%T'],text=True).strip()
    if status != 'RUNNING':
        raise RuntimeError('Authorized allocation unavailable: '+status)
    time.sleep(20)
assert json.loads(p.read_text())['completed'], 'Native calibration failed; stop mechanics'
workers=[json.loads((p.parent/f'worker{rank}/completed.json').read_text()) for rank in range(2)]
assert sum(w['examples'] for w in workers)==12
assert sum(w['normal_eos'] for w in workers)>=10, 'Normal-EOS calibration requirement not met'
def update(q):
    job=next(j for j in q['jobs'] if j['id']=='stage8a_mechanics_v1')
    job.update(status='running',slurm_job_id='115046',started_at=now_iso(),launcher='existing_allocation_srun')
mutate_gpu_queue(Path.cwd(),update)
print('Native calibration complete; launching registered mechanics within115046.',flush=True)
PY
set +e
srun --overlap --jobid=115046 --nodes=1 --ntasks=2 --cpus-per-task=8 --cpu-bind=none --mem=96G --gres=gpu:2 --gpus-per-task=1 --gpu-bind=single:1 --output=runs/stage8a/mechanics_v1_worker_%t.log --error=runs/stage8a/mechanics_v1_worker_%t.log .venv/bin/python -u scripts/stage8a/run_mechanics.py --config outputs/stage8a/config/mechanics_v1.json
stage8a_exit=$?
set -e
.venv/bin/python - "$stage8a_exit" <<'PY'
import json,sys
from pathlib import Path
from harness_state import mutate_gpu_queue,now_iso
out=Path('outputs/stage8a/mechanics/v1');exit_code=int(sys.argv[1])
completed=exit_code==0 and all((out/f'worker{r}/completed.json').is_file() and json.loads((out/f'worker{r}/completed.json').read_text())['completed'] for r in range(2))
record=dict(completed=completed,exit_code=exit_code,finished_at=now_iso(),slurm_job_id='115046')
out.mkdir(parents=True,exist_ok=True);target=out/'wrapper.json';assert not target.exists();target.write_text(json.dumps(record,indent=2)+'\n')
def update(q):
    job=next(j for j in q['jobs'] if j['id']=='stage8a_mechanics_v1')
    job.update(status='succeeded' if completed else 'failed',**record)
mutate_gpu_queue(Path.cwd(),update)
print(json.dumps(record),flush=True)
PY
exit "$stage8a_exit"
