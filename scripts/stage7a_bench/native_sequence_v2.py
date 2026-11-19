"""Launch frozen native batches serially inside the existing tmux allocation.

This lightweight controller performs no inference and submits no Slurm job.
Every GPU batch is registered by the existing-allocation launcher. Any failure
stops the sequence for inspection; it never retries or changes the cohort.
"""
import subprocess
import time

from scripts.stage7a.common import ROOT, read_json, sha, write_json

OUT = ROOT / 'outputs/stage7a_bench_v2'


def main():
    plan_path = OUT / 'config/native_execution_sequence.json'
    plan = read_json(plan_path)
    for batch in plan['batches']:
        predecessor = OUT / 'raw' / batch['after_run_id'] / 'run_summary.json'
        while not predecessor.exists():
            time.sleep(20)
        prior = read_json(predecessor)
        if not prior['completed'] or prior['exit_code'] != 0:
            raise RuntimeError('Predecessor failed: ' + batch['after_run_id'])
        evidence = OUT / 'native_screen/generations' / batch['after_run_id'] / 'run_summary.json'
        if not evidence.exists() or not read_json(evidence)['completed']:
            raise RuntimeError('Missing predecessor scientific completion record')
        target = OUT / 'raw' / batch['run_id'] / 'run_summary.json'
        if target.exists():
            if not read_json(target)['completed']:
                raise RuntimeError('Existing failed target cannot be retried automatically')
            continue
        for path, expected in batch['manifest_hashes'].items():
            if sha(ROOT / path) != expected:
                raise RuntimeError('Frozen queued manifest changed: ' + path)
        # Allow the worker to return to its interactive allocation shell after
        # writing completion. The launcher independently checks it is idle.
        time.sleep(3)
        command = [str(ROOT / '.venv/bin/python'), 'scripts/stage7a_bench/launch_images_v2_existing.py',
                   '--run-id', batch['run_id'], '--', '--bounded-attention']
        for manifest in batch['manifest_hashes']:
            command += ['--manifest', manifest]
        subprocess.run(command, cwd=ROOT, check=True)
        write_json(OUT / 'audit/native_sequence_progress.json', dict(
            sequence_sha256=sha(plan_path), launched=batch['run_id'], predecessor=batch['after_run_id'],
            time_unix=time.time(), new_allocation=False))
    print('All frozen native batches launched serially; inspect final completion.', flush=True)


if __name__ == '__main__':
    main()
