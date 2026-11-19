"""Adjacent native readout intervals involving a real role confirmation."""
import hashlib
from collections import Counter, defaultdict

from scripts.stage6b.common import read_json, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.prepare_readout_context import QUALIFIER
from scripts.stage6br.semantic_contract import transition_type


def main():
    role = list(rows(OUT / 'annotation_repair/role_confirmation_readouts.jsonl'))
    role_ids = {r['id'] for r in role}
    eids = {r['event_id'] for r in role}
    by = defaultdict(list)
    for r in list(rows(OUT / 'annotation_repair/value_readouts.jsonl')) + role:
        if r['event_id'] in eids:
            by[r['event_id']].append(r)
    contexts = {r['id']:r for r in rows(OUT / 'review/readout_context.jsonl')}
    index = {r['event_id']:r for r in rows(OUT / 'inputs/c1_index.jsonl')}
    result = []
    for eid, anchors in sorted(by.items()):
        packet = read_json(OUT / 'review/packets' / (eid + '.json'))
        spans = {s['span_id']:s for s in packet['spans']}
        raw = ''.join(t['decoded_token'] for t in rows(index[eid]['tokens_artifact']))
        for r in anchors:
            if r['id'] in contexts:
                continue
            span = spans[r['span_id']]
            prefix = raw[span['char_start']:r['assertion_end']]
            previous = spans.get('S'+str(int(r['span_id'][1:])-1).zfill(4))
            contexts[r['id']] = {'id':r['id'],'parent_prefix_through_assertion':prefix,
                'previous_span_context':previous['text'] if previous else None,
                'conditional_or_alternative_markers':[m.group() for m in QUALIFIER.finditer(prefix)],
                'mandatory_overlay':True,'readout_validity_if_unresolved':'READOUT_INSUFFICIENT'}
        grouped = defaultdict(list)
        for r in anchors:
            grouped[r['event']['current_query_zero_based']].append(r)
        sequence = []
        for query, group in sorted(grouped.items()):
            group.sort(key=lambda x:x['id'])
            sequence.append((group[0], sorted({s for x in group for s in x['demand_sources']})))
        for (a,before),(b,after) in zip(sequence,sequence[1:]):
            if not ({a['id'],b['id']} & role_ids):
                continue
            left=min(a['assertion_start'],b['assertion_start']);right=max(a['assertion_end'],b['assertion_end'])
            kind=transition_type(before,after)
            rid=eid+'__role_interval_'+hashlib.sha256((a['id']+'|'+b['id']).encode()).hexdigest()[:12]
            mapped=a['source_identity_mapped'] and b['source_identity_mapped']
            result.append({k:a[k] for k in ('event_id','base_id','dataset','condition','split','group_id')} | {
                'id':rid,'pre_id':a['id'],'post_id':b['id'],'demand_before':before,'demand_after':after,
                'endpoint_transition_type':kind,'pre_assertion':a['assertion'],'post_assertion':b['assertion'],
                'native_interval_text':raw[left:right],'native_interval_char_start':left,'native_interval_char_end':right,
                'pre_endpoint_context':contexts[a['id']],'post_endpoint_context':contexts[b['id']],
                'token_gap':b['event']['current_query_zero_based']-a['event']['current_query_zero_based'],
                'normalized_progress':b['normalized_token_progress'],
                'readout_type':('B' if a['id'] in role_ids else 'V')+'/'+('B' if b['id'] in role_ids else 'V'),
                'evidence_class':b['evidence_class'],'source_identity_mapped':mapped,
                'structural_primary_candidate':mapped and len(before)==len(after)==1 and kind in {'T0','T1'},
                'semantic_interval_review_status':'REQUIRED',
                'source_roi_overlap_status':'NOT_CHECKED_OPTIMISTIC_UPPER_BOUND_ONLY',
                'new_role_identification_does_not_automatically_qualify_as_hold':True})
    write_jsonl(OUT / 'review/role_interval_packets.jsonl',result,freeze=True)
    summary={'intervals':len(result),'types':Counter(r['endpoint_transition_type'] for r in result),
             'status':'ROLE_INTERVALS_REQUIRE_REVIEW','causal_values_used':False}
    write_json(OUT / 'audit/role_intervals.json',summary,freeze=True)
    print(summary)


if __name__=='__main__':
    main()
