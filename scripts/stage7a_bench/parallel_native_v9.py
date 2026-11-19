"""Dispatch one verified retained release within the existing allocation."""
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from scripts.stage7a.common import ROOT, read_json, sha, write_json

OUT = ROOT / 'outputs/stage7a_bench_v2'


@contextmanager
def locked_state(path):
    path = Path(path)
    with path.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            value = read_json(path)
            yield value
            temporary = path.with_suffix('.json.tmp')
            write_json(temporary, value)
            temporary.replace(path)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


from scripts.stage7a_bench.oom_continuation_v9 import (
    claim_next, preserve_predecessor, run_attempts)


def finish_batch(state, run_id, rank, exit_code):
    batch = next(b for b in state['batches'] if b['run_id'] == run_id)
    if batch['status'] != 'running' or batch['rank'] != rank or type(exit_code) is not int:
        raise ValueError('Only the active owner with a real exit code can finish a batch')
    batch.update(status='succeeded' if exit_code == 0 else 'failed', exit_code=exit_code)


def worker(plan_path):
    """Each Slurm-bound process owns exactly one GPU and one batch at a time."""
    sys.path.insert(0, str(ROOT / 'infra'))
    from harness_state import mutate_gpu_queue, now_iso
    plan = read_json(plan_path)
    rank = int(os.environ['SLURM_PROCID'])
    allocation = plan['allocation']
    if (os.environ.get('SLURM_JOB_ID') != allocation['slurm_allocation'] or
            platform.node().split('.')[0] != allocation['node']):
        raise ValueError('Parallel worker is outside its recorded allocation')
    base = OUT / 'raw' / plan['pool_id']
    state_path = base / 'dispatch.json'
    visible = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid,name',
        '--format=csv,noheader'], text=True).strip().splitlines()
    if len(visible) != 1 or 'A6000' not in visible[0]:
        raise ValueError('Slurm must expose exactly one A6000 to each worker')
    uuid = visible[0].split(',')[0].strip()
    with locked_state(state_path) as state:
        if state.get('startup_error') or state.get('worker_errors'):
            raise ValueError('An earlier worker aborted this startup')
        if state['plan_sha256'] != sha(plan_path) or str(rank) in state['workers']:
            raise ValueError('Changed execution plan or duplicate worker')
        if uuid not in plan['assigned_gpu_uuids'] or any(w['uuid'] == uuid for w in state['workers'].values()):
            raise ValueError('GPU is outside allocation or already owned by another worker')
        state['workers'][str(rank)] = dict(uuid=uuid, pid=os.getpid(),
            slurm_step_id=os.environ.get('SLURM_STEP_ID'), registered_at=now_iso())
    deadline = time.monotonic() + 300
    while True:
        # Writers replace the JSON atomically. Poll without repeatedly taking
        # and rewriting the shared state lock during worker registration.
        state = read_json(state_path)
        if state.get('startup_error') or state.get('worker_errors'):
            raise RuntimeError('Another worker aborted parallel startup')
        ready = set(state['workers']) == {'0', '1', '2', '3'}
        if ready:
            break
        if time.monotonic() >= deadline:
            with locked_state(state_path) as state:
                if set(state['workers']) == {'0', '1', '2', '3'}:
                    continue
                state['startup_error'] = 'Four distinct GPU workers did not register within300 seconds'
            raise RuntimeError('Four distinct Slurm GPU workers did not register')
        time.sleep(1)
    source_plan_ref = plan['predecessor_execution']
    source_plan_path = ROOT / source_plan_ref['path']
    if sha(source_plan_path) != source_plan_ref['sha256']:
        raise ValueError('Predecessor execution changed')
    source_plan = read_json(source_plan_path)
    source_dispatch = OUT / 'raw' / source_plan['pool_id'] / 'dispatch.json'
    selection = read_json(ROOT / plan['selection']['path'])
    full_rows = {}
    for manifest in selection['manifests']:
        from scripts.stage7a.common import read_jsonl
        full_rows.update({row['event_id']: row for row in read_jsonl(ROOT / manifest)})
    # A new Slurm step may overlap the old allocation, but a model may not overlap
    # the predecessor on the same GPU. Its terminal status is written after exit.
    while True:
        predecessor = read_json(source_dispatch)
        owners = predecessor['workers']
        busy = any(b['status'] == 'running' and owners[str(b['rank'])]['uuid'] == uuid
                   for b in predecessor['batches'])
        if not busy:
            break
        with locked_state(state_path) as state:
            state['workers'][str(rank)]['phase'] = 'waiting_for_predecessor_gpu'
        time.sleep(5)
    with locked_state(state_path) as state:
        state['workers'][str(rank)]['phase'] = 'dispatching'
    while True:
        predecessor = read_json(source_dispatch)
        if not (predecessor.get('worker_errors') or
                any(b['status'] == 'failed' for b in predecessor['batches'])):
            raise ValueError('Predecessor might still claim unstarted work')
        with locked_state(state_path) as state:
            batch = claim_next(state, rank, predecessor)
            if batch is not None:
                def start(queue):
                    job = next(j for j in queue['jobs'] if j['id'] == batch['queue_id'])
                    if job['status'] != 'queued':
                        raise ValueError('Batch is not uniquely queued')
                    job.update(status='running', launcher='existing_slurm_parallel_step',
                        slurm_job_id=allocation['slurm_allocation'], started_at=now_iso(),
                        gpu_uuid=uuid, slurm_task_rank=rank,
                        slurm_step_id=os.environ.get('SLURM_STEP_ID'))
                mutate_gpu_queue(ROOT, start)
        if batch is None:
            current = read_json(state_path)
            if current.get('worker_errors') or current.get('startup_error') or any(b['status'] == 'failed' for b in current['batches']):
                return
            if any(b['status'] == 'pending' for b in current['batches']):
                time.sleep(5)
                continue
            with locked_state(state_path) as state:
                state['workers'][str(rank)]['phase'] = 'finished'
            return
        command = [str(ROOT / '.venv/bin/python'), 'scripts/stage7a_bench/native_images_v9.py',
                   '--run-id', batch['run_id'], '--bounded-attention']
        for manifest, digest in batch['manifest_hashes'].items():
            if sha(ROOT / manifest) != digest:
                raise ValueError('Frozen queued manifest changed')
            command += ['--manifest', manifest]
        command += ['--selection', batch['selection'],
                    '--execution-plan', str(plan_path.relative_to(ROOT))]
        code = 1
        attempts = []
        started = time.time()
        try:
            members = next(b['event_ids'] for b in selection['batches'] if b['run_id'] == batch['run_id'])
            rows = [full_rows[event] for event in members]
            old_batch = next(b for b in predecessor['batches'] if b['run_id'] == batch['predecessor_run_id'])
            dest = OUT / 'native_screen/generations' / batch['run_id']
            preserve_predecessor(dest, rows, old_batch, source_plan_ref)
            code, attempts = run_attempts(command, dest, ROOT / batch['log_path'], set(members))
        finally:
            record = dict(exit_code=code, completed=code == 0,
                slurm_job_id=allocation['slurm_allocation'], slurm_step_id=os.environ.get('SLURM_STEP_ID'),
                rank=rank, gpu_uuid=uuid, started_unix=started, finished_at=now_iso(),
                elapsed_wall_seconds=time.time() - started, command=command, plan_sha256=sha(plan_path),
                process_attempts=attempts, predecessor_run_id=batch['predecessor_run_id'])
            write_json(OUT / 'raw' / batch['run_id'] / 'run_summary.json', record, freeze=True)
            with locked_state(state_path) as state:
                finish_batch(state, batch['run_id'], rank, code)
                def finish(queue):
                    job = next(j for j in queue['jobs'] if j['id'] == batch['queue_id'])
                    if job['slurm_job_id'] != allocation['slurm_allocation'] or job['slurm_task_rank'] != rank:
                        raise ValueError('Queue ownership changed')
                    job.update(status='succeeded' if code == 0 else 'failed', **record)
                mutate_gpu_queue(ROOT, finish)
        print('BATCH_FINISHED', batch['run_id'], code, flush=True)
        if code:
            raise SystemExit(code if code > 0 else 1)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--execution-plan', required=True)
    args = parser.parse_args()
    plan_path = (ROOT / args.execution_plan).resolve()
    if not plan_path.is_relative_to(OUT / 'config'):
        raise ValueError('Execution plan outside active config directory')
    try:
        worker(plan_path)
    except BaseException as error:
        # Publish startup/import failures as well as batch failures. A late
        # worker registration cannot turn a failed group into a ready group.
        plan = read_json(plan_path)
        with locked_state(OUT / 'raw' / plan['pool_id'] / 'dispatch.json') as state:
            state.setdefault('worker_errors', {})[os.environ.get('SLURM_PROCID', 'unknown')] = repr(error)
        raise
