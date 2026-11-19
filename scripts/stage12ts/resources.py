"""Separate conservative allocation budgets for CoT, same12, fresh12."""
import re,subprocess
from scripts.stage12ts.common import ROOT,PREFIX,load,save,now
from scripts.stage12c.resources import seconds,TERMINAL
LIMITS={'remaining':6.5}

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
        rows.append(dict(phase=phase,queue_id=j['id'],slurm_job_id=jid,node=f.get('NodeList','(pending)'),status=f['JobState'],
            terminal=done,exit_code=f.get('ExitCode'),gpus=j['gpus'],
            allocated_gpu_hours=seconds(f['RunTime'])*j['gpus']/3600,
            committed_gpu_hours_upper=seconds(f['RunTime'] if done else f['TimeLimit'])*j['gpus']/3600,
            command=j['command'],log_path=j['log_path']))
    totals={p:dict(allocated_gpu_hours=sum(r['allocated_gpu_hours'] for r in rows if r['phase']==p),
        committed_gpu_hours_upper=sum(r['committed_gpu_hours_upper'] for r in rows if r['phase']==p),hard_limit_gpu_hours=limit) for p,limit in LIMITS.items()}
    result=dict(at=now(),jobs=rows,phases=totals,all_released=all(r['terminal'] for r in rows))
    assert not final, 'Canonical accounting is written at closure'
    save(ROOT/f'audit/resource_{label}.json',result)
    return result
