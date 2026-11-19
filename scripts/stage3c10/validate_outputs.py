#!/usr/bin/env python3
"""Independently recompute primary estimands and audit all saved execution traces."""
import math
from scripts.stage3c10.freeze_inputs import ROOT,OUT,read_json,read_jsonl,write_json,sha


def finite_tree(obj):
    if isinstance(obj,float):return math.isfinite(obj)
    if isinstance(obj,dict):return all(finite_tree(v) for v in obj.values())
    if isinstance(obj,list):return all(finite_tree(v) for v in obj)
    return True


def main():
    config=read_json(OUT/'config/stage3c10_config.json');assets={r['base_problem_id']:r for r in read_jsonl(OUT/'config/assets.jsonl')}
    primary=read_json(OUT/'phase_b_primary/primary_statistics.json');freeze=read_json(OUT/'phase_b_primary/primary_freeze.json')
    checks={k:True for k in ['historical_input_hashes','primary_raw_immutable','primary_statistics_immutable',
        'primary_exact_coverage','primary_formulas','all_trace_positions','all_trace_layers_heads',
        'all_trace_sources','canonical_partitions','all_finite','all_followup_replays','M_T_native_scores_exact',
        'primary_no_gated_filtering','Q_rescue_recipient_KV','temporal_gate','layer_gate','hpre_gate','annotation_blind_freeze',
        'secondary_coverage','all_phase_coverage','all_figure_files']}
    for name,h in read_json(OUT/'config/immutable_inputs.json')['sha256'].items(): checks['historical_input_hashes'] &= sha(ROOT/name)==h
    for name,h in freeze['raw_sha256'].items():checks['primary_raw_immutable'] &= sha(ROOT/name)==h
    checks['primary_statistics_immutable']=sha(OUT/'phase_b_primary/primary_statistics.json')==freeze['statistics_sha256']
    allpaths=list((OUT/'raw').glob('*/shard_*/*/target_*/*.json'));rows=[read_json(p) for p in allpaths]
    p_rows=[r for r in rows if r['phase']=='primary'];grouped={}
    expected={(b,t,s) for b in config['cohort_ids']['primary'] for t in config['targets'] for s in ['M','T']}
    checks['primary_exact_coverage']=len(p_rows)==96 and {(r['base_problem_id'],r['target_id'],r['state']) for r in p_rows}==expected
    for row in p_rows:grouped[(row['base_problem_id'],row['target_id'],row['state'])]=row['arms']
    for base in config['cohort_ids']['primary']:
        native=[grouped[(base,t,s)]['N']['none']['D'] for t in config['targets'] for s in ['M','T']]
        checks['M_T_native_scores_exact'] &= all(x==native[0] for x in native)
        for t in config['targets']:
            m=grouped[(base,t,'M')];a=grouped[(base,t,'T')]
            def effect(arms,name,roi='T'):
                return (arms['N']['none']['D']-arms['N'][roi]['D'])-(arms[name]['none']['D']-arms[name][roi]['D'])
            values={'rds_T':a['N']['none']['rds']-a['R16']['none']['rds'],'vsd_T':effect(a,'R16'),
                'did':effect(a,'R16')-effect(m,'R16'),
                'r16_minus_e16':effect(a,'R16')-effect(a,'E16') if 'E16' in a else None,
                'target_minus_irrelevant':effect(a,'R16')-effect(a,'R16','I'),
                'r16_minus_q':effect(a,'R16')-effect(a,'Q')}
            saved=primary['paired_effects_by_base'][t][base]
            checks['primary_formulas'] &= all(saved[k]==v for k,v in values.items())
    arm_count=0;source_calls=0
    for r in rows:
        item=assets[r['base_problem_id']];coord=item['states'][r['target_id']][r['state']];layer=r['routing_layer']
        checks['all_finite'] &= finite_tree(r)
        checks['canonical_partitions'] &= r['partition']==item['partition']
        if r['phase'] not in ['validation','primary']:checks['all_followup_replays'] &= r['validation_checks']['primary_baseline_exact']
        for name,roi_arms in r['arms'].items():
            for roi,arm in roi_arms.items():
                arm_count+=1
                checks['canonical_partitions'] &= arm['partition']==item['partition']
                checks['all_trace_positions'] &= arm['current_generated_index_zero_based']==coord['current_zero_based_index'] and arm['absolute_current_query']==coord['absolute_query_position']
                windows=coord['source_windows_generated_zero_based'];generated=None
                if name in ['R16','replay_R16','noop_R16','Q_all','Q_selected','hpre']:generated=windows['R16']
                elif name in windows:generated=windows[name]
                if name=='Q':expected_source=item['Q_positions']
                elif generated is not None:expected_source=[item['prompt_length']+i for i in generated]
                elif name.startswith('L'):
                    task=next(x for x in read_json(OUT/'analysis/layers_tasks.json')['tasks'] if x['target_id']==r['target_id'] and x['arm']==name)
                    expected_source=[item['prompt_length']+i for i in windows[f"R{task['k']}"]]
                else:expected_source=[]
                checks['all_trace_sources'] &= arm['trigger_positions']==expected_source
                if expected_source:
                    expected_layers=task['layers'] if name.startswith('L') else list(range(layer))
                    checks['all_trace_layers_heads'] &= arm['trigger_layers']==expected_layers
                trigger=[x for x in arm['source_audits'] if x['source_kind']=='trigger'];visual=[x for x in arm['source_audits'] if x['source_kind']=='visual_roi']
                checks['all_trace_layers_heads'] &= len(trigger)==len(arm['trigger_layers']) if expected_source else not trigger
                checks['all_trace_layers_heads'] &= len(visual)==(36 if roi in ['T','I'] else 0)
                for a in arm['source_audits']:
                    source_calls+=1
                    checks['all_trace_positions'] &= a['query_positions']==[coord['absolute_query_position']] and set(a['changed_query_positions'])<={coord['absolute_query_position']} and a['outside_window_max_abs_delta']==0
                    checks['all_trace_layers_heads'] &= a['selected_heads']==list(range(32))
                    checks['all_trace_sources'] &= a['source_positions']==(expected_source if a['source_kind']=='trigger' else item['routing_groups'][roi])
                    checks['all_trace_sources'] &= a['attention_unchanged_by_source_deletion'] and a['key_unchanged_by_source_deletion'] and a['value_unchanged_by_source_deletion']
                qa=arm['q_patch_audit']
                if qa:checks['Q_rescue_recipient_KV'] &= qa['recipient_key_exact'] and qa['recipient_value_exact'] and qa['nonselected_head_max_abs_delta']==0 and set(qa['changed_sequence_positions'])<={0}
                if name=='Q':checks['all_trace_sources'] &= all(item['prompt_token_ids'][i]!=151644 for i in expected_source) # Qwen im_start, also checked by tokenizer during freeze
    checks['primary_no_gated_filtering']=freeze['complete_before_gates'] and len(freeze['raw_sha256'])==96
    for phase,key,gate in [('temporal','temporal_gate','temporal_eligible'),('layers','layer_gate','layers_eligible')]:
        tasks=read_json(OUT/f'analysis/{phase}_tasks.json')['tasks'];eligible={t for t,g in freeze['gates'].items() if g[gate]}
        checks[key]={x['target_id'] for x in tasks}==eligible
        selected=[r for r in rows if r['phase']==phase];checks['all_phase_coverage'] &= len(selected)==24*len(eligible) and {(r['base_problem_id'],r['target_id']) for r in selected}=={(b,t) for b in config['cohort_ids']['primary'] for t in eligible}
    mediation=read_json(OUT/'phase_e_mediation/mediation_statistics.json')
    expected_hpre={t for t in config['targets'] if primary['statistics'][t]['vsd_T']['robust_positive'] and mediation[t]['primary_family_with_rescue']['q_rescue_rds']['robust_positive'] and not mediation[t]['primary_family_with_rescue']['q_rescue_vsd']['robust_positive']}
    tasks=read_json(OUT/'analysis/hpre_tasks.json')['tasks'];checks['hpre_gate']={x['target_id'] for x in tasks}==expected_hpre
    checks['all_phase_coverage'] &= sum(r['phase']=='hpre' for r in rows)==24*len(expected_hpre) and sum(r['phase']=='mediation' for r in rows)==48
    ann=read_json(OUT/'annotations/annotation_freeze.json');checks['annotation_blind_freeze']=not ann['selection_used_attention'] and not ann['position_scores_available'] and sha(OUT/'annotations/optional_recent_token_annotations.jsonl')==ann['annotation_sha256']
    pos=read_jsonl(OUT/'phase_f_secondary/recent_position_scan.jsonl')
    expected_pos={(b,t,s,d) for b in config['cohort_ids']['primary'] for t in config['targets'] for s in ['M','T'] for d in range(1,min(8,assets[b]['states'][t][s]['current_zero_based_index'])+1)}
    checks['secondary_coverage']=len(pos)==len(expected_pos) and {(r['base_problem_id'],r['target_id'],r['state'],r['distance']) for r in pos}==expected_pos
    index=read_json(OUT/'analysis/figures/index.json');checks['all_figure_files']=len(index)==16 and all((ROOT/r[k]).is_file() and (ROOT/r[k]).stat().st_size>1000 for r in index for k in ['png','pdf'])
    result={'passed':all(checks.values()),'checks':checks,'raw_state_files':len(rows),'scored_arms':arm_count,'source_layer_calls':source_calls,'position_rows':len(pos)}
    write_json(OUT/'audit/independent_artifact_validation.json',result);print(result)
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
