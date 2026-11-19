"""Scientific joins only after immutable technical, trace and scoring seals."""
import json
from collections import Counter
import pandas as pd
from scripts.stage12ts.common import ROOT,OLD,load,save,sha,now
from scripts.stage12ts.seal import preservation
from scripts.stage12ts.inference import infer,transition
from scripts.stage12c.analyze import pathology_transition

def recommendation(states):
    visual='THINKING_VISUAL_RECOVERY_SIGNAL' in states;down='THINKING_DOWNSTREAM_SIGNAL' in states
    if visual and down:return 'Prioritize the B1 causal-retrieval analysis first, then test B4 downstream persistence with Thinking Equal-Evidence Oracles.'
    if visual:return 'Run a focused causal visual-retrieval comparison on B1 families that fail under CoT but succeed under Thinking with full task-critical evidence recovery in the Thinking trace.'
    if down:return 'Run Thinking Equal-Evidence Oracles on rescued B4 families to localize the gain downstream of visual evidence acquisition.'
    if 'THINKING_RESCUE_WITHOUT_CLEAR_EVIDENCE_LINK' in states:return 'Investigate alternative mechanisms on T-rescued B1 cases before attributing the gain to visual-evidence recovery.'
    return 'Stop the rescue branch and retain Stage12B-S plus the sparse CoT result as the completed Claim1 behavioral story.'

def main():
    assert load(ROOT/'audit/denominator_seal.json')['pass'];preservation()
    cs=load(ROOT/'audit/correctness_seal.json');ts=load(ROOT/'audit/trace_seal.json')
    for p,h in {**cs['label_hashes'],**cs['output_hashes'],**ts['annotation_hashes']}.items():assert sha(p)==h,p
    scores={r['item_id']:r for r in pd.read_parquet(ROOT/'stage12ts_thinking_scoring_blind.parquet').to_dict('records')}
    tech={r['item_id']:r for r in pd.read_parquet(ROOT/'stage12ts_thinking_results.parquet').to_dict('records')}
    prior=pd.read_parquet(OLD/'stage12cr_cot_rescue_transitions.parquet').to_dict('records')
    rows=[];traces=[];pathologies=[]
    for old in prior:
        r=dict(old);i=r['item_id'];v=tech[i];s=scores[i]
        for arm in ['n','c','o','e']:r[arm]=None if pd.isna(r[arm]) else bool(r[arm])
        r['t']=None if s['label']=='UNSCOREABLE_TECHNICAL' else s['label']=='CORRECT'
        r.update(T_outcome=v['extracted_outcome'],T_tokens=v['tokens'],T_cap=v['cap_hit'],T_trace=None)
        for k in range(1,6):r[f'T_R{k}']=bool(v[f'R{k}'])
        po=dict(item_id=i,family_id=r['family_id'],bottleneck=r['bottleneck'],correct=r['t'],scoreable=v['SCOREABLE'])
        new={k for k in range(1,4) if r[f'T_R{k}']}
        for arm in ['N','O','C']:
            before={k for k in range(1,4) if r[f'{arm}_R{k}']}
            po[arm+'_transition']=pathology_transition(before,new,v['SCOREABLE'])
        pathologies.append(po)
        if r['complete_native_failure']:
            a=load(ROOT/'audit/trace_annotations'/f'T_{i}_v1.json');r['T_trace']=a['state']
            traces.append(dict(item_id=i,family_id=r['family_id'],bottleneck=r['bottleneck'],correct=r['t'],state=a['state'],C_state=r['C_trace'],
                atom_states_json=json.dumps(a['atom_states']),reason=a['reason'],quotes_json=json.dumps(a['quotes']),
                evidence_linked_rescue=r['t'] is True and a['state']=='TRACE_E_FULL',
                thinking_only_evidence_recovery_rescue=r['bottleneck']=='B1' and r['c'] is False and r['t'] is True and a['state']=='TRACE_E_FULL'))
        r['CT_transition']=transition(r['c'],r['t']);r['NT_transition']=transition(r['n'],r['t']);rows.append(r)
    assert len(rows)==61 and len(traces)==26
    for name,rr in [('cot_thinking_transitions',rows),('trace_evidence_states',traces),('pathology_transitions',pathologies)]:
        p=ROOT/f'stage12ts_{name}.parquet';assert not p.exists();pd.DataFrame(rr).to_parquet(p,index=False)
    rules=load(ROOT/'audit/analysis_rules.json');boot=rules['bootstrap'];result=infer(rows,boot['draws'],boot['seed'])
    result['pathology_counts']={arm:{f'R{k}':sum(r[f'{arm}_R{k}'] for r in rows) for k in range(1,6)} for arm in ['N','O','C','T']}
    pp=[r for r in pathologies if r['bottleneck']=='B4']
    result['pathology_B4']={arm:{name:dict(count=sum(r[arm+'_transition']==name for r in pp),rescued=sum(r[arm+'_transition']==name and r['correct'] is True for r in pp))
        for name in ['RESOLVED','PRESERVED','CHANGED','NO_PRIOR_PATHOLOGY','NEW_PATHOLOGY','UNSCOREABLE_TECHNICAL']} for arm in ['N','O','C']}
    sensitivity={}
    for key in ['S1','S2']:
        excluded=set(rules['sensitivities'][key+'_exclude']);rr=[r for r in rows if r['item_id'] not in excluded]
        sensitivity[key]=dict(excluded_ids=sorted(excluded),remaining_families=len(rr),inference=infer(rr,boot['draws'],boot['seed']),primary_decision_used=False)
    save(ROOT/'stage12ts_sensitivity_results.json',dict(at=now(),rule=rules['sensitivities'],results=sensitivity))
    save(ROOT/'stage12ts_primary_inference.json',dict(at=now(),**result))
    save(ROOT/'stage12ts_decision.json',dict(at=now(),states=result['states'],recommendation=recommendation(result['states']),recommendation_executed=False))
    selected=sorted((r for r in traces if r['thinking_only_evidence_recovery_rescue']),key=lambda r:r['family_id'])[:3]
    facts={r['item_id']:r['facts'] for r in load(ROOT/'stage12ts_thinking_manifest.json')['rows']}
    save(ROOT/'audit/T5_deterministic_examples.json',dict(at=now(),rule='Smallest family IDs among frozen B1 C-negative T-positive TRACE_E_FULL-T; at most3, no replacement when none.',
        all_qualifying_families=result['evidence_B1']['qualifying_families'],examples=[dict(r,facts=facts[r['item_id']],
            outcomes={a:next(x for x in rows if x['item_id']==r['item_id'])[a] for a in ['n','c','t']}) for r in selected]))
    print('Scientific states:',result['states'],'B1',result['primary']['T-P1'],'B4',result['primary']['T-P2'])

if __name__=='__main__':main()
