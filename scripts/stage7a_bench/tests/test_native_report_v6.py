"""Retained reports bind every shard to its actual historical runtime."""
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.stage7a_bench import native_report_v6 as report
from scripts.stage7a_bench.tests.test_completed_screen_v7 import screen_fixture
from scripts.stage7a_bench.tests.test_native_report_v2 import runtime_packet
from scripts.stage7a_bench.tests.test_mmmu_behavioral_partitions_v6 import packet as behavior_packet


@pytest.fixture
def packet(screen_fixture, monkeypatch):
    root, out, bindings, save, _ = screen_fixture
    monkeypatch.setattr(report, 'ROOT', root)
    monkeypatch.setattr(report, 'OUT', out)
    env, sig, mech, runtime, _ = runtime_packet()
    env['sys_prefix'] = str(root / '.venv')
    original = save('config/runtime.json', runtime)
    runtime['original_runtime'] = dict(path=original, sha256=report.sha(root / original))
    current = save('config/runtime_node02_v3.json', runtime)
    prefix = 'native_screen/generations/shard0/'
    signature = report.read_json(out / (prefix+'signature.json'))
    signature.update(slurm_job_id='job', runtime_config=current,
                     dependencies={current:report.sha(root / current)})
    save(prefix+'signature.json', signature)
    save(prefix+'environment.json', env)
    mech['checks'][0]['input']['condition'] = 'photo'
    save(prefix+'mechanics.json', mech)
    actual = Path(__file__).resolve().parents[3]
    for name in report.REPORT_DEPENDENCIES:
        target = root / 'scripts/stage7a_bench' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((actual / 'scripts/stage7a_bench' / name).read_bytes())
    return root, out, bindings, save


def test_complete_shard_report_preserves_native_dimensions_and_runtime(packet):
    _, _, bindings, _ = packet
    result = report.build_report('mathvision_wild', 'test_complete', bindings, {})
    assert result['conditions']['photo']['native']['reviewed'] == 1
    assert result['verified_generated_event_ids'] == ['e0']
    assert result['native_runs']['shard0']['runtime_config'].endswith('runtime_node02_v3.json')
    assert result['causal_states_assigned'] is False
    assert result['pilot_selected'] is False


@pytest.mark.parametrize('defect', ['missing_runtime_hash', 'fp32', 'wrong_node',
    'failed_mechanics', 'wrong_condition', 'changed_protocol', 'implicit_old_runtime'])
def test_unverified_shard_cannot_enter_report(packet, defect):
    _, out, bindings, save = packet
    prefix = 'native_screen/generations/shard0/'
    if defect in ('missing_runtime_hash', 'implicit_old_runtime'):
        value = report.read_json(out / (prefix+'signature.json'))
        if defect == 'missing_runtime_hash':
            value['dependencies'] = {}
        else:
            value.pop('runtime_config')
        save(prefix+'signature.json', value)
    elif defect in ('fp32', 'wrong_node'):
        value = report.read_json(out / (prefix+'environment.json'))
        value['parameter_dtype' if defect == 'fp32' else 'node'] = 'other'
        save(prefix+'environment.json', value)
    elif defect in ('failed_mechanics', 'wrong_condition'):
        value = report.read_json(out / (prefix+'mechanics.json'))
        if defect == 'failed_mechanics':
            value['checks'][0]['repeat_token_ids_exact'] = False
        else:
            value['checks'][0]['input']['condition'] = 'screenshot'
        save(prefix+'mechanics.json', value)
    else:
        value = report.read_json(out / 'config/runtime_node02_v3.json')
        value['locked_generation_protocol']['max_new_tokens'] = 128
        current = save('config/runtime_node02_v3.json', value)
        signature = report.read_json(out / (prefix+'signature.json'))
        signature['dependencies'][current] = report.sha(out / 'config/runtime_node02_v3.json')
        save(prefix+'signature.json', signature)
    with pytest.raises(ValueError):
        report.build_report('mathvision_wild', 'reject', bindings, {})


def test_request_cannot_replace_loaded_evidence_hash(packet):
    _, _, bindings, _ = packet
    with pytest.raises(ValueError, match='conflicts'):
        report.build_report('mathvision_wild', 'reject', bindings,
                            {bindings['photo']['manifest']:'incorrect'})


def test_verified_preserved_prefix_keeps_its_original_allocation(packet, monkeypatch):
    root, out, bindings, save = packet
    # The real loader already owns prefix integrity. Here retain its verified
    # receipt and exercise only reporting of the historical runtime.
    receipt = report.load_completed_screen('mathvision_wild', bindings)
    monkeypatch.setattr(report, 'load_completed_screen', lambda *args:receipt)
    bindings['photo']['runs'][0]['preserved_prefix'] = {'verified_by_loader':True}
    prefix = 'native_screen/generations/shard0/'
    signature = report.read_json(out / (prefix+'signature.json'))
    signature.pop('runtime_config')
    original = 'outputs/stage7a_bench_v2/config/runtime.json'
    signature['dependencies'] = {original:report.sha(root / original)}
    signature_name = save(prefix+'signature.json', signature)
    receipt['artifact_sha256'][signature_name] = report.sha(root / signature_name)
    current = report.read_json(out / 'config/runtime_node02_v3.json')
    current['runtime'].update(slurm_allocation='new_job', node='new_node')
    save('config/runtime_node02_v3.json', current)
    result = report.build_report('mathvision_wild', 'preserved', bindings, {})
    assert result['native_runs']['shard0']['environment']['slurm_job_id'] == 'job'
    assert result['native_runs']['shard0']['runtime_config'] == original


