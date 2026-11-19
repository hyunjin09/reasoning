import numpy as np

from visual_reasoning.stage8b.block0 import geometry as frozen_geometry
from visual_reasoning.stage8b.block3b import geometry, post_read, pre_post, aligned_refresh


def test_onset_boundary_and_censoring():
    r=post_read(100,300,[50,100,101,228,229])
    assert r['windows']['128']['episodes']==2
    assert r['windows']['128']['within_window']==1
    assert r['time_to_next']==1
    assert r['windows']['256']['within_window'] is None
    assert r['windows']['256']['observed_return']
    assert post_read(299,300,[50,100])['next_retrieval_censored']


def test_symmetric_windows_require_full_exposure():
    z=np.arange(700.)[:,None]*np.array([[1.,2.,3.,4.]])
    p=pre_post(300,z)
    assert p['256']['complete'] and p['256']['pre']['valid_transitions']==256
    assert abs(p['256']['delta_tortuosity'])<1e-12
    assert not p['512']['complete'] and p['512']['delta_movement'] is None
    assert pre_post(100,z)['256']['delta_tortuosity'] is None


def test_geometry_matches_frozen_definition_with_missing_vectors():
    rng=np.random.default_rng(2);z=rng.normal(size=(25,4));z[0]=np.nan;z[10]=np.nan
    current=geometry(z);frozen,_=frozen_geometry(z)
    for new,old in [('path_length','path_length'),('movement','transition_normalized_path_length'),('displacement','net_displacement'),('tortuosity','tortuosity'),('valid_transitions','valid_transitions')]:
        assert np.isclose(current[new],frozen[old],rtol=1e-12)


def test_refresh_alignment_is_only_temporal():
    events=[dict(event_id='a',start_token=10,end_token=20),dict(event_id='b',start_token=100,end_token=110)]
    assert aligned_refresh(dict(start_token=45,end_token=49),events)==['a']


def test_family_duplicates_do_not_change_contrast():
    import pandas as pd
    from visual_reasoning.stage8b.block3b_stats import contrast
    frame=pd.DataFrame(dict(analysis_family_id=list('abcdef'),
        benchmark_label=['correct']*3+['wrong']*3,metric=[0,1,2,4,5,6]))
    freeze=dict(continuous={},categorical={})
    base=contrast(frame,'metric',freeze,draws=100)
    duplicate=contrast(pd.concat([frame,frame.iloc[[0]]]),'metric',freeze,draws=100)
    assert base['raw']==duplicate['raw']
    assert np.isclose(base['adjusted']['estimate'],duplicate['adjusted']['estimate'])
    assert base['families']==duplicate['families']==6


def test_full_confounding_is_not_silently_dropped():
    from visual_reasoning.stage8b.block3b_stats import estimate
    wrong=np.array([0.,0.,0.,1.,1.,1.])
    raw,adjusted,rank=estimate(wrong,wrong,np.column_stack([np.ones(6),wrong]),np.ones(6))
    assert raw==1 and np.isnan(adjusted) and rank==2


def test_unknown_semantics_are_not_negative_labels():
    import pandas as pd
    from visual_reasoning.stage8b.block3b_stats import missing_bounds, contrast
    frame=pd.DataFrame(dict(analysis_family_id=['a','b'],benchmark_label=['correct','wrong'],mutation=[None,None]))
    bounds=missing_bounds(frame,'mutation')
    assert bounds['difference_bounds']==[-1,1]
    assert contrast(frame,'mutation',dict(continuous={},categorical={}),draws=100)['events']==0
