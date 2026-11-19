"""Use project scheduler with a conservative cumulative eight-GPU-hour envelope."""
import argparse
import os
import re
import shlex
import subprocess
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage12ws.common import ROOT,PREFIX,ALLOWED_NODES,load,save,sha,now
from scripts.stage12ws.protocol import authorize
from scripts.stage12c.resources import seconds,TERMINAL


def account(label):
    rows=[]
    for j in load('state/gpu_experiment_queue.json')['jobs']:
        if not j['id'].startswith(PREFIX):continue
        jid=str(j['slurm_job_id']);path=ROOT/'audit/terminal_receipts'/f'{jid}.json'
        if path.exists():receipt=load(path)
        else:
            raw=subprocess.run(['scontrol','show','job',jid,'-o'],capture_output=True,text=True,check=True).stdout
            receipt=dict(at=now(),raw=raw,fields=dict(re.findall(r'(\w+)=([^\s]+)',raw)))
            if receipt['fields']['JobState'] in TERMINAL:save(path,receipt)
        f=receipt['fields'];done=f['JobState'] in TERMINAL
        rows.append(dict(queue_id=j['id'],slurm_job_id=jid,status=f['JobState'],terminal=done,
            exit_code=f.get('ExitCode'),node=f.get('NodeList'),gpus=j['gpus'],command=j['command'],log_path=j['log_path'],
            allocated_gpu_hours=seconds(f['RunTime'])*j['gpus']/3600,
            committed_gpu_hours_upper=seconds(f['RunTime'] if done else f['TimeLimit'])*j['gpus']/3600))
    result=dict(at=now(),jobs=rows,allocated_gpu_hours=sum(r['allocated_gpu_hours'] for r in rows),
                committed_gpu_hours_upper=sum(r['committed_gpu_hours_upper'] for r in rows),
                all_released=all(r['terminal'] for r in rows),hard_gpu_hours=8,target_gpu_hours=6)
    save(ROOT/'audit'/f'resources_{label}.json',result)
    return result


def main(phase,manifests,minutes):
    assert re.fullmatch(r'[A-Za-z0-9_]+',phase) and 1<=len(manifests)<=8 and 5<=minutes<=120
    for p in manifests:
        m=load(p);assert m['phase']==phase;authorize(m)
    ledger=account('prelaunch_'+phase)
    upper=ledger['committed_gpu_hours_upper']+len(manifests)*minutes/60
    assert upper<=8,upper
    args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
    project=Path.cwd();status=scheduler.gpu_status(args,scheduler.load_gpu_queue(project))
    assert not status['warnings'] and status['own_gpus']+len(manifests)<=8
    save(ROOT/'audit'/f'{phase}_resource_envelope.json',dict(at=now(),upper_gpu_hours=upper,minutes=minutes,manifests=manifests,status=status))
    ids=set()
    for i,p in enumerate(manifests):
        ident=PREFIX+phase+f'_{i}';ids.add(ident)
        command=shlex.join(['bash','scripts/stage12ws/run.sh','scripts/stage12ws/worker.py',p,'--manifest-sha256',sha(p)])
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
            '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--mem','28G','--cpus','4',
            '--allow-slurm-pending','--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
            '--command',command,'--log-path',f'runs/stage12ws/v1/{phase}_{i}/slurm.log','--result-path',str(ROOT)],check=True)
    jobs=[j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in ids]
    assert all(j['status']=='queued' for j in jobs)
    os.environ['SBATCH_TIMELIMIT']=f'{minutes//60:02d}:{minutes%60:02d}:00'
    planned=scheduler.plan_jobs({'jobs':jobs},status);assert len(planned)==len(jobs)
    for j in planned:
        assert not j['node'] or j['node'] in ALLOWED_NODES
        scheduler.execute_launch(project,j)
    jobs=[j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in ids]
    save(ROOT/'audit'/f'{phase}_launch.json',dict(at=now(),jobs=jobs));print([(j['id'],j['slurm_job_id']) for j in jobs])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase');p.add_argument('manifests',nargs='+');p.add_argument('--minutes',type=int,required=True)
    a=p.parse_args();main(a.phase,a.manifests,a.minutes)
