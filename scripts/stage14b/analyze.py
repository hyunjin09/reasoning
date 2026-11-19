"""Stage14B primary seal before predeclared source sensitivities; no launches."""
import argparse
from collections import Counter,defaultdict
import numpy as np
from scripts.stage14b.common import *
from scripts.stage14b.scoring import final_score,final_extraction,metadata
from scripts.stage14b.inference_math import paired,rescue,ratio_bootstrap,DRAWS,SEED
from scripts.stage14b.protocol import VERSIONS


def scored(mode):
    for model in 'IT':
        seal=load(ROOT/'audit'/f'{mode}_{model}_scoring_seal.json')
        for tid,h in seal['scores'].items():assert fingerprint(final_score(tid))==h,tid
    rr=[]
    for t in all_tasks(mode):
        s=final_score(t['task_id']);x=final_extraction(t['task_id']);meta=metadata(t);p=checked_result(t)
        g=load(p.parent/'generation.json') if p else {}
        rr.append(dict(task_id=t['task_id'],identity=t['identity'],family_id=t['family_id'],item_id=t['item_id'],
            model=t['model_key'],condition=t['condition'],version=t['source_version'],replicate=t['replicate'],
            correct=s['correct'],status=s['status'],answer=x['answer'],source_metadata=meta,
            tokens=g.get('tokens'),cap_hit=g.get('cap_hit'),finish_reason=g.get('finish_reason'),
            latency_seconds=g.get('request_latency_seconds'),answer_chars=len(x['answer']) if x['answer'] else None,
            generation_sha256=sha(p.parent/'generation.json') if p else None))
    return rr


def pairs(records,condition,ids=None,version=None):
    d=defaultdict(dict)
    for r in records:
        if r['condition']!=condition or (ids is not None and r['identity'] not in ids) or (version is not None and r['version']!=version):continue
        key=(r['identity'],r['replicate']);d[key][r['model']]=r
    result=[]
    for key,arms in d.items():
        assert set(arms)==set('IT')
        result.append(dict(identity=key[0],replicate=key[1],family_id=arms['I']['family_id'],I=arms['I']['correct'],T=arms['T']['correct']))
    return result


def transitions(records,model):
    d=defaultdict(dict)
    eids={r['identity'] for r in records if r['condition']=='evidence'}
    for r in records:
        if r['model']==model and r['identity'] in eids:d[r['identity'],r['replicate']][r['condition']]=r
    result=[];table=Counter()
    for (ident,rep),arms in d.items():
        assert set(arms)=={'image','evidence'}
        a,b=arms['image'],arms['evidence'];table[a['status']+'__'+b['status']]+=1
        result.append(dict(identity=ident,replicate=rep,family_id=a['family_id'],native=a['correct'],equal=b['correct']))
    return result,dict(table)


def verse_profile(records,clean=False):
    rr=[r for r in records if r['version'] and (not clean or r['source_metadata']['clean_paired'])]
    profile={v:paired(pairs(rr,'native',version=v)) for v in VERSIONS}
    byfamily=defaultdict(dict)
    for r in rr:byfamily[r['family_id'],r['replicate']][r['model'],r['version']]=r['correct']
    vals=[];families=[]
    for key,arms in byfamily.items():
        required=[(m,v) for m in 'IT' for v in ('Vision Dominant','Vision Only','Text Dominant','Text Lite')]
        if all(arms.get(k) is not None for k in required):
            delta={v:int(arms['T',v])-int(arms['I',v]) for v in ('Vision Dominant','Vision Only','Text Dominant','Text Lite')}
            vals.append((delta['Vision Dominant']+delta['Vision Only']-delta['Text Dominant']-delta['Text Lite'])/2);families.append(key[0])
    return dict(versions=profile,profile_contrast=ratio_bootstrap(vals,[1]*len(vals)),
        contrast_complete_families=len(vals),contrast_total_families=len(byfamily),contrast_family_ids=families,
        clean_only=clean,interpretation='Descriptive modality profile; no mechanism claim')


