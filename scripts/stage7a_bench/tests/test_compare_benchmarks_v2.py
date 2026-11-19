from copy import deepcopy
from pathlib import Path

import pytest

from scripts.stage7a_bench import compare_benchmarks_v2 as module
from scripts.stage7a_bench.tests.test_render_causal_v2 import inputs
from scripts.stage7a_bench.native_yield_v2 import rate
from scripts.stage7a_bench import native_report_v2
from scripts.stage7a.common import read_json, sha, write_json, write_jsonl


def evidence():
    pilot, native, source = inputs()
    native['paired_conditions'] = {}
    for i, row in enumerate(source):
        row['independent_semantic_edit'] = i < 20
    readouts = [dict(benchmark='charxiv', example_id=str(i), model_outputs_read=False,
                     readout_score='R4' if i < 32 else 'R2',
                     error_oriented_ground_truth_available=i < 16) for i in range(64)]
    candidate = dict(candidate_id='charxiv', canonical_name='CharXiv', track=['A'],
                     usable=True, status='VERIFIED', reason='Pinned source available')
    return candidate, source, readouts, native, pilot


def test_missing_native_and_pilot_are_unknown_not_zero_failure():
    candidate, source, readouts, *_ = evidence()
    row = module.comparison_row(candidate, source, readouts)
    assert row['dimensions']['A_native']['value'] is None
    assert row['dimensions']['F_causal_failure']['value'] is None
    assert row['dimensions']['B_source_identifiability']['value']['S3_S4']['value'] == .625
    assert row['dimensions']['C_readout_feasibility']['value']['R3_R4']['value'] == .5
    assert row['primary_gate_passed'] is None


def test_semantic_errors_weak_faithful_and_certified_failures_stay_separate():
    candidate, source, readouts, native, pilot = evidence()
    row = module.comparison_row(candidate, source, readouts, native=native, pilot=pilot)
    dims = row['dimensions']
    assert dims['A_native']['value']['image_present']['metrics']['local_error']['value'] == .5
    assert dims['F_causal_failure']['value']['strong_unfaithful']['events'] == 2
    assert dims['F_causal_failure']['value']['strong_unfaithful']['native_bases'] == 1
    assert dims['E_faithful']['value']['certified']['events'] == 1
    assert dims['F_causal_failure']['value']['states']['FAITHFUL_READ']['events'] == 2
    assert dims['J_gpu_cost']['value']['pilot_accounting']['complete_pipeline_gpu_hours'] is None
    assert dims['I_annotation_cost']['value'] is None
    assert row['selected'] is False


def test_photo_and_screenshot_denominators_are_not_pooled():
    candidate, source, readouts, native, _ = evidence()
    image = native['conditions'].pop('image_present')
    image['native']['condition'] = 'photo'
    native['conditions']['photo'] = image
    second = deepcopy(image)
    second['native']['condition'] = 'screenshot'
    second['native']['final_accuracy'] = dict(numerator=0, denominator=200, unknown=0, value=0)
    native['conditions']['screenshot'] = second
    row = module.comparison_row(candidate, source, readouts, native=native, native_condition='photo')
    metrics = row['dimensions']['A_native']['value']
    assert metrics['photo']['metrics']['final']['value'] == .5
    assert metrics['screenshot']['metrics']['final']['value'] == 0


@pytest.mark.parametrize('fault', ['unblinded', 'missing_readout', 'duplicate_source', 'partial_native'])
def test_inconsistent_evidence_is_rejected(fault):
    candidate, source, readouts, native, _ = evidence()
    if fault == 'unblinded': source[0]['model_outputs_read'] = True
    if fault == 'missing_readout': readouts.pop()
    if fault == 'duplicate_source': source[0] = deepcopy(source[1])
    if fault == 'partial_native': native['status'] = 'PROVISIONAL_INCOMPLETE'
    with pytest.raises(ValueError):
        module.comparison_row(candidate, source, readouts, native=native)


