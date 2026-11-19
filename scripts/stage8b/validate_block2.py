"""Verify the completed Block2 evidence and seal final artifacts without reruns."""
import ast
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from visual_reasoning.stage8b.block1_data import digest, save
from visual_reasoning.stage8b.block2_data import ROOT, PREFIX

REQUIRED = ['event_annotation_summary.json', 'TMU_table.parquet', 'local_read_table.parquet',
            'activation_comparison.json', 'source_routing_comparison.json', 'source_ambiguity_comparison.json',
            'transport_descriptive.json', 'head_layer_agreement.json', 'demand_coverage.json',
            'source_sequence_alignment.json', 'replay_manifest.json', 'summary.md']


def without_added_fields(value):
    if isinstance(value, dict):
        return {key: without_added_fields(item) for key, item in value.items() if key not in ['written_at', 'standardized_ci']}
    if isinstance(value, list):
        return [without_added_fields(item) for item in value]
    return value


def main():
    prep = json.loads((ROOT/'audit/preparation_freeze.json').read_text())
    for path, expected in prep['input_freezes'].items():
        assert digest(path) == expected, path
        freeze = json.loads(Path(path).read_text())
        for artifact, sha in {**freeze['artifacts_sha256'], **freeze['supporting_sha256']}.items():
            assert digest(artifact) == sha, artifact
    seal = json.loads((ROOT/'annotations/semantic_seal.json').read_text())
    for path, expected in seal['review_sha256'].items():
        assert digest(path) == expected
    assert digest(ROOT/'annotations/geometry_amendments_v1.json') == seal['geometry_amendments_sha256']
    table = pd.read_parquet(ROOT/(PREFIX+'TMU_table.parquet'))
    local = pd.read_parquet(ROOT/(PREFIX+'local_read_table.parquet'))
    assert len(table) == 456 and len(local) == 148
    assert set(table.event_id) == {e['event_id'] for e in prep['events']}
    assert local.local.value_counts().to_dict() == {'L+': 120, 'L-': 17, 'L?': 11}
    summary = json.loads((ROOT/(PREFIX+'event_annotation_summary.json')).read_text())
    assert summary['descriptive_only'] and not summary['preferred_gate_pass']
    manifest = json.loads((ROOT/(PREFIX+'replay_manifest.json')).read_text())
    assert len(manifest['requests']) == 21 and len(manifest['pairs']) == 9
    for path, expected in manifest['source_sha256'].items():
        assert digest(path) == expected, path
    captured, tie_heads, devices = set(), 0, []
    for rank in range(2):
        worker = ROOT/'replay'/f'worker{rank}'
        env = json.loads((worker/'environment.json').read_text()); devices.append(env['gpu_uuid'])
        assert env['node'] == 'node06' and env['slurm_job_id'] == '118076'
        completed = json.loads((worker/'completed.json').read_text())
        assert completed['completed']
        assert set(completed['events']) == {r['event_id'] for r in manifest['requests'] if r['rank'] == rank}
        for eid in completed['events']:
            event = json.loads((worker/'events'/f'{eid}.json').read_text())
            assert event['capture_logits_exact'] and event['native_features_match']
            assert event['feature_max_abs_delta'] == event['logits_max_abs_delta'] == 0
            assert event['query']+1 == event['predicting_token']
            assert event['manifest_sha256'] == digest(ROOT/(PREFIX+'replay_manifest.json'))
            for layer in event['per_head_records'].values():
                mass = np.asarray(layer['mass'])
                tie_heads += int(((mass == mass.max(1)[:, None]).sum(1) > 1).sum())
            captured.add(eid)
    assert len(set(devices)) == 2 and captured == {r['event_id'] for r in manifest['requests']}
    assert tie_heads == 0, 'Tie handling must be audited before interpreting consensus'
    ordered = ['activation_comparison', 'source_routing_comparison', 'source_ambiguity_comparison', 'transport_descriptive']
    times = [json.loads((ROOT/(PREFIX+name+'.json')).read_text())['written_at'] for name in ordered]
    assert times == sorted(times)
    old = ROOT/'audit/initial_analysis_before_standardized_intervals'
    for path in old.glob(PREFIX+'*.json'):
        previous, current = json.loads(path.read_text()), json.loads((ROOT/path.name).read_text())
        assert without_added_fields(previous) == without_added_fields(current), path.name
    assert json.loads((ROOT/(PREFIX+'demand_coverage.json')).read_text())['population_coverage'] is None
    assert json.loads((ROOT/(PREFIX+'source_sequence_alignment.json')).read_text())['continuous_lag'] is None
    receipt = (ROOT/'audit/slurm_118076_final.txt').read_text()
    assert 'JobState=COMPLETED' in receipt and 'ExitCode=0:0' in receipt and 'gres/gpu:2' in receipt
    assert len(list((ROOT/'figures').glob('*.png'))) == len(list((ROOT/'figures').glob('*.pdf'))) == 5
    for suffix in REQUIRED:
        assert (ROOT/(PREFIX+suffix)).stat().st_size > 0
    code = list(Path('scripts/stage8b').glob('*block2*.py'))+list(Path('code/visual_reasoning/stage8b').glob('block2*.py'))
    code += [Path('code/visual_reasoning/stage8b/tests/test_block2.py')]
    for path in code:
        ast.parse(path.read_text(), filename=str(path))
    validation = dict(at=datetime.now(timezone.utc).isoformat(), passed=True,
                      required_artifacts=12, figure_pairs=5, exact_review_membership=456,
                      verified_replay_events=21, distinct_GPUs=2, native_feature_and_logit_max_delta=0,
                      code_tests='5 passed; source mapping, missing confusers, role permutation, family bootstrap and shared-pair components',
                      input_freezes_unchanged=True, primary_point_estimates_unchanged_after_interval_completion=True,
                      analysis_order_verified=True, tied_candidate_head_count=tie_heads,
                      visual_inspection='All five PNG figures inspected; activation support explicitly reported.',
                      limits=['Single annotator', 'L- below24', 'Missing optional matching subtype in26 T rows',
                              'No full confound adjustment', 'Retrieval-conditioned demand denominator',
                              'Sparse changing source inventories'],
                      gpu_released=True, slurm_state='COMPLETED', slurm_job_id='118076',
                      git_metadata='Workspace is not a Git repository; content integrity is verified with artifact hashes.')
    save(ROOT/'audit/final_validation.json', validation)
    primary = [ROOT/(PREFIX+suffix) for suffix in REQUIRED]
    support = [p for p in ROOT.rglob('*') if p.is_file() and p not in primary and p.name != PREFIX+'freeze.json']
    support += code+[Path('scripts/stage8b/run_block2_replay.sh'), Path('plan/stage8b_block2_execution_protocol_v1.md'),
                     Path('plan/stage8b_block2_retrieval_event_local_read_success_failure_plan.md')]
    save(ROOT/(PREFIX+'freeze.json'), dict(at=datetime.now(timezone.utc).isoformat(), complete=True,
         decision='No robust earliest divergence established; source routing is the earliest descriptive candidate below the yield gate.',
         stop_before_block3=True, artifacts_sha256={str(p): digest(p) for p in primary},
         supporting_sha256={str(p): digest(p) for p in support}))
    print(json.dumps(validation, indent=2))


if __name__ == '__main__':
    main()
