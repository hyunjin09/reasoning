"""The amended gate may release only the next frozen MathWild prefix."""
from copy import deepcopy

import pytest

from scripts.stage7a_bench.mathwild_gate_v5 import bounded_shards


def rows():
    return [dict(event_id=f'e{i}', benchmark='mathvision_wild', condition='photo') for i in range(200)]


def test_four_shards_cover_exactly_the_fifty_seven_unfinished_gate_items():
    items = rows(); shards = bounded_shards(items, [f'e{i}' for i in range(39)], 96)
    assert [len(s) for s in shards] == [15, 14, 14, 14]
    got = [r['event_id'] for s in shards for r in s]
    assert len(got) == len(set(got)) == 57
    assert set(got) == {f'e{i}' for i in range(39, 96)}
    assert items == rows()


@pytest.mark.parametrize('change', ['deferred_benchmark', 'screenshot', 'completed_gap', 'gate_expansion', 'duplicate'])
def test_scope_or_frozen_prefix_changes_are_rejected(change):
    items = deepcopy(rows()); completed = [f'e{i}' for i in range(39)]; target = 96
    if change == 'deferred_benchmark': items[50]['benchmark'] = 'mathsight'
    elif change == 'screenshot': items[50]['condition'] = 'screenshot'
    elif change == 'completed_gap': completed.remove('e0')
    elif change == 'gate_expansion': target = 97
    else: items[80]['event_id'] = 'e79'
    with pytest.raises(ValueError):
        bounded_shards(items, completed, target)
