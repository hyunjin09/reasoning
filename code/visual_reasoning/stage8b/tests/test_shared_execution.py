import pytest
from visual_reasoning.stage8b.shared_execution import runtime_rank, assigned_rows, choose_layout


@pytest.mark.parametrize('per_gpu', [1, 2])
def test_two_gpu_layout_covers_125_once(per_gpu):
    rows = [dict(item_id=str(i)) for i in range(125)]
    ranks = [runtime_rank(dict(SLURM_JOB_ID='7', SLURM_PROCID=str(gpu), SLURM_NTASKS='2'),
                          visible_devices=1, allocation='7', lane=lane, workers_per_gpu=per_gpu)
             for gpu in range(2) for lane in range(per_gpu)]
    assert ranks == list(range(2*per_gpu))
    parts = [assigned_rows(rows, rank=r, workers=2*per_gpu) for r in ranks]
    assert sorted(int(row['item_id']) for part in parts for row in part) == list(range(125))
    assert max(map(len, parts))-min(map(len, parts)) == 1


@pytest.mark.parametrize('change,devices,lane', [({'SLURM_NTASKS':'4'},1,0), ({'SLURM_PROCID':'2'},1,0), ({},2,0), ({},1,2)])
def test_rejects_wrong_binding(change, devices, lane):
    env = dict(SLURM_JOB_ID='7', SLURM_PROCID='0', SLURM_NTASKS='2', **{})
    env.update(change)
    with pytest.raises(ValueError):
        runtime_rank(env, visible_devices=devices, allocation='7', lane=lane, workers_per_gpu=2)


def test_layout_requires_speed_memory_and_exactness():
    assert choose_layout(speedup=1.4, exact_parity=True, double_memory_gib=40, device_memory_gib=48) == 2
    assert choose_layout(speedup=1.01, exact_parity=True, double_memory_gib=40, device_memory_gib=48) == 1
    assert choose_layout(speedup=1.4, exact_parity=True, double_memory_gib=44, device_memory_gib=48) == 1
    with pytest.raises(ValueError):
        choose_layout(speedup=2, exact_parity=False, double_memory_gib=40, device_memory_gib=48)
