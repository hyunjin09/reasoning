from scripts.stage9a5.decisions import absolute_decision,reserve_gate


def s(zero=.2,t64=.1,t128=.1):
    return {'t0':{'damage':zero},'t64':{'damage':t64},'t128':{'damage':t128,'ci95':[-.02,.2]}}


def test_zero_stop_precedes_finite_search():
    assert absolute_decision(s(zero=.05,t128=0))==('stop_zero',None)


def test_128_gate_controls_the_only_extension():
    assert absolute_decision(s(t128=.05))==('selected',128)
    assert absolute_decision(s())==('run',256)
    v=s();v['t256']={'damage':.12}
    assert absolute_decision(v)==('stop_no_finite',256)


def test_earlier_finite_selection_when_both_preserve():
    assert absolute_decision(s(t64=0,t128=.01))==('selected',64)


def test_reserve_does_not_rescue_small_or_control_failed_effect():
    assert not reserve_gate(s(),{'difference':.04,'ci95':[-.1,.2]},True)
    assert not reserve_gate(s(),{'difference':.1,'ci95':[-.1,.2]},False)
    assert reserve_gate(s(),{'difference':.1,'ci95':[-.1,.2]},True)
