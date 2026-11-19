"""Passive sink descriptions; no sink intervention or causal attribution."""
from collections import defaultdict
import numpy as np
from scripts.stage6b.common import OUT,read_json,read_jsonl,write_json,write_jsonl
from scripts.stage6b.event_results import load_run,feature_values
from scripts.stage6b.c2_results import load_complete_run
from visual_reasoning.stage6b.statistics import paired_effect


def describe(values,groups):
    if not values:return {'bases':0,'mean':None,'bootstrap_mean_ci95':None}
    r=paired_effect(values,groups=groups)
    return {k:r[k] for k in ['bases','independent_groups','mean','median','positive_fraction','bootstrap_mean_ci95','bootstrap_resamples']}


def control(rows):
    fit=[r for r in rows if r['split']=='discovery' and r['visual_mass'] is not None]
    counts=defaultdict(int)
    for r in fit:counts[r['base_id']]+=1
    X=np.asarray([[1,r['visual_mass'],r['entropy']] for r in fit]);y=np.asarray([r['sink_mass'] for r in fit])
    weights=np.sqrt([1/counts[r['base_id']] for r in fit]);coef=np.linalg.lstsq(X*weights[:,None],y*weights,rcond=None)[0]
    for r in rows:
        r['generic_attention_controlled_sink']=float(r['sink_mass']-np.dot([1,r['visual_mass'],r['entropy']],coef)) if r['visual_mass'] is not None else None
    return {'columns':['intercept','visual_attention_mass','predictive_entropy'],'coefficients':coef.tolist(),
        'fit':'Discovery only; equal total weight per base. Confirmation residualization only.',
        'discovery_rows':len(fit),'discovery_bases':len(counts),'causal_interpretation':False}


