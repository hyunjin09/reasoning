import numpy as np
from scripts.stage6b.event_results import distribution_similarity


def test_full_distribution_js_is_symmetric_and_zero_for_same_logits():
    a=np.linspace(-10.,0.,100);b=a[::-1].copy()
    assert abs(distribution_similarity(a.copy(),a.copy())['js_divergence'])<1e-12
    left=distribution_similarity(a.copy(),b.copy())
    right=distribution_similarity(b.copy(),a.copy())
    assert 0<left['js_divergence']<np.log(2)
    assert abs(left['js_divergence']-right['js_divergence'])<1e-12
    assert left['top50_overlap']==0
