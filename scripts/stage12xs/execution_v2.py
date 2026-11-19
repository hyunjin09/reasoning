"""Frozen finite-queue contracts for the amended Stage12X-S cohort."""
import hashlib
from pathlib import Path
from scripts.stage12xs.common import ALLOWED_NODES, load, save, sha, now

ROOT=Path('outputs/stage12xs/v2')
PREFIX='vr_stage12xs_v2_'
CAPS={'E':256,'N':32768,'O':32768,'C':32768,'T':81920,
      'RT_T':81920,'RT_I':32768,'Q_I':32768,'Q_T':81920,'SH_I':32768}

def native_seed(family):
    return int(hashlib.sha256(('stage12a-gen-v1|'+family).encode()).hexdigest()[:8],16)%(2**31)

def validate_tasks(tasks, ids, phase):
    assert phase in ['A','B','C'] and tasks
    arms={'A':set('ENO'),'B':set('CT'),'C':{'RT_T','RT_I','Q_I','Q_T','SH_I'}}[phase]
    assert len({t['task_id'] for t in tasks})==len(tasks)
    assert {t['item_id'] for t in tasks}==set(ids)
    assert phase!='B' or len(ids)<=24
    assert phase!='C' or 3<=len(ids)<=10
    for i in ids:
        rows=[t for t in tasks if t['item_id']==i]
        assert {t['arm'] for t in rows}==arms
        if phase=='C':
            assert len(rows)==25
            assert {(t['arm'],t['replicate']) for t in rows}=={(a,k) for a in arms for k in range(5)}
        else:assert len(rows)==len(arms)
    for t in tasks:
        assert t['cap']==CAPS[t['arm']]
        assert bool(t['image'])==(phase!='C' and t['arm']!='O')

def fingerprint(task):
    import json
    return hashlib.sha256(json.dumps(task,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def authorize(manifest):
    phase=manifest['phase'];full=load(ROOT/'audit'/f'phase{phase}_execution.json')
    assert manifest['config_sha256']==sha(ROOT/'config.json')
    validate_tasks(full['tasks'],full['ids'],phase)
    expected={r['task_id']:r for r in full['tasks']}
    assert manifest['rows'] and len({t['task_id'] for t in manifest['rows']})==len(manifest['rows'])
    assert all(t==expected.get(t['task_id']) for t in manifest['rows'])
    assert len({t['model_key'] for t in manifest['rows']})==1
    for p,h in load(ROOT/'audit/final_source_seal.json')['files'].items():assert sha(p)==h,p
    if phase in ['B','C']:
        gate=load(ROOT/'audit'/f'phase{phase}_authorization.json')
        assert gate['authorized'] and gate['execution_sha256']==sha(ROOT/'audit'/f'phase{phase}_execution.json')

