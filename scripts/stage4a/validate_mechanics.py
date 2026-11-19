"""Audit all8 validation bases before opening primary scoring."""
import argparse
import math
import numpy as np
from scripts.stage4a.prepare_config import ROOT, OUT, read_json, read_jsonl, write_json, sha
from scripts.stage4a.run_scores import verify_freeze
from visual_reasoning.stage4a.runtime import event_coordinates, intervention_sources


def telemetry_valid(telemetry):
    if set(telemetry) != {'28', '29'}:
        return False
    for layer, roles in telemetry.items():
        for role, summary in roles.items():
            if not summary['all_values_finite']:
                return False
            groups = summary['groups']
            heads = summary['per_head']
            if len(heads) != (32 if role == 'all' else 4):
                return False
            for name, aggregate in groups.items():
                for metric in ('qk_cosine', 'raw_qk_dot', 'scaled_logit', 'attention_mass',
                               'attention_density', 'alpha_v_norm', 'post_wo_norm'):
                    key = 'mean_'+metric
                    per_key = key if metric in ('qk_cosine', 'raw_qk_dot', 'scaled_logit') else metric
                    actual = sum(h['groups'][name][per_key] for h in heads)/len(heads)
                    if not math.isclose(actual, aggregate[key], rel_tol=1e-10, abs_tol=1e-10):
                        return False
                for head in heads:
                    g = head['groups'][name]
                    if not math.isclose(float(np.linalg.norm(g['alpha_v_vector'])), g['alpha_v_norm'], rel_tol=2e-6, abs_tol=2e-6):
                        return False
                    if not math.isclose(g['attention_density']*g['token_count'], g['attention_mass'], rel_tol=2e-6, abs_tol=2e-6):
                        return False
            if summary['RDS_T_vs_M'] != groups['T']['mean_scaled_logit']-groups['M']['mean_scaled_logit']:
                return False
            if summary['ADG_T_vs_M'] != groups['T']['mean_attention_density']-groups['M']['mean_attention_density']:
                return False
        all_heads = {h['logical_query_head']: h for h in roles['all']['per_head']}
        if any(h != all_heads[h['logical_query_head']] for h in roles['selected']['per_head']):
            return False
    return True


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    verify_freeze()
    items = {i['base_problem_id']: i for i in read_jsonl(OUT/'cohort/validation_manifest.jsonl')}
    paths = sorted((OUT/'raw'/args.run_id).glob('shard_*/*/*/*.json'))
    rows = [read_json(p) for p in paths]
    expected = {(b, c, e) for b in items for c in ('OO','AO','OB','AB','A_sham','B_sham') for e in ('A1','B','A2')}
    observed = {(r['base_problem_id'], r['condition'], r['event']) for r in rows}
    if observed != expected or len(rows) != 144:
        raise RuntimeError(f'Incomplete validation: {len(observed)}/144 event files')
    names = ['roi_maps_exact', 'roi_nonoverlap', 'event_indices_exact', 'readout_indices_exact',
             'semantic_layouts_matched', 'roi_A_isolated', 'roi_B_isolated', 'joint_union_exact',
             'self_noop_exact', 'deterministic_replay', 'counterfactual_scoring_finite',
             'sham_pipeline_valid', 'recent_R_isolated', 'passive_reconstruction', 'selection_blind']
    checks = dict.fromkeys(names, True)
    details = []
    envs = [read_json(p) for p in (OUT/'raw'/args.run_id).glob('shard_*/environment.json')]
    canonical = len(envs)==4 and all('A6000' in e['gpu_name'] and e['slurm_job_id']=='108548' for e in envs)
    for item in items.values():
        m = read_json(ROOT/item['asset_metadata'])
        visual = m['prompt_metadata']['visual_token_indices']
        for fact in ('A','B'):
            checks['roi_maps_exact'] &= m['source_groups'][fact] == [visual[i] for i in m['roi_mapping'][fact]['local_positions']]
        checks['roi_nonoverlap'] &= not set(m['source_groups']['A']) & set(m['source_groups']['B'])
        checks['sham_pipeline_valid'] &= m['pixel_validation']['passed'] and m['layout_exact'] and m['edits_reviewed']
        checks['selection_blind'] &= not item['attention_used'] and not item['causal_scores_available']
    for row in rows:
        item = items[row['base_problem_id']]; m = read_json(ROOT/item['asset_metadata'])
        event = m['events'][row['event']]; prompt = m['prompt_metadata']['prompt_token_count']
        coords = event_coordinates(event, prompt)
        checks['semantic_layouts_matched'] &= row['image_layout_exact']
        checks['event_indices_exact'] &= row['event_history_sha256'] == event['history_before_ed_sha256']
        if row['condition']=='OO':
            checks['self_noop_exact'] &= all(row['validation_checks'][k] for k in ('noop_AB_exact','noop_trigger_exact','unhooked_exact'))
            checks['deterministic_replay'] &= row['validation_checks']['replay_exact']
            checks['passive_reconstruction'] &= telemetry_valid(row['arms']['N']['telemetry'])
        for name, arm in row['arms'].items():
            checks['counterfactual_scoring_finite'] &= arm['finite'] and all(s['finite'] for s in arm['step_audits'])
            checks['readout_indices_exact'] &= (arm['original_candidate']['candidate_token_ids']==event['original_divergent_suffix_ids']
                and arm['counterfactual_candidate']['candidate_token_ids']==event['counterfactual_divergent_suffix_ids'])
            checks['event_indices_exact'] &= arm['absolute_current_query']==prompt+coords['current'] and arm['partition']==[list(x) for x in coords['partition']]
            canonical &= arm['clone_no_alias'] and arm['past_cache_audit']['passed']
            canonical &= max(m['prompt_metadata']['visual_token_indices']) < arm['past_cache_audit']['past_length']
            if name=='unhooked':
                continue
            seen = []
            for a in arm['source_audits']:
                kind = a['source_kind']; layer = a['layer_index']; query = a['query_positions'][0]
                seen.append((kind, layer, query))
                exact = all(a[k] for k in ('query_exact','key_exact','value_exact','attention_exact','explicit_source_reference_exact','all_outputs_finite'))
                exact &= a['selected_heads']==list(range(32)) and a['partition_compute_dtype']=='float32'
                exact &= a['partition_max_abs_error']<=1e-5 and a['selected_head_expected_max_abs_error']==0
                exact &= a['outside_window_max_abs_delta']==0 and a['nonselected_head_max_abs_delta']==0
                if kind=='R16':
                    checks['recent_R_isolated'] &= exact and a['source_positions']==coords['R16'] and layer in range(16,24) and query==prompt+coords['current']
                else:
                    sources = intervention_sources(m['source_groups'], kind)[0][0]
                    valid = exact and a['source_positions']==sources
                    if kind=='A': checks['roi_A_isolated'] &= valid
                    elif kind=='B': checks['roi_B_isolated'] &= valid
                    elif kind=='AB': checks['joint_union_exact'] &= valid
                    else: canonical &= valid
            required = []
            if arm['roi']:
                required += [(arm['roi'], layer, prompt+i) for i in range(coords['end']-arm['window'],coords['end']) for layer in range(36)]
            if arm['trigger']:
                required += [('R16', layer, prompt+coords['current']) for layer in range(16,24)]
            canonical &= len(seen)==len(required) and sorted(seen)==sorted(required)
            details.append({'base_problem_id':row['base_problem_id'],'event':row['event'],'image':row['condition'],
                            'arm':name,'source_calls':len(seen),'past_cache_exact':arm['past_cache_audit']['passed']})
    checks = {k:bool(v) for k,v in checks.items()}
    result = {'passed':bool(canonical and all(checks.values())), 'canonical_path_passed':bool(canonical),
              'checks':checks, 'N_unique_bases':8, 'event_files':144, 'run_id':args.run_id,
              'raw_sha256':{str(p.relative_to(ROOT)):sha(p) for p in paths},'details':details}
    write_json(OUT/'audit/mechanical_validation.json', result)
    mapping = {'canonical_path_audit': 'canonical_path_passed', 'roi_nonoverlap':'roi_nonoverlap',
               'event_index_audit':'event_indices_exact','readout_index_audit':'readout_indices_exact',
               'source_suppression_selectivity':'roi_A_isolated','joint_suppression_audit':'joint_union_exact',
               'trigger_intervention_audit':'recent_R_isolated','deterministic_replay':'deterministic_replay',
               'self_patch_validation':'self_noop_exact'}
    for filename, key in mapping.items():
        write_json(OUT/f'audit/{filename}.json', {'passed':result[key] if key in result else checks[key],
                   'evidence':'outputs/stage4a/audit/mechanical_validation.json','N_unique_bases':8})
    print({k:v for k,v in result.items() if k not in ('details','raw_sha256')})
    if not result['passed']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
