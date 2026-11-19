"""Export targeted semantic review packets; no causal or outcome values enter."""
from collections import Counter, defaultdict

from scripts.stage6b.common import ROOT, SOURCE, read_json, sha, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.semantic_contract import blind_span


def main():
    index = {r['event_id']: r for r in rows(OUT / 'inputs/c1_index.jsonl')}
    targets = defaultdict(dict)
    allowed_types = {'demand_transition', 'refresh', 'matched_no_transition_candidate', 'wrong_claim'}
    for r in rows(SOURCE / 'traces/controlled_future_causal_anchors.jsonl'):
        if r['event_id'] in index and allowed_types.intersection(r['anchor_types']):
            targets[r['event_id']][r['span_id']] = sorted(allowed_types.intersection(r['anchor_types']))
    # Include immediate neighboring native spans, even unresolved ones. Skipping
    # intervening spans could create a false stable hold or false source switch.
    desired = {eid: {j for sid in spans for j in range(max(0, int(sid[1:]) - 1), int(sid[1:]) + 2)}
               for eid, spans in targets.items()}
    spans = defaultdict(list)
    for r in rows(SOURCE / 'traces/controlled_demand_annotations.jsonl'):
        eid = r['event_id']
        if eid in desired and int(r['span_id'][1:]) in desired[eid]:
            spans[eid].append(blind_span(r))
    definitions = defaultdict(dict)
    for r in rows(SOURCE / 'regions/ground_truth_rois.jsonl'):
        if r['cohort'] == 'C1':
            definitions[r['base_id']][r['source_id']] = {k: r.get(k) for k in (
                'source_id', 'entity', 'xyxy', 'truth_value', 'counterfactual_value', 'provenance')}
    maps = defaultdict(dict)
    for r in rows(SOURCE / 'regions/controlled_roi_maps.jsonl'):
        if r['event_id'] in targets:
            maps[r['event_id']][r['source_id']] = r['absolute_token_indices']
    packet_index = []
    universe = []
    for eid in sorted(targets, key=lambda e: (index[e]['split'] != 'discovery', index[e]['base_id'], index[e]['condition'])):
        r = index[eid]
        review_spans = sorted(spans[eid], key=lambda s: s['token_start'])
        present = {s['span_id'] for s in review_spans}
        assert set(targets[eid]) <= present, (eid, set(targets[eid]) - present)
        sources = []
        for sid, definition in sorted(definitions[r['base_id']].items()):
            source = dict(definition)
            source['condition_truth_value'] = (source['counterfactual_value'] if sid == 'T' and r['condition'] == 'counterfactual' else source['truth_value'])
            source['current_image_source_identity_mapped'] = bool(maps[eid].get(sid)) and r['condition'] not in {'no_image', 'unrelated'}
            sources.append(source)
        packet = {k: r[k] for k in ('event_id', 'base_id', 'dataset', 'condition', 'question', 'prompt', 'image_path')}
        packet.update(sources=sources, spans=review_spans,
                      instructions='Review local semantic demand using task/image/text/source definitions. Unknown is not empty demand. No acquisition inference from demand alone.',
                      annotation_status='NOT_YET_REVIEWED')
        path = OUT / 'review/packets' / (eid + '.json')
        write_json(path, packet, freeze=True)
        packet_index.append({'event_id': eid, 'base_id': r['base_id'], 'split': r['split'],
                             'packet_path': str(path.relative_to(ROOT)), 'sha256': sha(path),
                             'target_spans': len(targets[eid]), 'context_spans': len(review_spans)})
        for sid, kinds in targets[eid].items():
            universe.append({'event_id': eid, 'base_id': r['base_id'], 'split': r['split'], 'condition': r['condition'],
                             'span_id': sid, 'candidate_types': kinds, 'packet_path': str(path.relative_to(ROOT)), 'review_status': 'PENDING'})
    write_jsonl(OUT / 'review/packet_index.jsonl', packet_index, freeze=True)
    # Selection flags are kept in a separate accounting file, never shown in
    # demand packets, so the wrong-claim stratum does not disclose outcome labels.
    write_jsonl(OUT / 'review/candidate_universe.jsonl', universe, freeze=True)
    result = {'status': 'BLINDED_PACKETS_PREPARED_NOT_ANNOTATED', 'packets': len(packet_index),
              'target_spans': len(universe), 'context_spans': sum(p['context_spans'] for p in packet_index),
              'counts': Counter(t for r in universe for t in r['candidate_types']),
              'packet_fields': list(packet), 'span_fields': list(blind_span(review_spans[0])),
              'causal_or_attention_inputs': [], 'correctness_fields_in_packets': [], 'primary_panel_frozen': False}
    assert result['counts'] == {'demand_transition': 1385, 'refresh': 377, 'matched_no_transition_candidate': 3683, 'wrong_claim': 97}
    write_json(OUT / 'audit/blinded_packet_preparation.json', result, freeze=True)
    print(result)


if __name__ == '__main__':
    main()
