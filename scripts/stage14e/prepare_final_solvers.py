"""Freeze four disjoint full-cap solver queues from the completed acquisition ledger."""
from pathlib import Path
from scripts.stage14e.common import P, load, save, sha, now
from scripts.stage14e.accounting import refresh
from scripts.stage14e.split_execution import frozen_plan


def main():
    acquisition = P / 'raw/evaluation_acquisition_a6000_v2'
    result = load(acquisition / 'result.json')
    assert result['status'] == 'ACQUISITION_COMPLETED'
    frozen = load(P / 'audit/evaluation_acquisition_freeze_v1.json')
    for path, digest in frozen['files'].items():
        assert sha(path) == digest, path
    selection = load(P / 'manifests/evaluation_family_selection_v1.json')['rows']
    ids = [r['item_id'] for r in selection]
    assert len(ids) == len(set(ids)) == 32
    states = load(acquisition / 'acquisition_states.json')
    original = load(acquisition / 'solver_execution_manifest.json')['rows']
    counts = {i: len(frozen_plan(i, states[i], original)[0]) for i in ids}
    assert sum(counts.values()) == result['physical_solvers_planned']
    ledger = refresh()
    reservation = 4 * 3600
    assert ledger['new_actual_gpu_seconds'] + ledger['new_reserved_gpu_seconds'] + 4 * reservation <= 86400
    paths, roots = [], []
    for rank in range(4):
        ident = f'evaluation_solver_r{rank}_v1'
        path = P / 'manifests' / (ident + '.json')
        selected = ids[rank::4]
        save(path, dict(id=ident, mode='final_frozen_solver', families=selected,
            families_path=str(P / 'inference/evaluation_families.jsonl'),
            acquisition_root=str(acquisition), candidate='R', runtime=str(P / 'protocol/runtime_v1.json'),
            gpus=1, gpu_type='a6000', wall_seconds=172800, budget_reservation_seconds=reservation,
            budget_grant_path=str(P / 'audit/budget_grants' / (ident + '.json')),
            worker='continuation_worker', seal=str(P / 'audit/final_solver_seal_v1.json'),
            expected_gpu_hours=[0.75, 2.5], physical_solver_count=sum(counts[i] for i in selected),
            hard_total_cycle_gpu_seconds=86400, selection_rule='roundrobin frozen hash order'))
        paths.append(str(path)); roots.append(str(P / 'raw' / ident))
    seal = dict(load(P / 'audit/final_acquisition_seal_v2.json')['files'])
    seal.update(frozen['files'])
    for path in paths + [str(P / 'protocol/runtime_v1.json'), __file__]:
        seal[str(path)] = sha(path)
    save(P / 'audit/final_solver_seal_v1.json', dict(at=now(), files=seal))
    save(P / 'manifests/final_execution_registry_v1.json', dict(at=now(), solver_roots=roots,
         solver_manifests=paths, acquisition_root=str(acquisition), families=ids,
         physical_count=sum(counts.values()), logical_count=96, technical64_calls=16,
         frozen_acquisition_sha256=sha(P / 'audit/evaluation_acquisition_freeze_v1.json')))
    save(P / 'audit/final_solver_resource_estimate_v1.json', dict(at=now(),
         physical_solvers=sum(counts.values()), logical_solvers=96, shards=4,
         historical_solver_mean_tokens=5198520/345, planning_total_gpu_hours=[3,10],
         basis='Historical mean15068tokens, conservative40–100tokens/s plus startup; long tails unknown. No final outcomes used.',
         exclusive_reservation_gpu_hours=16, actual_gpu_hours_before_launch=ledger['new_actual_gpu_seconds']/3600,
         available_after_reservations_seconds=86400-ledger['new_actual_gpu_seconds']-ledger['new_reserved_gpu_seconds']-4*reservation,
         note='Reservations may be transferred from completed jobs with versioned grants; never exceed24actual GPUh. Full81920caps unchanged.'))
    print(paths)


if __name__ == '__main__':
    main()
