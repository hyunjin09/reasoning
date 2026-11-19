"""Bounded confirmation analyses; absent classes remain explicit unrun slots."""
import math
from collections import Counter,defaultdict
import numpy as np
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl
from visual_reasoning.stage5a.analysis import bucket,SIZE,paired_inference,holm,grouped_logistic


PRIMARY=['VSD_T','CE_minus_sham','QK_T_minus_control','alphaV_T','TE_T','sink_release']


def base_values(rows,key):
    grouped=defaultdict(list)
    for r in rows:
        x=r.get(key)
        if x is not None and math.isfinite(x):grouped[r['base_problem_id']].append(x)
    return {b:float(np.mean(x)) for b,x in grouped.items()}


def describe(rows,key):
    values=list(base_values(rows,key).values())
    return {'N_events':sum(r.get(key) is not None for r in rows),'N_bases':len(values),'median_base_mean':float(np.median(values)) if values else None,
            'min_base_mean':min(values) if values else None,'max_base_mean':max(values) if values else None}


def count(rows):return {'events':len(rows),'bases':len({r['base_problem_id'] for r in rows})}


def pairs(left,right,*,left_roi='T'):
    candidates=[]
    for a in left:
        for b in right:
            if a['base_problem_id']==b['base_problem_id'] or a.get(left_roi+'_source_class')!=b['T_source_class'] or a['readout_kind']!=b['readout_kind']:continue
            if bucket(a[left_roi+'_token_count'],SIZE)!=bucket(b['T_token_count'],SIZE):continue
            if abs(bucket(a['reasoning_progress'],[.25,.5,.75])-bucket(b['reasoning_progress'],[.25,.5,.75]))>1:continue
            x=a.get(left_roi+'_attention_density');y=b['T_attention_density']
            if not x or not y:continue
            distance=abs(math.log(x/y))
            if distance<=math.log(1.5):candidates.append((distance,a['event_id'],b['event_id'],a,b))
    used=set();chosen=[]
    for distance,_,__,a,b in sorted(candidates,key=lambda r:r[:3]):
        if a['base_problem_id'] in used or b['base_problem_id'] in used:continue
        used.update((a['base_problem_id'],b['base_problem_id']));chosen.append({'left_event':a['event_id'],'right_event':b['event_id'],
            'left_base':a['base_problem_id'],'right_base':b['base_problem_id'],'log_density_distance':distance,'left_roi':left_roi})
    return chosen


def family(paired,index,metrics=PRIMARY):
    results={}
    for metric in metrics:
        diffs=[]
        for p in paired:
            a=index[p['left_event']].get(metric);b=index[p['right_event']].get(metric)
            if a is not None and b is not None:diffs.append(a-b)
        results[metric]=paired_inference(diffs)
    corrected=holm([r['p_raw'] for r in results.values()])
    for r,p in zip(results.values(),corrected):r['p_Holm']=p
    return results


def descriptive_supplements(rows,classifiers):
    models=classifiers['grounded_correct_vs_hallucination'];bases=sorted({r['base_problem_id'] for r in models['F1']['base_class_predictions']})
    weights=np.random.default_rng(12348).multinomial(len(bases),np.ones(len(bases))/len(bases),size=10000);statistics={};ba={}
    for name,model in models.items():
        cube=np.zeros((len(bases),2,2))
        for r in model['base_class_predictions']:cube[bases.index(r['base_problem_id']),model['classes'].index(r['class']),np.argmax(r['probabilities'])]+=1
        confusion=(weights@cube.reshape(len(bases),4)).reshape(10000,2,2)
        ba[name]=(np.diagonal(confusion,axis1=1,axis2=2)/confusion.sum(2)).mean(1)
        statistics[name]={'balanced_accuracy_CI95':np.quantile(ba[name],[.025,.975]).tolist()}
    write_json(OUT/'phase_i_separability/classifier_base_bootstrap.json',{'unit':'unique base, preserving both states when present; bootstrap fixed out-of-fold predictions, no model refit',
        'N_bases':len(bases),'draws':10000,'seed':12348,'models':statistics,'F5_minus_F1_BA_CI95':np.quantile(ba['F5']-ba['F1'],[.025,.975]).tolist(),'causal_feature_circularity_remains':True})
    write_json(OUT/'analysis/source_summary.json',{'metrics':{k:describe(rows,k) for k in ['VSD_T','VSD_X','VSD_M','VSD_I','W8_T','CE_minus_sham','TE_T']},
        'semantic_positive_events':sum(r['CE_minus_sham'] is not None and r['CE_minus_sham']>.05 for r in rows),
        'semantic_total_events':sum(r['CE_minus_sham'] is not None for r in rows),
        'trigger_positive_events':sum(r['TE_T'] is not None and r['TE_T']>.05 for r in rows),'trigger_total_events':sum(r['TE_T'] is not None for r in rows),
        'source_role_counts':{k:sum(r[k] is not None for r in rows) for k in ['VSD_T','VSD_X','VSD_M','VSD_I']}})


