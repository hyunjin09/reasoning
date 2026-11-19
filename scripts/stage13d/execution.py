from scripts.stage13d.common import *
def authorize(m):
    assert m['config_sha256']==sha(m.get('config_path',ROOT/'config.json'))
    phase=m['phase']
    source=ROOT/('stage13d_semantic_seed_manifest.json' if phase.startswith('semantic') else 'stage13d_buffer_forced_sequences.json')
    expected={t['task_id']:t for t in load(source)['tasks']}
    assert m['rows'] and len({t['task_id'] for t in m['rows']})==len(m['rows'])
    assert all(t==expected.get(t['task_id']) and t['phase']==phase for t in m['rows'])
    assert {t['model_key'] for t in m['rows']}=={m['model_key']}
    if phase=='semantic_remaining':assert load(ROOT/'audit/semantic_initial8_gate.json')['passed']
    if phase=='scientific_buffer':assert load(ROOT/'stage13d_buffer_technical_validation.json')['passed']
def shards(label,tasks,n=1):
    paths=[]
    for model in sorted({t['model_key'] for t in tasks}):
        selected=[t for t in tasks if t['model_key']==model]
        for k in range(n):
            rows=selected[k::n]
            if not rows:continue
            p=ROOT/'audit/manifests'/f'{label}_{model}_{k}.json'
            save(p,dict(at=now(),phase=rows[0]['phase'],model_key=model,config_path=str(ROOT/'config.json'),config_sha256=sha(ROOT/'config.json'),rows=rows))
            authorize(load(p));paths.append(str(p))
    return paths
