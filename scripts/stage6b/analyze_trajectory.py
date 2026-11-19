"""Descriptive geometry after exact causal labels freeze; base-level summaries."""
from collections import defaultdict,Counter
import numpy as np
from scripts.stage6b.common import OUT,SOURCE,read_json,read_jsonl,write_json,write_jsonl,sha
from scripts.stage6b.dense_results import load_dense,passive_vector
from scripts.stage6b.event_results import load_run
from visual_reasoning.stage6b.geometry import fit_pca,project,path_metrics


def main():
    rules=read_json(OUT/'config/trajectory_geometry_rules.json');columns=rules['passive_columns']
    availability=read_json(OUT/'audit/native_candidate_readout_availability.json')
    assert availability['native_manifest_sha256']==sha(OUT/'trajectory/native_endpoint_manifest_v3_schedule.jsonl')
    assert availability['available_exact_native_endpoint_margins']==0
    assert sha(SOURCE/'traces/controlled_native_index.jsonl')==read_json(OUT/'audit/native_acquisition_context.json')['native_index_sha256']
    # Reading the frozen causal labels here is an explicit PCA sequencing gate.
    causal_states=read_jsonl(OUT/'c1_dynamics/exact_source_scores.jsonl')
    classes=read_jsonl(OUT/'c1_dynamics/wandering_fixation_classes.jsonl')
    assert (OUT/'c1_mirage/mirage_confirmation.json').is_file()
    native_keys=['ended_with_eos','truncated','token_count','generation_artifact']
    native_index={r['event_id']:{k:r[k] for k in native_keys} for r in read_jsonl(SOURCE/'traces/controlled_native_index.jsonl')}
    vectors=[];event_entries={};coverage=[]
    for e,r in load_dense('native_primary_02',OUT/'trajectory/native_endpoint_manifest_v3_schedule.jsonl'):
        native=native_index[e['id']];assert native['generation_artifact']==e['native_generation_path']
        event_entries[e['id']]=e
        coverage.append({'id':e['id'],'base_id':e['base_id'],'condition':e['condition'],'endpoints':len(r['endpoints'])})
        for endpoint in r['endpoints']:
            values,sources=passive_vector(endpoint['passive'])
            vector={'id':endpoint['id'],'event_id':e['id'],'base_id':e['base_id'],'group_id':e['group_id'],'dataset':e['dataset'],
                'condition':e['condition'],'split':e['split'],'token_end':endpoint['token_end'],'review_scope':endpoint['review_scope'],
                'semantic_unresolved':endpoint['semantic_unresolved'],'demanded_sources':endpoint['demanded_sources'],
                'previous_demand':endpoint['previous_demand'],'demand_changed':endpoint['demand_changed'],
                'source_specific_features':sources,'final_correctness':e['final_correctness']['final_answer_correctness'],
                'final_correctness_scope':'Frozen final reference agreement; not local visual truth or causal error attribution.',
                'condition_truth_applicable':e['final_correctness'].get('condition_truth_applicable'),
                'condition_answer_applicability':e['final_correctness']['condition_answer_applicability'],
                'native_ended_with_eos':native['ended_with_eos'],'native_truncated':native['truncated'],
                'native_generated_tokens':native['token_count'],
                'candidate_margin':None,**values}
            vectors.append(vector)
    eligible=[r for r in vectors if all(r[c] is not None for c in columns)]
    discovery=[r for r in eligible if r['split']=='discovery' and r['review_scope']=='manual_semantic_prefix' and r['condition']=='intact']
    model=fit_pca(discovery,columns)
    model.update(rule_sha256=sha(OUT/'config/trajectory_geometry_rules.json'),
        training_row_ids=[r['id'] for r in discovery],training_composition=dict(Counter(r['dataset'] for r in discovery)),
        training_condition_composition=dict(Counter(r['condition'] for r in discovery)),
        training_base_composition=dict(Counter({r['base_id']:r['dataset'] for r in discovery}.values())),
        training_source_groups=len({r['group_id'] for r in discovery}),
        label_freeze_sha256=sha(OUT/'c1_dynamics/wandering_fixation_classes.jsonl'))
    normalized,pca=project(eligible,model);lookup={};training_ids=set(model['training_row_ids'])
    projections=[]
    for r,z,p in zip(eligible,normalized,pca):
        lookup[r['id']]=(z,p)
        projections.append({'id':r['id'],'event_id':r['event_id'],'base_id':r['base_id'],'split':r['split'],
            'dataset':r['dataset'],'condition':r['condition'],'review_scope':r['review_scope'],
            'PC1':float(p[0]),'PC2':float(p[1]),'projection_only':r['id'] not in training_ids})
    write_jsonl(OUT/'trajectory/passive_state_vectors.jsonl',vectors)
    write_json(OUT/'trajectory/normalization.json',{k:model[k] for k in ['columns','mean','scale','fit_weighting','discovery_bases','discovery_rows']},freeze=True)
    write_json(OUT/'trajectory/pca_discovery.json',model,freeze=True)
    write_jsonl(OUT/'trajectory/pca_all_projections.jsonl',projections)
    write_jsonl(OUT/'trajectory/pca_confirmation_projection.jsonl',[r for r in projections if r['split']=='confirmation'])
    coupling={r['base_id']:r for r in read_json(OUT/'c1_dynamics/demand_coupling.json')['descriptive_base_summaries']}
    grouped=defaultdict(list)
    for r in eligible:
        grouped[(r['event_id'],'all_resolved_or_reviewed')].append(r)
        if r['review_scope']=='manual_semantic_prefix':grouped[(r['event_id'],'manual_reviewed_prefix')].append(r)
    metrics=[]
    for (eid,scope),rows in grouped.items():
        rows.sort(key=lambda r:r['token_end']);e=event_entries[eid]
        z=np.asarray([lookup[r['id']][0] for r in rows]);p=np.asarray([lookup[r['id']][1] for r in rows])
        exact=coupling.get(e['base_id']) if e['condition']=='intact' else None
        metrics.append({'event_id':eid,'base_id':e['base_id'],'group_id':e['group_id'],'split':e['split'],'dataset':e['dataset'],
            'condition':e['condition'],'scope':scope,'original_space':path_metrics(z),'pca_space':path_metrics(p),
            'final_correctness':e['final_correctness']['final_answer_correctness'],
            'exact_selected_anchor_coupling':exact,'unnecessary_switching_rate':None,
            'unnecessary_switching_status':'No matched exact no-change panel; not estimable.',
            'movement_does_not_define_failure':True})
    write_jsonl(OUT/'trajectory/trajectory_metrics.jsonl',metrics)
    comparisons=[]
    primary=[r for r in metrics if r['scope']=='manual_reviewed_prefix']
    for split in ['discovery','confirmation']:
        for correct in ['CORRECT','INCORRECT','UNRESOLVED']:
            chosen=[r for r in primary if r['split']==split and r['final_correctness']==correct and r['original_space']['path_length'] is not None]
            comparisons.append({'split':split,'final_correctness':correct,'bases':len(chosen),
                'original_space_mean_path':float(np.mean([r['original_space']['path_length'] for r in chosen])) if chosen else None,
                'original_space_mean_tortuosity':float(np.mean([r['original_space']['tortuosity'] for r in chosen])) if chosen else None,
                'pca_mean_path':float(np.mean([r['pca_space']['path_length'] for r in chosen])) if chosen else None,
                'mean_observed_spans':float(np.mean([r['original_space']['observed_states'] for r in chosen])) if chosen else None})
    write_json(OUT/'trajectory/vstream_style_comparison.json',{'descriptive_base_summaries':comparisons,
        'no_confirmatory_p_value':'Secondary unpaired correctness strata; annotation density/length differs and is reported. Movement is not a failure label.'})
    write_json(OUT/'trajectory/demand_aligned_comparison.json',{'cohort_level_mechanistic_comparison_identified':False,
        'reason':'Exact panel below minimum, without matched no-change pairs. Sparse selected-anchor coupling can be visualized alongside movement but cannot establish cohort-level superiority.',
        'paired_movement_and_coupling':[r for r in primary if r['exact_selected_anchor_coupling'] is not None],
        'causal_pair_counts':dict(Counter(c['causal_state_class'] for c in classes))})
    anchor_vectors=[];anchor_entries={};anchor_results={}
    for split in ['discovery','confirmation']:
        e,r,_=load_run('dynamics_'+split+'_01',OUT/'c1_dynamics/exact_anchor_manifest_v2.jsonl',split);anchor_entries.update(e);anchor_results.update(r)
    for state in causal_states:
        e=anchor_entries[state['id']];d=state['demanded_source'];scores=state['source_scores'];previous=e['semantic_state'].get('previous_demand')
        previous=previous[0] if previous and len(previous)==1 else None
        alt=[k for k in scores if k not in {d,previous}]
        passive_values,_=passive_vector(anchor_results[state['id']]['passive'])
        _,passive_projection=project([passive_values],model)
        anchor_vectors.append({'id':state['id'],'base_id':state['base_id'],'split':state['split'],'dataset':state['dataset'],
            'condition':e['condition'],
            'group_id':e['group_id'],
            'native_candidate_margin':state['native_D'],
            'positive_candidate_semantic_value':e['event']['correct_semantic_value'],
            'foil_candidate_semantic_value':e['event']['foil_semantic_value'],
            'VSD_demanded':scores[d],'VSD_previous':scores.get(previous),'VSD_alternative':scores[alt[0]] if alt else None,
            'VSD_irrelevant':None,'counterfactual_semantic_effect':None,'DCM':state['demanded_source_margin'],
            'demanded_source_id':d,'previous_source_id':previous,'alternative_source_id':alt[0] if alt else None,
            'all_exact_source_scores':scores,'passive_PC1_at_exact_readout':float(passive_projection[0,0]),
            'passive_PC2_at_exact_readout':float(passive_projection[0,1]),
            'dominant_source':state['dominant_source'],'missing_components_not_imputed':True})
    causal_discovery=[r for r in anchor_vectors if r['split']=='discovery']
    causal_model=fit_pca(causal_discovery,rules['causal_pca_columns'])
    causal_model.update(training_row_ids=[r['id'] for r in causal_discovery],
        training_composition=dict(Counter(r['dataset'] for r in causal_discovery)),
        training_condition_composition=dict(Counter(r['condition'] for r in causal_discovery)),
        training_base_composition=dict(Counter({r['base_id']:r['dataset'] for r in causal_discovery}.values())),
        training_source_groups=len({r['group_id'] for r in causal_discovery}),
        rule_sha256=model['rule_sha256'],label_freeze_sha256=model['label_freeze_sha256'])
    _,causal_projection=project(anchor_vectors,causal_model)
    for r,p in zip(anchor_vectors,causal_projection):r.update(PC1=float(p[0]),PC2=float(p[1]))
    write_jsonl(OUT/'trajectory/causal_anchor_vectors.jsonl',anchor_vectors)
    write_json(OUT/'trajectory/pca_causal_discovery.json',causal_model,freeze=True)
    write_json(OUT/'audit/native_endpoint_coverage.json',{'native_events':coverage,'passive_endpoints':len(vectors),
        'zero_endpoint_traces':sum(r['endpoints']==0 for r in coverage),
        'review_scope_counts':read_json(OUT/'config/native_passive_rules_v2.json')['coverage_by_review_scope'],
        'candidate_margin_availability_audit':'audit/native_candidate_readout_availability.json',
        'available_exact_native_endpoint_margins':availability['available_exact_native_endpoint_margins'],
        'primary_PCA_training_rows':len(discovery),'projected_endpoints':len(eligible),'excluded_missing_visual_components':len(vectors)-len(eligible),
        'no_causal_imputation':True,'confirmation_fit_rows':0})
    # B2 is explicitly separate, even though its storage shares dense state vectors.
    write_jsonl(OUT/'c1_mirage/native_condition_features.jsonl',vectors)
    byevent=defaultdict(list)
    for r in vectors:byevent[r['event_id']].append(r)
    summaries=[]
    for split in ['discovery','confirmation']:
        for condition in sorted({e['condition'] for e in event_entries.values()}):
            selected=[e for e in event_entries.values() if e['split']==split and e['condition']==condition]
            native=[native_index[e['id']] for e in selected];means={}
            for feature in ['visual_attention_mass','sink_attention_mass','predictive_entropy']:
                pertrace=[]
                for e in selected:
                    values=[r[feature] for r in byevent[e['id']] if r[feature] is not None]
                    if values:pertrace.append(float(np.mean(values)))
                means[feature]={'traces':len(pertrace),'mean_of_trace_means':float(np.mean(pertrace)) if pertrace else None}
            summaries.append({'split':split,'condition':condition,'traces':len(selected),
                'native_EOS_traces':sum(r['ended_with_eos'] for r in native),'truncated_traces':sum(r['truncated'] for r in native),
                'mean_generated_tokens':float(np.mean([r['token_count'] for r in native])),
                'frozen_final_reference_counts':dict(Counter(e['final_correctness']['final_answer_correctness'] for e in selected)),
                'zero_eligible_endpoint_traces':sum(not byevent[e['id']] for e in selected),
                'observed_endpoints':sum(len(byevent[e['id']]) for e in selected),'native_passive_trace_means':means})
    strict=read_json(OUT/'c1_mirage/mirage_confirmation.json')['classification_rows']
    write_json(OUT/'c1_mirage/native_condition_summary.json',{'condition_summaries':summaries,
        'native_index_sha256':sha(SOURCE/'traces/controlled_native_index.jsonl'),
        'strict_fixed_prefix_cases_native_outcomes':[{'id':r['id'],'native':native_index[r['id']],
            'final_reference_review':event_entries[r['id']]['final_correctness']} for r in strict if r['strict_mirage']],
        'scope':'Own native-condition traces; passive means cover eligible endpoints, with trace weighting and missingness reported. Capped/unknown traces remain in the denominator. B1fixed-prefix candidates are not transferred as B2causal labels.',
        'causal_error_or_failure_mode_inferred_from_completion_or_movement':False})
    print('Native/PCA complete:',len(vectors),'states;',len(discovery),'discovery fit rows;',model['explained_variance_ratio'])


if __name__=='__main__':main()
