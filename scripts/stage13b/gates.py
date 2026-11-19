"""Only predeclared technical gates; never select calls using correctness."""
from collections import defaultdict
from scripts.stage13b.execution import ROOT,load,save,sha,now,shards
from scripts.stage13b.review import tasks,technical,technical_path,checked
from scripts.stage13b.protocol import missing_gate


def technical_gate():
    rows=tasks('technical');assert len(rows)==48
    cells=defaultdict(list);files={}
    for t in rows:
        g,checks=checked(t);a=technical(t['task_id'])
        assert all(checks.values()) and a['validity']['INPUT_VALID']
        cells[t['scale']+'_'+t['arm']].append(dict(task_id=t['task_id'],tokens=g['tokens'],cap_hit=g['cap_hit'],
            normal_stop=g['normal_stop'],scoreable=a['scoreable'],technical_valid=a['validity']['TECHNICALLY_VALID']))
        files[str(technical_path(t['task_id']))]=sha(technical_path(t['task_id']))
    assert len(cells)==12 and all(len(v)==4 for v in cells.values())
    # No numeric technical4 completion threshold is specified by the plan.
    # Scientific completion is governed by the explicit frozen8/24-call gate.
    save(ROOT/'audit/technical_gate.json',dict(at=now(),passed=True,n=48,cells=dict(cells),files=files,
        input_backend_checks_passed=True,correctness_used=False,numeric_completion_gate='Applied to frozen scientific8, not invented for technical4'))


def initial_gate(phase,cell):
    initial=set(load(ROOT/'stage13b_frozen48_manifest.json')['selection']['initial8'])
    selected=[t for t in tasks(phase,cell) if t['family_id'] in initial];assert len(selected)==24
    rows=[]
    for t in selected:
        checked(t);a=technical(t['task_id'])
        rows.append(dict(task_id=t['task_id'],technical_valid=a['validity']['TECHNICALLY_VALID'],
                         path=str(technical_path(t['task_id'])),sha256=sha(technical_path(t['task_id']))))
    missing=sum(not r['technical_valid'] for r in rows);passed=missing_gate(missing,24)
    save(ROOT/'audit/gates'/f'{cell}_initial8.json',dict(at=now(),n=24,technical_missing=missing,passed=passed,rows=rows,correctness_used=False))
    print(cell,'missing',missing,'/24; passed',passed)
    return passed


def prepare_tranche(phase,initial=True,nshards=1):
    assert phase in ['equal','image']
    first=set(load(ROOT/'stage13b_frozen48_manifest.json')['selection']['initial8'])
    chosen=[t for t in tasks(phase) if (t['family_id'] in first)==initial]
    label=phase+('_initial8' if initial else '_remaining40')
    if not initial:
        for cell in sorted({t['scale']+'_'+t['arm'] for t in tasks(phase)}):
            assert load(ROOT/'audit/gates'/f'{cell}_initial8.json')['passed']
    paths=shards(label,chosen,nshards)
    save(ROOT/'audit'/f'{label}_execution.json',dict(at=now(),phase=phase,initial=initial,tasks=chosen,manifests=paths))
    return paths
