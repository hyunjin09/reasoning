"""Reject concrete false associations found during semantic review.

Passing these checks still requires source-role review and does not certify
the surrounding proposition or any interval between two assertions.
"""
import re


def local_assertion_checks(text, claim, source):
    reasons = []
    prefix = text[:claim['role_start']]
    tail = text[claim['value_end']:]
    entity = source['entity'].lower()
    preceding = prefix.rstrip()
    if preceding and preceding[-1] in '+-−*/×÷^' and preceding not in {'-', '−'}:
        reasons.append('SOURCE_IS_OPERAND_NOT_LEFT_HAND_QUANTITY')
    if re.search(r"\b(?:let['’]s say|for example|in the .*?example|suppos\w*|hypothetic\w*|imagin\w*)\b", text, re.I):
        reasons.append('HYPOTHETICAL_EXAMPLE')
    if re.search(r'\b(?:square|cube|difference|sum|ratio|product|area|angle)\b[^.;:]*$', prefix, re.I):
        reasons.append('EMBEDDED_ROLE_OR_DERIVED_SUBGOAL')
    if re.search(r'\b(?:vector|slope|more than|less than)\b[^.;]*$', prefix, re.I):
        reasons.append('DIFFERENT_QUANTITY_OR_COMPARISON_SCOPE')
    connector = text[claim['role_end']:claim['value_start']]
    if '(' in connector and re.match(r'^\s*,', tail):
        reasons.append('COORDINATE_REQUIRES_SET_AND_POSITION_REVIEW')
    if re.match(r'^\s*\(\s*[-+\d]', tail):
        reasons.append('FUNCTION_OR_IMPLICIT_PRODUCT_REQUIRES_REVIEW')
    if tail and tail[0].isalpha() and not re.match(r'^(?:cm|mm|km|ft|m)\b', tail):
        reasons.append('NUMERAL_IS_COEFFICIENT_NOT_COMPLETE_LITERAL')
    after_unit = re.sub(r'^\s*(?:cm|mm|km|ft|units?|meters?|metres?|degrees?|m)?\s*[²³]?', '', tail, flags=re.I)
    if re.match(r'^[+*/×÷^=−-]', after_unit):
        reasons.append('LITERAL_IS_PART_OF_ARITHMETIC_EXPRESSION')
    if ('angle' not in entity and 'arc' not in entity
            and re.match(r'^\s*(?:°|degrees?\b)', tail, re.I)):
        reasons.append('ANGLE_VALUE_ATTACHED_TO_NONANGLE_SOURCE')
    return reasons
