"""Verify the actual stop boundary, preserved inputs and required Stage12C artifacts."""
import re
from pathlib import Path
import pandas as pd
from scripts.stage12c.common import ROOT, load, save, sha, now
from scripts.stage12c.review import checked_generation
from scripts.stage12c.seal import preservation


def main():
    decision = load(ROOT/'stage12c_rescue_decision.json')
    resources = load(ROOT/'stage12c_resource_accounting.json')
    assert resources['final'] and resources['all_stage_allocations_released']
    assert resources['allocated_gpu_hours'] <= 8
    assert decision['recommendation'] and not decision['recommendation_executed']
    preserved = preservation()
    plan = Path('plan/stage12c_selective_rescue_cot_thinking_plan.md').read_text()
    names = re.findall(r'^\d+\. `(stage12c_[^`]+)`', plan, re.MULTILINE)
    assert len(names) == 17 and len(set(names)) == 17
    hashes = {str(ROOT/name): sha(ROOT/name) for name in names}
    full = load(ROOT/'stage12c_frozen_bottleneck_manifest.json')
    assert len(full['rows']) == 61 and len(full['tasks']) == 122
    assert len(set(full['sanity_ids'])) == 12
    assert set(full['sanity_ids']).isdisjoint(full['remaining_ids'])
    receipts = list((ROOT/'generations').glob('*/result.json'))
    if decision['decision'] == 'TECHNICAL_STOP':
        sanity = load(ROOT/'stage12c_technical_sanity.json')
        assert not sanity['pass'] and len(receipts) == 24
        assert not (ROOT/'audit/correctness_opened.json').exists()
        assert not (ROOT/'audit/remaining_launch.json').exists()
        expected = [t for t in full['tasks'] if t['item_id'] in full['sanity_ids']]
        for name in ['cot_scoring_blind', 'thinking_scoring_blind', 'rescue_transitions',
                     'trace_evidence_states', 'pathology_transitions']:
            assert pd.read_parquet(ROOT/f'stage12c_{name}.parquet').empty
        inference = load(ROOT/'stage12c_primary_inference.json')
        assert inference['status'] == 'NOT_RUN_TECHNICAL_STOP'
        assert all(v is None for v in inference['primary'].values())
        n_per_arm = 12
    else:
        assert decision['decision'] in ['RESCUE_INFORMATIVE', 'RESCUE_SPARSE']
        assert load(ROOT/'audit/denominator_seal.json')['pass']
        assert len(receipts) == 122
        expected = full['tasks']
        assert len(pd.read_parquet(ROOT/'stage12c_rescue_transitions.parquet')) == 61
        assert len(pd.read_parquet(ROOT/'stage12c_trace_evidence_states.parquet')) == 52
        n_per_arm = 61
    assert {p.parent.name for p in receipts} == {t['task_id'] for t in expected}
    for t in expected:
        generation, checks = checked_generation(t)
        assert all(checks.values()), (t['task_id'], checks)
        annotation = load(ROOT/'audit/technical_annotations'/f"{t['task_id']}.json")
        assert annotation['generation_sha256'] == sha(ROOT/'generations'/t['task_id']/'generation.json')
    for arm in ['cot', 'thinking']:
        assert len(pd.read_parquet(ROOT/f'stage12c_{arm}_results.parquet')) == n_per_arm
    save(ROOT/'audit/final_verification.json', dict(at=now(), decision=decision['decision'],
        preserved=preserved, required_artifact_hashes=hashes, checked_generations=len(expected),
        new_gpu_hours=resources['allocated_gpu_hours'], all_allocations_released=True,
        recommendation_executed=False))
    print('Verified:', decision['decision'], len(hashes), 'artifacts;', len(expected), 'generations.')


if __name__ == '__main__':
    main()
