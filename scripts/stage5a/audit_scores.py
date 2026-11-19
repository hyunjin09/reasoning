"""Verify complete frozen assay coverage and each saved source operation."""
import argparse,math
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,sha
from scripts.stage5a.run_scores import verify_freeze,validation_events
from visual_reasoning.stage4a.runtime import event_coordinates


def expected_arms(event,meta,phase):
    names={'N'}
    if phase in ('validation','causal'):
        names.update(r+'_W2' for r in ('T','M','X','I','joint') if r in event['source_groups'])
        names.add('T_W8')
        if phase=='validation' or meta.get('trigger_selected'):
            names.update(('R16','R16_T_W2'))
            alt=next((r for r in ('X','M') if r in event['source_groups']),None)
            if alt:names.add('R16_'+alt+'_W2')
    if phase=='validation':names.update(('noop_joint_W8','noop_R16_joint_W2','unhooked','replay_T_W2'))
    return names


def audit(phase,run_id):
    verify_freeze()
    manifest={'validation':'cohort/validation_manifest.jsonl','causal':'cohort/causal_atlas_manifest.jsonl',
              'semantic':'phase_c_counterfactual/subset_manifest.jsonl'}[phase]
    items=read_jsonl(OUT/manifest); expected={}; metas={}
    for item in items:
        b=item['base_problem_id'];m=read_json(ROOT/item['asset_metadata']);metas[b]=m
        events=validation_events(m) if phase=='validation' else m['events']
        for e in events:
            conditions=['OO'] if phase=='validation' else e['cf_conditions'] if phase=='semantic' and e['cf_validated'] else [] if phase=='semantic' else ['O']
            for c in conditions:expected[b,c,e['event']]=e
    paths=sorted((OUT/'raw'/run_id).glob('shard_*/*/*/*.json'))
    rows=[read_json(p) for p in paths]
    observed={(r['base_problem_id'],r['condition'],r['event']) for r in rows}
    assert observed==set(expected) and len(rows)==len(expected),f'Incomplete {phase}: {len(rows)}/{len(expected)}'
    envs=[read_json(OUT/'raw'/run_id/f'shard_{r:02d}/environment.json') for r in range(4)]
    summaries=[read_json(OUT/'raw'/run_id/f'shard_{r:02d}/run_summary.json') for r in range(4)]
    assert all(s['completed'] for s in summaries)
    code=envs[0]['code_sha256']
    assert all(sha(ROOT/p)==h for p,h in code.items())
    assert all('A6000' in e['gpu_name'] and e['world_size']==4 and e['code_sha256']==code and not e['passive_telemetry_enabled'] for e in envs)
    if phase!='validation':
        validated=read_json(OUT/'audit/mechanical_validation.json')
        assert validated['passed'] and code==validated['code_sha256']
    calls=arms=0;max_error=0.;details=[]
    for row in rows:
        b=row['base_problem_id'];m=metas[b];e=expected[b,row['condition'],row['event']]
        p=m['prompt_metadata']['prompt_token_count'];co=event_coordinates(e,p)
        assert row['image_layout_exact'] and row['event_history_sha256']==e['history_before_ed_sha256']
        assert not row['passive_features_extracted'] and set(row['arms'])==expected_arms(e,m,phase)
        assert all(row['validation_checks'].values())
        if phase=='validation':assert len(row['validation_checks'])==4
        if phase=='semantic' and row['condition']=='O':assert row['validation_checks']['primary_native_exact']
        for name,a in row['arms'].items():
            arms+=1
            assert a['finite'] and all(math.isfinite(a[k]) for k in ('D','L_o','L_c')) and a['D']==a['L_o']-a['L_c']
            assert not a['telemetry'] and not a['residual_norms'] and 'predictive_entropy' not in a
            assert a['partition']==[list(x) for x in co['partition']] and a['absolute_current_query']==p+co['current']
            for role,key in [('original','original_divergent_suffix_ids'),('counterfactual','counterfactual_divergent_suffix_ids')]:
                assert a[role+'_candidate']['candidate_token_ids']==e[key]
            if phase=='validation':assert a['clone_no_alias'] and a['past_cache_audit']['passed']
            if name=='unhooked':
                assert not a['source_audits'] and not a['step_audits'];continue
            assert len(a['step_audits'])==8
            for i,s in enumerate(a['step_audits']):
                q=co['window_start']+i
                assert s['generated_query']==q and s['layers']==list(range(36)) and s['finite']
                assert s['active_roi']==(a['roi'] if q>=co['end']-a['window'] else None)
                assert s['active_trigger']==(a['trigger'] and q==co['current'])
            required=[]
            if a['roi']:required.extend((a['roi'],layer,p+q) for q in range(co['end']-a['window'],co['end']) for layer in range(36))
            if a['trigger']:required.extend(('R16',layer,p+co['current']) for layer in range(16,24))
            actual=[]
            for s in a['source_audits']:
                calls+=1;kind=s['source_kind'];actual.append((kind,s['layer_index'],s['query_positions'][0]))
                positions=co['R16'] if kind=='R16' else e['source_groups'][kind]
                assert s['source_positions']==positions and s['selected_heads']==list(range(32))
                assert not s['qkv_directly_modified'] and not s['attention_directly_modified']
                assert s['all_outputs_finite'] and s['partition_compute_dtype']=='float32'
                assert s['selected_head_expected_max_abs_error']==s['nonselected_head_max_abs_delta']==s['outside_window_max_abs_delta']==0
                max_error=max(max_error,s['partition_max_abs_error'])
                if phase=='validation':assert all(s[k] for k in ('query_exact','key_exact','value_exact','attention_exact','explicit_source_reference_exact'))
            assert sorted(actual)==sorted(required) and len(actual)==len(required)
        details.append({'base_problem_id':b,'event':e['event'],'condition':row['condition'],'arms':len(row['arms'])})
    assert max_error<=1e-5
    checks=dict.fromkeys(['frozen_inputs_exact','complete_expected_coverage','four_A6000_ranks','validated_code_unchanged',
        'all_scores_finite_and_readouts_exact','event_partitions_and_histories_exact','all_source_positions_layers_queries_exact',
        'all32_heads_only_declared_source_values_removed','QKV_and_attention_not_modified','source_reduction_error_bounded',
        'no_passive_features_before_label_freeze','all_required_replays_exact'],True)
    if phase=='validation':checks.update({'unhooked_and_noop_exact':True,'cache_clones_and_prefixes_exact':True,'independent_source_reconstruction_exact':True})
    result={'passed':True,'phase':phase,'run_id':run_id,'checks':checks,'N_unique_bases':len(items),'event_files':len(rows),
            'arms':arms,'source_calls':calls,'max_partition_error':max_error,'code_sha256':code,
            'raw_sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths},'details':details}
    destination={'validation':'audit/mechanical_validation.json','causal':'phase_b_causal/causal_run_complete.json',
                 'semantic':'phase_c_counterfactual/semantic_run_complete.json'}[phase]
    write_json(OUT/destination,result)
    print({k:v for k,v in result.items() if k not in ('code_sha256','raw_sha256','details')})
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=['validation','causal','semantic'],required=True)
    p.add_argument('--run-id',required=True);a=p.parse_args();audit(a.phase,a.run_id)
