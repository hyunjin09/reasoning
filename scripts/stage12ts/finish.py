"""Verify authorized Stage12T-S artifacts and account for released allocations."""
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.stage12ts.common import ROOT, load, save, sha, now
from scripts.stage12ts.resources import account
from scripts.stage12ts.review import all_tasks, checked_generation
from scripts.stage12ts.seal import preservation
from scripts.stage12ts.report import responses


REQUIRED = [
    'thinking_scientific_spec.md', 'thinking_manifest.json', 'reused24_manifest.json',
    'remaining37_manifest.json', 'integrity_results.parquet', 'thinking_results.parquet',
    'thinking_scoring_blind.parquet', 'scoring_review_log.json',
    'trace_evidence_states.parquet', 'cot_thinking_transitions.parquet',
    'pathology.parquet', 'primary_inference.json', 'sensitivity_results.json',
    'decision.json', 'resource_accounting.json', 'summary.md',
]


def main():
    assert not (ROOT/'audit/final_verification.json').exists()
    # A failed technical gate requires a separate, explicitly unscored closure.
    assert load(ROOT/'audit/denominator_seal.json')['pass']
    tasks = all_tasks()
    assert len(tasks) == 61 and len({t['family_id'] for t in tasks}) == 61
    for t in tasks:
        _, checks = checked_generation(t)
        assert all(checks.values()), t['task_id']
    expected = {t['task_id'] for t in load(ROOT/'stage12ts_remaining37_manifest.json')['rows']}
    paths = list((ROOT/'generations').glob('*/generation.json'))
    assert len(paths) == 37 and {p.parent.name for p in paths} == expected
    preserved = preservation()
    for name in ['denominator_seal', 'trace_seal', 'correctness_seal']:
        obj = load(ROOT/f'audit/{name}.json')
        for group in ['annotation_hashes', 'label_hashes', 'output_hashes']:
            for p, h in obj.get(group, {}).items():
                assert sha(p) == h, p
    counts = {'integrity_results': 61, 'thinking_results': 61,
              'thinking_scoring_blind': 61, 'trace_evidence_states': 26,
              'cot_thinking_transitions': 61, 'pathology': 61}
    for stem, n in counts.items():
        assert len(pd.read_parquet(ROOT/f'stage12ts_{stem}.parquet')) == n, stem
    artifacts = [ROOT/f'stage12ts_{name}' for name in REQUIRED]
    assert all(p.exists() and p.stat().st_size for p in artifacts
               if p.name != 'stage12ts_resource_accounting.json')
    for ext in ['png', 'pdf']:
        assert len(list((ROOT/'figures').glob(f'T*.{ext}'))) == 5

    ledger_path = ROOT/'audit/resource_closure.json'
    ledger = load(ledger_path) if ledger_path.exists() else account('closure')
    assert len(ledger['jobs']) == 3 and ledger['all_released']
    assert all(r['status'] == 'COMPLETED' and r['exit_code'] == '0:0' for r in ledger['jobs'])
    assert ledger['phases']['remaining']['allocated_gpu_hours'] <= 6.5
    ids = {str(r['slurm_job_id']) for r in ledger['jobs']}
    live = subprocess.run(['squeue', '-h', '-u', 'hyunjin', '-o', '%i'],
                          capture_output=True, text=True, check=True).stdout.split()
    assert not ids.intersection(live)
    jobs = []
    for r in ledger['jobs']:
        r = dict(r)
        w = ROOT/'workers'/r['slurm_job_id']
        env = load(w/'environment.json')
        engine = load(w/'engine_ready.json')
        end = load(w/'exit.json')
        assert end['complete']
        assert env['model']['revision'] == '1de27d8c51f12e819435303b9e84c4e25ba8401e'
        r.update(observed_gpu=env['gpu'], total_gpu_memory_bytes=env['total_gpu_memory'],
                 packages=env['packages'], dtype=engine['dtype'], runtime=engine['runtime'],
                 checkpoint_revision=env['model']['revision'],
                 worker_seconds=end['seconds'], calls=end['calls'],
                 peak_gpu_memory_bytes=None,
                 memory_note='Peak not instrumented; startup model/KV measurements retained in Slurm log.',
                 receipts={str(p): sha(p) for p in
                           [w/'environment.json', w/'engine_ready.json', w/'exit.json']})
        jobs.append(r)
    generations = [load(p) for p in paths]
    lengths = [g['tokens'] for g in generations]
    latencies = [g['request_latency_seconds'] for g in generations]
    assert sum(r['calls'] for r in jobs) == 37
    accounting_path = ROOT/'stage12ts_resource_accounting.json'
    if not accounting_path.exists():
        save(accounting_path, dict(
            at=now(), jobs=jobs, phases=ledger['phases'], all_allocations_released=True,
            includes_startup=True, allocated_gpu_hours=sum(r['allocated_gpu_hours'] for r in jobs),
            target_new_gpu_hours=4.5, hard_limit_new_gpu_hours=6.5,
            new_calls=37, reused_calls=24, total_families=61,
            reused_compute_charged_to_prior_stage=True,
            reused_accounting='outputs/stage12cr/v1/stage12tr_resource_accounting.json',
            total_new_generated_tokens=sum(lengths),
            new_token_quantiles=dict(zip(['min', 'q25', 'median', 'q75', 'max'],
                                         np.percentile(lengths, [0, 25, 50, 75, 100]).tolist())),
            latency_seconds_median=float(np.median(latencies)),
            latency_seconds_max=max(latencies),
            latency_note='Per-request elapsed latency in concurrent batches; sums are not GPU time.',
            environments=['.venv (CPU)', '.venv/official_eval (GPU)'],
            downloads=0, retries=0, third_cap_attempted=False))
    accounting = load(accounting_path)
    responses()
    assert len(list(Path('reports/stage12ts/v1').glob('T_*.md'))) == 61
    summary = ROOT/'stage12ts_summary.md'
    body = summary.read_text()
    marker = 'Resource accounting: stage12ts_resource_accounting.json.'
    if marker in body:
        note = (f"Final new allocated compute: {accounting['allocated_gpu_hours']:.6f} GPU-hours, "
                '37 new calls, 24 reused calls. All three jobs completed exit0 and released their GPUs. '
                'No retries or downloads. Resource details: stage12ts_resource_accounting.json.')
        summary.write_text(body.replace(marker, note, 1))
    save(ROOT/'audit/final_verification.json', dict(
        at=now(), pass_all=True, preservation=preserved, input_receipts_verified=61,
        new_calls=37, reused_calls=24, required_artifacts=len(REQUIRED),
        required_artifact_hashes={str(p): sha(p) for p in artifacts},
        supporting_analysis_source_hashes={str(p): sha(p) for p in Path('scripts/stage12ts').glob('*.py')},
        total_allocated_gpu_hours=accounting['allocated_gpu_hours'],
        all_allocations_released=True, next_experiment_launched=False))
    print('Stage12T-S closed:', load(ROOT/'stage12ts_decision.json')['states'])


if __name__ == '__main__':
    main()
