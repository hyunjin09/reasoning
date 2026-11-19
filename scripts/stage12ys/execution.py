"""Finite immutable Stage12Y-S queues and exact reused-input contracts."""
from pathlib import Path
from scripts.stage12xs.common import load,save,sha,now,ALLOWED_NODES
from scripts.stage12ys.protocol import CAPS,ARMS,seed
from scripts.stage12xs.execution_v2 import fingerprint

ROOT=Path('outputs/stage12ys/v1')
OLD=Path('outputs/stage12xs/v2')
PREFIX='vr_stage12ys_v1_'

def cohort():return load(ROOT/'stage12ys_frozen96_manifest.json')['rows']

def task(row,arm,phase,replicate):
    key='E' if arm.startswith('E_') else 'N' if arm.endswith('_img') else 'O'
    model='T' if arm in ('E_T','T_img','T_E','RT_T') else 'I'
    image=key!='O' and phase!='C'
    return dict(task_id=f'{phase}_{arm}_{row["item_id"]}_r{replicate}',phase=phase,
        item_id=row['item_id'],family_id=row['family_id'],arm=arm,model_key=model,
        cap=CAPS[arm],prompt=row['prompts'][key],prompt_version='stage12xs-frozen-inputs-stage12ys-v1',
        image=row['image'] if image else None,image_sha256=row['image_sha256'] if image else None,
        seed=seed(row['family_id'],arm,replicate,phase),replicate=replicate)

def validate_tasks(tasks,ids,phase):
    assert phase in 'ABC' and tasks
    assert len({t['task_id'] for t in tasks})==len(tasks)
    assert {t['item_id'] for t in tasks}==set(ids)
    rows={r['item_id']:r for r in cohort()}
    for t in tasks:
        base=task(rows[t['item_id']],t['arm'],phase,t['replicate'])
        assert all(t[k]==v for k,v in base.items()),t['task_id']
        assert t['replicate'] in range({'A':1,'B':3,'C':5}[phase])
        assert t['arm'] in ({'E_T','T_img','T_E'} if phase=='A' else set(ARMS) if phase=='B' else {'RT_T','RT_I','Q_I','SH_I'})
        if phase=='C':assert 'prefix' in t and not t['image']
    if phase=='A':
        assert len(ids)==96 and len(tasks)==288
        for i in ids:assert {t['arm'] for t in tasks if t['item_id']==i}=={'E_T','T_img','T_E'}
    elif phase=='B':
        assert len(ids)<=32
        for i in ids:
            for a in {t['arm'] for t in tasks if t['item_id']==i}:
                assert {t['replicate'] for t in tasks if t['item_id']==i and t['arm']==a}==set(range(3))
    else:
        assert 2<=len(ids)<=10 and len(tasks)==20*len(ids)

def authorize(manifest):
    phase=manifest['phase'];full=load(ROOT/'audit'/f'phase{phase}_execution.json')
    assert manifest['config_sha256']==sha(ROOT/'config.json')
    validate_tasks(full['tasks'],full['ids'],phase)
    expected={t['task_id']:t for t in full['tasks']}
    assert manifest['rows'] and len({t['task_id'] for t in manifest['rows']})==len(manifest['rows'])
    assert all(t==expected.get(t['task_id']) for t in manifest['rows'])
    assert {t['model_key'] for t in manifest['rows']}=={manifest['model_key']}
    for p,h in load(ROOT/'audit/input_seal.json')['files'].items():assert sha(p)==h,p
    if phase!='A':
        gate=load(ROOT/'audit'/f'phase{phase}_authorization.json')
        assert gate['authorized'] and gate['execution_sha256']==sha(ROOT/'audit'/f'phase{phase}_execution.json')

def shards(phase,tasks,n):
    paths=[]
    for model in sorted({t['model_key'] for t in tasks}):
        selected=[t for t in tasks if t['model_key']==model]
        for k in range(min(n,len(selected))):
            p=ROOT/'audit/manifests'/f'{phase}_{model}_{k}.json'
            save(p,dict(at=now(),phase=phase,model_key=model,config_sha256=sha(ROOT/'config.json'),rows=selected[k::n]))
            authorize(load(p));paths.append(str(p))
    return paths
