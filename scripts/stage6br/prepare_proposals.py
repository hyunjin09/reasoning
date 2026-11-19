"""Prepare reviewable local assertions, including inherited exact source quotes."""
from collections import Counter, defaultdict

from scripts.stage6b.common import SOURCE, read_json, sha, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.propositions import split_propositions, binding_proposals


def main():
    packets = list(rows(OUT / 'review/packet_index.jsonl'))
    needed = {p['event_id'] for p in packets}
    patterns = {}
    claims = defaultdict(list)
    for r in rows(SOURCE / 'traces/controlled_demand_annotations.jsonl'):
        if r['event_id'] not in needed:
            continue
        patterns.setdefault(r['event_id'], r['source_alias_patterns'])
        # Claims retain semantic quote/source evidence, with correctness and
        # previously computed demand/causal labels deliberately omitted.
        for claim in r.get('source_claims', []):
            claims[(r['event_id'], r['span_id'])].append({k: claim[k] for k in ['source_id', 'quote']})
    write_json(OUT / 'review/source_aliases.json', patterns, freeze=True)
    propositions = []
    source_claims = []
    for item in packets:
        packet = read_json(item['packet_path'])
        eid = item['event_id']
        for span in packet['spans']:
            for number, p in enumerate(split_propositions(span['text'], patterns[eid])):
                found = binding_proposals(p['text'], patterns[eid])
                propositions.append({'id': eid + '__' + span['span_id'] + '__clause' + str(number),
                    'event_id': eid, 'base_id': item['base_id'], 'split': item['split'], 'span_id': span['span_id'],
                    'char_start': span['char_start'] + p['start'], 'char_end': span['char_start'] + p['end'],
                    'text': p['text'], 'binding_proposals': found, 'review_status': 'PENDING',
                    'provenance': item['packet_path']})
            for claim in claims[(eid, span['span_id'])]:
                start = span['text'].find(claim['quote'])
                source_claims.append({'event_id': eid, 'base_id': item['base_id'], 'split': item['split'],
                    'span_id': span['span_id'], **claim, 'quote_wholly_in_span': start >= 0,
                    'char_start': span['char_start'] + start if start >= 0 else None,
                    'source': 'Inherited exact semantic source quote; demand completeness and readout validity require repair review.'})
    write_jsonl(OUT / 'review/proposition_proposals.jsonl', propositions, freeze=True)
    write_jsonl(OUT / 'review/inherited_semantic_quotes.jsonl', source_claims, freeze=True)
    proposals = [p for p in propositions if p['binding_proposals']]
    result = {'status': 'PROPOSALS_ONLY_NOT_ACCEPTED_ANNOTATIONS', 'propositions': len(propositions),
        'with_explicit_binding_proposal': len(proposals), 'proposal_bases': len({p['base_id'] for p in proposals}),
        'inherited_source_quotes': len(source_claims), 'quote_bases': len({p['base_id'] for p in source_claims}),
        'split_proposals': Counter(p['split'] for p in proposals),
        'no_causal_scores_read': True, 'all_accepted_annotations_require_semantic_review': True,
        'proposal_sha256': sha(OUT / 'review/proposition_proposals.jsonl')}
    write_json(OUT / 'audit/proposal_preparation.json', result, freeze=True)
    print(result)


if __name__ == '__main__':
    main()
