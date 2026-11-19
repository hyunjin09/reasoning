"""Launch only specified frozen technical conditions; never a scientific rerun."""
import argparse
import os
import shlex
import subprocess
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.qwen3vl_official_eval.common import ROOT, PREFIX, ALLOWED_NODES, load, save, sha, now
from scripts.qwen3vl_official_eval.resources import account

def main(conditions,label,minutes):
    manifest_path=ROOT/'qwen3vl_official_sanity_manifest.json';m=load(manifest_path)
    allowed={'official_instruct_direct','official_thinking'}|{r['name'] for r in m['ablations']}
    assert set(conditions)<=allowed and len(conditions)==len(set(conditions)) and 5<=minutes<=60
    for condition in conditions:
        if not condition.startswith('official_'):assert load(ROOT/'audit/sanity_technical_gate.json')['instruct_gate_pass']
    ledger=account('prelaunch_'+label)
    worst=ledger['committed_gpu_hours_upper']+len(conditions)*minutes/60
    assert worst<=3,'Hard3GPUh includes entire requested allocations and all earlier work'
    args=SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
    project=Path.cwd();status=scheduler.gpu_status(args,scheduler.load_gpu_queue(project))
    assert not status['warnings'] and status['own_gpus']+len(conditions)<=8
    save(ROOT/'audit'/f'{label}_envelope.json',dict(at=now(),prospective_gpu_hours=worst,minutes=minutes,
        conditions=conditions,hard_limit=3,scheduler_status=status))
    ids=set()
    for condition in conditions:
        ident=PREFIX+label+'_'+condition;ids.add(ident)
        command=shlex.join(['bash','scripts/qwen3vl_official_eval/run.sh','scripts/qwen3vl_official_eval/worker.py',condition,
            '--manifest-sha256',sha(manifest_path)])
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
            '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--mem','28G','--cpus','4',
            '--allow-slurm-pending','--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
            '--command',command,'--log-path',f'runs/qwen3vl_official_eval/v1/{label}_{condition}/slurm.log',
            '--result-path',str(ROOT)],check=True)
    jobs=[j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in ids]
    assert all(j['status']=='queued' for j in jobs)
    os.environ['SBATCH_TIMELIMIT']=f'{minutes//60:02d}:{minutes%60:02d}:00'
    planned=scheduler.plan_jobs({'jobs':jobs},status);assert len(planned)==len(jobs)
    for j in planned:
        assert not j['node'] or j['node'] in ALLOWED_NODES
        scheduler.execute_launch(project,j)
    jobs=[j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in ids]
    save(ROOT/'audit'/f'{label}_launch.json',dict(at=now(),jobs=jobs))
    print('FINITE_TECHNICAL_WAVE',[(j['id'],j['slurm_job_id']) for j in jobs])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('label');p.add_argument('conditions',nargs='+');p.add_argument('--minutes',type=int,required=True)
    a=p.parse_args();main(a.conditions,a.label,a.minutes)
