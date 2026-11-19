"""Separate conservative allocation budgets for CoT, same12, fresh12."""
import re,subprocess
from scripts.stage12cr.common import ROOT,PREFIX,load,save,now
from scripts.stage12c.resources import seconds,TERMINAL
LIMITS={'cot':5.0,'same12':2.5,'fresh12':2.5}

def account(label,final=False):
    jobs=[j for j in load('state/gpu_experiment_queue.json')['jobs'] if j['id'].startswith(PREFIX)]
    rows=[]
    for j in jobs:
        jid=str(j.get('slurm_job_id') or '');p=ROOT/'audit/terminal_receipts'/f'{jid}.json'
        if p.exists():r=load(p)
        else:
            raw=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True,check=True).stdout
            r=dict(at=now(),raw=raw,fields=dict(re.findall(r'(\w+)=([^\s]+)',raw)))
            save(ROOT/'audit/resource_receipts'/f'{label}_{jid}.json',r)
        f=r['fields'];done=f['JobState'] in TERMINAL
        phase=j['id'][len(PREFIX):].rsplit('_',1)[0];assert phase in LIMITS
        rows.append(dict(phase=phase,queue_id=j['id'],slurm_job_id=jid,node=f['NodeList'],status=f['JobState'],
            terminal=done,exit_code=f.get('ExitCode'),gpus=j['gpus'],
            allocated_gpu_hours=seconds(f['RunTime'])*j['gpus']/3600,
            committed_gpu_hours_upper=seconds(f['RunTime'] if done else f['TimeLimit'])*j['gpus']/3600,
            command=j['command'],log_path=j['log_path']))
    totals={p:dict(allocated_gpu_hours=sum(r['allocated_gpu_hours'] for r in rows if r['phase']==p),
        committed_gpu_hours_upper=sum(r['committed_gpu_hours_upper'] for r in rows if r['phase']==p),hard_limit_gpu_hours=limit) for p,limit in LIMITS.items()}
    result=dict(at=now(),jobs=rows,phases=totals,all_released=all(r['terminal'] for r in rows))
    if final:
        assert result['all_released'] and all(t['allocated_gpu_hours']<=t['hard_limit_gpu_hours'] for t in totals.values())
        for phases,name in [(['cot'],'stage12cr_cot'),(['same12','fresh12'],'stage12tr')]:
            save(ROOT/f'{name}_resource_accounting.json',dict(at=now(),jobs=[r for r in rows if r['phase'] in phases],
                phases={p:totals[p] for p in phases},all_allocations_released=True,
                allocated_gpu_hours=sum(totals[p]['allocated_gpu_hours'] for p in phases),includes_startup=True))
    else:save(ROOT/f'audit/resource_{label}.json',result)
    return result
