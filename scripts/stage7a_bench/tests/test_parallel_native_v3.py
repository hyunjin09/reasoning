"""Dispatch must preserve unique ownership and stop new work after a failure."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest

from scripts.stage7a.common import read_json, write_json
from scripts.stage7a_bench.parallel_native_v3 import claim_next, locked_state, finish_batch


def state():
    return dict(batches=[dict(run_id=f'run{i}', status='pending') for i in range(6)])


def test_four_concurrent_claims_have_disjoint_ownership(tmp_path):
    path = tmp_path / 'dispatch.json'; write_json(path, state())
    def claim(rank):
        with locked_state(path) as current:
            return claim_next(current, rank)['run_id']
    with ThreadPoolExecutor(max_workers=4) as pool:
        names = list(pool.map(claim, range(4)))
    assert set(names) == {'run0', 'run1', 'run2', 'run3'}
    saved = read_json(path)
    assert [b['status'] for b in saved['batches']] == ['running'] * 4 + ['pending'] * 2


def test_failure_blocks_further_claims_without_changing_active_work():
    s = state(); claim_next(s, 0); claim_next(s, 1)
    finish_batch(s, 'run0', 0, 1)
    before = deepcopy(s)
    assert claim_next(s, 2) is None and s == before
    assert s['batches'][1]['status'] == 'running'


def test_success_makes_next_frozen_batch_available():
    s = state(); claim_next(s, 0); finish_batch(s, 'run0', 0, 0)
    assert claim_next(s, 0)['run_id'] == 'run1'


@pytest.mark.parametrize('rank,code', [(1, 0), (0, None)])
def test_foreign_owner_or_unknown_exit_cannot_complete_a_batch(rank, code):
    s = state(); claim_next(s, 0)
    with pytest.raises(ValueError):
        finish_batch(s, 'run0', rank, code)


def test_completed_work_cannot_be_reclaimed_or_finished_twice():
    s = state(); claim_next(s, 0); finish_batch(s, 'run0', 0, 0)
    with pytest.raises(ValueError):
        finish_batch(s, 'run0', 0, 0)
    assert claim_next(s, 1)['run_id'] == 'run1'
