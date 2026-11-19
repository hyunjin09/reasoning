"""Build split-specific readout drafts from inherited exact source quotations."""
import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import argparse
import re
from collections import Counter, defaultdict
from decimal import Decimal

from transformers import AutoTokenizer
from scripts.stage6b.common import ROOT, SOURCE, read_json, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.numeric_readouts import literal_decimal, select_numeric_foil
from visual_reasoning.stage6b.protocol import candidate_event

NUMBER = re.compile(r'(?<![\d.])-?\d+(?:\.\d+)?(?!\d|\.\d)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--split', choices=('discovery', 'confirmation'), default='discovery')
    split = parser.parse_args().split
    if split == 'confirmation':
        assert read_json(OUT / 'config/annotation_review_rules.json')['confirmation_rules_unchanged']
    config = read_json(OUT / 'config/stage6br_config.json')
    tokenizer = AutoTokenizer.from_pretrained(config['model_checkpoint'], local_files_only=True)
    index = {r['event_id']: r for r in rows(OUT / 'inputs/c1_index.jsonl') if r['split'] == split}
    sources = defaultdict(dict)
    for r in rows(SOURCE / 'regions/ground_truth_rois.jsonl'):
        if r['cohort'] == 'C1':
            sources[r['base_id']][r['source_id']] = r
    grouped = defaultdict(list)
    for r in rows(OUT / 'review/inherited_semantic_quotes.jsonl'):
        if r['event_id'] in index:
            grouped[r['event_id']].append(r)
    results, rejected = [], []
    for eid, quotes in grouped.items():
        meta = index[eid]
        tokens = list(rows(meta['tokens_artifact']))
        raw = ''.join(t['decoded_token'] for t in tokens)
        seen = set()
        for quote in quotes:
            source = sources[meta['base_id']][quote['source_id']]
            truth = source['counterfactual_value'] if meta['condition'] == 'counterfactual' and quote['source_id'] == 'T' else source['truth_value']
            if not quote['quote_wholly_in_span']:
                rejected.append({'event_id': eid, 'span_id': quote['span_id'], 'source_id': quote['source_id'], 'reason': 'QUOTE_CROSSES_SPAN_REQUIRES_REVIEW'})
                continue
            start = quote['char_start']
            assert raw[start:start + len(quote['quote'])] == quote['quote']
            value = literal_decimal(truth)
            if value is None:
                rejected.append({'event_id': eid, 'span_id': quote['span_id'], 'source_id': quote['source_id'], 'reason': 'NONLITERAL_SOURCE_VALUE'})
                continue
            numbers = list(NUMBER.finditer(quote['quote']))
            matches = [m for m in numbers if Decimal(m.group()) == value]
            # A single differing literal is an error-readout proposal, not an
            # exclusion based on whether the native value happens to be correct.
            if not matches and len(numbers) == 1:
                matches = numbers
            if not matches:
                rejected.append({'event_id': eid, 'span_id': quote['span_id'], 'source_id': quote['source_id'], 'reason': 'NO_UNAMBIGUOUS_LITERAL_VALUE'})
            for match in matches:
                a, b = start + match.start(), start + match.end()
                identity = (a, b, quote['source_id'])
                if identity in seen:
                    continue
                seen.add(identity)
                actual = raw[a:b]
                if Decimal(actual) != value:
                    foil = actual
                else:
                    other = [s['truth_value'] for sid, s in sorted(sources[meta['base_id']].items())
                             if sid != quote['source_id']]
                    foil = select_numeric_foil(truth, source['counterfactual_value'], other)
                assert Decimal(str(truth)) != Decimal(foil)
                try:
                    event = candidate_event(tokens, a, b, str(truth), foil, tokenizer)
                except (ValueError, RuntimeError) as error:
                    rejected.append({'event_id': eid, 'char_start': a, 'source_id': quote['source_id'], 'reason': str(error)})
                    continue
                results.append({'id': eid + '__char' + str(a) + '__' + quote['source_id'],
                    'event_id': eid, 'base_id': meta['base_id'], 'dataset': meta['dataset'], 'split': split,
                    'condition': meta['condition'], 'span_id': quote['span_id'], 'quote': quote['quote'],
                    'quote_char_start': start, 'char_start': a, 'char_end': b, 'associated_source_id': quote['source_id'],
                    'source_entity': source['entity'], 'source_truth_value': str(truth),
                    'native_value': actual, 'event': event,
                    'readout_type_proposal': 'V+E' if Decimal(actual) != value else 'V',
                    'semantic_demand_review_status': 'REQUIRED', 'binding_readout_status': 'NOT_YET_REPAIRED',
                    'normalized_token_progress': event['current_query_zero_based'] / len(tokens)})
    write_jsonl(OUT / f'review/{split}_quote_readouts.jsonl', results, freeze=True)
    write_jsonl(OUT / f'review/{split}_quote_readout_exclusions.jsonl', rejected, freeze=True)
    result = {'status': 'EXACT_TOKEN_DRAFTS_NOT_SEMANTIC_ACCEPTANCE', 'readouts': len(results),
              'bases': len({r['base_id'] for r in results}), 'excluded': len(rejected),
              'types': Counter(r['readout_type_proposal'] for r in results),
              'gpu_computation': False, 'confirmation_processed': split == 'confirmation'}
    write_json(OUT / f'audit/{split}_quote_readout_preparation.json', result, freeze=True)
    print(result)


if __name__ == '__main__':
    main()
