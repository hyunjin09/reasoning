"""Frozen inventory invariants independent of model outcomes."""
import json
from collections import Counter, defaultdict
from pathlib import Path


def test_complete_frozen_support():
    root=Path('outputs/stage9a_dynamics/v1/audit')
    tasks=json.loads((root/'tasks.json').read_text())['rows']
    manifest=json.loads((root/'interventions.json').read_text());rows=manifest['rows']
    assert len(tasks)==384 and len({r['family_id'] for r in tasks})==128
    assert manifest['frozen'] and not manifest['selection_uses_scientific_outcomes']
    assert Counter(r['assay'] for r in rows)==dict(cumulative=384*11,local=384*10,demand=539*4,redistribution=351)
    assert len({r['event_id'] for r in rows if r['assay']=='demand'})==539
    by_task=defaultdict(list)
    for r in rows:by_task[r['task_id']].append(r)
    for task in tasks:
        local=[r for r in by_task[task['task_id']] if r['assay']=='local']
        all_intervals=[i for r in local for i in r['intervals']]
        assert all(a>=1 and b>a for a,b in all_intervals)
        assert all(a[1]<=b[0] for a,b in zip(all_intervals,all_intervals[1:]))
        demand={r['condition_id']:r for r in by_task[task['task_id']] if r['assay']=='demand'}
        centers={r['demand_token'] for r in demand.values()}
        for r in demand.values():
            if r['role']!='control' or not r['paired']:continue
            d=demand[r['condition_id'].replace('_control','_demand')]
            a,b=r['intervals'][0];x,y=d['intervals'][0]
            assert b-a==y-x
            assert all(b<=c-32 or a>=c+33 for c in centers)
