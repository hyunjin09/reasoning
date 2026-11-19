from copy import deepcopy
import json

import numpy as np

import pytest

from scripts.stage7a_bench import compile_causal_v2 as module
from scripts.stage7a_bench.compile_causal_v2 import validate_completion, validate_event_identity, validate_distributions


def completion():
    expected = dict(pilot=dict(path='pilot', sha256='p'), dependencies={'code': 'c'}, runtime_sha256='r')
    signature = dict(execution_signature=deepcopy(expected), mechanics=False,
                     event_ids=['e1', 'e2'], passive_features_collected=False)
    summary = dict(completed=True, mechanics=False, seconds=10., passive_features_collected=False,
                   events=[{'event': {'path': 'e1'}, 'distributions': {'path': 'e1.npz'}},
                           {'event': {'path': 'e2'}, 'distributions': {'path': 'e2.npz'}}])
    wrapper = dict(completed=True, exit_code=0, slurm_job_id='job')
    env = dict(parameter_dtype='torch.bfloat16', slurm_job_id='job', node='node06.cluster')
    runtime = dict(slurm_allocation='job', node='node06')
    return signature, summary, wrapper, env, expected, runtime, ['e1', 'e2']


def test_completed_science_run_has_exact_frozen_order_and_runtime():
    validate_completion(*completion(), mechanics=False)


@pytest.mark.parametrize('change', ['incomplete', 'failed_wrapper', 'missing_wrapper',
    'wrong_allocation', 'wrong_node', 'fp32', 'mechanics_run', 'native_controls',
    'swapped_order', 'missing_event', 'extra_event', 'dependencies', 'passive',
    'summary_passive', 'negative_time', 'nan_time', 'no_event_receipts'])
def test_incomplete_or_mismatched_run_is_not_interpretable(change):
    args = list(completion()); sig, summary, wrapper, env = args[:4]
    if change == 'incomplete': summary['completed'] = False
    if change == 'failed_wrapper': wrapper['exit_code'] = 1
    if change == 'missing_wrapper': wrapper.pop('completed')
    if change == 'wrong_allocation': wrapper['slurm_job_id'] = 'other'
    if change == 'wrong_node': env['node'] = 'node03'
    if change == 'fp32': env['parameter_dtype'] = 'torch.float32'
    if change == 'mechanics_run': sig['mechanics'] = True
    if change == 'native_controls': sig['mode'] = 'native_controls'
    if change == 'swapped_order': sig['event_ids'].reverse()
    if change == 'missing_event': sig['event_ids'].pop()
    if change == 'extra_event': sig['event_ids'].append('e3')
    if change == 'dependencies': sig['execution_signature']['dependencies']['code'] = 'changed'
    if change == 'passive': sig['passive_features_collected'] = True
    if change == 'summary_passive': summary['passive_features_collected'] = True
    if change == 'negative_time': summary['seconds'] = -1
    if change == 'nan_time': summary['seconds'] = float('nan')
    if change == 'no_event_receipts': summary['events'].pop()
    with pytest.raises(ValueError): validate_completion(*args, mechanics=False)


def event():
    entry = dict(id='e', event_id='base__image', base_id='base', benchmark='charxiv',
                 condition='image_present', analysis_family_id='family', pilot_stratum='failure')
    result = dict(entry, complete=True, pilot_sha256='p', source_assay_mechanics=False,
                  passive_features_collected=False, seconds=5., checks={k: True for k in
                  ('all_finite', 'native_input_exact', 'local_control_input_geometry_exact',
                   'local_controls_all_finite', 'fixed_prior_inputs_verified', 'fixed_prior_scores_finite')})
    return entry, result


def test_event_identity_preserves_family_condition_and_stratum():
    validate_event_identity(*event(), 'p')


@pytest.mark.parametrize('field', ['id', 'event_id', 'base_id', 'benchmark', 'condition',
    'analysis_family_id', 'pilot_stratum', 'pilot_sha256'])
