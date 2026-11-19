import pytest
import torch
from visual_reasoning.stage4a.runtime import event_coordinates, intervention_sources
from visual_reasoning.stage3c10.runtime import delete_sources


def test_event_window_and_trigger_have_distinct_causal_coordinates():
    event = {'candidate_start_token': 25, 'current_query_zero_based': 24,
             'history_before_ed_token_ids': [1]*25}
    c = event_coordinates(event, 100)
    assert c['partition'] == [(0, 17)] + [(i, i+1) for i in range(17, 25)]
    assert c['R16'] == list(range(108, 124))
    assert 124 not in c['R16']
    with pytest.raises(ValueError):
        event_coordinates({**event, 'current_query_zero_based': 25}, 100)


def test_joint_is_one_union_not_sum_of_separately_rounded_effects():
    groups = {'A': [1, 3], 'B': [5, 7]}
    parts, names = intervention_sources(groups, 'AB', [10, 11])
    assert parts == [[10, 11], [1, 3, 5, 7]] and names == ['R16', 'AB']
    g = torch.Generator().manual_seed(49)
    v = torch.randn(1, 4, 20, 8, generator=g).bfloat16()
    a = torch.softmax(torch.randn(1, 4, 1, 20, generator=g), -1).bfloat16()
    native = (a @ v).transpose(1, 2)
    before = [x.clone() for x in (native, a, v)]
    actual, _ = delete_sources(native, a, v, parts, offset=19)
    expected = native[:, 0].float()
    for p in parts:
        expected -= (a[:, :, 0, p, None] * v[:, :, p]).sum(2).float()
    assert torch.equal(actual[:, 0], expected.bfloat16())
    assert all(torch.equal(x, y) for x, y in zip((native, a, v), before))
    noop, _ = delete_sources(native, a, v, parts, offset=19, gain=1.)
    assert torch.equal(noop, native)
    with pytest.raises(ValueError):
        intervention_sources(groups, 'A', [1])
