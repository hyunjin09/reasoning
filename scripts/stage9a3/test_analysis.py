import numpy as np
from visual_reasoning.stage9a3.analysis import image_surface,calibration,extract_option


def test_two_queries_are_averaged_within_image_not_independent():
    rows=[dict(image_id='a',policy='full',correct=1),dict(image_id='a',policy='full',correct=0),
          dict(image_id='b',policy='full',correct=0),dict(image_id='b',policy='full',correct=0)]
    images,policies,values=image_surface(rows)
    assert images==['a','b'] and values.shape==(2,1)
    assert values[:,0].tolist()==[.5,0]


def test_joint_gate_rejects_flat_no_access_even_if_finite_is_preserved():
    values=np.ones((32,3));meta={'full':(1,None),'zero':(0,0),'finite':(.5,16)}
    out=calibration(['full','zero','finite'],values,meta,median_length=100)
    assert not out['pass'] and not out['clear_restriction_damage'] and not out['reserve_eligible']


def test_positive_gate_and_deterministic_smallest_time_then_depth():
    policies=['full','zero','a','b','c'];values=np.ones((32,5));values[:,1]=0
    meta={'full':(1,None),'zero':(0,0),'a':(.75,16),'b':(.5,16),'c':(.5,64)}
    result=calibration(policies,values,meta,median_length=120)
    assert result['pass'] and result['selected_policy']=='b'
    assert result['bootstrap_joint_stability']==1 and result['n_images']==32


def test_braced_literal_extraction_keeps_missing_and_uses_final_claim():
    assert extract_option('There are two red objects. Answer: {C}')=='C'
    assert extract_option('Maybe {A}. Recounting gives {B}.')=='B'
    assert extract_option('There are2objects') is None