def test_event_swap_rejected_even_when_score_record_is_complete(field):
    entry, result = event(); result[field] = 'other'
    with pytest.raises(ValueError): validate_event_identity(entry, result, 'p')


@pytest.mark.parametrize('field,value', [('complete', False), ('source_assay_mechanics', True),
    ('passive_features_collected', True), ('seconds', 0), ('seconds', float('inf'))])
def test_event_completion_and_cost_must_be_valid(field, value):
    entry, result = event(); result[field] = value
    with pytest.raises(ValueError): validate_event_identity(entry, result, 'p')


def test_removed_required_check_does_not_become_vacuous_success():
    entry, result = event(); result['checks'].pop('native_input_exact')
    with pytest.raises(ValueError): validate_event_identity(entry, result, 'p')


@pytest.mark.parametrize('change', ['missing', 'extra', 'wrong_shape', 'nan', 'integer', 'short'])
def test_vocabulary_arrays_require_exact_finite_control_coverage(change):
    arrays = dict(N=np.zeros(100), T_sham=np.zeros(100), fixed_mask=np.zeros(100))
    local = ['T_semantic', 'T_sham']; prior = ['fixed_mask']
    validate_distributions(arrays, local, prior)
    if change == 'missing': arrays.pop('fixed_mask')
    if change == 'extra': arrays['unrequested'] = np.zeros(100)
    if change == 'wrong_shape': arrays['fixed_mask'] = np.zeros((1, 100))
    if change == 'nan': arrays['fixed_mask'][0] = np.nan
    if change == 'integer': arrays['N'] = np.zeros(100, dtype=int)
    if change == 'short': arrays = {k: np.zeros(50) for k in arrays}
    with pytest.raises(ValueError): validate_distributions(arrays, local, prior)


@pytest.fixture
def fake_completed_run(tmp_path, monkeypatch):
    """Real temporary JSON/NPZ graph; scientific adapters/certificate are mocked.

    This tests parser provenance and exports, not model mechanics or state rules.
    The invocation fixes pytest's temporary root inside the approved audit root.
    """
    out = tmp_path / 'outputs/stage7a_bench_v2'
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'OUT', out)
    def stage(name, directory):
        path = (tmp_path / name).resolve()
        if not path.is_relative_to(out / directory): raise ValueError('Outside test stage')
        return path
    monkeypatch.setattr(module, 'stage_path', stage)
    def write(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content))
        return dict(path=str(path.relative_to(tmp_path)), sha256=module.sha(path))
    entry, result = event(); entry['native_index'] = 1
    pilot = dict(benchmark='charxiv', selected_entries=[entry])
    pilot_ref = write(out / 'causal_pilot/frozen/charxiv.json', pilot)
    config = dict(runtime=dict(slurm_allocation='job', node='node06'))
    config_ref = write(out / 'config/runtime.json', config)
    expected = dict(pilot=pilot_ref, dependencies={'fixture': 'same'}, runtime_sha256=config_ref['sha256'])
    monkeypatch.setattr(module, 'load_frozen_pilot', lambda *a: deepcopy(pilot))
    monkeypatch.setattr(module, 'dependency_hashes', lambda: {'fixture': 'same'})
    monkeypatch.setattr(module, 'validate_mechanics', lambda *a: entry['id'])
    monkeypatch.setattr(module, 'requested_native_banks', lambda *a: {})
    local = dict(status='UNAVAILABLE', reason='No local controls')
    prior = dict(status='UNAVAILABLE', reason='No prior controls')
    monkeypatch.setattr(module, 'load_reviewed_controls', lambda *a: ({}, local))
    monkeypatch.setattr(module, 'load_prior_controls', lambda *a: ({}, prior))
    monkeypatch.setattr(module, 'compile_benchmark_metrics', lambda *a: dict(id=entry['id'], native_D=0.))
    monkeypatch.setattr(module, 'classify_benchmark', lambda *a, **k: dict(id=entry['id'], state='UNRESOLVED', tier=None))
    write(tmp_path / 'outputs/stage7a/config/discovery_thresholds.json', dict(frozen=True, vsd_floor=.12))
    write(out / 'config/inherited_causal_definition_freeze.json', dict(numeric_thresholds=dict(vsd_floor=.12)))
    result.update(pilot_sha256=pilot_ref['sha256'], controls={}, control_provenance=local,
                  fixed_prior_controls=prior, semantic_controls_available=False)
    for name, mechanics in [('mechanics', True), ('science', False)]:
        run = out / 'causal_pilot/raw' / name
        er = write(run / 'events/e.json', result)
        np.savez_compressed(run / 'events/e.npz', N=np.zeros(100))
        ar = dict(path=str((run / 'events/e.npz').relative_to(tmp_path)), sha256=module.sha(run / 'events/e.npz'))
        refs = dict(event=er, distributions=ar)
        write(run / 'environment.json', dict(parameter_dtype='torch.bfloat16', slurm_job_id='job', node='node06'))
        write(run / 'run_summary.json', dict(completed=True, mechanics=mechanics, seconds=6.,
            passive_features_collected=False, events=[refs]))
        write(out / 'causal_pilot/wrappers' / (name + '.json'), dict(completed=True, exit_code=0, slurm_job_id='job'))
        signature = dict(execution_signature=expected, mechanics=mechanics,
                         event_ids=['e'], passive_features_collected=False)
        if mechanics:
            cert = write(out / 'causal_pilot/mechanics/charxiv.json', dict(artifacts=refs))
        else:
            signature['mechanics_certificate'] = cert
        write(run / 'signature.json', signature)
    return out, write


