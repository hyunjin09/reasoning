"""Stage14C allocation intervals, preserved terminal records, and honest proxies."""
import re
import subprocess
from scripts.stage14c.common import *
from scripts.stage14b.accounting_v2 import elapsed_accounting,timestamp,ACTIVE


def accounting():
    current=dt.datetime.now(dt.timezone.utc)
    live=subprocess.run(['squeue','-u',os.environ.get('USER','hyunjin'),'-h','-o','%i|%j|%T'],capture_output=True,text=True,check=True).stdout
    active={line.split('|')[0]:line.split('|') for line in live.splitlines() if line}
    previous={}
    for p in sorted((ROOT/'audit/resource_snapshots').glob('*.json')):
        for r in load(p)['jobs']:
            if r.get('start_timestamp') is not None:previous[r['job_id']]=r['start_timestamp']
    jobs=[]
    for p in sorted((ROOT/'audit/launches').glob('job_*.json')):
        launch=load(p);job=launch['job'];jid=str(job['slurm_job_id']);gpus=int(job.get('gpus',0))
        final=ROOT/'audit'/f'job_{jid}_final_scontrol.json'
        if final.exists():raw=load(final)['text'];record_source=str(final)
        else:
            result=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True)
            raw=result.stdout;record_source='live scontrol' if result.returncode==0 else 'record expired'
        fields=dict(re.findall(r'(\w+)=(\S+)',raw));state=active[jid][2] if jid in active else fields.get('JobState','NOT_IN_SLURM')
        start=None if state=='PENDING' else timestamp(fields.get('StartTime')) or previous.get(jid)
        end=timestamp(fields.get('EndTime')) if state not in ACTIVE else None
        ep=ROOT/'audit/workers'/jid/'exit.json';ex=load(ep) if ep.exists() else None
        value=elapsed_accounting(gpus,state,start,end,ex,current.timestamp())
        if fields.get('JobState')=='CANCELLED' and not fields.get('AllocTRES') and fields.get('NodeList') in {'(null)','None'}:
            value=dict(gpu_hours=0,basis='Cancelled pending; no allocated node or TRES')
        jobs.append(dict(job_id=jid,queue_id=job['id'],mode=launch.get('mode'),gpus=gpus,
             active=jid in active,state=state,node=fields.get('NodeList') or job.get('node'),
             requested_gpu_hours=gpus*launch.get('hours',0),start_timestamp=start,end_timestamp=end,
             record_source=record_source,raw_scontrol=raw,worker_exit=ex,**value))
    return dict(at=now(),jobs=jobs,active_stage_jobs=[r for r in active.values() if PREFIX in r[1]],
         gpu_hours_observed_or_proxy=sum(r['gpu_hours'] or 0 for r in jobs),
         requested_gpu_hours_gross=sum(r['requested_gpu_hours'] for r in jobs),
         unknown_duration_jobs=[r['job_id'] for r in jobs if r['gpus'] and r['gpu_hours'] is None],
         precision='Retained Slurm intervals when available. Expired records use explicit worker-lifetime proxies; unobserved allocation startup/release is not invented. CPU jobs use zero GPU-hours. sacct unavailable.',
         VRAM_limit='Frontend torch counters do not measure vLLM child peak VRAM; engine profiling logs retained separately.',
         scientific_outcomes_used=False)


if __name__=='__main__':
    value=accounting();stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    save(ROOT/'audit/resource_snapshots'/f'{stamp}.json',value)
    print(json.dumps({k:v for k,v in value.items() if k!='jobs'},indent=2))
