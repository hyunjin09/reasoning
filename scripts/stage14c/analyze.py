"""Frozen cross-task estimands; primary analysis precedes diagnostic interpretation."""
from collections import defaultdict
from scripts.stage14c.common import *
from scripts.stage14c.design_core import panel,contrast
from scripts.stage14c.scoring import final_score

def public(x):return {k:v for k,v in x.items() if not k.startswith('_')}

def assemble_new():
    for m in 'IT':
        for tid,h in load(ROOT/'audit'/f'main_{m}_scoring_seal.json')['scores'].items():assert fingerprint(final_score(tid))==h
    metadata={r['family_id']:r for r in rows(ROOT/'source/cohort_manifest.jsonl')}
    data={fid:dict(family_id=fid,item_id=r['item_id'],benchmark=r['benchmark'],category=r['category']) for fid,r in metadata.items()}
    for t in all_tasks('main'):
        field=t['model_key']+('_img' if t['condition']=='native' else '_E')
        assert field not in data[t['family_id']]
        data[t['family_id']][field]=final_score(t['task_id'])['status']
    assert len(data)==1714
    return list(data.values())

def anchor():
    for p,h in load(ROOT/'audit/parent_artifact_hashes_v1.json')['files'].items():assert sha(p)==h,p
    original=load('outputs/stage14b/audit/primary_analysis_seal.json')
    scored=Path('outputs/stage14b/scoring/scored_outputs.jsonl');assert sha(scored)==original['files'][str(scored)]
    cfg=load(ROOT/'spec/model_and_recipe_identity.json');old=load('outputs/stage14b/spec/frozen_run_config.json')
    for key in ['models','runtime','environment']:assert cfg[key]==old[key],key
    rr=[r for r in rows(scored) if r['identity'].startswith('mv:')]
    data={}
    for r in rr:
        assert r['replicate']==0
        ident=r['identity'];d=data.setdefault(ident,dict(family_id=r['family_id'],item_id=r['item_id'],benchmark='math'))
        field=r['model']+('_img' if r['condition']=='image' else '_E');assert field not in d;d[field]=r['status']
    assert len(data)==3040 and sum('I_E' in d for d in data.values())==1000
    return list(data.values()),dict(parent_scored_sha256=sha(scored),models_runtime_environment_exact=True,
        prompts_seeds_raw_and_scores='Existing Stage14B immutable reference condition reused verbatim; new benchmark seeds differ by family as specified.',
        external_anchor=True,independent_new_math_replication=False,math_reruns=0,math_regrades=0)

def task_panels(data,name):
    e=[r for r in data if 'I_E' in r]
    return dict(native_all=panel(data,'I_img','T_img',stream=name+'|native_all'),
        native_eligible=panel(e,'I_img','T_img',stream=name+'|native_eligible'),
        post=panel(e,'I_E','T_E',stream=name+'|post'),
        I_supply=panel(e,'I_img','I_E',stream=name+'|I_supply'),
        T_supply=panel(e,'T_img','T_E',stream=name+'|T_supply'))

def main():
    new=assemble_new();math,identity=anchor();data=new+math
    results={b:task_panels([r for r in data if r['benchmark']==b],b) for b in ['math','MMStar','BlindTest']}
    contrasts={}
    for key,bench,endpoint in [('C1','MMStar','rescue'),('C2','BlindTest','rescue'),('C3','MMStar','difference'),('C4','BlindTest','difference')]:
        field='I_supply' if endpoint=='rescue' else 'post'
        contrasts[key]=dict(benchmark=bench,**contrast(results['math'][field],results[bench][field],endpoint))
    save(ROOT/'audit/condition_identity_audit.json',dict(at=now(),**identity))
    write_rows(ROOT/'scoring/scored_outcomes.jsonl',data)
    save(ROOT/'analysis/primary_results.json',dict(at=now(),tasks={b:{k:public(v) for k,v in p.items()} for b,p in results.items()},
        interpretation='Eligible-stratum oracle-supply responsiveness and variant gaps; not pure perception/reasoning partition or causal task-type effect.'))
    save(ROOT/'analysis/cross_task_contrasts.json',contrasts)
    save(ROOT/'analysis/complete_pair_transitions.json',{b:{k:v['transitions'] for k,v in ps.items()} for b,ps in results.items()})
    save(ROOT/'analysis/missingness_bounds.json',{b:{k:dict(difference=v['difference_bounds_pp'],rescue=v['rescue']['bounds_pp']) for k,v in ps.items()} for b,ps in results.items()})
    save(ROOT/'analysis/family_cluster_bootstrap.json',dict(draws=10000,master_seed=120220260929,family_equal=True,streams={b:{k:v['stream'] for k,v in ps.items()} for b,ps in results.items()},multiplicity='Unadjusted95% intervals; no familywise-significance claim'))
    paths=list((ROOT/'analysis').glob('*.json'))+[ROOT/'scoring/scored_outcomes.jsonl',ROOT/'audit/condition_identity_audit.json']
    save(ROOT/'audit/primary_analysis_seal.json',dict(at=now(),files={str(p):sha(p) for p in paths},secondary_or_D1_interpreted=False))
    print('Primary analysis sealed.')

if __name__=='__main__':main()
