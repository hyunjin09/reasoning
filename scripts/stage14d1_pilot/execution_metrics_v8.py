"""Descriptive execution accounting after the immutable scientific freeze."""
from collections import Counter
from pathlib import Path
import numpy as np
from scripts.stage14d1_pilot.common import P, load, save, sha, now
from scripts.stage14d1.contracts import ARMS


def describe(values):
    a = np.asarray(values, dtype=float)
    if not len(a):
        return dict(n=0, total=0, median=None, iqr=None, maximum=None)
    return dict(n=len(a), total=float(a.sum()), median=float(np.median(a)),
                iqr=np.quantile(a, [.25, .75]).tolist(), maximum=float(a.max()))


def summarize(paths):
    unique = sorted(set(paths))
    generations = [load(p) for p in unique]
    inputs = [load(Path(p).parent/'input.json') for p in unique]
    return dict(physical_calls=len(unique),
        output_tokens=describe([g['tokens'] for g in generations]),
        prompt_tokens=describe([g['prompt_tokens'] for g in generations]),
        visual_tokens=describe([g['visual_tokens'] for g in generations]),
        request_latency_seconds=describe([g['latency_seconds'] for g in generations]),
        image_preprocessing_seconds=describe([r['preprocessing_seconds'] for r in inputs]),
        images_per_request=dict(Counter(len(r['images']) for r in inputs)),
        finish_reasons=dict(Counter(g['finish_reason'] for g in generations)),
        stop_reasons=dict(Counter(str(g['stop_reason']) for g in generations)),
        cap_hits=sum(g['cap_hit'] for g in generations),
        paths={p: sha(p) for p in unique})


def main():
    freeze = load(P/'audit/scientific_generation_freeze_v8.json')
    assert freeze['families'] == 72 and freeze['logical_slots'] == 432
    scored = load(P/'analysis/scored_logical_rows_v8.json')['rows']
    assert len(scored) == 432
    design = load(P/'manifests/resumption_v8_design.json')
    states = [load(p) for p in design['source_states'].values()]
    helpers = {'query': [], 'locate': [], **{a: [] for a in ARMS[1:]}}
    for state in states:
        helpers['query'].append(state['query_generation'])
        if state['locator_generation']:
            helpers['locate'].append(state['locator_generation'])
        for arm, read in state['readouts'].items():
            if read.get('generation_path'):
                helpers[arm].append(read['generation_path'])
    solver_paths = [r['generation_path'] for r in scored]
    assert len(set(solver_paths)) == 345
    by_arm = {}
    for arm in ARMS:
        rs = [r for r in scored if r['arm'] == arm]
        assert len(rs) == 72
        by_arm[arm] = dict(assigned=72, receipt_slots=72,
            physical_alias_slots=sum(r['logical_alias'] for r in rs),
            alias_to_native=sum(r['logical_alias'] and r['physical_id'].endswith('_N') for r in rs),
            helper_alias_slots=sum(r['read_alias'] is not None for r in rs),
            solver=summarize([r['generation_path'] for r in rs]))
    save(P/'analysis/execution_metrics_v8.json', dict(at=now(),
        all_solver=summarize(solver_paths),
        all_helpers=summarize([p for ps in helpers.values() for p in ps]),
        helpers_by_role={role: summarize(ps) for role, ps in helpers.items()},
        arms=by_arm,
        query_status=dict(Counter(s['query']['status'] for s in states)),
        query_valid=sum(s['query_valid'] for s in states),
        locator_attempts=sum(bool(s['locator_generation']) for s in states),
        address_valid=sum(s['address_valid'] for s in states),
        local_view_families=sum(len(s['views']['paths']) > 1 for s in states),
        archived_completed_scientific_paths=design['archived_partial_family_outputs'],
        interpretation=[
            'Per-arm logical costs reuse identical receipts; do not add arm totals as actual physical work.',
            'Helper role costs also overlap when readouts are aliased. Unique totals deduplicate exact paths.',
            'Request latency includes overlapping scheduler residence and is not additive GPU billing.',
            'Image preprocessing is measured CPU wall time, not separately measured GPU visual-encoder time.',
            'These totals cover primary solver and reused scientific helper receipts, not all failed/technical requests.',
            'The Slurm allocation ledger is authoritative for cumulative GPU charges, including failed attempts.'
        ]))
    print('Execution metrics: 432 logical / 345 physical solver receipts.')


if __name__ == '__main__':
    main()
