"""Dispatch frozen native batches within one existing four-GPU Slurm step."""
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


def claim_next(state, rank):
    if type(rank) is not int or not 0 <= rank < 4:
        raise ValueError('Expected one of four Slurm task ranks')
    if any(b['status'] == 'failed' for b in state['batches']):
        return None
    if any(b['status'] == 'running' and b['rank'] == rank for b in state['batches']):
        raise ValueError('Worker already owns an active batch')
    for batch in state['batches']:
        if batch['status'] == 'pending':
            batch.update(status='running', rank=rank)
            return deepcopy(batch)
    return None


def finish_batch(state, run_id, rank, exit_code):
    batch = next(b for b in state['batches'] if b['run_id'] == run_id)
    if batch['status'] != 'running' or batch['rank'] != rank or type(exit_code) is not int:
        raise ValueError('Only the active owner with a real exit code can finish a batch')
    batch.update(status='succeeded' if exit_code == 0 else 'failed', exit_code=exit_code)


def worker():
    """Each Slurm-bound process owns exactly one GPU and one batch at a time."""
    sys.path.insert(0, str(ROOT / 'infra'))
    from harness_state import mutate_gpu_queue, now_iso
    plan_path = OUT / 'config/native_parallel_execution_v3.json'
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
        if state['plan_sha256'] != sha(plan_path) or str(rank) in state['workers']:
            raise ValueError('Changed execution plan or duplicate worker')
        if uuid not in plan['assigned_gpu_uuids'] or any(w['uuid'] == uuid for w in state['workers'].values()):
            raise ValueError('GPU is outside allocation or already owned by another worker')
        state['workers'][str(rank)] = dict(uuid=uuid, pid=os.getpid(),
            slurm_step_id=os.environ.get('SLURM_STEP_ID'), registered_at=now_iso())
    deadline = time.monotonic() + 60
    while True:
        with locked_state(state_path) as state:
            ready = set(state['workers']) == {'0', '1', '2', '3'}
        if ready:
            break
        if time.monotonic() >= deadline:
            raise RuntimeError('Four distinct Slurm GPU workers did not register')
        time.sleep(1)
    while True:
        with locked_state(state_path) as state:
            batch = claim_next(state, rank)
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
            return
        command = [str(ROOT / '.venv/bin/python'), 'scripts/stage7a_bench/native_images_v3.py',
                   '--run-id', batch['run_id'], '--bounded-attention']
        for manifest, digest in batch['manifest_hashes'].items():
            if sha(ROOT / manifest) != digest:
                raise ValueError('Frozen queued manifest changed')
            command += ['--manifest', manifest]
        if batch.get('continuation'):
            command += ['--continuation', batch['continuation']]
        code = 1
        started = time.time()
        try:
            with (ROOT / batch['log_path']).open('x') as log:
                code = subprocess.call(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        finally:
            record = dict(exit_code=code, completed=code == 0,
                slurm_job_id=allocation['slurm_allocation'], slurm_step_id=os.environ.get('SLURM_STEP_ID'),
                rank=rank, gpu_uuid=uuid, started_unix=started, finished_at=now_iso(),
                elapsed_wall_seconds=time.time() - started, command=command, plan_sha256=sha(plan_path))
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
    worker()
