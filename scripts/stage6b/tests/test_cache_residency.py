import torch
from transformers.cache_utils import DynamicCache
from visual_reasoning.stage3c9.streaming import StreamingPrefixState
from visual_reasoning.stage6b.cache_residency import clone_to_device, move_state


def test_inactive_cache_copy_preserves_values_metadata_and_isolation():
    cache = DynamicCache()
    values = torch.arange(48, dtype=torch.bfloat16).reshape(1, 2, 6, 4)
    cache.update(values, -values, 0)
    original = StreamingPrefixState(cache, torch.tensor([[7]]), 2, 4, values.flatten())
    copied = clone_to_device(original, 'cpu')
    assert copied.cache.layers[0].keys.data_ptr() != values.data_ptr()
    assert torch.equal(copied.cache.layers[0].keys, values)
    assert copied.cache.layers[0].keys.dtype == torch.bfloat16
    assert copied.prompt_length == 2 and copied.generated_length == 4
    assert torch.equal(copied.rope_deltas, original.rope_deltas)
    copied.cache.layers[0].keys.zero_()
    assert torch.equal(original.cache.layers[0].keys, values)
    assert values.sum() > 0
    assert move_state(copied, 'cpu') is copied
