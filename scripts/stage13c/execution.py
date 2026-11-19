"""Finite queues guarded by Stage13C's prospective source and validity seals."""
import json
from scripts.stage13c.common import *

def fingerprint(value):return digest(json.dumps(value,sort_keys=True,ensure_ascii=False))

def authorize(manifest):
    assert manifest['config_sha256']==sha(manifest.get('config_path',ROOT/'config.json'))
    source=ROOT/('audit/technical_buffer_tasks.json' if manifest['phase']=='technical_buffer' else 'stage13c_seed_manifest.json')
    expected={t['task_id']:t for t in load(source)['tasks']}
    assert manifest['rows'] and len({t['task_id'] for t in manifest['rows']})==len(manifest['rows'])
    assert all(t==expected.get(t['task_id']) for t in manifest['rows'])
    assert {t['model_key'] for t in manifest['rows']}=={manifest['model_key']}
    if manifest['phase'].startswith('scientific'):
        assert load(ROOT/'stage13c_forced_trace_technical_validation.json')['passed']
        for t in manifest['rows']:
            if not t['initial8']:
                assert load(ROOT/'audit/gates'/f"{t['condition']}_initial8.json")['passed']

def shards(label,tasks,n=1,config_path=None):
    config_path=str(config_path or ROOT/'config.json')
    paths=[]
    for model in sorted({t['model_key'] for t in tasks}):
        selected=[t for t in tasks if t['model_key']==model]
        for k in range(n):
            rows=selected[k::n]
            if not rows:continue
            p=ROOT/'audit/manifests'/f'{label}_{model}_{k}.json'
            save(p,dict(at=now(),phase=rows[0]['phase'],model_key=model,config_path=config_path,config_sha256=sha(config_path),rows=rows))
            authorize(load(p));paths.append(str(p))
    return paths
