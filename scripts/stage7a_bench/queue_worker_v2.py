"""Preserve failure evidence and queue status for the registered existing job."""
import argparse
import os
import subprocess
import sys
from scripts.stage7a.common import ROOT, write_json

sys.path.insert(0, str(ROOT / 'infra'))
from harness_state import mutate_gpu_queue, now_iso


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    args, extra = parser.parse_known_args()
    code = 1
    try:
        code = subprocess.call([str(ROOT / '.venv/bin/python'),
            'scripts/stage7a_bench/native_v2.py', '--run-id', args.run_id, *extra])
    finally:
        record = dict(exit_code=code, completed=code == 0,
                      slurm_job_id=os.environ.get('SLURM_JOB_ID'), finished_at=now_iso())
        write_json(ROOT / 'outputs/stage7a_bench_v2/raw' / args.run_id / 'run_summary.json', record)
        def finish(queue):
            job = next(j for j in queue['jobs'] if j['id'] == 'stage7a_bench_v2_' + args.run_id)
            assert job['slurm_job_id'] == record['slurm_job_id']
            job.update(status='succeeded' if code == 0 else 'failed', **record)
        mutate_gpu_queue(ROOT, finish)
    sys.exit(code)


if __name__ == '__main__':
    main()
