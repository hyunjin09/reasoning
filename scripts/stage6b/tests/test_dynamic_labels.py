from scripts.stage6b.analyze_dynamics import dominant


def test_no_forced_winner_for_mixed_inactive_or_unmeasured_sources():
    assert dominant({'T':.01,'P':-.1},.05,.1)=='NONE'
    assert dominant({'T':1.,'P':.96},.05,.1)=='MIXED'
    assert dominant({'T':1.},.05,.1)=='UNRESOLVED'
    assert dominant({'T':.01,'P':1.},.05,.1)=='P'
