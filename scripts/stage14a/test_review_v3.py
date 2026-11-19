import pytest
from scripts.stage14a.review_v3 import canonical_map, accepted_families, advance


def test_transitive_source_aliases_and_excluded_variants():
    aliases = [{'frozen_family_ids':['b','c']}, {'frozen_family_ids':['a','b']}]
    canonical = canonical_map(['a','b','c','d'], aliases)
    assert canonical == {'a':'a','b':'a','c':'a','d':'d'}
    assert canonical_map(['a','b','c','d'], aliases[::-1]) == canonical
    rows = [{'family_id':'a','decision':'EXCLUDE'}, {'family_id':'b','decision':'ACCEPT'},
            {'family_id':'c','decision':'ACCEPT'}]
    assert accepted_families(rows, canonical) == {'a'}


def test_duplicates_do_not_consume_target_and_stop_is_immediate():
    seen = advance(set(), 'a', 'ACCEPT', target=2)
    assert advance(seen, 'a', 'ACCEPT', target=2) == {'a'}
    assert advance(seen, 'b', 'EXCLUDE', target=2) == {'a'}
    seen = advance(seen, 'b', 'ACCEPT', target=2)
    with pytest.raises(AssertionError):
        advance(seen, 'c', 'EXCLUDE', target=2)
