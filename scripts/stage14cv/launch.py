"""Stage-scoped scheduler submissions with conservative allocation reservations."""
import argparse
import datetime as dt
import re
import shlex
import subprocess
import sys
from types import SimpleNamespace
from scripts.stage14cv.common import *
from scripts.stage14cv.control import budget_check
sys.path.insert(0,str(Path('infra').resolve()))
import gpu_scheduler as scheduler

TERMINAL={'COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','PREEMPTED','BOOT_FAIL','DEADLINE'}


def runtime_hours(value):
    days=0
    if '-' in value:day,value=value.split('-');days=int(day)
    h,m,s=map(int,value.split(':'));return days*24+h+m/60+s/3600


def accounting():
    charges=[]
    for p in sorted((ROOT/'audit/launches').glob('job_*.json')):
        j=load(p);jid=j['job']['slurm_job_id'];receipt=ROOT/'audit/terminal_jobs'/f'{jid}.json'
        if receipt.exists():r=load(receipt)
        else:
            output=subprocess.run(['scontrol','show','job',str(jid),'-o'],text=True,capture_output=True)
            match=re.search(r'JobState=(\S+)',output.stdout);state=match[1] if match else 'UNKNOWN'
            r=dict(at=now(),job_id=jid,state=state,scontrol_stdout=output.stdout,scontrol_stderr=output.stderr)
            if state in TERMINAL:
                elapsed=re.search(r'RunTime=(\S+)',output.stdout);assert elapsed
                r['actual_GPUh']=runtime_hours(elapsed[1])*j['job']['gpus'];save(receipt,r)
        charge=r.get('actual_GPUh',j['hours']*j['job']['gpus'])
        charges.append(dict(job_id=jid,state=r['state'],charge_GPUh=charge,
            basis='Retained terminal Slurm allocation duration' if 'actual_GPUh' in r else 'Full wall-time reservation; live or unavailable record',
            model=j.get('model'),condition=j.get('condition'),panel=j.get('panel')))
    return charges


def launch(panel,model,condition,hours,node=None,allow_pending=False):
    assert panel in {'technical','R','C'} and model in 'IT' and 0<hours<=6
    charges=accounting();budget_check([c['charge_GPUh'] for c in charges],[hours])
    assert not any(c['panel']==panel and c['model']==model and c['condition']==condition and c['state'] not in TERMINAL for c in charges),'Duplicate active queue'
    selected=[t for t in tasks(panel) if t['model_key']==model and (panel=='technical' or t['condition']==condition)]
    assert selected and any(checked(t) is None and not missing_path(t).exists() for t in selected),'Queue already finished'
    if panel=='technical':assert hours<=1,'Reserve2GPUh for the two technical workers'
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')
    manifest=dict(at=now(),panel=panel,model_key=model,rows=selected,requested_hours=hours)
    authorize(manifest)
    args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
    project=Path.cwd();status=scheduler.gpu_status(args,scheduler.load_gpu_queue(project))
    assert not status['warnings'] and status['remaining_user_slots']>=1,status
    assert allow_pending or status['available_gpus']['a6000']>=1,status
    stem=f'{panel}_{model}_{condition or "all"}_{stamp}';mp=ROOT/'audit/shards'/f'{stem}.json';save(mp,manifest)
    ident=PREFIX+stem;command=shlex.join(['bash','scripts/stage14cv/run.sh','-m','scripts.stage14cv.runner',str(mp),'--manifest-sha256',sha(mp)])
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
            reserved_total_GPUh=sum(c['charge_GPUh'] for c in charges)+hours,approved_ceiling_GPUh=24))
        print('SUBMITTED',jid,job['node'],panel,model,condition,flush=True)
    finally:index.write_text(old)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['technical','R','C']);p.add_argument('model',choices=['I','T'])
    p.add_argument('--condition');p.add_argument('--hours',type=float,required=True);p.add_argument('--node');p.add_argument('--allow-pending',action='store_true')
    a=p.parse_args();launch(a.panel,a.model,a.condition,a.hours,a.node,a.allow_pending)
