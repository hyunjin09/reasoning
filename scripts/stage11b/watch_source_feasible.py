"""Launch only four frozen discovery shards as capacity frees; never a next phase."""
import argparse
import os
import re
import subprocess
import time
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage11b.common import ROOT, load, save, now


def main(once=False):
    project = Path.cwd()
    execution = load(ROOT/'source_feasible_execution.json')
    assert execution['worst_case_stage_gpu_hours'] <= execution['hard_limit_gpu_hours'] == 8
    targets = {'stage11b_feasible_'+s['id'] for s in load(ROOT/'source_feasible_tasks.json')['shards']}
    assert len(targets) == execution['new_job_count'] == 4
    args = SimpleNamespace(max_user_gpus=8, squeue_output=None, all_squeue_output=None,
        scontrol_output=None, available_gpus=None)
    os.environ['SBATCH_TIMELIMIT'] = '01:30:00'
    deadline = time.monotonic()+12*3600
    receipts = ROOT/'audit/source_feasible_terminal_receipts'
    receipts.mkdir(parents=True, exist_ok=True)
    while True:
        queue = scheduler.load_gpu_queue(project)
        jobs = [j for j in queue['jobs'] if j['id'] in targets]
        assert len(jobs) == 4
        for job in jobs:
            if job['status'] != 'running' or not job['slurm_job_id']:
                continue
            result = subprocess.run(['scontrol', 'show', 'job', str(job['slurm_job_id']), '-o'], capture_output=True, text=True)
            if result.returncode:
                continue
            fields = dict(re.findall(r'(\w+)=([^\s]+)', result.stdout))
            if fields.get('JobState') in ['RUNNING', 'PENDING', 'CONFIGURING', 'COMPLETING']:
                continue
            dest = receipts/(str(job['slurm_job_id'])+'.json')
            if not dest.exists():
                save(dest, dict(at=now(), queue=job, fields=fields, raw=result.stdout))
            worker_exit = ROOT/'source_feasible/workers'/str(job['slurm_job_id'])/'exit.json'
            success = fields.get('JobState') == 'COMPLETED' and fields.get('ExitCode') == '0:0' and worker_exit.exists() and load(worker_exit)['complete']
            state = 'succeeded' if success else 'failed'
            subprocess.run([str(project/'.venv/bin/python'), 'infra/gpu_scheduler.py', 'update', '--project', '.',
                '--id', job['id'], '--status', state, '--note', 'Terminal Slurm receipt preserved; finite source-feasible shard '+state], check=True)
        queue = scheduler.load_gpu_queue(project)
        jobs = [j for j in queue['jobs'] if j['id'] in targets]
        stop = (ROOT/'source_feasible/STOP').exists()
        if any(j['status'] == 'failed' for j in jobs):
            stop = True
        if not stop:
            status = scheduler.gpu_status(args, queue)
            for job in scheduler.plan_jobs({'jobs': jobs}, status):
                assert job['id'] in targets and job['node'] in ['node02', 'node03', 'node06', 'node07']
                assert job['gpu_type'] == 'a6000' and job['gpus'] == 1 and not job.get('allow_slurm_pending')
                scheduler.execute_launch(project, job)
                print(now(), 'LAUNCHED', job['id'], job['node'], flush=True)
        else:
            for job in jobs:
                if job['status'] == 'queued':
                    subprocess.run([str(project/'.venv/bin/python'), 'infra/gpu_scheduler.py', 'update', '--project', '.',
                        '--id', job['id'], '--status', 'cancelled', '--note', 'Source-feasible coordinator stopped; no automatic retries or phase launch'], check=True)
        jobs = [j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in targets]
        print(now(), [(j['id'], j['status'], j.get('slurm_job_id')) for j in jobs], flush=True)
        terminal = all(j['status'] in ['succeeded', 'failed', 'cancelled'] for j in jobs)
        if terminal:
            save(ROOT/'audit/source_feasible_coordinator_exit.json', dict(at=now(), jobs=jobs,
                status='READY_FOR_MANUAL_ANSWER_REVIEW' if all(j['status']=='succeeded' for j in jobs) else 'STOP_NEEDS_REVIEW',
                no_heldout_or_oracle_or_next_experiment_launched=True))
            return
        if once:
            return
        if time.monotonic() > deadline:
            save(ROOT/'audit/source_feasible_coordinator_timeout.json', dict(at=now(), jobs=jobs, queued_jobs_not_launched=True))
            return
        time.sleep(60)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--once', action='store_true')
    main(p.parse_args().once)
