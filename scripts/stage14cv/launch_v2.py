"""Stage-scoped scheduler submissions with conservative allocation reservations."""
import argparse
import datetime as dt
import re
import shlex
import subprocess
import sys
from types import SimpleNamespace
from scripts.stage14cv.common import *
from scripts.stage14cv.operational_v2 import check_amended_budget as budget_check, authorize_v2, approval
from scripts.stage14cv.launch import accounting
sys.path.insert(0,str(Path('infra').resolve()))
import gpu_scheduler as scheduler

TERMINAL={'COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','PREEMPTED','BOOT_FAIL','DEADLINE'}


def launch(panel,model,condition,hours,node=None,allow_pending=False):
    assert panel in {'technical','R','C'} and model in 'IT' and 0<hours<=6
    approval();charges=accounting();budget_check([c['charge_GPUh'] for c in charges],[hours])
    queue_now=subprocess.run(['squeue','-u','hyunjin','-h','-o','%i'],text=True,capture_output=True,check=True)
    live_ids=set(queue_now.stdout.split())
    assert not any(c['panel']==panel and c['model']==model and c['condition']==condition and str(c['job_id']) in live_ids for c in charges),'Duplicate active queue'
    selected=[t for t in tasks(panel) if t['model_key']==model and (panel=='technical' or t['condition']==condition)]
    context_ids=[]
    if panel=='technical':
        c='C1' if model=='I' else 'R2'
        selected=[t for t in selected if t['condition']==c]
        context_ids=[t['task_id'] for t in selected]
    elif panel=='R':
        p=load(ROOT/'audit/time_limit_recovery_proposal_v1.json')
        context_ids=p['context_replay_ids']
        allowed=set(context_ids+p['interrupted_ids']+p['unstarted_ids'])
        selected=[t for t in selected if t['task_id'] in allowed]
    assert selected and (bool(context_ids) or any(checked(t) is None and not missing_path(t).exists() for t in selected)),'Queue already finished'
    if panel=='technical':assert hours<=1,'Reserve2GPUh for the two technical workers'
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')
    manifest=dict(at=now(),panel=panel,model_key=model,rows=selected,requested_hours=hours,context_ids=context_ids,operational_version=2)
    authorize_v2(manifest)
    args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
    project=Path.cwd();status=scheduler.gpu_status(args,scheduler.load_gpu_queue(project))
    assert not status['warnings'] and status['remaining_user_slots']>=1,status
    assert allow_pending or status['available_gpus']['a6000']>=1,status
    stem=f'{panel}_{model}_{condition or "all"}_{stamp}';mp=ROOT/'audit/shards'/f'{stem}.json';save(mp,manifest)
    ident=PREFIX+stem;command=shlex.join(['bash','scripts/stage14cv/run.sh','-m','scripts.stage14cv.runner_v2',str(mp),'--manifest-sha256',sha(mp)])
    index=Path('reports/index.md');old=index.read_text()
    try:
        cmd=['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.', '--id',ident,'--exp-id',ident,
            '--gpu-type','a6000','--gpus','1','--mem','28G','--cpus','4',
            '--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
            '--command',command,'--log-path',f'runs/stage14cv/{stem}/slurm.log','--result-path',str(ROOT)]
        if node:assert node in ALLOWED_NODES;cmd+=['--node',node]
        if allow_pending:cmd+=['--allow-slurm-pending']
        subprocess.run(cmd,check=True)
        registered=[j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id']==ident]
        planned=scheduler.plan_jobs({'jobs':registered},status);assert len(planned)==1
        job=planned[0];assert job['node'] in ALLOWED_NODES or (allow_pending and not job['node'])
        total_seconds=round(hours*3600);h,rem=divmod(total_seconds,3600);mi,se=divmod(rem,60)
        sbatch=scheduler.sbatch_args(project,job);sbatch.insert(1,f'--time={h:02}:{mi:02}:{se:02}')
        Path(job['log_path']).parent.mkdir(parents=True,exist_ok=True)
        result=subprocess.run(sbatch,text=True,capture_output=True,check=True);jid=result.stdout.strip().split(';')[0]
        scheduler.mark_launched(project,job,jid)
        job=next(j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id']==ident)
        save(ROOT/'audit/launches'/f'job_{jid}.json',dict(at=now(),job=job,panel=panel,model=model,condition=condition,
            hours=hours,exact_sbatch_args=sbatch,prior_charges=charges,
            reserved_total_GPUh=sum(c['charge_GPUh'] for c in charges)+hours,approved_ceiling_GPUh=32))
        print('SUBMITTED',jid,job['node'],panel,model,condition,flush=True)
        subprocess.run(['.venv/bin/python','-m','scripts.stage14cv.submit_cpu','account_'+str(jid),
            ".venv/bin/python -c 'from scripts.stage14cv.launch import accounting; print(accounting())'",
            '--dependency','afterany:'+str(jid)],check=True)
    finally:index.write_text(old)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['technical','R','C']);p.add_argument('model',choices=['I','T'])
    p.add_argument('--condition');p.add_argument('--hours',type=float,required=True);p.add_argument('--node');p.add_argument('--allow-pending',action='store_true')
    a=p.parse_args();launch(a.panel,a.model,a.condition,a.hours,a.node,a.allow_pending)
