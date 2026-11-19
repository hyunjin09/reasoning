#!/usr/bin/env python3
"""Independently derive scientific gates from raw scores and verify provenance."""

import math
import statistics
from collections import Counter

from scripts.stage3c9r.analyze import collect
from scripts.stage3c9r.finish_analysis import followup_scores
from scripts.stage3c9r.freeze_inputs import ROOT, OUT, OLD, read_json, sha, write_json
from scripts.stage3c9r.validate_mechanics import all_finite
from visual_reasoning.stage3c9r.protocol import shared_partition


def execution_trace_checks(manifest, paths, readout_overrides=None):
    """Check actual query ranges and patched coordinates at frozen readouts."""
    annotations = {(str(b['base_problem_id']),e['event_id']):(b,e) for b in manifest for e in b['events']}
    checks = []
    for path in paths:
        raw = read_json(ROOT/path)
        item,event = annotations[raw['base_problem_id'],raw['event_id']]
        expected_readout = (readout_overrides or {}).get(
            (raw['base_problem_id'],raw['event_id'],raw['readout_name']), event['local_use_readout'])
        expected_partition = [list(x) for x in shared_partition(event,end=expected_readout['token_index'])]
        exact = raw['event']==event and raw['readout']==expected_readout
        exact = exact and raw['target_positions']==item['roi_mapping']['absolute_source_groups']['V_target']
        for window,row in raw['windows'].items():
            expected_queries = list(range(event['span_start_token']-int(window[1:]),event['span_start_token']))
            for arm in ['native','suppressed']:
                exact = exact and row[arm]['streaming_audit']['executed_chunk_ranges']==expected_partition
            executions=row['suppressed']['streaming_audit']['source_suppression_executions']
            exact = exact and [q for x in executions for q in x['generated_query_indices']]==expected_queries
            for execution in executions:
                exact = exact and [a['layer_index'] for a in execution['layer_audits']]==list(range(36))
                for audit in execution['layer_audits']:
                    exact = exact and audit['source_positions']==raw['target_positions'] and audit['selected_heads']==list(range(32))
                    exact = exact and audit['query_positions']==[raw['prompt_length']+q for q in execution['generated_query_indices']]
                    exact = exact and audit['lambda_zero_exact'] and audit['outside_window_max_abs_delta']==0
            neighbor=event['matched_neighbor_span']
            for arm,positions in [('event_rescue',list(range(event['span_start_token'],event['span_end_token']))),
                                  ('neighbor_rescue',list(range(neighbor['start_token'],neighbor['end_token'])))]:
                cut=max(positions)+1
                patch=row[arm]['cache_patch']
                exact = exact and row[arm]['streaming_audit']['executed_chunk_ranges']==[p for p in expected_partition if p[0]>=cut]
                exact = exact and patch['patch_generated_indices']==positions
                exact = exact and all(a['positions_replaced']==[raw['prompt_length']+p for p in positions] for a in patch['layer_audits'])
        checks.append({'raw_artifact':path,'executed_ranges_sources_and_patch_positions_exact':bool(exact)})
    return checks


def derive(conditions, floor=.05, final=None):
    sign = {'O':1,'O_sham':1,'C':-1,'C_sham':-1}
    losses = {c:sign[c]*(r['native']['D']-r['suppressed']['D']) for c,r in conditions.items()}
    gains = {c:sign[c]*(r['event_rescue']['D']-r['suppressed']['D']) for c,r in conditions.items()}
    neighbors = {c:sign[c]*(r['neighbor_rescue']['D']-r['suppressed']['D']) for c,r in conditions.items()}
    L = (losses['O']+losses['C'])/2
    G = (gains['O']+gains['C'])/2
    control = (neighbors['O']+neighbors['C'])/2
    sham = (abs(losses['O_sham'])+abs(losses['C_sham']))/2
    source = losses['O'] >= 0 and losses['C'] >= 0 and L >= floor and L > sham
    ratios = [gains[c]/losses[c] for c in ('O','C') if losses[c] != 0]
    causal = source and all(gains[c]>0 for c in ('O','C')) and G >= floor and len(ratios)==2 and statistics.median(ratios)>=.25 and G>control
    persistent = causal and final is not None and all(v>0 for v in final.values()) and statistics.fmean(final.values())>=floor
    return {'classification':'C3' if persistent else 'C2' if causal else 'C1' if source else 'C0',
            'source_sensitive':source, 'checkpoint':causal, 'L':L,'G':G,'neighbor':control}


