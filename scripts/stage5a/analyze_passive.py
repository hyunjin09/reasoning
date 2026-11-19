"""Audit passive replays, freeze discovery references, then evaluate confirmation."""
import argparse,math
from collections import Counter
from datetime import datetime,timezone
import numpy as np
from scripts.stage5a.prepare import ROOT,OUT,read_json,read_jsonl,write_json,write_jsonl,sha
from scripts.stage5a.run_passive import verify_labels
from visual_reasoning.stage5a.annotation import canonical_source_class
from visual_reasoning.stage5a.analysis import normalize_roi


METRICS=['qk_cosine','raw_qk_dot','scaled_logit','attention_mass','attention_density','alpha_v_norm','post_wo_norm']


def reconstruct(state):
    if not state['available']:return
    assert set(state['telemetry'])=={'28','29'}
    for layer,t in state['telemetry'].items():
        assert len(t['per_head'])==32 and t['all_values_finite']
        for name,g in t['groups'].items():
            per=[h['groups'][name] for h in t['per_head']]
            for metric in METRICS:
                assert math.isclose(sum(p[metric] for p in per)/32,g['mean_'+metric],rel_tol=1e-8,abs_tol=1e-8)
            for p in per:
                assert math.isclose(p['attention_density']*p['token_count'],p['attention_mass'],rel_tol=2e-6,abs_tol=2e-6)
                assert math.isclose(float(np.linalg.norm(p['alpha_v_vector'])),p['alpha_v_norm'],rel_tol=2e-6,abs_tol=2e-6)
        partition=('sink','visual','prompt_text','reasoning')
        assert abs(sum(t['groups'][r]['mean_attention_mass'] for r in partition)-1)<.015
        assert sum(t['groups'][r]['token_count'] for r in partition)==t['visible_source_token_count']


def summarize(state):
    if not state['available']:return None
    telemetry=state['telemetry'];groups={}
    for name,g in telemetry['28']['groups'].items():
        groups[name]={'token_count':g['token_count'],**{m:sum(t['groups'][name]['mean_'+m] for t in telemetry.values())/2 for m in METRICS}}
    return {'groups':groups,'entropy':state['predictive_entropy'],
            'residual_norm':sum(state['residual_norms'].values())/2,'attention_output_norm':sum(state['attention_output_norms'].values())/2,
            'attention_entropy':sum(t['mean_attention_entropy'] for t in telemetry.values())/2}


def historical_references():
    references=[];hashes={};compatible={r['base_problem_id'] for r in read_jsonl(OUT/'cohort/historical_anchor_manifest.jsonl') if r['quantitative_attention_discovery_compatible']}
    for item in read_jsonl(ROOT/'outputs/stage4a/cohort/primary_manifest.jsonl'):
        b=item['base_problem_id']
        if b not in compatible:continue
        meta_path=ROOT/item['asset_metadata'];m=read_json(meta_path);hashes[str(meta_path.relative_to(ROOT))]=sha(meta_path)
        generation=read_json(ROOT/m['artifact_dir']/'generation.json');reasoning=generation['full_generated_response'].split('</think>')[0]
        for name,e in m['events'].items():
            paths=list((ROOT/'outputs/stage4a/raw/primary_01').glob(f'shard_*/{b}/OO/{name}.json'));assert len(paths)==1
            p=paths[0];r=read_json(p);hashes[str(p.relative_to(ROOT))]=sha(p)
            role='T' if e['fact']=='A' else 'M';ts=r['arms']['N']['telemetry'];fact=m['facts'][e['fact']]
            references.append({'reference_id':'stage4a_'+b+'_'+name,'base_problem_id':'historical_'+b,'source_class':canonical_source_class({**fact,'value':fact['original_value'],'cf_allowed':True}),
                'token_count':len(m['source_groups'][e['fact']]),'reasoning_progress':e['match_start']/max(1,len(reasoning)),
                'sequence_length':m['prompt_metadata']['prompt_token_count']+e['candidate_start_token'],
                'mass':sum(t['all']['groups'][role]['mean_attention_mass'] for t in ts.values())/2,
                'density':sum(t['all']['groups'][role]['mean_attention_density'] for t in ts.values())/2})
    assert len(references)==144
    return references,hashes


