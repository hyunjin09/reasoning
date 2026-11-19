"""Submit only explicit frozen manifests through the project scheduler."""
import argparse,os,shlex,subprocess
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage12br.common import ROOT,PREFIX,ALLOWED_NODES,load,save,sha,now
from scripts.stage12br.resources import account
from scripts.stage12br.protocol import authorize_manifest

def main(label,manifests,minutes):
    assert 5<=minutes<=60 and 1<=len(manifests)<=8
    for p in manifests:
        m=load(p);assert m['frozen'];authorize_manifest(m)
    ledger=account('prelaunch_'+label)
    worst=ledger['committed_gpu_hours_upper']+len(manifests)*minutes/60
    assert worst<=1.0,'Hard1.0GPUh includes all earlier work and full new allocation limits'
    args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
    project=Path.cwd();status=scheduler.gpu_status(args,scheduler.load_gpu_queue(project))
    assert not status['warnings'] and status['own_gpus']+len(manifests)<=8
    save(ROOT/'audit'/f'{label}_envelope.json',dict(at=now(),prospective_gpu_hours=worst,minutes=minutes,manifests=manifests,scheduler_status=status))
    ids=set()
    for i,p in enumerate(manifests):
        ident=PREFIX+label+f'_{i}';ids.add(ident)
        command=shlex.join(['bash','scripts/stage12br/run.sh','scripts/stage12br/worker.py',p,'--manifest-sha256',sha(p)])
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
            '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--mem','28G','--cpus','4',
            '--allow-slurm-pending','--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
            '--command',command,'--log-path',f'runs/stage12br/v1/{label}_{i}/slurm.log','--result-path',str(ROOT)],check=True)
    jobs=[j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in ids]
    assert all(j['status']=='queued' for j in jobs)
    os.environ['SBATCH_TIMELIMIT']=f'{minutes//60:02d}:{minutes%60:02d}:00'
    planned=scheduler.plan_jobs({'jobs':jobs},status);assert len(planned)==len(jobs)
    for j in planned:
        assert not j['node'] or j['node'] in ALLOWED_NODES
        scheduler.execute_launch(project,j)
    jobs=[j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in ids]
    save(ROOT/'audit'/f'{label}_launch.json',dict(at=now(),jobs=jobs))
    print('FINITE_STAGE12BR_WAVE',[(j['id'],j['slurm_job_id']) for j in jobs])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('manifests',nargs='+');p.add_argument('--minutes',type=int,required=True)
    a=p.parse_args();main(a.label,a.manifests,a.minutes)
