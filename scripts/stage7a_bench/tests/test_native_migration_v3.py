"""A hardware move must neither rerun completed samples nor change the protocol."""
from copy import deepcopy

import pytest

from scripts.stage7a.common import sha, write_json
from scripts.stage7a_bench.native_migration_v3 import pending_rows, validate_runtime_move


@pytest.fixture
def migration(tmp_path):
    rows = [dict(event_id=f'e{i}', prompt=f'question{i}') for i in range(4)]
    base = tmp_path / 'outputs/stage7a_bench_v2/native_screen/generations/old'
    protected = {}
    for row in rows[:2]:
        d = base / 'examples' / row['event_id']
        write_json(d / 'manifest_row.json', row)
        write_json(d / 'generation.json', dict(text=row['event_id']))
        (d / 'tokens.jsonl').write_text(row['event_id'])
        write_json(d / 'result.json', dict(event_id=row['event_id'],
            generation_sha256=sha(d / 'generation.json'), tokens_sha256=sha(d / 'tokens.jsonl')))
        for f in d.iterdir():
            protected[str(f.relative_to(tmp_path))] = sha(f)
    packet = dict(status='FROZEN_ALLOCATION_CONTINUATION', predecessor_run_id='old',
        continuation_run_id='new', all_event_ids=[r['event_id'] for r in rows],
        completed_event_ids=['e0', 'e1'], protected_files=protected)
    return tmp_path, rows, packet, base


def test_continuation_runs_only_the_unfinished_suffix(migration):
    root, rows, packet, _ = migration
    before = deepcopy(rows)
    assert pending_rows(root, rows, packet, 'new') == rows[2:]
    assert rows == before


@pytest.mark.parametrize('change', ['tokens', 'row', 'missing_result'])
def test_damaged_completed_response_blocks_continuation(migration, change):
    root, rows, packet, base = migration
    d = base / 'examples/e0'
    if change == 'tokens':
        (d / 'tokens.jsonl').write_text('changed')
    elif change == 'row':
        write_json(d / 'manifest_row.json', dict(event_id='e0', prompt='another question'))
    else:
        (d / 'result.json').unlink()
    with pytest.raises(ValueError, match='protected'):
        pending_rows(root, rows, packet, 'new')


@pytest.mark.parametrize('change', ['arbitrary_subset', 'new_order', 'run', 'unsafe_path'])
def test_changed_selection_or_identity_blocks_continuation(migration, change):
    root, rows, packet, _ = migration
    if change == 'arbitrary_subset': packet['completed_event_ids'] = ['e1']
    elif change == 'new_order': rows.reverse()
    elif change == 'run': packet['continuation_run_id'] = 'another'
    else: packet['protected_files']['../outside'] = 'no'
    with pytest.raises(ValueError):
        pending_rows(root, rows, packet, 'new')


def runtime():
    return dict(model_checkpoint='frozen_model', locked_generation_protocol=dict(seed=1234, max_new_tokens=40960),
        runtime=dict(slurm_allocation='old', node='old_node', gpus=1, cpus=4, host_memory='14G', dtype='bfloat16'))


def test_only_allocation_fields_may_change():
    old = runtime(); new = deepcopy(old)
    new['runtime'].update(slurm_allocation='new', node='node02', gpus=4, cpus=32, host_memory='120G')
    validate_runtime_move(old, new)
    new['locked_generation_protocol']['seed'] = 42
    with pytest.raises(ValueError, match='protocol'):
        validate_runtime_move(old, new)


def test_dtype_change_cannot_be_disguised_as_a_hardware_move():
    old = runtime(); new = deepcopy(old); new['runtime']['dtype'] = 'float32'
    with pytest.raises(ValueError, match='scientific runtime'):
        validate_runtime_move(old, new)
