#!/usr/bin/env python3
"""Derive the 15 mechanical gates from frozen coordinates and raw tensor audits."""

import math

from visual_reasoning.stage3c9.assay import CONDITIONS, exact_readout_sequences, source_window_indices
from visual_reasoning.stage3c9r.protocol import shared_partition
from scripts.stage3c9r.freeze_inputs import ROOT, OUT, read_json, read_jsonl, write_json


def all_finite(value):
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(all_finite(v) for v in value.values())
    if isinstance(value, list):
        return all(all_finite(v) for v in value)
    return True


def main():
    config = read_json(OUT / 'config/stage3c9r_config.json')
    manifest = read_jsonl(OUT / 'cohort/validation_manifest.jsonl')
    expected = {(str(b['base_problem_id']), e['event_id'], c): (b, e)
                for b in manifest for e in b['events'] for c in CONDITIONS}
    files = list((OUT / 'audit/raw').glob('shard_*/*/*/*_local.json'))
    raw = {}
    for p in files:
        r = read_json(p)
        key = (r['base_problem_id'], r['event_id'], r['condition'])
        if key in raw:
            raise RuntimeError(f'Duplicate raw validation cell {key}')
        raw[key] = r
    if set(raw) != set(expected):
        raise RuntimeError(f'Incomplete validation: {len(raw)}/{len(expected)} cells')
    path_rows, window_rows, event_rows, neighbor_rows, invariance_rows = [], [], [], [], []
    self_rows, replay_rows, readout_rows = [], [], []
    for key, r in raw.items():
        item, event = expected[key]
        tokens = read_jsonl(ROOT / item['tokens_path'])
        local = exact_readout_sequences(tokens, event['local_use_readout'])
        final = exact_readout_sequences(tokens, item['final_use_readout'])
        partition = [list(x) for x in shared_partition(event, end=local['readout_generated_index'])]
        span = list(range(event['span_start_token'], event['span_end_token']))
        control = event['matched_neighbor_span']
        neighbor = list(range(control['start_token'], control['end_token']))
        target = item['roi_mapping']['absolute_source_groups']['V_target']
        assert r['event'] == event and r['target_positions'] == target
        assert set(r['windows']) == {w for w in ('W8', 'W16') if event['span_start_token'] >= int(w[1:])}
        for window, row in r['windows'].items():
            identity = dict(base_problem_id=key[0], event_id=key[1], condition=key[2], window=window)
            actual = row['native']['streaming_audit']['executed_chunk_ranges']
            path_rows.append({**identity, 'same_partition': row['partition'] == partition == actual == row['suppressed']['streaming_audit']['executed_chunk_ranges'],
                              'fixed_2048_maximum': all(0 < b-a <= 2048 for a,b in actual)})
            expected_indices = source_window_indices(span_start_token=event['span_start_token'], width=int(window[1:]))
            executions = row['suppressed']['streaming_audit']['source_suppression_executions']
            combined = [q for execution in executions for q in execution['generated_query_indices']]
            for execution in executions:
                audits = execution['layer_audits']
                absolute = [r['prompt_length'] + q for q in execution['generated_query_indices']]
                window_rows.append({**identity,
                    'indices_exact': combined == expected_indices == row['source_window_generated_indices'],
                    'layers_exact': [x['layer_index'] for x in audits] == list(range(36)),
                    'heads_roi_queries_exact': all(x['selected_heads'] == list(range(32)) and x['source_positions'] == target and x['query_positions'] == absolute for x in audits),
                    'outside_queries_exact': all(x['outside_window_max_abs_delta'] == 0 and x['nonselected_head_max_abs_delta'] == 0 for x in audits),
                    'native_qkv_attention': all(all(x[k] == 0 for k in ['query_max_abs_delta', 'key_max_abs_delta', 'value_max_abs_delta', 'attention_max_abs_delta']) for x in audits),
                    'zero_contribution_exact': all(x['lambda_zero_exact'] and x['all_outputs_finite'] for x in audits)})
            for arm, positions, destination in [('event_rescue', span, event_rows), ('neighbor_rescue', neighbor, neighbor_rows)]:
                patch = row[arm]['cache_patch']
                audits = patch['layer_audits']
                cut = max(positions) + 1
                path_rows.append({**identity, 'arm': arm,
                    'same_partition': row[arm]['partition'] == partition and row[arm]['streaming_audit']['executed_chunk_ranges'] == [x for x in partition if x[0] >= cut],
                    'same_recipient': row[arm]['recipient_execution_id'] == row['execution_id'] == row['suppressed']['execution_id'],
                    'fixed_2048_maximum': True})
                destination.append({**identity,
                    'positions_exact': patch['patch_generated_indices'] == positions and all(x['positions_replaced'] == [r['prompt_length'] + p for p in positions] for x in audits),
                    'layers_exact': [x['layer_index'] for x in audits] == list(range(36)),
                    'gqa_exact': all(x['native_kv_head_count'] == 8 and x['head_dimension'] == 128 and x['post_rope_key'] and x['projected_value'] for x in audits),
                    'bridge_exact': patch['first_downstream_absolute_query'] == r['prompt_length'] + cut < r['prompt_length'] + local['readout_generated_index'],
                    'matched_width_disjoint': len(span) == len(neighbor) and not set(span) & set(neighbor)})
                invariant = patch['measured_invariance']
                invariance_rows.append({**identity, 'arm': arm,
                    **{k: invariant[k] for k in ['all_nonselected_exact', 'visual_exact', 'selected_exact', 'logits_unchanged_at_patch']},
                    'gqa_shapes_measured': len(invariant['layers']) == 36 and all(x['shape'][0:2] == [1,8] and x['shape'][-1] == 128 for x in invariant['layers'])})
            controls = row['self_controls']
            self_rows.append({**identity, 'native_exact': controls['native_to_native_exact'], 'suppressed_exact': controls['suppressed_to_suppressed_exact']})
            replay_rows.append({**identity, 'rescue_exact': controls['rescue_replay_exact'], 'suppressed_exact': controls['suppressed_replay_exact'],
                                'inherited_path': row['inherited_path_comparison']})
            readout_rows.append({**identity, 'local_index_and_hash_exact': row['readout_generated_index'] == local['readout_generated_index'] and row['prefix_sha256'] == local['prefix_sha256'],
                                 'final_index_and_hash_exact': r['final_readout_index'] == final['readout_generated_index'] and r['final_prefix_hash_exact']})
    def passed(rows):
        identifiers = {'base_problem_id','event_id','condition','window','arm'}
        return bool(rows) and all(all(v for k,v in row.items() if k not in identifiers) for row in rows)
    envs = [read_json(p) for p in (OUT / 'audit/raw').glob('shard_*/environment.json')]
    canonical = len(envs) == 4 and all('A6000' in e['gpu_name'] and e['world_size'] == 4 and e['slurm_job_id'] == config['runtime']['slurm_allocation'] for e in envs)
    inherited = [r['inherited_path'] for r in replay_rows if r['inherited_path'] is not None]
    canonical = canonical and len(inherited) == 16 and all(all(r.values()) for r in inherited)
    checks = {
        '1_canonical_A6000_calibration_v2_path': canonical,
        '2_fixed_2048_chunking': all(r['fixed_2048_maximum'] for r in path_rows),
        '3_all_arms_and_shams_same_path_recipient': passed(path_rows),
        '4_exact_W8_W16_indices': all(r['indices_exact'] for r in window_rows),
        '5_isolated_target_ROI_suppression': passed(window_rows),
        '6_exact_event_KV_positions': passed(event_rows),
        '7_exact_neighbor_KV_positions': passed(neighbor_rows),
        '8_exact_native_GQA': all(r['gqa_exact'] for r in event_rows + neighbor_rows) and all(r['gqa_shapes_measured'] for r in invariance_rows),
        '9_visual_KV_invariant': all(r['visual_exact'] for r in invariance_rows),
        '10_nontarget_caches_invariant': passed(invariance_rows),
        '11_native_self_exact': all(r['native_exact'] for r in self_rows),
        '12_suppressed_self_exact': all(r['suppressed_exact'] for r in self_rows),
        '13_deterministic_replay': all(r['rescue_exact'] and r['suppressed_exact'] for r in replay_rows),
        '14_exact_local_final_readouts': passed(readout_rows),
        '15_finite_outputs': all(all_finite(r) for r in raw.values()),
    }
    for name, rows in [('canonical_path_audit',path_rows), ('source_window_audit',window_rows),
                       ('event_patch_selectivity',event_rows), ('neighbor_patch_selectivity',neighbor_rows),
                       ('cache_invariance',invariance_rows), ('self_patch_validation',self_rows),
                       ('deterministic_replay',replay_rows), ('readout_index_audit',readout_rows)]:
        write_json(OUT / f'audit/{name}.json', {'rows':rows})
    result = {'checks': checks, 'passed': all(checks.values()), 'passed_count': sum(checks.values()),
              'total_checks':len(checks), 'validation_bases':8, 'validation_events':24,
              'condition_files':len(raw), 'event_window_condition_families':len(self_rows),
              'inherited_comparisons':len(inherited)}
    write_json(OUT / 'audit/mechanical_validation.json', result)
    print(result)
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
