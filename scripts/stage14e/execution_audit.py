"""Final receipt verification and physical-cost accounting; no model execution."""
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scripts.stage14e.common import P, load, rows, save, sha, now
from scripts.stage14e.accounting_retry import refresh as refresh_with_retry
from scripts.stage14e.accounting import TERMINAL


def describe(values):
    return dict(n=len(values), sum=float(sum(values)),
        median=float(np.median(values)) if values else None,
        quartiles=np.quantile(values, [.25, .75]).tolist() if values else None,
        max=max(values) if values else None)


def main():
    ledger = refresh_with_retry()
    assert all(j['state'] in TERMINAL for j in ledger['new_jobs']), 'Wait for every allocation to release'
    assert ledger['new_actual_gpu_seconds'] <= 86400 and ledger['new_reserved_gpu_seconds'] == 0
    registry = load(P / 'manifests/final_execution_registry_v1.json')
    family = {r['item_id']: r for r in rows(P / 'inference/evaluation_families.jsonl')}
    source = load(P / 'annotations/evaluation_source_review_v1.json')
    prefix_check = P / 'audit/native_prefix_token_equivalence_v1.json'
    assert load(prefix_check)['all_exact']
    scored = load(P / 'analysis/final_scored_rows_v1.json')['records']
    assert len(scored) == 96
    scientific_paths = {r['generation_path'] for r in scored}
    assert len(scientific_paths) == 77
    acquisition_root = Path(registry['acquisition_root'])
    states = load(acquisition_root / 'acquisition_states.json')
    assert set(states) == set(family)
    helper_calls = 0
    for i, state in states.items():
        if 'M' in state['read_plan']:
            assert state['read_plan']['M']['prompt'] == state['read_plan']['M_noimage']['prompt']
        for arm, plan in state['read_plan'].items():
            inp = load(Path(plan['generation_path']).with_name('input.json'))
            assert inp['images'] == ([] if arm == 'M_noimage' else [family[i]['image']])
            assert inp['cap'] == 2048 and not inp['diagnostic_oracle_target']
            helper_calls += 1
    assert helper_calls == 62
    gates = []
    for root in registry['solver_roots']:
        root = Path(root)
        assert load(root / 'result.json')['status'] == 'COMPLETED'
        checks = load(root / 'technical_gate.json')
        assert len(checks) == 2 and all(c['same_tokens'] and c['same_input'] for c in checks)
        gates.append(dict(path=str(root / 'technical_gate.json'), sha256=sha(root / 'technical_gate.json'), checks=checks))
    for logical in scored:
        p = Path(logical['generation_path']); inp = load(p.with_name('input.json')); g = load(p)
        r = family[logical['item_id']]
        assert inp['prefix_sha256'] == r['prefix_sha256'] and inp['seed'] == r['seed'] == g['seed']
        assert inp['images'] == [r['image']] and inp['pixels'] == r['original_image_pixels']
        assert inp['sizes'] == r['original_image_sizes'] and inp['cap'] == 81920
        assert not inp['diagnostic_oracle_target']
        assert inp['sampling'] == dict(temperature=1.0, top_p=.95, top_k=20, repetition_penalty=1.0, presence_penalty=0)
    groups, physical = defaultdict(list), []
    for path in sorted((P / 'raw').glob('*/*/generation.json')):
        g = load(path); inp = load(path.with_name('input.json')); receipt = load(path.with_name('result.json'))
        assert receipt['generation_sha256'] == sha(path) and receipt['input_sha256'] == sha(path.with_name('input.json'))
        assert g['tokens'] == len(g['generated_token_ids'])
        stage = path.parents[1].name
        kind = 'technical64' if inp['cap'] == 64 else inp['kind']
        row = dict(path=str(path), sha256=sha(path), attempt=stage, kind=kind,
            request_name=inp['id'].split('_', 1)[1],
            condition=inp['condition'], tokens=g['tokens'], latency_seconds=g['latency_seconds'],
            preprocessing_seconds=inp['preprocessing_seconds'], images_processed=len(inp['images']),
            image_pixels=sum(w*h for w, h in inp['sizes']), visual_tokens=g['visual_tokens'],
            prompt_tokens=g['prompt_tokens'], cap_hit=g['cap_hit'], finish_reason=g['finish_reason'], job=g['job'])
        physical.append(row); groups[stage].append(row)
    summary = {}
    for stage, rs in groups.items():
        environment_path = P / 'raw' / stage / 'environment.json'
        environment = load(environment_path)
        summary[stage] = dict(physical_calls=len(rs), kinds=dict(Counter(r['kind'] for r in rs)),
            environment_path=str(environment_path), environment_sha256=sha(environment_path),
            gpu=environment['gpu'], node=environment['node'], versions=environment['versions'],
            engine_ready_seconds=environment['ready_seconds'], usable_token_capacity=environment['usable_token_capacity'],
            generated_tokens=describe([r['tokens'] for r in rs]),
            request_latency_seconds=describe([r['latency_seconds'] for r in rs]),
            preprocessing_seconds=describe([r['preprocessing_seconds'] for r in rs]),
            images_processed=sum(r['images_processed'] for r in rs),
            image_pixels=sum(r['image_pixels'] for r in rs),
            finish_reasons=dict(Counter(r['finish_reason'] for r in rs)))
    per_arm = {}
    for arm in ['N', 'S', 'M']:
        rs = [r for r in scored if r['arm'] == arm]
        gs = [load(r['generation_path']) for r in rs]
        per_arm[arm] = dict(assigned=len(rs), execution_status=dict(Counter(r['status'] for r in rs)),
            logical_generated_tokens=describe([g['tokens'] for g in gs]),
            logical_latency_seconds=describe([g['latency_seconds'] for g in gs]),
            cap_hits=sum(g['cap_hit'] for g in gs),
            committed_finals=sum('</think>' in g['raw_decoded_response'] for g in gs))
    helpers = {}
    for component in ['S_query', 'M_query', 'S_read', 'M_read', 'M_noimage_read']:
        rs = [r for r in physical if r['attempt'] == acquisition_root.name and r['request_name'] == component]
        helpers[component] = dict(physical_calls=len(rs), generated_tokens=describe([r['tokens'] for r in rs]),
            request_latency_seconds=describe([r['latency_seconds'] for r in rs]),
            preprocessing_seconds=describe([r['preprocessing_seconds'] for r in rs]),
            images_processed=sum(r['images_processed'] for r in rs),
            image_pixels=sum(r['image_pixels'] for r in rs))
    assert [helpers[k]['physical_calls'] for k in helpers] == [32, 32, 28, 17, 17]
    seals = {}
    for name in ['final_solver_seal_v1.json', 'final_acquisition_seal_v2.json', 'evaluation_acquisition_freeze_v1.json']:
        p = P / 'audit' / name; seal = load(p)
        for file, digest in seal['files'].items():
            assert sha(file) == digest, file
        seals[name] = dict(files=len(seal['files']), sha256=sha(p))
    save(P / 'audit/final_execution_verification_v1.json', dict(at=now(), families=32,
        logical_solver_rows=96, physical_solver_generations=77, alias_assignments=19,
        helper_review_rows=len(source['records']), native_repeat_gates=gates,
        native_prefix_equivalence_sha256=sha(prefix_check),
        seals=seals, raw_receipts_verified=len(physical), all_final_inputs_verified=True,
        no_new_generation=True, all_cycle_allocations_terminal=True))
    save(P / 'analysis/execution_efficiency_v1.json', dict(at=now(), attempts=summary,
        final_logical_arms=per_arm, final_helper_components=helpers, physical_records=physical,
        limitations='Request latencies overlap under helper batching and are not GPU allocation charges. '
            'Logical arm tokens/latencies repeat shared native aliases and must not be summed as physical cost. '
            'Preprocessing measurements include caching/reuse effects; pixels count processed representations, not unique source images.'))
    save(P / 'audit/resource_accounting_final_v1.json', dict(at=now(), **{k:v for k,v in ledger.items() if k!='at'},
        new_actual_gpu_hours=ledger['new_actual_gpu_seconds']/3600,
        historical_plus_new_gpu_hours=ledger['historical_sava_gpu_hours']+ledger['new_actual_gpu_seconds']/3600,
        budget_remaining_gpu_hours=24-ledger['new_actual_gpu_seconds']/3600,
        latency_not_used_as_billing=True))
    print('Verified32families/96logical/77physical; actualnewGPUh', ledger['new_actual_gpu_seconds']/3600)


if __name__ == '__main__':
    main()
