"""Allocated GPU time, including failed and cancelled work; no output scoring."""
import argparse
from scripts.stage11b.common import ROOT, load, save, now

TERMINAL = {'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY', 'NODE_FAIL', 'PREEMPTED'}


def seconds(value):
    days, clock = value.split('-', 1) if '-' in value else ('0', value)
    h, m, s = map(int, clock.split(':'))
    return int(days)*86400+h*3600+m*60+s


def main(label, final=False):
    latest = {}
    snapshots = []
    for path in (ROOT/'audit').glob('resource_snapshot_*.json'):
        x = load(path)
        for r in x['jobs']:
            if r['slurm_fields']:
                snapshots.append((x['at'], str(r['queue'].get('slurm_job_id')), r['slurm_fields'], str(path)))
    for path in (ROOT/'audit/source_feasible_terminal_receipts').glob('*.json'):
        x = load(path)
        snapshots.append((x['at'], str(x['queue']['slurm_job_id']), x['fields'], str(path)))
    for stamp, job_id, fields, path in sorted(snapshots):
        latest[job_id] = dict(at=stamp, fields=fields, evidence_path=path)
    rows = []
    for job in load('state/gpu_experiment_queue.json')['jobs']:
        if not job['id'].startswith('stage11b_'):
            continue
        job_id = str(job.get('slurm_job_id') or '')
        receipt = latest.get(job_id)
        fields = receipt['fields'] if receipt else {}
        terminal = fields.get('JobState') in TERMINAL if job_id else job['status'] in ['cancelled', 'failed']
        elapsed = seconds(fields['RunTime']) if fields.get('RunTime') else 0
        rows.append(dict(queue_id=job['id'], slurm_job_id=job_id or None,
            queue_status=job['status'], slurm_status=fields.get('JobState'), terminal=terminal,
            node=fields.get('NodeList') or job.get('node'), requested_gpus=job['gpus'],
            allocated_gpu_seconds_observed=elapsed*job['gpus'], observed_at=receipt['at'] if receipt else None,
            evidence_path=receipt['evidence_path'] if receipt else None,
            command=job['command'], log_path=job['log_path'], exit_code=fields.get('ExitCode')))
    if final:
        assert all(r['terminal'] for r in rows), 'All stage jobs must be terminal before final accounting'
        assert all(r['evidence_path'] for r in rows if r['slurm_job_id']), 'Never infer missing allocated time as zero'
    total = sum(r['allocated_gpu_seconds_observed'] for r in rows)
    generations = []
    partial_inputs = []
    for queue in ['discovery', 'source_feasible']:
        generations.extend(load(p) for p in (ROOT/queue/'results').glob('*/result.json'))
        partial_inputs.extend(str(p) for p in (ROOT/queue/'results').glob('*/input.json') if not (p.parent/'result.json').exists())
    output = dict(at=now(), final=final, jobs=rows, allocated_gpu_seconds_observed=total,
        allocated_gpu_hours_observed=total/3600, hard_limit_gpu_hours=8,
        under_hard_limit=total <= 8*3600, all_stage_allocations_released=all(r['terminal'] for r in rows),
        completed_generation_records=len(generations), budget_interrupted_records=sum(r['budget_interrupted'] for r in generations),
        complete_batch_generation_gpu_seconds=sum(r['batch_seconds']/4 for r in generations),
        input_only_attempts=partial_inputs, preflight_and_failed_and_cancelled_time_included=True,
        annotation_counts=dict(construction=128, initial_independent_reviews=256, independent_repair_reviews=16),
        caveat='Interim active runtimes are lower bounds at preserved snapshot timestamps. Allocated time includes startup, failures and abandoned in-flight batches. Model-agent annotation cost is not measured by Slurm GPU-hours.')
    dest = ROOT/'stage11b_resource_accounting.json' if final else ROOT/'audit'/f'resource_accounting_{label}.json'
    save(dest, output)
    print('GPUH_OBSERVED', total/3600, 'FINAL', final, 'TERMINAL', sum(r['terminal'] for r in rows), '/', len(rows))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('label')
    p.add_argument('--final', action='store_true')
    a = p.parse_args()
    main(a.label, a.final)
