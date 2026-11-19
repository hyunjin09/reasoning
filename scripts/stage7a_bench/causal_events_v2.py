"""Join reviewed native claims and source geometry before any causal scoring.

This compiler does not select a pilot, certify edits, infer source truth, or
assign a causal state. The caller must verify artifact hashes and freeze the
selected cohort before using these entries for an experiment.
"""
from copy import deepcopy

from scripts.stage7a_bench.causal_readouts_v2 import compile_readout
from scripts.stage7a_bench.source_mapping_v2 import map_source_boxes


def compile_downstream_review(review, claim_index, tokens, annotation):
    """Bind an independently reviewed later integration error to this read.

    Final-answer disagreement alone never supplies this review. The exact
    response, source annotation and semantic review receive artifact checks in
    causal_provenance_v2 before a prepared entry can enter a frozen pilot.
    """
    downstream = annotation.get('downstream_review')
    if downstream is None:
        return None
    claim = review['claims'][claim_index]
    if (not isinstance(downstream, dict) or
            downstream.get('status') != 'REVIEWED_DOWNSTREAM_ERROR' or
            type(downstream.get('claim_index')) is not int or
            downstream['claim_index'] != claim_index or
            downstream.get('demanded_source_id') != claim['source_id'] or
            any(downstream.get('claim_'+k) != claim[k]
                for k in ('readout_char_start', 'readout_char_end'))):
        raise ValueError('Downstream review is not bound to the selected native claim')
    if (claim.get('locally_correct') is not True or
            review.get('correct_local_read_followed_by_later_error') is not True or
            any(downstream.get(k) is not True for k in
                ('integration_error_eligible', 'later_error', 'error_uses_selected_local_evidence')) or
            any(downstream.get(k) is not False for k in
                ('error_is_new_visual_read', 'causal_or_passive_scores_used')) or
            not isinstance(downstream.get('review_note'), str) or
            not downstream['review_note'].strip()):
        raise ValueError('Downstream integration requires a reviewed correct read and dependent later error')
    raw = ''.join(t['decoded_token'] for t in tokens)
    quote = downstream.get('error_quote')
    start, end = downstream.get('error_char_start'), downstream.get('error_char_end')
    if (not isinstance(quote, str) or not quote or raw.count(quote) != 1 or
            type(start) is not int or type(end) is not int or
            not claim['readout_char_end'] < start < end <= len(raw) or
            raw[start:end] != quote):
        raise ValueError('Downstream error must have a unique exact native span after the local read')
    return deepcopy(downstream)


