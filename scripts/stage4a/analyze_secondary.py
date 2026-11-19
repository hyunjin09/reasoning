"""Complete the fixed Stage4A analyses without changing frozen primary evidence."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from scripts.stage4a.prepare_config import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha
from scripts.stage4a.run_scores import verify_freeze, score_equal
from visual_reasoning.stage3c8.analysis import inferential_summary, summarize_effect, holm_adjust
from visual_reasoning.stage4a.analysis import EVENTS, primary_family, trigger_contrasts, semantic_contrasts, failure_phenotypes


def load_phase(run_id, bases, conditions):
    folder = OUT/'raw'/run_id
    summaries = [read_json(p) for p in folder.glob('shard_*/run_summary.json')]
    assert len(summaries) == 4 and all(r['completed'] for r in summaries)
    paths = sorted(folder.glob('shard_*/*/*/*.json'))
    rows = [read_json(p) for p in paths]
    keys = {(r['base_problem_id'], r['condition'], r['event']) for r in rows}
    expected = {(b,c,e) for b in bases for c in conditions for e in EVENTS}
    assert keys == expected and len(rows) == len(expected)
    assert all(r['image_layout_exact'] and all(a['finite'] and a['clone_no_alias'] is not False
               and all(s['finite'] for s in a['step_audits']) for a in r['arms'].values()) for r in rows)
    return {(r['base_problem_id'],r['condition'],r['event']):r for r in rows}, paths


def secondary_family(contrasts):
    stats = {key:inferential_summary(values) for key,values in contrasts.items()}
    for key,p in zip(stats,holm_adjust([s['wilcoxon_p'] for s in stats.values()])):
        s=stats[key];s['holm_p']=p
        s['robust_positive']=bool(s['median']>0 and s['bootstrap_mean_ci95'][0]>0
                                  and s['positive_fraction']>=.75 and p<.05)
    return stats


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--trigger-run',default='trigger_01')
    parser.add_argument('--semantic-run',default='semantic_01')
    args=parser.parse_args()
    verify_freeze()
    frozen=read_json(OUT/'phase_b_source_switch/primary_freeze.json')
    for p,digest in frozen['raw_sha256'].items():assert sha(ROOT/p)==digest
    primary=read_json(OUT/'phase_b_source_switch/dynamic_selectivity.json')
    w2,w8=primary['W2'],primary['W8'];bases=list(w2)
    p_rows,_=load_phase(frozen['run_id'],bases,['OO'])
    trigger={};all_paths=[]
    if frozen['phase_c_gate_open']:
        t_rows,paths=load_phase(args.trigger_run,bases,['OO']);all_paths+=paths
        for b in bases:
            for e in EVENTS:
                assert score_equal(t_rows[b,'OO',e]['arms']['N'],p_rows[b,'OO',e]['arms']['N'])
                assert t_rows[b,'OO',e]['validation_checks']['primary_native_exact']
            trigger[b]=trigger_contrasts(w2[b],{e:t_rows[b,'OO',e] for e in EVENTS})
        write_jsonl(OUT/'phase_c_trigger/r16_l16_23.jsonl',[
            {'base_problem_id':b,'event':e,'native_VSD':w2[b]['VSD'][e],
             'R16_VSD':trigger[b]['R16_VSD'][e],'TE':trigger[b]['TE'][e],
             'native_D':t_rows[b,'OO',e]['arms']['N']['D'],'R16_D':t_rows[b,'OO',e]['arms']['R16']['D']}
            for b in bases for e in EVENTS])
    else:
        write_jsonl(OUT/'phase_c_trigger/r16_l16_23.jsonl',[])
    family=primary_family(w2,trigger)
    write_json(OUT/'phase_c_trigger/trigger_selectivity.json',{'gate_open':frozen['phase_c_gate_open'],'bases':trigger})
    write_json(OUT/'phase_c_trigger/trigger_statistics.json',{
        'gate_open':frozen['phase_c_gate_open'],'layers':[16,17,18,19,20,21,22,23],
        'current_query_only':True,'same_native_denominator_exact':True,
        'nine_test_primary_family':family,
        'TE_descriptive':{e:{x:summarize_effect({b:r['TE'][e][x] for b,r in trigger.items()})
                             for x in ('A','B')} for e in EVENTS}})
    subset=read_jsonl(OUT/'phase_d_counterfactual_refresh/subset_manifest.jsonl')
    d_bases=[r['base_problem_id'] for r in subset]
    assert d_bases==bases[:24]
    d_rows,paths=load_phase(args.semantic_run,d_bases,['OO','AO','OB','AB','A_sham','B_sham']);all_paths+=paths
    semantic={}
    for b in d_bases:
        for e in EVENTS:
            assert score_equal(d_rows[b,'OO',e]['arms']['N'],p_rows[b,'OO',e]['arms']['N'])
            assert d_rows[b,'OO',e]['validation_checks']['primary_native_exact']
            assert len({d_rows[b,c,e]['event_history_sha256'] for c in ('OO','AO','OB','AB','A_sham','B_sham')})==1
        semantic[b]=semantic_contrasts({c:{e:d_rows[b,c,e] for e in EVENTS} for c in ('OO','AO','OB','AB','A_sham','B_sham')})
    for source in ('A','B'):
        write_jsonl(OUT/f'phase_d_counterfactual_refresh/{source.lower()}_edit_results.jsonl',[
            {'base_problem_id':b,'event':e,'effect':r[e][source+'_effect'],
             'factorial_contexts':r[e][source+'_factorial_contexts'],'all_condition_D':r[e]['D']}
            for b,r in semantic.items() for e in EVENTS])
    write_jsonl(OUT/'phase_d_counterfactual_refresh/double_edit_results.jsonl',[
        {'base_problem_id':b,'event':e,'OO_minus_AB':r[e]['D']['OO']-r[e]['D']['AB'],
         'all_condition_D':r[e]['D']} for b,r in semantic.items() for e in EVENTS])
    write_jsonl(OUT/'phase_d_counterfactual_refresh/sham_results.jsonl',[
        {'base_problem_id':b,'event':e,**{k:r[e][k] for k in ('A_sham_signed','B_sham_signed','demanded_sham_magnitude','semantic_minus_sham')}}
        for b,r in semantic.items() for e in EVENTS])
    d_stats=secondary_family({f'{e}_{metric}':{b:r[e][metric] for b,r in semantic.items()}
        for e in EVENTS for metric in ('demanded_effect','semantic_selectivity','semantic_minus_sham')})
    d_summary={'N_unique_bases':len(d_bases),'secondary_nine_test_family':d_stats,'bases':semantic,
        'OO_primary_exact':True,'fixed_history_exact':True,
        'factorial_context_descriptive':{e:{source:[summarize_effect({b:r[e][source+'_factorial_contexts'][i] for b,r in semantic.items()})
                                                   for i in (0,1)] for source in ('A','B')} for e in EVENTS},
        'boundary':'Secondary fixed native history; image changed throughout replay, not spliced into the cache only at A2. No natural-rollout or image-update-time claim.'}
    write_json(OUT/'phase_d_counterfactual_refresh/counterfactual_refresh_statistics.json',d_summary)
    descriptive={}
    for window,ws in [('W2',w2),('W8',w8)]:
        descriptive[window]={e:{x:summarize_effect({b:r['VSD'][e][x] for b,r in ws.items()}) for x in ('A','B')} for e in EVENTS}
    joint={e:{'joint':summarize_effect({b:r['joint_AB'][e] for b,r in w2.items()}),
              'joint_minus_demanded':summarize_effect({b:r['joint_AB'][e]-r['VSD'][e]['B' if e=='B' else 'A'] for b,r in w2.items()})} for e in EVENTS}
    result={'N_unique_bases':48,'primary_family':family,'W8_sensitivity_family':primary_family(w8),
            'VSD_descriptive':descriptive,'joint_secondary':joint,
            'dynamic_W2_count':sum(r['dynamic'] for r in w2.values()),'dynamic_W8_count':sum(r['dynamic'] for r in w8.values())}
    write_json(OUT/'analysis/selection_switch_refresh.json',result)
    manifest=read_jsonl(OUT/'cohort/primary_manifest.jsonl')
    heterogeneity={}
    for correct in (True,False):
        group=[r['base_problem_id'] for r in manifest if r['final_correct']==correct]
        heterogeneity[str(correct)]={'N':len(group),'base_ids':group,'dynamic_W2_count':sum(w2[b]['dynamic'] for b in group),
            'contrasts':{k:summarize_effect({b:w2[b][k] for b in group}) for k in ('S_A1','S_B','S_A2','Switch_AB','Refresh_BA')}}
    write_json(OUT/'analysis/target_heterogeneity.json',{'descriptive_only_no_subgroup_selection':True,'final_correctness':heterogeneity,
        'events':{e:{'native_D':summarize_effect({b:p_rows[b,'OO',e]['arms']['N']['D'] for b in bases}),
                    'local_original_preferred_count':sum(p_rows[b,'OO',e]['arms']['N']['D']>0 for b in bases)} for e in EVENTS}})
    phenotypes={b:failure_phenotypes(r) for b,r in w2.items()}
    write_json(OUT/'analysis/native_failure_phenotypes.json',{'basis':'W2 causal scores only; descriptive labels can overlap; dominance is strict, ties separate',
        'floor':.05,'bases':phenotypes})
    counts={k:sum(bool(r[k]) for r in phenotypes.values()) for k in next(iter(phenotypes.values()))}
    o1=all(family[k]['robust_positive'] for k in ('S_A1','S_B','S_A2','Switch_AB','Refresh_BA'))
    o2=all(family[k]['robust_positive'] for k in ('S_B','S_A2','Refresh_BA'))
    o3=all(family['TS_'+e]['robust_positive'] for e in EVENTS)
    claims={'O1_dynamic_multi_evidence_retrieval':o1,'O2_native_visual_reengagement':o2,
        'O3_trigger_retargeting':o3,'O4_persistent_joint_without_crossover':False if o1 else None,
        'O5_sticky_dominant_pattern':False,'O6_local_assay_insufficient':False if o1 else None,
        'phenotype_base_counts':counts,
        'strong_secondary_semantic_pattern':all(s['robust_positive'] for s in d_stats.values()),
        'interpretation_boundaries':['Local numeric fact-reference events, including tentative readings; not all are correct reasoning steps.',
            'W2 necessity is conditional on the tested contribution intervention, not proof of unique information flow.',
            'Fixed-history counterfactuals replay the entire history with each image; they do not time-localize acquisition to A2.',
            'A few stale signatures do not establish that refresh failure is common or explain why it occurs.',
            'Passive attention and restored routing do not establish Q mediation.',
            'Independent bases can share geometry templates; generalization beyond the selected editable numeric-label assay is unresolved.']}
    write_json(OUT/'analysis/paper_claim_assessment.json',claims)
    control_manifest=read_jsonl(OUT/'cohort/irrelevant_subset_manifest.jsonl')
    observed={b for b,r in w2.items() if 'demanded_minus_irrelevant' in r}
    assert observed=={r['base_problem_id'] for r in control_manifest}
    omitted=[]
    for r in manifest:
        if r['base_problem_id'] in observed:continue
        meta=read_json(ROOT/r['asset_metadata'])
        omitted.append({'base_problem_id':r['base_problem_id'],'aggregate_flag':meta.get('irrelevant_controls_validated'),
                        'per_roi_review':{k:v.get('manual_review') for k,v in meta['irrelevant_mapping'].items()}})
    write_json(OUT/'audit/irrelevant_subset_reconciliation.json',{'frozen_manifest_count':len(observed),'actual_scored_count':len(observed),
        'earlier_phase_memory_count_incorrect':47,'omitted':omitted,'resolution':'Preserve frozen40; correct prose only, no post-effect expansion.'})
    all_raw=list((OUT/'raw').glob('*_01/shard_*/*/*/*.json'))
    raw=[read_json(p) for p in all_raw]
    resources={'allocation':'108548','tmux':'9','node':'node07','gpus':4,'gpu_type':'RTX A6000',
        'new_slurm_allocations':0,'event_files':len(raw),'arms':sum(len(r['arms']) for r in raw),
        'max_allocated_GiB':max(r['peak_gpu_allocated_bytes'] for r in raw)/2**30,
        'max_reserved_GiB':max(r['peak_gpu_reserved_bytes'] for r in raw)/2**30,
        'summed_event_seconds':sum(r['runtime_seconds'] for r in raw),
        'rank_summaries':{str(p.relative_to(ROOT)):read_json(p) for p in (OUT/'raw').glob('*_01/shard_*/run_summary.json')},
        'generation_accounting':read_json(OUT/'cohort/generation_completion.json'),
        'timing_caveat':'Rank times exclude model loading; summed event time is work across parallel ranks, not wall time. Generation counted separately.'}
    write_json(OUT/'audit/resource_summary.json',resources)
    write_json(OUT/'analysis/secondary_evidence_freeze.json',{'frozen_at':datetime.now(timezone.utc).isoformat(),
        'raw_sha256':{str(p.relative_to(ROOT)):sha(p) for p in all_paths},
        'analysis_code_sha256':{p:sha(ROOT/p) for p in ['scripts/stage4a/analyze_secondary.py','code/visual_reasoning/stage4a/analysis.py']},
        'secondary_protocol_sha256':sha(OUT/'phase_d_counterfactual_refresh/secondary_analysis_protocol.json')})
    print({'primary':family,'secondary':d_stats,'claims':claims,'resources':{k:v for k,v in resources.items() if k not in ('rank_summaries','generation_accounting')}})


if __name__=='__main__':main()
