import pytest
from visual_reasoning.stage8a.transport import weak_transport, fit_cheap_gates


def event(js, ce):
    return {"first_query_js": {"visual_off": js}, "ce_effect": {"visual_off": ce}}


def test_query_weak_but_span_strong_is_not_weak():
    rule = {"tau_js": .01, "tau_abs_ce": .02}
    assert weak_transport(event(.001, .001), rule)
    assert not weak_transport(event(.001, .5), rule)
    assert not weak_transport(event(.001, -.5), rule)
    assert not weak_transport(event(.01, .001), rule)
    assert not weak_transport(event(.001, .02), rule)
    with pytest.raises(ValueError):
        weak_transport(event(float("nan"), .001), rule)


def test_confirmation_cannot_fit_transport_gate():
    with pytest.raises(ValueError, match="discovery-only"):
        fit_cheap_gates([{"split": "confirmation"}], {})
