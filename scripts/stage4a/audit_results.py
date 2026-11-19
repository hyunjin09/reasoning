"""Independently reconstruct statistics and audit every saved Stage4A score."""
import math
from collections import Counter
import numpy as np
from scipy.stats import wilcoxon
from scripts.stage4a.prepare_config import ROOT, OUT, read_json, read_jsonl, write_json, sha
from scripts.stage4a.validate_mechanics import telemetry_valid

EVENTS=('A1','B','A2')
CONDITIONS=('OO','AO','OB','AB','A_sham','B_sham')


def independent_stats(values):
    v=np.array([values[b] for b in sorted(values,key=int)],dtype=float)
    means=v[np.random.default_rng(12348).integers(len(v),size=(10000,len(v)))].mean(1)
    return {'N_unique_bases':len(v),'mean':v.mean(),'median':np.median(v),'positive_count':sum(v>0),
            'positive_fraction':np.mean(v>0),'bootstrap_mean_ci95':np.quantile(means,[.025,.975]),
            'wilcoxon_p':float(wilcoxon(v,alternative='two-sided').pvalue) if np.any(v) else 1.}


def check_statistics(contrasts,saved):
    for k,v in contrasts.items():
        s=independent_stats(v)
        for metric,value in s.items():assert np.allclose(saved[k][metric],value,rtol=1e-11,atol=1e-14),(k,metric)
    keys=list(contrasts);p=np.array([independent_stats(contrasts[k])['wilcoxon_p'] for k in keys])
    order=np.argsort(p,kind='stable');adjust=np.minimum(1,np.maximum.accumulate(p[order]*np.arange(len(p),0,-1)))
    for rank,i in enumerate(order):
        s=saved[keys[i]];assert math.isclose(s['holm_p'],adjust[rank],abs_tol=1e-14,rel_tol=1e-10)
        expected=s['median']>0 and s['bootstrap_mean_ci95'][0]>0 and s['positive_fraction']>=.75 and adjust[rank]<.05
        assert s['robust_positive']==expected


