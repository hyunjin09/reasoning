"""Conservative checks for local assertion proposals; semantic review is separate."""
import re


def claim_checks(text, claim, source):
    reasons = []
    role = text[claim['role_start']:claim['role_end']].lower()
    entity = source['entity'].lower()
    if not source['current_image_source_identity_mapped']:
        reasons.append('SOURCE_IDENTITY_NOT_MAPPED_IN_CURRENT_IMAGE')
    if re.search(r'\b(?:if|maybe|might|could|probably|perhaps|suppose|assuming|assume|not|instead|rather|versus)\b', text, re.I):
        reasons.append('HYPOTHETICAL_OR_NEGATED_CONTEXT')
    if re.fullmatch(r'[\d\s]+', role):
        reasons.append('NUMERIC_ALIAS_REQUIRES_CELL_REVIEW')
    if (('radius' in entity and 'diameter' in role)
            or ('diameter' in entity and 'radius' in role)
            or ('vertical height' in entity and 'slant' in role)
            or ('slant height' in entity and 'vertical' in role)):
        reasons.append('ROLE_CONVERSION_REQUIRES_REVIEW')
    tail = text[claim['value_end']:].lstrip()
    if re.match(r'^(?:[+*/^²³]|-(?=\s*\d))', tail):
        reasons.append('ARITHMETIC_OPERAND_REQUIRES_REVIEW')
    # Truth equality is deliberately not a filter: wrong but unambiguous local
    # assertions must remain available for value and error-oriented readouts.
    return reasons
