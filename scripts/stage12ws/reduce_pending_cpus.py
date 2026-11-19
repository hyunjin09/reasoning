"""Reduce only pending W-S CPU requests to fit two available node02 cores."""
import argparse
import re
import subprocess
from pathlib import Path

import gpu_scheduler as scheduler
from scripts.stage12ws.common import ROOT, PREFIX, now, save


def main(phase):
    assert re.fullmatch(r'[A-Za-z0-9_]+', phase)
    jobs = [j for j in scheduler.load_gpu_queue(Path.cwd())['jobs']
            if j['id'].startswith(PREFIX + phase + '_')]
    for job in jobs:
        jid = str(job['slurm_job_id'])
        command = ['scontrol', 'show', 'job', jid, '-o']
        before = subprocess.run(command, check=True, capture_output=True, text=True).stdout
        if 'JobState=PENDING' not in before or 'CPUs/Task=2' in before:
            continue
        save(ROOT/'audit'/f'cpu_request_adjustment_{jid}_before.json',
             dict(at=now(), raw=before, reason='Operational CPU fit only; fixed single-thread OMP/OpenBLAS; scientific inputs and GPU/RAM/walltime unchanged.'))
        subprocess.run(['scontrol', 'update', f'JobId={jid}', 'NumCPUs=2',
                        'CPUsPerTask=2', 'MinCPUsNode=2', 'TresPerTask=cpu:2'], check=True)
        after = subprocess.run(command, check=True, capture_output=True, text=True).stdout
        assert all(s in after for s in ['NumCPUs=2', 'CPUs/Task=2', 'MinCPUsNode=2', 'TresPerTask=cpu:2'])
        save(ROOT/'audit'/f'cpu_request_adjustment_{jid}_consistent.json', dict(at=now(), raw=after))

        def update(queue):
            row = next(j for j in queue['jobs'] if j['id'] == job['id'])
            row.update(cpus=2, updated_at=now(), notes='Pending CPU request4→2; original launch and resource-change receipts preserved.')

        scheduler.mutate_gpu_queue(Path.cwd(), update)
        print(jid, 'pending CPU request reduced to2')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase')
    main(parser.parse_args().phase)
