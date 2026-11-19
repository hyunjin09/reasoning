from visual_reasoning.stage9a.demands import nominate


def tokens(s):
    return [dict(decoded_token=c) for c in s]


def test_bounded_and_score_free():
    s=("From the diagram angle A looks acute. "*40)
    found=nominate(tokens(s),0,len(s),"task")
    assert len(found)==4 and len({e["quarter"] for e in found})==4
    assert all(e["review_status"]=="pending" for e in found)
    assert not any("score" in key or "correct" in key for e in found for key in e)


def test_excludes_final_answer_and_nonvisual_math():
    s="We solve x + 2 = 5.\n\nFrom the diagram the answer is 3."
    assert not nominate(tokens(s),0,19,"task")
    assert not nominate(tokens("The answer is 3."),0,16,"task")


def test_exact_token_coordinate_and_stable_event_id():
    s="Let's check. From the figure we can read 30 degrees."
    a=nominate(tokens(s),0,len(s),"task")
    assert a[0]["demand_token"]==s.index("From")
    assert a==nominate(tokens(s),0,len(s),"task")
