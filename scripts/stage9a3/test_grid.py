from scripts.stage9a3.grid import unique_policies, baseline_alias


def test_zero_depth_and_zero_time_are_exact_aliases():
    policies=unique_policies([0,16,64,None])
    assert len(policies)==10 and (0,0) in policies and (1,None) in policies


def test_unreached_cutoff_identity_requires_full_depth_and_eos():
    assert baseline_alias(1,16,17,True)
    assert not baseline_alias(1,16,18,True)
    assert not baseline_alias(.75,64,12,True)
    assert not baseline_alias(1,64,12,False)
