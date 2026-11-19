"""Outcome-blind progress and allocation accounting; no answer/correctness reads."""
import argparse
import re
import subprocess
from zoneinfo import ZoneInfo
from scripts.stage14b.common import *


def timestamp(text):
    if not text or text in ('Unknown','None','N/A'):return None
    return dt.datetime.fromisoformat(text).replace(tzinfo=ZoneInfo('Asia/Seoul')).timestamp()

def status(persist=True):
    current=dt.datetime.now(dt.timezone.utc);jobs=[]
    previous={}
    snapshots=sorted((ROOT/'audit/progress').glob('*.json'))
    if snapshots:previous={r['job_id']:r for r in load(snapshots[-1])['jobs']}
    for p in sorted((ROOT/'audit/launches').glob('job_*.json')):
        launch=load(p);job=launch['job'];jid=str(job['slurm_job_id']);old=previous.get(jid,{})
        if old.get('closed'):jobs.append(old);continue
        proc=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True)
        fields=dict(re.findall(r'(\w+)=(\S+)',proc.stdout));state=fields.get('JobState','NOT_IN_SLURM')
        closed=state not in ('RUNNING','PENDING','COMPLETING','CONFIGURING','SUSPENDED')
        start=None if state=='PENDING' else timestamp(fields.get('StartTime')) or old.get('start_timestamp')
        end=timestamp(fields.get('EndTime'))
        if state=='PENDING':hours=0
        elif start:hours=max(0,(end if end and closed else current.timestamp())-start)/3600
        else:hours=old.get('gpu_hours_upper',0)
        worker=ROOT/'audit/workers'/jid;beats=sorted(worker.glob('heartbeat_*.json'))
        exit_record=load(worker/'exit.json') if (worker/'exit.json').exists() else None
        heartbeat=load(beats[-1]) if beats else None
        jobs.append(dict(job_id=jid,queue_id=job['id'],mode=launch['mode'],state=state,node=fields.get('NodeList'),closed=closed,
            start_timestamp=start,gpu_hours_upper=hours,record_available=proc.returncode==0,
            accounting_basis='live Slurm allocation interval' if start else 'pending zero or prior observation; unknown if purged unobserved',
            committed_hours=hours if closed else max(hours,launch['hours']),hours_requested=launch['hours'],
            heartbeat=heartbeat,exit=exit_record,raw_scontrol=proc.stdout,stderr=proc.stderr))
    counts={}
    for mode in ('preflight','main','confirmatory'):
        tt=all_tasks(mode);group={}
        for t in tt:
            key=t['phase']+'_'+t['model_key'];v=group.setdefault(key,dict(total=0,complete=0,attempted=0))
            v['total']+=1
            folders=list((ROOT/'raw'/t['collection']/t['task_id']).glob('attempt_*'))
            v['attempted']+=bool(folders);v['complete']+=any((p/'result.json').exists() for p in folders)
        counts[mode]=group
    result=dict(at=now(),jobs=jobs,counts=counts,allocated_gpu_hours_upper=sum(j['gpu_hours_upper'] for j in jobs),
        active=[j['job_id'] for j in jobs if not j['closed']],completed_stage=False,scientific_outcomes_inspected=False)
    if persist:save(ROOT/'audit/progress'/f'{current.strftime("%Y%m%dT%H%M%S%f")}.json',result)
    return result

if __name__=='__main__':
    r=status();print(json.dumps({k:v for k,v in r.items() if k!='jobs'},indent=2))
    for j in r['jobs']:
        b=j['heartbeat'] or {};print(j['job_id'],j['state'],j['node'],'complete',b.get('completed'),'active',len(b.get('active',[])))