def main():
    rows=[];c1=[];c2=[];dyn={}
    labels={r['id']:r for split in ['discovery','confirmation'] for r in read_json(OUT/f'c1_mirage/mirage_{split}.json')['classification_rows']}
    for r in read_jsonl(OUT/'c1_mirage/fixed_prefix_scores.jsonl'):
        item={'id':r['id'],'base_id':r['base_id'],'group_id':r['group_id'],'split':r['split'],'phase':'C1_fixed',
            'condition':r['condition'],'state':'strict_mirage' if labels.get(r['id'],{}).get('strict_mirage') else r['condition'],
            'sink_mass':r['sink_mass'],'visual_mass':r['global_visual_attention'],'entropy':r['entropy'],'target_mass':r['attention_mass']}
        c1.append(item)
    # C2 native raw telemetry contains the global groups omitted by its source-specific flat table.
    for split in ['discovery','confirmation']:
        entries,results=load_complete_run('c2_'+split+'_01',split)
        for eid,e in entries.items():
            r=results[eid]
            c2.append({'id':eid,'base_id':e['base_id'],'group_id':e['group_id'],'split':split,'phase':'C2',
                'condition':e['condition'],'state':'factorial_'+e['condition'],'sink_mass':feature_values(r,'sink')['attention_mass'],
                'visual_mass':feature_values(r,'visual')['attention_mass'],'entropy':r['passive']['predictive_entropy'],
                'target_mass':feature_values(r,'T')['attention_mass'],'state_scope':'Focal-source factorial role; no global image-independent cell.'})
        entries,results,_=load_run('dynamics_'+split+'_01',OUT/'c1_dynamics/exact_anchor_manifest_v2.jsonl',split)
        for eid,e in entries.items():
            r=results[eid];dyn[eid]=(e,r)
    models={'C1_fixed':control([r for r in c1 if r['condition'] in ['intact','mild','strong','mask','sham_mild','sham_strong','sham_mask']]),'C2':control(c2)}
    grouped=defaultdict(dict)
    for r in c1:grouped[r['base_id']][r['condition']]=r
    for c in grouped.values():
        for r in c.values():
            r['sink_release_from_intact']=c['intact']['sink_mass']-r['sink_mass']
            r['target_gain_from_intact']=r['target_mass']-c['intact']['target_mass'] if r['target_mass'] is not None else None
            r['comparison_scope']='Same fixed textual prefix; positive sink release means less sink mass.'
    rows+=c1+c2
    transitions=[]
    for pair in read_jsonl(OUT/'c1_dynamics/wandering_fixation_classes.jsonl'):
        before=dyn[pair['pre_id']][1];after=dyn[pair['post_id']][1];source=pair['post_source']
        transitions.append({'id':pair['pair_id'],'base_id':pair['base_id'],'group_id':pair['group_id'],'split':pair['split'],
            'phase':'C1_dynamic_pair','state':pair['causal_state_class'],
            'sink_release':feature_values(before,'sink')['attention_mass']-feature_values(after,'sink')['attention_mass'],
            'new_target_gain':feature_values(after,source)['attention_mass']-feature_values(before,source)['attention_mass'],
            'scope':'Different reviewed query positions; passive covariance does not establish sink causality.'})
    rows+=transitions
    for phase,path,keys in [('C1_native','trajectory/passive_state_vectors.jsonl',('sink_attention_mass','visual_attention_mass','predictive_entropy')),
            ('C3','c3_object_stress/passive_features.jsonl',('sink_mass','global_visual_mass','entropy')),
            ('C4','c4_natural_validation/passive_state_vectors.jsonl',('sink_attention_mass','visual_attention_mass','predictive_entropy'))]:
        groups=defaultdict(list)
        for r in read_jsonl(OUT/path):
            item={'id':r['id'],'base_id':r['base_id'],'split':r['split'],'phase':phase,'state':r.get('condition',r.get('role')),
                'sink_mass':r[keys[0]],'visual_mass':r[keys[1]],'entropy':r[keys[2]],
                'target_mass':r.get('source_specific_features',{}).get('T',{}).get('attention_mass',r.get('attention_mass')),
                'token_end':r.get('token_end'),'scope':'Native passive only; no imputed causal identity.'}
            if phase=='C3' and not r['present']:
                item['distractor_mass']=item['target_mass'];item['target_mass']=None
            rows.append(item);groups[r.get('event_id',r['base_id'])].append(item)
        if phase=='C1_native':
            for values in groups.values():
                values.sort(key=lambda r:r['token_end']);first=values[0]
                for r in values:
                    r['sink_release_from_first_observed']=first['sink_mass']-r['sink_mass']
                    r['target_gain_from_first_observed']=r['target_mass']-first['target_mass'] if r['target_mass'] is not None and first['target_mass'] is not None else None
    strict={}
    for split in ['discovery','confirmation']:
        delta=defaultdict(list);residual=defaultdict(list);g={}
        for r in c1:
            if r['split']!=split or r['state']!='strict_mirage':continue
            intact=grouped[r['base_id']]['intact'];b=r['base_id'];g[b]=r['group_id']
            delta[b].append(r['sink_mass']-intact['sink_mass'])
            residual[b].append(r['generic_attention_controlled_sink']-intact['generic_attention_controlled_sink'])
        strict[split]={'mirage_minus_intact_sink':describe([float(np.mean(v)) for v in delta.values()],[g[b] for b in delta]),
            'generic_attention_controlled':describe([float(np.mean(v)) for v in residual.values()],[g[b] for b in residual])}
    factorial={};c2groups=defaultdict(dict)
    for r in c2:c2groups[r['base_id']][r['condition']]=r
    for split in ['discovery','confirmation']:
        chosen=[c for c in c2groups.values() if c['AR']['split']==split];factorial[split]={}
        for feature in ['sink_mass','generic_attention_controlled_sink']:
            values=[((c['AR'][feature]-c['A_only'][feature])+(c['R_only'][feature]-c['Neither'][feature]))/2 for c in chosen]
            factorial[split][feature+'_focal_demand_effect']=describe(values,[c['AR']['group_id'] for c in chosen])
    write_jsonl(OUT/'sink/state_sink_features.jsonl',rows)
    write_json(OUT/'sink/sink_descriptive_statistics.json',{'C1_strict_mirage_comparisons':strict,'C2_focal_demand_comparisons':factorial,
        'generic_attention_models':models,'dynamic_pair_descriptors':transitions,'p_value_headline':False,
        'unidentified_states':['wandering: no matched no-change panel','fixation: none strictly identified in selected comparisons'],
        'limitations':'Sink and target masses share an attention budget. Descriptive redistribution and residualization cannot establish causal behavioral effects.'})
    write_json(OUT/'sink/future_sink_gate.json',{'recommend_sink_causality':False,'clear_causal_behavioral_prediction_established':False,
        'reason':'No intervention identifies sink mediation or a mechanism-specific behavioral prediction. Correlations or generic-attention residuals alone cannot pass the gate.',
        'sink_interventions_run':0})
    print('Passive sink synthesis:',len(rows),'records; future sink gate remains closed.')


if __name__=='__main__':main()
