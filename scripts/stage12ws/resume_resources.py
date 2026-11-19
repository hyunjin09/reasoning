"""Versioned operational accounting for the explicitly approved resumption."""
import argparse
import datetime as dt
import os
import re
import shlex
import subprocess
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage12ws.common import ROOT, load, save, sha, now, ALLOWED_NODES
from scripts.stage12ws.protocol import authorize
from scripts.stage12c.resources import seconds, TERMINAL

PREFIX = 'stage12ws_resume_'
KST = dt.timezone(dt.timedelta(hours=9))

def cost(fields, observed):
    state = fields['JobState']
    runtime = seconds(fields['RunTime']) / 3600
    limit = seconds(fields['TimeLimit']) / 3600
    released = state in TERMINAL
    elapsed = 0
    if fields.get('StartTime') not in [None, 'Unknown', 'N/A'] and state != 'PENDING':
        start = dt.datetime.fromisoformat(fields['StartTime']).replace(tzinfo=KST)
        elapsed = max(0, (dt.datetime.fromisoformat(observed) - start).total_seconds()/3600)
    return dict(lower=runtime, upper=max(runtime, elapsed, 0 if released else limit), released=released)

def enforce(base_upper, new_upper, proposed):
    assert new_upper + proposed <= 3 + 1e-9, 'Additional three-GPU-hour cap'
    assert base_upper + new_upper + proposed <= 14 + 1e-9, 'Total fourteen-GPU-hour cap'

def account(label):
    amendment = load(ROOT/'audit/resource_amendment_approved_v1.json')
    assert amendment['approved'] and amendment['additional_gpu_hours'] == 3 and amendment['total_ceiling_gpu_hours'] == 14
    base = load(ROOT/'audit/resume_resource_reconciliation_v1.json')['conservative_allocation_hours_bounds']
    rows = []
    for job in scheduler.load_gpu_queue(Path.cwd())['jobs']:
        if not job['id'].startswith(PREFIX): continue
        jid = str(job['slurm_job_id']); path = ROOT/'audit/resume_terminal_receipts'/f'{jid}.json'
        bounded = ROOT/'audit/resume_missing_terminal_bounds'/f'{jid}.json'
        if bounded.exists():
            receipt = load(bounded)
            assert receipt['released'] and 0 <= receipt['lower'] <= receipt['upper']
            assert receipt['worker_exit_sha256'] == sha(ROOT/'workers'/jid/'exit.json')
            rows.append(dict(queue_id=job['id'], slurm_job_id=jid, status=receipt['status'],
                node=receipt['node'], gpus=job['gpus'], command=job['command'], log_path=job['log_path'],
                lower=receipt['lower'], upper=receipt['upper'], released=True,
                accounting_note=receipt['interpretation'], bounded_receipt=str(bounded)))
            continue
        if path.exists(): receipt = load(path)
        else:
            p = subprocess.run(['scontrol', 'show', 'job', jid, '-o'], capture_output=True, text=True, check=True)
            receipt = dict(at=now(), raw=p.stdout, fields=dict(re.findall(r'(\w+)=([^\s]+)', p.stdout)))
            if receipt['fields']['JobState'] in TERMINAL: save(path, receipt)
        c = cost(receipt['fields'], receipt['at'])
        rows.append(dict(queue_id=job['id'], slurm_job_id=jid, status=receipt['fields']['JobState'],
                         node=receipt['fields'].get('NodeList'), gpus=job['gpus'],
                         command=job['command'], log_path=job['log_path'], **c))
    lower = sum(r['lower']*r['gpus'] for r in rows)
    upper = sum(r['upper']*r['gpus'] for r in rows)
    result = dict(at=now(), historical_allocation_hours_bounds=base, new_gpu_hours_lower=lower,
                  new_gpu_hours_upper=upper, total_allocation_hours_bounds=[base[0]+lower,base[1]+upper],
                  hard_gpu_hours=14, additional_hard_gpu_hours=3,
                  all_released=all(r['released'] for r in rows), jobs=rows)
    save(ROOT/'audit'/f'resume_resources_{label}.json',result)
    return result

def launch(label, manifests, minutes):
    assert re.fullmatch('[A-Za-z0-9_]+', label) and 1 <= len(manifests) <= 8 and 5 <= minutes <= 60
    for path in manifests:
        manifest = load(path); authorize(manifest)
        assert all(not (ROOT/'generations'/t['task_id']).exists() for t in manifest['rows']), 'No retries'
    ledger = account('pre_'+label)
    assert ledger['all_released'], 'Close current wave before launching the next'
    enforce(ledger['historical_allocation_hours_bounds'][1], ledger['new_gpu_hours_upper'], len(manifests)*minutes/60)
    args = SimpleNamespace(max_user_gpus=8,squeue_output=None,all_squeue_output=None,scontrol_output=None,available_gpus=None)
    status = scheduler.gpu_status(args, scheduler.load_gpu_queue(Path.cwd()))
    assert not status['warnings'] and status['own_gpus']+len(manifests)<=8
    save(ROOT/'audit'/f'resume_{label}_envelope.json',dict(at=now(),minutes=minutes,manifests=manifests,status=status))
    identifiers=[]
    for i,path in enumerate(manifests):
        ident=PREFIX+label+f'_{i}';identifiers.append(ident)
        command=shlex.join(['bash','scripts/stage12ws/run.sh','scripts/stage12ws/worker.py',path,'--manifest-sha256',sha(path)])
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
            '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--mem','28G','--cpus','4',
            '--allow-slurm-pending','--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
            '--command',command,'--log-path',f'runs/stage12ws/v1/resume_{label}_{i}/slurm.log','--result-path',str(ROOT)],check=True)
    jobs=[j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id'] in identifiers]
    assert len(jobs)==len(manifests) and all(j['status']=='queued' for j in jobs)
    os.environ['SBATCH_TIMELIMIT']=f'00:{minutes:02d}:00'
    planned=scheduler.plan_jobs({'jobs':jobs},status)
    assert len(planned)==len(jobs)
    for job in planned:
        assert not job['node'] or job['node'] in ALLOWED_NODES
        scheduler.execute_launch(Path.cwd(),job)
    launched=[j for j in scheduler.load_gpu_queue(Path.cwd())['jobs'] if j['id'] in identifiers]
    save(ROOT/'audit'/f'resume_{label}_launch.json',dict(at=now(),jobs=launched))
    print([(j['id'],j['slurm_job_id']) for j in launched])

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['launch','account']);p.add_argument('label')
    p.add_argument('manifests',nargs='*');p.add_argument('--minutes',type=int,default=20);a=p.parse_args()
    launch(a.label,a.manifests,a.minutes) if a.action=='launch' else print(account(a.label))
