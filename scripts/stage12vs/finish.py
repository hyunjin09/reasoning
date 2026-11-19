"""Verify complete evidence, render deliverables, then seal the final STOP."""
import argparse
import subprocess
from pathlib import Path
import pandas as pd
from scripts.stage12vs.common import ROOT, load, save, sha, now
from scripts.stage12vs.launch import account
from scripts.stage12vs.review import checked

REQUIRED = ['portable_state_localization_spec.md', 'primary_manifest.json', 'semantic_steps.json',
            'step_annotations.json', 'coarse_prefix_manifest.json', 'coarse_results.parquet',
            'fine_localization.json', 'adjacent_thinking_checks.parquet', 'critical_step_interventions.json',
            'content_ablation_results.parquet', 'replicated_evidence_oracle.parquet',
            'evidence_plus_step_results.parquet', 'primary_inference.json', 'decision.json',
            'resource_accounting.json', 'summary.md']


def prepare():
    info = load(ROOT / 'stage12vs_primary_inference.json')
    rows = info['all_seed_rows']
    assert len(rows) == len(list((ROOT / 'generations').glob('*/result.json'))) == 162
    for phase in ['phaseA'] + [f'phaseB{i}' for i in range(1, 8)] + ['adjacentT', 'contentC', 'optionalE']:
        for task in load(ROOT / 'audit' / f'{phase}_execution.json')['tasks']:
            checked(task)
    for name, count in [('coarse_results', 72), ('adjacent_thinking_checks', 12),
                        ('content_ablation_results', 24), ('replicated_evidence_oracle', 6), ('evidence_plus_step_results', 6)]:
        assert len(pd.read_parquet(ROOT / f'stage12vs_{name}.parquet')) == count
    ledger = account('final_closure')
    assert ledger['all_released'] and ledger['allocated_gpu_hours'] <= 7
    assert all(r['status'] == 'COMPLETED' and r['exit_code'] == '0:0' for r in ledger['jobs'])
    live = subprocess.run(['squeue', '-h', '-u', 'hyunjin', '-o', '%i'], capture_output=True, text=True, check=True).stdout.split()
    assert not {r['slurm_job_id'] for r in ledger['jobs']}.intersection(live)
    for job in ledger['jobs']:
        worker = ROOT / 'workers' / job['slurm_job_id']
        end = load(worker / 'exit.json'); engine = load(worker / 'engine_ready.json')
        assert end['complete']
        job.update(environment=load(worker / 'environment.json'), dtype=engine['dtype'], runtime=engine['runtime'],
                   worker_calls=end['calls'], worker_seconds=end['seconds'], peak_memory_bytes=None,
                   memory_note='Exact peak not instrumented; model and KV allocation in preserved Slurm logs. vLLM reservation90%.')
    assert sum(j['worker_calls'] for j in ledger['jobs']) == 162
    resource = dict(**ledger, retries=0, downloads=0, includes_startup=True, scientific_calls=162,
                    observer_gpu_count=0, all_allocations_released=True,
                    latency_note='Requests overlap within batches; allocated GPU-hours use terminal Slurm wall time.')
    save(ROOT / 'stage12vs_resource_accounting.json', resource)
    history = load(ROOT / 'audit/preserved_history.json')['files']
    for path, digest in history.items():
        assert sha(path) == digest, path
    for seal in ['source_seal.json', 'analysis_rules_before_results.json']:
        for path, digest in load(ROOT / 'audit' / seal)['hashes'].items():
            assert sha(path) == digest, path
    qc = [r for p in (ROOT / 'audit').glob('*_scoring_closed.json') for r in load(p)['reviews']]
    assert all(r['agreement'] for r in qc)
    verification = dict(at=now(), calls_verified=162, scoreable=sum(r['correct'] is not None for r in rows),
                        missing=sum(r['correct'] is None for r in rows), qc_agreements=len(qc),
                        prior_files_unchanged=len(history), all_gpu_allocations_released=True,
                        source_and_analysis_hashes_unchanged=True)
    save(ROOT / 'audit/closure_checks.json', verification)
    from scripts.stage12vs.report import figures, reading_copies, summary
    figures(); reading_copies(info); summary(info, resource, verification)
    print('Prepared verified report; final STOP awaits artifact/figure review.', verification)


def close():
    checks = load(ROOT / 'audit/closure_checks.json')
    assert load(ROOT / 'audit/figure_review.json')['pass_all']
    for name in REQUIRED:
        if name != 'decision.json':
            path = ROOT / f'stage12vs_{name}'
            assert path.exists() and path.stat().st_size, path
    assert len(list((ROOT / 'figures').glob('V*.png'))) == len(list((ROOT / 'figures').glob('V*.pdf'))) == 4
    assert len(list(Path('reports/stage12vs/v1').glob('*_r*.md'))) == 162
    result = load(ROOT / 'audit/decision_candidate.json')
    result.update(at=now(), stage_complete=True, stop=True, next_experiment_launched=False)
    save(ROOT / 'stage12vs_decision.json', result)
    artifacts = [ROOT / f'stage12vs_{name}' for name in REQUIRED]
    save(ROOT / 'audit/final_verification.json', dict(**checks, final_at=now(), pass_all=True,
         required_artifacts=len(REQUIRED), artifact_hashes={str(p): sha(p) for p in artifacts},
         analysis_implementation_sha256=sha('scripts/stage12vs/analyze.py'),
         report_implementation_sha256=sha('scripts/stage12vs/report.py'), next_experiment_launched=False))
    print('Stage closed:', result['decision'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'close'])
    globals()[parser.parse_args().action]()
