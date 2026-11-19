"""Bounded Slurm coordinator for only the frozen dynamics assays.

Continues genuine walltime-limited work from completed units, never retries a
model/runtime failure or a user cancellation. No scientific selection or scoring.
"""
import argparse
import fcntl
import json
import os
import re
import subprocess
import time
from datetime import datetime,timezone,timedelta
from pathlib import Path
import gpu_scheduler as scheduler
from harness_state import load_gpu_queue
from scripts.stage9a.run_native import now

ROOT=Path('outputs/stage9a_dynamics/v1')
READOUT_ROOT=ROOT
PREFIX='stage9a_dynamics'
ALLOWED={'node02','node03','node06','node07'}
MAX_GPUS=4
WORKER_NODE=None


def command(*args):
    result=subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py',*args,'--project','.'],text=True,capture_output=True,check=True)
    print(result.stdout.strip(),flush=True)


def write_status(**value):
    path=ROOT/'audit/dispatcher_status.json';tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(dict(at=now(),**value),indent=2)+'\n');tmp.replace(path)


def is_compute(job):
    return job['id'].startswith(PREFIX+'_worker') or job['id'].startswith(PREFIX+'_readout')


def release_timeout_claims(sid):
    worker='slurm_'+sid
    wd=ROOT/'rollouts/workers'/worker
    assert (wd/'progress.jsonl').exists(),'No completed unit: timeout without progress requires diagnosis'
    archive=ROOT/'audit/timeout_continuations'/worker;archive.mkdir(parents=True,exist_ok=False)
    for claim in (ROOT/'rollouts/claims').iterdir():
        owner=claim/'owner.json'
        if not owner.exists() or json.loads(owner.read_text())['worker']!=worker:continue
        if (ROOT/'rollouts/tasks'/claim.name/'complete.json').exists():continue
        task=claim.name
        # Preserve any interrupted write; only durable, parseable receipts count.
        manifest=json.loads((ROOT/'audit/interventions.json').read_text())['rows']
        for c in manifest:
            if c['task_id']!=task or c['execution']!='run':continue
            dest=ROOT/'rollouts/results'/c['result_key']
            if not dest.exists():continue
            receipt=dest/'result.json'
            if receipt.exists():
                try:json.loads(receipt.read_text());continue
                except json.JSONDecodeError:pass
            dest.rename(archive/dest.name)
        owner.rename(archive/(task+'_owner.json'));claim.rmdir()


def add_compute(kind,index,node):
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    jid=f'{PREFIX}_{kind}_{stamp}_{index}'
    if kind=='worker':
        arm=['thinking','instruct_cot','instruct_direct','thinking'][index%4]
        cmd=f'bash scripts/stage9a_dynamics/run.sh scripts/stage9a_dynamics/run_worker.py --root {ROOT} --preferred {arm}'
    else:cmd='bash scripts/stage9a_dynamics/run.sh scripts/stage9a_dynamics/run_readouts.py'
    command('add','--id',jid,'--exp-id',jid,'--gpu-type','a6000','--gpus','1','--node',node,
        '--mem','30G','--cpus','4','--shell-mode','plain','--command',cmd,
        '--log-path',f'runs/stage9a_dynamics/{ROOT.name}/{jid}_slurm.log','--result-path',str((ROOT if kind=='worker' else READOUT_ROOT)/('rollouts' if kind=='worker' else 'readouts')))
    return jid


