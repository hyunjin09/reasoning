"""Finite CPU supervisor: replace only failed GPU-OOM main jobs, never extend scope."""
import argparse
import fcntl
import os
import re
import shlex
import subprocess
import time
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage14b.common import *
from scripts.stage14b.oom_policy import is_gpu_oom, remaining, resolve_oom, verify_recovery
from scripts.stage14b.worker import authorize

WATCH = ROOT/'audit/oom_watch'


def submit_replacement(original, manifest, hours):
    """Idempotent replacement submission, respecting the user's GPU ceiling."""
    project = Path.cwd(); ident = PREFIX+'oom_recovery_'+original
    queued = scheduler.load_gpu_queue(project)
    existing = next((j for j in queued['jobs'] if j['id'] == ident), None)
    if existing and existing.get('slurm_job_id'):
        return existing
    args = SimpleNamespace(max_user_gpus=8, squeue_output=None, all_squeue_output=None,
                           scontrol_output=None, available_gpus=None)
    capacity = scheduler.gpu_status(args, queued)
    if capacity['warnings'] or capacity['remaining_user_slots'] < 1:
        return None
    if existing is None:
        command = shlex.join(['bash', 'scripts/stage14b/run.sh', '-m', 'scripts.stage14b.oom_runner',
                              str(manifest), '--manifest-sha256', sha(manifest)])
        subprocess.run(['.venv/bin/python','infra/gpu_scheduler.py','add','--project','.',
            '--id',ident,'--exp-id',ident,'--gpu-type','a6000','--gpus','1','--mem','28G','--cpus','4',
            '--allow-slurm-pending','--exclude-node','node01','--exclude-node','node04','--exclude-node','node05',
            '--command',command,'--log-path',f'runs/stage14b/oom_recovery_{original}/slurm.log',
            '--result-path',str(ROOT)], check=True)
        existing = next(j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] == ident)
    plan = scheduler.plan_jobs({'jobs':[existing]}, capacity)
    if not plan:
        return None
    assert len(plan) == 1 and plan[0]['gpus'] == 1
    assert not plan[0]['node'] or plan[0]['node'] in ALLOWED_NODES
    minutes = max(1, int(hours*60))
    os.environ['SBATCH_TIMELIMIT'] = f'{minutes//60:02d}:{minutes%60:02d}:00'
    saved_index = Path('reports/index.md').read_text()
    try:
        scheduler.execute_launch(project, plan[0])
    finally:
        Path('reports/index.md').write_text(saved_index)
    return next(j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] == ident)


def inspect_closed(jid, launch, fields):
    state = fields.get('JobState')
    # Explicit cancellations/time limits/host OOMs are not sample CUDA OOMs.
    if state != 'FAILED':
        return dict(action='DONE' if state == 'COMPLETED' else 'HOLD', reason=state)
    failure_path = ROOT/'audit/workers'/jid/'failure.json'
    failure = load(failure_path) if failure_path.exists() else {}
    log_path = Path(launch['job']['log_path'])
    log = log_path.read_text(errors='replace')
    if not is_gpu_oom(log+'\n'+failure.get('traceback','')+'\n'+failure.get('error','')):
        return dict(action='HOLD', reason='NON_GPU_OOM_FAILURE')
    command = shlex.split(launch['job']['command'])
    i = command.index('--manifest-sha256')
    source = Path(command[i-1]); assert sha(source) == command[i+1]
    m = load(source); authorize(m)
    # Include all unfinished admitted receipts. Old workers did not record a
    # pending add_request ID separately; a batch OOM must not blame a random row.
    partial = [t['task_id'] for t in m['rows'] if
        result_dir(t).exists() and not (result_dir(t)/'result.json').exists()]
    failure['active_ids'] = sorted(set(failure.get('active_ids', [])) | set(partial))
    evidence = dict(original_job=jid, failure=str(failure_path), log=str(log_path))
    culprit = resolve_oom(m['rows'], failure, log, evidence)
    tasks, attempts = remaining(m['rows'])
    if not tasks:
        return dict(action='DONE', reason='ALL_ROWS_TERMINAL', skipped=culprit)
    manifest = WATCH/f'recovery_{jid}.json'
    if not manifest.exists():
        save(manifest, dict(m, at=now(), rows=tasks, attempts=attempts, batch_size=1,
                            recovery_of=jid, amendment='oom_skip_amendment_v1'))
    return dict(action='RECOVER', manifest=str(manifest), skipped=culprit,
                affected_ids=failure['active_ids'], source_manifest=str(source))


