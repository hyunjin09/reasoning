import numpy as np
from scripts.stage10b.routing import roi_indices,reaccess


def test_roi_is_row_major_pixel_center_mapping_with_disjoint_control():
    assert roi_indices([0,0,.5,1],(1,2,4))==[0,1,4,5]
    assert roi_indices([.5,0,1,1],(1,2,4))==[2,3,6,7]


def test_global_detector_without_target_specificity_never_qualifies():
    r=reaccess(np.ones((32,4)),np.ones(32),list(range(32)),target=[0],irrelevant=[1,2,3],tau=.5,observation_offset=3)
    assert not r['C5'] and r['classification']=='ATTENTION_ONLY'


def test_two_target_specific_queries_and_detector_qualify_with_exact_timing():
    f=np.ones((32,4));f[5:7,0]=10
    r=reaccess(f,np.ones(32),list(range(32)),target=[0],irrelevant=[1,2,3],tau=.5,observation_offset=None)
    assert r['C5'] and r['lag']==5 and r['evidence_channel']=='detector_and_target_routing'


def test_routing_only_requires_explicit_observation_in_frozen_window():
    f=np.ones((32,4));f[3:6,0]=10
    assert reaccess(f,None,list(range(32)),target=[0],irrelevant=[1,2,3],tau=.5,observation_offset=10)['C5']
    assert not reaccess(f,None,list(range(32)),target=[0],irrelevant=[1,2,3],tau=.5,observation_offset=32)['C5']


def test_partial_coverage_and_missing_target_are_not_observed_absence():
    r=reaccess(np.ones((3,4)),np.zeros(3),[0,1,2],target=[0],irrelevant=[1,2,3],tau=.5,observation_offset=None)
    assert r['classification']=='ROUTING_DATA_MISSING' and not r['coverage_complete']
    r=reaccess(np.ones((32,4)),np.ones(32),list(range(32)),target=[],irrelevant=[1,2,3],tau=.5,observation_offset=2)
    assert r['classification']=='TARGET_AMBIGUOUS' and not r['C5']


def test_timing_uses_earliest_qualifying_channel_not_detector_preference():
    f=np.ones((32,4));f[2:4,0]=10;f[20:22,0]=10
    score=np.zeros(32);score[20:22]=1
    r=reaccess(f,score,list(range(32)),target=[0],irrelevant=[1,2,3],tau=.5,observation_offset=4)
    assert r['C5'] and r['lag']==2 and r['evidence_channel']=='routing_and_explicit_observation'
