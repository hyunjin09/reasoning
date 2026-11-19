from scripts.stage14a.review_v4 import accepted_families,advance
import pytest

def test_qc_rejection_reopens_exactly_one_slot_preserving_alias_count():
 rows=[dict(item_id='1',family_id='a',decision='ACCEPT'),dict(item_id='2',family_id='b',decision='ACCEPT'),dict(item_id='3',family_id='c',decision='ACCEPT')]
 can={'a':'a','b':'b','c':'b'}
 qc=[dict(item_id='1',eligibility='FAIL',resolved_for_final_seal=True)]
 assert accepted_families(rows,can)=={'a','b'}
 seen=accepted_families(rows,can,qc)
 assert seen=={'b'}
 assert advance(seen,'b','ACCEPT',2)=={'b'}
 seen=advance(seen,'d','ACCEPT',2)
 with pytest.raises(AssertionError):advance(seen,'e','EXCLUDE',2)
