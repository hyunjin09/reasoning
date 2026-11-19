"""The amended primary queue cannot include reserve or superseded conditions."""
import json
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path('outputs/stage9a_dynamics/amendment_v1')


def test_frozen_cohort_conditions_and_controls():
    selection=json.loads((ROOT/'stage9a_amended_family_selection.json').read_text())
    main={r['family_id'] for r in selection['main']};reserve={r['family_id'] for r in selection['reserve']}
    assert len(main)==len(reserve)==64 and not main&reserve
    assert len(selection['extension32'])==len(selection['final32'])==32
    tasks={r['task_id']:r for r in json.loads((ROOT/'audit/tasks.json').read_text())['rows']}
    assert len(tasks)==192 and {r['family_id'] for r in tasks.values()}==main
    manifest=json.loads((ROOT/'stage9a_amended_condition_manifest.json').read_text())
    assert not manifest['scientific_outcomes_accessed']
    counts=Counter(r['execution'] for r in manifest['rows'])
    assert counts==dict(run=1904,identity_native=234)
    assert len(manifest['deferred_control_rows'])==87 and manifest['distinct_continuations_main_plus_deferred_controls']==1991
    by=defaultdict(list)
    for r in manifest['rows']:by[r['task_id']].append(r)
    old=json.loads(Path('outputs/stage9a_dynamics/v1/audit/interventions.json').read_text())['rows']
    for task,rows in by.items():
        assert {r['cutoff'] for r in rows if r['assay']=='cumulative'}=={0,128,512,2048,None}
        windows=[r for r in rows if r['assay']=='local'];assert len(windows)==5
        assert [r['normalized_window'] for r in windows]==[[k/5,(k+1)/5] for k in range(5)]
        demand=[r for r in rows if r['assay']=='demand'];assert len(demand) in (0,2)
        if demand:
            assert len({r['event_id'] for r in demand})==1
            assert {r['role'] for r in demand}=={'demand','control'}
            assert all(r['radius']==16 and r['paired'] for r in demand)
            control=next(r for r in demand if r['role']=='control')['intervals'][0]
            assert control[1]-control[0]==33
            centers={r['demand_token'] for r in old if r['task_id']==task and r['assay']=='demand'}
            assert all(control[1]<=d-32 or control[0]>=d+33 for d in centers)
        assert all(r['assay']!='redistribution' for r in rows)
