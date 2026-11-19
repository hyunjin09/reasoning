"""Source-only, lossless format proposals; no model responses or gold inputs."""
import hashlib
import json
import re

POSITIONS = ('left', 'middle', 'right')
ORIGINAL_PREFIX = ('- The blue and red paths each join left, middle, and right vertices '
                   'with straight segments, sharing those three horizontal positions. ')
CONTRACT_SUFFIX = ' Answer with a number in curly brackets, e.g., {5}.'
CONTRACT_SUFFIXES = (CONTRACT_SUFFIX, ' Put your answer in curly brackets, e.g., {2}.')
EXPANSION_SALT = 'stage14cv-v1-20261009|C-expansion'
ORDER_SALT = 'stage14cv-v1-20261009|matched-order'


def ledger_for(orders):
    if len(orders) != 3 or any(x not in {'above', 'below'} for x in orders):
        raise ValueError('Unsupported source relation')
    return dict(paths=['blue', 'red'], ordered_vertices=list(POSITIONS),
                segments_for_each_path=[['left', 'middle'], ['middle', 'right']],
                segment_type='straight', shared_horizontal_vertex_positions=True,
                blue_relative_to_red=dict(zip(POSITIONS, orders)))


def parse_original(text):
    if not text.startswith(ORIGINAL_PREFIX):
        raise ValueError('Unknown topology or evidence prefix')
    tail = text[len(ORIGINAL_PREFIX):]
    same = re.fullmatch(r'Blue is (above|below) red at the left, middle, and right vertices\.', tail)
    if same:
        return ledger_for([same[1]] * 3)
    expanded = re.fullmatch(
        r'At the left vertex blue is (above|below) red; '
        r'At the middle vertex blue is (above|below) red; '
        r'At the right vertex blue is (above|below) red\.', tail)
    early = re.fullmatch(
        r'Blue is (above|below) red at the left vertex, '
        r'(above|below) red at the middle vertex, and '
        r'(above|below) red at the right vertex\.', tail)
    matched = expanded or early
    if not matched:
        raise ValueError('Unknown or extra source content')
    return ledger_for(matched.groups())


def validate_ledger(ledger):
    try:
        relations = ledger['blue_relative_to_red']
        expected = ledger_for([relations[p] for p in POSITIONS])
    except (KeyError, TypeError) as exc:
        raise ValueError('Incomplete semantic ledger') from exc
    if ledger != expected:
        raise ValueError('Extra, missing, or altered source content')
    return ledger


def render_r1(ledger):
    return json.dumps(validate_ledger(ledger), ensure_ascii=False, indent=2)


def parse_r1(text):
    def unique_fields(pairs):
        if len({k for k, _ in pairs}) != len(pairs):
            raise ValueError('Duplicate field in typed representation')
        return dict(pairs)
    return validate_ledger(json.loads(text, object_pairs_hook=unique_fields))


def render_r2(ledger):
    validate_ledger(ledger)
    sentences = [f'The {color} path connects its left vertex to its middle vertex with a straight segment, '
                 f'and its middle vertex to its right vertex with a straight segment.' for color in ('blue', 'red')]
    sentences.append('The corresponding left, middle, and right vertices of the blue and red paths share horizontal positions.')
    sentences.extend(f'At the {p} vertex, the blue path is {ledger["blue_relative_to_red"][p]} the red path.' for p in POSITIONS)
    return '\n'.join(sentences)


def parse_r2(text):
    tail = r'At the (left|middle|right) vertex, the blue path is (above|below) the red path\.'
    relations = re.findall(tail, text)
    if [p for p, _ in relations] != list(POSITIONS):
        raise ValueError('Missing or reordered source bindings')
    ledger = ledger_for([v for _, v in relations])
    if text != render_r2(ledger):
        raise ValueError('Unexpected content in entity-explicit representation')
    return ledger


def remove_conflict(question):
    matches = [s for s in CONTRACT_SUFFIXES if question.endswith(s)]
    if len(matches) != 1 or sum(question.count(s) for s in CONTRACT_SUFFIXES) != 1:
        raise ValueError('Historical instruction identity mismatch')
    return question[:-len(matches[0])]


def rank(family_id, salt):
    return hashlib.sha256(f'{salt}|{family_id}'.encode()).hexdigest(), family_id


def select_expansion(all_ids, old_ids):
    full, old = set(all_ids), set(old_ids)
    if len(full) != 300 or len(all_ids) != 300 or len(old) != 100 or len(old_ids) != 100 or not old <= full:
        raise ValueError('Original cohort or D1 identity mismatch')
    return sorted(full - old, key=lambda f: rank(f, EXPANSION_SALT))[:100]
