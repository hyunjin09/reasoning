from scripts.stage10a.anchors import locate, choose_cohort


def test_anchor_is_before_fact_and_after_downstream_use():
    text='Look. There are two circles. Thus the count is 2. Done.'
    d=locate(text,'There are two circles.','Thus the count is 2.')
    assert text[:d['pre_char']]=='Look. '
    assert text[d['pre_char']:d['emit_char']]=='There are two circles.'
    assert text[:d['post_char']].endswith('Thus the count is 2.')


def test_repeated_fact_uses_first_occurrence_and_later_step():
    d=locate('Two. Other. Two. End.','Two.','Other.')
    assert d['pre_char']==0 and d['emit_char']==4 and d['post_char']==11


def test_balanced_independent_cohort_is_order_invariant():
    rows=[dict(image_id=f'image{i:03d}',attribute='color' if i%2==0 else 'shape') for i in range(32)]
    a,b=choose_cohort(rows);c,d=choose_cohort(list(reversed(rows)))
    assert [r['image_id'] for r in a]==[r['image_id'] for r in c]
    assert len(a)==24 and len(b)==8
    assert sum(r['attribute']=='color' for r in a)==12
    assert not {r['image_id'] for r in a}&{r['image_id'] for r in b}


def test_duplicate_independent_units_rejected():
    import pytest
    rows=[dict(image_id=f'image{i:03d}',attribute='color' if i%2==0 else 'shape') for i in range(32)]
    with pytest.raises(AssertionError):choose_cohort(rows+[rows[0]])