def run(deadline):
    assert os.environ.get('SLURM_JOB_ID'),'Long-lived CPU coordination runs via Slurm with zero GPUs'
    tasks=json.loads((ROOT/'audit/tasks.json').read_text())['rows'];project=Path('.').resolve()
    started=time.monotonic();index=0
    args=argparse.Namespace(squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None,max_user_gpus=MAX_GPUS)
    while datetime.now(timezone.utc)<deadline:
        if (ROOT/'audit/STOP_DISPATCH').exists():write_status(state='stopped_by_file');return
        queue=load_gpu_queue(project);jobs=[j for j in queue['jobs'] if is_compute(j)]
        blockers=[j for j in jobs if j['status']=='cancelled' or
                  (j['status']=='failed' and not str(j.get('notes','')).startswith('Slurm walltime reached after completed units;'))]
        if blockers:
            write_status(state='blocked_recorded_failure_or_cancellation',jobs=[j['id'] for j in blockers],automatic_retry=False);return
        live_rows=subprocess.run(['squeue','--me','-h','-o','%i|%T|%b'],text=True,capture_output=True,check=True).stdout.splitlines()
        live={line.split('|')[0] for line in live_rows}
        # Include pending GPU reservations as well as running allocations.
        reserved=sum(int(match.group(1)) for line in live_rows for match in [re.search(r'gpu(?::[^:,|]+)*:(\d+)',line.split('|')[-1])] if match)
        for job in jobs:
            if job['status']!='running' or str(job.get('slurm_job_id')) in live:continue
            sid=str(job['slurm_job_id']);kind='readouts' if 'readout' in job['id'] else 'rollouts'
            wd=(READOUT_ROOT if kind=='readouts' else ROOT)/kind/'workers'/('slurm_'+sid)
            record=subprocess.run(['scontrol','show','job',sid,'-o'],text=True,capture_output=True)
            (ROOT/'audit'/f'slurm_{sid}_terminal.txt').write_text(record.stdout+record.stderr)
            if (wd/'completed.json').exists():
                command('update','--id',job['id'],'--status','succeeded','--note','Worker completion receipt verified; GPU released.')
            elif 'JobState=TIMEOUT' in record.stdout and kind=='rollouts' and not (wd/'failure.json').exists():
                release_timeout_claims(sid)
                command('update','--id',job['id'],'--status','failed','--note','Slurm walltime reached after completed units; partial write preserved; resume only remaining immutable conditions.')
            else:
                command('update','--id',job['id'],'--status','failed','--note','Worker ended without receipt; no automatic retry. Inspect preserved logs.')
                write_status(state='blocked_runtime_or_user_cancellation',job=job['id'],slurm_job_id=sid,automatic_retry=False);return
        queue=load_gpu_queue(project);jobs=[j for j in queue['jobs'] if is_compute(j)]
        active=[j for j in jobs if j['status'] in ('queued','running')]
        completed=sum((ROOT/'rollouts/tasks'/r['task_id']/'complete.json').exists() for r in tasks)
        readouts_done=(READOUT_ROOT/'audit/readouts_complete.json').exists()
        if completed==len(tasks) and readouts_done and not active:
            write_status(state='main_gpu_assays_complete_review_then_bounded_controls_pending',native_tasks=len(tasks),readout_events=50,scientific_stage_complete=False);return
        available=scheduler.gpu_status(args,queue)
        if available['warnings']:raise RuntimeError(available['warnings'])
        free={n:int(v['available']) for n,v in available['available_node_gpus'].items()
              if n in ALLOWED and (WORKER_NODE is None or n==WORKER_NODE)}
        unclaimed=any(not (ROOT/'rollouts/claims'/r['task_id']).exists() for r in tasks)
        # Readouts are frozen secondary assays, independent of primary outcomes.
        readout_active=any('readout' in j['id'] for j in active)
        slots=min(MAX_GPUS-len(active),int(available['remaining_user_slots']),max(0,MAX_GPUS-reserved))
        for _ in range(max(0,slots)):
            nodes=sorted([n for n,v in free.items() if v>0],key=lambda n:(-free[n],n))
            if not nodes:break
            if not readouts_done and not readout_active:kind='readout';readout_active=True
            elif unclaimed:kind='worker'
            else:break
            node=nodes[0];add_compute(kind,index,node);index+=1;free[node]-=1
        queue=load_gpu_queue(project);owned=dict(queue,jobs=[j for j in queue['jobs'] if is_compute(j)])
        available=scheduler.gpu_status(args,queue)
        available['remaining_user_slots']=min(available['remaining_user_slots'],max(0,MAX_GPUS-reserved))
        for job in scheduler.plan_jobs(owned,available):
            assert job['node'] in ALLOWED and job['gpus']==1
            os.environ['SBATCH_TIMELIMIT']='2-00:00:00' if 'readout' in job['id'] else '7-00:00:00'
            scheduler.execute_launch(project,job)
        write_status(state='frozen_assays_running',completed_native_tasks=completed,total_native_tasks=len(tasks),
            readouts_complete=readouts_done,maximum_gpus=MAX_GPUS,worker_node=WORKER_NODE,
            deadline=deadline.isoformat(),scientific_stage_complete=False)
        # A long coordinator itself hands off before the partition's wall limit.
        if time.monotonic()-started>12.5*86400:
            jid=PREFIX+'_coordinator_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
            cmd=f'bash scripts/stage9a_dynamics/run.sh scripts/stage9a_dynamics/dispatch.py --root {ROOT} --readout-root {READOUT_ROOT} --prefix {PREFIX} --deadline {deadline.isoformat()} --max-gpus {MAX_GPUS}'
            if WORKER_NODE:cmd+=f' --worker-node {WORKER_NODE}'
            command('add','--id',jid,'--exp-id',jid,'--gpu-type','a6000','--gpus','0','--node',socket_node(),
                '--mem','2G','--cpus','1','--shell-mode','plain','--command',cmd,'--log-path',f'runs/stage9a_dynamics/{ROOT.name}/{jid}.log','--result-path',str(ROOT/'audit/dispatcher_status.json'))
            queue=load_gpu_queue(project);owned=dict(queue,jobs=[j for j in queue['jobs'] if j['id']==jid])
            os.environ['SBATCH_TIMELIMIT']='13-00:00:00'
            for job in scheduler.plan_jobs(owned,scheduler.gpu_status(args,queue)):scheduler.execute_launch(project,job)
            return
        time.sleep(30)
    write_status(state='coordinator_deadline',note='No new submissions; existing bounded Slurm jobs may finish. Scientific plan remains pending.')


def socket_node():
    import socket
    return socket.gethostname().split('.')[0]


def main():
    global ROOT,READOUT_ROOT,PREFIX,MAX_GPUS,WORKER_NODE
    ap=argparse.ArgumentParser();ap.add_argument('--deadline')
    ap.add_argument('--root',default=str(ROOT));ap.add_argument('--readout-root',default=str(READOUT_ROOT))
    ap.add_argument('--prefix',default=PREFIX)
    ap.add_argument('--max-gpus',type=int,choices=range(1,9),default=MAX_GPUS)
    ap.add_argument('--worker-node',choices=sorted(ALLOWED))
    args=ap.parse_args()
    ROOT=Path(args.root);READOUT_ROOT=Path(args.readout_root);PREFIX=args.prefix
    MAX_GPUS=args.max_gpus;WORKER_NODE=args.worker_node
    deadline=datetime.fromisoformat(args.deadline) if args.deadline else datetime.now(timezone.utc)+timedelta(days=30)
    lock=(ROOT/'audit/dispatcher.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX)
    try:run(deadline)
    except Exception as exc:write_status(state='coordinator_error',error=repr(exc),automatic_retry=False);raise
    finally:lock.close()


if __name__=='__main__':main()
