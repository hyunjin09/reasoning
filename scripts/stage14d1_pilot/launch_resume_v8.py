"""Submit fixed recovery work with user-authorized two-day Slurm limits."""
import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path('infra').resolve()))
import gpu_scheduler as scheduler
from scripts.stage14d1_pilot.common import P,load,save,sha,now


def main(path):
    m=load(path);ident='sava14d1_pilot_'+m['id']
    assert m['wall_seconds']==172800 and m['mode']=='resume_main'
    receipt=P/'audit/launches'/f'{ident}.json';assert not receipt.exists()
    opts=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
    status=scheduler.gpu_status(opts,scheduler.load_gpu_queue(Path.cwd()))
    assert status['remaining_user_slots']>=1
    command=shlex.join(['env','VLLM_ENABLE_V1_MULTIPROCESSING=0','bash','scripts/stage14d1/run.sh',
                        '-m','scripts.stage14d1_pilot.worker_resume_v8',path])
    index=Path('reports/index.md').read_text()
    try:
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
            '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--mem','16G','--cpus','1',
            '--allow-slurm-pending','--command',command,'--log-path',f'runs/stage14d1_pilot/{ident}/slurm.log',
            '--result-path',str(P/'raw'/m['id'])],check=True,capture_output=True,text=True)
        selected=[j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==ident]
        plans=scheduler.plan_jobs({'jobs':selected},status);assert len(plans)==1
        os.environ['SBATCH_TIMELIMIT']='2-00:00:00'
        scheduler.execute_launch(Path.cwd(),plans[0])
        job=next(j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id']==ident)
        save(receipt,dict(at=now(),job=job,manifest_sha256=sha(path),slurm_time_seconds=172800,
             resource_authority=m['user_resource_amendment'],actual_accounting_required=True,
             prior_actual_gpu_seconds=45658,capacity_at_submission=status))
        print('SUBMITTED',job['slurm_job_id'],ident)
    finally:
        Path('reports/index.md').write_text(index)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('manifest');main(p.parse_args().manifest)
