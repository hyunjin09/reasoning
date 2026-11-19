from scripts.stage9a3.baseline import gates_and_lengths


def test_accuracy_cannot_rescue_invalid_cot():
    rows=[dict(cot=i<57,option='A',correct=True,normal_eos=True,tokens=100) for i in range(64)]
    result=gates_and_lengths(rows)
    assert not result['gates']['pass']
    assert not result['gates']['cot_90pct']


def test_no_answer_is_no_credit_and_temporal_grid_is_length_only():
    rows=[dict(cot=True,option='A',correct=i<40,normal_eos=True,tokens=40) for i in range(64)]
    result=gates_and_lengths(rows)
    assert result['gates']['pass'] and result['token_grid']==[0,16,20,None]


def test_short_answers_fail_temporal_gate():
    rows=[dict(cot=True,option='A',correct=True,normal_eos=True,tokens=4) for _ in range(64)]
    assert not gates_and_lengths(rows)['gates']['suitable_lengths']