def behavior_inputs():
    groups, ids, families = behavior_packet()
    bindings = {c: {'manifest': 'frozen_'+c} for c in groups}
    hashes = {b['manifest']: c+'_hash' for c, b in bindings.items()}
    receipt = dict(reviews=groups, family_map=families, artifact_sha256=hashes)
    protocol = dict(status='PRE_NATIVE_PROTOCOL_COMPATIBILITY_AUDIT', benchmark='mmmu_pro',
        paired_base_ids=ids, frozen_conditions={c: dict(manifest=b['manifest'],
        sha256=hashes[b['manifest']]) for c, b in bindings.items()})
    return receipt, bindings, protocol


def test_report_behavior_keeps_all_frozen_pairs_and_uncertain_absent_results():
    result = report.mmmu_behavior(*behavior_inputs())
    assert result['paired_universe']['bases'] == 4
    assert result['partitions']['unresolved_absent_conditions']['base_ids'] == ['c', 'd']
    assert result['published_bclean_labels_reproduced'] is False
    assert result['subset_selected'] is False


@pytest.mark.parametrize('defect', ['changed_manifest', 'changed_hash', 'removed_pair',
                                  'missing_absent_review', 'wrong_protocol'])
def test_report_rejects_altered_behavioral_universe(defect):
    receipt, bindings, protocol = behavior_inputs()
    if defect == 'changed_manifest':
        bindings['silent_no_image']['manifest'] = 'different'
    elif defect == 'changed_hash':
        protocol['frozen_conditions']['image_present']['sha256'] = 'different'
    elif defect == 'removed_pair':
        protocol['paired_base_ids'].remove('c')
    elif defect == 'missing_absent_review':
        receipt['reviews']['silent_no_image'].pop()
    else:
        protocol['benchmark'] = 'different'
    with pytest.raises(ValueError):
        report.mmmu_behavior(receipt, bindings, protocol)


def test_complete_mmmu_report_attaches_behavior_and_protocol_provenance(packet, monkeypatch):
    root, out, old_bindings, save = packet
    receipt = report.load_completed_screen('mathvision_wild', old_bindings)
    source_review = receipt['reviews']['photo'][0]
    source_screen = receipt['screen']['photo']
    conditions = ('image_present', 'silent_no_image', 'explicit_guess')
    bindings, groups, specs = {}, {}, {}
    for condition, correct in zip(conditions, (True, False, None)):
        manifest = save('cohort/benchmark_manifests/'+condition+'.json', {'condition': condition})
        receipt['artifact_sha256'][manifest] = report.sha(root / manifest)
        bindings[condition] = dict(manifest=manifest, runs=deepcopy(old_bindings['photo']['runs']))
        value = deepcopy(source_review)
        value.update(benchmark='mmmu_pro', condition=condition, final_correctness=correct)
        groups[condition] = [value]
        specs[condition] = dict(manifest=manifest, sha256=report.sha(root / manifest))
    receipt.update(reviews=groups, screen={c: source_screen for c in conditions})
    monkeypatch.setattr(report, 'load_completed_screen', lambda *args: receipt)
    prefix = 'native_screen/generations/shard0/'
    mechanics = report.read_json(out / (prefix+'mechanics.json'))
    check = mechanics['checks'][0]
    mechanics['checks'] = [dict(check, input=dict(check['input'], condition=c)) for c in conditions]
    save(prefix+'mechanics.json', mechanics)
    official = save('cohort/provenance/original_protocol.json', {'executed': False})
    protocol = save('audit/mmmu_bclean_frozen_protocol_compatibility_v1.json',
        dict(status='PRE_NATIVE_PROTOCOL_COMPATIBILITY_AUDIT', benchmark='mmmu_pro',
        frozen_conditions=specs, paired_base_ids=[source_review['base_id']],
        official_protocol=dict(path=official, sha256=report.sha(root / official))))
    result = report.build_report('mmmu_pro', 'mmmu_complete', bindings, {})
    behavior = result['local_mmmu_behavior']
    assert behavior['partitions']['unresolved_absent_conditions']['bases'] == 1
    assert behavior['partitions']['both_absent_conditions_wrong']['bases'] == 0
    assert result['artifact_sha256'][protocol] == report.sha(root / protocol)
    assert result['artifact_sha256'][official] == report.sha(root / official)
    with pytest.raises(ValueError, match='protocol changed'):
        report.build_report('mmmu_pro', 'reject', bindings, {official: 'different'})
