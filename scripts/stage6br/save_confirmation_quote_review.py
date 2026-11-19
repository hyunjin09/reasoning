"""Serialize the main agent's completed quote/image review under frozen rules.

This is an annotation sidecar, not a general semantic classifier. The specific
overrides below record inspection of all source-linked quotations exported for
confirmation; they do not certify intervening text or the full candidate pool.
"""
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.stage6b.common import read_json, sha, write_json, write_jsonl
from scripts.stage6br.prepare_inputs import OUT, rows
from scripts.stage6br.semantic_contract import demand_type


VIEWED = ['mathverse_664', 'mathverse_673', 'mathverse_745', 'mathverse_771',
          'mathverse_777', 'mathverse_786', 'mathvision_1089', 'mathvision_2427',
          'mathvision_3004', 'mathvista_238', 'mathvista_283', 'mathvista_408',
          'mathvista_678', 'mathvista_684', 'mathvista_726', 'mathvista_757',
          'mathvista_781', 'mathvista_819']


def reviewed_case(r, shared):
    base, start, source, q = r['base_id'], r['quote_char_start'], r['associated_source_id'], r['quote'].lower()
    demand = sorted(shared)
    binding = 'NO_SPECIFIC_MISMATCH_IDENTIFIED_IN_QUOTED_VALUE_ASSERTION'
    note = 'Reviewed local assertion against inherited source definition; downstream geometry is not certified.'
    value, valid = r['source_truth_value'], True
    if len(demand) > 1:
        note = 'One joint assertion/list/coordinate uses multiple validated sources; retain compound demand.'
    if base == 'mathverse_638' and start == 713:
        demand, valid = ['B', 'T'], False
        binding = 'INHERITED_QUOTE_TO_NUMERAL_ASSOCIATION_MISMATCH'
        note = 'The numeral12 belongs to BC, not AB. The associated-T draft17vs12 is invalid; retain both AB and BC demands.'
    elif base in {'mathverse_664', 'mathverse_673', 'mathverse_745'} and 'diameter' in q:
        binding, valid = 'RADIUS_AS_DIAMETER_CONFIRMED', False
        note = 'Viewed radius marker, not full diameter; a literal glyph contrast cannot validate the diameter claim.'
    elif base == 'mathverse_771':
        binding, valid = 'RADIUS_AS_FULL_AB_DIAMETER_CONFIRMED', False
        note = 'Image labels AO=7. AB is the full diameter14, not7.'
    elif base == 'mathverse_777' and 'tangent' in q:
        demand, binding, valid = None, 'RADIUS_CHORD_ANGLE_AS_TANGENT_CHORD_ANGLE_CONFIRMED', False
        note = '80 labels angle OAB. No tangent is drawn; intended tangent construction is unresolved.'
    elif base == 'mathverse_786':
        binding, valid = 'LARGE_RADIUS_AS_INTERCENTER_DISTANCE_CONFIRMED', False
        note = '4 labels the large-circle radius from P downward, not PQ. PQ derives2 from the tangent-circle geometry.'
    elif base == 'mathvision_1089' and start in {340, 346, 355}:
        demand, valid = ['A', 'B', 'T'], False
        note = 'Bare numerals belong to the opening multi-angle list; no independent source-role assertion.'
    elif base == 'mathvision_1089' and start == 2847:
        demand, binding, valid = None, 'WRONG_INTERSECTING_LINE_CONFIRMED', False
        note = '100 is the BD/CA crossing, not the BD/CE crossing; needed geometric relation is not localized by numeral alone.'
    elif base == 'mathvision_2427' and source == 'A':
        demand, binding, valid = None, 'VERTICAL_STEP_AS_HORIZONTAL_OR_UNSPECIFIED_TOP_SEGMENT', False
        note = '2 labels the upper-left vertical step. Horizontal assertions are wrong; top-segment-only descriptions remain ambiguous.'
    elif base == 'mathvision_2427' and source == 'T' and start in {4683, 5712}:
        demand, binding, valid = ['A', 'T'], 'PART_HEIGHT_AS_TOTAL_HEIGHT_CONFIRMED', False
        note = 'Total height is8+2; left-side8 alone does not define total extent.'
    elif base == 'mathvision_2986':
        demand, valid = ['C', 'T'], False
        note = '2x+2 is a joint expression with two identical numeral occurrences; coefficient and additive constant need position-specific repair.'
    elif base == 'mathvision_3004' and start in {2225, 2249}:
        value = '4' if source == 'A' else '10'
        binding = 'CORRECT_RADIUS_DERIVED_FROM_PRINTED_DIAMETER'
        note = 'Image diameters8/20 imply radii4/10. Native radius claim is correct; the draft was not an error readout.'
    elif base == 'mathvision_3020' and source == 'D' and start in {605, 1111, 1760}:
        demand = ['B', 'D']
        note = 'Base length derives the difference of endpoint x-coordinates12-0; retain both sources.'
    elif base == 'mathvision_3020' and source == 'T' and start in {1018, 1144, 1780}:
        demand = ['C', 'E', 'T']
        note = 'Height above BC uses A-y and the two baseline y-coordinates; retain compound demand.'
    elif base == 'mathvista_238' and source == 'A':
        demand, binding, valid = ['A', 'B'], 'SUBSEGMENT_RS_AS_WHOLE_RQ_CONFIRMED', False
        note = 'Image RS10 and SQ5 imply RQ15. The whole-baseline claim needs both sources.'
    elif base == 'mathvista_238' and start == 4105:
        demand, binding, valid = None, 'CORRECT_PQ_VALUE_WITH_WRONG_BASE_COORDINATE', False
        note = 'PQ25 is printed, but the same assertion uses Q-x10 instead of RQ15; numeric correctness alone does not certify this coordinate claim.'
    elif base == 'mathvista_283':
        demand, binding, valid = None, 'CHORD_LABEL_AS_ARC_LABEL_CONFIRMED', False
        note = '2x+10 and4x label chords WY and TY, not arcs. The intended arc quantity is not resolved by the printed coefficients.'
    elif base == 'mathvista_408' and start in {1822, 5474}:
        demand, binding, valid = ['A', 'T'], 'HYPOTENUSE_SUBSEGMENT_AS_WHOLE_CONFIRMED', False
        note = 'The full hypotenuse is3+12=15;12 is its right subsegment.'
    elif base == 'mathvista_678' and start == 400:
        demand, binding, valid = ['A', 'T'], 'LEG_AS_HYPOTENUSE_CONFIRMED', False
        note = '16 is the opposite leg; the hypotenuse derives both perpendicular legs16 and10.'
    elif base == 'mathvista_684':
        demand, binding, valid = None, 'ARC_MEASURE_AS_VERTEX_OR_INSCRIBED_ANGLE_CONFIRMED', False
        note = '83 and2x-27 label minor arcs GJ and KH. Native vertex/inscribed-angle associations are wrong or unspecified.'
    elif base == 'mathvista_726':
        demand, binding, valid = None, 'ARC_MEASURE_AS_ANGLE_WITH_UNRESOLVED_ROLE', False
        note = '30 and4x+50 label intercepted arcs;3x is the external angle. Bare angle wording does not identify a valid entity contrast.'
    elif base == 'mathvista_757' and source in {'A', 'B'}:
        demand, binding, valid = None, 'SECANT_INTERNAL_EXTERNAL_OR_TANGENT_ROLE_ERROR', False
        note = 'Lower secant has external8/internal12. There is no tangent; native claims also assign12 to an external segment.'
    elif base == 'mathvista_781' and source == 'A':
        demand, binding, valid = None, 'FK_LENGTH_AS_FH_CONFIRMED', False
        note = '12 labels median FK, not FH. FH requires other geometry not localized by this one numeric ROI.'
    elif base == 'mathvista_781' and source == 'T':
        note = 'CG=DG=9 follows from G being the midpoint; the native CG claim is not an error merely because DG carries the label.'
    elif base == 'mathvista_819':
        demand, binding, valid = None, 'HALF_DIAGONAL_AS_SIDE_CONFIRMED', False
        note = '8 and6 label half-diagonals, not sides WX/YZ/ZW. Side demand is not recoverable from a single numeral association.'
    return demand, binding, note, value, valid


