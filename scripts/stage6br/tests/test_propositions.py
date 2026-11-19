from scripts.stage6br.propositions import split_propositions, binding_proposals


def test_decimal_and_coordinates_do_not_create_spurious_subgoals():
    text = 'The point is (1, 2), and V = 3.14*r*r*h. Then compute the volume.'
    parts = split_propositions(text, {'A': r'\bradius\b'})
    assert [p['text'] for p in parts] == ['The point is (1, 2), and V = 3.14*r*r*h.', 'Then compute the volume.']
    assert all(text[p['start']:p['end']] == p['text'] for p in parts)


def test_independent_value_assertions_can_be_reviewed_separately():
    text = 'Wednesday is $2, Thursday is $7.'
    patterns = {'A': r'\bWednesday\b', 'T': r'\bThursday\b'}
    parts = split_propositions(text, patterns)
    assert [p['text'] for p in parts] == ['Wednesday is $2,', 'Thursday is $7.']
    assert [binding_proposals(p['text'], patterns)[0]['source_id'] for p in parts] == ['A', 'T']


def test_computation_is_not_split_into_singleton_source_claims():
    text = 'The area uses radius and height: V = 3.14*6*6*8.'
    patterns = {'A': r'\bradius\b', 'T': r'\bheight\b'}
    assert len(split_propositions(text, patterns)) == 1


def test_negated_value_is_not_an_affirmative_binding_proposal():
    patterns = {'A': r'\bradius\b'}
    assert binding_proposals('The radius is not 6.', patterns) == []
    assert binding_proposals('The radius is 6.', patterns)[0]['value_text'] == '6'
