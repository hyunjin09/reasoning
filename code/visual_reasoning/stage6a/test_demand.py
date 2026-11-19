from visual_reasoning.stage6a.demand import temporal_labels


def span(sources, explicit=(), text='quote', unresolved=False):
    return dict(demanded_sources=sources,explicit_visual_claim_sources=list(explicit),text=text,unresolved=unresolved)


def test_first_reuse_refresh_uses_full_source_history():
    rows=temporal_labels([span(['T'],['T'],'T=3'),span(['T']),span(['X'],['X'],'X=5'),span(['T'])])
    assert rows[0]['first_reuse_refresh']=='FIRST_USE'
    assert rows[1]['first_reuse_refresh']=='REUSE'
    assert rows[3]['first_reuse_refresh']=='REFRESH'
    assert rows[3]['prior_explicit_evidence']['T']['text']=='T=3'
    assert rows[3]['previous_demand']==['X']


def test_unknown_history_cannot_be_called_first_use_or_no_change():
    rows=temporal_labels([span([],unresolved=True),span(['T'],['T'])])
    assert rows[1]['first_reuse_refresh']=='UNRESOLVED'
    assert rows[1]['prior_explicit_access']['T'] is None
    assert rows[1]['demand_changed'] is None


def test_prior_positive_survives_unknown_but_no_refresh_is_invented():
    rows=temporal_labels([span(['T'],['T']),span([],unresolved=True),span(['T'])])
    assert rows[2]['prior_explicit_access']['T'] is True
    assert rows[2]['first_reuse_refresh']=='UNRESOLVED'


def test_mentions_are_not_demands_or_prior_visual_access():
    rows=temporal_labels([span([]),span(['T'])])
    assert rows[0]['first_reuse_refresh']=='NONE'
    assert rows[1]['first_reuse_refresh']=='FIRST_USE'
    assert rows[1]['prior_explicit_access']['T'] is False


def test_unreviewed_claim_candidate_is_unknown_not_negative_prior_access():
    candidate={**span(['T']),'candidate_visual_claim_sources':['T']}
    rows=temporal_labels([candidate,span(['T'])])
    assert rows[1]['prior_explicit_access']['T'] is None
    assert rows[1]['first_reuse_refresh']=='UNRESOLVED'


def test_joint_demand_narrowing_does_not_refresh_a_still_active_source():
    rows=temporal_labels([span(['T','X'],['T','X']),span(['T'])])
    assert rows[1]['first_reuse_refresh']=='REUSE'
    assert rows[1]['source_temporal_roles']=={'T':'REUSE'}


def test_returning_one_source_can_mix_refresh_with_continuing_reuse():
    rows=temporal_labels([span(['T','X'],['T','X']),span(['T']),span(['T','X'])])
    assert rows[2]['first_reuse_refresh']=='MIXED'
    assert rows[2]['source_temporal_roles']=={'T':'REUSE','X':'REFRESH'}


def test_arithmetic_pause_alone_does_not_count_as_visiting_another_source():
    rows=temporal_labels([span(['T'],['T']),span([]),span(['T'])])
    assert rows[2]['first_reuse_refresh']=='REUSE'
