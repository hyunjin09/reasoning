"""Merge immutable family-coherent executions; never choose by answer outcome."""
from pathlib import Path
from scripts.stage14d1_pilot.common import P, load, rows, sha
from scripts.stage14d1_pilot.execution import continuation_plan
from scripts.stage14d1_pilot.resume_v7 import completed_receipt


def merge_physical(design, new_results):
    attempts = design['attempts']
    if len(attempts) != len(set(attempts)) or set(attempts) != set(new_results):
        raise ValueError('Attempt coverage mismatch')
    count = design['physical_new']
    if type(count) is not int or count < 0 or sum(len(r) for r in new_results.values()) != count:
        raise ValueError('New physical request count mismatch')
    merged = dict(design['completed_reuse'])
    for attempt in attempts:
        if merged.keys() & new_results[attempt].keys():
            raise ValueError('Duplicate physical request')
        merged.update(new_results[attempt])
    if set(merged.values()) & set(design['archived_partial_family_outputs'].values()):
        raise ValueError('Archived partial-family receipt entered primary analysis')
    return merged


def verified_states():
    design_path = P/'manifests/resumption_v8_design.json'
    design = load(design_path)
    files = {str(design_path): sha(design_path)}
    new_results = {}
    for attempt in design['attempts']:
        root = P/'raw'/attempt
        assert load(root/'exit.json')['status'] == 'COMPLETE', attempt
        assert load(root/'technical_gate.json')['passed'], attempt
        new_results[attempt] = load(root/'resolved_requests.json')['paths']
        for name in ['exit.json','technical_gate.json','resolved_requests.json']:
            files[str(root/name)] = sha(root/name)
    merged = merge_physical(design,new_results)
    originals = {r['item_id']:r for r in rows(P/'inference/families.jsonl')}
    assert set(originals) == set(design['source_states']) and len(originals)==72
    cfg = load(P/'protocol/runtime_v6.json')
    states = {}
    expected_ids = set()
    for item, source in design['source_states'].items():
        s = load(source)
        files[source] = sha(source)
        physical, logical = continuation_plan(item, {a:r['value'] for a,r in s['readouts'].items()})
        assert logical == s['logical_continuations']
        expected_ids.update(physical)
        block = design['schedule_blocks'][s['family_id']]
        family_attempts=set()
        for rid, suffix in physical.items():
            p = Path(merged[rid])
            assert completed_receipt(p.parent, originals[item], suffix)==str(p)
            inp = load(p.parent/'input.json')
            assert inp['sampling'] == cfg['helper_recipe']
            family_attempts.add(p.parent.parent.name)
            for path in [p,p.parent/'input.json',p.parent/'result.json']:
                files[str(path)] = sha(path)
        assert len(family_attempts)==1, 'Within-family scheduling mixture'
        attempt=family_attempts.pop()
        assert (block=='original_v6' and attempt=='main_v6_rank0') or (block=='recovered_v8' and attempt in design['attempts'])
        s['continuation_paths']={a:merged[rid] for a,rid in logical.items()}
        s['execution_block']=block
        s['execution_attempt']=attempt
        states[s['family_id']]=s
    assert expected_ids==set(merged) and len(merged)==345
    assert len(states)==72 and sum(len(s['continuation_paths']) for s in states.values())==432
    return states,files
