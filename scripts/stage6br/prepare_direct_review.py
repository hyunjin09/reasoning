"""Split-specific direct assertion proposals; semantic review remains separate."""
import argparse
import re
from collections import Counter

from scripts.stage6b.common import ROOT, read_json, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.direct_claims import claim_checks
from scripts.stage6br.propositions import binding_proposals, split_propositions


def normalized_patterns(original, sources):
    result = dict(original)
    for sid, source in sources.items():
        words = source['entity'].split()
        if len(words) == 2 and words[1] in {'height', 'radius', 'diameter', 'length', 'depth'}:
            reverse = r'\b' + re.escape(words[1]) + r'\s+of\s+(?:the\s+)?' + re.escape(words[0]) + r'\b'
            result[sid] = '(?:' + result.get(sid, re.escape(source['entity'])) + ')|(?:' + reverse + ')'
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', choices=('discovery', 'confirmation'), default='discovery')
    split = parser.parse_args().split
    if split == 'confirmation':
        assert read_json(OUT / 'config/annotation_review_rules.json')['confirmation_rules_unchanged']
    aliases = read_json(OUT / 'review/source_aliases.json')
    records = []
    for item in rows(OUT / 'review/packet_index.jsonl'):
        if item['split'] != split:
            continue
        packet = read_json(ROOT / item['packet_path'])
        sources = {r['source_id']: r for r in packet['sources']}
        patterns = normalized_patterns(aliases[item['event_id']], sources)
        for span in packet['spans']:
            for n, part in enumerate(split_propositions(span['text'], patterns)):
                mentions = sorted(s for s, pattern in patterns.items() if re.search(pattern, part['text'], re.I))
                for k, claim in enumerate(binding_proposals(part['text'], patterns)):
                    checks = claim_checks(part['text'], claim, sources[claim['source_id']])
                    start = span['char_start'] + part['start']
                    records.append({'id': item['event_id'] + '__' + span['span_id'] + f'__p{n}_c{k}',
                        'event_id': item['event_id'], 'base_id': item['base_id'], 'split': split,
                        'dataset': packet['dataset'], 'condition': packet['condition'], 'span_id': span['span_id'],
                        'text': part['text'], 'full_span': span['text'], 'char_start': start,
                        'char_end': span['char_start'] + part['end'], 'normalized_span_progress': span['normalized_token_progress'],
                        'value_char_start': start + claim['value_start'], 'value_char_end': start + claim['value_end'],
                        'role_char_start': start + claim['role_start'], 'role_char_end': start + claim['role_end'],
                        'source_mentions': mentions, 'claim': claim, 'source_definition': sources[claim['source_id']],
                        'rule_checks': checks, 'provisional_demand': mentions if not checks else None,
                        'review_status': 'PENDING_SEMANTIC_REVIEW', 'packet_path': item['packet_path']})
    write_jsonl(OUT / f'review/{split}_direct_assertions.jsonl', records, freeze=True)
    clear = [r for r in records if not r['rule_checks']]
    result = {'status': split.upper() + '_DRAFT_ONLY', 'assertions': len(records), 'checks_clear': len(clear),
              'clear_singletons': sum(len(r['source_mentions']) == 1 for r in clear),
              'clear_bases': len({r['base_id'] for r in clear}),
              'review_flags': Counter(x for r in records for x in r['rule_checks']),
              'confirmation_processed': split == 'confirmation', 'causal_scoring_permitted': False}
    write_json(OUT / f'audit/{split}_direct_assertion_preparation.json', result, freeze=True)
    print(result)


if __name__ == '__main__':
    main()
