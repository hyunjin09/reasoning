"""Scientific CoT join only after validity, blind trace and correctness seals."""
import json
from collections import Counter
import pandas as pd
from scripts.stage12cr.common import ROOT,load,save,sha,now
from scripts.stage12cr.seal import preservation
from scripts.stage12cr.inference import infer,transition,proportion
from scripts.stage12c.analyze import pathology_transition

def main():
    assert load(ROOT/'audit/denominator_seal.json')['pass'];preservation()
    cs=load(ROOT/'audit/correctness_seal.json');ts=load(ROOT/'audit/trace_seal.json')
    for p,h in {**cs['label_hashes'],**cs['output_hashes'],**ts['annotation_hashes']}.items():assert sha(p)==h,p
    full=load(ROOT/'stage12cr_cot_manifest.json')
    scores={r['item_id']:r for r in pd.read_parquet(ROOT/'stage12cr_cot_scoring_blind.parquet').to_dict('records')}
    technical={r['item_id']:r for r in pd.read_parquet(ROOT/'stage12cr_cot_results.parquet').to_dict('records')}
    rows=[];traces=[];pathologies=[]
    for old in full['labels']:
        r=dict(old);i=r['item_id'];s=scores[i];v=technical[i]
        r['c']=None if s['label']=='UNSCOREABLE_TECHNICAL' else s['label']=='CORRECT'
        r.update(C_outcome=v['extracted_outcome'],C_tokens=v['tokens'],C_cap=v['cap_hit'])
        for k in range(1,6):r[f'C_R{k}']=bool(v[f'R{k}'])
        new={k for k in range(1,4) if r[f'C_R{k}']}
        po=dict(item_id=i,family_id=r['family_id'],bottleneck=r['bottleneck'],correct=r['c'],scoreable=v['SCOREABLE'])
        for origin in ['N','O','NO_union']:
            before={k for arm in ('NO' if origin=='NO_union' else origin) for k in range(1,4) if r[f'{arm}_R{k}']}
            po[origin+'_transition']=pathology_transition(before,new,v['SCOREABLE'])
        pathologies.append(po)
        if r['complete_native_failure']:
            a=load(ROOT/'audit/trace_annotations'/f'C_{i}_v1.json');r['C_trace']=a['state']
            traces.append(dict(item_id=i,family_id=r['family_id'],bottleneck=r['bottleneck'],correct=r['c'],state=a['state'],
                atom_states_json=json.dumps(a['atom_states']),reason=a['reason'],quotes_json=json.dumps(a['quotes']),
                evidence_recovery_consistent_rescue=r['c'] is True and a['state']=='TRACE_E_FULL'))
        r['NC_transition']=transition(r['n'],r['c']);rows.append(r)
    assert len(rows)==61 and len(traces)==26
    for name,rr in [('rescue_transitions',rows),('trace_evidence_states',traces),('pathology_transitions',pathologies)]:
        p=ROOT/f'stage12cr_cot_{name}.parquet';assert not p.exists();pd.DataFrame(rr).to_parquet(p,index=False)
    rules=load(ROOT/'audit/analysis_rules.json')['bootstrap'];result=infer(rows,rules['draws'],rules['seed'])
    result['visible_evidence_B1']={}
    for correct,name in [(True,'rescued'),(False,'not_rescued'),(None,'unscoreable')]:
        rr=[r for r in traces if r['bottleneck']=='B1' and r['correct'] is correct]
        result['visible_evidence_B1'][name]=dict(n=len(rr),counts=dict(Counter(r['state'] for r in rr)),full=proportion(sum(r['state']=='TRACE_E_FULL' for r in rr),len(rr)))
    pp=[r for r in pathologies if r['bottleneck']=='B4']
    result['pathology_B4']={origin:{name:dict(count=sum(r[origin+'_transition']==name for r in pp),rescued=sum(r[origin+'_transition']==name and r['correct'] is True for r in pp))
        for name in ['RESOLVED','PRESERVED','CHANGED','NO_PRIOR_PATHOLOGY','NEW_PATHOLOGY','UNSCOREABLE_TECHNICAL']} for origin in ['N','O','NO_union']}
    k1=result['primary']['A-P1']['numerator'];k4=result['primary']['A-P2']['numerator']
    rec=('Follow both an upstream B1 retrieval branch and a downstream B4 equal-evidence branch.' if k1>=5 and k4>=5 else
         'Run a focused causal retrieval comparison on B1 native failures rescued by CoT.' if k1>=5 else
         'Run a CoT Equal-Evidence follow-up on rescued B4 cases to isolate downstream benefit.' if k4>=5 else
         'Keep Stage12B-S as the main Claim1 and stop the CoT rescue branch.')
    save(ROOT/'stage12cr_cot_primary_inference.json',dict(at=now(),**result))
    save(ROOT/'stage12cr_cot_decision.json',dict(at=now(),decision=result['decision'],recommendation=rec,recommendation_executed=False,thinking_outcome_not_used=True))
    print(json.dumps(dict(primary=result['primary'],decision=result['decision']),indent=2))

if __name__=='__main__':main()
