import pytest
from visual_reasoning.stage4a.cohort import choose_event_triplet, dynamic_class
from visual_reasoning.stage4a.cohort import equivalent_numeric_matches

def test_numeric_proposals_preserve_sign_and_accept_equivalent_decimal_forms():
    text='158 degrees, 158.0 degrees; -158, 1158, 158.5, x158. 2x + 23.'
    assert [m.group() for m in equivalent_numeric_matches(text,'158.0')] == ['158','158.0']
    assert [m.group() for m in equivalent_numeric_matches(text,'2')] == ['2']

def test_choose_keeps_first_use_and_prefers_well_separated_events():
    assert choose_event_triplet([10,28,70],[25,40]) == (10,40,70)
    assert choose_event_triplet([10,35],[23]) == (10,23,35)
    assert choose_event_triplet([10,30],[15]) is None

def test_dynamic_class_needs_real_demanded_source_effects():
    good={'A1':{'A':.2,'B':.01},'B':{'A':.01,'B':.2},'A2':{'A':.2,'B':.01}}
    assert dynamic_class(good)['dynamic']
    good['A2']={'A':.02,'B':-.1}
    assert not dynamic_class(good)['dynamic']
