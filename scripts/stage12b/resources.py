"""Conservative allocated-GPU-time accounting; missing receipts are not free."""
import argparse
import re
import subprocess
from scripts.stage12b.common import ROOT, PREFIX, load, save, now
TERMINAL={'COMPLETED','FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','PREEMPTED','BOOT_FAIL','DEADLINE','REVOKED'}

def seconds(text):
    day,clock=text.split('-',1) if '-' in text else ('0',text)
    parts=list(map(int,clock.split(':')))
    if len(parts)==2:parts.insert(0,0)
    return int(day)*86400+parts[0]*3600+parts[1]*60+parts[2]

def account(label,final=False):
    jobs=[j for j in load('state/gpu_experiment_queue.json')['jobs'] if j['id'].startswith(PREFIX)]
    rows=[]
    for j in jobs:
        jid=str(j.get('slurm_job_id') or '');p=ROOT/'audit/terminal_receipts'/f'{jid}.json'
        if p.exists():r=load(p)
        else:
            result=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True,check=True)
            r=dict(at=now(),raw=result.stdout,fields=dict(re.findall(r'(\w+)=([^\s]+)',result.stdout)))
            save(ROOT/'audit/resource_receipts'/f'{label}_{jid}.json',r)
        f=r['fields'];done=f.get('JobState') in TERMINAL
        elapsed=seconds(f['RunTime'])*j['gpus'];upper=elapsed if done else seconds(f['TimeLimit'])*j['gpus']
        rows.append(dict(queue_id=j['id'],slurm_job_id=jid,node=f['NodeList'],gpus=j['gpus'],
            status=f['JobState'],exit_code=f.get('ExitCode'),terminal=done,allocated_gpu_seconds=elapsed,
            committed_gpu_seconds_upper=upper,command=j['command'],log_path=j['log_path']))
    data=dict(at=now(),final=final,jobs=rows,allocated_gpu_hours=sum(r['allocated_gpu_seconds'] for r in rows)/3600,
        committed_gpu_hours_upper=sum(r['committed_gpu_seconds_upper'] for r in rows)/3600,
        hard_limit_gpu_hours=8.0,all_stage_allocations_released=all(r['terminal'] for r in rows),
        includes_startup_failures_partial_and_diagnostics=True,
        cpu_installation='Reused existing project-local official_eval uv environment; no install or dataset/model download.',
        annotation='Oracle source review before generation; output-only technical gate before scientific scoring.')
    if final:assert data['all_stage_allocations_released'] and data['allocated_gpu_hours']<=8.0
    save(ROOT/('stage12b_resource_accounting.json' if final else f'audit/resource_{label}.json'),data)
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('--final',action='store_true');a=p.parse_args()
    print(account(a.label,a.final))
