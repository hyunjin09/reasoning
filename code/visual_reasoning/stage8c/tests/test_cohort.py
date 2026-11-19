import random
from visual_reasoning.stage8c.cohort import family_groups, proportional_sample


def test_conservative_transitive_family_and_alias():
    rows = [dict(item_id=str(i), question='') for i in range(4)]
    sig = {str(i): dict(exact=str(i), normalized=str(i), phash=(1 << (15*i))-1, aspect=1)
           for i in range(4)}
    sig['1']['exact'] = sig['0']['exact']
    fam, groups, _ = family_groups(rows, sig, [('1', '2')])
    assert fam['0'] == fam['1'] == fam['2'] != fam['3']


def test_proportional_selection_independent_and_reproducible():
    rows = [dict(item_id=str(i), family_id=str(i), subject='a' if i < 60 else 'b',
                 level=1, answer_format='choice') for i in range(100)]
    selected = proportional_sample(rows, 20, random.Random(9))
    assert selected == proportional_sample(rows, 20, random.Random(9))
    assert sum(r['subject'] == 'a' for r in selected) == 12
    assert len({r['item_id'] for r in selected}) == 20
