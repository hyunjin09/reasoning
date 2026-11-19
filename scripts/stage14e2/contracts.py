"""Prospectively frozen helper boundaries and committed readout extraction."""
import json
import re


def helper_boundary(prompt, mode):
    if mode not in ['compact', 'thinking'] or not prompt.endswith('<think>\n'):
        raise ValueError('UNEXPECTED_HELPER_BOUNDARY')
    return prompt + '</think>\n\n' if mode == 'compact' else prompt


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate JSON key')
        value[key] = item
    return value


def parse_readout(raw, mode, cap_hit):
    if mode not in ['compact', 'thinking']:
        raise ValueError('Unknown readout mode')
    if cap_hit:
        return dict(status='CAPPED', parsed=None)
    if mode == 'thinking' and '</think>' not in raw:
        return dict(status='NO_COMMITTED_FINAL', parsed=None)
    body = raw.rsplit('</think>', 1)[-1].strip() if mode == 'thinking' else raw.strip()
    fence = re.fullmatch(r'```(?:json)?\s*([\s\S]*?)\s*```', body)
    if fence:
        body = fence.group(1)
    try:
        value = json.loads(body, object_pairs_hook=unique_object)
    except (ValueError, TypeError):
        return dict(status='INVALID_JSON', parsed=None, final_body=body)
    fields = {'target', 'read_value', 'supporting_source', 'uncertainty'}
    if (not isinstance(value, dict) or set(value) != fields or
            not all(isinstance(v, str) for v in value.values()) or
            value['uncertainty'] not in ['certain', 'uncertain', 'unresolvable']):
        return dict(status='INVALID_SCHEMA', parsed=None, final_body=body)
    return dict(status='VALID', parsed=value, final_body=body)
