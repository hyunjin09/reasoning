from copy import deepcopy
from pathlib import Path

import pytest

from scripts.stage7a_bench import render_paired_native_v2 as module
from scripts.stage7a_bench import native_report_v2
from scripts.stage7a_bench.native_report_v2 import paired_transitions
from scripts.stage7a_bench.tests.test_render_native_v2 import report
from scripts.stage7a.common import read_json, sha, write_json


def paired_report():
    result = report()
    native = result['conditions'].pop('image_present')
    for condition in ('explicit_guess','image_present','photo','screenshot','silent_no_image'):
        row = deepcopy(native)
        row['native']['condition'] = condition
        result['conditions'][condition] = row
    def review(base, correct, claim):
        return dict(base_id=base, final_correctness=correct, local_visual_claim_present=claim,
            abstention_or_caveat=not claim, unsupported_evidence_claim=False, guessed_answer=False,
            screen_label='F0' if claim else 'F5', claims=[], output_confidence='Fixture only')
    a = [review('a',True,True), review('b',None,True)]
    b = [review('a',False,False), review('c',True,True)]
    result['paired_conditions'] = {'image_present__silent_no_image':paired_transitions(a,b),
        'explicit_guess__silent_no_image':paired_transitions(a,b),
        'photo__screenshot':paired_transitions(a,b)}
    return result


def test_pair_uses_common_ids_and_reverses_explicit_guess_order():
    row = module.select_pair(paired_report(),'silent_no_image','explicit_guess')
    assert row['paired_reviewed'] == 1
    assert row['left_final_accuracy']['value'] == 0
    assert row['right_final_accuracy']['value'] == 1
    assert row['final_correctness_transitions'] == {'wrong → correct':1}
    assert row['unpaired_left'] == row['unpaired_right'] == 1


def test_whole_condition_accuracy_does_not_replace_paired_accuracy():
    row = module.select_pair(paired_report(),'image_present','silent_no_image')
    assert row['right_final_accuracy']['value'] == 0
    assert row['right_final_accuracy']['denominator'] == 1
    assert row['paired_base_ids'] == ['a']


@pytest.mark.parametrize('change',['partial','denominator','unknown_zero','duplicate','transitions'])
def test_invalid_pair_cannot_be_plotted(change):
    result = paired_report()
    p = result['paired_conditions']['image_present__silent_no_image']
    if change == 'partial': result['conditions']['photo']['native']['pending_review'] = 1
    if change == 'denominator': p['left_visual_claim_rate']['denominator'] = 2
    if change == 'unknown_zero': p['left_final_accuracy'].update(numerator=0,denominator=0,unknown=1,value=0)
    if change == 'duplicate': p['paired_base_ids'] = ['a','a']
    if change == 'transitions': p['final_correctness_transitions'] = {'wrong → correct':2}
    with pytest.raises(ValueError):
        module.select_pair(result,'image_present','silent_no_image')


def test_export_all_supported_pair_categories(tmp_path,monkeypatch):
    code = Path(module.__file__).read_bytes()
    monkeypatch.setattr(module,'ROOT',tmp_path)
    monkeypatch.setattr(module,'OUT',tmp_path/'outputs/stage7a_bench_v2')
    monkeypatch.setattr(native_report_v2,'ROOT',tmp_path)
    script = tmp_path/'scripts/stage7a_bench/render_paired_native_v2.py'
    script.parent.mkdir(parents=True)
    script.write_bytes(code)
    result = paired_report()
    result['artifact_sha256'] = {}
    report_path = module.OUT/'native_screen/reports/synthetic/report.json'
    write_json(report_path,result)
    request = module.OUT/'analysis/paired_figure_requests/synthetic.json'
    write_json(request,dict(figure_batch_id='synthetic',reports=[dict(
        path=str(report_path.relative_to(tmp_path)),sha256=sha(report_path))]))
    dest = module.render(request)
    manifest = read_json(dest/'manifest.json')
    assert {f['figure_number'] for f in manifest['figures']} == {10,11,21}
    assert manifest['causal_states_assigned'] is False
    assert manifest['pairs']['10'][0]['paired_reviewed'] == 1
    for figure in manifest['figures']:
        for reference in figure['files'].values():
            assert sha(tmp_path/reference['path']) == reference['sha256']
    with pytest.raises(FileExistsError):
        module.render(request)
