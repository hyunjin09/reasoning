"""Stage-scoped finite Slurm submissions, respecting live capacity and GPU cap."""
import argparse
import os
import shlex
import subprocess
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage14c.common import *
from scripts.stage14c.d1_worker import authorize
from scripts.stage14c.oom_policy import missing_path


def main(mode,n_i,n_t,hours):
    assert mode=='D1' and 1<=n_i+n_t<=4
    assert 0<hours and (n_i+n_t)*hours<=12
    cfg_sha=sha(ROOT/'spec/model_and_recipe_identity.json');tasks=all_tasks(mode)
    manifests=[];stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')
    for model,n in [('I',n_i),('T',n_t)]:
        selected=[t for t in tasks if t['model_key']==model and checked_result(t) is None and not missing_path(t).exists()]
        assert not selected or n>0
        for k in range(n):
            subset=selected[k::n]
            if not subset:continue
            p=ROOT/'audit/shards'/f'{mode}_{model}_{k}_{stamp}.json'
            manifest=dict(at=now(),mode=mode,model_key=model,config_sha256=cfg_sha,rows=subset,attempt=0)
            authorize(manifest);save(p,manifest);manifests.append(p)
    assert manifests
    # Conservative reservation: count every prior requested allocation-hour in
    # full until an explicit audited closeout releases its unused reservation.
    prior=sum(load(p)['hours'] for p in (ROOT/'audit/launches').glob('job_*.json'))
    assert not any(load(p)['mode']=='D1' for p in (ROOT/'audit/launches').glob('job_*.json')), 'One bounded D1 wave only'
    assert prior+len(manifests)*hours<=120,'Hard stage ceiling'
    args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
    project=Path.cwd();status=scheduler.gpu_status(args,scheduler.load_gpu_queue(project))
    assert not status['warnings'] and status['remaining_user_slots']>=len(manifests),status
    active=subprocess.run(['squeue','-u',os.environ.get('USER','hyunjin'),'-h','-o','%i|%j|%T'],capture_output=True,text=True,check=True).stdout
    assert not any(PREFIX in line for line in active.splitlines()),'Stage job already active: do not duplicate'
    saved_index=Path('reports/index.md').read_text();ids=[]
    try:
        for p in manifests:
            ident=PREFIX+p.stem;ids.append(ident)
            command=shlex.join(['bash','scripts/stage14c/run.sh','-m','scripts.stage14c.d1_worker',str(p),'--manifest-sha256',sha(p)])
            subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
                '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--mem','28G','--cpus','4',
                '--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
                '--command',command,'--log-path',f'runs/stage14c/{p.stem}/slurm.log','--result-path',str(ROOT)],check=True)
        jobs=[j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in ids]
        plan=scheduler.plan_jobs({'jobs':jobs},status)
        assert len(plan)==len(jobs),('insufficient live capacity; queues preserved, nothing submitted',len(plan),len(jobs))
        save(ROOT/'audit/launches'/f'{mode}_{stamp}_planned.json',dict(at=now(),status=status,jobs=plan,hours=hours))
        os.environ['SBATCH_TIMELIMIT']=f'{int(hours):02d}:{round((hours%1)*60):02d}:00'
        for job in plan:
            assert job['node'] in ALLOWED_NODES
            scheduler.execute_launch(project,job)
            registered=next(j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id']==job['id'])
            save(ROOT/'audit/launches'/f"job_{registered['slurm_job_id']}.json",dict(at=now(),hours=hours,mode=mode,job=registered))
            print('SUBMITTED',registered['slurm_job_id'],registered['node'],registered['id'],flush=True)
    finally:Path('reports/index.md').write_text(saved_index)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('--instruct',type=int,default=1);p.add_argument('--thinking',type=int,default=1);p.add_argument('--hours',type=float,default=2)
    a=p.parse_args();main(a.mode,a.instruct,a.thinking,a.hours)
