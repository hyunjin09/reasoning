import pytest
from scripts.stage14c.d1_analysis import summarize


def row(total,recovered):
    return dict(status='SCORED',full_E_star_recovery=total==recovered,exact_atom_recall=float(total==recovered),
        exact_atoms=int(total==recovered),atoms=1,subfact_recall=recovered/total,
        subfacts=total,recovered_subfacts=recovered,structured_subfacts=total,
        recovered_structured_subfacts=recovered,targeted_precision=1.,
        required_visual_facts=recovered,asserted_visual_facts=recovered,claim_classes={'required':recovered})


def test_macro_micro_and_missing_denominators_are_distinct():
    result=summarize([row(1,1),row(8,4),{'status':'UNRESOLVED'}])
    assert result['scored_families']==2 and result['n']==3
    assert result['subfact_recall_macro']==.75
    assert result['subfact_recall_micro']==pytest.approx(5/9)
    assert result['full_recovery_bounds']==[1/3,2/3]


def test_no_scored_probes_remains_undefined():
    result=summarize([{'status':'TECHNICAL_MISSING'}])
    assert result['targeted_precision_micro'] is None
    assert result['subfact_recall_macro'] is None
    assert result['full_recovery_bounds']==[0,1]
