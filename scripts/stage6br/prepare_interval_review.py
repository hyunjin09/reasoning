"""Export consecutive repaired endpoints with every intervening native byte."""
import hashlib
from collections import Counter, defaultdict

from scripts.stage6b.common import SOURCE, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.semantic_contract import transition_type


def main():
    index = {r['event_id']: r for r in rows(OUT / 'inputs/c1_index.jsonl')}
    contexts = {r['id']:r for r in rows(OUT / 'review/readout_context.jsonl')}
    by_event = defaultdict(list)
    for r in rows(OUT / 'annotation_repair/value_readouts.jsonl'):
        by_event[r['event_id']].append(r)
    maps = defaultdict(dict)
    for r in rows(SOURCE / 'regions/controlled_roi_maps.jsonl'):
        if r['event_id'] in by_event:
            maps[r['event_id']][r['source_id']] = set(r['absolute_token_indices'])
    records = []
    for eid, anchors in sorted(by_event.items()):
        meta = index[eid]
        tokens = list(rows(meta['tokens_artifact']))
        raw = ''.join(t['decoded_token'] for t in tokens)
        grouped = defaultdict(list)
        for r in anchors:
            grouped[r['event']['current_query_zero_based']].append(r)
        sequence = []
        for query, same_query in sorted(grouped.items()):
            same_query.sort(key=lambda r:r['id'])
            demand = sorted({s for r in same_query for s in r['demand_sources']})
            sequence.append((same_query[0], demand, [r['id'] for r in same_query]))
        for (pre, before, preids), (post, after, postids) in zip(sequence, sequence[1:]):
            label = transition_type(before, after)
            pair_id = eid + '__interval_' + hashlib.sha256((pre['id'] + '|' + post['id']).encode()).hexdigest()[:12]
            left, right = min(pre['assertion_start'], post['assertion_start']), max(pre['assertion_end'], post['assertion_end'])
            assert left <= pre['char_start'] < post['char_start'] < right
            bridge = raw[pre['assertion_end']:post['assertion_start']] if pre['assertion_end'] <= post['assertion_start'] else None
            singleton = len(before) == len(after) == 1
            mapped = pre['source_identity_mapped'] and post['source_identity_mapped']
            overlap = sorted(maps[eid].get(before[0], set()) & maps[eid].get(after[0], set())) if singleton and before != after else []
            records.append({'id': pair_id, **{k:meta[k] for k in ('event_id','base_id','dataset','condition','split','group_id')},
                'pre_id': pre['id'], 'post_id': post['id'], 'pre_equivalent_query_ids': preids, 'post_equivalent_query_ids': postids,
                'demand_before': before, 'demand_after': after, 'endpoint_transition_type': label,
                'pre_assertion': pre['assertion'], 'post_assertion': post['assertion'],
                'native_interval_text': raw[left:right], 'native_interval_char_start': left, 'native_interval_char_end': right,
                'inter_assertion_bridge': bridge,
                'pre_endpoint_context': contexts[pre['id']],
                'post_endpoint_context': contexts[post['id']],
                'token_gap': post['event']['current_query_zero_based'] - pre['event']['current_query_zero_based'],
                'normalized_progress': post['normalized_token_progress'],
                'readout_type': 'V', 'evidence_class': post['evidence_class'],
                'source_identity_mapped': mapped, 'source_overlap_token_indices': overlap,
                'structural_primary_candidate': singleton and label in {'T0','T1'} and mapped and not overlap,
                'semantic_interval_review_status': 'REQUIRED',
                'warning': 'Endpoint demand equality alone does not establish a stable hold. Full interval text must be reviewed.'})
    write_jsonl(OUT / 'review/interval_packets.jsonl', records, freeze=True)
    summary = {'status':'INTERVAL_PACKETS_NOT_ACCEPTED', 'intervals':len(records),
        'endpoint_types':Counter(r['endpoint_transition_type'] for r in records),
        'structural_primary_candidates':Counter(r['endpoint_transition_type'] for r in records if r['structural_primary_candidate']),
        'all_intervening_text_retained':True, 'primary_panel_frozen':False}
    write_json(OUT / 'audit/interval_preparation.json', summary, freeze=True)
    print(summary)


if __name__ == '__main__':
    main()
