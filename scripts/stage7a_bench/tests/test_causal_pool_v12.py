import pytest
from scripts.stage7a_bench.causal_pool_v12 import partition_entries


def test_partitions_cover_once_and_serialize_large_cache_events():
    entries=[dict(id=str(i),native_input={'prompt_token_count':n},event={'history_before_ed_token_ids':[]}) for i,n in enumerate([12000,50000,90000,198000,40000,198001])]
    a,b=partition_entries(entries,0),partition_entries(entries,1)
    assert sorted(x['id'] for x in a+b)==sorted(x['id'] for x in entries)
    assert not {x['id'] for x in a}&{x['id'] for x in b}
    assert [x['id'] for x in a[-2:]]==['3','5']
    assert all(x['native_input']['prompt_token_count']<100000 for x in b)
    assert len(b)>0
    assert partition_entries(entries,0)==a


def test_partition_rejects_unknown_worker():
    with pytest.raises(ValueError):partition_entries([],2)