def main():
    path = OUT / 'review/confirmation_quote_readouts.jsonl'
    readouts = list(rows(path))
    shared = defaultdict(set)
    for r in readouts:
        shared[(r['event_id'], r['quote_char_start'], r['quote'])].add(r['associated_source_id'])
    reviews = []
    for r in readouts:
        demand, binding, note, value, valid = reviewed_case(r, shared[(r['event_id'], r['quote_char_start'], r['quote'])])
        reviews.append({'id': r['id'], 'event_id': r['event_id'], 'base_id': r['base_id'], 'split': 'confirmation',
            'quote_char_start': r['quote_char_start'], 'quote': r['quote'],
            'associated_content_source': r['associated_source_id'], 'demand_sources': demand,
            'demand_type': demand_type(demand), 'semantic_role': 'JOINT_SOURCE_ASSERTION' if demand and len(demand)>1 else 'LOCAL_SOURCE_ASSERTION',
            'binding_assessment': binding, 'proposed_binding_contrast': None,
            'local_semantic_value_for_current_readout': value, 'note': note,
            'annotation_method': 'Main-agent review of all exported local quotations; inherited source definitions and selected direct image inspection.',
            'new_visual_acquisition_required': 'UNRESOLVED', 'prior_text_content_status': 'NOT_YET_AUDITED',
            'source_value_readout_matches_current_demand': valid,
            'value_readout_scope': 'Current local quantity where the role is resolved; downstream reasoning is not certified.',
            'readouts_frozen_for_scoring': False})
    write_jsonl(OUT / 'annotation_repair/confirmation_quote_semantic_reviews.jsonl', reviews, freeze=True)
    write_json(OUT / 'audit/confirmation_quote_semantic_review.json', {
        'status': 'LOCAL_QUOTE_REVIEW_COMPLETE_PANEL_NOT_FROZEN',
        'reviewed_at': datetime.now(ZoneInfo('Asia/Seoul')).isoformat(),
        'readout_rows': len(readouts), 'distinct_event_quotations': len(shared),
        'distinct_source_linked_quotations': len({(r['event_id'], r['quote_char_start'], r['quote'], r['associated_source_id']) for r in readouts}),
        'input_sha256': sha(path), 'frozen_rules_sha256': sha(OUT / 'config/annotation_review_rules.json'),
        'viewed_intact_source_images': VIEWED, 'causal_values_used': False,
        'full_primary_panel_validated': False, 'scope': 'Local quotation review only, not every target or intervening span.'}, freeze=True)
    print({'reviewed': len(reviews), 'unique_quotations': len(shared), 'panel_frozen': False})


if __name__ == '__main__':
    main()
