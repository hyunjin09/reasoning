from visual_reasoning.stage3c9r.analysis import classify_bases, summarize_bases
from scripts.stage3c9r.tests.test_protocol import family


def test_two_windows_of_one_event_are_not_two_checkpoints():
    event = {'event_id': 1, 'span_start_token': 20, 'span_end_token': 22}
    manifest = [{'base_problem_id': '1', 'events': [event]}]
    families = {('1', 1, w): family() for w in ('W8', 'W16')}
    bases = classify_bases(manifest, families)
    assert bases[0]['checkpoint_count'] == 1
    assert not bases[0]['repeated_checkpoint']


def test_repeated_requires_separated_distinct_event_spans():
    events = [{'event_id': i, 'span_start_token': start, 'span_end_token': start+2}
              for i,start in enumerate([20, 44])]
    manifest = [{'base_problem_id': '1', 'events': events}]
    families = {('1', i, w): family() for i in (0,1) for w in ('W8', 'W16')}
    result = classify_bases(manifest, families)
    assert result[0]['checkpoint_count'] == 2
    assert result[0]['repeated_checkpoint']
    assert summarize_bases(result)['statistics']['checkpoint_count']['N_unique_bases'] == 1


def test_distinct_final_can_upgrade_without_changing_repeated_count():
    manifest = [{'base_problem_id': '1', 'events': [{'event_id':0,'span_start_token':20,'span_end_token':22}]}]
    families = {('1', 0, 'W8'): family()}
    result = classify_bases(manifest, families, final_gains={('1',0,'W8'):{'O':.1,'C':.1}})
    assert result[0]['events'][0]['classification'] == 'C3'
    assert result[0]['checkpoint_count'] == 1
