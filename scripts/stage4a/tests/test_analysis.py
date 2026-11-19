from visual_reasoning.stage4a.analysis import primary_contrasts, trigger_contrasts, primary_family, semantic_contrasts


def test_crossed_trigger_and_within_base_source_orientation():
    rows = {}
    for e, demanded in [('A1','A'),('B','B'),('A2','A')]:
        effects = {x:3. if x==demanded else 1. for x in ('A','B')}
        arms = {'N':{'D':10.}, 'AB_W2':{'D':5.}, 'I_W2':{'D':9.75}}
        arms.update({x+'_W2':{'D':10.-v} for x,v in effects.items()})
        rows[e] = {'arms':arms}
    base = primary_contrasts(rows)
    assert base['dynamic'] and base['S_B']==2 and base['Switch_AB']==4
    assert base['demanded_minus_irrelevant']==2.75
    trigger = {e:{'arms':{'R16':{'D':7.},'R16_A_W2':{'D':6.},'R16_B_W2':{'D':6.}}} for e in rows}
    result = trigger_contrasts(base, trigger)
    assert [result['TS_'+e] for e in rows] == [2.,2.,2.]
    family = primary_family({'1':base})
    assert len(family)==9 and family['TS_B']['wilcoxon_p']==1 and family['TS_B']['status']=='gated_unrun'


def test_semantic_factorial_conditions_hold_other_fact_fixed_and_use_sham_magnitude():
    ds = {'OO':10., 'AO':6., 'OB':9., 'AB':4., 'A_sham':11., 'B_sham':9.5}
    rows = {c:{e:{'arms':{'N':{'D':d}}} for e in ('A1','B','A2')} for c,d in ds.items()}
    r = semantic_contrasts(rows)
    assert r['A2']['A_factorial_contexts']==[4.,5.]
    assert r['A2']['B_factorial_contexts']==[1.,2.]
    assert r['A2']['semantic_minus_sham']==3.5
    assert r['B']['semantic_selectivity']==-3.
def test_equal_source_effects_are_a_tie_not_stale_dominance():
    from visual_reasoning.stage4a.analysis import failure_phenotypes
    result = failure_phenotypes({'S_A1':1.,'S_B':0.,'S_A2':0.,'dynamic':False,
        'VSD':{'A1':{'A':1.,'B':0.},'B':{'A':.3125,'B':.3125},'A2':{'A':.2,'B':.2}}})
    assert not result['failed_switch_A_dominant']
    assert not result['failed_refresh_stale_B']
    assert result['tied_retrieval_events'] == ['B','A2']
