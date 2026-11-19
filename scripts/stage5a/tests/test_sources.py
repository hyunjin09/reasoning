import numpy as np
import pytest
from visual_reasoning.stage5a.sources import source_pixel_mask,event_groups


def test_disconnected_source_mask_does_not_suppress_intervening_fact():
    f={'roi':[0,0,10,2],'roi_boxes':[[0,0,2,2],[8,0,10,2]]}
    m=source_pixel_mask(f,(4,12,3))
    assert m[:2,:2].all() and m[:2,8:10].all()
    assert not m[:,2:8].any()
    with pytest.raises(ValueError):source_pixel_mask({'roi':[0,0,13,2]},(4,12,3))


def test_equal_valued_joint_claim_is_one_union_target_and_mentions_are_aliases():
    e={'source':'A','joint_source_ids':['A','B'],'mentioned_source':'B'}
    result=event_groups(e,{'A':{},'B':{},'C':{}},{'A':[21],'B':[23],'C':[61]},list(range(100,200)),[1,10,10],np.zeros((10,10)))
    assert result['source_groups']['T']==[121,123]
    assert 'M' not in result['source_groups'] and result['roi_aliases']['M']=='T'
    assert result['source_groups']['X']==[161]
    assert not set(result['source_groups']['I']) & {121,123,161}


def test_overlap_does_not_become_an_independent_alternative_control():
    result=event_groups({'source':'A'}, {'A':{},'B':{},'C':{}}, {'A':[21,22],'B':[22,23],'C':[61]},list(range(100)),[1,10,10],np.zeros((10,10)))
    assert result['source_groups']['X']==[61]
    assert result['source_overlap']['excluded_X_B']==[22]


def test_dense_image_cannot_silently_supply_an_irrelevant_control():
    result=event_groups({'source':'A'}, {'A':{}},{'A':[21]},list(range(100)),[1,10,10],np.ones((10,10)))
    assert 'I' not in result['source_groups'] and 'unavailable' in result['irrelevant_mapping']
