"""Separate immutable Stage14C-V execution namespace."""
from pathlib import Path
from scripts.stage14c.common import load,rows,sha,fingerprint,save,write_rows,now

ROOT=Path('outputs/stage14c_v_blindtest_validation')
PREFIX='vr_stage14cv_'
ALLOWED_NODES={'node02','node03','node06','node07'}


def tasks(panel):return rows(ROOT/'manifests'/f'{panel}_tasks.jsonl')
def folder(t,attempt=0):return ROOT/'raw'/t['collection']/t['task_id']/f'attempt_{attempt}'
def missing_path(t):return ROOT/'scoring/technical_missingness'/f"{t['task_id']}.json"


def checked(t):
    found=list((ROOT/'raw'/t['collection']/t['task_id']).glob('attempt_*/result.json'))
    assert len(found)<=1,('Duplicate result',t['task_id'])
    if not found:return None
    p=found[0];r=load(p)
    assert r['task_sha256']==fingerprint(t)
    assert sha(p.parent/'input.json')==r['input_sha256']
    assert sha(p.parent/'generation.json')==r['generation_sha256']
    assert not missing_path(t).exists()
    return p


def mark_missing(t,reason,evidence):
    assert checked(t) is None
    p=missing_path(t)
    if p.exists():
        assert load(p)['task_sha256']==fingerprint(t);return
    save(p,dict(at=now(),task_id=t['task_id'],task_sha256=fingerprint(t),
        status='TECHNICAL_MISSING',reason=reason,evidence=evidence,scientific_outcomes_used=False))


def authorize(m):
    approval=load(ROOT/'spec/g0_user_approval_v1.json');assert approval['hard_GPU_hours']==24
    version=2 if (ROOT/'audit/g1_source_and_execution_seal_v2.json').exists() else 1
    g1=load(ROOT/f'audit/g1_source_and_execution_seal_v{version}.json');assert g1['status']=='G1_PASS'
    for p,h in g1['files'].items():assert sha(p)==h,p
    expected={t['task_id']:t for t in tasks(m['panel'])}
    assert m['rows'] and len({t['task_id'] for t in m['rows']})==len(m['rows'])
    assert all(t==expected[t['task_id']] for t in m['rows'])
    assert {t['model_key'] for t in m['rows']}=={m['model_key']}
    if m['panel']!='technical':
        assert load(ROOT/'audit/g2_validation_v1.json')['status']=='PASS'
        assert len({t['condition'] for t in m['rows']})==1
    if m['panel']=='C':assert (ROOT/'audit/R_primary_seal_v1.json').exists()
