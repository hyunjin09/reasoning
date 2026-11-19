"""User-requested post-plan GPU workload in the existing allocation only.

Launch only after Stage7A reporting is complete. Stop with Ctrl-C in tmux10.
This is allocation maintenance, not a research experiment or a new allocation.
"""
import argparse
import os
import platform
import signal
import sys
import time
import torch
from scripts.stage7a.common import ROOT, OUT, read_json, write_json

sys.path.insert(0, str(ROOT / 'infra'))
from harness_state import mutate_gpu_queue, now_iso


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    acceptance = read_json(OUT / 'summaries/stage7a_acceptance.json')
    assert acceptance['execution_complete'], 'Launch utilization only after the authorized Stage7A work finishes'
    allocation = read_json(OUT / 'config/stage7a_config.json')['runtime']
    assert os.environ.get('SLURM_JOB_ID') == allocation['slurm_allocation']
    assert platform.node().split('.')[0] == allocation['node']
    assert torch.cuda.device_count() == 1
    running = True
    stopped_signal = None

    def stop(signum, frame):
        nonlocal running, stopped_signal
        running = False
        stopped_signal = signum

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    dest = OUT / 'raw' / args.run_id
    started = time.time()
    record = dict(purpose='User-requested post-Stage7A allocation maintenance',
                  slurm_job_id=os.environ['SLURM_JOB_ID'], node=platform.node(),
                  gpu=torch.cuda.get_device_name(0), torch_version=torch.__version__,
                  dtype='bfloat16', matrix_size=4096, started_unix=started,
                  stop_command='Ctrl-C in tmux session 10', research_result=False)
    write_json(dest / 'environment.json', record, freeze=True)
    a = torch.randn((4096, 4096), device='cuda', dtype=torch.bfloat16)
    b = torch.randn_like(a)
    out = torch.empty_like(a)
    iterations = 0
    last = 0.
    failed = False
    print(record, flush=True)
    try:
        with torch.inference_mode():
            while running:
                for _ in range(64):
                    torch.mm(a, b, out=out)
                torch.cuda.synchronize()
                iterations += 64
                now = time.time()
                if now - last >= 60:
                    progress = dict(running=True, iterations=iterations,
                                    seconds=now-started, heartbeat_unix=now,
                                    peak_gpu_bytes=torch.cuda.max_memory_allocated())
                    write_json(dest / 'heartbeat.json', progress)
                    print(progress, flush=True)
                    last = now
    except BaseException:
        failed = True
        raise
    finally:
        write_json(dest / 'run_summary.json', dict(running=False, iterations=iterations,
                   seconds=time.time()-started, stopped_unix=time.time(), stopped_signal=stopped_signal,
                   completed=not failed, research_result=False))
        def finish(queue):
            job = next(j for j in queue['jobs'] if j['id'] == 'stage7a_'+args.run_id)
            assert job['slurm_job_id'] == allocation['slurm_allocation']
            job.update(status='failed' if failed else 'succeeded', finished_at=now_iso(), exit_code=1 if failed else 0)
        mutate_gpu_queue(ROOT, finish)


if __name__ == '__main__':
    main()
