from copy import deepcopy
from pathlib import Path

import pytest

from scripts.stage7a_bench import render_native_v2 as module
from scripts.stage7a_bench.native_yield_v2 import rate
from scripts.stage7a.common import read_json, sha, write_json
from scripts.stage7a_bench import native_report_v2


def report():
    native = dict(benchmark='charxiv', condition='image_present', frozen=200,
        generated=2, unavailable=198, reviewed=2, pending_generation=0,
        pending_review=0, screen_complete=True, final_accuracy=rate([True, None]),
        local_visual_error_rate=rate([False, True]), unsupported_claim_rate=rate([False, False]),
        faithful_control_candidate_rate=rate([True, False]))
    return dict(status='COMPLETED_BENCHMARK_NATIVE_REPORT_ONLY', benchmark='charxiv',
        report_id='synthetic_test', causal_states_assigned=False, primary_benchmark_selected=False,
        conditions={'image_present': dict(native=native,
            dimensions={'binding_error_among_adjudicated_bindings': rate([True, True])})})


def test_plot_rows_keep_final_local_binding_and_f0_separate():
    result = module.report_rows(report())[0]
    assert result['metrics']['final']['value'] == 1
    assert result['metrics']['final']['unknown'] == 1
    assert result['metrics']['local_error']['value'] == .5
    assert result['metrics']['binding_error']['value'] == 1
    assert result['metrics']['f0_candidate']['value'] == .5
    assert result['unavailable'] == 198
    assert 'causal_state' not in result


def test_unknown_rate_has_no_plotted_point():
    obj = report()
    obj['conditions']['image_present']['native']['final_accuracy'] = rate([None, None])
    result = module.report_rows(obj)[0]
    assert result['metrics']['final']['value'] is None
    assert module.rate_label(result['metrics']['final']) == 'Unknown; 2 unadjudicated'
    assert module.rate_label(rate([False, False])) == '0/2; 0 unadjudicated'


@pytest.mark.parametrize('change', ['status', 'causal', 'selected', 'pending', 'unreviewed', 'wrong_condition'])
def test_incomplete_or_incompatible_report_is_rejected(change):
    obj = report()
    native = obj['conditions']['image_present']['native']
    if change == 'status': obj['status'] = 'PROVISIONAL_INCOMPLETE'
    if change == 'causal': obj['causal_states_assigned'] = True
    if change == 'selected': obj['primary_benchmark_selected'] = True
    if change == 'pending': native['pending_generation'] = 1
    if change == 'unreviewed': native['reviewed'] = 1
    if change == 'wrong_condition': native['condition'] = 'silent_no_image'
    with pytest.raises(ValueError):
        module.report_rows(obj)


@pytest.mark.parametrize('metric', [dict(numerator=0, denominator=0, unknown=2, value=0),
    dict(numerator=1, denominator=2, unknown=0, value=1),
    dict(numerator=3, denominator=2, unknown=0, value=1.5)])
def test_inconsistent_rate_cannot_be_plotted(metric):
    obj = deepcopy(report())
    obj['conditions']['image_present']['native']['final_accuracy'] = metric
    with pytest.raises(ValueError):
        module.report_rows(obj)


@pytest.fixture
def disk_request(tmp_path, monkeypatch):
    # Synthetic data stays in pytest's stage-audit directory, never a live report.
    real_renderer = Path(module.__file__).read_bytes()
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    monkeypatch.setattr(module, 'OUT', tmp_path/'outputs/stage7a_bench_v2')
    monkeypatch.setattr(native_report_v2, 'ROOT', tmp_path)
    renderer = tmp_path/'scripts/stage7a_bench/render_native_v2.py'
    renderer.parent.mkdir(parents=True)
    renderer.write_bytes(real_renderer)
    evidence = module.OUT/'audit/synthetic_evidence.json'
    write_json(evidence, {'scope':'Synthetic renderer test only; no research results'})
    obj = report()
    obj['artifact_sha256'] = {str(evidence.relative_to(tmp_path)):sha(evidence)}
    obj['conditions']['image_present']['native']['final_accuracy'] = rate([None, None])
    report_path = module.OUT/'native_screen/reports/synthetic_test/report.json'
    write_json(report_path, obj)
    request = module.OUT/'analysis/native_figure_requests/synthetic_test.json'
    write_json(request, dict(figure_batch_id='synthetic_test',
        reports=[dict(path=str(report_path.relative_to(tmp_path)), sha256=sha(report_path))]))
    return request, evidence, report_path


def test_real_export_keeps_unknown_and_preserves_prior_batch(disk_request):
    request, *_ = disk_request
    dest = module.render(request)
    obj = read_json(dest/'manifest.json')
    assert obj['rows'][0]['metrics']['final']['value'] is None
    assert obj['complete_sweep_claimed'] is False
    assert obj['figures'][-1]['scope'].startswith('Native component only')
    assert len(obj['figures']) == 4
    for figure in obj['figures']:
        for ref in figure['files'].values():
            assert sha(module.ROOT/ref['path']) == ref['sha256']
    with pytest.raises(FileExistsError):
        module.render(request)


@pytest.mark.parametrize('change', ['evidence', 'report'])
def test_changed_source_prevents_any_figure_export(disk_request, change):
    request, evidence, report_path = disk_request
    (evidence if change == 'evidence' else report_path).write_text('{}')
    with pytest.raises(ValueError, match='changed'):
        module.render(request)
    assert not (module.OUT/'analysis/figures').exists()
