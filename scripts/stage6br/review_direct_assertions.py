"""Record reviewed local assertion associations, retaining unresolved proposals.

All531discovery singleton-clear and940confirmation check-clear distinct
source/text pairs were read by the main agent. Subsequent syntactic guards only
remove false associations from that reviewed pool. Approval applies to the
short source/value assertion, never the surrounding coordinate/calculation.
"""
import re
from collections import Counter

from scripts.stage6b.common import sha, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.local_assertions import local_assertion_checks
from scripts.stage6br.numeric_readouts import literal_decimal


def review(r):
    c, src, text = r['claim'], r['source_definition'], r['text']
    role = text[c['role_start']:c['role_end']].lower()
    prefix = text[:c['role_start']].lower()
    reasons = list(r['rule_checks']) + local_assertion_checks(text, c, src)
    demand = [c['source_id']]
    if r['split'] == 'discovery' and len(r['source_mentions']) != 1:
        reasons.append('MULTI_ALIAS_DIRECT_PROPOSAL_NOT_IN_THIS_LOCAL_REVIEW_STRATUM')
    if '?' in text or re.search(r'\b(?:case\s*\d|either|would|likely|probably|example|typo|intended|let.s take|let.s say)\b', text, re.I):
        reasons.append('QUESTION_OR_ALTERNATIVE_SCENARIO_REQUIRES_REVIEW')
    if re.search(r'(?:\^|[²³]|\*)[^.;]*$', prefix):
        reasons.append('EQUATION_CONTEXT_NOT_INDEPENDENT_SOURCE_ASSERTION')
    if literal_decimal(src['condition_truth_value']) is None or any(w in src['entity'] for w in ('coefficient', 'constant', 'multiplier', 'radicand')):
        reasons.append('DERIVED_QUANTITY_OR_EXPRESSION_NEEDS_SEPARATE_READOUT')
    base, sid = r['base_id'], c['source_id']
    if (base == 'mathverse_385'
            or (base == 'mathverse_703' and sid == 'C' and "trapezoid" not in text.lower())
            or (base == 'mathverse_714' and sid in {'A', 'B'})
            or (base == 'mathvision_2504' and role == 'width')
            or (base == 'mathvision_393' and 'corner' in role)
            or base == 'mathvision_573'):
        reasons.append('SOURCE_ROLE_SCOPE_AMBIGUOUS_OR_DIFFERENT_QUANTITY')
    if base == 'mathvision_1186' and sid == 'A' and re.search(r'\b(?:layer|next|top row)\b', text, re.I):
        reasons.append('SUBROW_WIDTH_IS_NOT_FULL_BASE_WIDTH')
    if base == 'mathvision_2958':
        demand = ['D', 'F'] if sid == 'F' else ['B', 'T']
    if base == 'mathvision_3020':
        if role in {'a', 'c'}:
            reasons.append('COORDINATE_POINT_LETTER_IS_NOT_NAMED_COMPONENT')
        else:
            demand = ['B', 'D'] if sid == 'D' else ['C', 'E', 'T']
    if base == 'mathvision_3004' and role in {'top circle', 'bottom circle'}:
        reasons.append('CIRCUMFERENCE_OR_ENTITY_ONLY_NOT_DIAMETER_ASSERTION')
    if base == 'mathvision_1089' and re.search(r'\b(?:angle abc|triangle abc|angle in the triangle)\b', text, re.I):
        reasons.append('STAR_VERTEX_BINDING_REQUIRES_EXPLICIT_RAYS')
    if base == 'mathverse_779' and re.search(r'\btriangle\s+[a-z]{3}\b', text, re.I):
        reasons.append('MULTIRAY_VERTEX_SUBANGLE_REQUIRES_REVIEW')
    if base == 'mathvista_978' and re.search(r'\b(?:largest|smallest)\b', text, re.I):
        demand = sorted('TABCDEF')
    if base == 'mathvista_726':
        reasons.append('ARC_RELATION_TO_EXTERIOR_ANGLE_REQUIRES_GEOMETRY_REVIEW')
    if base == 'mathvista_781' and sid == 'A':
        reasons.append('MEDIAN_EQUATION_IS_NOT_INDEPENDENT_FK_LOOKUP')
    return sorted(set(reasons)), demand


def main():
    records = []
    inputs = []
    for split in ('discovery', 'confirmation'):
        path = OUT / f'review/{split}_direct_assertions.jsonl'
        inputs.append({'path': str(path), 'sha256': sha(path)})
        for r in rows(path):
            reasons, demand = review(r)
            c = r['claim']
            records.append({'id': r['id'], 'event_id': r['event_id'], 'base_id': r['base_id'], 'split': split,
                'source_id': c['source_id'], 'span_id': r['span_id'], 'demand_sources': demand if not reasons else None,
                'review_status': 'LOCAL_ASSERTION_VALID' if not reasons else 'UNRESOLVED_OR_READOUT_UNAVAILABLE',
                'reasons': reasons, 'local_assertion': r['text'][c['role_start']:c['value_end']],
                'char_start': r['role_char_start'], 'char_end': r['value_char_end'],
                'value_char_start': r['value_char_start'], 'correct_value': str(r['source_definition']['condition_truth_value']),
                'native_value': c['value_text'],
                'scope': 'Explicit entity/value assertion only; surrounding reasoning and interval demand require separate review.',
                'new_visual_acquisition_required': 'UNRESOLVED', 'prior_text_content_status': 'NOT_YET_AUDITED',
                'annotation_method': 'Main-agent review of source/text template pool with conservative ambiguity guards; excluded proposals are not certified.',
                'causal_values_used': False})
    write_jsonl(OUT / 'annotation_repair/direct_assertion_semantic_reviews.jsonl', records, freeze=True)
    eligible = [r for r in records if r['review_status'] == 'LOCAL_ASSERTION_VALID']
    result = {'status': 'LOCAL_ASSERTION_REVIEW_COMPLETE_FULL_INTERVALS_PENDING', 'inputs': inputs,
        'records': len(records), 'local_assertions_valid': len(eligible),
        'bases_with_local_assertions': len({r['base_id'] for r in eligible}),
        'excluded': len(records)-len(eligible), 'exclusion_reasons': Counter(x for r in records for x in r['reasons']),
        'reviewed_distinct_template_counts': {'discovery_singleton_check_clear': 531, 'confirmation_check_clear': 940},
        'primary_panel_frozen': False, 'causal_values_used': False}
    write_json(OUT / 'audit/direct_assertion_semantic_review.json', result, freeze=True)
    print({k: v for k, v in result.items() if k not in {'inputs', 'exclusion_reasons'}})


if __name__ == '__main__':
    main()
