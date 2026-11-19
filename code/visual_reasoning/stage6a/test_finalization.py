import pytest

from scripts.stage6a.finalize_when_ready import validate_shard


def test_terminal_caps_do_not_block_finalization_or_count_as_eos():
    rows = [dict(event_id='first', manifest_sha256='frozen', complete=True),
            dict(event_id='second', manifest_sha256='frozen', complete=False, truncated=True)]
    receipt = dict(rank=2, complete=True, results=rows)
    assert validate_shard(receipt, 2, ['first', 'second'], 'frozen') == rows


@pytest.mark.parametrize('actual', [[], ['first'], ['first', 'first'], ['second', 'first'], ['first', 'foreign']])
def test_missing_duplicate_foreign_or_reordered_records_cannot_release(actual):
    receipt = dict(rank=0, complete=True,
                   results=[dict(event_id=key, manifest_sha256='frozen') for key in actual])
    with pytest.raises(AssertionError, match='event order'):
        validate_shard(receipt, 0, ['first', 'second'], 'frozen')


def test_wrong_manifest_rank_and_unfinished_receipt_cannot_release():
    receipt = dict(rank=1, complete=True,
                   results=[dict(event_id='first', manifest_sha256='old')])
    with pytest.raises(AssertionError, match='manifest'):
        validate_shard(receipt, 1, ['first'], 'frozen')
    with pytest.raises(AssertionError, match='rank'):
        validate_shard(receipt, 0, ['first'], 'old')
    with pytest.raises(AssertionError, match='terminal'):
        validate_shard({**receipt, 'complete': False}, 1, ['first'], 'old')
