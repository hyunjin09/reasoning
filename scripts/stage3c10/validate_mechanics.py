#!/usr/bin/env python3
"""Validate actual seven-base query/source/cache traces before primary scoring."""
from scripts.stage3c10.freeze_inputs import ROOT,OUT,read_json,read_jsonl,write_json,sha


def audit_rows(rows,assets):
    checks={k:True for k in ['mt_coordinates','routing_layers','rds_reconstruction','r16_positions',
        'e16_positions','prompt_positions','fp32_partition','current_query_only','past_cache_exact',
        'visual_kv_exact','target_t0_semantics','irrelevant_roi_isolated','deterministic_replay','self_noop_exact','finite']}
    details=[]
    for row in rows:
        item=assets[row['base_problem_id']];target=row['target_id'];state=row['state']
        coord=item['states'][target][state];layer=29 if target=='target_a' else 28
        checks['mt_coordinates'] &= row['frozen_state']==coord
        checks['routing_layers'] &= row['routing_layer']==layer
        vc=row['validation_checks']
        checks['deterministic_replay'] &= vc['replay_exact']
        checks['self_noop_exact'] &= vc['noop_exact'] and vc['self_Q_exact'] and vc['inherited_none_exact']
        checks['target_t0_semantics'] &= vc['inherited_T_exact']
        for name,rois in row['arms'].items():
            for roi,arm in rois.items():
                checks['finite'] &= arm['finite'] and all(r['finite'] for r in arm['layer_norms'])
                checks['past_cache_exact'] &= arm['past_cache_audit']['passed']
                # All visual tokens precede the current query, so measured full-past
                # K/V equality is a strict superset of the visual-invariance check.
                checks['visual_kv_exact'] &= arm['past_cache_audit']['passed'] and max(item['visual_positions'])<arm['past_cache_audit']['past_length']
                expected=[]
                if name in ['R16','noop_R16','replay_R16','Q_all','Q_selected']:
                    expected=[item['prompt_length']+i for i in coord['source_windows_generated_zero_based']['R16']]
                    checks['r16_positions'] &= arm['trigger_positions']==expected
                elif name=='E16':
                    expected=[item['prompt_length']+i for i in coord['source_windows_generated_zero_based']['E16']]
                    checks['e16_positions'] &= arm['trigger_positions']==expected
                elif name=='Q':
                    expected=item['Q_positions'];checks['prompt_positions'] &= arm['trigger_positions']==expected
                trigger_a=[a for a in arm['source_audits'] if a['source_kind']=='trigger']
                if expected:
                    checks['routing_layers'] &= sorted(a['layer_index'] for a in trigger_a)==list(range(layer))
                for a in arm['source_audits']:
                    checks['fp32_partition'] &= a['partition_compute_dtype']=='float32' and a['partition_max_abs_error']<=1e-5
                    checks['current_query_only'] &= a['query_positions']==[coord['absolute_query_position']] and a['outside_window_max_abs_delta']==0 and a['nonselected_head_max_abs_delta']==0
                    checks['current_query_only'] &= a['attention_unchanged_by_source_deletion'] and a['key_unchanged_by_source_deletion'] and a['value_unchanged_by_source_deletion']
                    if a['source_kind']=='trigger':checks['current_query_only'] &= a['source_positions']==expected
                    checks['finite'] &= a['all_outputs_finite']
                visual=[a for a in arm['source_audits'] if a['source_kind']=='visual_roi']
                if roi in ['T','I']:
                    valid=len(visual)==36 and sorted(a['layer_index'] for a in visual)==list(range(36)) and all(a['selected_heads']==list(range(32)) and a['source_positions']==item['routing_groups'][roi] for a in visual)
                    checks['target_t0_semantics' if roi=='T' else 'irrelevant_roi_isolated'] &= valid
                else:checks['irrelevant_roi_isolated'] &= not visual
                for summary in arm['routing'].values():
                    g=summary['groups']
                    expected_rds=g['T']['mean_scaled_logit']-g['M']['mean_scaled_logit']
                    checks['rds_reconstruction'] &= summary['RDS_T_vs_M']==expected_rds
                    for group in ['T','M','I']:
                        mean=sum(h['groups'][group]['mean_scaled_logit'] for h in summary['per_head'])/len(summary['per_head'])
                        checks['rds_reconstruction'] &= abs(mean-g[group]['mean_scaled_logit'])<1e-12
                qa=arm['q_patch_audit']
                if qa:
                    valid=qa['recipient_key_exact'] and qa['recipient_value_exact'] and qa['nonselected_head_max_abs_delta']==0 and set(qa['changed_sequence_positions'])<={0}
                    checks['self_noop_exact'] &= valid
                details.append({'base_problem_id':row['base_problem_id'],'target_id':target,'state':state,
                    'arm':name,'roi':roi,'D':arm['D'],'rds':arm['rds'],'past_cache_exact':arm['past_cache_audit']['passed'],
                    'source_layer_calls':len(arm['source_audits']),'max_partition_error':max((a['partition_max_abs_error'] for a in arm['source_audits']),default=0.)})
    return {k:bool(v) for k,v in checks.items()},details


def main():
    assets={x['base_problem_id']:x for x in read_jsonl(OUT/'config/assets.jsonl') if x['cohort_role']=='validation'}
    paths=list((OUT/'raw/validation').glob('shard_*/*/target_*/*.json'))
    rows=[read_json(p) for p in paths]
    expected={(b,t,s) for b in assets for t in ['target_a','target_b'] for s in ['M','T']}
    assert len(rows)==28 and {(r['base_problem_id'],r['target_id'],r['state']) for r in rows}==expected
    checks,details=audit_rows(rows,assets)
    frozen=read_json(OUT/'config/routing_readout.json')
    checks['rds_reconstruction'] &= sha(ROOT/'code/visual_reasoning/stage3c3/metrics.py')==frozen['source_sha256']
    result={'passed':all(checks.values()),'checks':checks,'N_unique_bases':7,'state_files':28,
        'scored_arms':len(details),'source':'raw/validation','details':details}
    write_json(OUT/'audit/mechanical_validation.json',result)
    mapping={'mt_coordinate_audit':'mt_coordinates','rds_reconstruction':'rds_reconstruction',
        'source_partition_audit':'fp32_partition','r16_position_audit':'r16_positions','e16_position_audit':'e16_positions',
        'prompt_source_audit':'prompt_positions','current_query_selectivity':'current_query_only',
        't0_target_suppression_audit':'target_t0_semantics','irrelevant_roi_audit':'irrelevant_roi_isolated',
        'q_patch_audit':'self_noop_exact','self_patch_validation':'self_noop_exact','deterministic_replay':'deterministic_replay'}
    for name,key in mapping.items():write_json(OUT/f'audit/{name}.json',{'passed':checks[key],'check':key,'evidence':'audit/mechanical_validation.json','N_unique_bases':7})
    print({k:v for k,v in result.items() if k!='details'})
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
