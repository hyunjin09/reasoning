"""Technical identity gate. Does not load golds or evaluate scientific accuracy."""
import argparse
from scripts.stage14cv.common import *


def validate():
    cfg=load(ROOT/'spec/frozen_model_recipe.json');all_rows=tasks('technical')
    generations={};inputs={};files={}
    assert len(all_rows)==20
    for t in all_rows:
        path=checked(t);assert path,('Incomplete technical request',t['task_id'])
        g=load(path.parent/'generation.json');i=load(path.parent/'input.json')
        assert g['task_sha256']==fingerprint(t) and g['seed']==t['seed']
        assert g['sampling']==dict(cfg['models'][t['model_key']]['recipe'],max_tokens=t['cap'])
        assert (g['visual_tokens']>0)==bool(t['image_reference'])
        assert i['image_sha256']==t['image_sha256']
        assert g['finish_reason'] in {'stop','length'} and g['tokens']==len(g['generated_token_ids'])
        assert not g['cap_hit'] or g['tokens']==t['cap']
        assert i['messages'][0]['content'][-1]['text']==t['prompt']
        generations[t['task_id']]=g;inputs[t['task_id']]=i
        files.update({str(p):sha(p) for p in [path,path.parent/'input.json',path.parent/'generation.json']})
    replay=[]
    for model in 'IT':
        for condition in ['R0','R1','R2','C0','C1']:
            names=[f'G2_{model}_{r}_{condition}' for r in [0,1]]
            a,b=[generations[n] for n in names];ia,ib=[inputs[n] for n in names]
            assert ia['chat_prompt']==ib['chat_prompt'] and ia['prepared_image_pixel_sha256']==ib['prepared_image_pixel_sha256']
            assert a['prompt_token_ids']==b['prompt_token_ids']
            exact_prefix=a['generated_token_ids'][:128]==b['generated_token_ids'][:128]
            replay.append(dict(model=model,condition=condition,first128_or_shorter_exact=exact_prefix,
                whole_response_exact=a['generated_token_ids']==b['generated_token_ids'],tokens=[a['tokens'],b['tokens']],
                finish_reasons=[a['finish_reason'],b['finish_reason']],cap_hits=[a['cap_hit'],b['cap_hit']]))
    workers=[]
    for p in (ROOT/'audit/launches').glob('job_*.json'):
        j=load(p)
        if j.get('panel')!='technical':continue
        d=ROOT/'audit/workers'/str(j['job']['slurm_job_id'])
        assert (d/'exit.json').exists() and load(d/'exit.json')['complete']
        ready=list(d.glob('engines/*/ready.json'));assert len(ready)==2
        for p in ready:
            r=load(p);assert r['fixed_max_num_seqs']==18 and r['singleton']
        workers.append(str(j['job']['slurm_job_id']))
    assert len(workers)==2
    passed=all(r['first128_or_shorter_exact'] for r in replay)
    out=dict(at=now(),status='PASS' if passed else 'FAIL_HOLD',calls=20,max_calls=24,
        replay=replay,worker_jobs=workers,files=files,scientific_accuracy_inspected=False,
        scope='Fixed single-active request sequence in two fresh engines/model with18-sequence capacity; not universal cross-batch reproducibility.')
    dest=ROOT/'audit/g2_validation_v1.json';save(dest,out)
    print(out['status'],'20technical calls; exact prefix tests',sum(r['first128_or_shorter_exact'] for r in replay),'/10')
    assert passed,'Technical replay failed; no main launch'
    return out


def release_R():
    if (ROOT/'audit/g2_validation_v1.json').exists():assert load(ROOT/'audit/g2_validation_v1.json')['status']=='PASS'
    else:validate()
    from scripts.stage14cv.launch import launch
    # Finite approved R grid only. C still requires R scoring/primary seal.
    for model,hours in [('I',1),('T',3)]:
        for condition in ['R0','R1','R2']:
            existing=[load(p) for p in (ROOT/'audit/launches').glob('job_*.json')]
            if any(j.get('panel')=='R' and j.get('model')==model and j.get('condition')==condition for j in existing):continue
            launch('R',model,condition,hours,allow_pending=True)
    save(ROOT/'audit/R_release_v1.json',dict(at=now(),authorized_calls=1800,g2_sha256=sha(ROOT/'audit/g2_validation_v1.json'),
        C_launched=False,follow_on_launched=False,action='Finite R grid submitted; worker queues stop on exhaustion.'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release-R',action='store_true');a=p.parse_args()
    if a.release_R:release_R()
    else:validate()
