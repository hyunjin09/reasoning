"""Finite, user-authorized post-Stage7A allocation maintenance between pilots.

No research outputs. Stop by creating the run directory's STOP file. Uses only
the existing Slurm allocation and exits after twenty minutes at the latest.
"""
import os
import platform
import signal
import sys
import time

import torch

from scripts.stage7a.common import ROOT, read_json, write_json

sys.path.insert(0, str(ROOT / 'infra'))
from harness_state import mutate_gpu_queue, now_iso


def main():
    run = 'review_maintenance_20260915_0300'
    job_id = 'stage7a_bench_v2_'+run
    base = ROOT / 'outputs/stage7a_bench_v2'
    runtime = read_json(base / 'config/runtime_node02_v3.json')['runtime']
    if not read_json(ROOT / 'outputs/stage7a/summaries/stage7a_acceptance.json')['execution_complete']:
        raise RuntimeError('Prior Stage7A completion is required for authorized maintenance')
    if (os.environ.get('SLURM_JOB_ID') != runtime['slurm_allocation'] or
            platform.node().split('.')[0] != runtime['node'] or torch.cuda.device_count() != 4):
        raise RuntimeError('Use only the existing four-GPU allocation')
    dest = base / 'raw' / run
    dest.mkdir(parents=True, exist_ok=False)
    running = True

    def stop(*args):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    started = time.time()
    write_json(dest / 'environment.json', dict(research_result=False,
        purpose='Resume previously authorized post-Stage7A maintenance across03:00KST CPU-review gap',
        slurm_job_id=os.environ['SLURM_JOB_ID'], node=platform.node(),
        devices=[torch.cuda.get_device_name(i) for i in range(4)], torch_version=torch.__version__,
        dtype='bfloat16', matrix_size=4096, max_seconds=1200,
        stop_file=str((dest / 'STOP').relative_to(ROOT)), started_unix=started), freeze=True)
    failed = True
    iterations = 0
    try:
        matrices = []
        for index in range(4):
            with torch.cuda.device(index):
                a = torch.randn((4096, 4096), device=f'cuda:{index}', dtype=torch.bfloat16)
                matrices.append((a, torch.randn_like(a), torch.empty_like(a)))
        last = 0
        with torch.inference_mode():
            while running and time.time()-started < 1200 and not (dest / 'STOP').exists():
                for a, b, out in matrices:
                    with torch.cuda.device(a.device):
                        for _ in range(64):
                            torch.mm(a, b, out=out)
                for index in range(4):
                    torch.cuda.synchronize(index)
                iterations += 64
                now = time.time()
                if now-last >= 30:
                    heartbeat = dict(running=True, iterations_per_gpu=iterations,
                        seconds=now-started, heartbeat_unix=now, research_result=False)
                    write_json(dest / 'heartbeat.json', heartbeat)
                    print(heartbeat, flush=True)
                    last = now
        failed = False
    finally:
        record = dict(completed=not failed, seconds=time.time()-started,
            iterations_per_gpu=iterations, research_result=False, finished_at=now_iso(),
            exit_code=int(failed), stop_file_present=(dest / 'STOP').exists())
        write_json(dest / 'run_summary.json', record, freeze=True)

        def finish(queue):
            job = next(j for j in queue['jobs'] if j['id'] == job_id)
            if job['slurm_job_id'] != runtime['slurm_allocation']:
                raise RuntimeError('Maintenance allocation changed')
            job.update(status='failed' if failed else 'succeeded', **record)

        mutate_gpu_queue(ROOT, finish)


if __name__ == '__main__':
    main()
