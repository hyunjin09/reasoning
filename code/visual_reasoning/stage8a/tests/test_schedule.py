import pytest
from visual_reasoning.stage8a.schedule import query_schedule


def test_first_evidence_token_is_predicted_from_final_prefix_token_and_past_is_strict():
    ids = [10,11,12,13,14,15,16]
    requests = [dict(event_id="x",prefix_token_ids=ids[:3],original_token_ids=ids[3:5]),
                dict(event_id="y",prefix_token_ids=ids[:5],original_token_ids=ids[5:7])]
    s = query_schedule(requests,ids,past_window=2)
    assert s["readout"] == {2:[("x",0)],3:[("x",1)],4:[("y",0)],5:[("y",1)]}
    assert s["passive"] == {0,1,2,3,4}
    assert s["last_query"] == 5
    assert 5 not in s["passive"]  # Future evidence query is not temporal history.


def test_mismatched_native_readout_is_rejected_before_replay():
    with pytest.raises(ValueError,match="align"):
        query_schedule([dict(event_id="x",prefix_token_ids=[1,2],original_token_ids=[4])],[1,2,3])
