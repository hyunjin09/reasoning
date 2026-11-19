import numpy as np
from visual_reasoning.stage8a.evaluation import family_resamples, semantic_gate


def test_bootstrap_keeps_family_members_together_with_replacement():
    draws=list(family_resamples(["a","a","b"],repetitions=30,seed=3))
    assert len(draws)==30
    for ids in draws:
        assert np.count_nonzero(ids==0)==np.count_nonzero(ids==1)
        assert np.count_nonzero(ids==0)+np.count_nonzero(ids==2)==2


def test_uneven_event_counts_do_not_hide_a_negative_independent_family():
    events=[dict(event_id=f"a{i}",family_id="a",semantic_minus_sham=10.) for i in range(10)]
    events.append(dict(event_id="b",family_id="b",semantic_minus_sham=-2.))
    result=semantic_gate(events,repetitions=1000)
    assert result["positive_event_fraction"]==10/11
    assert result["family_median_effect"]==4.
    assert result["family_ci95"][0]==-2.
    assert not result["pass"]
    single=semantic_gate(events[:1],repetitions=10)
    assert single["family_ci95"] is None and single["pass"] is None
    assert semantic_gate([])["pass"] is None
