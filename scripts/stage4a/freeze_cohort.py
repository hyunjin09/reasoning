"""Freeze the completed, effect-blind screening prefix and stop native acquisition."""
from collections import Counter
from datetime import datetime, timezone
from scripts.stage4a.prepare_config import ROOT, OUT, read_json, read_jsonl, write_json, write_jsonl, sha


def main():
    flag = OUT / 'cohort/cohort_freeze_complete.json'
    if flag.exists():
        raise FileExistsError('Cohort freeze is create-once')
    screen = read_jsonl(OUT / 'cohort/prospective_screen_manifest.jsonl')
    annotations = read_jsonl(OUT / 'cohort/manual_annotations.jsonl')
    by_base = {a['base_problem_id']: a for a in annotations}
    decisions = read_json(OUT / 'cohort/review/prefix_exclusion_decisions.json')
    reused = read_jsonl(OUT / 'cohort/reused_native_outcomes.jsonl')
    new = [read_json(p) for p in (OUT / 'prospective_generation/raw').glob('shard_*/examples/*/result.json')]
    outcomes = {r['example_id']: r for r in reused + new}
    selected, excluded, ledger = [], [], []
    for row in screen[:800]:
        base = row['base_problem_id']
        outcome = outcomes.get(row['example_id'])
        assert outcome and outcome['complete'] and not outcome['truncated'], ('unresolved native', base)
        ann = by_base.get(base)
        common = {k: row[k] for k in ('base_problem_id', 'example_id', 'screen_order', 'source_image_sha256')}
        if ann and not ann.get('candidate_excluded'):
            assert ann['semantic_reviewed'] and ann['edits_reviewed'] and ann['token_map_validated']
            assert not ann['attention_used'] and not ann['causal_scores_available']
            meta = read_json(ROOT / ann['asset_metadata'])
            assert meta['manual_asset_review'] == meta['manual_roi_review'] == 'pass'
            assert meta['layout_exact'] and meta['native_generation_query_exact'] and meta['pixel_validation']['passed']
            visual = set(meta['prompt_metadata']['visual_token_indices'])
            assert not (set(meta['source_groups']['A']) & set(meta['source_groups']['B']))
            for group in ('A', 'B'):
                assert meta['source_groups'][group] and set(meta['source_groups'][group]) <= visual
            positions = []
            for name in ('A1', 'B', 'A2'):
                event = meta['events'][name]
                p = event['candidate_start_token']
                positions.append(p)
                assert event['current_query_zero_based'] == p - 1 and p >= 8
                assert len(event['history_before_ed_token_ids']) == p
                assert event['original_candidate_exact_generated_tokens'] and event['prefix_ends_at_token_boundary']
                assert event['original_divergent_suffix_ids'] != event['counterfactual_divergent_suffix_ids']
            assert min(positions[1] - positions[0], positions[2] - positions[1]) >= 12
            assert sha(row['source_image']) == row['source_image_sha256']
            for condition, path in meta['paths'].items():
                assert sha(ROOT / path) == meta['asset_sha256'][condition]
            item = {**ann, **common, 'retained': True,
                    'split': 'validation' if len(selected) < 8 else 'primary',
                    'native_status': outcome['status'], 'final_correct': outcome['status'] == 'correct',
                    'native_generation_kind': 'reused_matching_A6000_native' if row['native_reuse'] else 'new_stage4a',
                    'asset_metadata_sha256': sha(ROOT / ann['asset_metadata']),
                    'irrelevant_controls_validated': bool(meta.get('irrelevant_controls_validated'))}
            selected.append(item)
            ledger.append({**common, 'decision': 'retained', 'split': item['split'], 'evidence': ann['asset_metadata']})
        else:
            if ann:
                reason = {'category': 'independent_edit_not_established',
                          'reason': ann.get('exclusion_reason', ann.get('candidate_exclusion_reason')),
                          'evidence': ann.get('exclusion_evidence', 'outputs/stage4a/cohort/manual_annotations.jsonl')}
                assert reason['reason'], base
            elif base in decisions:
                reason = decisions[base]
            elif 430 <= int(base) <= 638:
                reason = {'category': 'independent_edit_not_established',
                          'reason': 'Shared plotted curves/grids: two independent local numeric-label edits were not established without conflicting unchanged curve/axis evidence.',
                          'evidence': f"outputs/stage4a/cohort/review/native_{row['screen_order']//20*20:04d}.jpg"}
            else:
                raise RuntimeError(f'Unresolved earlier candidate: {base}')
            record = {**common, **reason, 'attention_used': False, 'causal_scores_available': False,
                      'decision': 'excluded_from_reviewed_assay'}
            excluded.append(record)
            ledger.append(record)
        if len(selected) == 56:
            break
    assert len(selected) == 56 and len({r['base_problem_id'] for r in selected}) == 56
    validation, primary = selected[:8], selected[8:]
    prior = set(read_json(OUT / 'config/cohort_rules.json')['prior_excluded_bases'])
    assert not prior & {r['base_problem_id'] for r in selected}
    identities = read_json(OUT / 'config/identity_exclusions.json')
    for group in identities['exact_duplicate_groups'] + identities['manually_verified_duplicate_groups']:
        assert len(set(group) & {r['base_problem_id'] for r in selected}) <= 1
    retained = {r['base_problem_id']: r['split'] for r in selected}
    for ann in annotations:
        ann['retained'] = ann['base_problem_id'] in retained
        if ann['retained']:
            ann['split'] = retained[ann['base_problem_id']]
    write_jsonl(OUT / 'cohort/manual_annotations.jsonl', annotations)
    products = {
        'cohort/validation_manifest.jsonl': validation,
        'cohort/primary_manifest.jsonl': primary,
        'cohort/exclusions.jsonl': excluded,
        'cohort/prefix_review_ledger.jsonl': ledger,
        'phase_d_counterfactual_refresh/subset_manifest.jsonl': primary[:24],
        'cohort/irrelevant_subset_manifest.jsonl': [r for r in primary if r['irrelevant_controls_validated']],
    }
    for path, rows in products.items():
        write_jsonl(OUT / path, rows)
    roi, events, readouts, roles, images, shams = [], [], [], [], [], []
    for item in selected:
        meta = read_json(ROOT / item['asset_metadata'])
        key = {k: item[k] for k in ('base_problem_id', 'example_id', 'split')}
        roi.append({**key, 'facts': meta['facts'], 'source_groups': meta['source_groups'], 'roi_mapping': meta['roi_mapping']})
        for name, event in meta['events'].items():
            events.append({**key, 'event': name, **{k: v for k, v in event.items() if not k.startswith('history_before_ed')}})
            readouts.append({**key, 'event': name, **event})
            roles.append({**key, 'event': name, 'demanded_fact': event['fact'], 'judgment': event['semantic_judgment'], 'attention_used': False})
        images.append({**key, 'paths': meta['paths'], 'sha256': meta['asset_sha256'], 'asset_metadata': item['asset_metadata']})
        shams.append({**key, 'paths': {x: meta['paths'][x] for x in ('A_sham', 'B_sham')}})
    for path, rows in [('annotations/roi_a_b.jsonl', roi), ('annotations/event_a1_b_a2.jsonl', events),
                       ('annotations/local_readouts.jsonl', readouts), ('annotations/semantic_roles.jsonl', roles),
                       ('counterfactuals/image_manifest.jsonl', images), ('counterfactuals/sham_manifest.jsonl', shams)]:
        write_jsonl(OUT / path, rows)
    cutoff = selected[-1]['screen_order']
    prefix = screen[:cutoff+1]
    account = {'snapshot_at': datetime.now(timezone.utc).isoformat(), 'initial_budget': 800, 'maximum_budget': 1200,
               'fully_reviewed_prefix_trajectories': len(prefix), 'prefix_last_screen_order': cutoff,
               'prefix_completed': len(prefix), 'prefix_correct': sum(outcomes[r['example_id']]['status']=='correct' for r in prefix),
               'prefix_static_multi_numeric_candidates': sum(r['numeric_candidate_count']>=2 for r in prefix),
               'prefix_semantic_ABA_annotated': sum(r['base_problem_id'] in by_base for r in prefix),
               'prefix_two_ROI_and_edit_valid': 56, 'retained_validation': 8, 'retained_primary': 48,
               'phase_d_frozen_bases': 24, 'irrelevant_primary_bases': sum(r['irrelevant_controls_validated'] for r in primary),
               'all_provisional_annotations': len(annotations), 'all_asset_review_passes': sum(a['edits_reviewed'] and not a.get('candidate_excluded') for a in annotations),
               'available_reused_native_outcomes': len(reused), 'new_completed_at_freeze': len(new),
               'new_attempted_at_freeze': len(list((OUT/'prospective_generation/raw').glob('shard_*/examples/*/input.json'))),
               'prefix_exclusions_by_category': dict(Counter(r['category'] for r in excluded)),
               'selection_used_attention': False, 'selection_used_causal_scores': False, 'final_correctness_filter': False,
               'review_scope': 'Bounded manual fact/event and construction review; exclusions state what was not established, not exhaustive impossibility of every alternative pair.',
               'asynchronous_generation': 'Work outside the prefix and in-flight completions is preserved and counted; it cannot change the frozen membership.'}
    write_json(OUT / 'cohort/screening_accounting.json', account)
    write_json(OUT / 'counterfactuals/edit_validation.json', {'passed': True, 'bases': 56, 'conditions_each': 6, 'reviewed_before_causal_scoring': True})
    frozen_paths = list((OUT/'config').glob('*.json')) + [OUT/path for path in products]
    frozen_paths += list((OUT/'annotations').glob('*.jsonl')) + list((OUT/'counterfactuals').glob('*'))
    frozen_paths += [OUT/'cohort/manual_annotations.jsonl', OUT/'cohort/prospective_screen_manifest.jsonl']
    freeze = {'frozen_at': datetime.now(timezone.utc).isoformat(), 'validation_bases': [r['base_problem_id'] for r in validation],
              'primary_bases': [r['base_problem_id'] for r in primary], 'prefix_last_screen_order': cutoff,
              'phase_d_bases': [r['base_problem_id'] for r in primary[:24]], 'causal_scoring_started': False,
              'sha256': {str(p.relative_to(ROOT)): sha(p) for p in frozen_paths},
              'asset_metadata_sha256': {r['asset_metadata']: r['asset_metadata_sha256'] for r in selected}}
    write_json(flag, freeze)  # Native workers check this only between completed trajectories.
    print({'validation': freeze['validation_bases'], 'primary': freeze['primary_bases'], 'cutoff': cutoff})


if __name__ == '__main__':
    main()
