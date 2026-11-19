import numpy as np
import pytest

from visual_reasoning.stage8b.transfer import reasoning_length, evaluate_transfer


def test_reasoning_boundary_excludes_final_and_retains_capped_thinking():
    assert reasoning_length(['Think', '.', '</think>', 'A']) == 2
    assert reasoning_length(['Still', ' thinking']) == 2


def fixture():
    scores = {str(i): np.zeros(100) for i in range(32)}
    demands = {str(i): i < 24 for i in range(32)}
    events = []
    for i in range(32):
        scores[str(i)][0] = np.nan
        if i < 24:
            scores[str(i)][20] = .9
            events.append(dict(item_id=str(i), category='T', query_index=20))
        events.append(dict(item_id=str(i), category='nonvisual', query_index=80))
    return scores, demands, events


def test_valid_transfer_counts_items_and_semantic_events_separately():
    scores, demands, events = fixture()
    out = evaluate_transfer(scores, demands, events, threshold=.5)
    assert out['status'] == 'PASS'
    assert out['demanding_items'] == 24
    assert out['T']['aligned_queries'] == 24
    assert out['negative']['false_alarms'] == 0


def test_false_alarm_gate_cannot_be_hidden_by_good_T_alignment():
    scores, demands, events = fixture()
    for i in range(7):
        scores[str(i)][80] = .9
    out = evaluate_transfer(scores, demands, events, threshold=.5)
    assert out['status'] == 'FAIL'
    assert out['negative']['false_alarm_rate'] == 7 / 32


def test_missing_queries_are_inconclusive_and_threshold_is_strict():
    scores, demands, events = fixture()
    out = evaluate_transfer(scores, demands, events[:10], threshold=.9)
    assert out['status'] == 'INCONCLUSIVE'
    assert out['items_with_retrieval'] == 0


def test_no_duplicate_or_out_of_range_queries_silently_inflate_denominators():
    scores, demands, events = fixture()
    with pytest.raises(ValueError, match='Duplicate'):
        evaluate_transfer(scores, demands, events + [events[0]], threshold=.5)
    events[0] = dict(events[0], query_index=100)
    with pytest.raises(ValueError, match='range'):
        evaluate_transfer(scores, demands, events, threshold=.5)
