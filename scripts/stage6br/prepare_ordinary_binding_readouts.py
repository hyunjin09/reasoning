"""Export ordinary radius/diameter contrasts without selecting error cases.

These are full assertions, not extra timepoints inside a single assertion.
Context and interval adjudication remain mandatory before panel admission.
"""
import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import re
from collections import defaultdict

from transformers import AutoTokenizer

from scripts.stage6b.common import read_json, sha, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from visual_reasoning.stage6b.protocol import candidate_event


# Explicitly reviewed local source/role templates; parent scope is separate.
REVIEWED_BASES = {
    'mathverse_639', 'mathverse_641', 'mathverse_645', 'mathverse_651',
    'mathverse_654', 'mathverse_690', 'mathverse_691', 'mathverse_692',
    'mathverse_698', 'mathverse_715', 'mathvision_3004', 'mathvista_804',
}


def main():
    tokenizer = AutoTokenizer.from_pretrained(
        read_json(OUT / 'config/stage6br_config.json')['model_checkpoint'],
        local_files_only=True)
    index = {r['event_id']: r for r in rows(OUT / 'inputs/c1_index.jsonl')}
    by_event = defaultdict(list)
    for r in rows(OUT / 'annotation_repair/value_readouts.jsonl'):
        if (r['base_id'] in REVIEWED_BASES and len(r['demand_sources']) == 1
                and not r['observed_wrong_claim']
                and len(re.findall(r'\b(?:radius|diameter)\b', r['assertion'], re.I)) == 1):
            by_event[r['event_id']].append(r)
    output, exclusions = [], []
    for eid, candidates in sorted(by_event.items()):
        tokens = list(rows(index[eid]['tokens_artifact']))
        raw = ''.join(t['decoded_token'] for t in tokens)
        seen = set()
        for r in candidates:
            key = (r['assertion_start'], r['assertion_end'], r['source_id'])
            if key in seen:
                continue
            seen.add(key)
            native = r['assertion']
            assert raw[key[0]:key[1]] == native
            role = re.search(r'\b(radius|diameter)\b', native, re.I).group().lower()
            replacement = 'diameter' if role == 'radius' else 'radius'
            foil = re.sub(r'\b' + role + r'\b', replacement, native, flags=re.I)
            old_symbol, new_symbol = ('r', 'd') if role == 'radius' else ('d', 'r')
            foil = re.sub(r'\b' + old_symbol + r'\b', new_symbol, foil)
            foil = re.sub(r'\b' + old_symbol.upper() + r'\b', new_symbol.upper(), foil)
            assert re.findall(r'\d+(?:\.\d+)?', native) == re.findall(r'\d+(?:\.\d+)?', foil)
            try:
                event = candidate_event(tokens, key[0], key[1], native, foil, tokenizer)
            except (ValueError, RuntimeError) as error:
                exclusions.append({'input_id': r['id'], 'reason': str(error)})
                continue
            assert event['native_claim_suffix_ids'] == event['original_divergent_suffix_ids']
            result = {k:v for k,v in r.items() if k not in {
                'event', 'input_id', 'native_value', 'correct_value', 'foil_value'}}
            result.update({
                'id': eid + '__ordinary_binding_' + str(key[0]) + '_' + r['source_id'],
                'input_value_id': r['id'], 'char_start': key[0], 'char_end': key[1],
                'event': event, 'native_claim': native, 'correct_claim': native,
                'foil_claim': foil, 'readout_types': ['B'],
                'readout_validity': 'BINDING_CANDIDATE_CONTEXT_REVIEW_REQUIRED',
                'values_held_fixed': True, 'observed_wrong_claim': False,
                'ground_truth_direction': 'correct_minus_foil', 'wrong_direction': None,
                'full_claim_context_scored': True,
                'normalized_token_progress': event['current_query_zero_based'] / len(tokens),
                'reason_for_validity': 'Explicitly reviewed nonzero radius/diameter assignment; role foil holds all literal numbers fixed. Parent qualification must still be adjudicated.',
                'annotation_method': 'MAIN_AGENT_REVIEWED_RADIUS_DIAMETER_TEMPLATES',
                'same_assertion_is_not_an_independent_hold': True,
            })
            output.append(result)
    path = OUT / 'annotation_repair/ordinary_binding_readouts.jsonl'
    write_jsonl(path, output, freeze=True)
    write_jsonl(OUT / 'annotation_repair/ordinary_binding_exclusions.jsonl', exclusions, freeze=True)
    audit = {'status': 'ORDINARY_BINDING_CANDIDATES_FROZEN_CONTEXT_PENDING',
             'candidates': len(output), 'bases': len({r['base_id'] for r in output}),
             'all_values_fixed': True, 'all_native_histories_exact': True,
             'error_panel_selected': False, 'gpu_computation': False,
             'sha256': sha(path), 'exclusions': len(exclusions)}
    write_json(OUT / 'audit/ordinary_binding_readout_freeze.json', audit, freeze=True)
    print(audit)


if __name__ == '__main__':
    main()
