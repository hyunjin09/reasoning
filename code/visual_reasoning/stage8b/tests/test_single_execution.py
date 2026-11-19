import pytest
from visual_reasoning.stage8b.single_execution import runtime_rank, assigned_rows


def test_one_worker_keeps_every_frozen_item_in_order():
    rows = list(range(32))
    assert assigned_rows(rows, rank=0) == rows


def test_single_slurm_binding_is_required():
    env = dict(SLURM_JOB_ID='123', SLURM_PROCID='0', SLURM_NTASKS='1')
    assert runtime_rank(env, visible_devices=1, allocation='123') == 0
    for changes, devices in [({'SLURM_JOB_ID':'124'},1), ({'SLURM_NTASKS':'2'},1),
                             ({'SLURM_PROCID':'1'},1), ({},2)]:
        with pytest.raises(ValueError):
            runtime_rank(dict(env, **changes), visible_devices=devices, allocation='123')
    with pytest.raises(ValueError):
        assigned_rows(list(range(32)), rank=1)
