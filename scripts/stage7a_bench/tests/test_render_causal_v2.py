from copy import deepcopy
from pathlib import Path

import pytest

from scripts.stage7a_bench import render_causal_v2 as module
from scripts.stage7a_bench import native_report_v2
from scripts.stage7a_bench.pilot_yield_v2 import summarize
from scripts.stage7a_bench.native_yield_v2 import rate
from scripts.stage7a_bench.tests.test_pilot_yield_v2 import packet
from scripts.stage7a_bench.tests.test_render_native_v2 import report
from scripts.stage7a.common import read_json, sha, write_json, write_jsonl


def inputs():
    entries, labels, native, compilation = packet()
    full = report()
    condition = full['conditions']['image_present']['native']
    condition.update(generated=200, reviewed=200, unavailable=0, native_elapsed_seconds=3600)
    for key in ('final_accuracy', 'local_visual_error_rate', 'unsupported_claim_rate',
                'faithful_control_candidate_rate'):
        condition[key] = rate([True, False, None]*66+[True, False])
    full['conditions']['image_present']['dimensions']['binding_error_among_adjudicated_bindings'] = rate([True]*200)
    native.update(full)
    result = summarize(entries, labels, native, compilation)
    result.update(status='COMPLETED_PILOT_YIELD_ONLY', thresholds_retuned=False,
                  primary_benchmark_selected=False, run_id='synthetic_pilot')
    structural = [dict(benchmark='charxiv', example_id=str(i), model_outputs_read=False,
                       source_score='S3' if i < 40 else 'S2') for i in range(64)]
    return result, native, structural


def test_captured_events_and_bases_differ_and_weak_controls_stay_weak():
    row = module.report_row(*inputs())
    assert row['unfaithful_events_per_100'] == 1
    assert row['unfaithful_bases_per_100'] == .5
    assert row['faithful_events_per_100'] == .5
    assert row['states']['FAITHFUL_READ']['events'] == 2
    assert row['states']['FAITHFUL_READ']['certified_events'] == 1
    assert row['native_accuracy']['unknown'] == 66
    assert row['source_identifiability'] == dict(numerator=40, denominator=64, value=.625)
    assert row['complete_pipeline_gpu_hours'] is None
    assert row['annotation_minutes_per_strong_failure'] is None


def test_all_unknown_accuracy_does_not_become_zero():
    args = inputs()
    args[1]['conditions']['image_present']['native']['final_accuracy'] = rate([None]*200)
    assert module.report_row(*args)['native_accuracy']['value'] is None


def test_named_photo_condition_is_supported_without_pooling_screenshot_accuracy():
    result, native, structural = inputs()
    photo = native['conditions'].pop('image_present')
    photo['native']['condition'] = 'photo'
    native['conditions']['photo'] = photo
    screenshot = deepcopy(photo)
    screenshot['native']['condition'] = 'screenshot'
    screenshot['native']['final_accuracy'] = rate([False]*200)
    native['conditions']['screenshot'] = screenshot
    row = module.report_row(result, native, structural, native_condition='photo')
    assert row['native_condition'] == 'photo'
    assert row['native_accuracy']['value'] == .5
    with pytest.raises(ValueError):
        module.report_row(result, native, structural, native_condition='silent_no_image')


@pytest.mark.parametrize('change', ['partial', 'selected', 'retuned', 'count', 'rate',
                                  'native_bases', 'structural_unblinded', 'duplicate_structure'])
def test_inconsistent_completed_evidence_is_rejected(change):
    result, native, structural = inputs()
    if change == 'partial': result['status'] = 'PARTIAL'
    if change == 'selected': result['primary_benchmark_selected'] = True
    if change == 'retuned': result['thresholds_retuned'] = True
    if change == 'count': result['state_counts']['FAITHFUL_READ']['certified_events'] = 3
    if change == 'rate': result['strong_unfaithful_events_per_100_frozen_native_bases'] = 50
    if change == 'native_bases': result['native_frozen_bases'] = 199
    if change == 'structural_unblinded': structural[0]['model_outputs_read'] = True
    if change == 'duplicate_structure': structural[0] = deepcopy(structural[1])
    with pytest.raises(ValueError):
        module.report_row(result, native, structural)


@pytest.fixture
def disk_request(tmp_path, monkeypatch):
    renderer = Path(module.__file__).read_bytes()
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'OUT', tmp_path/'outputs/stage7a_bench_v2')
    monkeypatch.setattr(native_report_v2, 'ROOT', tmp_path)
    script = tmp_path/'scripts/stage7a_bench/render_causal_v2.py'
    script.parent.mkdir(parents=True)
    script.write_bytes(renderer)
    def put(name, value, lines=False):
        path = module.OUT/name
        (write_jsonl if lines else write_json)(path, value)
        return dict(path=str(path.relative_to(tmp_path)), sha256=sha(path))
    result, native, structural = inputs()
    evidence = put('audit/synthetic.json', {'scope':'Synthetic rendering fixture only'})
    native['artifact_sha256'] = {evidence['path']:evidence['sha256']}
    native_ref = put('native_screen/reports/synthetic/report.json', native)
    result['source_sha256'] = {**native['artifact_sha256'], native_ref['path']:native_ref['sha256']}
    yield_ref = put('causal_pilot/reports/synthetic_pilot/yield.json', result)
    source_ref = put('structural_audit/source_identifiability.jsonl', structural, True)
    request = put('analysis/causal_figure_requests/synthetic.json', dict(figure_batch_id='synthetic',
        source_identifiability=source_ref, reports=[dict(pilot_yield=yield_ref, native_report=native_ref)]))
    return tmp_path/request['path'], evidence, source_ref


def test_exports_nine_categories_and_preserves_batch(disk_request):
    request, *_ = disk_request
    dest = module.render(request)
    result = read_json(dest/'manifest.json')
    assert {r['figure_number'] for r in result['figures']} == {9,13,14,15,16,17,18,19,20}
    assert result['primary_benchmark_selected'] is False
    assert result['population_prevalence_estimated'] is False
    assert result['rows'][0]['unfaithful_bases_per_100'] == .5
    for figure in result['figures']:
        for ref in figure['files'].values():
            assert sha(module.ROOT/ref['path']) == ref['sha256']
    with pytest.raises(FileExistsError):
        module.render(request)


@pytest.mark.parametrize('which', [1,2])
def test_changed_raw_or_structural_source_blocks_export(disk_request, which):
    request = disk_request[0]
    (module.ROOT/disk_request[which]['path']).write_text('{}')
    with pytest.raises(ValueError, match='changed'):
        module.render(request)
    assert not (module.OUT/'analysis/figures').exists()