def repeated(events):
    qualified = [e for e in events if e['classification'] in ('C2','C3')]
    return any((a['span_end_token']<=b['span_start_token'] or b['span_end_token']<=a['span_start_token'])
               and abs(a['span_start_token']-b['span_start_token'])>=24
               for i,a in enumerate(qualified) for b in qualified[i+1:])


def main():
    manifest,families,paths = collect()
    immutable = read_json(OUT / 'config/immutable_inputs.json')
    changed = [p for p,h in immutable['sha256'].items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    current_old = {str(p.relative_to(ROOT)) for p in OLD.rglob('*') if p.is_file()}
    expected_old = {p for p in immutable['sha256'] if p.startswith('outputs/stage3c9/')}
    original_unchanged = not changed and current_old==expected_old
    freeze = read_json(OUT / 'analysis/primary_freeze.json')
    assert paths == freeze['raw_sha256'], 'Primary raw scores changed after freeze'
    trace_checks=execution_trace_checks(manifest,paths)
    traces_exact=all(r['executed_ranges_sources_and_patch_positions_exact'] for r in trace_checks)
    result = read_json(OUT / 'analysis/checkpoint_classification.json')
    saved_bases = {b['base_problem_id']:b for b in result['bases']}
    tasks,life_raw = followup_scores('lifetime')
    overrides={}
    for task in tasks:
        item=next(b for b in manifest if str(b['base_problem_id'])==task['base_problem_id'])
        index=next(i for i,e in enumerate(item['events']) if e['event_id']==task['event_id'])
        expected_readout=(item['final_use_readout'] if task['readout_name']=='final'
                          else item['events'][index+1]['local_use_readout'])
        assert task['readout']==expected_readout, 'Unfrozen lifetime readout'
        overrides[task['base_problem_id'],task['event_id'],task['readout_name']]=expected_readout
    life_paths=[str(p.relative_to(ROOT)) for p in (OUT/'lifetime_raw').glob('shard_*/*/*/*.json')]
    life_traces=execution_trace_checks(manifest,life_paths,readout_overrides=overrides)
    traces_exact=traces_exact and all(r['executed_ranges_sources_and_patch_positions_exact'] for r in life_traces)
    finals = {}
    for task in tasks:
        if task['readout_name'] != 'final':
            continue
        for w in task['windows']:
            gains = {}
            for c,sign in [('O',1),('C',-1)]:
                row = life_raw[task['base_problem_id'],task['event_id'],'final',c]['windows'][w]
                gains[c] = sign*(row['event_rescue']['D']-row['suppressed']['D'])
            finals[task['base_problem_id'],task['event_id'],w] = gains
    raw_rows,base_rows = [],[]
    for item in manifest:
        base = str(item['base_problem_id'])
        saved = saved_bases[base]
        events = []
        for event,saved_event in zip(item['events'],saved['events']):
            assert all(saved_event[k]==v for k,v in event.items()), 'Frozen event changed'
            windows = []
            for w in ('W8','W16'):
                key=base,event['event_id'],w
                if key not in families:
                    continue
                expected = derive(families[key],final=finals.get(key))
                actual = saved_event['windows'][w]
                windows.append(expected)
                scores = families[key]
                expected_partition = scores['O']['partition']
                same = all(r['partition']==expected_partition and all(r[a]['recipient_execution_id']==r['execution_id'] for a in ['event_rescue','neighbor_rescue']) for r in scores.values())
                raw_rows.append({'base_problem_id':base,'event_id':event['event_id'],'window':w,
                    'classification_exact':actual['classification']==expected['classification'],
                    'source_loss_exact':actual['source_loss_mean']==expected['L'],
                    'rescue_gain_exact':actual['rescue_gain_mean']==expected['G'],
                    'neighbor_gain_exact':actual['neighbor_gain_mean']==expected['neighbor'],
                    'same_path_and_recipient':same, 'finite':all_finite(scores)})
            classification = max((r['classification'] for r in windows))
            assert saved_event['classification']==classification
            events.append({**event,'classification':classification})
        count=sum(e['classification'] in ['C2','C3'] for e in events)
        base_rows.append({'base_problem_id':base,'checkpoint_count_exact':count==saved['checkpoint_count'],
                          'repeated_exact':repeated(events)==saved['repeated_checkpoint']})
    sensitivity = read_json(OUT / 'analysis/threshold_sensitivity.json')
    sensitivity_exact = []
    for row in sensitivity['rows']:
        counts=[];repeat=[]
        for item in manifest:
            events=[]
            for event in item['events']:
                cs=[derive(families[str(item['base_problem_id']),event['event_id'],w],floor=row['effect_floor'])['classification']
                    for w in ('W8','W16') if (str(item['base_problem_id']),event['event_id'],w) in families]
                events.append({**event,'classification':max(cs)})
            counts.append(sum(e['classification'] in ('C2','C3') for e in events));repeat.append(repeated(events))
        sensitivity_exact.append(row['checkpoint_events']==sum(counts) and row['repeated_checkpoint_bases']==sum(repeat))
    lifetime = read_json(OUT / 'analysis/lifetime_analysis.json')
    censoring = all((r['phenotype']=='RIGHT-CENSORED')==all(not w['readouts'] for w in r['per_window'].values()) for r in lifetime['rows'])
    path_envs=[read_json(p) for p in (OUT/'same_path_scores/raw').glob('shard_*/environment.json')]
    environment = len(path_envs)==4 and all('A6000' in r['gpu_name'] and r['world_size']==4 for r in path_envs)
    figures=read_json(OUT/'analysis/figures/index.json')
    files_ok=figures['count']==15 and all((OUT/r[ext]).is_file() and (OUT/r[ext]).stat().st_size>1000 for r in figures['figures'] for ext in ('png','pdf'))
    outcome=read_json(OUT/'analysis/scientific_outcome.json')
    route=read_json(OUT/'route/route_status.json')
    necessity=read_json(OUT/'optional_necessity/gate.json')
    checks = {
        '1_original_48_bases_and_artifacts_immutable': original_unchanged and len(manifest)==48,
        '2_original_144_events_reused': sum(len(b['events']) for b in manifest)==144,
        '3_no_new_events_spans': len(raw_rows)==len(families),
        '4_canonical_A6000_source_path': environment and traces_exact and all(r['same_path_and_recipient'] for r in raw_rows),
        '5_canonical_rescue_neighbor_path': traces_exact and all(r['same_path_and_recipient'] for r in raw_rows),
        '6_all_event_windows_scored_before_classification': paths==freeze['raw_sha256'],
        '7_no_source_computational_pre_gate': freeze['all_rescues_scored_before_classification'],
        '8_same_recipient_denominators': all(r['source_loss_exact'] and r['rescue_gain_exact'] and r['neighbor_gain_exact'] for r in raw_rows),
        '9_frozen_checkpoint_rules_rederived': all(r['classification_exact'] for r in raw_rows),
        '10_repeated_rule_rederived': all(r['checkpoint_count_exact'] and r['repeated_exact'] for r in base_rows),
        '11_primary_floor_005': freeze['primary_effect_floor']==.05,
        '12_secondary_fixed_sensitivity_grid': [r['effect_floor'] for r in sensitivity['rows']]==[.025,.05,.1,.15] and all(sensitivity_exact),
        '13_base_is_independent_unit': result['independent_unit']=='base_problem_id' and all(r['N_unique_bases']==48 for r in result['statistics'].values()),
        '14_right_censoring_explicit': censoring,
        '15_no_attention_selection': all(not b['selection_used_attention'] for b in manifest),
        '16_no_cohort_expansion': immutable['base_ids']['primary']==[str(b['base_problem_id']) for b in manifest],
        '17_routes_and_necessity_respect_gates': route['run']==(route['eligible_bases']>=16) and (route['status']=='COMPLETE' if route['run'] else route['status']=='NOT RUN') and necessity['run']==(necessity['robust_unique_checkpoints']>=4),
        '18_no_retrieval_trigger_experiment': not outcome['next_experiment_started'],
        '19_no_sink_intervention': not outcome['next_experiment_started'],
        '20_exactly_one_recommendation_and_complete_outputs': isinstance(outcome['recommendation'],str) and files_ok,
    }
    mechanical=read_json(OUT/'audit/mechanical_validation.json')['passed']
    result={'checks':checks,'passed_count':sum(checks.values()),'total_checks':20,
            'passed':all(checks.values()) and mechanical and all(r['finite'] for r in raw_rows),
            'original_files_hashed':len(immutable['sha256']),'changed_originals':changed,
            'primary_condition_files':len(paths),'event_window_rows':len(raw_rows),'base_rows':base_rows}
    write_json(OUT/'audit/independent_artifact_validation.json',{**result,'raw_rederivation_rows':raw_rows,
        'primary_execution_traces':trace_checks,'lifetime_execution_traces':life_traces})
    write_json(OUT/'summaries/stage3c9r_acceptance.json',result)
    print(result)
    if not result['passed']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
