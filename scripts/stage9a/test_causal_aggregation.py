import pytest

from scripts.stage9a.finish_causal import validate_result


def result():
    return dict(completed=True,capture_noop_exact=True,sham_noop_exact=True,
                selected_routing_fixed=True,effects={'sham':0.},first_query_js={'sham':-4.7e-17})


def test_exact_logits_allow_signed_fp64_js_roundoff():
    validate_result(result())


@pytest.mark.parametrize('defect',['logits','score','divergence'])
def test_roundoff_tolerance_cannot_hide_real_sham_failures(defect):
    row=result()
    if defect=='logits':row['sham_noop_exact']=False
    if defect=='score':row['effects']['sham']=1e-15
    if defect=='divergence':row['first_query_js']['sham']=1e-8
    with pytest.raises(AssertionError):validate_result(row)
