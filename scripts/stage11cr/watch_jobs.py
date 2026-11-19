"""Bounded receipt watcher for one already-submitted wave; never launches work."""
import argparse
import re
import subprocess
import time
from pathlib import Path
from scripts.stage11cr.common import ROOT, load, save, now

TERMINAL = {'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY',
            'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL', 'DEADLINE', 'REVOKED'}


def main(receipt_path, once=False):
    launch = load(receipt_path)
    jobs = launch['jobs']
    assert jobs and all(j['id'].startswith('stage11cr_') for j in jobs)
    deadline = time.monotonic()+12*3600
    label = Path(receipt_path).stem
    terminal_dir = ROOT/'audit/terminal_receipts'
    while True:
        observations = []
        for job in jobs:
            job_id = str(job['slurm_job_id'])
            dest = terminal_dir/(job_id+'.json')
            if dest.exists():
                observations.append(load(dest))
                continue
            result = subprocess.run(['scontrol', 'show', 'job', job_id, '-o'],
                                    capture_output=True, text=True, timeout=20)
            fields = dict(re.findall(r'(\w+)=([^\s]+)', result.stdout))
            record = dict(at=now(), queue=job, fields=fields, raw=result.stdout,
                          returncode=result.returncode, stderr=result.stderr)
            observations.append(record)
            if fields.get('JobState') in TERMINAL:
                save(dest, record)
                queue_path = Path(job['result_path'])
                worker_exit = queue_path/'workers'/job_id/'exit.json'
                success = (fields['JobState'] == 'COMPLETED' and
                           fields.get('ExitCode') == '0:0' and worker_exit.exists()
                           and load(worker_exit)['complete'])
                state = 'succeeded' if success else 'failed'
                subprocess.run(['.venv/bin/python', 'infra/gpu_scheduler.py', 'update',
                    '--project', '.', '--id', job['id'], '--status', state,
                    '--note', 'Stage11C-R terminal receipt preserved; finite wave '+state], check=True)
        stamp = now().replace(':', '').replace('.', '')
        save(ROOT/'audit/job_snapshots'/f'{label}_{stamp}.json',
             dict(at=now(), jobs=observations, no_launch_authority=True))
        print(now(), [(j['queue']['slurm_job_id'], j['fields'].get('JobState', 'UNKNOWN'))
                      for j in observations], flush=True)
        if all(j['fields'].get('JobState') in TERMINAL for j in observations):
            save(ROOT/'audit'/f'{label}_watch_exit.json',
                 dict(at=now(), status='TERMINAL_REVIEW_REQUIRED', jobs=observations,
                      no_next_phase_launched=True))
            return
        if once or time.monotonic() >= deadline:
            return
        time.sleep(60)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('receipt')
    p.add_argument('--once', action='store_true')
    a = p.parse_args()
    main(a.receipt, a.once)
