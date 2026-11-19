import pytest
from visual_reasoning.stage8b.block3a_tasks import assigned_tasks


def test_all_seeds_are_preserved_once_across_both_layouts():
    rows=[dict(item_id=str(i),seed=s,task_id=f'{i}_s{s}') for i in range(32) for s in range(1235,1239)]
    for workers in (2,4):
        chunks=[assigned_tasks(rows,rank=r,workers=workers) for r in range(workers)]
        assert len({x['task_id'] for chunk in chunks for x in chunk})==128
        assert sum(map(len,chunks))==128
    with pytest.raises(ValueError):assigned_tasks(rows+[rows[0]],rank=0,workers=4)
