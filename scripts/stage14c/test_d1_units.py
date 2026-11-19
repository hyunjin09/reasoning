import pytest
from scripts.stage14c.common import fingerprint
from scripts.stage14c.d1_review_v2 import validate_units,unit_maps


def test_every_frozen_unit_matches_its_preserved_count():
    maps=unit_maps();assert len(maps)==300
    for r in maps.values():
        for a in r['atoms']:
            assert len(set(a['subfact_keys']))==a['subfact_count']


def test_unlisted_recovered_fact_cannot_enter_target_recall():
    target={'atoms':[{'subfact_keys':['left endpoint','right endpoint']}]}
    record={'unit_map_sha256':fingerprint(target),'review':{'status':'SCORED','atoms':[{'recovered_units':['left endpoint']}]}}
    validate_units(target,record)
    record['review']['atoms'][0]['recovered_units']=['derived length']
    with pytest.raises(AssertionError):validate_units(target,record)
