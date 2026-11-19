"""Stage11C allocated-time ledger, including unfinished and failed allocations."""
import argparse
import re
import subprocess
from scripts.stage11c.common import ROOT, load, save, now
from scripts.stage11c.watch_jobs import TERMINAL


def seconds(value):
    days, value = value.split('-', 1) if '-' in value else ('0', value)
    parts = list(map(int, value.split(':')))
    assert len(parts) in (2, 3)
    if len(parts) == 2:
        parts.insert(0, 0)
    h, m, s = parts
    return int(days)*86400+h*3600+m*60+s


def account(label, final=False):
    rows = []
    jobs = [j for j in load('state/gpu_experiment_queue.json')['jobs'] if j['id'].startswith('stage11c_')]
    for job in jobs:
        job_id = str(job.get('slurm_job_id') or '')
        terminal_path = ROOT/'audit/terminal_receipts'/f'{job_id}.json'
        if terminal_path.exists():
            receipt = load(terminal_path)
            evidence = str(terminal_path)
        elif job_id:
            result = subprocess.run(['scontrol', 'show', 'job', job_id, '-o'],
                                    capture_output=True, text=True, timeout=20)
            receipt = dict(at=now(), queue=job, raw=result.stdout, stderr=result.stderr,
                           returncode=result.returncode,
                           fields=dict(re.findall(r'(\w+)=([^\s]+)', result.stdout)))
            evidence = str(ROOT/'audit/resource_receipts'/f'{label}_{job_id}.json')
            save(evidence, receipt)
        else:
            receipt, evidence = dict(fields={}, at=now()), None
        fields = receipt['fields']
        terminal = fields.get('JobState') in TERMINAL
        # Missing accounting is unknown, never free compute.
        elapsed = seconds(fields['RunTime'])*job['gpus'] if 'RunTime' in fields else None
        upper = (elapsed if terminal else seconds(fields['TimeLimit'])*job['gpus']) if 'TimeLimit' in fields else None
        rows.append(dict(queue_id=job['id'], slurm_job_id=job_id or None,
            queue_status=job['status'], slurm_status=fields.get('JobState'), terminal=terminal,
            node=fields.get('NodeList') or job.get('node'), gpus=job['gpus'],
            allocated_gpu_seconds_observed=elapsed, committed_gpu_seconds_upper_bound=upper,
            evidence_path=evidence, observed_at=receipt['at'], exit_code=fields.get('ExitCode'),
            command=job['command'], log_path=job['log_path']))
    known = all(r['allocated_gpu_seconds_observed'] is not None for r in rows)
    total = sum(r['allocated_gpu_seconds_observed'] for r in rows) if known else None
    bound_known = all(r['committed_gpu_seconds_upper_bound'] is not None for r in rows)
    upper = sum(r['committed_gpu_seconds_upper_bound'] for r in rows) if bound_known else None
    if final:
        assert rows and known and all(r['terminal'] for r in rows)
    result = dict(at=now(), final=final, jobs=rows, accounting_known=known,
        allocated_gpu_hours_observed=total/3600 if known else None,
        committed_gpu_hours_upper_bound=upper/3600 if bound_known else None,
        hard_limit_gpu_hours=8, budget_safe_for_new_wave=bound_known and upper < 8*3600,
        all_stage_allocations_released=bool(rows) and all(r['terminal'] for r in rows),
        includes_startup_failures_cancelled_and_inflight=True,
        annotation_cost='Source model-agent review is separate from measured Slurm GPU time.')
    path = ROOT/'stage11c_resource_accounting.json' if final else ROOT/'audit'/f'resource_accounting_{label}.json'
    save(path, result)
    print(path, result['allocated_gpu_hours_observed'], result['committed_gpu_hours_upper_bound'])
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('label')
    p.add_argument('--final', action='store_true')
    a = p.parse_args()
    account(a.label, a.final)
