"""Exact frozen image-free inputs and finite Stage13A worker contracts."""
import hashlib,json
from pathlib import Path
from scripts.stage12xs.common import load,save,sha,now,ALLOWED_NODES

ROOT=Path('outputs/stage13a/v1')
OLD=Path('outputs/stage12xs/v2')
PREFIX='vr_stage13a_v1_'
CAPS={'I_EQ':32768,'T_EQ':81920,'T_32K':32768}
NAMES={'I':'Qwen/Qwen3-VL-4B-Instruct','T':'Qwen/Qwen3-VL-4B-Thinking'}

def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def seed(family,model,replicate):return int(hashlib.sha256(f'stage13a-v1|{family}|{NAMES[model]}|{replicate}'.encode()).hexdigest(),16)%(2**31)
def cohort():return load(ROOT/'stage13a_frozen96_manifest.json')['rows']

def task(row,model,replicate,phase='P'):
    arm=model+'_EQ' if phase=='P' else 'T_32K'
    assert phase=='P' or model=='T'
    return dict(task_id=f'{phase}_{arm}_{row["item_id"]}_r{replicate}',phase=phase,
        item_id=row['item_id'],family_id=row['family_id'],arm=arm,model_key=model,
        cap=CAPS[arm],prompt=row['prompts']['O'],prompt_version='stage12xs-frozen-oracle-stage13a-v1',
        image=None,image_sha256=None,seed=seed(row['family_id'],model,replicate),replicate=replicate)

def authorize(manifest):
    phase=manifest['phase'];assert phase in ['P','S']
    full=load(ROOT/'audit'/f'phase{phase}_execution.json')
    assert manifest['config_sha256']==sha(ROOT/'config.json')
    rows={r['item_id']:r for r in cohort()}
    expected={t['task_id']:t for t in full['tasks']}
    assert len(expected)==len(full['tasks'])==(576 if phase=='P' else 72)
    for t in full['tasks']:
        assert t==task(rows[t['item_id']],t['model_key'],t['replicate'],phase)
        assert t['replicate'] in range(3)
    assert manifest['rows'] and len({t['task_id'] for t in manifest['rows']})==len(manifest['rows'])
    assert all(t==expected.get(t['task_id']) for t in manifest['rows'])
    assert {t['model_key'] for t in manifest['rows']}=={manifest['model_key']}
    for p,h in load(ROOT/'stage13a_input_hashes.json')['files'].items():assert sha(p)==h,p
    if phase=='S':
        gate=load(ROOT/'audit/capmatched_authorization.json')
        assert gate['authorized'] and gate['execution_sha256']==sha(ROOT/'audit/phaseS_execution.json')

def shards(phase,tasks,n):
    paths=[]
    for model in sorted({t['model_key'] for t in tasks}):
        selected=[t for t in tasks if t['model_key']==model]
        for k in range(n):
            p=ROOT/'audit/manifests'/f'{phase}_{model}_{k}.json'
            save(p,dict(at=now(),phase=phase,model_key=model,config_sha256=sha(ROOT/'config.json'),rows=selected[k::n]))
            authorize(load(p));paths.append(str(p))
    return paths
