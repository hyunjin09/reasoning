"""Prespecified R endpoints, four-state transitions and immutable parent context."""
from collections import Counter
import re
import numpy as np
from scripts.stage14cv.common import *
from scripts.stage14cv.analysis_core import paired_binary,transitions,VALUES,STATUSES


def main():
    for name in ['analysis_adapter_seal_v1.json','R_raw_seal_v1.json','R_scoring_seal_v1.json']:
        for p,h in load(ROOT/'audit'/name)['files'].items():assert sha(p)==h,p
    parent=Path('outputs/stage14c')
    for p,h in load(parent/'audit/primary_analysis_seal.json')['files'].items():assert sha(p)==h,p
    historical={r['family_id']:r for r in rows(parent/'scoring/scored_outcomes.jsonl') if r['benchmark']=='BlindTest'}
    families=sorted({t['family_id'] for t in tasks('R')})
    joined={f:dict(family_id=f) for f in families}
    for f in families:
        for model in 'IT':
            joined[f][model+'_native']=historical[f][model+'_img']
            joined[f][model+'_historical_E']=historical[f][model+'_E']
    technical={}
    for t in tasks('R'):
        s=load(ROOT/'scoring/R_scores'/f"{t['task_id']}.json")
        key=t['model_key']+'_'+t['condition'];joined[t['family_id']][key]=s['status']
        g=load(checked(t).parent/'generation.json')
        body=g['raw_decoded_response'].rsplit('</think>',1)[-1].strip()
        technical.setdefault(key,[]).append(dict(tokens=g['tokens'],latency=g['request_latency_seconds'],cap=g['cap_hit'],
             closed=t['model_key']!='T' or '</think>' in g['raw_decoded_response'],
             strict_native_format=bool(re.fullmatch(r'\{[+-]?\d+\}',body))))
    data=list(joined.values());assert len(data)==300
    def comparison(left,right,subset=data):
        return paired_binary([dict(family_id=r['family_id'],a=VALUES[r[left]],b=VALUES[r[right]]) for r in subset],
                              'a','b',left+'->'+right)
    primary=comparison('I_R0','I_R1')
    secondary={}
    for model in 'IT':
        for cond in ['R1','R2']:
            secondary[model+'_'+cond+'_minus_R0']=comparison(model+'_R0',model+'_'+cond)
    for cond in ['R0','R1','R2']:secondary['T_minus_I_'+cond]=comparison('I_'+cond,'T_'+cond)
    native_tables={};balance={};marginal={};drift={};overlap={}
    for model in 'IT':
        n=model+'_native'
        correct=[r for r in data if r[n]=='CORRECT'];wrong=[r for r in data if r[n]=='WRONG']
        cc=paired_binary([dict(family_id=r['family_id'],a=None if VALUES[r[model+'_R0']] is None else 1-VALUES[r[model+'_R0']],
             b=None if VALUES[r[model+'_R1']] is None else 1-VALUES[r[model+'_R1']]) for r in correct],
             'a','b',model+'|regression_R1_minus_R0')
        rc=comparison(model+'_R0',model+'_R1',wrong)
        balance[model]=dict(native_correct=len(correct),native_wrong=len(wrong),regression_rate_change=cc,rescue_rate_change=rc)
        drift[model]=comparison(model+'_historical_E',model+'_R0')
        regressed={c:{r['family_id'] for r in data if r[n]=='CORRECT' and r[model+'_'+c]=='WRONG'} for c in ['R0','R1','R2']}
        overlap[model]={a+'__'+b:len(regressed[a]&regressed[b]) for a,b in [('R0','R1'),('R0','R2'),('R1','R2')]}
        for cond in ['R0','R1','R2']:
            k=model+'_'+cond;tab=transitions(data,n,k)
            native_tables[k]=dict(transitions=tab,net_accuracy=comparison(n,k),
                 rescues=tab['WRONG__CORRECT'],regressions=tab['CORRECT__WRONG'],
                 net_correct_change=tab['WRONG__CORRECT']-tab['CORRECT__WRONG'])
            counts=Counter(r[k] for r in data);den=counts['CORRECT']+counts['WRONG']
            marginal[k]=dict(n=300,counts={s:counts[s] for s in STATUSES},scored_n=den,
                 accuracy_pp=100*counts['CORRECT']/den if den else None,
                 planned_accuracy_bounds_pp=[counts['CORRECT']/3,(300-counts['WRONG'])/3])
    tech={}
    for k,rr in technical.items():
        ts=[r['tokens'] for r in rr];ls=[r['latency'] for r in rr]
        tech[k]=dict(n=len(rr),cap_hits=sum(r['cap'] for r in rr),unclosed=sum(not r['closed'] for r in rr),
             strict_native_format=sum(r['strict_native_format'] for r in rr),tokens_quantiles=np.quantile(ts,[0,.25,.5,.75,1]).tolist(),
             request_latency_median_seconds=float(np.median(ls)),tokens_total=sum(ts),
             latency_note='Parallel request latency; do not sum as allocation GPU-hours')
    outputs={
      'representation_primary.json':dict(at=now(),primary_Instruct_R1_minus_R0=primary,marginals=marginal,secondary=secondary,
          inference='10000 paired-family draws, frozen seed20261009; unadjusted95% intervals; no p-values or efficacy threshold'),
      'r_native_transition_tables.json':dict(at=now(),panels=native_tables,balance=balance,regression_overlap=overlap),
      'historical_reference_comparison.json':dict(at=now(),R0_minus_historical_E=drift,
          caveat='Parent continuous refill versus fixed-wave new runs; historical outcomes contextual, not concurrent controls'),
      'R_technical_summary.json':dict(at=now(),panels=tech,context_replays_excluded=True)}
    for name,value in outputs.items():save(ROOT/'analysis'/name,value)
    write_rows(ROOT/'analysis/R_joined_outcomes.jsonl',data)
    paths=[ROOT/'analysis'/n for n in outputs]+[ROOT/'analysis/R_joined_outcomes.jsonl']
    save(ROOT/'audit/R_primary_seal_v1.json',dict(at=now(),files={str(p):sha(p) for p in paths},
         primary_and_companions_sealed=True,case_narratives_not_selected=True,C_may_proceed=True))
    print('R primary and companion analysis sealed')


if __name__=='__main__':main()
