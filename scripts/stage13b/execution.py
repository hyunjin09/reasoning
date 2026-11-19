"""Frozen tasks, phase gates and finite worker contracts for Stage13B."""
import hashlib,json
from pathlib import Path
from scripts.stage12xs.common import load,save,sha,now,ALLOWED_NODES

ROOT=Path('outputs/stage13b/v1')
OLD=Path('outputs/stage12xs/v2')
PREFIX='vr_stage13b_v1_'
CAPS={'I_img':32768,'I_EQ':32768,'T_img':81920,'T_EQ':81920}


def fingerprint(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def task(row,scale,model,condition,replicate,phase):
    arm=model+'_'+condition
    namespace='stage13b-v1' if phase!='technical' else 'stage13b-v1-technical'
    seedtext=f'{namespace}|{scale}|{row["family_id"]}|{arm}|{replicate}'
    return dict(task_id=f'{phase}_{scale}_{arm}_{row["item_id"]}_r{replicate}',phase=phase,scale=scale,
        item_id=row['item_id'],family_id=row['family_id'],arm=arm,model_key=scale+'_'+model,mode=model,
        cap=CAPS[arm],prompt=row['prompts']['O' if condition=='EQ' else 'N'],
        prompt_version='stage12xs-frozen-oracle' if condition=='EQ' else 'original-native-question',
        image=None if condition=='EQ' else row['image'],image_sha256=None if condition=='EQ' else row['image_sha256'],
        seed=int(hashlib.sha256(seedtext.encode()).hexdigest(),16)%(2**31),seed_string=seedtext,replicate=replicate)


def authorize(manifest):
    assert manifest['config_sha256']==sha(ROOT/'config.json')
    full=load(ROOT/'stage13b_seed_manifest.json')
    expected={t['task_id']:t for t in full['new_scientific']+full['technical']}
    assert manifest['rows'] and len({t['task_id'] for t in manifest['rows']})==len(manifest['rows'])
    assert all(t==expected.get(t['task_id']) for t in manifest['rows'])
    assert {t['model_key'] for t in manifest['rows']}=={manifest['model_key']}
    assert {t['phase'] for t in manifest['rows']}=={manifest['phase']}
    for p,h in load(ROOT/'stage13b_input_hashes.json')['files'].items():assert sha(p)==h,p
    if manifest['phase']!='technical':
        assert load(ROOT/'audit/technical_gate.json')['passed']
        initial=set(load(ROOT/'stage13b_frozen48_manifest.json')['selection']['initial8'])
        for t in manifest['rows']:
            if t['family_id'] not in initial:
                assert load(ROOT/'audit/gates'/f"{t['scale']}_{t['arm']}_initial8.json")['passed']
        if manifest['phase']=='image':assert load(ROOT/'audit/phase2_compute_gate.json')['authorized']


def shards(label,tasks,n=1):
    paths=[]
    for model in sorted({t['model_key'] for t in tasks}):
        selected=[t for t in tasks if t['model_key']==model]
        for k in range(n):
            rows=selected[k::n]
            if not rows:continue
            p=ROOT/'audit/manifests'/f'{label}_{model}_{k}.json'
            save(p,dict(at=now(),label=label,phase=rows[0]['phase'],model_key=model,
                        config_sha256=sha(ROOT/'config.json'),rows=rows))
            authorize(load(p));paths.append(str(p))
    return paths
