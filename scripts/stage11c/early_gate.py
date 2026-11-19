"""Completion gate only: never score partial native cohorts as complete studies."""
from scripts.stage11c.common import ROOT, ARMS, load, save, sha, now
from scripts.stage11c.protocol import completion_gate


def main():
    path = ROOT/'native_early_tasks.json'
    manifest = load(path)
    assert manifest['frozen'] and manifest['n_calls'] == 32
    records, caps, missing = [], {arm: [] for arm in ARMS}, []
    tasks = sorted([r for s in manifest['shards'] for r in s['rows']], key=lambda r: (r['arm'], r['primary_order']))
    for task in tasks:
        dest = ROOT/'native_early/results'/task['task_id']/'result.json'
        if not dest.exists():
            missing.append(task['task_id'])
            caps[task['arm']].append(None)
            continue
        r = load(dest)
        assert r['manifest_sha256'] == sha(path) and r['batch_size'] == 1
        assert r['generation_sha256'] == sha(dest.parent/'generation.json')
        assert r['input_sha256'] == sha(dest.parent/'input.json')
        assert r['cap'] == manifest['common_cap']
        caps[task['arm']].append(None if r['budget_interrupted'] else r['at_length_cap'])
        if r['budget_interrupted']:
            missing.append(task['task_id'])
        records.append(r)
    gate = completion_gate(caps['thinking'], caps['instruct_direct'])
    if gate == 'INCOMPLETE':
        print('INCOMPLETE', missing)
        return
    save(ROOT/'audit/early_native_completion_gate.json', dict(at=now(), frozen=True, status=gate,
        n_families=16, n_calls=32, common_cap=manifest['common_cap'],
        cap_hits={arm: sum(caps[arm]) for arm in ARMS}, cap_rates={arm: sum(caps[arm])/16 for arm in ARMS},
        structural_failures={arm: sum(not r['structural_complete'] for r in records if r['arm']==arm) for arm in ARMS},
        native_manifest_sha256=sha(path), rows=records, model_accuracy_not_used=True,
        next_action='STOP_BEFORE_ORACLE' if gate=='STOP' else 'COMPLETE_FROZEN_NATIVE_COHORT'))
    print('EARLY_COMPLETION_GATE', gate, {arm: sum(caps[arm]) for arm in ARMS})


if __name__ == '__main__':
    main()
