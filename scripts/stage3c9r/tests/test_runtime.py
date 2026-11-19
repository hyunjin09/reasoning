from types import SimpleNamespace

import torch

from visual_reasoning.stage3c9.streaming import StreamingPrefixState
from visual_reasoning.stage3c9r.runtime import copy_state_to, measured_patch


class Cache:
    def __init__(self, offset):
        key = torch.arange(80, dtype=torch.float32).reshape(1, 2, 10, 4) + offset
        self.layers = [SimpleNamespace(keys=key, values=key + 100)]


def state(offset):
    return StreamingPrefixState(Cache(offset), torch.zeros(1, 1), 4, 6, torch.arange(5.))


def test_saved_recipient_and_donor_are_immutable_and_copy_is_exact():
    recipient, donor = state(0), state(10)
    saved = copy_state_to(recipient, 'cpu')
    patched, audit = measured_patch(saved, donor=donor, generated_positions=[2, 3], visual_positions=[0, 1])
    selected = [6, 7]
    keep = [0, 1, 2, 3, 4, 5, 8, 9]
    assert torch.equal(saved.cache.layers[0].keys, recipient.cache.layers[0].keys)
    assert torch.equal(patched.cache.layers[0].keys[:, :, selected], donor.cache.layers[0].keys[:, :, selected])
    assert torch.equal(patched.cache.layers[0].keys[:, :, keep], recipient.cache.layers[0].keys[:, :, keep])
    assert audit['measured_invariance']['all_nonselected_exact']
    assert audit['measured_invariance']['visual_exact']
    assert audit['measured_invariance']['selected_exact']
    assert audit['measured_invariance']['logits_unchanged_at_patch']
    assert patched.cache.layers[0].keys.data_ptr() != saved.cache.layers[0].keys.data_ptr()


def test_self_patch_is_exact_for_all_cached_values_and_logits():
    original = state(0)
    result, audit = measured_patch(original, donor=original, generated_positions=[1, 2], visual_positions=[0])
    assert torch.equal(original.cache.layers[0].keys, result.cache.layers[0].keys)
    assert torch.equal(original.cache.layers[0].values, result.cache.layers[0].values)
    assert torch.equal(original.last_logits, result.last_logits)
