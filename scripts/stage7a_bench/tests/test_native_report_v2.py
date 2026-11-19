from copy import deepcopy
from pathlib import Path

import pytest

from scripts.stage7a_bench import native_report_v2 as module
from scripts.stage7a.common import sha
from scripts.stage7a_bench.tests.test_completed_screen_v2 import screen


def review(base, *, final=True, local=False, binding=False, label='F1'):
    return dict(base_id=base, event_id=base+'__image', screen_label=label,
        final_correctness=final, local_visual_claim_present=True,
        local_visual_claim_correctness=local, binding_claim_present=True,
        binding_claim_correctness=binding,
        claims=[dict(demand='singleton', locally_correct=local)])


def test_dimensions_keep_local_binding_and_final_errors_separate():
    a = review('a')
    a['claims'].append(dict(demand='singleton', locally_correct=True))
    b = review('b', final=False, local=True, binding=True, label='F0')
    c = review('c', final=None, local=None, binding=None, label=None)
    got = module.dimension_summary([a, b, c])
    assert got['binding_error_among_adjudicated_bindings']['value'] == .5
    assert got['responses_with_correct_singleton']['numerator'] == 2
    assert got['responses_with_correct_singleton']['unknown'] == 1
    assert got['responses_with_wrong_singleton']['numerator'] == 1
    assert got['final_local_contingency'] == {
        'correct / wrong': 1, 'wrong / correct': 1, 'unknown / unknown': 1}


def test_no_binding_or_singleton_is_not_an_adjudicated_binding_error():
    a = review('a', binding=None)
    a['binding_claim_present'] = False
    a['claims'] = []
    got = module.dimension_summary([a])
    assert got['binding_error_among_adjudicated_bindings']['denominator'] == 0
    assert got['responses_with_correct_singleton']['value'] == 0


def test_pair_transitions_use_only_common_bases_and_preserve_unknown():
    a, b, extra = review('a'), review('b', final=None, label=None), review('extra')
    right = [review('a', final=False, label='F2'), deepcopy(b)]
    got = module.paired_transitions([a, b, extra], right)
    assert got['paired_reviewed'] == 2
    assert got['screen_class_transitions'] == {'F1 → F2': 1, 'unknown → unknown': 1}
    assert got['final_correctness_transitions'] == {'correct → wrong': 1, 'unknown → unknown': 1}
    assert got['unpaired_left'] == 1 and got['unpaired_right'] == 0


def test_pair_duplicate_base_is_rejected():
    with pytest.raises(ValueError):
        module.paired_transitions([review('a'), review('a')], [review('a')])


def test_unknown_rate_is_not_printed_as_zero():
    assert module.format_rate(dict(numerator=0, denominator=0, unknown=3, value=None)) == 'Unknown (3 unadjudicated)'
    assert module.format_rate(dict(numerator=1, denominator=2, unknown=1, value=.5)) == '1/2 (50.0%; 1 unadjudicated)'


@pytest.fixture
def export(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'OUT', tmp_path/'outputs/stage7a_bench_v2')
    evidence = module.OUT/'audit/native.json'
    evidence.parent.mkdir(parents=True)
    evidence.write_text('{}')
    report = dict(status='COMPLETED_BENCHMARK_NATIVE_REPORT_ONLY', report_id='charxiv_v1',
        benchmark='charxiv', artifact_sha256={str(evidence.relative_to(tmp_path)): sha(evidence)},
        conditions={}, paired_conditions={}, scope='Native behavior only.',
        causal_states_assigned=False, primary_benchmark_selected=False)
    return report, evidence


def test_export_is_immutable_and_source_bound(export):
    report, _ = export
    dest = module.write_report(report)
    assert (dest/'report.json').exists() and (dest/'summary.md').exists()
    assert 'Native behavior only.' in (dest/'summary.md').read_text()
    with pytest.raises(FileExistsError):
        module.write_report(report)


def test_changed_evidence_prevents_any_export(export):
    report, evidence = export
    evidence.write_text('{"changed":true}')
    with pytest.raises(ValueError, match='changed'):
        module.write_report(report)
    assert not (module.OUT/'native_screen/reports/charxiv_v1').exists()


@pytest.mark.parametrize('name', ['../escape', '', 'A/B', '/absolute'])
def test_unsafe_report_identity_is_rejected(export, name):
    report, _ = export
    report['report_id'] = name
    with pytest.raises(ValueError):
        module.write_report(report)


def test_incomplete_native_screen_cannot_be_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'load_completed_screen', lambda *a: (_ for _ in ()).throw(ValueError('incomplete')))
    with pytest.raises(ValueError, match='incomplete'):
        module.build_report('charxiv', 'charxiv_v1', {'image_present': {}}, {})