def compile_event(row, review, claim_index, meta, tokens, annotation, family_map, tokenizer):
    if row.get('no_image') or row['benchmark'] == 'phantom_0' or not meta.get('visual_token_indices'):
        raise ValueError('Source-causal event requires an actual visual input')
    for key in ('event_id', 'base_id', 'benchmark', 'condition'):
        if review.get(key) != row[key]:
            raise ValueError('Semantic review identity differs from native row: ' + key)
    if any(meta.get(k) != row[k] for k in ('event_id', 'condition')):
        raise ValueError('Input metadata identity differs from native row')
    if any(v.get('causal_or_passive_scores_used') is not False for v in (review, annotation)):
        raise ValueError('Semantic/source annotation must precede causal or passive scores')
    family = family_map.get(row['base_id'])
    if not isinstance(family, str) or not family:
        raise ValueError('Verified analysis source family is required; no filename fallback')
    if type(claim_index) is not int or not 0 <= claim_index < len(review['claims']):
        raise ValueError('Explicit reviewed claim index required')
    claim = deepcopy(review['claims'][claim_index])
    if (annotation.get('demanded_source_id') != claim.get('source_id') or
            annotation.get('target_ground_truth') != claim.get('ground_truth')):
        raise ValueError('Source identity/truth differs between the independent reviews')
    note = annotation.get('source_review_note')
    if not isinstance(note, str) or not note.strip():
        raise ValueError('Source review evidence is required')
    availability = annotation.get('target_source_status')
    if availability not in ('available', 'degraded', 'unavailable', 'queried_object_absent'):
        raise ValueError('Explicit reviewed target availability required')
    mapping = map_source_boxes(meta, annotation['sources'])
    groups = mapping['groups']
    if any(p >= len(meta['prompt_token_ids']) for positions in groups.values() for p in positions):
        raise ValueError('Source token lies outside the native prompt')
    if availability == 'available' and 'T' not in groups:
        raise ValueError('Available demanded source requires a reviewed target footprint')
    independent = annotation.get('independently_identified_target_and_alternative')
    if type(independent) is not bool:
        raise ValueError('Explicit independent source-identification judgment required')
    candidates = annotation['candidates']
    if candidates.get('correct') != annotation['target_ground_truth']:
        raise ValueError('The correct candidate must equal the independently reviewed literal truth')
    alternative = annotation.get('alternative')
    wrong_matches, other_id = None, None
    if 'X' in groups:
        if (not isinstance(alternative, dict) or not alternative.get('source_id') or
                alternative['source_id'] == claim['source_id'] or
                not isinstance(alternative.get('review_note'), str) or
                not alternative['review_note'].strip() or
                'alternative_original' not in candidates or 'wrong_claim_matches' not in alternative):
            raise ValueError('An alternative footprint requires its own reviewed identity and literal value')
        other_id = alternative['source_id']
        wrong_matches = alternative.get('wrong_claim_matches')
        if type(wrong_matches) is not bool and wrong_matches is not None:
            raise ValueError('Alternative match must be adjudicated boolean or explicit unknown')
        if wrong_matches is True and (claim['locally_correct'] is not False or
                candidates['alternative_original'] != claim['readout']):
            raise ValueError('Claimed alternative match contradicts actual wrong literal evidence')
    elif alternative or any(k.startswith('alternative_') for k in candidates) or independent:
        raise ValueError('Unavailable alternative cannot acquire semantic candidates or independence')
    if 'I' in groups:
        control = annotation.get('irrelevant_control_review') or {}
        if (control.get('matched_to_target') is not True or control.get('irrelevant_to_claim') is not True or
                not isinstance(control.get('note'), str) or not control['note'].strip() or
                len(groups['I']) != len(groups.get('T', [])) or
                any(set(groups['I']) & set(groups.get(s, [])) for s in ('T', 'X', 'X2'))):
            raise ValueError('An irrelevant control requires reviewed matching and disjoint irrelevant tokens')
    event = compile_readout(tokens, claim, candidates, tokenizer)
    claim['wrong_claim_matches_alternative'] = wrong_matches
    native_row = deepcopy(row)
    native_row['target_availability'] = 'intact' if availability == 'available' else availability
    return dict(id=row['event_id'] + f'__e{claim_index:02d}', event_id=row['event_id'],
        base_id=row['base_id'], benchmark=row['benchmark'], condition=row['condition'],
        analysis_family_id=family, native_family_id=row.get('family_id'), row=native_row,
        event=event, reviewed_claim=claim, source_annotation=deepcopy(annotation),
        source_groups=groups, source_mapping=mapping,
        source_separation_valid=independent and mapping['target_alternative_token_disjoint'] is True,
        source_aliases={}, physical_demanded_source=claim['source_id'], physical_alternative_source=other_id,
        irrelevant_control_valid_for_current_demand='I' in groups,
        w2_sources=[s for s in ('T', 'X', 'X2', 'I', 'G') if s in groups],
        w8_sources=[s for s in ('T', 'X') if s in groups], readout_type='V',
        downstream_review=compile_downstream_review(review, claim_index, tokens, annotation),
        causal_state=None, causal_pilot_frozen=False,
        selection_used_causal_or_passive_scores=False,
        compilation_scope='Mechanical native singleton-value event with optional independently reviewed later-error span; pilot eligibility, artifact provenance, edits and causal integration state remain unverified here.')
