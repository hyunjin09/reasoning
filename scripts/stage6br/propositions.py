"""Suggest exact local proposition boundaries, never certify semantic labels."""
import re


def split_propositions(text, patterns):
    boundaries = {0, len(text)}
    for match in re.finditer(r'(?<=[.!?;])\s+(?=\S)|\n+', text):
        boundaries.add(match.end())
    if patterns:
        names = '|'.join('(?:' + value + ')' for value in patterns.values())
        independent = re.compile(r'(?:,\s*|\s+and\s+)(?=(?:the\s+)?(?:' + names + r')\s*(?:is\b|was\b|=|:))', re.I)
        for match in independent.finditer(text):
            left = max(x for x in boundaries if x <= match.start())
            right = min(x for x in boundaries if x >= match.end())
            following = binding_proposals(text[match.end():right], patterns)
            if (binding_proposals(text[left:match.start()], patterns)
                    and any(p['role_start'] <= 4 for p in following)):
                boundaries.add(match.end())
    ordered = sorted(boundaries)
    result = []
    for left, right in zip(ordered, ordered[1:]):
        raw = text[left:right]
        start = left + len(raw) - len(raw.lstrip())
        end = right - len(raw) + len(raw.rstrip())
        if start < end:
            result.append({'start': start, 'end': end, 'text': text[start:end]})
    return result


def binding_proposals(text, patterns):
    result = []
    for source, alias in patterns.items():
        expression = (r'(?P<role>' + alias + r')\s*(?:(?:is|was|equals|measures)\b(?:\s+given\s+as)?|=|:)'
                      r'[\s$\\()]*?(?P<value>-?\d+(?:\.\d+)?)(?!\d|\.\d)')
        for match in re.finditer(expression, text, re.I):
            result.append({'source_id': source, 'role_start': match.start('role'),
                           'role_end': match.end('role'), 'value_start': match.start('value'),
                           'value_end': match.end('value'), 'value_text': match.group('value'),
                           'claim_text': text[match.start('role'):match.end('value')],
                           'status': 'PROPOSAL_REQUIRES_SEMANTIC_REVIEW'})
    return sorted(result, key=lambda r: (r['role_start'], r['source_id']))
