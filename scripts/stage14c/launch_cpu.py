"""Bounded Stage14C CPU support submissions through the project scheduler."""
import argparse, subprocess, sys
from types import SimpleNamespace
from scripts.stage14c.common import *
sys.path.insert(0,str(Path('infra').resolve()))
import gpu_scheduler as s

def main():
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('command');p.add_argument('--result',required=True);p.add_argument('--mem',default='6G');p.add_argument('--dependency');p.add_argument('--node',default='node06');a=p.parse_args();assert a.node in ALLOWED_NODES
    ident=PREFIX+'cpu_'+a.name;project=Path.cwd();index=Path('reports/index.md');old=index.read_text()
    try:
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.', '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','0','--node',a.node,'--mem',a.mem,'--cpus','2','--exclude-node','node01','--exclude-node','node04','--exclude-node','node05','--command',a.command,'--log-path',f'runs/stage14c/cpu_{a.name}/slurm.log','--result-path',a.result],check=True)
        queue=s.load_gpu_queue(project);args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
        status=s.gpu_status(args,queue);plan=s.plan_jobs({'jobs':[j for j in queue['jobs'] if j['id']==ident]},status)
        assert len(plan)==1;job=plan[0];assert job['gpus']==0 and job['node'] in ALLOWED_NODES
        command=s.sbatch_args(project,job);command.insert(1,'--time=01:00:00')
        if a.dependency:command.insert(1,'--dependency='+a.dependency)
        Path(job['log_path']).parent.mkdir(parents=True,exist_ok=True)
        result=subprocess.run(command,text=True,capture_output=True,check=True);jid=result.stdout.strip().split(';')[0]
        s.mark_launched(project,job,jid);registered=next(j for j in s.load_gpu_queue(project)['jobs'] if j['id']==ident)
        controller=subprocess.run(['scontrol','show','job',jid,'-o'],text=True,capture_output=True,check=True).stdout
        save(ROOT/'audit/launches'/f'job_{jid}.json',dict(at=now(),hours=1,mode='cpu_'+a.name,job=registered,exact_sbatch_args=command,initial_scontrol=controller))
        print('SUBMITTED',jid,job['node'])
    finally:index.write_text(old)
if __name__=='__main__':main()
