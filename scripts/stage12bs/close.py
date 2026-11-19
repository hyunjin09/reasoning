"""Verify the completed frozen profile and close its resource/registry records."""
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

import pandas as pd

from scripts.stage12bs.common import ROOT, load, save, sha, now
from scripts.stage12bs.review import checked_generation, origin_for
from scripts.stage12bs.seal import preservation


def verify_hashes(mapping):
    for path, expected in mapping.items():
        assert sha(path) == expected, path


def main():
    target = ROOT / 'audit/final_verification.json'
    assert not target.exists(), 'Closure is immutable once written'
    preserved = preservation()
    full = load(ROOT / 'stage12bs_full_manifest.json')
    remaining = load(ROOT / 'stage12bs_remaining_generation_manifest.json')
    assert len(full['rows']) == len({r['family_id'] for r in full['rows']}) == 61
    assert sum(len(r['facts']) for r in full['rows']) == 157
    assert len(full['tasks']) == 183 and len(full['reuse']) == 72
    assert len(remaining['tasks']) == 111
    new_ids = {p.parent.name for p in (ROOT / 'generations').glob('*/generation.json')}
    assert new_ids == {t['task_id'] for t in remaining['tasks']}
    generated = []
    for task in full['tasks']:
        generation, checks = checked_generation(task)
        assert all(checks.values()), (task['task_id'], checks)
        generated.append(generation)
    for record in full['reuse']:
        folder = origin_for(record['task_id']) / 'generations' / record['task_id']
        for kind in ['generation', 'input', 'result']:
            assert sha(folder / f'{kind}.json') == record[f'{kind}_sha256']

    denominators = load(ROOT / 'audit/denominator_seal.json')
    correctness = load(ROOT / 'audit/correctness_seal.json')
    first = load(ROOT / 'audit/first_scoring_seal.json')
    opened = load(ROOT / 'audit/correctness_opened.json')
    paired = load(ROOT / 'audit/paired_analysis_opened.json')
    verify_hashes(denominators['annotation_hashes'])
    verify_hashes(first['first_hashes'])
    verify_hashes(correctness['label_hashes'])
    verify_hashes(correctness['output_hashes'])
    assert sha(ROOT / 'stage12bs_integrity_results.parquet') == denominators['integrity_sha256']
    for arm, expected in opened['packet_hashes'].items():
        assert sha(ROOT / f'audit/correctness_packets/{arm}.jsonl') == expected
    assert denominators['at'] <= opened['at'] < correctness['at'] <= paired['at']
    assert paired['correctness_seal_sha256'] == sha(ROOT / 'audit/correctness_seal.json')
    assert len(list((ROOT / 'audit/first_scores').glob('*.json'))) == 183
    second_ids = {p.stem for p in (ROOT / 'audit/second_scores').glob('*.json')}
    assert second_ids == set(first['second_tasks']) and len(second_ids) == 103
    assert set(first['mandatory_tasks']).issubset(second_ids)
    assert len(list((ROOT / 'audit/adjudications').glob('*.json'))) == 3

    integrity = pd.read_parquet(ROOT / 'stage12bs_integrity_results.parquet')
    profile = pd.read_parquet(ROOT / 'stage12bs_failure_profiles.parquet')
    assert len(integrity) == 183 and integrity.task_id.nunique() == 183
    assert len(profile) == profile.family_id.nunique() == 61
    assert len(pd.read_parquet(ROOT / 'stage12bs_pathology_analysis.parquet')) == 61
    for name in ['evidence', 'native', 'oracle']:
        scores = pd.read_parquet(ROOT / f'stage12bs_{name}_scoring_blind.parquet')
        assert len(scores) == scores.family_id.nunique() == 61
    assert integrity.INPUT_VALID.all()
    assert integrity.groupby('arm').SCOREABLE.sum().to_dict() == {'E': 60, 'N': 57, 'O': 55}
    assert profile.n.notna().sum() == 57 and profile.complete_profile.sum() == 51
    failures = profile[profile.complete_native_failure]
    classes = Counter(failures.bottleneck)
    assert classes == dict(B1=11, B2=1, B3=3, B4=11)
    assert len(failures) == 26 and (profile.n == False).sum() == 29
    assert (profile.bottleneck == 'TECHNICAL_UNRESOLVED').sum() == 10
    assert sorted(profile.loc[profile.n.notna(), 'family_id']) == denominators['native_scoreable_families']
    assert sorted(profile.loc[profile.complete_profile, 'family_id']) == denominators['complete_profile_families']
    inference = load(ROOT / 'stage12bs_primary_inference.json')
    assert inference['classes'] == classes
    assert math.isclose(sum(inference['endpoints'][f'P{i}']['estimate'] for i in range(3, 7)), 1)
    assert inference['endpoints']['P2']['numerator'] == failures.o.sum() == 12
    assert inference['bootstrap_seed'] == load(ROOT / 'config.json')['bootstrap_seed'] == 120220260929
    assert all(c['draws'] == 4000 for c in inference['contrasts'].values())
    decision = load(ROOT / 'stage12bs_profile_decision.json')
    assert decision['decision'] == 'PROFILE_INFORMATIVE' and not decision['follow_on_launched']
    assert decision['full_validity_gate']['pass'] and decision['oracle_integrity_pass']

    resource_path = ROOT / 'stage12bs_resource_accounting.json'
    resources = load(resource_path)
    save(ROOT / 'audit/resource_accounting_before_closure.json', resources)
    jobs = resources['jobs']
    assert len(jobs) == 4
    queue = {j['id']: j for j in load('state/gpu_experiment_queue.json')['jobs']}
    for job in jobs:
        assert job['status'] == 'COMPLETED' and job['exit_code'] == '0:0'
        assert queue[job['queue_id']]['status'] == 'succeeded'
    command = ['squeue', '--noheader', '--jobs=' + ','.join(j['slurm_job_id'] for j in jobs), '--format=%i|%T|%N|%b']
    live = subprocess.run(command, capture_output=True, text=True, check=True)
    assert not live.stdout.strip(), live.stdout
    save(ROOT / 'audit/final_slurm_queue.json', dict(at=now(), command=command, stdout=live.stdout, stderr=live.stderr))
    assert resources['all_stage_allocations_released'] and resources['allocated_gpu_hours'] < 5
    assert math.isclose(sum(j['allocated_gpu_seconds'] for j in jobs) / 3600, resources['allocated_gpu_hours'])
    new = pd.DataFrame([g for g in generated if g['task_id'] in new_ids])
    resources['closure_at'] = now()
    resources['prior_reused_gpu_hours_by_stage'] = {
        name: load(f'outputs/{name}/v1/{name}_resource_accounting.json')['allocated_gpu_hours']
        for name in ['stage12b', 'stage12br']
    }
    resources['prior_costs_included_in_new_compute'] = False
    resources['new_generation_statistics'] = {
        arm: dict(calls=len(part), total_tokens=int(part.tokens.sum()),
                  median_tokens=float(part.tokens.median()), maximum_tokens=int(part.tokens.max()),
                  median_request_latency_seconds=float(part.request_latency_seconds.median()),
                  maximum_request_latency_seconds=float(part.request_latency_seconds.max()))
        for arm, part in new.groupby('arm')
    }
    resources['annotation'] = dict(technical_calls=183, first_scoring_calls=183,
                                   second_scoring_calls=103, adjudications=3,
                                   independent_reviewer=False, measured_annotation_hours=None)
    resources['worker_receipts'] = {}
    for job in jobs:
        worker = ROOT / 'workers' / job['slurm_job_id']
        environment = load(worker / 'environment.json')
        assert load(worker / 'exit.json')['complete']
        resources['worker_receipts'][job['slurm_job_id']] = dict(
            environment=str(worker / 'environment.json'), engine_ready=str(worker / 'engine_ready.json'),
            exit=str(worker / 'exit.json'), gpu=environment['gpu'], packages=environment['packages'],
            total_gpu_memory_bytes=environment['total_gpu_memory'])
    resource_path.write_text(json.dumps(resources, indent=2) + '\n')

    for job in jobs:
        path = Path('state/runs') / f"{job['queue_id']}.json"
        record = load(path)
        record.update(status='completed', current_step='Generation completed; Stage12B-S PROFILE_INFORMATIVE',
                      node=job['node'], result_path=str(ROOT / 'stage12bs_summary.md'),
                      display_summary='All frozen calls and profiling complete; allocation released.',
                      updated_at=now(), completed_at=load(ROOT / 'workers' / job['slurm_job_id'] / 'exit.json')['at'])
        record['history'].append(dict(time=now(), event='stage12bs_closure', message='COMPLETED0:0; receipts verified; GPU released.'))
        path.write_text(json.dumps(record, indent=2) + '\n')

    required = [
        'scientific_profile_spec.md', 'full_manifest.json', 'remaining_generation_manifest.json',
        'integrity_results.parquet', 'evidence_scoring_blind.parquet', 'native_scoring_blind.parquet',
        'oracle_scoring_blind.parquet', 'second_review_log.json', 'scoring_audit.json',
        'failure_profiles.parquet', 'pathology_analysis.parquet', 'primary_inference.json',
        'sensitivity_results.json', 'profile_decision.json', 'resource_accounting.json', 'summary.md']
    artifacts = [ROOT / ('stage12bs_' + name) for name in required]
    assert all(p.is_file() and p.stat().st_size for p in artifacts)
    figures = list((ROOT / 'figures').glob('figure*.png')) + list((ROOT / 'figures').glob('figure*.pdf'))
    assert len(figures) == 10
    responses = list(Path('reports/stage12bs/v1').glob('*.md'))
    assert len(responses) == 62
    save(target, dict(at=now(), passed=True, preservation=preserved, logical_calls=183,
        new_calls=111, reused_calls=72, independent_families=61, frozen_facts=157,
        native_scoreable=57, complete_profiles=51, complete_native_failures=26, classes=dict(classes),
        chronological_seals_verified=True, all_generation_receipts_verified=True,
        scoring_and_second_review_hashes_verified=True, all_stage_gpus_released=True,
        required_artifacts=16, figures=5, raw_response_pages=61, follow_on_launched=False,
        output_hashes={str(p):sha(p) for p in artifacts + figures + responses},
        final_source_hashes={str(p):sha(p) for p in Path('scripts/stage12bs').glob('*.py')}))
    print(json.dumps(dict(passed=True, decision=decision['decision'], preservation=preserved,
                          gpu_hours=resources['allocated_gpu_hours'], final_verification=str(target))))


if __name__ == '__main__':
    main()
