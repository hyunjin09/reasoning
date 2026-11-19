from visual_reasoning.stage6a.matching import match_controls


def row(key,split,x):return dict(base_id=key,split=split,x=x)


def test_controls_unique_and_folds_never_cross():
    cases=[row('a','discovery',1),row('b','discovery',2),row('c','confirmation',1)]
    controls=[row('d','discovery',1),row('e','discovery',3),row('f','confirmation',9)]
    pairs,unmatched=match_controls(cases,controls,lambda a,b:abs(a['x']-b['x']))
    assert len(pairs)==3 and not unmatched
    assert len({p['control_base_id'] for p in pairs})==3
    assert next(p for p in pairs if p['case_base_id']=='c')['control_base_id']=='f'


def test_control_shortfall_is_explicit_not_filled_across_splits():
    pairs,unmatched=match_controls([row('a','discovery',1)],[row('b','confirmation',1)],lambda a,b:0)
    assert pairs==[] and unmatched==['a']


def test_input_order_does_not_change_matching():
    cases=[row('a','discovery',1),row('b','discovery',2)]
    controls=[row('c','discovery',0),row('d','discovery',3)]
    cost=lambda a,b:abs(a['x']-b['x'])
    assert match_controls(cases,controls,cost)==match_controls(cases[::-1],controls[::-1],cost)
