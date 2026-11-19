"""Closure checks for the approved cohort, immutable evidence and compute limits."""
from collections import Counter
from scripts.stage14c.common import *


def validate_scope(tasks, native, eligible):
    assert eligible <= native
    expected = {(f, m, c) for f in native for m in 'IT'
                for c in (['native', 'equal_evidence'] if f in eligible else ['native'])}
    observed = [(t['family_id'], t['model_key'], t['condition']) for t in tasks]
    assert len({t['task_id'] for t in tasks}) == len(tasks), 'duplicate task ID'
    assert len(set(observed)) == len(observed), 'duplicate scientific condition'
    assert set(observed) == expected, 'missing or unauthorized scientific condition'


def validate_resources(record):
    assert not record['unknown_duration_jobs'], 'unknown allocation duration'
    assert 0 <= record['gpu_hours_observed_or_proxy'] <= 120
    assert not any(r['gpus'] and r['active'] for r in record['jobs']), 'GPU still allocated'
    d1 = [r for r in record['jobs'] if r['mode'] == 'D1' and r['gpus']]
    assert all(r['gpu_hours'] is not None and r['gpu_hours'] >= 0 for r in d1)
    assert sum(r['gpu_hours'] for r in d1) <= 12, 'D1 compute ceiling'


def check_hashes(name, fields=('files',)):
    record = load(ROOT / 'audit' / name)
    checked = 0
    for field in fields:
        for path, digest in record[field].items():
            assert sha(path) == digest, path
            checked += 1
    return checked


def main():
    from scripts.stage14c.accounting import accounting
    from scripts.stage14c.preflight import checked
    from scripts.stage14c.oom_policy import missing_path
    from scripts.stage14c.scoring_v5 import final_score
    from scripts.stage14c.d1_review_v2 import unit_maps, validate_units
    from scripts.stage14c.d1_scoring_v2 import validate_review

    hash_entries = sum(check_hashes(name) for name in [
        'g0_design_seal_v1.json', 'g2_execution_seal_v1.json',
        'D1_execution_seal_v1.json', 'D1_materialization_seal_v1.json',
        'D1_shared_unit_map_seal_v1.json',
        'parent_artifact_hashes_v1.json', 'main_raw_seal.json',
        'primary_analysis_seal.json', 'D1_raw_seal.json',
        'D1_scoring_seal.json', 'D1_analysis_seal.json'])
    hash_entries += check_hashes('g1_final_source_seal_v1.json',
                                ('input_hashes', 'artifact_hashes'))
    native = {r['family_id'] for r in rows(ROOT / 'source/cohort_manifest.jsonl')}
    eligible = {r['family_id'] for r in rows(ROOT / 'source/estar_eligibility_manifest.jsonl')
                if r['E_star_final_QC_passed']}
    assert len(native) == 1714 and len(eligible) == 580
    tasks = all_tasks('main')
    validate_scope(tasks, native, eligible)
    d1 = all_tasks('D1')
    assert len(d1) == 600 and len({t['task_id'] for t in d1}) == 600
    assert Counter((t['benchmark'], t['model_key']) for t in d1) == {
        (b, m): 100 for b in ['math', 'MMStar', 'BlindTest'] for m in 'IT'}
    assert all(len({t['family_id'] for t in d1 if t['model_key'] == m}) == 300 for m in 'IT')
    assert {t['family_id'] for t in d1 if t['model_key'] == 'I'} == {
        t['family_id'] for t in d1 if t['model_key'] == 'T'}
    missing = []
    for task in tasks + d1:
        result = checked(task)
        path = missing_path(task)
        assert bool(result) != path.exists(), task['task_id']
        if not result:
            record = load(path)
            assert record['task_sha256'] == fingerprint(task) and record['final_technical_failure']
            missing.append(task['task_id'])
    for model in 'IT':
        seal = load(ROOT / 'audit' / f'main_{model}_scoring_seal.json')
        assert set(seal['scores']) == {t['task_id'] for t in tasks if t['model_key'] == model}
        for tid, digest in seal['scores'].items():
            score = final_score(tid)
            assert fingerprint(score) == digest
            assert score['status'] in {'CORRECT', 'WRONG', 'UNSCORABLE', 'TECHNICAL_MISSING'}
        for tid in seal['audit_task_ids']:
            qc = load(ROOT / 'scoring/qc' / f'{tid}.json')
            assert qc['resolved'] and qc['score_sha256'] == fingerprint(final_score(tid))
    targets = {r['family_id']: r for r in rows(ROOT / 'source/D1_review_schema_v1.jsonl')}
    maps = unit_maps()
    for task in d1:
        first = load(ROOT / 'scoring/D1_pass1' / f"{task['task_id']}.json")
        second = load(ROOT / 'scoring/D1_pass2' / f"{task['task_id']}.json")
        assert second['first_review_sha256'] == fingerprint(first)
        for review in [first, second]:
            assert review['target_sha256'] == fingerprint(targets[task['family_id']])
            validate_units(maps[task['family_id']], review)
            validate_review(targets[task['family_id']], review['review'])
    primary = load(ROOT / 'audit/primary_summary_seal.json')
    assert primary['summary_sha256'] == sha(ROOT / 'summaries/stage14c_primary_summary.md')
    assert primary['primary_analysis_seal_sha256'] == sha(ROOT / 'audit/primary_analysis_seal.json')
    for launch in (ROOT / 'audit/launches').glob('job_*.json'):
        record = load(launch)
        if record['mode'] == 'D1':
            assert dt.datetime.fromisoformat(record['at']) > dt.datetime.fromisoformat(primary['at'])
    required = ['analysis/secondary_and_sensitivity.json', 'analysis/optional_diagnostics.json',
                'audit/technical_output_summary.json', 'summaries/stage14c_final_summary.md',
                'summaries/next_stage_recommendation.md']
    required += [f'figures/{name}.png' for name in [
        'figure1_eligibility_map', 'figure2_rescue_profile', 'figure3_post_evidence_profile',
        'figure4_native_selectivity', 'figure5_task_map']]
    for path in required:
        assert (ROOT / path).stat().st_size > 0, path
    resources = accounting()
    validate_resources(resources)
    save(ROOT / 'audit/resource_accounting.json', resources)
    save(ROOT / 'audit/final_validation.json', dict(
        at=now(), status='PASS', hash_entries_verified=hash_entries,
        main_calls=len(tasks), D1_calls=len(d1), technical_missing=missing,
        no_active_stage_GPUs=True, scope_and_budget_verified=True,
        same_agent_reviews=True, independent_reliability_claimed=False))
    paths = sorted(p for p in ROOT.rglob('*') if p.is_file())
    paths += sorted(Path('scripts/stage14c').glob('*.py'))
    save(ROOT / 'audit/artifact_catalog.json', dict(
        at=now(), files={str(p): sha(p) for p in paths},
        note='Closure snapshot; catalog excludes itself and later scheduler receipts.'))
    print('Stage14C final validation PASS; artifact catalog sealed.')


if __name__ == '__main__':
    main()
