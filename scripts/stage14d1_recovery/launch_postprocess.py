import os,subprocess,shlex
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage14d1_recovery.contracts import *
assert not (R/'audit/cpu_launch.json').exists()
parent=str(load(R/'audit/launch.json')['job']['slurm_job_id'])
ident='sava14d1_recovery_report_v1_20261019'
args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
status=scheduler.gpu_status(args,scheduler.load_gpu_queue(Path.cwd()))
command=shlex.join(['.venv/bin/python','-m','scripts.stage14d1_recovery.postprocess'])
saved=Path('reports/index.md').read_text()
try:
    subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
        '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','0','--node','node03',
        '--mem','4G','--cpus','1','--command',command,
        '--log-path',f'runs/stage14d1_recovery/{ident}/slurm.log','--result-path',str(R/'reports/technical_recovery_report.md')],
        check=True,capture_output=True,text=True)
    selected=[j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==ident]
    plans=scheduler.plan_jobs({'jobs':selected},status);assert len(plans)==1
    os.environ['SBATCH_TIMELIMIT']='00:10:00'
    os.environ['SBATCH_DEPENDENCY']='afterany:'+parent
    scheduler.execute_launch(Path.cwd(),plans[0])
    job=next(j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==ident)
    save(R/'audit/cpu_launch.json',dict(at=now(),job=job,dependency='afterany:'+parent,
        requested_GPUs=0,postprocess_script_sha256=sha('scripts/stage14d1_recovery/postprocess.py')))
    print('CPU_REPORT_SUBMITTED',job['slurm_job_id'])
finally:
    Path('reports/index.md').write_text(saved)
