import os,subprocess,shlex
from types import SimpleNamespace
from pathlib import Path
import gpu_scheduler as scheduler
from scripts.stage14d1_recovery.contracts import *
assert not (R/'audit/launch.json').exists()
assert load(R/'audit/cpu_preflight.json')['status']=='PASS'
assert load(R/'audit/model_integrity.json')['status']=='PASS'
assert 4800<=remaining_seconds(1421,[])
ident='sava14d1_recovery_v1_20261019'
command=shlex.join(['bash','scripts/stage14d1/run.sh','-m','scripts.stage14d1_recovery.run'])
args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
status=scheduler.gpu_status(args,scheduler.load_gpu_queue(Path.cwd()))
assert status['remaining_user_slots']>=1
save(R/'audit/capacity_at_submission.json',dict(at=now(),status=status))
saved=Path('reports/index.md').read_text()
try:
    subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
        '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--allow-slurm-pending',
        '--mem','28G','--cpus','1','--command',command,'--log-path',f'runs/stage14d1_recovery/{ident}/slurm.log',
        '--result-path',str(R)],capture_output=True,text=True,check=True)
    selected=[j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==ident]
    plans=scheduler.plan_jobs({'jobs':selected},status);assert len(plans)==1
    os.environ['SBATCH_TIMELIMIT']='01:20:00'
    scheduler.execute_launch(Path.cwd(),plans[0])
    job=next(j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==ident)
    save(R/'audit/launch.json',dict(at=now(),job=job,maximum_additional_GPU_seconds=4800,
          prior_allocated_GPU_seconds=1421,total_reserved_GPU_seconds=6221,technical_limit_seconds=7200))
    print('SUBMITTED',job['slurm_job_id'])
finally:
    Path('reports/index.md').write_text(saved)