def test_real_artifact_graph_exports_once_and_keeps_unresolved(fake_completed_run):
    out, _ = fake_completed_run
    summary = module.compile_run('science', None)
    assert summary['events'] == summary['native_bases'] == summary['source_families'] == 1
    labels = out / 'causal_pilot/compiled/charxiv/science/state_labels.jsonl'
    assert json.loads(labels.read_text())['state'] == 'UNRESOLVED'
    before = labels.read_bytes()
    with pytest.raises(FileExistsError): module.compile_run('science', None)
    assert labels.read_bytes() == before


@pytest.mark.parametrize('damage', ['json', 'npz', 'swapped_receipt', 'missing_requested_review',
    'unrequested_review', 'threshold', 'extra_control', 'failed_mechanics_wrapper'])
def test_artifact_damage_cannot_write_partial_scientific_export(fake_completed_run, monkeypatch, damage):
    out, write = fake_completed_run
    run = out / 'causal_pilot/raw/science'
    refs = None
    if damage == 'json':
        (run / 'events/e.json').write_text('{}')
    if damage == 'npz':
        np.savez_compressed(run / 'events/e.npz', N=np.ones(100))
    if damage == 'swapped_receipt':
        summary = module.read_json(run / 'run_summary.json')
        summary['events'][0]['event'] = write(run / 'events/other.json', module.read_json(run / 'events/e.json'))
        write(run / 'run_summary.json', summary)
    if damage == 'missing_requested_review':
        monkeypatch.setattr(module, 'requested_native_banks', lambda *a: {'e': {}})
    if damage == 'unrequested_review': refs = {'e': {}}
    if damage == 'threshold':
        write(out / 'config/inherited_causal_definition_freeze.json', dict(numeric_thresholds=dict(vsd_floor=.5)))
    if damage == 'extra_control':
        result = module.read_json(run / 'events/e.json'); result['controls']['unrequested'] = {}
        er = write(run / 'events/e.json', result)
        summary = module.read_json(run / 'run_summary.json'); summary['events'][0]['event'] = er
        write(run / 'run_summary.json', summary)
    if damage == 'failed_mechanics_wrapper':
        write(out / 'causal_pilot/wrappers/mechanics.json', dict(completed=False, exit_code=1, slurm_job_id='job'))
    with pytest.raises(ValueError): module.compile_run('science', None, refs)
    assert not (out / 'causal_pilot/compiled').exists()
