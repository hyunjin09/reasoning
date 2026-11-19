"""Offline analysis only after all scientific generation and source-query review freeze."""
import csv
import json
from pathlib import Path
import numpy as np
from scripts.stage14d1_pilot.common import *
from scripts.stage14d1.contracts import ARMS
from scripts.stage14d1.scoring import score
from scripts.stage14d1_pilot.statistics import bootstrap_indices,paired_summary,interval


def main():
    design=load(P/'manifests/main_design.json')
    query_review=load(P/'annotations/query_review_complete.json')
    assert query_review['families']==72 and query_review['final_answers_hidden']
    source={r['item_id']:r for r in rows('outputs/stage14b/manifests/mathvision_3040_eval_manifest.jsonl')}
    original={r['family_id']:r for r in rows(P/'inference/families.jsonl')}
    offline={r['family_id']:r for r in rows(P/'data/offline_source_manifest.jsonl')}
    states={};files={}
    for attempt in design['attempts']:
        root=P/'raw'/attempt
        assert load(root/'exit.json')['status']=='COMPLETE'
        for path in sorted((root/'states').glob('*.json')):
            s=load(path);assert s['family_id'] not in states
            states[s['family_id']]=s;files[str(path)]=sha(path)
            for pathstr in set(s['continuation_paths'].values()):
                gpath=Path(pathstr);receipt=load(gpath.parent/'result.json');inp=load(gpath.parent/'input.json')
                assert inp['kind']=='solver' and inp['cap']==81920
                assert sha(gpath)==receipt['generation_sha256'] and sha(gpath.parent/'input.json')==receipt['input_sha256']
                for p in (gpath,gpath.parent/'input.json',gpath.parent/'result.json'):files[str(p)]=sha(p)
    assert set(states)==set(original) and len(states)==72
    save(P/'audit/scientific_generation_freeze.json',dict(at=now(),families=72,logical_slots=432,files=files))
    result=[];cache={}
    for family in sorted(states):
        s=states[family];r=original[family];ref=source[r['item_id']]
        for arm in ARMS:
            path=s['continuation_paths'][arm];g=load(path)
            if path not in cache:
                cache[path]=score(r['prefix']+g['raw_decoded_response'],g['finish_reason'],ref['options'],ref['gold_answer'])
            scored=cache[path]
            result.append(dict(family_id=family,item_id=r['item_id'],arm=arm,
                source_stratum=offline[family]['source_stratum'],context_stratum=offline[family]['audit_context_stratum'],
                generation_path=path,physical_id=g['id'],logical_alias=g['id']!=r['item_id']+'_'+arm,
                query_valid=s['query_valid'],query_status=(s['query'] or {}).get('status'),address_valid=s['address_valid'],
                read_alias=s['read_aliases'].get(arm),crop_count=len(s['views']['paths'])-1,
                query_generation=s['query_generation'],locator_generation=s['locator_generation'],
                read_generation=s.get('readouts',{}).get(arm,{}).get('generation_path'),
                tokens=g['tokens'],cap_hit=g['cap_hit'],finish_reason=g['finish_reason'],latency_seconds=g['latency_seconds'],
                answer=scored['answer'],extraction_status=scored['status'],final_status=scored['final_status'],correct=scored['correct'],
                extraction_method=scored.get('method'),gold_answer=ref['gold_answer']))
    save(P/'analysis/scored_logical_rows.json',dict(at=now(),rows=result,scorer_sha256=sha('scripts/stage14d1/scoring.py'),
        inherited_extractor_sha256=sha('scripts/stage14b/protocol.py'),response_review_pending=sum(r['correct'] is None for r in result)))
    p=P/'analysis/scored_logical_rows.csv'
    with p.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
    ordered=sorted(states);by={(r['family_id'],r['arm']):r for r in result}
    strata=[offline[f]['source_stratum'] for f in ordered]
    ix=bootstrap_indices(strata)
    matrix=np.array([[np.nan if by[f,a]['correct'] is None else float(by[f,a]['correct']) for a in ARMS] for f in ordered])
    arms={}
    for j,a in enumerate(ARMS):
        x=matrix[:,j];valid=np.isfinite(x);sample=x[ix];counts=np.isfinite(sample).sum(axis=1)
        means=np.divide(np.nansum(sample,axis=1),counts,out=np.full(len(ix),np.nan),where=counts>0)
        correct=int(np.nansum(x));unscorable=int((~valid).sum())
        arms[a]=dict(correct=correct,wrong=int((x==0).sum()),unscorable=unscorable,missing=0,
            scorable_accuracy=float(np.nanmean(x)) if valid.any() else None,scorable_bootstrap_95ci=interval(means),
            known_correct_fraction=correct/72,accuracy_missingness_bounds=[correct/72,(correct+unscorable)/72],
            cap_hits=sum(by[f,a]['cap_hit'] for f in ordered))
    pairs={}
    for b,t in [('N',a) for a in ARMS[1:]]+[('G','QI'),('Q','QI'),('QI','QGL'),('QIA','QGL')]:
        pairs[t+'-'+b]=paired_summary(matrix[:,ARMS.index(b)],matrix[:,ARMS.index(t)],ix)
    subgroup={}
    for group in sorted({r['context_stratum'] for r in result}):
        selected=[i for i,f in enumerate(ordered) if offline[f]['audit_context_stratum']==group]
        m=matrix[selected];subgroup[group]=dict(families=len(selected),arms={a:dict(correct=int(np.nansum(m[:,j])),unscorable=int(np.isnan(m[:,j]).sum())) for j,a in enumerate(ARMS)})
    save(P/'analysis/accuracy_and_pairs.json',dict(at=now(),families=72,arms=arms,pairs=pairs,subgroups=subgroup,
        bootstrap=dict(draws=4000,seed=20261019,unit='independent conservative family',strata='answerformat x structured',equal_family_weight=True),
        physical_solver_calls=len(cache),logical_slots=432,pending_response_reviews=sum(r['correct'] is None for r in result)))
    print('Scored432logical;',len(cache),'physical;',sum(r['correct'] is None for r in result),'pending/unscorable')
if __name__=='__main__':main()
