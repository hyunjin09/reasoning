import numpy as np
from visual_reasoning.stage9a.statistics import mean_interval,paired
from scripts.stage9a.extract_analysis import aligned


def test_missing_and_low_support_are_not_zero_or_equivalence():
    assert mean_interval([None,np.nan])['mean'] is None
    assert mean_interval([1]*19)['ci'] is None
    assert mean_interval([1]*20)['ci']==[1.,1.]


def test_paired_overlap_and_equal_family_weight():
    rows=[]
    for f in range(20):
        for a,v in [('thinking',4),('instruct_cot',1)]:
            rows.append(dict(family_id=str(f),arm=a,primary={'P1':v}))
    rows.append(dict(family_id='unpaired',arm='thinking',primary={'P1':1000}))
    r=paired(rows,'P1');assert r['n_families']==20 and r['mean']==3 and r['ci']==[3,3]


def test_generated_prediction_alignment_window_and_edges():
    active=np.zeros(100,dtype=bool);active[36]=True
    assert aligned(active,20,0,100)
    assert not aligned(active,19,0,100)
    active[99]=True
    assert not aligned(active,0,0,100)


def test_adjustment_recovers_known_arm_contrast_with_family_resampling(monkeypatch):
    import visual_reasoning.stage9a.statistics as st
    monkeypatch.setattr(st,'B',80)
    rng=np.random.default_rng(7);rows=[]
    for family in range(30):
        for arm in ('instruct_direct','instruct_cot','thinking'):
            length=int(rng.integers(50,1500))
            rows.append(dict(family_id=str(family),arm=arm,subject=str(family%3),completion='normal',
                answer_format='free',difficulty=family%5+1,question_length=20+family,
                primary=dict(reasoning_tokens=length,P1=2*(arm=='thinking')+0.1*np.log(length))))
    out=st.adjusted(rows,'P1')
    assert abs(out['coefficient']-2)<1e-8
    assert out['n_families']==30 and out['valid_replicates']==80
    assert np.allclose(out['ci'],[2,2])