def main():
    assert read_json(OUT/'audit/telemetry_reconstruction.json')['passed']
    rows=read_jsonl(OUT/'phase_e_internal/features.jsonl');index={r['event_id']:r for r in rows}
    annotations=read_jsonl(OUT/'annotations/events.jsonl');ann={r['event_id']:r for r in annotations};natural=read_jsonl(OUT/'cohort/natural_prevalence_manifest.jsonl')
    discovery=[r for r in rows if r['split']=='discovery'];confirmation=[r for r in rows if r['split']=='confirmation']
    census={'denominator_bases':len(natural),'selected_events':len(annotations),'selection':'first eligible fixed screen; no correctness balancing',
        'scope':'Up to3 selected native events per base, not exhaustive trace-level error prevalence.',
        'semantic_roles':{s:count([r for r in annotations if r['semantic_role']==s]) for s in sorted({r['semantic_role'] for r in annotations})},
        'local_correctness':{s:count([r for r in annotations if r['local_correctness']==s]) for s in sorted({r['local_correctness'] for r in annotations})},
        'final_correct_bases':sum(r['final_correct'] for r in natural),'final_wrong_bases':sum(not r['final_correct'] for r in natural)}
    write_json(OUT/'phase_a_census/semantic_prevalence.json',census)
    write_json(OUT/'phase_a_census/event_prevalence.json',{'events_per_base':dict(Counter(sum(e['base_problem_id']==r['base_problem_id'] for e in annotations) for r in natural)),
        'selected_event_positions':{e:count([r for r in annotations if r['event']==e]) for e in ('E1','E2','E3')}})
    correctness={s:{'natural':count([r for r in annotations if predicate(r)]),'atlas':count([r for r in rows if predicate(r)])} for s,predicate in
        [('locally_correct',lambda r:r['local_correctness']=='CORRECT'),('locally_incorrect',lambda r:r['local_correctness']=='INCORRECT'),
         ('globally_correct',lambda r:r['final_correct']),('globally_wrong',lambda r:not r['final_correct'])]}
    write_json(OUT/'phase_a_census/correctness_strata.json',correctness)
    cells={cell:count([r for r in confirmation if r['two_by_two_cell']==cell]) for cell in sorted({r['two_by_two_cell'] for r in rows})}
    write_json(OUT/'phase_f_alignment_retrieval/two_by_two_cells.json',{'confirmation':cells,'semantic_axis':'reviewed explicit semantic mention; independent of attention',
        'caution':'Mention without demanded-source retrieval is a broad cell; only independently mentioned M with weak M dependence qualifies for strict alignment-only.',
        'strict_alignment_only':count([r for r in confirmation if r['strict_alignment_only']]),'all_atlas_alignment_candidates':count([r for r in rows if r['alignment_only_candidate']])})
    align=pairs([r for r in confirmation if r['strict_alignment_only']],[r for r in confirmation if r['genuine_retrieval'] and r['high_attention']],left_roi='M')
    mirage=pairs([r for r in confirmation if r['strict_mirage']],[r for r in confirmation if r['genuine_retrieval'] and r['high_attention']])
    write_jsonl(OUT/'phase_f_alignment_retrieval/attention_matched_pairs.jsonl',align)
    write_json(OUT/'phase_f_alignment_retrieval/matched_state_statistics.json',{'direction':'alignment minus retrieval','pairs':len(align),'family':family(align,index)})
    write_json(OUT/'phase_g_mirage/mirage_statistics.json',{'confirmation':{s:count([r for r in confirmation if r[s]]) for s in
        ('strict_mirage','mirage_candidate_missing_CE','hallucinatory_mirage','benign_mirage')},
        'matched_pairs':mirage,'family':family(mirage,index),'CE_missing_is_not_null':True,'direction':'mirage minus retrieval'})
    subtypes={}
    wrong_bases={e['base_problem_id'] for e in annotations if e['local_correctness']=='INCORRECT' and e['has_explicit_visual_claim']}
    for name in ('H-NR','H-MR','H-SC','H-ST','H-INT'):
        selected=[r for r in rows if r['integration_failure']] if name=='H-INT' else [r for r in rows if name in r['hallucination_subtypes']]
        tests={}
        for metric in ('T_minus_X','T_minus_I','CE_minus_sham','TE_T'):
            enriched=[]
            for r in selected:
                value=(r['VSD_T']-r.get('VSD_'+metric[-1]) if metric.startswith('T_minus_') and r.get('VSD_'+metric[-1]) is not None else r.get(metric))
                enriched.append({**r,metric:value})
            tests[metric]=paired_inference(list(base_values(enriched,metric).values()))
        for result,p in zip(tests.values(),holm([v['p_raw'] for v in tests.values()])):result['p_Holm']=p
        selected_bases={r['base_problem_id'] for r in selected}
        subtypes[name]={**count(selected),'confidence_tiers':dict(Counter(r['subtype_confidence_tiers'].get(name,r['confidence_tier']) for r in selected)),
            'events_ids':[r['event_id'] for r in selected],'templates':dict(Counter(r['template_family'] for r in selected)),
            'causal_profiles':{k:describe(selected,k) for k in ('VSD_T','VSD_X','VSD_I','CE_minus_sham','TE_T')},'family':tests,
            'natural_ascertained_base_fraction':len(selected_bases)/200,'natural_fraction_interpretation':'ascertained subset, not an effect-balanced atlas prevalence estimate',
            'semantic_eligibility_upper_bound_bases':len(wrong_bases) if name!='H-INT' else sum(not r['final_correct'] for r in natural)}
    # One Holm family across all subtype causal contrasts, including empty slots.
    slots=[r for s in subtypes.values() for r in s['family'].values()]
    for r,p in zip(slots,holm([r['p_raw'] for r in slots])):r['p_Holm']=p
    write_json(OUT/'phase_h_failure/subtype_statistics.json',{'subtypes':subtypes,'labels_may_overlap':True,'all_semantically_wrong_bases':len(wrong_bases),
        'unscored_natural_bases':len({r['base_problem_id'] for r in natural}-{r['base_problem_id'] for r in rows}),
        'hallucination_denominator':'Only explicit, semantically checkable, locally incorrect claims; H-INT is separate.'})
    # Fixed utility candidates already have M source-removal arms; final-answer assay is separately gated.
    eligible=[r for r in rows if ann[r['event_id']]['independent_source_contrasts'].get('M',False)]
    utility=[]
    primary=read_json(OUT/'phase_b_causal/causal_run_complete.json')
    for r in eligible:
        paths=list((OUT/'raw'/primary['run_id']).glob(f'shard_*/{r["base_problem_id"]}/O/{r["event"]}.json'));assert len(paths)==1
        arms=read_json(paths[0])['arms'];delta=arms['N']['L_o']-arms['M_W2']['L_o'];d=arms['M_W2']['D']-arms['N']['D']
        utility.append({'base_problem_id':r['base_problem_id'],'event_id':r['event_id'],'strict_alignment_only':r['strict_alignment_only'],
            'correct_local_NLL_change_removal_minus_native':delta,'demanded_D_change':d,'final_candidate_margin_change':None,
            'label':'helpful' if delta>.05 else 'interfering' if delta<-.05 else 'benign','scope':'Descriptive reuse of frozen M arm; alignment-only qualification not assumed.'})
    write_jsonl(OUT/'phase_j_alignment_utility/subset_manifest.jsonl',[{'base_problem_id':r['base_problem_id'],'event_id':r['event_id'],'strict_alignment_only':r['strict_alignment_only']} for r in eligible])
    write_jsonl(OUT/'phase_j_alignment_utility/alignment_removal_results.jsonl',utility)
    strict_utility=[r for r in utility if r['strict_alignment_only']]
    assert len(strict_utility)<32,'Sufficient utility cohort requires separately frozen final-answer readouts before completing this script'
    write_json(OUT/'phase_j_alignment_utility/utility_statistics.json',{'status':'unrun_insufficient_alignment_only_events','target':48,'minimum':32,
        'independent_mentioned_candidates':len(eligible),'strict_alignment_only_events':len(strict_utility),
        'descriptive_existing_M_arms':len(utility),'final_candidate_margin':'unrun; not replaced by local D',
        'family':{k:{'status':'unrun','p_raw':1.,'p_Holm':1.} for k in ('correct_candidate_NLL','demanded_D','final_candidate_margin')}})
    # Discovery-only adjustment; target/source matching remains independent of sink effects.
    def design(r):return [1.,r['visual_share'],math.log1p(r['sequence_length']),r['reasoning_progress'],math.log1p(r['roi_token_count'])]
    design_discovery=np.array([design(r) for r in discovery]);coef=np.linalg.lstsq(design_discovery,np.array([r['sink_mass'] for r in discovery]),rcond=None)[0]
    for r in rows:r['sink_adjusted']=r['sink_mass']-float(np.array(design(r))@coef)
    sink_results={}
    for split,selected in [('discovery',discovery),('confirmation',confirmation)]:
        matched=pairs([r for r in selected if r['local_insensitive']],[r for r in selected if r['genuine_retrieval']])
        sink_results[split]={'pairs':matched,'family':family(matched,index,['sink_mass','sink_release','sink_adjusted'])}
    sink_states={s:{'count':count([r for r in rows if r['primary_state']==s]),**{key:describe([r for r in rows if r['primary_state']==s],key) for key in ('sink_mass','sink_release','visual_share')}} for s in sorted({r['primary_state'] for r in rows})}
    gains=[]
    for r in rows:
        if r['sink_release'] is not None:gains.append({**r,'target_gain':r['T_attention_gain']})
    bx=base_values(gains,'sink_release');by=base_values(gains,'target_gain');common=sorted(set(bx)&set(by))
    correlation=float(np.corrcoef([bx[b] for b in common],[by[b] for b in common])[0,1]) if len(common)>2 else None
    write_json(OUT/'phase_k_sink/state_sink_statistics.json',{'states':sink_states,'matched':sink_results,'discovery_adjustment_coefficients':coef.tolist(),
        'sink_release_vs_target_gain_base_correlation':correlation,'correlation_is_compositional_and_descriptive':True})
    confirmed=sink_results['confirmation']['family'];disc=sink_results['discovery']['family']
    robust=any(r['p_Holm']<.05 and r['CI95'] is not None and r['CI95'][0]*r['CI95'][1]>0 for r in confirmed.values())
    adjusted=confirmed['sink_adjusted']['p_Holm']<.05
    replication=any(confirmed[k]['p_Holm']<.05 and disc[k]['p_Holm']<.05 and (confirmed[k]['median'] or 0)*(disc[k]['median'] or 0)>0 for k in confirmed)
    gate={'robust_state_difference_after_matching':robust,'beyond_generic_visual_attention':adjusted,'heldout_replication':replication,
          'paper_critical_causal_explanation':False,'clear_behavioral_prediction_from_current_evidence':False}
    write_json(OUT/'phase_k_sink/sink_gate.json',{'passed':all(gate.values()),'conditions':gate,'action':'descriptive only; no sink intervention',
        'reason':'No sink manipulation or validated behavioral link establishes the last two criteria; state association alone is insufficient.'})
    # All classifier inputs are confirmation events; discovery calibrates attention only.
    attention=[r+'_'+m for r in ('T','M','X','I') for m in ('attention_mass','attention_density')]+['T_to_M_density_ratio','T_to_X_density_ratio','T_to_I_density_ratio','visual_share']
    qk=[r+'_'+m for r in ('T','M','X','I') for m in ('qk_cosine','scaled_logit')]
    value=[r+'_'+m for r in ('T','M','X','I') for m in ('alpha_v_norm','post_wo_norm')]
    causal=['VSD_T','VSD_M','VSD_X','VSD_I','W8_T','CE_minus_sham','TE_T']
    sets={'F1':attention,'F2':attention+qk,'F3':attention+qk+value,'F4':causal,'F5':attention+qk+value+causal+['sink_mass','sink_release','entropy','residual_norm','attention_output_norm']}
    tasks={
        'alignment_vs_retrieval':[(r,'alignment' if r['strict_alignment_only'] else 'retrieval') for r in confirmation if r['strict_alignment_only'] or r['genuine_retrieval']],
        'retrieval_vs_mirage':[(r,'mirage' if r['strict_mirage'] else 'retrieval') for r in confirmation if r['strict_mirage'] or r['genuine_retrieval']],
        'grounded_correct_vs_hallucination':[(r,'hallucination' if r['local_visual_hallucination'] else 'grounded_correct') for r in confirmation if r['local_visual_hallucination'] or (r['local_correctness']=='CORRECT' and r['genuine_retrieval'])],
        'failure_subtype':[(r,'H-INT' if r['integration_failure'] else r['hallucination_subtypes'][0]) for r in confirmation if r['integration_failure'] or len(r['hallucination_subtypes'])==1]}
    classifiers={task:{name:grouped_logistic([r for r,y in examples],[y for r,y in examples],features) for name,features in sets.items()} for task,examples in tasks.items()}
    write_json(OUT/'phase_i_separability/feature_sets.json',{'sets':sets,'all_inputs_confirmation_only':True,'labels':'fixed A–D, plus frozen discovery mirage criterion','F4_F5_circularity_explicit':True})
    write_json(OUT/'phase_i_separability/classifier_results.json',classifiers)
    write_json(OUT/'phase_i_separability/grouped_splits.json',{t:{f:r.get('folds',[]) for f,r in rs.items()} for t,rs in classifiers.items()})
    write_json(OUT/'phase_i_separability/feature_ablation.json',{t:{f:{k:r.get(k) for k in ('status','metrics','class_bases')} for f,r in rs.items()} for t,rs in classifiers.items()})
    matrix=np.array([[r.get(k) if r.get(k) is not None else np.nan for k in sets['F3']] for r in rows]);train=matrix[[r['split']=='discovery' for r in rows]]
    median=np.array([np.nanmedian(train[:,i]) if np.isfinite(train[:,i]).any() else 0. for i in range(train.shape[1])]);matrix=np.where(np.isfinite(matrix),matrix,median)
    train=matrix[[r['split']=='discovery' for r in rows]];mean=train.mean(0);std=train.std(0);std[std<1e-10]=1.;z=(matrix-mean)/std
    _,singular,components=np.linalg.svd((train-mean)/std,full_matrices=False);coords=z@components[:2].T
    write_json(OUT/'phase_i_separability/unsupervised_geometry.json',{'method':'PCA fitted on discovery F3; descriptive projection only','taxonomy_defined_by_clusters':False,
        'explained_variance_ratio':(singular[:2]**2/np.square(singular).sum()).tolist(),'coordinates':[{'event_id':r['event_id'],'state':r['primary_state'],'split':r['split'],'PC1':float(c[0]),'PC2':float(c[1])} for r,c in zip(rows,coords)]})
    robustness={}
    for name,paired in [('alignment_vs_retrieval',align),('mirage_vs_retrieval',mirage),('sink_weak_vs_retrieval',sink_results['confirmation']['pairs'])]:
        metrics=['sink_mass','sink_release','sink_adjusted'] if name=='sink_weak_vs_retrieval' else PRIMARY
        templates=sorted({r['template_family'] for r in rows});robustness[name]={t:family([p for p in paired if index[p['left_event']]['template_family']!=t and index[p['right_event']]['template_family']!=t],index,metrics) for t in templates}
    write_json(OUT/'analysis/template_robustness.json',{'leave_one_template_out':robustness,'state_template_composition':{s:dict(Counter(r['template_family'] for r in rows if r['primary_state']==s)) for s in sorted({r['primary_state'] for r in rows})}})
    stratification={}
    for name,paired in [('alignment_vs_retrieval',align),('mirage_vs_retrieval',mirage),('sink_weak_vs_retrieval',sink_results['confirmation']['pairs'])]:
        metrics=['sink_mass','sink_release','sink_adjusted'] if name=='sink_weak_vs_retrieval' else PRIMARY
        stratification[name]={s:family([p for p in paired if pred(index[p['left_event']]) and pred(index[p['right_event']])],index,metrics) for s,pred in
            [('locally_correct',lambda r:r['local_correctness']=='CORRECT'),('locally_incorrect',lambda r:r['local_correctness']=='INCORRECT'),('globally_correct',lambda r:r['final_correct']),('globally_wrong',lambda r:not r['final_correct'])]}
    write_json(OUT/'analysis/correctness_stratification.json',{'counts':correctness,'major_contrasts':stratification})
    summary={'natural':census,'atlas':count(rows),'confirmation':count(confirmation),'states':{s:count([r for r in rows if r['primary_state']==s]) for s in sorted({r['primary_state'] for r in rows})},
        'confirmation_matched_target_events':sum(r['T_density_percentile'] is not None for r in confirmation),'subtypes':subtypes,
        'alignment_pairs':len(align),'mirage_pairs':len(mirage),'sink_confirmation_pairs':len(sink_results['confirmation']['pairs']),
        'utility_strict_events':len(strict_utility),'strict_mirage_confirmation':count([r for r in confirmation if r['strict_mirage']]),
        'missing_CE_mirage_candidates_confirmation':count([r for r in confirmation if r['mirage_candidate_missing_CE']])}
    write_json(OUT/'analysis/taxonomy_summary.json',summary)
    descriptive_supplements(rows,classifiers)
    print({k:v for k,v in summary.items() if k not in ('natural','subtypes','states')})


if __name__=='__main__':main()
