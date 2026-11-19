import pytest
from visual_reasoning.stage3c10.protocol import source_windows, paired_effects, trigger_gate

def test_coordinates_exclude_current_and_do_not_spill_into_prompt():
    assert source_windows(34)['R16'] == list(range(17,33))
    assert source_windows(34)['E16'] == list(range(1,17))
    assert source_windows(7)['R16'] == list(range(6))
    assert source_windows(32)['E16'] is None
    assert source_windows(33)['E16'] == list(range(16))
    with pytest.raises(ValueError): source_windows(0)

def test_difference_in_differences_and_roi_controls():
    states={s:{a:{'none':{'D':10.,'rds':6.},'T':{'D':8.},'I':{'D':9.}} for a in ['N','R16','E16','Q']} for s in ['M','T']}
    states['T']['R16']['T']['D']=9.5
    states['T']['R16']['none']['rds']=2.
    e=paired_effects(states)
    assert e['rds_T']==4
    assert e['vsd_T']==1.5
    assert e['did']==1.5
    assert e['r16_minus_e16']==1.5
    assert e['target_minus_irrelevant']==1.5

def test_routing_only_cannot_pass_trigger():
    s={k:{'robust_positive':k=='rds_T'} for k in ['rds_T','vsd_T','did','r16_minus_e16','target_minus_irrelevant']}
    assert not trigger_gate(s)['passed']
