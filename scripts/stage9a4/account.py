"""Summarize captured Slurm runtimes without assuming purged jobs remain queryable."""
from pathlib import Path
from datetime import datetime
from scripts.stage9a4.common import ROOT,load,save,now


def seconds(s):
    days=0
    if '-' in s:day,s=s.split('-');days=int(day)
    h,m,sec=map(int,s.split(':'));return days*86400+h*3600+m*60+sec


def main():
    best={}
    for path in sorted((ROOT/'audit').glob('resource_snapshot_*.json')):
        snap=load(path)
        for r in snap['jobs']:
            key=r['queue']['id'];f=r['slurm_fields'];old=best.get(key)
            if f.get('RunTime') and (old is None or seconds(f['RunTime'])>seconds(old['slurm_fields']['RunTime']) or
                (seconds(f['RunTime'])==seconds(old['slurm_fields']['RunTime']) and f['JobState']=='COMPLETED')):
                best[key]=dict(r,snapshot=str(path))
    jobs=[];gpu_seconds=0
    for name,r in sorted(best.items()):
        f=r['slurm_fields'];g=r['queue']['resources']['gpus'] if 'resources' in r['queue'] else r['queue'].get('gpus',0)
        jobs.append(dict(id=name,slurm_job_id=r['queue']['slurm_job_id'],gpus=g,runtime_seconds=seconds(f['RunTime']),
            state=f['JobState'],exit_code=f.get('ExitCode'),node=f.get('NodeList'),start=f.get('StartTime'),end=f.get('EndTime'),snapshot=r['snapshot']))
        gpu_seconds+=g*seconds(f['RunTime'])
    expected={j['id'] for j in load('state/gpu_experiment_queue.json')['jobs'] if j['id'].startswith('stage9a4_') and j['gpus']}
    assert expected=={j['id'] for j in jobs if j['gpus']},'Missing allocation records'
    events=[]
    for j in jobs:
        if j['gpus']:
            assert j['state']=='COMPLETED' and j['exit_code']=='0:0'
            events.extend([(datetime.fromisoformat(j['start']),j['gpus']),(datetime.fromisoformat(j['end']),-j['gpus'])])
    active=peak=0
    for _,change in sorted(events):active+=change;peak=max(peak,active)
    assert peak<=4 and active==0
    generations=[];counts={}
    for p in ROOT.glob('*/results/*/generation.json'):
        r=load(p);generations.append(r);stage=p.parts[-4];counts[stage]=counts.get(stage,0)+1
    receipts=[load(p) for p in ROOT.glob('*/results/*/result.json')]
    result=dict(at=now(),jobs=jobs,allocated_gpu_hours=gpu_seconds/3600,counts=counts,
        scientific_generations=len(generations),generation_gpu_hours=sum(r['runtime_seconds'] for r in generations)/3600,
        generated_tokens=sum(r['tokens'] for r in generations),peak_allocated_bytes=max(r['peak_allocated_bytes'] for r in receipts),
        peak_reserved_bytes=max(r['peak_reserved_bytes'] for r in receipts),max_authorized_concurrent_gpus=4,observed_peak_gpus=peak,
        all_gpu_jobs_terminal=all(j['state']=='COMPLETED' and j['exit_code']=='0:0' for j in jobs if j['gpus']))
    save(ROOT/'stage9a4_resource_accounting.json',result);print(result,flush=True)


if __name__=='__main__':main()
