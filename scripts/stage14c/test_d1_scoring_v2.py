import pytest
from scripts.stage14c.d1_scoring_v2 import validate_review,metrics


def test_equal_values_in_distinct_cells_do_not_collapse():
    target={'atoms':[{'text':'A=2; B=2','atom_type':'structured_layout','subfact_count':2}]}
    review={'status':'SCORED','reason':'Both source bindings correct.',
            'atoms':[{'exact':True,'recovered_units':['A=2','B=2'],'evidence_quotes':['2','2']}],
            'claims':[{'text':'2','binding':'A','classification':'required','target_atom':0,'target_unit':0},
                      {'text':'2','binding':'B','classification':'required','target_atom':0,'target_unit':1}]}
    validate_review(target,review)
    assert metrics(target,review)['targeted_precision']==1
    review['claims'][1]['binding']='A'
    with pytest.raises(AssertionError):validate_review(target,review)
