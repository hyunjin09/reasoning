import pytest
from visual_reasoning.stage8b.four_execution import runtime_rank, assigned_rows


def test_four_workers_cover_unfinished_rows_once_preserving_order():
    rows = [dict(item_id=str(i)) for i in range(32)]
    shards = [assigned_rows(rows, rank=rank, reused={'0'}) for rank in range(4)]
    ids = [r['item_id'] for part in shards for r in part]
    assert len(ids) == 31 and set(ids) == {str(i) for i in range(1,32)}
    assert [r['item_id'] for r in shards[0]] == [str(i) for i in range(1,32,4)]
    assert [len(part) for part in shards] == [8,8,8,7]


def test_rank_requires_four_slurm_tasks_one_visible_gpu_each():
    env = dict(SLURM_JOB_ID='123', SLURM_PROCID='3', SLURM_NTASKS='4')
    assert runtime_rank(env, visible_devices=1, allocation='123') == 3
    for changes, devices in [({'SLURM_JOB_ID':'124'},1), ({'SLURM_NTASKS':'1'},1),
                             ({'SLURM_PROCID':'4'},1), ({},4)]:
        with pytest.raises(ValueError):
            runtime_rank(dict(env, **changes), visible_devices=devices, allocation='123')


def test_unknown_reuse_or_rank_cannot_silently_drop_samples():
    with pytest.raises(ValueError):
        assigned_rows([dict(item_id='a')], rank=0, reused={'b'})
    with pytest.raises(ValueError):
        assigned_rows([dict(item_id='a')], rank=4, reused=set())