def phantom():
    condition = dict(frozen=200, generated=200, reviewed=200, unavailable=0,
                     pending_generation=0, pending_review=0, screen_complete=True,
                     native_elapsed_seconds=100, final_accuracy=rate([None]*200),
                     local_visual_error_rate=rate([None]*200))
    for key in ('unsupported_claim_rate','abstention_or_caveat_rate','guessed_answer_rate','truncation_rate'):
        condition[key] = rate([False]*200)
    conditions = {k:deepcopy(condition) for k in ('silent_no_image','explicit_guess')}
    conditions['silent_no_image']['unsupported_claim_rate'] = rate([True]*4+[False]*196)
    return dict(status='PHANTOM_PAIRED_SCREEN_COMPLETE_ONLY', causal_states_assigned=False,
                primary_benchmark_selected=False, conditions=conditions,
                paired_comparison=dict(paired_reviewed=200, paired_base_ids=[str(i) for i in range(200)],
                                       causal_label=None), class_transitions={'F3 → F5':4},
                family_categories={'category':200})


def test_phantom_unsupported_claims_never_become_factual_errors_or_prior_fill():
    candidate = dict(candidate_id='phantom_0', canonical_name='Phantom', track=['B'])
    row = module.comparison_row(candidate, [], [])
    module.add_phantom_behavior(row, phantom())
    assert row['dimensions']['A_native']['value']['silent_no_image']['metrics']['unsupported']['numerator'] == 4
    assert row['dimensions']['A_native']['value']['silent_no_image']['metrics']['final']['value'] is None
    assert row['dimensions']['E_faithful']['value'] is None
    assert row['dimensions']['F_causal_failure']['value'] is None
    assert row['dimensions']['H_diversity']['value']['source_families'] is None


def test_phantom_factual_accuracy_is_rejected():
    report = phantom()
    report['conditions']['silent_no_image']['final_accuracy'] = rate([True]*200)
    row = module.comparison_row(dict(candidate_id='phantom_0', canonical_name='Phantom', track=['B']), [], [])
    with pytest.raises(ValueError):
        module.add_phantom_behavior(row, report)


@pytest.fixture
def disk_request(tmp_path, monkeypatch):
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'OUT', tmp_path/'outputs/stage7a_bench_v2')
    monkeypatch.setattr(native_report_v2, 'ROOT', tmp_path)
    def put(name, value, lines=False):
        path = module.OUT/name
        (write_jsonl if lines else write_json)(path,value)
        return dict(path=str(path.relative_to(tmp_path)),sha256=sha(path))
    candidate, source, readouts, native, pilot = evidence()
    raw = put('audit/raw.json', {'synthetic':True})
    native['artifact_sha256'] = {raw['path']:raw['sha256']}
    nref = put('native_screen/reports/synthetic/report.json',native)
    pilot['source_sha256'] = {raw['path']:raw['sha256'],nref['path']:nref['sha256']}
    pref = put('causal_pilot/reports/synthetic/yield.json',pilot)
    second = dict(candidate_id='missing',canonical_name='Missing',track=['B'],usable=False,status='UNAVAILABLE',reason='No input')
    request = dict(comparison_id='synthetic', roster=put('config/benchmark_candidates.json',[candidate,second]),
        inventory=put('cohort/dataset_inventory.json',dict(candidates=[candidate,second])),
        source=put('structural_audit/source_identifiability.jsonl',source,True),
        readouts=put('structural_audit/readout_feasibility.jsonl',readouts,True),
        reports=[dict(native_report=nref,pilot_yield=pref)])
    return tmp_path/put('analysis/comparison_requests/synthetic.json',request)['path'], raw


def test_export_preserves_missing_candidates_and_snapshot(disk_request):
    request, _ = disk_request
    dest = module.export(request)
    report = read_json(dest/'benchmark_comparison.json')
    assert report['status'] == 'RAW_COMPARISON_SNAPSHOT_ONLY'
    assert report['track_members'] == {'A':['charxiv'],'B':['missing']}
    assert report['rows'][1]['dimensions']['F_causal_failure']['value'] is None
    assert report['primary_benchmark_selected'] is False
    with pytest.raises(FileExistsError): module.export(request)


def test_changed_transitive_native_evidence_blocks_comparison(disk_request):
    request, raw = disk_request
    (module.ROOT/raw['path']).write_text('{"changed":true}')
    with pytest.raises(ValueError,match='changed'): module.export(request)
    assert not (module.OUT/'analysis/comparison_batches').exists()
