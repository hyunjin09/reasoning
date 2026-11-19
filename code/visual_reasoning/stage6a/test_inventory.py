from pathlib import Path
from scripts.stage6a.inventory import select_shards


def test_test_split_does_not_include_testmini():
    paths=[Path('math_vision-test.arrow'),Path('math_vision-testmini.arrow')]
    assert select_shards(paths,'test',{})==paths[:1]


def test_multiple_complete_encodings_choose_declared_shard_count():
    paths=[Path(f'doc_vqa-validation-{i:05}-of-{n:05}.arrow') for n in (5,7) for i in range(n)]
    result=select_shards(paths,'validation',{'shard_lengths':[1]*7})
    assert len(result)==7
    assert all('of-00007' in str(p) for p in result)


def test_partial_shards_rejected():
    import pytest
    with pytest.raises(ValueError,match='incomplete'):
        select_shards([Path('x-test-00000-of-00002.arrow')],'test',{'shard_lengths':[1,1]})
