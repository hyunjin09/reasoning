import pytest
from visual_reasoning.stage6b.dense_partition import endpoint_partition


def test_checkpoint_reuse_preserves_partial_chunk_and_eight_single_queries():
    assert endpoint_partition(8)==(0,[],[(i,i+1) for i in range(8)])
    checkpoint,partial,queries=endpoint_partition(4107)
    assert checkpoint==4096 and partial==[(4096,4099)]
    assert queries==[(i,i+1) for i in range(4099,4107)]
    assert endpoint_partition(4104)[1]==[]


def test_early_endpoint_does_not_change_canonical_window():
    with pytest.raises(ValueError):endpoint_partition(7)