def primary():
    rr=scored('main');assert len(rr)==17536
    mv=[r for r in rr if r['identity'].startswith('mv:')]
    native=pairs(mv,'image');eq=pairs(mv,'evidence');res,table=transitions(mv,'I')
    assert (len(native),len(eq),len(res))==(3040,1000,1000)
    p1=paired(native);p2=rescue(res);p3=paired(eq);p4=verse_profile(rr)
    output=dict(at=now(),P1_G_img=p1,P2_R_I=p2,P3_G_post=p3,P4_mathverse=p4,
        primary_hypothesis_family=load(ROOT/'spec/frozen_run_config.json')['stats']['primary'],
        four_way_counts={c:dict(Counter(r['status'] for r in rr if r['condition']==c)) for c in ['image','evidence','native']},
        counts_by_arm={m+'_'+c:dict(Counter(r['status'] for r in rr if r['condition']==c and r['model']==m)) for m in 'IT' for c in ['image','evidence','native']},
        precision='Percentage-point paired effects; known-family clusters; unadjusted95% intervals',
        interpretation_limit='Variants under native validated recipes. Evidence rescue is not pure perception; no downstream mechanism identified.')
    write_rows(ROOT/'scoring/scored_outputs.jsonl',rr)
    write_rows(ROOT/'scoring/answer_extraction.jsonl',[final_extraction(r['task_id']) for r in rr])
    write_rows(ROOT/'scoring/technical_missingness.jsonl',[r for r in rr if r['status']=='TECHNICAL_MISSING'])
    save(ROOT/'analysis/primary_results.json',output)
    save(ROOT/'analysis/transition_tables.json',dict(I_native_to_evidence=table,native_model_pairs=p1['paired_transitions'],equal_model_pairs=p3['paired_transitions']))
    save(ROOT/'analysis/bootstrap_results.json',dict(draws=DRAWS,seed=SEED,P1=p1['item'],P2=p2['bootstrap'],P3=p3['item'],P4=p4['profile_contrast']))
    save(ROOT/'analysis/family_cluster_sensitivity.json',dict(P1_cluster=p1['cluster'],P1_family_equal=p1['family_equal'],P3_cluster=p3['cluster'],P3_family_equal=p3['family_equal']))
    save(ROOT/'analysis/mathverse_modality_profile.json',p4)
    paths=list((ROOT/'analysis').glob('*.json'))+list((ROOT/'scoring').glob('*.jsonl'))
    save(ROOT/'audit/primary_analysis_seal.json',dict(at=now(),files={str(p):sha(p) for p in paths},secondary_inspected=False))
    print('Primary analysis sealed; no secondary narratives opened.')


def secondary():
    seal=load(ROOT/'audit/primary_analysis_seal.json')
    for p,h in seal['files'].items():assert sha(p)==h
    rr=rows(ROOT/'scoring/scored_outputs.jsonl');mv=[r for r in rr if r['identity'].startswith('mv:')]
    res,table=transitions(mv,'T');out=dict(at=now(),Thinking_rescue=rescue(res),Thinking_transition_four_way=table,
        mathverse_clean_profile=verse_profile(rr,clean=True),strata={})
    # Frozen source strata only; no performance-driven cohorts.
    for field in ('answer_type','difficulty','subject','has_structured_atom','num_e_star_atoms','source_validity_status'):
        values=sorted({str(r['source_metadata'][field]) for r in rr if field in r['source_metadata']})
        out['strata'][field]={}
        for value in values:
            selected=[r for r in rr if field in r['source_metadata'] and str(r['source_metadata'][field])==value]
            estimates={}
            for condition in sorted({r['condition'] for r in selected}):
                # Never mix six MathVerse versions as independent pairs.
                versions=VERSIONS if condition=='native' else [None]
                for version in versions:
                    pp=pairs(selected,condition,version=version)
                    if pp:estimates[condition+(':'+version if version else '')]=paired(pp)
            out['strata'][field][value]=estimates
    # Known MathVerse cross-ID repeats as conservative cluster sensitivity.
    vf=stage14a('mathverse788_family_manifest')['rows'];parent={r['family_id']:r['family_id'] for r in vf}
    def find(x):
        while parent[x]!=x:x=parent[x]
        return x
    for group in load(ROOT/'audit/source_clean_layer.json')['known_repeat_groups']:
        ids=['mathverse:testmini:'+str(i) for i in group['problem_indices']]
        for item in ids[1:]:parent[find(item)]=find(ids[0])
    adjusted=[dict(r,family_id=find(r['family_id'])) if r['version'] else r for r in rr]
    out['mathverse_repeat_cluster_profiles']={v:paired(pairs(adjusted,'native',version=v)) for v in VERSIONS}
    out['technical_diagnostics']={}
    for model in 'IT':
        for condition in ('image','evidence','native'):
            ss=[r for r in rr if r['model']==model and r['condition']==condition];tokens=[r['tokens'] for r in ss if r['tokens'] is not None]
            out['technical_diagnostics'][model+'_'+condition]=dict(n=len(ss),labels=dict(Counter(r['status'] for r in ss)),cap_hits=sum(r['cap_hit'] is True for r in ss),
                generated_tokens_median=float(np.median(tokens)) if tokens else None,generated_tokens_iqr=np.quantile(tokens,[.25,.75]).tolist() if tokens else None,
                generated_tokens_max=max(tokens) if tokens else None)
    save(ROOT/'analysis/secondary_results.json',out)
    save(ROOT/'audit/secondary_analysis_seal.json',dict(at=now(),file=str(ROOT/'analysis/secondary_results.json'),sha256=sha(ROOT/'analysis/secondary_results.json'),primary_sha256=sha(ROOT/'audit/primary_analysis_seal.json')))
    print('Secondary analysis sealed; confirmation now permitted by frozen worker gate.')


