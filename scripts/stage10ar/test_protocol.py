import numpy as np
from scripts.stage10ar.protocol import contrasts,mask_cutoff,earliest_transition,multiplicity_interval


def test_four_paired_contrasts_preserve_sign_and_anchor_order():
    # Assay order image_off,text_only; A2 omitted from primary contrasts.
    x=np.array([[[0,0,0,1,1],[0,0,0,1,1]],[[1,0,1,1,0],[0,1,1,0,1]]])
    assert contrasts(x).tolist()==[[1,1,1,1],[-1,1,1,-1]]


def test_prefill_reference_and_later_mask_start_are_distinct():
    assert mask_cutoff(0)==0
    assert mask_cutoff(1)==0
    assert mask_cutoff(17)==16


def test_state_is_first_available_success_and_reversals_remain_visible():
    x=[[False,False],None,[True,True],[False,True],[True,True]]
    assert earliest_transition(x)==dict(H='A2',later_reversals=['A3'])
    assert earliest_transition([[False,True]]*5)==dict(H=None,later_reversals=[])


def test_multiplicity_interval_uses_four_endpoint_bonferroni():
    ci=multiplicity_interval(np.arange(4000))
    assert np.allclose(ci,[24.99375,3974.00625])
