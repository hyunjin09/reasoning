import pytest
from scripts.stage14c.d1_scoring import metrics,validate_review


def example():
    target={'atoms':[{'text':'A=2; B=3','atom_type':'structured_layout','subfact_count':2}]}
    review={'status':'SCORED','reason':'One binding recovered.',
            'atoms':[{'exact':False,'recovered_units':['A=2'],'evidence_quotes':['A is 2']}],
            'claims':[{'text':'A is 2','classification':'required','target_atom':0,'target_unit':0},
                      {'text':'B is 8','classification':'contradictory'}]}
    return target,review


def test_partial_recovery_and_false_claim_remain_distinct():
    target,review=example(); validate_review(target,review)
    result=metrics(target,review)
    assert result['subfact_recall']==.5 and result['targeted_precision']==.5
    assert result['exact_atom_recall']==0 and result['full_E_star_recovery'] is False


def test_no_facts_has_zero_recall_undefined_precision():
    target,review=example();review['claims']=[]
    review['atoms'][0].update(recovered_units=[],evidence_quotes=[])
    validate_review(target,review);result=metrics(target,review)
    assert result['subfact_recall']==0 and result['targeted_precision'] is None


def test_unresolved_is_not_zero_recovery():
    target,_=example();review={'status':'UNRESOLVED','reason':'No native thinking close.'}
    validate_review(target,review)
    assert metrics(target,review)=={'status':'UNRESOLVED'}


def test_duplicate_recovery_cannot_inflate_precision():
    target,review=example();review['claims'].append(dict(review['claims'][0]))
    with pytest.raises(AssertionError):validate_review(target,review)


def test_exact_requires_every_source_unit():
    target,review=example();review['atoms'][0]['exact']=True
    with pytest.raises(AssertionError):validate_review(target,review)
