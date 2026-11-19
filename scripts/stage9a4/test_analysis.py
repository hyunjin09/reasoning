import pytest
from scripts.stage9a4.analyze import summarize


def fixture():
    return [dict(image_id=str(i),policy=p,correct=c,raw_correct=c)
            for i in range(4) for q in range(2)
            for p,c in [('full',i<3),('t0',i<2),('t64',i<3)]]


def test_paired_identity_has_exact_zero_interval():
    r=summarize(fixture())
    assert r['n_images']==4
    assert r['surface']['t0']['damage']==.25
    assert r['surface']['t64']['ci95']==[0.,0.]


def test_incomplete_image_pairs_fail_closed():
    with pytest.raises(AssertionError):summarize(fixture()[:-1])


def test_bootstrap_is_deterministic_and_images_are_equal():
    rows=fixture();a=summarize(rows);b=summarize(list(reversed(rows)))
    assert a==b and a['surface']['t0']['paired_images_harmed']==1
