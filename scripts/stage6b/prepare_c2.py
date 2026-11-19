"""Freeze C2 source/readout identities from reviewed semantics, without scores."""
import re
from collections import defaultdict, Counter
from transformers import AutoTokenizer

from scripts.stage6b.common import ROOT, OUT, SOURCE, read_json, read_jsonl, sha, write_json, write_jsonl, verify_stage6a
from visual_reasoning.stage6b.protocol import candidate_event, c2_roles


def main():
    verify_stage6a()
    old_config = read_json(SOURCE/'config/stage6a_config.json')
    config = {'stage': '6B', 'model_checkpoint': old_config['model_checkpoint'],
        'slurm_allocation': '110860', 'node': 'node03', 'tmux_session': '9',
        'world_size': 2, 'dtype': 'bfloat16', 'seed': 1234,
        'max_generated_chunk': 2048, 'release_allocator_cache': True,
        'language_attention': 'eager', 'vision_attention': 'sdpa',
        'primary_window': 2, 'sensitivity_window': 8,
        'suppression_layers': list(range(36)), 'suppression_heads': list(range(32)),
        'passive_layers': [28, 29], 'passive_heads': list(range(32)),
        'new_allocations_permitted': False,
        'stage6a_release_sha256': sha(SOURCE/'cohort/primary_release_events.jsonl')}
    write_json(OUT/'config/stage6b_config.json', config, freeze=True)
    tokenizer = AutoTokenizer.from_pretrained(config['model_checkpoint'], local_files_only=True)
    cohort = [r for r in read_jsonl(SOURCE/'cohort/primary_release_events.jsonl') if r['cohort']=='C2']
    index = {r['event_id']: r for r in read_jsonl(SOURCE/'traces/controlled_native_index.jsonl') if r['cohort']=='C2'}
    claims = defaultdict(list)
    for row in read_jsonl(SOURCE/'traces/controlled_local_correctness.jsonl'):
        if row['cohort']=='C2':
            claims[row['event_id']].extend(row['source_claims'])
    maps = defaultdict(dict)
    for row in read_jsonl(SOURCE/'regions/controlled_roi_maps.jsonl'):
        if row['cohort']=='C2':
            maps[row['event_id']][row['source_id']] = row
    finals = {r['event_id']: r for r in read_jsonl(SOURCE/'traces/controlled_final_correctness.jsonl')}
    events, roles, failures = [], [], []
    for row in cohort:
        eid = row['event_id']; role = c2_roles(row); native = index[eid]
        choices = sorted((c for c in claims[eid] if c['source_id']==role['demanded'] and c.get('readout')),
                         key=lambda c: (c['char_start'], c['char_end']))
        tokens = read_jsonl(native['tokens_artifact'])
        raw = ''.join(t['decoded_token'] for t in tokens)
        correct_index = 0 if role['demanded']=='T' else 1
        errors = []
        event = None
        for claim in choices:
            quote = raw[claim['char_start']:claim['char_end']]
            if quote != claim['quote']:
                raise RuntimeError('Reviewed quote does not match native text: '+eid)
            pattern = r'\s*'.join(re.escape(c) for c in str(claim['readout']) if not c.isspace())
            match = re.search(pattern, quote, re.IGNORECASE)
            if not match:
                errors.append('No literal whitespace-tolerant readout match'); continue
            start = claim['char_start'] + match.start(); end = claim['char_start'] + match.end()
            try:
                event = candidate_event(tokens, start, end, str(row['answers'][correct_index]),
                                        str(row['answers'][1-correct_index]), tokenizer)
            except ValueError as error:
                errors.append(str(error)); continue
            event.update({'readout_char_start': start, 'readout_char_end': end,
                          'reviewed_claim': claim, 'skipped_earlier_mechanical_readouts': errors})
            break
        if event is None:
            failures.append({'event_id': eid, 'base_id': row['base_id'], 'reasons': errors});continue
        source_groups = {source: maps[eid][source]['absolute_token_indices'] for source in ('T', 'X')}
        if not all(source_groups.values()):
            raise RuntimeError('Missing source token footprint: '+eid)
        input_meta = read_json(native['input_metadata_artifact'])
        assert input_meta['prompt']==row['prompt']
        assert all(set(v)<=set(input_meta['visual_token_indices']) for v in source_groups.values())
        entry = {'id': eid, 'event_id': eid, 'base_id': row['base_id'],
            'cohort': 'C2', 'dataset': row['dataset'], 'split': row['split'], 'group_id': row['group_id'],
            'condition': row['condition'], 'phase': 'a', 'row': row,
            'event': event, 'source_groups': source_groups, 'roles': role,
            'native_input_path': native['input_metadata_artifact'],
            'native_generation_path': native['generation_artifact'],
            'source_geometry': {'T': row['target']['roi'], 'X': row['other_sources'][0]['roi']},
            'final_correctness': finals[eid],
            'source_map_overlap': sorted(set(source_groups['T']) & set(source_groups['X'])),
            'w2_sources': ['T', 'X'], 'w8_sources': ['T', 'X'],
            'irrelevant_control': 'unavailable: no independently validated irrelevant C2 ROI',
            'selection_rule': 'first mechanically valid independently reviewed demanded-source literal readout; frozen family order; no scores or attention'}
        events.append(entry)
        roles.append({k:entry[k] for k in ('event_id','base_id','split','condition','roles','source_geometry','source_groups','source_map_overlap','irrelevant_control')})
    # No outcome-based replacement or silently incomplete factorial families.
    if failures:
        write_json(OUT/'audit/c2_readout_preparation_failures.json', failures)
        raise RuntimeError('C2 mechanically underidentified events; inspect before family freeze')
    assert len(events)==124 and len({r['base_id'] for r in events})==31
    write_jsonl(OUT/'c2_alignment_retrieval/source_roles.jsonl', roles, freeze=True)
    write_jsonl(OUT/'config/phase_a_events.jsonl', events, freeze=True)
    rules = {'focal_source': 'Stage6A T, fixed within family',
        'task_demanded_source': 'T in AR/R_only, X in A_only/Neither',
        'primary_retrieval_factor_estimand': 'effect of demand for fixed focal source on focal-source VSD',
        'additional_planned_estimand': 'current demanded-source VSD across all cells; all cells need an image source, so not an image-needed/image-unneeded test',
        'readout': 'correct requested field versus the other independently reviewed field; same semantic pair with direction reversed between focal-demand conditions',
        'w2': ['T','X'], 'w8': ['T','X'],
        'w8_justification': 'Includes demanded-source sensitivity and fixed-focal sensitivity needed to interpret the factorial contrast',
        'alignment_feature_source': 'fixed focal ROI T in every cell',
        'high_attention_threshold': 'discovery pooled focal attention-density 75th percentile; freeze numerical threshold before confirmation',
        'matching': {'within_family': True, 'attention_log_ratio_max': 0.35,
                     'normalized_progress_difference_max': 0.20, 'candidate_token_length_ratio_max': 2.0,
                     'minimum_confirmation_pairs': 8,
                     'tie_break': 'smallest absolute log attention-density difference, then frozen cell order AR/R_only'},
        'exclusions': [], 'source_roles_frozen_before_scoring': True,
        'effect_or_correctness_selection': False}
    write_json(OUT/'config/c2_factorial_rules.json', rules, freeze=True)
    write_json(OUT/'audit/c2_source_readout_freeze.json', {'status':'PASS', 'families':31,'events':124,
        'events_by_split':dict(Counter(r['split'] for r in events)),
        'manifest_sha256':sha(OUT/'config/phase_a_events.jsonl'),
        'roles_sha256':sha(OUT/'c2_alignment_retrieval/source_roles.jsonl'),
        'rules_sha256':sha(OUT/'config/c2_factorial_rules.json'),
        'attention_or_causal_scores_used':False}, freeze=True)
    print('C2 source/readout freeze PASS: 31 families, 124 events; 48 discovery / 76 confirmation')


if __name__ == '__main__':
    main()
