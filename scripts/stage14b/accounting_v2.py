"""Evidence-based allocation accounting, including purged Slurm records.

CPU allocations contribute zero GPU-hours. Unobserved terminal duration remains
unknown; a worker exit can supply a explicitly labelled allocation-time proxy.
"""
import re
import subprocess
from zoneinfo import ZoneInfo
from scripts.stage14b.common import *

ACTIVE={'RUNNING','PENDING','CONFIGURING','COMPLETING','SUSPENDED'}


def timestamp(value):
    if not value or value in ('Unknown','None','N/A'):return None
    parsed=dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:parsed=parsed.replace(tzinfo=ZoneInfo('Asia/Seoul'))
    return parsed.timestamp()


def elapsed_accounting(gpus,state,start,end,exit_record,current):
    if not gpus:return dict(gpu_hours=0,basis='CPU-only allocation')
    if state=='PENDING':return dict(gpu_hours=0,basis='Pending, no allocation')
    if state not in ACTIVE and start is not None and end is not None:
        return dict(gpu_hours=max(0,end-start)*gpus/3600,basis='Slurm start/end interval')
    if state in ACTIVE and start is not None:
        return dict(gpu_hours=max(0,current-start)*gpus/3600,basis='Live allocation through snapshot')
    if exit_record:
        hours=(timestamp(exit_record['at'])-start)/3600 if start is not None else exit_record['seconds']/3600
        return dict(gpu_hours=max(0,hours)*gpus,basis='Allocation-to-worker-exit proxy; release tail unavailable' if start is not None else 'Worker-lifetime proxy; allocation startup/release unavailable')
    return dict(gpu_hours=None,basis='Terminal allocation duration unknown; not extrapolated')


def accounting():
    current=dt.datetime.now(dt.timezone.utc);history={}
    for path in sorted((ROOT/'audit/progress').glob('*.json')):
        for row in load(path).get('jobs',[]):
            jid=row['job_id'];entry=history.setdefault(jid,{})
            if row.get('start_timestamp') is not None:entry['start']=row['start_timestamp']
            fields=dict(re.findall(r'(\w+)=(\S+)',row.get('raw_scontrol','')))
            if row.get('record_available') and fields.get('JobState') not in ACTIVE and timestamp(fields.get('EndTime')) is not None:
                entry.update(end=timestamp(fields['EndTime']),terminal_state=fields.get('JobState'),terminal_source=str(path))
    live=subprocess.run(['squeue','-u',os.environ.get('USER','hyunjin'),'-h','-o','%i|%j|%T'],capture_output=True,text=True,check=True).stdout
    live_rows={line.split('|')[0]:line.split('|') for line in live.splitlines() if line}
    jobs=[]
    for path in sorted((ROOT/'audit/launches').glob('job_*.json')):
        launch=load(path);job=launch['job'];jid=str(job['slurm_job_id']);gpus=int(job.get('gpus',0));old=history.get(jid,{})
        raw=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True)
        fields=dict(re.findall(r'(\w+)=(\S+)',raw.stdout))
        state=live_rows[jid][2] if jid in live_rows else fields.get('JobState',old.get('terminal_state','NOT_IN_SLURM'))
        start=None if state=='PENDING' else timestamp(fields.get('StartTime')) or old.get('start')
        end=timestamp(fields.get('EndTime')) if state not in ACTIVE else None
        if end is None:end=old.get('end')
        ep=ROOT/'audit/workers'/jid/'exit.json';ex=load(ep) if ep.exists() else None
        jobs.append(dict(job_id=jid,queue_id=job['id'],mode=launch.get('mode'),gpus=gpus,state=state,
             active=jid in live_rows,requested_hours=launch.get('hours'),start_timestamp=start,end_timestamp=end,
             node=fields.get('NodeList') or job.get('node'),worker_exit=ex,
             historical_terminal_source=old.get('terminal_source'),raw_scontrol=raw.stdout,
             **elapsed_accounting(gpus,state,start,end,ex,current.timestamp())))
    active=[row for row in live_rows.values() if PREFIX in row[1]]
    return dict(at=now(),jobs=jobs,active=active,active_gpu_jobs=[j['job_id'] for j in jobs if j['active'] and j['gpus']],
         gpu_hours_observed_or_proxy=sum(j['gpu_hours'] or 0 for j in jobs),
         unknown_gpu_duration_jobs=[j['job_id'] for j in jobs if j['gpus'] and j['gpu_hours'] is None],
         precision='Exact retained Slurm intervals where available; otherwise worker-exit proxies. No stale time-to-now estimates for purged terminal jobs. CPU and watcher GPU-hours are zero. Slurm accounting service unavailable.',
         scientific_outcomes_used=False)


if __name__=='__main__':
    result=accounting()
    save(ROOT/'audit'/('resource_snapshot_v2_'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'),result)
    print(json.dumps({k:v for k,v in result.items() if k!='jobs'},indent=2))
