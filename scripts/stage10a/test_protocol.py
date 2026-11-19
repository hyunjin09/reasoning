import pytest
from scripts.stage10a.protocol import anchor_cutoff, gate_a
from visual_reasoning.stage9a3.access import blocked_rows


def test_first_future_prediction_is_blocked_without_changing_prior_prefix():
    prompt=70;n=15;cutoff=anchor_cutoff(n)
    assert blocked_rows(0,prompt,20,prompt,36,cutoff)==list(range(n-1,20))
    assert blocked_rows(35,prompt+n-1,1,prompt,36,cutoff)==[0]
    assert blocked_rows(35,0,prompt,prompt,36,cutoff)==[]


def test_empty_prefix_is_not_a_semantic_anchor():
    with pytest.raises(AssertionError):anchor_cutoff(0)


def test_gate_a_stops_when_neither_transition_is_substantial():
    assert not gate_a(0,0)
    assert not gate_a(2/24,1/24)


def test_either_transition_opens_execution_but_not_full_claim():
    assert gate_a(3/24,0)
    assert gate_a(-1/24,3/24)
