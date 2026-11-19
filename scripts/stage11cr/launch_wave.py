"""Submit one explicitly frozen Stage11C-R early/calibration wave, then return."""
import argparse
import os
import re
import shlex
import subprocess
from pathlib import Path
from types import SimpleNamespace
import gpu_scheduler as scheduler
from scripts.stage11cr.common import ROOT, load, save, sha, now
from scripts.stage11cr.resources import account


def main(manifest_name, label, minutes):
    assert re.fullmatch(r'[a-z0-9_]+', label) and 5 <= minutes <= 60
    path = ROOT/manifest_name
    manifest = load(path)
    assert manifest['frozen'] and manifest['config_sha256'] == sha(ROOT/'config.json')
    assert manifest['queue'] in ['known_good','diagnostic','nonprimary40960','native','oracle','neutral','cot','reserve']
    if manifest['queue'] not in ['known_good','diagnostic']:
        assert load(ROOT/'stage11cr_repaired_protocol.json')['pass']
    if manifest['queue'] in ['native','oracle','neutral','cot','reserve']:
        assert load(ROOT/'stage11cr_nonprimary_validation.json')['pass']
    n = len(manifest['shards'])
    assert 1 <= n <= 8
    ledger = account('prelaunch_'+label)
    assert ledger['accounting_known'] and ledger['committed_gpu_hours_upper_bound'] is not None
    worst = ledger['committed_gpu_hours_upper_bound'] + n*minutes/60
    assert worst <= 9, 'Hard9allocatedGPUh; no submission outside the remaining envelope'
    args = SimpleNamespace(max_user_gpus=8, squeue_output=None, all_squeue_output=None,
                           scontrol_output=None, available_gpus=None)
    project = Path.cwd()
    status = scheduler.gpu_status(args, scheduler.load_gpu_queue(project))
    assert not status['warnings'] and status['own_gpus']+n <= 8
    save(ROOT/'audit'/f'{label}_resource_envelope.json', dict(at=now(), frozen=True,
        manifest_sha256=sha(path), previous_committed_gpu_hours=ledger['committed_gpu_hours_upper_bound'],
        jobs=n, minutes_per_job=minutes, worst_case_stage_gpu_hours=worst, hard_limit_gpu_hours=9,
        scheduler_status=status, no_automatic_next_phase=True))
    targets = set()
    for shard in manifest['shards']:
        ident = 'stage11cr_'+label+'_'+shard['id']
        targets.add(ident)
        worker = 'scripts/stage11cr/diagnostic.py' if manifest['queue']=='diagnostic' else 'scripts/stage11cr/worker.py'
        command = shlex.join(['bash', 'scripts/stage11cr/run.sh', worker,
            '--manifest', str(path), '--manifest-sha256', sha(path), '--shard', shard['id'],
            '--max-seconds', str(minutes*60-120)])
        subprocess.run(['.venv/bin/python', 'infra/gpu_scheduler.py', 'add', '--project', '.',
            '--id', ident, '--exp-id', ident, '--gpu-type', 'a6000', '--gpus', '1', '--mem', '24G',
            '--cpus', '4', '--allow-slurm-pending', '--exclude-node', 'node01', '--exclude-node', 'node04',
            '--exclude-node', 'node05', '--command', command,
            '--log-path', f'runs/stage11cr/v1/{label}_{shard["id"]}/slurm.log',
            '--result-path', str(ROOT/manifest['queue'])], check=True)
    jobs = [j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in targets]
    assert len(jobs) == n and all(j['status']=='queued' for j in jobs)
    os.environ['SBATCH_TIMELIMIT'] = f'{minutes//60:02d}:{minutes%60:02d}:00'
    planned = scheduler.plan_jobs({'jobs': jobs}, status)
    assert len(planned) == n, 'Finite wave needs a new capacity check; no unrelated queue launch'
    for job in planned:
        assert job['id'] in targets and job['gpus'] == 1
        assert not job['node'] or job['node'] in ['node02', 'node03', 'node06', 'node07']
        scheduler.execute_launch(project, job)
    jobs = [j for j in scheduler.load_gpu_queue(project)['jobs'] if j['id'] in targets]
    save(ROOT/'audit'/f'{label}_launch_receipt.json', dict(at=now(), jobs=jobs))
    print('LAUNCHED_FINITE_WAVE', [(j['id'], j['slurm_job_id']) for j in jobs])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('manifest_name')
    p.add_argument('label')
    p.add_argument('--minutes', type=int, required=True)
    a = p.parse_args()
    main(a.manifest_name, a.label, a.minutes)
