"""Join immutable labels only after validity, trace review and correctness seal."""
import json
from collections import Counter
import pandas as pd
from scripts.stage12c.common import ROOT,load,save,sha,now
from scripts.stage12c.seal import preservation
from scripts.stage12c.protocol import transition,rescue_decision
from scripts.stage12c.inference import infer,proportion


def pathology_transition(old, new, scoreable):
    if not scoreable:return 'UNSCOREABLE_TECHNICAL'
    if not old:return 'NO_PRIOR_PATHOLOGY' if not new else 'NEW_PATHOLOGY'
    if not new:return 'RESOLVED'
    return 'PRESERVED' if old & new else 'CHANGED'


def main():
    assert load(ROOT/'audit/denominator_seal.json')['pass']
    preservation()
    cs=load(ROOT/'audit/correctness_seal.json');ts=load(ROOT/'audit/trace_seal.json')
    for p,h in {**cs['label_hashes'],**cs['output_hashes'],**ts['annotation_hashes']}.items():assert sha(p)==h,p
    full=load(ROOT/'stage12c_frozen_bottleneck_manifest.json')
    scores={};technical={}
    for arm,name in [('C','cot'),('T','thinking')]:
        scores[arm]={r['item_id']:r for r in pd.read_parquet(ROOT/f'stage12c_{name}_scoring_blind.parquet').to_dict('records')}
        technical[arm]={r['item_id']:r for r in pd.read_parquet(ROOT/f'stage12c_{name}_results.parquet').to_dict('records')}
    rows=[];traces=[];pathologies=[]
    for old in full['labels']:
        r=dict(old);i=r['item_id']
        for arm in 'CT':
            s=scores[arm][i];v=technical[arm][i]
            r[arm.lower()]=None if s['label']=='UNSCOREABLE_TECHNICAL' else s['label']=='CORRECT'
            r[arm+'_outcome']=v['extracted_outcome'];r[arm+'_tokens']=v['tokens'];r[arm+'_cap']=v['cap_hit']
            for k in range(1,6):r[f'{arm}_R{k}']=bool(v[f'R{k}'])
            new={k for k in range(1,4) if r[f'{arm}_R{k}']}
            po=dict(item_id=i,family_id=r['family_id'],bottleneck=r['bottleneck'],arm=arm,
                    correct=r[arm.lower()],scoreable=v['SCOREABLE'],new_pathology_json=json.dumps(sorted(new)))
            for old_arm in 'NO':
                before={k for k in range(1,4) if r[f'{old_arm}_R{k}']}
                po[old_arm+'_transition']=pathology_transition(before,new,v['SCOREABLE'])
                po[old_arm+'_pathology_json']=json.dumps(sorted(before))
            union={k for old_arm in 'NO' for k in range(1,4) if r[f'{old_arm}_R{k}']}
            po['NO_union_transition']=pathology_transition(union,new,v['SCOREABLE'])
            pathologies.append(po)
            if r['complete_native_failure']:
                a=load(ROOT/'audit/trace_annotations'/f'{arm}_{i}_v1.json')
                r[arm+'_trace']=a['state']
                traces.append(dict(item_id=i,family_id=r['family_id'],bottleneck=r['bottleneck'],arm=arm,
                    correct=r[arm.lower()],state=a['state'],atom_states_json=json.dumps(a['atom_states']),
                    reason=a['reason'],quotes_json=json.dumps(a['quotes']),
                    evidence_recovery_consistent_rescue=(r[arm.lower()] is True and a['state']=='TRACE_E_FULL'),
                    annotation_sha256=sha(ROOT/'audit/trace_annotations'/f'{arm}_{i}_v1.json')))
        r['CT_transition']=transition(r['c'],r['t'])
        r['NC_transition']=transition(r['n'],r['c'])
        r['NT_transition']=transition(r['n'],r['t'])
        rows.append(r)
    assert len(rows)==61 and len(traces)==52 and len(pathologies)==122
    for name,rr in [('rescue_transitions',rows),('trace_evidence_states',traces),('pathology_transitions',pathologies)]:
        dest=ROOT/f'stage12c_{name}.parquet';assert not dest.exists();pd.DataFrame(rr).to_parquet(dest,index=False)
    rules=load(ROOT/'audit/analysis_rules.json')['bootstrap']
    result=infer(rows,draws=rules['draws'],seed=rules['seed'])
    result['decision']=rescue_decision(rows,True)
    result['visible_evidence_B1']={}
    result['pathology_B4']={}
    for arm in 'CT':
        result['visible_evidence_B1'][arm]={}
        for correct,name in [(True,'rescued'),(False,'not_rescued'),(None,'unscoreable')]:
            rr=[r for r in traces if r['bottleneck']=='B1' and r['arm']==arm and r['correct'] is correct]
            result['visible_evidence_B1'][arm][name]=dict(n=len(rr),counts=dict(Counter(r['state'] for r in rr)),
                full=proportion(sum(r['state']=='TRACE_E_FULL' for r in rr),len(rr)))
        pp=[r for r in pathologies if r['bottleneck']=='B4' and r['arm']==arm]
        result['pathology_B4'][arm]={origin:{name:dict(count=sum(r[origin+'_transition']==name for r in pp),
            rescued=sum(r[origin+'_transition']==name and r['correct'] is True for r in pp))
            for name in ['RESOLVED','PRESERVED','CHANGED','NO_PRIOR_PATHOLOGY','NEW_PATHOLOGY','UNSCOREABLE_TECHNICAL']}
            for origin in ['N','O','NO_union']}
    result.update(at=now(),paired_outcomes_opened=True,limitations=[
        '61 developmental families; no benchmark-wide prevalence claim.',
        'N versus C is a same-checkpoint prompt comparison. C versus T is a variant comparison, not a Thinking-on causal effect.',
        'Visible evidence is externalization, not proof of hidden retrieval. Not externalized does not mean internally absent.',
        'B1 includes seven explicit-wrong and four unresolved-only E profiles; preserve this qualification.',
        'B2/B3 descriptive only; primary cells are small and missingness remains explicit.',
        'Second scoring pass is single-agent QC, not independent inter-rater reliability.'])
    save(ROOT/'stage12c_primary_inference.json',result)
    print(json.dumps(dict(decision=result['decision'],primary=result['primary'],contrasts=result['contrasts']),indent=2))


if __name__=='__main__':main()
