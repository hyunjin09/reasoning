import pytest
from visual_reasoning.stage8b.block3a_resume import runtime_rank, balanced_remaining


def test_four_gpu_binding_requires_one_visible_device_per_parent():
    ranks=[]
    for p in range(4):
        for lane in range(2):
            ranks.append(runtime_rank(dict(SLURM_JOB_ID='11',SLURM_NTASKS='4',SLURM_PROCID=str(p)),visible_devices=1,allocation='11',lane=lane,workers_per_gpu=2))
    assert ranks==list(range(8))
    with pytest.raises(ValueError):runtime_rank(dict(SLURM_JOB_ID='11',SLURM_NTASKS='2',SLURM_PROCID='0'),visible_devices=1,allocation='11',lane=0,workers_per_gpu=2)


def test_resume_exact_membership_and_seed_preservation():
    rows=[dict(task_id=f'{i}_s{s}',item_id=str(i),seed=s) for i in range(32) for s in range(1235,1239)]
    done={r['task_id'] for r in rows[:14]}
    remaining,loads=balanced_remaining(rows,done,{str(i):i+1 for i in range(32)})
    assert len(remaining)==114 and not done.intersection(r['task_id'] for r in remaining)
    assert {r['task_id'] for r in remaining}|done=={r['task_id'] for r in rows}
    assert {r['assigned_rank'] for r in remaining}==set(range(8))
    assert sum(loads)==sum(int(r['item_id'])+1 for r in remaining)
    assert max(loads)-min(loads)<=32
    with pytest.raises(ValueError):balanced_remaining(rows,{'unknown'},{str(i):i+1 for i in range(32)})
