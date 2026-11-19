"""Restart a poisoned vLLM process inside its allocation; skip identifiable OOMs."""
import argparse
import os
import signal
import subprocess
import sys
import time
from scripts.stage14c.common import *
from scripts.stage14c.oom_policy import remaining, resolve_oom, verify_recovery, missing_path
from scripts.stage14c.worker import authorize


def stop_group(child):
    # A crashed frontend can leave engine children holding VRAM. Only touch the
    # process group that this runner created, never other workers on the node.
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        pass
    time.sleep(1)
    try:
        os.killpg(child.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    child.wait(timeout=10)


def run(path, expected_hash, worker_command=None, poll_seconds=10):
    verify_recovery()
    assert sha(path) == expected_hash
    m = load(path); authorize(m)
    job = os.environ['SLURM_JOB_ID']
    dest = ROOT/'audit/workers'/job
    save(dest/'recovery_started.json', dict(at=now(), manifest=str(path), manifest_sha256=expected_hash,
        concurrency=m.get('batch_size',18), oom_action='skip identifiable sample, restart engine, continue'))
    total_finished = 0; beat_index = 0; previous_remaining = None; unknown_batch_retry = False; start=time.monotonic()
    try:
        # Each successful OOM recovery must remove at least one request. This
        # bound prevents crash/restart loops without progress.
        for cycle in range(len(m['rows']) + 2):
            tasks, attempts = remaining(m['rows'])
            if not tasks:
                save(dest/'exit.json', dict(at=now(), complete=True, calls=total_finished,
                    technical_missing=sum(missing_path(t).exists() for t in m['rows']),
                    queue_exhausted=True, recovery=True, seconds=time.monotonic()-start))
                return
            if previous_remaining is not None and not unknown_batch_retry:
                assert len(tasks) < previous_remaining, 'OOM recovery made no progress'
            previous_remaining = len(tasks)
            engine_id = f'{cycle:04d}'
            engine_dir = dest/'engines'/engine_id
            manifest = dict(m, rows=tasks, attempts=attempts, batch_size=18 if cycle==0 else 1, engine_id=engine_id)
            engine_manifest = dest/f'engine_{engine_id}_manifest.json'
            save(engine_manifest, manifest)
            engine_dir.mkdir(parents=True, exist_ok=True)
            log = engine_dir/'engine.log'
            with log.open('x') as stream:
                command = worker_command or [sys.executable, '-m', 'scripts.stage14c.worker']
                child = subprocess.Popen([*command,
                    str(engine_manifest), '--manifest-sha256', sha(engine_manifest)],
                    stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
                latest = None
                try:
                    while child.poll() is None:
                        beats = sorted(engine_dir.glob('heartbeat_*.json'))
                        if beats and beats[-1] != latest:
                            latest = beats[-1]; h = load(latest)
                            h['completed'] += total_finished
                            h.update(engine_id=engine_id, total=len(m['rows']))
                            save(dest/f'heartbeat_{beat_index:05d}.json', h); beat_index += 1
                        time.sleep(poll_seconds)
                    code = child.returncode
                finally:
                    stop_group(child)
            if code == 0:
                e = load(engine_dir/'exit.json')
                total_finished += e['calls']
                if e.get('technical_failures', 0):
                    raise RuntimeError('non-OOM technical failure requires review')
                # Same engine processed all remaining rows successfully.
                continue
            failure_path = engine_dir/'failure.json'
            failure = load(failure_path) if failure_path.exists() else {}
            culprit = resolve_oom(tasks, failure, log.read_text(errors='replace'),
                dict(job=job, engine_id=engine_id, failure=str(failure_path), log=str(log)))
            if culprit is None:
                assert cycle==0, 'Repeated unidentifiable OOM; hold'
                unknown_batch_retry=True
            else:
                unknown_batch_retry=False
            total_finished += failure.get('completed', 0)
            save(dest/f'oom_skip_{engine_id}.json', dict(at=now(), task_id=culprit,
                action='TECHNICAL_MISSING; fresh engine continues' if culprit else 'Unknown batch culprit; interrupted incomplete rows resume once at singleton'))
        raise RuntimeError('bounded OOM recovery exhausted')
    except BaseException as exc:
        save(dest/'failure.json', dict(at=now(), error=repr(exc), action='HOLD; no unrelated-error retry'))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest'); parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    run(args.manifest, args.manifest_sha256)
