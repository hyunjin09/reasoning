from scripts.stage11cr.protocol import completion_gate,token_comparison,repetition_metrics


def rows(n):
    return [dict(task_id=str(i),arm='thinking' if i<n//2 else 'instruct_direct',
        at_length_cap=False,committed_final=True,pathological_repetition=False,
        image_input_valid=True,replay_tier_pass=True,budget_interrupted=False) for i in range(n)]


def test_nonprimary_strict_rates_and_missing():
    r=rows(24)
    for i in [0,1,12]:r[i]['at_length_cap']=True
    assert completion_gate(r,'nonprimary')['pass_gate']
    r[13]['at_length_cap']=True
    assert not completion_gate(r,'nonprimary')['pass_gate']
    r[13]['at_length_cap']=False;r[2]['at_length_cap']=True
    assert not completion_gate(r,'nonprimary')['pass_gate']
    assert completion_gate(r[:-1],'nonprimary')['status']=='INCOMPLETE'
    r=rows(24);r[0]['budget_interrupted']=True
    assert completion_gate(r,'nonprimary')['status']=='INCOMPLETE'


def test_native_completion_imbalance_and_cap_boundary():
    r=rows(160)
    for i in range(16):r[i]['at_length_cap']=True
    assert not completion_gate(r,'native')['pass_gate']
    r=rows(160)
    for i in range(16):r[i]['committed_final']=False
    assert not completion_gate(r,'native')['pass_gate']
    r[15]['committed_final']=True
    assert completion_gate(r,'native')['pass_gate']


def test_replay_cannot_hide_divergence_or_loops():
    assert token_comparison([1,2],[1,2])['exact_token_identity']
    assert token_comparison([1,2],[1,2,3])['first_divergence_token']==2
    assert token_comparison([1,2],[1,3])['first_divergence_token']==1
    assert repetition_metrics(list(range(64))*15)['automatic_pathology']
    r=rows(12);r[0]['replay_tier_pass']=False
    assert not completion_gate(r,'known_good')['pass_gate']
