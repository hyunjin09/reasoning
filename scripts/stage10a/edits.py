"""Frozen count edits; no outcome-dependent choice or second fact search."""
import re

WORDS = {1:'one', 2:'two', 3:'three', 4:'four', 5:'five'}
SINGLETONS = {
    'So only one red object.': ('So two red objects.', 'So exactly one red object.'),
    'Wait, the red objects—only the red circle.': (
        'Wait, the red objects—only the two red circles.',
        'Wait, the red objects—only the single red circle.'),
    'So only one green object, which is the green circle.': (
        'So two green objects, which are the green circles.',
        'So exactly one green object, which is the green circle.'),
    'So the only blue one is the blue circle.': (
        'So the only two blue ones are the blue circles.',
        'So the single blue one is the blue circle.'),
    'So only the blue square is a square.': (
        'So only the two blue squares are squares.',
        'So the single blue square is the only square.'),
    'The green triangle is the only one.': (
        'The two green triangles are the only ones.',
        'The single green triangle is the only one.'),
    'So only the blue one is a star.': (
        'So only the two blue ones are stars.',
        'So the single blue one is the only star.'),
    'So only the yellow square is a square.': (
        'So only the two yellow squares are squares.',
        'So the single yellow square is the only square.'),
}


def variants(fact, count):
    if fact in SINGLETONS:
        assert count == 1
        return (*SINGLETONS[fact], 'Singleton count edit with required singular/plural agreement; same color/shape/source group. Sham retains the singleton proposition.')
    matches = list(re.finditer(r'\b(?:'+str(count)+'|'+WORDS[count]+r')\b', fact))
    assert len(matches) == 1, (fact, count)
    m = matches[0]; next_count = count % 5 + 1
    cf = str(next_count) if m[0].isdigit() else WORDS[next_count]
    sham = WORDS[count] if m[0].isdigit() else str(count)
    return (fact[:m.start()]+cf+fact[m.end():], fact[:m.start()]+sham+fact[m.end():],
            'Only the aggregate count changes; any earlier enumeration/arithmetic operands remain unchanged. Sham changes word/digit spelling only.')


def replace_fact(prefix, start, end, replacement):
    assert 0 <= start < end <= len(prefix)
    return prefix[:start] + replacement + prefix[end:]


def gate_b(cf_original, cf_sham):
    return all(r['point'] >= .25-1e-12 and r['ci95'][0] > 0 for r in (cf_original,cf_sham))