def main():
    verify_recovery(); WATCH.mkdir(parents=True, exist_ok=True)
    with (WATCH/'supervisor.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        amendment = load(ROOT/'spec/oom_skip_amendment_v1.json')
        deadline = dt.datetime.fromisoformat(amendment['supervisor_deadline_utc']).timestamp()
        job = os.environ['SLURM_JOB_ID']; dest = WATCH/job
        save(dest/'started.json', dict(at=now(), job=job, gpus=0,
            watched_jobs=amendment['existing_jobs'], deadline=deadline,
            authority='GPU OOM replacements only; max8; no next phase'))
        tick = 0
        while time.time() < deadline:
            live_proc = subprocess.run(['squeue','-u',os.environ.get('USER','hyunjin'),'-h','-o','%i'],
                                       capture_output=True,text=True,check=True)
            live = set(live_proc.stdout.split()); unresolved = []
            for jid in amendment['existing_jobs']:
                record = WATCH/f'original_{jid}.json'
                if record.exists():
                    r = load(record)
                    replacement = r.get('replacement_job')
                    if replacement and replacement in live:
                        unresolved.append(replacement)
                    continue
                if jid in live:
                    unresolved.append(jid); continue
                launch = load(ROOT/'audit/launches'/f'job_{jid}.json')
                proc = subprocess.run(['scontrol','show','job',jid,'-o'], capture_output=True,text=True)
                if proc.returncode:
                    raise RuntimeError(f'Cannot verify terminal state for {jid}')
                fields = dict(re.findall(r'(\w+)=(\S+)',proc.stdout))
                if fields.get('JobState') in ('RUNNING','PENDING','COMPLETING','CONFIGURING'):
                    unresolved.append(jid); continue
                try:
                    action = inspect_closed(jid, launch, fields)
                except Exception as exc:
                    action = dict(action='HOLD', reason=repr(exc))
                if action['action'] == 'RECOVER':
                    hours = min(72, (deadline-time.time())/3600)
                    if hours < 0.1:
                        action = dict(action='HOLD', reason='SUPERVISOR_DEADLINE')
                    else:
                        replacement = submit_replacement(jid, Path(action['manifest']), hours)
                        if replacement is None:
                            unresolved.append(jid); continue
                        new_id = str(replacement['slurm_job_id'])
                        receipt = ROOT/'audit/launches'/f'job_{new_id}.json'
                        if not receipt.exists():
                            save(receipt, dict(at=now(), mode=launch['mode'], hours=hours,
                                               job=replacement, recovery_of=jid))
                        action['replacement_job'] = new_id; unresolved.append(new_id)
                save(record, dict(at=now(), original_job=jid, **action))
            save(dest/f'heartbeat_{tick:05d}.json', dict(at=now(), active_or_waiting=unresolved,
                                                       scientific_outcomes_inspected=False))
            tick += 1
            print(now(), 'OOM supervisor active jobs', unresolved, flush=True)
            if not unresolved:
                save(dest/'exit.json', dict(at=now(), reason='WATCHED_QUEUES_TERMINAL'))
                return
            time.sleep(45)
        save(dest/'exit.json', dict(at=now(), reason='FINITE_DEADLINE; no new launch'))


if __name__ == '__main__':
    main()