def runtime_packet():
    runtime = dict(model_checkpoint='local_4b', locked_generation_protocol=dict(max_new_tokens=40960),
                   runtime=dict(slurm_allocation='job', node='node06'))
    environment = dict(model_checkpoint_resolved='local_4b', parameter_dtype='torch.bfloat16',
        architecture='Qwen3VLForConditionalGeneration', parameter_count=4437815808,
        language_layers=36, attention_heads=32, max_new_tokens=40960, world_size=1,
        slurm_job_id='job', node='node06.cluster', sys_prefix=str(module.ROOT/'.venv'))
    signature = dict(slurm_job_id='job', dependencies={
        'outputs/stage7a_bench_v2/config/runtime.json': 'runtime_sha'})
    mechanics = dict(cap=128, checks=[dict(repeat_token_ids_exact=True, scientific_use=False,
                                         input=dict(condition='image_present'))])
    return environment, signature, mechanics, runtime, 'runtime_sha'


def test_frozen_bf16_model_runtime_is_accepted():
    module.validate_runtime(*runtime_packet())


@pytest.mark.parametrize('change', ['checkpoint', 'fp32', 'layers', 'heads', 'allocation',
                                  'node', 'global_env', 'cap', 'signature', 'empty_checks', 'failed_mechanics'])
def test_runtime_or_mechanics_mismatch_cannot_be_reported(change):
    args = runtime_packet()
    env, sig, mech = args[:3]
    if change == 'checkpoint': env['model_checkpoint_resolved'] = 'other'
    if change == 'fp32': env['parameter_dtype'] = 'torch.float32'
    if change == 'layers': env['language_layers'] = 32
    if change == 'heads': env['attention_heads'] = 16
    if change == 'allocation': env['slurm_job_id'] = 'another'
    if change == 'node': env['node'] = 'node03'
    if change == 'global_env': env['sys_prefix'] = 'global'
    if change == 'cap': mech['cap'] = 2048
    if change == 'signature': sig['dependencies'] = {}
    if change == 'empty_checks': mech['checks'] = []
    if change == 'failed_mechanics': mech['checks'][0]['repeat_token_ids_exact'] = False
    with pytest.raises(ValueError):
        module.validate_runtime(*args)


def test_reread_does_not_replace_previously_verified_evidence_hash(export):
    report, evidence = export
    hashes = deepcopy(report['artifact_sha256'])
    evidence.write_text('{"changed":true}')
    with pytest.raises(ValueError, match='changed during loading'):
        module.remember_hash(hashes, evidence)
    assert hashes == report['artifact_sha256']


def test_report_parent_symlink_cannot_redirect_export(export, tmp_path):
    report, _ = export
    parent = module.OUT/'native_screen'
    parent.mkdir()
    elsewhere = tmp_path/'unrelated'
    elsewhere.mkdir()
    (parent/'reports').symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(ValueError, match='destination'):
        module.write_report(report)
    assert not list(elsewhere.iterdir())


@pytest.fixture
def complete_report_packet(screen, monkeypatch):
    # Tiny real on-disk response/token/review graph; metadata describes the
    # runtime contract but is synthetic. This test does not execute a model.
    bindings, put, get, root = screen
    real_root = Path(module.__file__).resolve().parents[2]
    monkeypatch.setattr(module, 'ROOT', root)
    monkeypatch.setattr(module, 'OUT', root/'outputs/stage7a_bench_v2')
    env, _, mech, runtime, _ = runtime_packet()
    runtime_name = put('outputs/stage7a_bench_v2/config/runtime.json', runtime)
    for condition, binding in bindings.items():
        base = 'outputs/stage7a_bench_v2/native_screen/generations/'+binding['native_run_id']
        sig = get(base+'/signature.json')
        sig.update(slurm_job_id='job', dependencies={runtime_name: sha(root/runtime_name)})
        put(base+'/signature.json', sig)
        put(base+'/environment.json', env)
        checks = deepcopy(mech)
        checks['checks'][0]['input']['condition'] = condition
        put(base+'/mechanics.json', checks)
    for name in ('native_report_v2.py', 'completed_screen_v2.py', 'native_yield_v2.py'):
        dest = root/'scripts/stage7a_bench'/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((real_root/'scripts/stage7a_bench'/name).read_bytes())
    return bindings, put, get, root


def test_complete_disk_graph_builds_and_exports_report(complete_report_packet):
    bindings, *_ = complete_report_packet
    report = module.build_report('charxiv', 'complete_test', bindings, {})
    pair = report['paired_conditions']['image_present__silent_no_image']
    assert pair['paired_reviewed'] == 1 and pair['unpaired_left'] == 1
    assert report['conditions']['image_present']['native']['final_accuracy']['value'] is None
    assert report['conditions']['image_present']['reviewed_unique_families'] == 2
    assert len(report['verified_generated_event_ids']) == 3
    dest = module.write_report(report)
    assert 'Unknown (2 unadjudicated)' in (dest/'summary.md').read_text()
    module.verify_hashes(report['artifact_sha256'])


def test_missing_condition_mechanics_blocks_complete_report(complete_report_packet):
    bindings, put, get, _ = complete_report_packet
    path = 'outputs/stage7a_bench_v2/native_screen/generations/silent_no_image_run/mechanics.json'
    record = get(path)
    record['checks'][0]['input']['condition'] = 'image_present'
    put(path, record)
    with pytest.raises(ValueError, match='lacks a native preflight'):
        module.build_report('charxiv', 'missing_mechanics', bindings, {})
