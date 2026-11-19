"""Frozen family estimands; no source edits and no follow-on execution."""
import numpy as np,pandas as pd
from scripts.stage13d.scoring import selected,final_score
from scripts.stage13d.common import *
from scripts.stage13d.protocol import bootstrap,bootstrap_counts,semantic_decision,buffer_decision
from scripts.stage13d.validate_buffer import receipt

def main():
    for arm in CONDITIONS:assert (ROOT/'audit'/f'{arm}_scoring_closed.json').exists()
    observations=[]
    for arm in CONDITIONS:
        for t in selected(arm):
            tid=t['task_id'];a=load(ROOT/'audit/technical_decisions'/f'{tid}.json');s=final_score(tid);g=load(ROOT/'generations'/tid/'generation.json')
            observations.append(dict(task_id=tid,item_id=t['item_id'],family_id=t['family_id'],condition=arm,replicate=t['replicate'],
                correct=s['correct'],valid=a['validity']['TECHNICALLY_VALID'],outcome=a['outcome'],tokens=g['tokens'],cap_hit=g['cap_hit'],seed=t['seed'],
                generation_path=str(ROOT/'generations'/tid/'generation.json'),generation_sha256=sha(ROOT/'generations'/tid/'generation.json')))
    df=pd.DataFrame(observations);df.to_parquet(ROOT/'stage13d_semantic_results.parquet',index=False)
    eligible=[r for r in load(ROOT/'stage13d_derived_state_extractions.json')['rows'] if r['status']=='SAFE_NONEMPTY'];labels={r['item_id']:r['correctness_label'] for r in load(ROOT/'stage13d_derived_state_audit.json')['rows']}
    families=[]
    for r in eligible:
        f=dict(item_id=r['item_id'],family_id=r['family_id'],derived_correctness=labels[r['item_id']])
        for arm in CONDITIONS:
            rr=[x for x in observations if x['item_id']==r['item_id'] and x['condition']==arm];resolved=[x for x in rr if x['correct'] is not None]
            f[arm+'_correct']=sum(x['correct'] for x in resolved);f[arm+'_resolved']=len(resolved);f[arm+'_missing']=5-len(resolved)
            f[arm+'_accuracy']=f[arm+'_correct']/5 if len(resolved)==5 else None
        f['complete']=all(f[c+'_resolved']==5 for c in CONDITIONS)
        for short,control in [('base','I_BASE'),('dummy','I_DUMMY'),('shuffle','I_SHUFFLED')]:f['delta_'+short]=(f['I_DERIVED_correct']-f[control+'_correct'])/5 if f['complete'] else None
        families.append(f)
    pd.DataFrame(families).to_parquet(ROOT/'audit/semantic_family_effects.parquet',index=False)
    complete=[r for r in families if r['complete']];contrasts={};bounds={}
    for name,control in [('base','I_BASE'),('dummy','I_DUMMY'),('shuffle','I_SHUFFLED')]:
        contrasts[name]=bootstrap_counts([r['I_DERIVED_correct']-r[control+'_correct'] for r in complete])
        lo=sum(r['I_DERIVED_correct']-r[control+'_correct']-r[control+'_missing'] for r in families)/(5*len(families))
        hi=sum(r['I_DERIVED_correct']+r['I_DERIVED_missing']-r[control+'_correct'] for r in families)/(5*len(families))
        bounds[name]=dict(n_families=len(families),lower=lo,upper=hi,denominator='All safe families, including unrun calls if stopped')
    sem=semantic_decision(len(complete),contrasts['dummy'],contrasts['base']['mean'],contrasts['shuffle']['mean']) if complete else False
    rates={arm:dict(complete_family_accuracy=float(np.mean([r[arm+'_accuracy'] for r in complete])) if complete else None,
        scoreable_calls=sum(x['condition']==arm and x['valid'] for x in observations),missing_calls=sum(x['condition']==arm and not x['valid'] for x in observations),
        correct_calls=sum(x['condition']==arm and x['correct'] is True for x in observations)) for arm in CONDITIONS}
    groups={}
    for label in ['ALL_VERIFIED_CORRECT','HAS_VERIFIED_ERROR','MIXED_OR_UNCLEAR']:
        group=[r for r in complete if r['derived_correctness']==label]
        groups[label]=dict(n_complete=len(group),derived_accuracy=float(np.mean([r['I_DERIVED_accuracy'] for r in group])) if group else None,
            delta_dummy=float(np.mean([r['delta_dummy'] for r in group])) if group else None,interpretation='Descriptive, not causal error propagation')
    technical=load(ROOT/'stage13d_buffer_technical_validation.json');probrows=[];margins=[];mc=load(ROOT/'stage13d_mc_buffer_manifest.json')['rows']
    if technical['passed']:
        tasks=[t for t in load(ROOT/'stage13d_buffer_forced_sequences.json')['tasks'] if t['phase']=='scientific_buffer'];lookup={}
        for t in tasks:
            f=receipt(t);lookup[t['item_id'],t['condition']]=f
            for label,values in f['option_token_logprobs'].items():
                for pos,logp in enumerate(values):probrows.append(dict(task_id=t['task_id'],item_id=t['item_id'],family_id=t['family_id'],condition=t['condition'],option=label,token_position=pos,token_id=f['candidate_ids'][label][pos],log_probability=logp,free_generated_tokens=0))
        for row in mc:
            r=dict(item_id=row['item_id'],family_id=row['family_id'],gold=row['gold'])
            for condition in ['B_SHORT','B_LONG']:
                vals={a:sum(v)/len(v) for a,v in lookup[row['item_id'],condition]['option_token_logprobs'].items()}
                r[condition+'_gold_logp']=vals[row['gold']];r[condition+'_margin']=vals[row['gold']]-max(v for a,v in vals.items() if a!=row['gold'])
                best=max(vals,key=vals.get);r[condition+'_top1']=best;r[condition+'_top1_gold']=best==row['gold'];r[condition+'_tie_count']=sum(v==vals[best] for v in vals.values())
            r['delta_margin']=r['B_LONG_margin']-r['B_SHORT_margin'];margins.append(r)
    probs=pd.DataFrame(probrows,columns=['task_id','item_id','family_id','condition','option','token_position','token_id','log_probability','free_generated_tokens'])
    probs.to_parquet(ROOT/'stage13d_buffer_option_logprobs.parquet',index=False)
    pd.DataFrame(margins,columns=['item_id','family_id','gold','B_SHORT_gold_logp','B_SHORT_margin','B_SHORT_top1','B_SHORT_top1_gold','B_SHORT_tie_count','B_LONG_gold_logp','B_LONG_margin','B_LONG_top1','B_LONG_top1_gold','B_LONG_tie_count','delta_margin']).to_parquet(ROOT/'stage13d_buffer_family_margins.parquet',index=False)
    # Independent second computation: operate on saved token table, not receipt dicts.
    independent=[]
    if len(probs):
        table=pd.read_parquet(ROOT/'stage13d_buffer_option_logprobs.parquet').groupby(['item_id','condition','option']).log_probability.mean()
        for r in margins:
            reconstructed=[]
            for c in ['B_SHORT','B_LONG']:
                series=table.loc[r['item_id'],c];margin=float(series.loc[r['gold']]-series.drop(r['gold']).max());assert abs(margin-r[c+'_margin'])<1e-10;reconstructed.append(margin)
            assert abs(reconstructed[1]-reconstructed[0]-r['delta_margin'])<1e-10
            independent.append(dict(item_id=r['item_id'],passed=True))
    save(ROOT/'audit/buffer_margin_recomputation.json',dict(at=now(),rows=independent,implementation='Pandas groupby on reread saved token parquet, independent of receipt aggregation'))
    bv=[r['delta_margin'] for r in margins];buffer=bootstrap(bv);buf=buffer_decision(bv)
    buffer.update(confirmed=buf,technical_valid=technical['passed'],positive_fraction=buffer['positive']/len(bv) if bv else None,
        short_top1=sum(r['B_SHORT_top1_gold'] for r in margins),long_top1=sum(r['B_LONG_top1_gold'] for r in margins),
        top1_tie_rule='Canonical option order; ties explicitly counted')
    if sem and buf:decision='COMPLEMENTARY_BUFFER_AND_SEMANTIC_PRIMING'
    elif sem:decision='SEMANTIC_PRIMING_ONLY'
    elif buf:decision='BUFFER_ONLY'
    elif (contrasts['dummy']['mean'] is not None and contrasts['dummy']['mean']>0) or (buffer['mean'] is not None and buffer['mean']>0):decision='POST_EVIDENCE_MECHANISM_PARTIAL'
    else:decision='POST_EVIDENCE_MECHANISM_UNRESOLVED'
    inference=dict(at=now(),decision=decision,unit='family',bootstrap_draws=10000,bootstrap_seed=ANALYSIS_SEED,
        semantic=dict(confirmed=sem,status='DERIVED_STATE_PRIMING_CONFIRMED' if sem else 'NOT_CONFIRMED',n_safe=len(eligible),n_complete=len(complete),contrasts=contrasts,rates=rates,correctness_groups=groups),
        buffer=buffer,identification_boundary='Portability/sufficiency in Instruct and same-Thinking-checkpoint forced-computation intervention; not a hybrid Thinking ON/OFF decomposition',selected_historical_cases_opened=False)
    save(ROOT/'stage13d_missingness_bounds.json',dict(at=now(),semantic=bounds,buffer_missing=2*len(mc)-len({r['task_id'] for r in probrows})))
    save(ROOT/'stage13d_primary_inference.json',inference)
    recommendations={
        'COMPLEMENTARY_BUFFER_AND_SEMANTIC_PRIMING':'Treat this as the final 4B Thinking-mechanism result and stop further mechanism expansion.',
        'SEMANTIC_PRIMING_ONLY':'Validate the derived-state priming effect once on an independent fresh cohort before elevating it to a broad mechanism claim.',
        'BUFFER_ONLY':'Compare the immediate computational-buffer effect with a matched text-only reasoning model before making a modality-specific interpretation.',
        'POST_EVIDENCE_MECHANISM_PARTIAL':'Preserve the supported component as secondary mechanism evidence and stop additional decomposition unless a cleaner hybrid ON/OFF model becomes available.',
        'POST_EVIDENCE_MECHANISM_UNRESOLVED':"Retain Stage 13A's confirmed post-evidence advantage as the strongest Thinking claim and close the mechanism branch."}
    save(ROOT/'stage13d_decision.json',dict(at=now(),decision=decision,recommendation=recommendations[decision],recommendation_count=1,follow_on_launched=False))
    print('SEALED_PRIMARY',decision,'SEMANTIC',contrasts,'BUFFER',buffer)
if __name__=='__main__':main()