def main():
    checks={};validation=read_json(OUT/'audit/mechanical_validation.json')
    cohort=read_json(OUT/'cohort/cohort_freeze_complete.json')
    primary=read_json(OUT/'phase_b_source_switch/primary_freeze.json')
    secondary=read_json(OUT/'analysis/secondary_evidence_freeze.json')
    frozen={**cohort['sha256'],**cohort['asset_metadata_sha256'],**validation['raw_sha256'],**primary['raw_sha256'],**secondary['raw_sha256']}
    checks['all_frozen_inputs_and_raw_hashes_unchanged']=all(sha(ROOT/p)==h for p,h in frozen.items())
    checks['mechanical_gate_15_of_15']=validation['passed'] and len(validation['checks'])==15 and all(validation['checks'].values())
    manifests={split:read_jsonl(OUT/f'cohort/{split}_manifest.jsonl') for split in ('validation','primary')}
    items={r['base_problem_id']:r for rows in manifests.values() for r in rows}
    metas={b:read_json(ROOT/r['asset_metadata']) for b,r in items.items()}
    v_bases={r['base_problem_id'] for r in manifests['validation']};p_bases={r['base_problem_id'] for r in manifests['primary']}
    d_bases={r['base_problem_id'] for r in read_jsonl(OUT/'phase_d_counterfactual_refresh/subset_manifest.jsonl')}
    checks['cohort_unique_disjoint_8_48_24']=len(v_bases)==8 and len(p_bases)==48 and not v_bases&p_bases and len(d_bases)==24 and d_bases<=p_bases
    checks['selection_blind']=all(not r['attention_used'] and not r['causal_scores_available'] for r in items.values())
    checks['independent_image_assets_and_layout']=all(m['layout_exact'] and m['pixel_validation']['passed']
        and all(sha(ROOT/p)==m['asset_sha256'][c] for c,p in m['paths'].items()) for m in metas.values())
    checks['roi_maps_disjoint_and_exact']=all(not set(m['source_groups']['A'])&set(m['source_groups']['B'])
        and all(m['source_groups'][x]==[m['prompt_metadata']['visual_token_indices'][i] for i in m['roi_mapping'][x]['local_positions']] for x in ('A','B')) for m in metas.values())
    code=read_json(OUT/'raw/validation_01/shard_00/run_config.json')['code_sha256']
    envs=[read_json(p) for p in (OUT/'raw').glob('*_01/shard_*/environment.json')]
    checks['all16_rank_environments_canonical']=len(envs)==16 and all(e['slurm_job_id']=='108548' and 'A6000' in e['gpu_name'] and e['world_size']==4 and e['code_sha256']==code for e in envs)
    checks['validated_runtime_code_unchanged']=all(sha(ROOT/p)==h for p,h in code.items())
    all_paths=sorted((OUT/'raw').glob('*_01/shard_*/*/*/*.json'))
    records={};source_calls=0;arms_count=0;max_partition_error=0.
    for p in all_paths:
        r=read_json(p);b=r['base_problem_id'];m=metas[b];e=m['events'][r['event']]
        prompt=m['prompt_metadata']['prompt_token_count'];t=e['current_query_zero_based'];end=e['candidate_start_token']
        assert t==end-1 and len(e['history_before_ed_token_ids'])==end and r['event_history_sha256']==e['history_before_ed_sha256']
        partition=[[i,min(i+2048,t-7)] for i in range(0,t-7,2048)]+[[i,i+1] for i in range(t-7,t+1)]
        assert r['image_layout_exact'] and all(r['validation_checks'].values())
        records[r['phase'],b,r['condition'],r['event']]=r
        for name,a in r['arms'].items():
            arms_count+=1
            assert a['finite'] and math.isfinite(a['D']) and a['D']==a['L_o']-a['L_c']
            assert a['partition']==partition and a['absolute_current_query']==prompt+t
            for direction,key in [('original','original_divergent_suffix_ids'),('counterfactual','counterfactual_divergent_suffix_ids')]:
                candidate=a[direction+'_candidate'];assert candidate['candidate_token_ids']==e[key]
            if r['phase']=='validation':assert a['clone_no_alias'] and a['past_cache_audit']['passed']
            if name=='unhooked':continue
            assert len(a['step_audits'])==8
            for i,s in enumerate(a['step_audits']):
                q=t-7+i;assert s['generated_query']==q and s['layers']==list(range(36)) and s['finite']
                assert s['active_roi']==(a['roi'] if q>=end-a['window'] else None)
                assert s['active_trigger']==(a['trigger'] and q==t)
            expected=[]
            if a['roi']:expected += [(a['roi'],layer,prompt+q) for q in range(end-a['window'],end) for layer in range(36)]
            if a['trigger']:expected += [('R16',layer,prompt+t) for layer in range(16,24)]
            actual=[]
            for audit in a['source_audits']:
                source_calls+=1;kind=audit['source_kind']
                actual.append((kind,audit['layer_index'],audit['query_positions'][0]))
                positions=(list(range(prompt+max(0,t-16),prompt+t)) if kind=='R16' else
                           sorted(set(m['source_groups']['A'])|set(m['source_groups']['B'])) if kind=='AB' else m['source_groups'][kind])
                assert audit['source_positions']==positions and audit['selected_heads']==list(range(32))
                assert not audit['qkv_directly_modified'] and not audit['attention_directly_modified']
                assert audit['all_outputs_finite'] and audit['partition_compute_dtype']=='float32'
                assert audit['selected_head_expected_max_abs_error']==audit['nonselected_head_max_abs_delta']==audit['outside_window_max_abs_delta']==0
                max_partition_error=max(max_partition_error,audit['partition_max_abs_error'])
            assert sorted(actual)==sorted(expected) and len(actual)==len(expected)
            if a['telemetry']:assert telemetry_valid(a['telemetry'])
    checks['all_source_calls_coordinates_and_isolation']=max_partition_error<=1e-5
    checks['all_scores_finite_and_readouts_exact']=True
    checks['all_passive_telemetry_reconstructs']=True
    checks['all_event_partitions_and_histories_exact']=True
    expected=set()
    for phase,bs,cs in [('validation',v_bases,CONDITIONS),('primary',p_bases,('OO',)),('trigger',p_bases,('OO',)),('semantic',d_bases,CONDITIONS)]:
        expected|={(phase,b,c,e) for b in bs for c in cs for e in EVENTS}
    checks['complete864_event_images_no_duplicates']=set(records)==expected and len(all_paths)==len(expected)==864
    for phase,bs in [('trigger',p_bases),('semantic',d_bases)]:
        for b in bs:
            for e in EVENTS:
                a=records[phase,b,'OO',e]['arms']['N'];n=records['primary',b,'OO',e]['arms']['N']
                assert all(a[k]==n[k] for k in ('D','L_o','L_c','current_logits_sha256','original_candidate','counterfactual_candidate'))
    checks['all216_primary_denominator_replays_exact']=True
    contrasts={k:{} for k in ('S_A1','S_B','S_A2','Switch_AB','Refresh_BA','demanded_minus_irrelevant','TS_A1','TS_B','TS_A2')}
    dynamic=[];semantic_values={f'{e}_{k}':{} for e in EVENTS for k in ('demanded_effect','semantic_selectivity','semantic_minus_sham')}
    base_stats=read_json(OUT/'phase_b_source_switch/dynamic_selectivity.json')['W2']
    for b in p_bases:
        effects={};i_diffs=[]
        for e in EVENTS:
            r=records['primary',b,'OO',e]['arms'];a=r['N']['D']-r['A_W2']['D'];bv=r['N']['D']-r['B_W2']['D']
            s=(bv-a) if e=='B' else (a-bv);contrasts['S_'+e][b]=s;effects[e]=(a,bv)
            assert s==base_stats[b]['S_'+e]
            if 'I_W2' in r:i_diffs.append((bv if e=='B' else a)-(r['N']['D']-r['I_W2']['D']))
            tr=records['trigger',b,'OO',e]['arms'];ta=a-(tr['R16']['D']-tr['R16_A_W2']['D']);tb=bv-(tr['R16']['D']-tr['R16_B_W2']['D'])
            contrasts['TS_'+e][b]=(tb-ta) if e=='B' else (ta-tb)
        contrasts['Switch_AB'][b]=contrasts['S_A1'][b]+contrasts['S_B'][b]
        contrasts['Refresh_BA'][b]=contrasts['S_B'][b]+contrasts['S_A2'][b]
        if len(i_diffs)==3:contrasts['demanded_minus_irrelevant'][b]=sum(i_diffs)/3
        is_dynamic=all(contrasts['S_'+e][b]>0 and effects[e][1 if e=='B' else 0]>.05 for e in EVENTS)
        assert is_dynamic==base_stats[b]['dynamic'];dynamic.append(is_dynamic)
    final=read_json(OUT/'analysis/selection_switch_refresh.json')
    check_statistics(contrasts,final['primary_family'])
    checks['nine_primary_tests_independently_recomputed']=True
    checks['36_dynamic_classes_independently_recomputed']=sum(dynamic)==36
    phenotypes=read_json(OUT/'analysis/native_failure_phenotypes.json')['bases']
    for b,r in base_stats.items():
        v=r['VSD'];labels=phenotypes[b]
        assert labels['failed_switch_A_dominant']==(v['B']['A']>v['B']['B'] and v['B']['A']>.05)
        assert labels['failed_refresh_stale_B']==(v['A2']['B']>v['A2']['A'] and v['A2']['B']>.05)
        assert labels['tied_retrieval_events']==[e for e in EVENTS if v[e]['A']==v[e]['B'] and v[e]['A']>.05]
    checks['strict_stale_dominance_and_ties_distinguished']=True
    for b in d_bases:
        for e in EVENTS:
            d={c:records['semantic',b,c,e]['arms']['N']['D'] for c in CONDITIONS}
            a=(d['OO']-d['AO']+d['OB']-d['AB'])/2;bv=(d['OO']-d['OB']+d['AO']-d['AB'])/2
            demand,other=(bv,a) if e=='B' else (a,bv)
            semantic_values[e+'_demanded_effect'][b]=demand
            semantic_values[e+'_semantic_selectivity'][b]=demand-other
            semantic_values[e+'_semantic_minus_sham'][b]=demand-abs(d['OO']-d['B_sham' if e=='B' else 'A_sham'])
    check_statistics(semantic_values,read_json(OUT/'phase_d_counterfactual_refresh/counterfactual_refresh_statistics.json')['secondary_nine_test_family'])
    checks['nine_secondary_tests_independently_recomputed']=True
    checks['phase_c_gate_open_before_trigger']=primary['phase_c_gate_open'] and (primary['primary_family']['Switch_AB']['robust_positive'] or primary['primary_family']['Refresh_BA']['robust_positive'])
    checks['forty_irrelevant_bases_match_frozen_manifest']=set(contrasts['demanded_minus_irrelevant'])=={r['base_problem_id'] for r in read_jsonl(OUT/'cohort/irrelevant_subset_manifest.jsonl')}
    fig=read_json(OUT/'analysis/figures/figure_index.json')
    checks['sixteen_png_pdf_figures']=len(fig['figures'])==16 and all((OUT/'analysis/figures'/f'{r["stem"]}.{ext}').stat().st_size>1000 for r in fig['figures'] for ext in ('png','pdf'))
    checks={k:bool(v) for k,v in checks.items()}
    output={'passed':all(checks.values()),'checks':checks,'check_count':len(checks),'event_files':len(all_paths),
            'arms':arms_count,'source_layer_query_calls':source_calls,'max_partition_error':max_partition_error,
            'frozen_hashes_verified':len(frozen),'scope':'Independent algebra/statistics and full raw-artifact audit by main agent; no independent reviewer agent claimed.'}
    write_json(OUT/'audit/final_artifact_validation.json',output)
    print(output)
    assert output['passed']


if __name__=='__main__':main()
