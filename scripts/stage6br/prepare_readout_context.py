"""Expose parent-span qualification omitted by local assertion extraction.

This sidecar is a mandatory eligibility overlay on frozen candidate strings.
An unresolved conditional scope must never become an observed error merely by
comparing a conditional literal with unconditional image ground truth.
"""
import re
from collections import Counter

from scripts.stage6b.common import read_json, sha, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows

QUALIFIER = re.compile(r'\b(?:if|maybe|might|could|probably|perhaps|suppose|assuming|assume|hypothetical|example)\b', re.I)


def main():
    packets = {}
    records = []
    inputs = []
    for name in ('value_readouts', 'binding_readouts', 'claim_value_readouts'):
        path = OUT / f'annotation_repair/{name}.jsonl'
        inputs.append({'path': str(path), 'sha256': sha(path)})
        for r in rows(path):
            if r['event_id'] not in packets:
                packet = read_json(OUT / 'review/packets' / (r['event_id'] + '.json'))
                packets[r['event_id']] = {s['span_id']: s for s in packet['spans']}
            spans = packets[r['event_id']]
            span = spans[r['span_id']]
            end = min(span['char_end'], r['assertion_end'])
            prefix = span['text'][:end-span['char_start']]
            assert span['char_start'] <= r['char_start'] < end
            markers = [m.group() for m in QUALIFIER.finditer(prefix)]
            previous = spans.get('S' + str(int(r['span_id'][1:])-1).zfill(4))
            records.append({'id':r['id'],'event_id':r['event_id'],'base_id':r['base_id'],
                'span_id':r['span_id'],'parent_prefix_char_start':span['char_start'],
                'parent_prefix_through_assertion':prefix,
                'previous_span_context':None if previous is None else previous['text'],
                'conditional_or_alternative_markers':markers,
                'context_status':'QUALIFICATION_REQUIRES_EXPLICIT_ADJUDICATION' if markers else 'REQUIRES_SELECTED_ENDPOINT_CONTEXT_REVIEW',
                'readout_validity_if_unresolved':'READOUT_INSUFFICIENT',
                'image_literal_mismatch_alone_establishes_error':False,
                'mandatory_overlay':True})
    write_jsonl(OUT / 'review/readout_context.jsonl', records, freeze=True)
    result={'status':'MANDATORY_FULL_CONTEXT_REVIEW_OVERLAY','inputs':inputs,'readouts':len(records),
        'parent_scope_flagged':sum(bool(r['conditional_or_alternative_markers']) for r in records),
        'by_status':Counter(r['context_status'] for r in records),
        'reason':'Do not lose conditional scope when local clauses are split. All selected endpoint contexts require review; flagged items remain insufficient until explicitly adjudicated.',
        'new_causal_scores_seen':False}
    write_json(OUT / 'audit/readout_context_requirements.json', result, freeze=True)
    print(result['by_status'])


if __name__ == '__main__':
    main()
