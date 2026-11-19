"""Freeze exact V/E contrasts for reviewed local quantities, without scoring."""
import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

from collections import Counter, defaultdict

from transformers import AutoTokenizer

from scripts.stage6b.common import ROOT, read_json, sha, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.numeric_readouts import literal_decimal, select_numeric_foil
from visual_reasoning.stage6b.protocol import candidate_event


def evidence_class(entity):
    entity = entity.lower()
    if any(w in entity for w in ('price', 'fare', 'count', 'frequency', 'miles', 'cartwheel')):
        return 'TABLE_OR_CHART_NUMERIC_CELL'
    if any(w in entity for w in ('coefficient', 'constant', 'expression', 'radicand', 'multiplier')):
        return 'FORMULA_COMPONENT'
    if 'coordinate' in entity:
        return 'COORDINATE_COMPONENT'
    if 'angle' in entity or 'arc' in entity:
        return 'ANGLE_OR_ARC_LABEL'
    if 'area' in entity:
        return 'AREA_LABEL'
    return 'LENGTH_LABEL'


def main():
    tokenizer = AutoTokenizer.from_pretrained(read_json(OUT / 'config/stage6br_config.json')['model_checkpoint'], local_files_only=True)
    index = {r['event_id']: r for r in rows(OUT / 'inputs/c1_index.jsonl')}
    draft_by_event, exclusions = defaultdict(list), []
    quoted_reviews = {}
    for split in ('discovery', 'confirmation'):
        reviews = {r['id']: r for r in rows(OUT / f'annotation_repair/{split}_quote_semantic_reviews.jsonl')}
        for r in rows(OUT / f'review/{split}_quote_readouts.jsonl'):
            review = reviews[r['id']]
            key = (r['event_id'], r['char_start'], r['char_end'], r['associated_source_id'])
            quoted_reviews[key] = review
            if not review['source_value_readout_matches_current_demand'] or review['demand_sources'] is None:
                exclusions.append({'id': r['id'], 'reason': review['binding_assessment'], 'method': 'QUOTE_REVIEW'})
                continue
            correct = review['local_semantic_value_for_current_readout']
            note = review['note']
            # Native "40 points lost" is already a signed-loss claim. Replacing
            # 40 with -40 would reverse the semantics a second time.
            if r['base_id'] == 'mathvista_323' and r['associated_source_id'] == 'A':
                correct = '40'
                note = 'Loss direction is carried by lost/loss in native context; numeric magnitude40 is correct, not an observed wrong token.'
            draft_by_event[r['event_id']].append({'input_id': r['id'], 'source_id': r['associated_source_id'],
                'span_id': r['span_id'], 'char_start': r['char_start'], 'char_end': r['char_end'],
                'assertion_start': r['quote_char_start'], 'assertion_end': r['quote_char_start']+len(r['quote']),
                'assertion': r['quote'], 'correct_value': correct, 'demand_sources': review['demand_sources'],
                'reason_for_validity': note, 'annotation_method': 'REVIEWED_SOURCE_QUOTATION'})
    for r in rows(OUT / 'annotation_repair/direct_assertion_semantic_reviews.jsonl'):
        if r['review_status'] != 'LOCAL_ASSERTION_VALID':
            continue
        key = (r['event_id'], r['value_char_start'], r['char_end'], r['source_id'])
        # Preserve the explicit quote adjudication when both methods address
        # the same literal/source; a short alias cannot undo a role ambiguity.
        if key in quoted_reviews:
            continue
        draft_by_event[r['event_id']].append({'input_id': r['id'], 'source_id': r['source_id'],
            'span_id': r['span_id'], 'char_start': r['value_char_start'], 'char_end': r['char_end'],
            'assertion_start': r['char_start'], 'assertion_end': r['char_end'], 'assertion': r['local_assertion'],
            'correct_value': r['correct_value'], 'demand_sources': r['demand_sources'],
            'reason_for_validity': r['scope'], 'annotation_method': 'REVIEWED_DIRECT_ASSERTION'})
    result = []
    for eid in sorted(draft_by_event):
        meta = index[eid]
        packet = read_json(OUT / 'review/packets' / (eid + '.json'))
        source_defs = {s['source_id']: s for s in packet['sources']}
        tokens = list(rows(meta['tokens_artifact']))
        raw = ''.join(t['decoded_token'] for t in tokens)
        seen = set()
        for r in sorted(draft_by_event[eid], key=lambda x: (x['char_start'], x['source_id'])):
            key = (r['char_start'], r['char_end'], r['source_id'])
            if key in seen:
                continue
            seen.add(key)
            source = source_defs[r['source_id']]
            actual = raw[r['char_start']:r['char_end']]
            assert raw[r['assertion_start']:r['assertion_end']] == r['assertion']
            correct = str(r['correct_value'])
            actual_number, correct_number = literal_decimal(actual), literal_decimal(correct)
            if actual_number is None or correct_number is None:
                exclusions.append({'id': r['input_id'], 'reason': 'NONLITERAL_VALUE_REQUIRES_OTHER_READOUT'})
                continue
            is_wrong = actual_number != correct_number
            foil = actual if is_wrong else select_numeric_foil(correct, source['counterfactual_value'],
                [s['condition_truth_value'] for sid, s in sorted(source_defs.items()) if sid != r['source_id']])
            try:
                event = candidate_event(tokens, r['char_start'], r['char_end'], correct, foil, tokenizer)
            except (ValueError, RuntimeError) as error:
                exclusions.append({'id': r['input_id'], 'reason': str(error)})
                continue
            assert event['history_before_ed_token_ids'] == [int(t['token_id']) for t in tokens[:event['candidate_start_token']]]
            result.append({**r, 'id': eid + '__value_' + str(r['char_start']) + '_' + r['source_id'],
                **{k: meta[k] for k in ('event_id', 'base_id', 'dataset', 'condition', 'split', 'group_id')},
                'event': event, 'readout_types': ['V', 'E'] if is_wrong else ['V'],
                'readout_validity': 'MULTI_VALID' if is_wrong else 'VALUE_VALID',
                'native_value': actual, 'foil_value': foil, 'observed_wrong_claim': is_wrong,
                'ground_truth_direction': 'correct_minus_foil', 'wrong_direction': 'foil_minus_correct' if is_wrong else None,
                'evidence_class': evidence_class(source['entity']),
                'normalized_token_progress': event['current_query_zero_based'] / len(tokens),
                'source_identity_mapped': all(source_defs[s]['current_image_source_identity_mapped'] for s in r['demand_sources']),
                'new_visual_acquisition_required': 'UNRESOLVED',
                'full_interval_review_status': 'PENDING', 'frozen_before_new_causal_scores': True})
    write_jsonl(OUT / 'annotation_repair/value_readouts.jsonl', result, freeze=True)
    write_jsonl(OUT / 'annotation_repair/value_readout_exclusions.jsonl', exclusions, freeze=True)
    audit = {'status': 'VALUE_CANDIDATES_FROZEN_INTERVALS_PENDING', 'readouts': len(result),
        'bases': len({r['base_id'] for r in result}), 'conditions': Counter(r['condition'] for r in result),
        'observed_wrong_value_readouts': sum(r['observed_wrong_claim'] for r in result),
        'excluded_quote_or_token_drafts': len(exclusions), 'all_native_histories_exact': True,
        'signed_loss_magnitude_repaired': True, 'derived_radii_not_mislabeled_wrong': True,
        'sha256': sha(OUT / 'annotation_repair/value_readouts.jsonl'), 'gpu_computation': False}
    write_json(OUT / 'audit/value_readout_freeze.json', audit, freeze=True)
    print(audit)


if __name__ == '__main__':
    main()