def confirmation():
    assert (ROOT/'audit/secondary_analysis_seal.json').exists()
    fresh=scored('confirmatory');assert len(fresh)==9600
    mv_ids={r['identity'] for r in rows(ROOT/'manifests/confirm300_mathvision.jsonl')}
    v_ids={r['identity'] for r in rows(ROOT/'manifests/confirm300_mathverse.jsonl')}
    original=[r for r in rows(ROOT/'scoring/scored_outputs.jsonl') if r['identity'] in mv_ids|v_ids]
    assert len(original)==4800
    per_seed={}
    for rep in range(3):
        ss=[r for r in original+fresh if r['replicate']==rep];mv=[r for r in ss if r['identity'].startswith('mv:')]
        res,tab=transitions(mv,'I')
        per_seed[str(rep)]=dict(G_img=paired(pairs(mv,'image')),R_I=rescue(res),G_post=paired(pairs(mv,'evidence')),mathverse=verse_profile(ss),transitions=tab)
    primary_result=load(ROOT/'analysis/primary_results.json')
    endpoints={'G_img':([s['G_img']['paired_difference_pp'] for s in per_seed.values()],primary_result['P1_G_img']['paired_difference_pp']),
        'G_post':([s['G_post']['paired_difference_pp'] for s in per_seed.values()],primary_result['P3_G_post']['paired_difference_pp']),
        'R_I':([s['R_I']['bootstrap']['estimate_pp'] for s in per_seed.values()],primary_result['P2_R_I']['bootstrap']['estimate_pp']),
        'MathVerse_profile':([s['mathverse']['profile_contrast']['estimate_pp'] for s in per_seed.values()],primary_result['P4_mathverse']['profile_contrast']['estimate_pp'])}
    for v in VERSIONS:
        endpoints['MathVerse_'+v]=([s['mathverse']['versions'][v]['paired_difference_pp'] for s in per_seed.values()],primary_result['P4_mathverse']['versions'][v]['paired_difference_pp'])
    stability={}
    for endpoint,(values,reference) in endpoints.items():
        resolved=[x for x in values if x is not None]
        stability[endpoint]=dict(values_pp=values,mean_pp=float(np.mean(resolved)) if resolved else None,sd_pp=float(np.std(resolved,ddof=1)) if len(resolved)>1 else None,
            primary_reference_pp=reference,sign_stability_fraction=sum(np.sign(v)==np.sign(reference) for v in resolved)/len(resolved) if resolved and reference is not None else None)
    byslot=defaultdict(list);patterns=defaultdict(dict)
    for r in original+fresh:
        byslot[r['identity'],r['condition'],r['model']].append(r['correct'])
        patterns[r['identity'],r['condition']].setdefault(r['replicate'],{})[r['model']]=r['correct']
    resolved_patterns=[]
    for value in patterns.values():
        assert set(value)=={0,1,2} and all(set(v)==set('IT') for v in value.values())
        if all(v[m] is not None for v in value.values() for m in 'IT'):
            resolved_patterns.append([tuple(value[rep][m] for m in 'IT') for rep in range(3)])
    transition_stability=dict(slots=len(byslot),all_three_resolved=sum(None not in v for v in byslot.values()),
        identical_binary_all_seeds=sum(None not in v and len(set(v))==1 for v in byslot.values()),unknown_any_seed=sum(None in v for v in byslot.values()),
        paired_model_patterns_total=len(patterns),paired_model_patterns_all_seeds_resolved=len(resolved_patterns),
        paired_model_patterns_stable_all_seeds=sum(len(set(v))==1 for v in resolved_patterns))
    save(ROOT/'analysis/confirmatory_results.json',dict(at=now(),per_seed=per_seed,stability=stability,transition_stability=transition_stability,
        caveat='Fixed source-selected robustness subsets; not independent untouched confirmation. Seed0 reused exactly.'))
    write_rows(ROOT/'scoring/confirmatory_scored_outputs.jsonl',fresh)
    save(ROOT/'audit/confirmation_analysis_seal.json',dict(at=now(),sha256=sha(ROOT/'analysis/confirmatory_results.json')))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['primary','secondary','confirmation']);a=p.parse_args()
    {'primary':primary,'secondary':secondary,'confirmation':confirmation}[a.phase]()
