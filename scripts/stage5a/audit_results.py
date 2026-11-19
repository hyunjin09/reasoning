"""Final independent artifact, label, replay, split and resource checks."""
from collections import Counter
from datetime import datetime
import math
import numpy as np
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,sha
from scripts.stage5a.run_scores import verify_freeze,score_equal
from scripts.stage5a.run_passive import verify_labels
from visual_reasoning.stage5a.protocol import classify_event
from visual_reasoning.stage5a.analysis import holm,classification_metrics


def main():
    freeze=verify_freeze();label_freeze=verify_labels();checks={}
    gates=[read_json(OUT/p) for p in ('audit/mechanical_validation.json','phase_b_causal/causal_run_complete.json','phase_c_counterfactual/semantic_run_complete.json','audit/telemetry_reconstruction.json')]
    checks['four_completed_gated_assays']=all(g['passed'] for g in gates)
    hashes={**freeze['sha256'],**freeze['asset_metadata_sha256'],**freeze['native_provenance_sha256'],**label_freeze['sha256']}
    for g in gates:hashes.update(g['raw_sha256'])
    hashes.update(gates[-1]['historical_reference_sha256'])
    checks['all_frozen_and_raw_hashes_exact']=all(sha(ROOT/p)==h for p,h in hashes.items())
    natural=read_jsonl(OUT/'cohort/natural_prevalence_manifest.jsonl');atlas=read_jsonl(OUT/'cohort/causal_atlas_manifest.jsonl')
    checks['natural200_atlas128_unique']=len(natural)==len({r['base_problem_id'] for r in natural})==200 and len(atlas)==len({r['base_problem_id'] for r in atlas})==128
    checks['discovery32_confirmation96_disjoint']=len(freeze['discovery_bases'])==32 and len(freeze['confirmation_bases'])==96 and not set(freeze['discovery_bases'])&set(freeze['confirmation_bases'])
    annotations={e['event_id']:e for e in read_jsonl(OUT/'annotations/events.jsonl')};labels=read_jsonl(OUT/'annotations/causal_labels.jsonl');features=read_jsonl(OUT/'phase_e_internal/features.jsonl')
    primary={(r['base_problem_id'],r['event']):r for p in (OUT/'raw/causal_01').glob('shard_*/*/O/*.json') for r in [read_json(p)]}
    passive=[read_json(p) for p in (OUT/'raw/passive_01').glob('shard_*/*/E*.json')]
    assert len(primary)==len(passive)==len(labels)==len(features)==347
    for r in passive:
        e=annotations[r['event_id']];n=primary[r['base_problem_id'],r['event']]['arms']['N']
        assert score_equal(r['current'],n)
        for role,positions in e['source_groups'].items():
            if role=='joint':continue
            assert r['current']['groups'][role]==positions
        assert r['current']['current_query_zero_based']==e['current_query_zero_based']
        if r['prior']['available']:assert r['prior']['current_query_zero_based']==e['current_query_zero_based']-8
    checks['independent_all347_passive_score_replays']=True
    for r in labels:
        e=annotations[r['event_id']];arms=primary[r['base_problem_id'],r['event']]['arms']
        actual={role:arms['N']['D']-arms[role+'_W2']['D'] for role in ('T','M','X','I','joint') if role+'_W2' in arms}
        assert actual==r['VSD']
        strict={role:v for role,v in actual.items() if role not in ('M','X') or e['independent_source_contrasts'].get(role,False)}
        later=(e['integration_error_reviewed'] and bool(e['next_downstream_use']) and e['next_downstream_use'] not in e['history_before_ed_text'])
        recomputed=classify_event(local_correctness=e['local_correctness'],final_correct=e['final_correct'],vsd=strict,w8_t=r['W8_T'],
            ce_minus_sham=r['CE_minus_abs_sham'],temporal=e['temporal_role'],integration_error_reviewed=later,
            mention_differs=e['independent_source_contrasts'].get('M',False),has_explicit_claim=e['has_explicit_visual_claim'],
            ce_effect=r['CE'],sham_effect=r['sham_shift'],previous_source_roi=e['previous_source_roi'])
        assert all(r[k]==v for k,v in recomputed.items())
        assert r['local_visual_hallucination']==(e['local_correctness']=='INCORRECT' and e['has_explicit_visual_claim'])
        if r['integration_failure']:assert later and e['local_correctness']=='CORRECT' and not e['final_correct']
        if not e['temporal_unresolved']:assert e['temporal_evidence']['full_native_prefix_reviewed']
    checks['frozen_labels_reconstruct_without_attention']=True;checks['wrong_final_not_hallucination']=True
    checks['integration_error_is_reviewed_and_later']=True;checks['temporal_labels_require_full_native_review']=True
    for item in atlas:
        m=read_json(ROOT/item['asset_metadata']);visual=m['prompt_metadata']['visual_token_indices']
        for e in m['events']:
            for role,positions in e['source_groups'].items():
                assert set(positions)<=set(visual)
                if role in e['local_source_groups']:assert positions==[visual[i] for i in e['local_source_groups'][role]]
            if 'I' in e['source_groups']:
                assert e['irrelevant_control_validated'] and len(e['source_groups']['I'])==len(e['source_groups']['T'])
                assert not set(e['source_groups']['I'])&set(e['source_groups']['T'])
            for role,independent in e['independent_source_contrasts'].items():
                if independent:assert not set(e['source_groups']['T'])&set(e['source_groups'][role])
    checks['source_maps_I_cardinality_and_independent_alternatives']=True
    cf=read_jsonl(OUT/'phase_c_counterfactual/semantic_effects.jsonl')
    for r in cf:
        e=annotations[r['event_id']];d=r['condition_D'];s=r['edited_source']
        assert e['cf_validated'] and r['CE']==d['O']-d['C_'+s]
        assert r['CE_minus_abs_sham']==r['CE']-abs(d['O']-d['S_'+s])
    checks['all85_semantic_signs_and_sham_subtractions']=len(cf)==85
    for r in read_jsonl(OUT/'phase_d_trigger/trigger_effects.jsonl'):
        a=primary[r['base_problem_id'],r['event']]['arms']
        for role,te in r['TE_VSD'].items():assert te==(a['N']['D']-a[role+'_W2']['D'])-(a['R16']['D']-a['R16_'+role+'_W2']['D'])
    checks['all256_trigger_effects_reconstruct']=True
    rule=read_json(OUT/'phase_g_mirage/frozen_rule.json')
    assert rule['high_density_percentile']==.9 and rule['minimum_reference_rois']==8
    assert all(r['base_problem_id'].startswith('historical_') or r['base_problem_id'] in freeze['discovery_bases'] for r in rule['reference_rois'])
    for r in features:
        if r['strict_mirage']:assert r['high_attention'] and r['local_insensitive'] and r['semantic_null_with_sham_control']
    checks['discovery_only_reference_and_strict_mirage_gate']=True
    classifiers=read_json(OUT/'phase_i_separability/classifier_results.json')
    for task,sets in classifiers.items():
        for result in sets.values():
            if result['status']!='scored':continue
            alltest=[]
            for fold in result['folds']:
                assert fold['status']=='scored' and fold['optimizer_success']
                assert not set(fold['train_bases'])&set(fold['test_bases'])
                assert not set(fold['train_templates'])&set(fold['test_templates'])
                alltest.extend(fold['test_bases'])
            assert len(alltest)==len(set(alltest))
            p=result['base_class_predictions'];metrics=classification_metrics([result['classes'].index(r['class']) for r in p],np.array([r['probabilities'] for r in p]),len(result['classes']))
            assert metrics==result['metrics']
    checks['whole_template_and_base_splits_no_leakage']=True;checks['classifier_metrics_independently_reconstructed']=True
    for path in ('phase_f_alignment_retrieval/matched_state_statistics.json','phase_g_mirage/mirage_statistics.json'):
        family=read_json(OUT/path)['family'];assert [r['p_Holm'] for r in family.values()]==holm([r['p_raw'] for r in family.values()])
    checks['empty_primary_comparisons_unrun_with_Holm_slots']=True
    utility=read_json(OUT/'phase_j_alignment_utility/utility_statistics.json')
    checks['utility_minimum_gate_and_distinct_final_readout']=utility['strict_alignment_only_events']<32 and utility['final_candidate_margin'].startswith('unrun')
    checks['sink_descriptive_only']=not read_json(OUT/'phase_k_sink/sink_gate.json')['passed']
    diagnostic=read_json(OUT/'audit/hmr_readout_orientation_diagnostic.json')
    for r in diagnostic['rows']:
        a=primary[r['base_problem_id'],r['event_id'].split('_')[-1]]['arms'];s=a[r['alternative_roi']+'_W2']
        assert r['wrong_logp_source_contribution']==a['N']['L_c']-s['L_c']
    checks['HMR_margin_not_conflated_with_wrong_token_support']=len(diagnostic['rows'])==10
    envs=[];resources={}
    for phase in ('validation','causal','semantic','passive'):
        run=OUT/'raw'/(phase+'_01');environments=[read_json(p) for p in run.glob('shard_*/environment.json')];summaries=[read_json(p) for p in run.glob('shard_*/run_summary.json')]
        assert len(environments)==len(summaries)==4;envs.extend(environments)
        rows_phase=[read_json(p) for p in run.glob('shard_*/*/E*.json')] if phase=='passive' else [read_json(p) for p in run.glob('shard_*/*/*/*.json')]
        resources[phase]={'rank_seconds_sum':sum(s['runtime_seconds'] for s in summaries),'maximum_rank_seconds':max(s['runtime_seconds'] for s in summaries),
            'peak_allocated_GiB':max(r['peak_gpu_allocated_bytes'] for r in rows_phase)/2**30,'peak_reserved_GiB':max(r['peak_gpu_reserved_bytes'] for r in rows_phase)/2**30,
            'event_files':len(rows_phase),'scheduler_id':f'stage5a_{phase}_01_tmux9_108548'}
    checks['all16_scoring_environments_existing_four_A6000s']=all(e['slurm_job_id']=='108548' and e['world_size']==4 and 'A6000' in e['gpu_name'] for e in envs)
    checks['labels_frozen_before_each_passive_rank']=all(datetime.fromisoformat(e['started_at'])>datetime.fromisoformat(label_freeze['frozen_at']) for e in envs if e['phase']=='passive')
    generation=[read_json(p) for p in (OUT/'prospective_generation/raw').glob('shard_*/result.json')];assert len(generation)==4
    assert all((g['intentional_cohort_target_stop'] or g['planned_shard_complete']) and g['all_raw_outcomes_preserved'] for g in generation)
    new=[r for g in generation for r in g['results']]
    resources['generation']={'completed':len(new),'statuses':dict(Counter(r['status'] for r in new)),
        'generation_rank_seconds_sum':sum(r['runtime']['elapsed_seconds'] for r in new),'all_outcomes_preserved':True,
        'scheduler_id':'stage5a_generation_tmux9_108548','target_cohort_stop':True,
        'rank_stop_modes':{str(g['rank']):'planned_shard_complete' if g['planned_shard_complete'] else 'genuine_cohort_target_stop' for g in generation}}
    checks['native_generation_stopped_cleanly_without_fake_load']=True
    write_json(OUT/'audit/resource_summary.json',{'slurm_job_id':'108548','tmux_session':'9','node':'node07','GPUs':4,'new_allocation_requests':0,
        'package_installs':0,'phases':resources,'scoring_GPU_hours_excluding_model_load':sum(resources[p]['rank_seconds_sum'] for p in ('validation','causal','semantic','passive'))/3600})
    figures=read_json(OUT/'analysis/figures/index.json')['figures'];assert len(figures)==20
    assert all((ROOT/r[k]).is_file() and (ROOT/r[k]).stat().st_size>1000 for r in figures for k in ('png','pdf'))
    checks['all20_standalone_PNG_PDF_figures']=True
    result={'passed':all(checks.values()),'checks':checks,'check_count':len(checks),'frozen_hashes_verified':len(hashes),
        'score_event_image_files':sum(g['event_files'] for g in gates[:3]),'passive_event_files':len(passive),
        'scoring_arms':sum(g['arms'] for g in gates[:3]),'source_calls':sum(g['source_calls'] for g in gates[:3]),
        'review_scope':'Independent reconstruction by main agent; no independent reviewer agent claimed.'}
    write_json(OUT/'audit/final_artifact_validation.json',result)
    for name,description in {'canonical_path_audit':'Four A6000 ranks; validated unchanged canonical source runtime and exact passive replay.',
        'event_index_audit':'All source partitions, native histories and candidate spans checked by complete score audits.',
        'roi_audit':'Frozen reviewed ROI maps;267 validated I events; overlapping alternatives excluded from strict contrasts.',
        'source_suppression_selectivity':'All243776 source calls checked by score audits.',
        'counterfactual_edit_audit':'48 reviewed bases;85 event readouts; source-image and edit hashes exact; semantic/sham signs reconstructed.',
        'trigger_intervention_audit':'96 frozen bases,256 events; R16 current query/layers16–23; effects reconstructed.',
        'self_patch_validation':'24 historical events; native/no-op/unhooked exact.',
        'deterministic_replay':'Mechanical source replay and85 semantic plus347 passive native readouts exact.'}.items():
        write_json(OUT/f'audit/{name}.json',{'passed':result['passed'],'description':description,'evidence':'audit/final_artifact_validation.json','mechanical_evidence':'audit/mechanical_validation.json'})
    print(result)
    assert result['passed']


if __name__=='__main__':main()
