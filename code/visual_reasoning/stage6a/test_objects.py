from visual_reasoning.stage6a.objects import extract_object_claims

ALIASES={'dog':['dog','dogs'],'cat':['cat','cats'],'hot dog':['hot dog','hot dogs'],
         'person':['person','people','man','men'],'orange':['orange','oranges']}


def test_multiword_object_does_not_create_nested_dog_claim():
    claims=extract_object_claims('A man eats a hot dog.',ALIASES)
    assert [r['category'] for r in claims]==['person','hot dog']


def test_negation_and_hypothesis_are_not_positive_object_assertions():
    claims=extract_object_claims('There is no dog, but a cat is visible. Perhaps a man is nearby.',ALIASES)
    assert [(r['category'],r['assertion']) for r in claims]==[('dog','negated'),('cat','asserted'),('person','uncertain')]


def test_color_use_is_not_fruit_hallucination():
    claims=extract_object_claims('A man in an orange shirt holds oranges.',ALIASES)
    assert [r['category'] for r in claims]==['person','orange']


def test_exact_character_offsets_and_not_only():
    text='Not only dogs but also cats are visible.'
    claims=extract_object_claims(text,ALIASES)
    assert all(r['assertion']=='asserted' for r in claims)
    assert all(text[r['char_start']:r['char_end']]==r['surface'] for r in claims)