def main(run_id):
    verify_labels();items=read_jsonl(OUT/'cohort/causal_atlas_manifest.jsonl')
    metas={i['base_problem_id']:read_json(ROOT/i['asset_metadata']) for i in items}
    annotations={e['event_id']:e for e in read_jsonl(OUT/'annotations/events.jsonl') if e['split']!='natural_only'}
    labels={e['event_id']:e for e in read_jsonl(OUT/'annotations/causal_labels.jsonl')}
    paths=sorted((OUT/'raw'/run_id).glob('shard_*/*/E*.json'));rows=[read_json(p) for p in paths]
    assert len(rows)==len(annotations)==347 and {r['event_id'] for r in rows}==set(annotations)
    envs=[read_json(OUT/'raw'/run_id/f'shard_{rank:02d}/environment.json') for rank in range(4)]
    assert all(read_json(OUT/'raw'/run_id/f'shard_{rank:02d}/run_summary.json')['completed'] for rank in range(4))
    assert all(e['labels_sha256']==sha(OUT/'annotations/causal_label_freeze.json') and e['code_sha256']==envs[0]['code_sha256'] and 'A6000' in e['gpu_name'] for e in envs)
    assert all(sha(ROOT/p)==h for p,h in envs[0]['code_sha256'].items())
    prior_count=0;features=[];roi_records=[]
    for r in rows:
        assert r['native_causal_replay_exact'];e=annotations[r['event_id']];m=metas[r['base_problem_id']]
        reconstruct(r['current']);reconstruct(r['prior']);prior_count+=r['prior']['available']
        current=summarize(r['current']);prior=summarize(r['prior']);g=current['groups'];label=labels[r['event_id']]
        row={**label,'sequence_length':m['prompt_metadata']['prompt_token_count']+e['candidate_start_token'],
            'roi_token_count':len(e['source_groups']['T']),'entropy':current['entropy'],'residual_norm':current['residual_norm'],
            'attention_output_norm':current['attention_output_norm'],'attention_entropy':current['attention_entropy'],
            'sink_mass':g['sink']['attention_mass'],'sink_release':prior['groups']['sink']['attention_mass']-g['sink']['attention_mass'] if prior else None,
            'visual_share':g['visual']['attention_mass'],'candidate_margin':r['current']['D'],'prior_available':bool(prior)}
        row['T_attention_gain']=g['T']['attention_mass']-prior['groups']['T']['attention_mass'] if prior else None
        for name in ('T','M','X','I','R16','text_entity','text_control'):
            for metric in METRICS:row[name+'_'+metric]=g[name][metric] if name in g else None
        for alt in ('M','X','I'):
            row['T_to_'+alt+'_density_ratio']=g['T']['attention_density']/g[alt]['attention_density'] if alt in g and g[alt]['attention_density']>0 else None
        control=next((name for name in ('I','X') if name in g),None)
        row['QK_control']=control;row['QK_T_minus_control']=g['T']['scaled_logit']-g[control]['scaled_logit'] if control else None
        for name in ('T','M','X','I'):row['VSD_'+name]=label['VSD'].get(name)
        row['CE_minus_sham']=label['CE_minus_abs_sham'];row['TE_T']=label['TE_VSD'].get('T');row['alphaV_T']=g['T']['alpha_v_norm']
        partition=('visual','prompt_text','reasoning','sink')
        delta={name:g[name]['attention_mass']-prior['groups'][name]['attention_mass'] for name in partition} if prior else {}
        row['source_partition_mass_delta']=delta;row['largest_gaining_source_group']=max(delta,key=delta.get) if delta else None;row['largest_losing_source_group']=min(delta,key=delta.get) if delta else None
        for role in ('T','M','X','I'):
            if role not in g:continue
            ids=e['source_identities'].get(role,e['source_identities']['T'] if role=='M' and e['roi_aliases'].get('M')=='T' else [])
            source_class=canonical_source_class(m['facts'][ids[0]]) if len(ids)==1 else e['source_class'] if role=='T' else 'irrelevant_background' if role=='I' else 'joint_visual_source'
            row[role+'_token_count']=g[role]['token_count'];row[role+'_source_class']=source_class
            roi_records.append({'event_id':e['event_id'],'reference_id':'stage5a_'+e['event_id']+'_'+role,'base_problem_id':r['base_problem_id'],
                'split':e['split'],'role':role,'source_class':source_class,'token_count':g[role]['token_count'],
                'reasoning_progress':e['reasoning_progress'],'sequence_length':row['sequence_length'],
                'mass':g[role]['attention_mass'],'density':g[role]['attention_density']})
        features.append(row)
    historical,historical_hashes=historical_references()
    references=historical+[r for r in roi_records if r['split']=='discovery' and r['role']=='T']
    rule_path=OUT/'phase_g_mirage/frozen_rule.json'
    rule={'frozen_at':datetime.now(timezone.utc).isoformat(),'discovery_only':True,'confirmation_labels_or_features_used_to_choose_threshold':False,
        'high_density_percentile':.90,'minimum_reference_rois':8,'matching_rule':read_json(OUT/'config/passive_extraction_rule.json'),
        'reference_rois':references,'historical_raw_sha256':historical_hashes,'cohort_freeze_sha256':sha(OUT/'cohort/cohort_freeze_complete.json')}
    if rule_path.exists():
        old=read_json(rule_path);assert old['reference_rois']==references and old['matching_rule']==rule['matching_rule'];rule=old
    else:write_json(rule_path,rule)
    # Only this point applies the fixed discovery rule to held-out observations.
    normalized={}
    for r in roi_records:
        n=normalize_roi(r,references);normalized[r['event_id'],r['role']]=n;r['matched']=n
    for row in features:
        e=annotations[row['event_id']]
        for role in ('T','M','X','I'):
            n=normalized.get((row['event_id'],role),{})
            for metric in ('mass','density'):
                for statistic in ('z','percentile'):row[role+'_'+metric+'_'+statistic]=n.get(metric+'_'+statistic)
        pct=row['T_density_percentile'];row['high_attention']=pct>=.9 if pct is not None else None
        row['strict_mirage']=(row['high_attention'] is True and row['local_insensitive'] and row['semantic_null_with_sham_control'] and not row['alternative_dominant'])
        row['mirage_candidate_missing_CE']=(row['high_attention'] is True and row['unsupported_candidate_without_CE'])
        row['hallucinatory_mirage']=row['strict_mirage'] and row['local_visual_hallucination']
        row['benign_mirage']=row['strict_mirage'] and row['local_correctness']=='CORRECT'
        row['semantic_mention']=e['has_explicit_visual_claim'] or e['semantic_role']=='MENTION_ONLY'
        row['two_by_two_cell']=('mention' if row['semantic_mention'] else 'no_mention')+('_retrieval' if row['genuine_retrieval'] else '_no_retrieval')
        row['strict_alignment_only']=row['alignment_only_candidate'] and row['M_density_percentile'] is not None and row['M_density_percentile']>=.9
        row['primary_state']=('integration_failure' if row['integration_failure'] else row['hallucination_subtypes'][0] if row['hallucination_subtypes'] else
            'strict_mirage' if row['strict_mirage'] else 'alignment_only' if row['strict_alignment_only'] else 'refresh' if row['refresh'] else
            'verification' if row['verification'] else 'retrieval' if row['genuine_retrieval'] else 'weak_grounding_candidate' if row['mirage_candidate_missing_CE'] else 'unresolved')
    write_jsonl(OUT/'phase_e_internal/features.jsonl',features);write_jsonl(OUT/'phase_e_internal/roi_features.jsonl',roi_records)
    families={'attention':['attention_mass','attention_density','density_ratio','visual_share','percentile','_z'],
              'qk':['qk','scaled_logit','QK_'],'value':['alpha_v','post_wo','alphaV_'],
              'sink':['sink_','largest_','source_partition'],'state_uncertainty':['entropy','candidate_margin','residual_norm','attention_output_norm']}
    for name,patterns in families.items():write_jsonl(OUT/f'phase_e_internal/{name}_features.jsonl',
        [{k:v for k,v in r.items() if k in ('base_problem_id','event_id','split') or any(p in k for p in patterns)} for r in features])
    for split,destination in [('discovery','discovery.json'),('confirmation','confirmation.jsonl')]:
        selected=[r for r in features if r['split']==split]
        if destination.endswith('jsonl'):write_jsonl(OUT/'phase_g_mirage'/destination,selected)
        else:write_json(OUT/'phase_g_mirage'/destination,{'bases':len({r['base_problem_id'] for r in selected}),'events':len(selected),
            'matched_target_events':sum(r['T_density_percentile'] is not None for r in selected),'historical_reference_events':len(historical),'fresh_reference_events':len(references)-len(historical)})
    result={'passed':True,'run_id':run_id,'events':len(rows),'prior_events':prior_count,'native_replays_exact':len(rows),
        'all_head_aggregate_and_alphaV_reconstruction':True,'source_partition_normalization':True,'labels_frozen_before_run':True,
        'raw_sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths},'historical_reference_sha256':historical_hashes,
        'code_sha256':envs[0]['code_sha256'],'matched_target_events':sum(r['T_density_percentile'] is not None for r in features),
        'confirmation_strict_mirage':sum(r['strict_mirage'] for r in features if r['split']=='confirmation'),
        'confirmation_missing_CE_candidates':sum(r['mirage_candidate_missing_CE'] for r in features if r['split']=='confirmation')}
    write_json(OUT/'audit/telemetry_reconstruction.json',result)
    print({k:v for k,v in result.items() if not k.endswith('sha256')})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run-id',required=True);args=parser.parse_args();main(args.run_id)
