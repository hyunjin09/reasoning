"""Bounded zero-GPU stage support via the mandatory project scheduler."""
import argparse
import subprocess
import sys
from types import SimpleNamespace
from scripts.stage14cv.common import *
sys.path.insert(0,str(Path('infra').resolve()))
import gpu_scheduler as scheduler


def main():
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('command');p.add_argument('--dependency');p.add_argument('--node',default='node07');a=p.parse_args()
    assert a.node in ALLOWED_NODES
    ident=PREFIX+'cpu_'+a.name;project=Path.cwd();index=Path('reports/index.md');old=index.read_text()
    try:
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.', '--id',ident,'--exp-id',ident,
            '--gpu-type','a6000','--gpus','0','--node',a.node,'--mem','6G','--cpus','2',
            '--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
            '--command',a.command,'--log-path',f'runs/stage14cv/cpu_{a.name}/slurm.log','--result-path',str(ROOT)],check=True)
        args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
        queue=scheduler.load_gpu_queue(project);status=scheduler.gpu_status(args,queue)
        plan=scheduler.plan_jobs({'jobs':[j for j in queue['jobs'] if j['id']==ident]},status);assert len(plan)==1
        job=plan[0];assert job['gpus']==0
        command=scheduler.sbatch_args(project,job);command.insert(1,'--time=00:30:00')
        if a.dependency:command.insert(1,'--dependency='+a.dependency)
        Path(job['log_path']).parent.mkdir(parents=True,exist_ok=True)
        result=subprocess.run(command,text=True,capture_output=True,check=True);jid=result.stdout.strip().split(';')[0]
        scheduler.mark_launched(project,job,jid)
        job=next(j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id']==ident)
        save(ROOT/'audit/launches'/f'job_{jid}.json',dict(at=now(),job=job,panel='cpu_'+a.name,model=None,condition=None,
            hours=.5,exact_sbatch_args=command,GPUh_reserved=0))
        print('SUBMITTED_CPU',jid,a.node)
    finally:index.write_text(old)


if __name__=='__main__':main()
